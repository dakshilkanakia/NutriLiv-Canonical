
# Stage-2 Dev Pseudocode (Updated Field Names)

This document consolidates the pseudocode for each Stage-2 module using the **final field names**:

**Canonical field name mapping (authoritative):**
- `canonical_qty_si_value_min` → `canonical_qty_min`
- `canonical_qty_si_value_max` → `canonical_qty_max`
- `canonical_qty_si_value` → `canonical_qty`
- `canonical_qty_si_unit` → `canonical_unit`
- `density_g_per_ml_used` → `density_g_per_ml`

> Notes:  
> • Counts (`ea`) are never converted to mass/volume in Stage-2.  
> • No container *count→content* conversions.  
> • No piece-weight conversions.

---

## 1) Intake & Validation

```python
def intake_stage1_rows(rows: Iterable[dict]) -> IntakeResult:
    accepted, rejected = [], []
    per_recipe_seen = defaultdict(set)
    per_recipe_max = defaultdict(int)

    for r in rows:
        r = normalize_stage1_row(r)  # trim, unicode NFC, collapse spaces, empty normalization

        # Required fields
        if not r.get("recipe_id") or not r.get("ingredient_original_text"):
            reject(r, "MISSING_REQUIRED_FIELD", "recipe_id or ingredient_original_text")
            continue
        try:
            ln = int(r.get("ingredient_line_number"))
            if ln < 1: raise ValueError()
        except Exception:
            reject(r, "TYPE_MISMATCH", "ingredient_line_number must be int >= 1")
            continue

        # Section-header guard (heuristic)
        if looks_like_section_header(r["ingredient_original_text"]):
            reject(r, "SECTION_HEADER_ROW", "Likely a header")
            continue

        # Idempotency: recipe_id + ingredient_line_number + line_hash|text
        key = make_idempotency_key(
            r["recipe_id"],
            ln,
            r.get("line_hash"),
            r["ingredient_original_text"]
        )
        if exists_in_db(key):
            continue  # idempotent skip

        # Soft check on unit format only (no enum map here)
        if is_pathologic_unit(r.get("unit_original", "")):
            reject(r, "UNIT_INVALID_FORMAT", "unit token malformed")
            continue

        save_validated_row(key, r)
        per_recipe_seen[r["recipe_id"]].add(ln)
        per_recipe_max[r["recipe_id"]] = max(per_recipe_max[r["recipe_id"]], ln)
        accepted.append(key)

    # Non-blocking sequence gap warnings
    for recipe_id, max_ln in per_recipe_max.items():
        seen = per_recipe_seen[recipe_id]
        if set(range(1, max_ln + 1)) != seen:
            log_warning("SEQUENCE_GAP", recipe_id, detail={
                "missing": sorted(list(set(range(1, max_ln + 1)) - seen))
            })

    return IntakeResult(accepted_count=len(accepted), rejected_count=len(rejected))
```

---

## 2) Quantity Parsing (lossless → numeric)

```python
def parse_quantity(qty_value_original: str) -> dict:
    out = {
        "qty_min": None,
        "qty_max": None,
        "qty_is_range": False,
        "qty_approx_flag": False,
        "qty_parse_warnings": [],
        "qty_precision_code": None
    }
    s = (qty_value_original or "").strip()
    if not s:
        return out

    # approx markers
    approx_markers = ["~", "≈", "about", "approx", "approximately", "around", "circa", "c."]
    trailing_plus = s.endswith("+")
    if trailing_plus or any(m in s.lower() for m in approx_markers):
        out["qty_approx_flag"] = True
        s = s.rstrip("+")
        for m in approx_markers:
            s = re.sub(fr"\b{re.escape(m)}\b", "", s, flags=re.I)
        s = s.strip()

    # normalize thousands & range separators
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    s_match = replace_unicode_fractions_for_matching(s)
    s_match = re.sub(r"\s*(–|—|-|\bto\b)\s*", " RANGE_SEP ", s_match, flags=re.I)

    parts = [p.strip() for p in s_match.split("RANGE_SEP")]
    if len(parts) == 2:
        left = parse_single_value(parts[0])
        right = parse_single_value(parts[1])
        if left is None or right is None:
            out["qty_parse_warnings"].append("QTY_RANGE_SIDE_INVALID")
            return out
        out["qty_min"], out["qty_max"] = left, right
        out["qty_is_range"] = True
        out["qty_precision_code"] = "range"
        return out
    elif len(parts) > 2:
        out["qty_parse_warnings"].append("MULTIPLE_RANGE_SEPARATORS")
        return out

    val = parse_single_value(parts[0]) or parse_text_number(parts[0])
    if val is None:
        out["qty_parse_warnings"].append("NO_NUMERIC_QUANTITY")
        return out

    out["qty_min"] = out["qty_max"] = val
    out["qty_precision_code"] = detect_precision_code(parts[0])
    return out
```

