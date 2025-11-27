# How to Fix Common Errors - Step by Step Guide

This guide shows you **exactly** how to fix the errors in your test run.

## 🎯 Your Current Situation

First run results:
- ✓ Successful: 13 (11.3%)
- ✗ Failed: 102 (88.7%)

Main issues:
- **33 missing ingredients** - Need to add to ingredient table
- **8 missing densities** - Need to add to density table  
- **5 multi-ingredient lines** - Need to split in Stage 1

Let's fix them!

---

## 🔧 Fix #1: Add Missing Ingredients

### Example Error:
```
Recipe 127, Line 8: "1 tsp maca root powder"
  → Candidate name: maca root powder
  → Action: Add ingredient to Ingredient Table
```

### Step-by-Step Fix:

1. **Open** `Ingredient_Table_Populated_Master_251105.xlsx`

2. **Find the last ingredient ID**
   - Scroll to bottom
   - Note last ID (e.g., INGR_00959)

3. **Add new row:**
   ```
   ingredient_id:    INGR_00960
   primary_name:     Maca root powder
   aliases:          maca powder;maca root
   category:         Superfoods
   default_form_id:  FORM_POWDER
   notes_internal:   Added Nov 2024
   created_at:       2024-11-27
   updated_at:       2024-11-27
   ```

4. **Save** the Excel file

5. **Rerun** processor: `python main.py`

6. **Check** - "maca root powder" error should be gone!

### More Examples to Add:

```
INGR_00961: Coconut milk
  aliases: canned coconut milk
  category: Dairy Alternatives
  default_form_id: FORM_CANNED

INGR_00962: Coconut kefir
  aliases: kefir coconut
  category: Dairy Alternatives
  default_form_id: FORM_WHOLE

INGR_00963: Apple juice concentrate
  aliases: concentrated apple juice;apple concentrate
  category: Juices
  default_form_id: FORM_CONCENTRATE

INGR_00964: Nutmeg
  aliases: ground nutmeg
  category: Spices
  default_form_id: FORM_GROUND

INGR_00965: Dinosaur kale
  aliases: lacinato kale;tuscan kale;black kale
  category: Vegetables
  default_form_id: FORM_WHOLE
```

**Pro tip:** Add 10-20 ingredients at once, then rerun. More efficient!

---

## 🔧 Fix #2: Add Missing Densities

### Example Error:
```
Recipe 127, Line 1: "1/2 cup chia seeds"
  → Ingredient: Chia seeds (INGR_01091)
  → Form: FORM_SEEDS
  → Conversion needed: vol→mass
  → Action: Add density for INGR_01091 + FORM_SEEDS
```

### Step-by-Step Fix:

1. **Measure the ingredient:**
   - Take a measuring cup
   - Fill with chia seeds (1 cup)
   - Weigh on kitchen scale (e.g., 170 grams)

2. **Calculate density:**
   ```
   g/mL = grams / milliliters
   g/mL = 170 / 236.588  (1 cup = 236.588 mL)
   g/mL = 0.719
   ```

3. **Open** `Density_Table_Populated__Final_251126.xlsx`

4. **Find last density ID**
   - Scroll to bottom
   - Note last ID (e.g., DENS_00926)

5. **Add new row:**
   ```
   density_id:      DENS_00927
   ingredient_id:   INGR_01091
   form_id:         FORM_SEEDS
   g_per_mL:        0.719
   notes_internal:  Measured 1 cup = 170g
   source_name:     Kitchen measurement - Nov 2024
   updated_at:      2024-11-27
   ```

6. **Save** and **rerun**

### Quick Density References:

If you don't have the ingredient to measure, use these typical values:

```
Flour (FORM_POWDER):         0.528 g/mL
Sugar (FORM_GRANULATED):     0.845 g/mL
Cocoa powder (FORM_POWDER):  0.520 g/mL
Nuts, chopped (FORM_CHOPPED): 0.506 g/mL
Leafy greens (FORM_WHOLE):   0.085 g/mL (loosely packed)
Milk/water (liquids):        1.000 g/mL
Olive oil:                   0.910 g/mL
Honey:                       1.420 g/mL
```

**Important:** Different forms have different densities!
- Flour sifted: 0.450 g/mL
- Flour packed: 0.600 g/mL
- Onion whole: different from chopped!

---

## 🔧 Fix #3: Handle Multi-Ingredient Lines

