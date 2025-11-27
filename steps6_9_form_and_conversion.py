"""
Stage 2 Processor - Steps 6-9: Form, Dimension, Density, Conversion
"""

import re
from typing import Dict, Optional, List


# ============================================================================
# STEP 6: FORM RESOLUTION
# ============================================================================

def resolve_form(ingredient_text: str, form_hint_raw: str, ingredient_id: str,
                 unit_enum: str, reference_data, meaning_tokens: Dict) -> Dict:
    """
    Determine the form_id for the ingredient
    
    Returns dict with:
        - resolved_form_id: str
        - form_resolution_method: str
        - form_resolution_conflict: bool
        - form_resolution_notes: str
    """
    result = {
        "resolved_form_id": None,
        "form_resolution_method": None,
        "form_resolution_conflict": False,
        "form_resolution_notes": ""
    }
    
    if not ingredient_id:
        return result
    
    # Get ingredient data
    if ingredient_id not in reference_data.ingredients:
        return result
    
    ingredient_data = reference_data.ingredients[ingredient_id]
    default_form_id = ingredient_data.get("default_form_id")
    
    # Collect form hints from the full text (Option B from discussion)
    form_tokens_found = extract_form_tokens(ingredient_text, meaning_tokens)
    
    # Also check form_hint_raw if provided
    if form_hint_raw:
        additional_tokens = extract_form_tokens(form_hint_raw, meaning_tokens)
        form_tokens_found.extend(additional_tokens)
    
    # Remove duplicates
    form_tokens_found = list(set(form_tokens_found))
    
    if not form_tokens_found:
        # No explicit form hints - use default
        if default_form_id:
            result["resolved_form_id"] = default_form_id
            result["form_resolution_method"] = "default"
            return result
        else:
            # No default either - use FORM_WHOLE as fallback
            result["resolved_form_id"] = "FORM_WHOLE"
            result["form_resolution_method"] = "fallback_whole"
            result["form_resolution_notes"] = "no_default_form_available"
            return result
    
    # Map tokens to form IDs
    from config import FORM_TOKEN_MAP
    
    form_ids = []
    for token in form_tokens_found:
        if token.lower() in FORM_TOKEN_MAP:
            form_ids.append(FORM_TOKEN_MAP[token.lower()])
    
    if not form_ids:
        # Tokens found but not in our mapping
        if default_form_id:
            result["resolved_form_id"] = default_form_id
            result["form_resolution_method"] = "default"
            result["form_resolution_notes"] = f"unmapped_tokens:{','.join(form_tokens_found)}"
            return result
    
    # Check for conflicts (multiple different forms)
    unique_forms = list(set(form_ids))
    
    if len(unique_forms) > 1:
        # Conflict! Multiple forms detected
        result["form_resolution_conflict"] = True
        result["resolved_form_id"] = unique_forms[0]  # Take first by precedence
        result["form_resolution_method"] = "explicit_with_conflict"
        result["form_resolution_notes"] = f"conflict_forms:{','.join(unique_forms)}"
        return result
    
    if len(unique_forms) == 1:
        result["resolved_form_id"] = unique_forms[0]
        result["form_resolution_method"] = "explicit"
        return result
    
    # Fallback to default
    if default_form_id:
        result["resolved_form_id"] = default_form_id
        result["form_resolution_method"] = "default"
        return result
    
    result["resolved_form_id"] = "FORM_WHOLE"
    result["form_resolution_method"] = "fallback_whole"
    return result


def extract_form_tokens(text: str, meaning_tokens: Dict) -> List[str]:
    """Extract form-related tokens from text"""
    if not text:
        return []
    
    text_lower = text.lower()
    
    # Get state_form tokens from meaning_tokens
    form_keywords = meaning_tokens.get("state_form", []) if meaning_tokens else []
    
    # Add our known form keywords
    known_form_keywords = [
        'ground', 'powder', 'powdered', 'whole', 'sliced', 'chopped', 'diced',
        'minced', 'grated', 'shredded', 'mashed', 'puree', 'dried', 'dehydrated',
        'canned', 'jarred', 'seed', 'seeds', 'flake', 'flakes'
    ]
    
    all_keywords = list(set(form_keywords + known_form_keywords))
    
    found_tokens = []
    for keyword in all_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            found_tokens.append(keyword)
    
    return found_tokens


# ============================================================================
# STEP 7: CANONICAL DIMENSION SELECTION
# ============================================================================