---

## 3) Unit Normalization

```python
def normalize_unit(unit_original: str, ing_text: str, ingredient_id: Optional[str]) -> dict:
    out = {"unit_enum": None, "original_dimension": None, "flag_nonstandard_unit": False}
    s = (unit_original or "").strip().lower()
    s = re.sub(r"\.+$", "", s)     # drop trailing periods
    s = re.sub(r"\s+", " ", s)

    # explicit FLOZ detection
    if re.search(r"\b(fl\s*oz|fl\.?\s*oz\.?|fluid\s+ounce(s)?)\b", s):
        out["unit_enum"] = "FLOZ"
        out["original_dimension"] = "volume"
        return out

    token = UNIT_SYNONYM_MAP.get(s)
    if token:
        out["unit_enum"] = token
    else:
        out["flag_nonstandard_unit"] = s not in SPECIAL_SYNONYMS
        out["unit_enum"] = SPECIAL_SYNONYMS.get(s)  # may be None

    if out["unit_enum"] in MASS_ENUMS:
        out["original_dimension"] = "mass"
    elif out["unit_enum"] in VOLUME_ENUMS:
        out["original_dimension"] = "volume"
    elif out["unit_enum"] in COUNT_ENUMS:
        out["original_dimension"] = "count"
    elif out["unit_enum"] in SPECIAL_ENUMS:
        out["original_dimension"] = "special"
    else:
        out["original_dimension"] = None

    return out
```

---

## 4) Package & Variant Parsing (no count→content math)