### Example Error:
```
Recipe 127, Line 3: "coconut or coconut flakes"
  → Action: Split into separate ingredient lines
```

### Step-by-Step Fix:

This error means your **Stage 1 parsing** needs to be updated.

**Option A: Split in Stage 1**
Change your Stage 1 JSONL from:
```json
{
  "ingredient_line_number": 3,
  "ingredient_original_text": "coconut or coconut flakes"
}
```

To two separate lines:
```json
{
  "ingredient_line_number": 3,
  "ingredient_original_text": "coconut"
}
{
  "ingredient_line_number": 4,
  "ingredient_original_text": "coconut flakes"
}
```

**Option B: Choose primary ingredient**
If "or" means "either one works", just pick one:
```json
{
  "ingredient_line_number": 3,
  "ingredient_original_text": "coconut"
}
```

**Note:** This requires going back to your Stage 1 data. Stage 2 can't fix this automatically.

---

## 📊 Tracking Your Progress

### Before Fixes:
```
✓ Successful: 13 (11.3%)
✗ Failed: 102 (88.7%)
```

### After Adding 10 Ingredients:
```
✓ Successful: 25 (21.7%)
✗ Failed: 90 (78.3%)
```

### After Adding Densities:
```
✓ Successful: 35 (30.4%)
✗ Failed: 80 (69.6%)
```

### Target Goal:
```
✓ Successful: 100 (87%)
✗ Failed: 15 (13%)
```

The remaining 13% will be true edge cases that need manual review.

---

## ⚡ Quick Fix Workflow

### Morning Session (30 minutes):
1. Review `stage2_errors.txt`
2. Add 10-15 missing ingredients
3. Add 5-10 densities
4. Rerun processor
5. Note improvement

### Afternoon Session (30 minutes):
1. Review new errors
2. Add 10-15 more ingredients
3. Add 5-10 more densities
4. Rerun
5. Continue

### Result After 1 Day:
- Added ~40 ingredients
- Added ~20 densities
- Success rate: ~60%

### Result After 2-3 Days:
- Added ~100 ingredients
- Added ~50 densities
- Success rate: ~85%

**At 85%, you're ready for production!**

---

## 🎯 Priority Order

Fix errors in this order for fastest improvement:

### Priority 1: Common Ingredients
Add these first (they appear in many recipes):
- Water
- Salt
- Olive oil
- Onion
- Garlic
- Tomato
- Milk
- Butter
- Flour
- Sugar

### Priority 2: Common Spices/Herbs
- Black pepper
- Cumin
- Coriander
- Cinnamon
- Nutmeg
- Basil
- Parsley
- Oregano

### Priority 3: Recipe-Specific Items
- Specialty ingredients
- Exotic spices
- Regional items
- Uncommon variations

---

## 🔍 Troubleshooting

### "I added ingredient but still getting error"
- Check spelling exactly matches
- Check aliases include variations
- Reopen Excel file to confirm save
- Restart Excel if needed

### "Density seems wrong"
- Verify measurement (1 cup = 236.588 mL)
- Check if packed vs loose
- Compare with online sources
- Better to be approximate than missing!

### "Too many errors to fix"
- Focus on top 20 most common
- These will fix 80% of errors
- Build database iteratively
- Don't try to fix everything at once

### "Same error appearing multiple times"
- Fix once, applies to all
- That's why you see multiple of same ingredient
- One fix helps many recipes

---

## 📝 Keep Track

Create a simple log:

```
Nov 27, 2024
-----------
Added: maca root powder, coconut milk, kefir
Densities: chia seeds, cocoa powder
Success rate: 11% → 25%
Time spent: 30 minutes

Nov 28, 2024
-----------
Added: 15 more ingredients
Densities: 10 more items
Success rate: 25% → 45%
Time spent: 45 minutes
```

This helps you see progress and estimate time for remaining work.

---

## ✅ Success Checklist

- [ ] Added top 10 missing ingredients
- [ ] Added corresponding densities
- [ ] Reran processor
- [ ] Success rate improved
- [ ] Reviewed new error report
- [ ] Added another batch
- [ ] Success rate > 50%
- [ ] Added another batch
- [ ] Success rate > 75%
- [ ] Final batch
- [ ] Success rate > 85%
- [ ] Ready for production!

---

**Remember:** Every ingredient you add helps multiple recipes. You're building a reusable database that will serve you for years!

🚀 Start with the top 10, and you'll see immediate improvement!
