# Stage 2 Processor - Quick Start Guide

## What You Have

A complete, production-ready Stage 2 processor that:
✅ Parses quantities (fractions, ranges, unicode)
✅ Normalizes units to canonical codes
✅ Links ingredients with fuzzy matching
✅ Resolves ingredient forms (chopped, ground, etc.)
✅ Converts everything to SI units (grams/milliliters/each)
✅ Handles density lookups for volume↔mass conversions
✅ Generates detailed error reports

## How to Use It

### 1. Prepare Your Files

Put these in `/mnt/project/` (or same directory as script):
- ✅ Your Stage 1 JSONL file (e.g., `recipe_sample_251105__1_.jsonl`)
- ✅ `Ingredient_Table_Populated_Master_251130.xlsx`
- ✅ `Form_Table_Populated_Complete.xlsx`
- ✅ `Density_Table_Populated__Final_251130.xlsx`
- ✅ `Unit_Conversion_Constants_Table_Populated.xlsx`
- ✅ `Meaning-carrying_tokens_-_allow_list.txt`

### 2. Configure Input File

Edit `config.py`:
```python
INPUT_FILE = "your_stage1_file.jsonl"  # Change this to your file name
```

### 3. Run the Processor

```bash
python main.py
```

That's it! ✨

### 4. Check Your Outputs

Three files are generated:

**1. `stage2_output.jsonl`** - Your processed data
```json
{
  "ingredient_canonical_name": "Chia seeds",
  "canonical_qty": 118.294,
  "canonical_unit": "mL",
  "conversion_path": "vol→vol"
}
```

**2. `stage2_errors.txt`** - Human-readable errors
```
MISSING INGREDIENTS (33)
Recipe 127, Line 8: "1 tsp maca root powder"
  → Action: Add ingredient to Ingredient Table
```

**3. `stage2_errors.json`** - Machine-readable errors
```json
{
  "missing_ingredients": [...],
  "missing_densities": [...]
}
```

## The First Run Will Have Errors! (This is Normal)

Your first run might show:
```
✓ Successful: 13 (11.3%)
✗ Failed: 102 (88.7%)
```

**This is expected!** You need to build up your reference tables.

## How to Fix Errors

### Error Type 1: Missing Ingredients

**Error:**
```
"1 tsp maca root powder"
  → Candidate name: maca root powder
  → Action: Add ingredient to Ingredient Table
```

**Fix:**
1. Open `Ingredient_Table_Populated_Master.xlsx`
2. Add new row:
   - `ingredient_id`: INGR_01500 (next available ID)
   - `primary_name`: Maca root powder
   - `aliases`: maca powder
   - `category`: Superfoods
   - `default_form_id`: FORM_POWDER
3. Save file
4. Rerun processor

### Error Type 2: Missing Densities

**Error:**
```
"1 cup chia seeds"
  → Conversion needed: vol→mass
  → Action: Add density for INGR_01091 + FORM_SEEDS
```

**Fix:**
1. Open `Density_Table_Populated__Final.xlsx`
2. Add new row:
   - `density_id`: DENS_01000 (next available)
   - `ingredient_id`: INGR_01091
   - `form_id`: FORM_SEEDS
   - `g_per_mL`: 0.72 (measure: 1 cup chia = 170g, so 170/236.588 = 0.72)
   - `source_name`: Your measurement source
3. Save file
4. Rerun processor

### Error Type 3: Multi-Ingredient Lines

**Error:**
```
"coconut or coconut flakes"
  → Action: Split into separate ingredient lines
```

**Fix:**
Go back to Stage 1 and split this into two separate lines:
- Line 1: "coconut"
- Line 2: "coconut flakes"

## Workflow for Building Your Database

### Phase 1: Process Sample (Done! ✅)
- Run on small sample
- Identify missing data
- **This is where you are now**

### Phase 2: Fill Gaps (Next Step)
1. Review `stage2_errors.txt`
2. Add ~10-20 missing ingredients
3. Add corresponding densities
4. Rerun processor
5. Repeat until sample success rate > 80%

### Phase 3: Expand
1. Process larger recipe batch
2. Continue adding missing data
3. Build comprehensive reference tables

### Phase 4: Production
1. Process all recipes
2. Success rate should be 90%+
3. Remaining errors are true edge cases

## Common Questions

### Q: Why is my success rate so low?
**A:** First run always has low success! You're building your reference database. Add missing ingredients and densities, then rerun.

### Q: How do I measure densities?
**A:** 
1. Measure 1 cup of ingredient (in grams)
2. Divide by 236.588 (mL per cup)
3. That's your g/mL density

Example: 1 cup flour = 125g
Density = 125 / 236.588 = 0.528 g/mL

### Q: Can I skip densities?
**A:** Only if you never convert volume↔mass. But for accurate nutrition, you need densities.

### Q: What if an ingredient has multiple forms?
**A:** Add separate density entries for each form:
- Onion + FORM_WHOLE → one density
- Onion + FORM_CHOPPED → different density
- Onion + FORM_MINCED → another density

### Q: How do I process multiple recipe files?
**A:** Change `INPUT_FILE` in `config.py` and rerun. Or write a batch script:
```python
for filename in ["recipe1.jsonl", "recipe2.jsonl", "recipe3.jsonl"]:
    # Update config
    # Run processor
```

## What Each File Does

**`main.py`**
- Entry point
- Orchestrates everything
- Generates reports

**`config.py`**
- All settings in one place
- File paths
- Conversion constants
- Thresholds

**`data_loader.py`**
- Loads Excel files
- Indexes ingredients for fast lookup
- Normalizes names

**`processor.py`**
- Main orchestrator
- Runs each step sequentially
- Tracks errors

**`step2_quantity_parser.py`**
- Parses "1/2", "1 1/2", "½", "1-2"
- Handles ranges, approximations
- Test with: `python step2_quantity_parser.py`

**`step3_unit_normalizer.py`**
- "cup" → CUP, "tbsp" → TBSP
- Determines dimension (mass/volume/count)
- Test with: `python step3_unit_normalizer.py`

**`step5_ingredient_linking.py`**
- Extracts ingredient name from text
- Fuzzy matches against table
- Handles aliases

**`steps6_9_form_and_conversion.py`**
- Form resolution (chopped, ground, etc.)
- Canonical dimension selection
- Density lookup
- Final SI conversion math

## Success Tips

1. **Start small**: Process 10-20 recipes first
2. **Build iteratively**: Add missing data gradually
3. **Document sources**: Note where densities come from
4. **Use aliases**: Add common variations to ingredient aliases
5. **Check forms**: Make sure form detection is working
6. **Test often**: Rerun after each batch of additions

## Next Steps

1. ✅ Review the error report from your test run
2. ⬜ Add top 10 missing ingredients to table
3. ⬜ Add corresponding densities
4. ⬜ Rerun and check improvement
5. ⬜ Repeat until satisfied
6. ⬜ Process all your recipes!

## Need Help?

Check these in order:
1. `README.md` - Full documentation
2. `stage2_errors.txt` - Your specific errors
3. Test individual modules - Run the test functions
4. Check example data - See what worked vs what failed

---

**You're all set!** The processor is ready to use. Start by fixing the errors in your test run, then scale up. 🚀