```python
def parse_package_variant(unit_enum, package_size_raw, ing_text):
    out = {
        "package_multiplier": 1.0,
        "package_size_value": None,
        "package_size_unit": None,     # OZ/FLOZ/G/KG/ML/L
        "package_size_SI_value": None, # g or mL
        "package_size_SI_unit": None,  # G or ML
        "package_parse_warnings": []
    }

    text = " ".join([t for t in [package_size_raw, ing_text] if t]).lower()
    text = re.sub(r"\s+", " ", text)

    # 1) multiplier patterns (non-destructive)
    m = re.search(r"\b(\d+)\s*(x|×)\s*(\d+(?:\.\d+)?)\s*(fl\s*oz|fl\.?\s*oz\.?|oz|g|kg|ml|l)\b", text)
    if m:
        out["package_multiplier"] = float(m.group(1))
        out["package_parse_warnings"].append("MULTIPLIER_FOUND")
    else:
        m2 = re.search(r"\b(\d+)\s*\([^)]*\b(\d+(?:\.\d+)?)\s*(fl\s*oz|fl\.?\s*oz\.?|oz|g|kg|ml|l)\b[^)]*\)", text)
        if m2:
            out["package_multiplier"] = float(m2.group(1))

    # 2) size extraction
    s = re.search(r"\b(\d+(?:\.\d+)?)\s*-\s*(fl\s*oz|fl\.?\s*oz\.?|oz|g|kg|ml|l)\b", text)         or re.search(r"\b(\d+(?:\.\d+)?)\s*(fl\s*oz|fl\.?\s*oz\.?|oz|g|kg|ml|l)\b", text)         or re.search(r"\((\d+(?:\.\d+)?)\s*(fl\s*oz|fl\.?\s*oz\.?|oz|g|kg|ml|l)\)", text)
    if s:
        val = float(s.group(1))
        unit = normalize_unit_token(s.group(2))  # -> OZ/FLOZ/G/KG/ML/L
        out["package_size_value"] = val
        out["package_size_unit"] = unit
    else:
        out["package_parse_warnings"].append("NO_PACKAGE_SIZE_FOUND")

    # 3) SI mirror
    if out["package_size_unit"] in ("G", "KG"):
        g = val * (1000.0 if out["package_size_unit"] == "KG" else 1.0)
        out["package_size_SI_value"] = g
        out["package_size_SI_unit"] = "G"
    elif out["package_size_unit"] in ("ML", "L"):
        ml = val * (1000.0 if out["package_size_unit"] == "L" else 1.0)
        out["package_size_SI_value"] = ml
        out["package_size_SI_unit"] = "ML"
    elif out["package_size_unit"] == "OZ":
        out["package_size_SI_value"] = val * 28.349523125
        out["package_size_SI_unit"] = "G"
    elif out["package_size_unit"] == "FLOZ":
        out["package_size_SI_value"] = val * 29.5735295625
        out["package_size_SI_unit"] = "ML"

    # 4) Ambiguity warning if plain "oz" and likely liquid
    if "oz" in text and re.search(r"\b(fl\s*oz|fl\.?\s*oz\.?|fluid ounce)", text) is None        and looks_like_liquid_context(ing_text):
        out["package_parse_warnings"].append("AMBIGUOUS_OZ_LIQUID")

    return out
```

---

## 5) Ingredient Linking

```python
def link_ingredient(row, dictionaries) -> dict:
    cand = extract_candidate(row.ingredient_original_text,
                             row.qty_min, row.unit_enum,
                             row.package_size_raw, row.get("size_descriptor_raw"))
    cand_norm, cand_tokens = normalize_for_matching(cand)

    # L0: primary exact
    hit = dictionaries.primary.get(cand_norm)
    if hit:
        return accept_link(hit, 1.0, "exact")

    # L1: alias exact
    hit = dictionaries.alias.get(cand_norm)
    if hit:
        return accept_link(hit, 0.99, "alias")

    # L2: normalized keep-tokens exact
    cand_keep = keep_meaning_tokens(cand_norm)
    hit = dictionaries.keep.get(cand_keep)
    if hit:
        return accept_link(hit, 0.97, "normalized")

    # L3: token-set fuzzy
    candidates = topk_by_jaccard(cand_tokens, dictionaries.index, k=5)
    if candidates and candidates[0].score >= 0.92:
        return accept_link(candidates[0].ingredient_id, candidates[0].score, "fuzzy")
    elif candidates and candidates[0].score >= 0.80:
        return review_link(candidates[:3], "LOW_CONFIDENCE", cand, cand_norm)
    else:
        if looks_multi_ingredient(cand):
            return unresolved_link("MULTI_INGREDIENT_LINE", cand, cand_norm)
        return unresolved_link("NO_MATCH", cand, cand_norm)
```

---

## 6) Form Resolution