def select_canonical_dimension(unit_enum: str, original_dimension: str,
                               resolved_form_id: str, reference_data) -> Dict:
    """
    Select the canonical dimension and unit for storage
    
    Returns dict with:
        - canonical_dimension_selected: str (mass|volume|count)
        - canonical_unit: str (g|mL|ea)
        - bridge_required: str (none|vol→mass|mass→vol)
        - bridge_inputs_ready: bool (preliminary flag)
    """
    result = {
        "canonical_dimension_selected": None,
        "canonical_unit": None,
        "bridge_required": "none",
        "bridge_inputs_ready": False
    }
    
    # Rule 1: Specials short-circuit
    if original_dimension == "special":
        return result
    
    # Rule 2: Counts stay counts
    if original_dimension == "count":
        result["canonical_dimension_selected"] = "count"
        result["canonical_unit"] = "ea"
        result["bridge_required"] = "none"
        result["bridge_inputs_ready"] = True
        return result
    
    # Rule 3: Mass/Volume normalize to form's target
    if not resolved_form_id or resolved_form_id not in reference_data.forms:
        # No form info - keep original dimension
        if original_dimension == "mass":
            result["canonical_unit"] = "g"
        elif original_dimension == "volume":
            result["canonical_unit"] = "mL"
        result["canonical_dimension_selected"] = original_dimension
        result["bridge_required"] = "none"
        result["bridge_inputs_ready"] = True
        return result
    
    form_data = reference_data.forms[resolved_form_id]
    target_dim = form_data.get("target_dimension", "auto")
    
    # Map target_dimension to canonical unit
    if target_dim == "prefer_mass":
        target_unit = "g"
        target_canonical = "mass"
    elif target_dim == "prefer_volume":
        target_unit = "mL"
        target_canonical = "volume"
    elif target_dim == "auto":
        # Keep original
        if original_dimension == "mass":
            target_unit = "g"
            target_canonical = "mass"
        else:  # volume
            target_unit = "mL"
            target_canonical = "volume"
    else:
        # Unknown - keep original
        if original_dimension == "mass":
            target_unit = "g"
            target_canonical = "mass"
        else:
            target_unit = "mL"
            target_canonical = "volume"
    
    result["canonical_unit"] = target_unit
    result["canonical_dimension_selected"] = target_canonical
    
    # Determine bridge requirement
    if original_dimension == "volume" and target_unit == "g":
        result["bridge_required"] = "vol→mass"
        result["bridge_inputs_ready"] = False  # Will check in next step
    elif original_dimension == "mass" and target_unit == "mL":
        result["bridge_required"] = "mass→vol"
        result["bridge_inputs_ready"] = False
    else:
        result["bridge_required"] = "none"
        result["bridge_inputs_ready"] = True
    
    return result


# ============================================================================
# STEP 8: BRIDGING DATA LOOKUP
# ============================================================================

def lookup_density(ingredient_id: str, resolved_form_id: str, bridge_required: str,
                   reference_data) -> Dict:
    """
    Find density data if needed for volume<->mass conversion
    
    Returns dict with:
        - density_id: str
        - density_g_per_ml: float
        - bridge_inputs_ready: bool
        - bridge_selection_path: str
        - flag_needs_density_lookup: bool
        - bridge_warning: list
    """
    result = {
        "density_id": None,
        "density_g_per_ml": None,
        "bridge_inputs_ready": False,
        "bridge_selection_path": None,
        "flag_needs_density_lookup": False,
        "bridge_warning": []
    }
    
    # Skip if no bridge needed
    if bridge_required == "none":
        result["bridge_inputs_ready"] = True
        return result
    
    # We need a density
    # H1: Exact form match
    key = (ingredient_id, resolved_form_id)
    if key in reference_data.densities:
        density_data = reference_data.densities[key]
        result["density_id"] = density_data["density_id"]
        result["density_g_per_ml"] = density_data["g_per_ml"]
        result["bridge_inputs_ready"] = True
        result["bridge_selection_path"] = "H1_EXACT_FORM"
        return result
    
    # H2: Default form match
    if ingredient_id in reference_data.ingredients:
        default_form = reference_data.ingredients[ingredient_id].get("default_form_id")
        if default_form:
            key = (ingredient_id, default_form)
            if key in reference_data.densities:
                density_data = reference_data.densities[key]
                result["density_id"] = density_data["density_id"]
                result["density_g_per_ml"] = density_data["g_per_ml"]
                result["bridge_inputs_ready"] = True
                result["bridge_selection_path"] = "H2_DEFAULT_FORM"
                result["bridge_warning"].append("USED_DEFAULT_FORM")
                return result
    
    # No density found
    result["flag_needs_density_lookup"] = True
    result["bridge_selection_path"] = "H0_NO_DENSITY"
    result["bridge_warning"].append("DENSITY_NOT_FOUND")
    return result


