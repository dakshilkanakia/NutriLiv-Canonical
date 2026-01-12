# Stage 2 Ingredient Processor

Complete implementation of the 9-step Stage 2 processing pipeline for converting ingredient data to canonical SI units.

## 📋 Overview

This processor takes Stage 1 parsed ingredient data (JSONL format) and converts it to standardized canonical format with:
- Normalized quantities in SI units (grams, milliliters, or each)
- Linked ingredient IDs from master ingredient table
- Resolved form IDs (whole, chopped, ground, etc.)
- Density-based volume↔mass conversions

## 🚀 Quick Start

### Prerequisites
- Python 3.6+
- Required Excel reference files in `/mnt/project/`:
  - `Ingredient_Table_Populated_Master_260111.xlsx`
  - `Form_Table_Populated_Complete.xlsx`
  - `Density_Table_Populated__Final_260111.xlsx`
  - `Unit_Conversion_Constants_Table_Populated.xlsx`
  - `Meaning-carrying_tokens_-_allow_list.txt`

### Running the Processor

1. **Edit config.py** to set your input filename:
```python
INPUT_FILE = "your_stage1_data.jsonl"
```

2. **Run the processor**:
```bash
python main.py
```

3. **Check outputs**:
- `stage2_output.jsonl` - Successfully processed ingredients
- `stage2_errors.txt` - Human-readable error report
- `stage2_errors.json` - Machine-readable error data

## 📁 File Structure

```
stage2_processor/
├── main.py                          # Main entry point
├── config.py                        # Configuration & constants
├── data_loader.py                   # Excel reference data loader
├── processor.py                     # Main orchestrator
├── step2_quantity_parser.py         # Step 2: Quantity parsing
├── step3_unit_normalizer.py         # Step 3: Unit normalization
├── step5_ingredient_linking.py      # Step 5: Ingredient matching
├── steps6_9_form_and_conversion.py  # Steps 6-9: Form & conversion
└── README.md                        # This file
```

## 🔄 Processing Pipeline

### Step 1: Intake & Validation
- Validates Stage 1 input data
- Already handled by Stage 1 processing

### Step 2: Quantity Parsing
Converts text quantities to numeric values:
- `"1/2"` → 0.5
- `"1 1/2"` → 1.5
- `"½"` → 0.5 (Unicode)
- `"1-2"` → min=1, max=2 (range)
- `"about 2"` → 2 (approx flag)

### Step 3: Unit Normalization
Maps units to canonical enums:
- `"cup"/"cups"` → `CUP`
- `"tbsp"/"tablespoon"` → `TBSP`
- `"eggs"/"egg"` → `EGG`
- `"oz"` → `OZ` (mass)
- `"fl oz"` → `FLOZ` (volume)

Determines dimension: `mass`, `volume`, `count`, or `special`

### Step 4: Package Parsing
*(Not implemented - optional feature)*

### Step 5: Ingredient Linking
Matches ingredient names to master table:
- **Exact match**: "chia seeds" → INGR_01091
- **Alias match**: "chili peppers" → "chile peppers"
- **Fuzzy match**: Score-based token matching

**Threshold:**
- ≥0.92 = auto-accept
- 0.80-0.91 = needs review
- <0.80 = no match (error)

### Step 6: Form Resolution
Determines ingredient form from text:
- Searches for form keywords: "ground", "chopped", "dried", "whole"
- Maps to form IDs: `FORM_GROUND`, `FORM_CHOPPED`, `FORM_DRIED`
- Falls back to ingredient's default form if no hints

### Step 7: Canonical Dimension Selection
Chooses target storage unit:
- **Count → ea** (always)
- **Mass/Volume → Based on form's target_dimension**
  - `prefer_mass` → grams
  - `prefer_volume` → milliliters
  - `auto` → keep original dimension

### Step 8: Bridging Data Lookup
Finds density when converting volume↔mass:
- Looks up `(ingredient_id, form_id)` in density table
- Falls back to default form if exact not found
- Flags missing densities for addition

### Step 9: Canonical Conversion
Final math to convert to SI units:

**Mass → Mass:**
```
200 oz × 28.349 = 5,669.8 g
```

**Volume → Volume:**
```
1 cup × 236.588 = 236.588 mL
```

**Volume → Mass (with density):**
```
1 cup flour × 236.588 mL × 0.528 g/mL = 125 g
```

**Mass → Volume (with density):**
```
100 g olive oil ÷ 0.91 g/mL = 109.89 mL
```

## 📊 Output Format

### Successful Processing Example
```json
{
  "recipe_id": "127",
  "ingredient_line_number": 1,
  "ingredient_original_text": "1/2 cup chia seeds",
  "qty_min": 0.5,
  "qty_max": 0.5,
  "unit_enum": "CUP",
  "original_dimension": "volume",
  "ingredient_id": "INGR_01091",
  "ingredient_canonical_name": "Chia seeds",
  "resolved_form_id": "FORM_SEEDS",
  "canonical_unit": "mL",
  "canonical_qty": 118.294118,
  "conversion_path": "vol→vol"
}
```