```python
def resolve_form(row, ingredient, forms, rules) -> dict:
    tokens = collect_tokens(row.form_hint_raw, row.modifiers_raw, row.ingredient_original_text)
    tokens = filter_to_meaning_tokens(tokens)

    # P1: per-ingredient overrides
    hit = rules.per_ingredient.get(row.ingredient_id, {}).get_match(tokens)
    if hit:
        return accept_form(hit, "alias", conflict=False)

    # P2: global token → form map
    g_hits = [rules.global_map[t] for t in tokens if t in rules.global_map]
    g_hits = dedupe_preserve_precedence(g_hits)
    if len(g_hits) == 1:
        return accept_form(g_hits[0], "explicit", conflict=False)
    elif len(g_hits) > 1:
        chosen = choose_by_precedence(g_hits)
        return accept_form(chosen, "explicit", conflict=True,
                           notes=f"conflict among {g_hits}")

    # P3: unit-implied heuristic (low precedence)
    maybe = rules.unit_bias(row.unit_enum, row.ingredient_id)
    if maybe:
        return accept_form(maybe, "unit_bias", conflict=False)

    # P4: fallback default
    if ingredient.default_form_id:
        return accept_form(ingredient.default_form_id, "default", conflict=False)

    # P5: category fallback (optional)
    cat_default = rules.category_default(ingredient.category)
    if cat_default:
        return accept_form(cat_default, "category_default", conflict=False)

    return unresolved_form("NO_FORM_MATCH")
```

---

## 7) Canonical Dimension Selection

```python
def select_canonical_dimension(row, form) -> dict:
    out = {
        "canonical_unit": None,                 # "g" | "mL" | "ea"
        "canonical_dimension_selected": None,   # "mass" | "volume" | "count"
        "bridge_required": "none",              # "none" | "vol→mass" | "mass→vol"
        "bridge_inputs_ready": None,            # bool or None
        "dimension_decision_reason": "",
        "display_rule": form.display_rule_default
    }

    # 1) specials
    if row.original_dimension == "special":
        out["dimension_decision_reason"] = "special unit; no canonical stored"
        return out

    # 2) count stays count
    if row.original_dimension == "count":
        out["canonical_unit"] = "ea"
        out["canonical_dimension_selected"] = "count"
        out["bridge_required"] = "none"
        out["bridge_inputs_ready"] = None
        out["dimension_decision_reason"] = "count stays ea"
        return out

    # 3) mass/volume normalize to form target
    target = form.target_dimension   # "g" or "mL"
    out["canonical_unit"] = target
    out["canonical_dimension_selected"] = "mass" if target == "g" else "volume"

    if row.original_dimension == "volume" and target == "g":
        out["bridge_required"] = "vol→mass"
        out["dimension_decision_reason"] = "form target mass"
    elif row.original_dimension == "mass" and target == "mL":
        out["bridge_required"] = "mass→vol"
        out["dimension_decision_reason"] = "form target volume"
    else:
        out["bridge_required"] = "none"
        out["dimension_decision_reason"] = "already in target dimension"

    return out
```

---

## 8) Bridging Data Lookup (density only)

```python
def lookup_density_bridge(row, density_repo, form_repo, today) -> dict:
    result = {
        "density_id": None,
        "density_g_per_ml": None,
        "bridge_inputs_ready": True,
        "flag_needs_density_lookup": False,
        "bridge_selection_path": "",
        "bridge_warning": []
    }

    # Skip if no bridge needed or count/special
    if row.bridge_required == "none" or row.canonical_unit == "ea" or row.original_dimension == "special":
        return result

    packed_hint = detect_packed_state(row.modifiers_raw)  # "packed" | "loosely_packed" | None
    candidates = []

    def add(tag, filt):
        for d in density_repo.find(filt):
            if d.is_active and (d.effective_from is None or d.effective_from <= today) and                (d.effective_to is None or today < d.effective_to):
                candidates.append((tag, d))

    # H1: exact + packed
    add("H1_EXACT_FORM_PACKED", lambda d: d.ingredient_id==row.ingredient_id and
                                          d.form_id==row.resolved_form_id and
                                          (packed_hint is None or d.packed_state==packed_hint))
    # H2: exact form
    if not candidates:
        add("H2_EXACT_FORM", lambda d: d.ingredient_id==row.ingredient_id and
                                       d.form_id==row.resolved_form_id)
    # H3: form group (optional)
    if not candidates and form_repo.group(row.resolved_form_id):
        grp = form_repo.group(row.resolved_form_id)
        add("H3_FORM_GROUP", lambda d: d.ingredient_id==row.ingredient_id and d.form_id in grp)
    # H4: default form
    if not candidates and form_repo.default_form(row.ingredient_id):
        df = form_repo.default_form(row.ingredient_id)
        add("H4_DEFAULT_FORM", lambda d: d.ingredient_id==row.ingredient_id and d.form_id==df)
    # H5: any form
    if not candidates:
        add("H5_ANY_FORM", lambda d: d.ingredient_id==row.ingredient_id)

    if not candidates:
        result["bridge_inputs_ready"] = False
        result["flag_needs_density_lookup"] = True
        result["bridge_selection_path"] = "H0_NO_DENSITY"
        return result

    def rank(item):
        tag, d = item
        return (-d.source_priority, d.effective_from or date.min, -getattr(d, "quality_score", 0), d.density_id)

    tag, chosen = sorted(candidates, key=rank)[0]
    result["density_id"] = chosen.density_id
    result["density_g_per_ml"] = chosen.g_per_mL
    result["bridge_selection_path"] = tag

    # Sanity checks
    if not in_reasonable_range(chosen.g_per_mL, row.ingredient_id, row.resolved_form_id):
        result["bridge_warning"].append("SANITY_RANGE_EDGE")
        result["bridge_inputs_ready"] = False
        result["flag_needs_density_lookup"] = True

    if packed_hint and chosen.packed_state != packed_hint:
        result["bridge_warning"].append("PACKED_STATE_MISMATCH")

    if chosen.temp_c and abs(chosen.temp_c - 20) > 10:
        result["bridge_warning"].append("TEMP_MISMATCH")

    return result
```