# ============================================================================
# STEP 9: DETERMINISTIC CONVERSION TO CANONICAL SI
# ============================================================================

def convert_to_canonical(qty_min: float, qty_max: float, unit_enum: str,
                        canonical_unit: str, bridge_required: str,
                        density_g_per_ml: Optional[float], 
                        original_dimension: str, reference_data) -> Dict:
    """
    Convert quantities to canonical SI units
    
    Returns dict with:
        - canonical_qty_min: float
        - canonical_qty_max: float
        - canonical_qty: float (midpoint)
        - conversion_path: str
        - conversion_notes: str
    """
    from config import MASS_TO_GRAMS, VOLUME_TO_ML
    
    result = {
        "canonical_qty_min": None,
        "canonical_qty_max": None,
        "canonical_qty": None,
        "conversion_path": None,
        "conversion_notes": ""
    }
    
    if qty_min is None or qty_max is None:
        result["conversion_notes"] = "missing_quantity"
        return result
    
    # Count stays count
    if canonical_unit == "ea":
        result["canonical_qty_min"] = qty_min
        result["canonical_qty_max"] = qty_max
        result["canonical_qty"] = (qty_min + qty_max) / 2.0
        result["conversion_path"] = "count"
        return result
    
    # Special units - no conversion
    if original_dimension == "special":
        return result
    
    # Mass → Mass
    if canonical_unit == "g" and unit_enum in MASS_TO_GRAMS:
        factor = MASS_TO_GRAMS[unit_enum]
        result["canonical_qty_min"] = round(qty_min * factor, 6)
        result["canonical_qty_max"] = round(qty_max * factor, 6)
        result["canonical_qty"] = round((result["canonical_qty_min"] + result["canonical_qty_max"]) / 2.0, 6)
        result["conversion_path"] = "mass→mass"
        return result
    
    # Volume → Volume
    if canonical_unit == "mL" and unit_enum in VOLUME_TO_ML:
        factor = VOLUME_TO_ML[unit_enum]
        result["canonical_qty_min"] = round(qty_min * factor, 6)
        result["canonical_qty_max"] = round(qty_max * factor, 6)
        result["canonical_qty"] = round((result["canonical_qty_min"] + result["canonical_qty_max"]) / 2.0, 6)
        result["conversion_path"] = "vol→vol"
        return result
    
    # Volume → Mass (needs density)
    if bridge_required == "vol→mass":
        if density_g_per_ml is None:
            result["conversion_notes"] = "missing_density"
            return result
        
        if unit_enum not in VOLUME_TO_ML:
            result["conversion_notes"] = f"unknown_volume_unit:{unit_enum}"
            return result
        
        # Convert to mL first
        ml_min = qty_min * VOLUME_TO_ML[unit_enum]
        ml_max = qty_max * VOLUME_TO_ML[unit_enum]
        
        # Then to grams using density
        result["canonical_qty_min"] = round(ml_min * density_g_per_ml, 6)
        result["canonical_qty_max"] = round(ml_max * density_g_per_ml, 6)
        result["canonical_qty"] = round((result["canonical_qty_min"] + result["canonical_qty_max"]) / 2.0, 6)
        result["conversion_path"] = "vol→mass via density"
        return result
    
    # Mass → Volume (needs density)
    if bridge_required == "mass→vol":
        if density_g_per_ml is None or density_g_per_ml == 0:
            result["conversion_notes"] = "missing_density"
            return result
        
        if unit_enum not in MASS_TO_GRAMS:
            result["conversion_notes"] = f"unknown_mass_unit:{unit_enum}"
            return result
        
        # Convert to grams first
        g_min = qty_min * MASS_TO_GRAMS[unit_enum]
        g_max = qty_max * MASS_TO_GRAMS[unit_enum]
        
        # Then to mL using density
        result["canonical_qty_min"] = round(g_min / density_g_per_ml, 6)
        result["canonical_qty_max"] = round(g_max / density_g_per_ml, 6)
        result["canonical_qty"] = round((result["canonical_qty_min"] + result["canonical_qty_max"]) / 2.0, 6)
        result["conversion_path"] = "mass→vol via density"
        return result
    
    # Shouldn't reach here
    result["conversion_notes"] = "conversion_path_unknown"
    return result