## ⚠️ Error Handling

The processor generates detailed error reports for:

### 1. Missing Ingredients
Ingredient name not found in table.
**Action:** Add to `Ingredient_Table_Populated_Master.xlsx`

Example:
```
Recipe 127, Line 8: "1 tsp maca root powder"
  → Candidate name: maca root powder
  → Action: Add ingredient to Ingredient Table
```

### 2. Missing Densities
Volume↔mass conversion needs density data.
**Action:** Add to `Density_Table_Populated__Final.xlsx`

Example:
```
Recipe 127, Line 1: "1/2 cup chia seeds"
  → Ingredient: Chia seeds (INGR_01091)
  → Form: FORM_SEEDS
  → Conversion needed: vol→mass
  → Action: Add density for INGR_01091 + FORM_SEEDS
```

### 3. Multi-Ingredient Lines
Line contains "or" or "and" (multiple ingredients).
**Action:** Split into separate lines in Stage 1

Example:
```
Recipe 127, Line 3: "coconut or coconut flakes"
  → Action: Split into separate ingredient lines
```

### 4. Unrecognized Units
Unit not in synonym dictionary.
**Action:** Add to `UNIT_SYNONYMS` in `config.py`

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Input/Output files
INPUT_FILE = "your_stage1_data.jsonl"
OUTPUT_FILE = "stage2_output.jsonl"
ERROR_TXT_FILE = "stage2_errors.txt"
ERROR_JSON_FILE = "stage2_errors.json"

# Reference tables
INGREDIENT_TABLE = "Ingredient_Table_Populated_Master_251130.xlsx"
FORM_TABLE = "Form_Table_Populated_Complete.xlsx"
# ... etc

# Matching thresholds
FUZZY_MATCH_THRESHOLD_ACCEPT = 0.92
FUZZY_MATCH_THRESHOLD_REVIEW = 0.80

# Precision
DECIMAL_PRECISION = 6
```

## 📈 Performance Stats

From test run (69 ingredient lines):
- **Total processed:** 115 ingredients
- **Successful:** 13 (11.3%)
- **Failed:** 102 (88.7%)

**Error breakdown:**
- Missing ingredients: 33
- Missing densities: 8
- Parsing failures: 56
- Multi-ingredient lines: 5

*Note: Low success rate is expected for initial run. Add missing ingredients and densities to improve.*

## 🧪 Testing Individual Modules

Each module can be tested independently:

```bash
# Test quantity parser
python step2_quantity_parser.py

# Test unit normalizer
python step3_unit_normalizer.py

# Test ingredient extractor
python step5_ingredient_linking.py
```

## 📝 Adding Missing Data

### Adding Ingredients
1. Open `Ingredient_Table_Populated_Master.xlsx`
2. Add new row with:
   - `ingredient_id`: INGR_XXXXX (next available)
   - `primary_name`: Canonical name
   - `aliases`: Semicolon-separated alternatives
   - `category`: Food category
   - `default_form_id`: Default form (e.g., FORM_WHOLE)
3. Save and rerun processor

### Adding Densities
1. Open `Density_Table_Populated__Final.xlsx`
2. Add new row with:
   - `density_id`: DENS_XXXXX (next available)
   - `ingredient_id`: From ingredient table
   - `form_id`: From form table
   - `g_per_mL`: Density value (weigh 1 cup, convert to g/mL)
   - `source_name`: Where you got the data
3. Save and rerun processor

## 🎯 Expected Workflow

1. **First run:** Many errors (missing ingredients/densities)
2. **Add missing data:** Update Excel reference files
3. **Second run:** Fewer errors
4. **Iterate:** Keep adding missing data until success rate is acceptable
5. **Production:** Process all recipes in batch

## 🔍 Troubleshooting

### "FileNotFoundError: Ingredient table not found"
- Ensure Excel files are in `/mnt/project/` directory
- Or update `base_path` in `config.py`

### "No module named 'openpyxl'"
```bash
pip install openpyxl
```

### High failure rate
- **Normal for first run!**
- Check `stage2_errors.txt` for specific issues
- Add missing ingredients and densities
- Rerun processor

### "PARSE_FAILED" errors
- Check `qty_value_original` in Stage 1 data
- Ensure quantities are properly extracted
- May need to improve Stage 1 parsing

## 📞 Support

For questions or issues:
1. Check error reports in `stage2_errors.txt`
2. Review this README
3. Examine test outputs in `stage2_output.jsonl`
4. Check individual module tests

## 🔮 Future Enhancements

- [ ] Package parsing (Step 4)
- [ ] Batch processing optimization
- [ ] Firebase integration
- [ ] Web UI for error review
- [ ] Auto-suggestion for missing ingredients
- [ ] Confidence scoring improvements

---

**Version:** 1.0  
**Last Updated:** November 27, 2024  
**Created for:** Recipe ingredient canonicalization project