---

## 9) Deterministic Conversion to Canonical SI

```python
def to_si(row, constants) -> dict:
    out = {
        "canonical_qty_min": None,
        "canonical_qty_max": None,
        "canonical_qty": None,
        "canonical_unit": row.canonical_unit,
        "conversion_path": None,
        "conversion_notes": ""
    }

    def conv_mass_to_g(v, unit):
        return v * {"MG":1/1000,"G":1,"KG":1000,"OZ":28.349523125,"LB":453.59237}[unit]

    def conv_vol_to_ml(v, unit):
        return v * {"TSP":4.92892159375,"TBSP":14.78676478125,"CUP":236.5882365,
                    "FLOZ":29.5735295625,"PINT":473.176473,"QUART":946.352946,
                    "GALLON":3785.411784,"ML":1,"L":1000}[unit]

    def compute_end(q):
        if q is None: return None
        if row.canonical_unit == "ea":
            out["conversion_path"] = out["conversion_path"] or "count"
            return q
        if row.canonical_unit == "g":
            if row.bridge_required == "vol→mass":
                ml = conv_vol_to_ml(q, row.unit_enum)
                out["conversion_path"] = "vol→mass via density"
                return ml * row.density_g_per_ml
            elif row.bridge_required == "none":
                out["conversion_path"] = "mass→mass"
                return conv_mass_to_g(q, row.unit_enum)
            return None
        if row.canonical_unit == "mL":
            if row.bridge_required == "mass→vol":
                g = conv_mass_to_g(q, row.unit_enum)
                out["conversion_path"] = "mass→vol via density"
                return g / row.density_g_per_ml
            elif row.bridge_required == "none":
                out["conversion_path"] = "vol→vol"
                return conv_vol_to_ml(q, row.unit_enum)
            return None
        return None

    # Guard: bridge inputs
    if row.canonical_unit in {"g","mL"} and row.bridge_required in {"vol→mass","mass→vol"}:
        if not row.density_g_per_ml:
            return out  # not computable yet

    vmin = compute_end(row.qty_min)
    vmax = compute_end(row.qty_max)

    out["canonical_qty_min"] = vmin
    out["canonical_qty_max"] = vmax
    if vmin is not None and vmax is not None:
        out["canonical_qty"] = (vmin + vmax) / 2.0  # policy midpoint

    notes = []
    if row.density_id:
        notes.append(f"density={row.density_id}@{row.density_g_per_ml} g/mL")
    out["conversion_notes"] = "; ".join(notes)
    return out
```
