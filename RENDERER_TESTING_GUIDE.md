# Ingredient Renderer Testing Guide

**Created:** December 14, 2024  
**Status:** Ready for Testing 🧪

---

## ✅ What We Built Today

### **Phase 1: Recipe Grouping** ✅
- **File:** `test_recipes_canonical.json`
- **Contents:** 11 recipes, 108 ingredient lines in canonical SI format
- **Structure:** Grouped by `recipe_id` with all metadata

### **Phase 2: Full Renderer Service** ✅
- **File:** `/lib/recipe_plan_v2/services/ingredient_renderer_service.dart`
- **Features:**
  - Serving scaling (multiply quantities)
  - Display mode determination (mass/volume/count)
  - Small-measure rule (spices < 15g → tsp/tbsp)
  - Complete rounding rules from spec
  - Fraction formatting (⅛, ¼, ½, ¾, etc.)
  - Unit ladder (tsp→tbsp→cup→quart)
  - Mass ↔ Volume conversion via density
  - Ingredient localization
  - Metric vs. Standard (US) support

### **Phase 3: Visual Test Screen** ✅
- **File:** `/lib/recipe_plan_v2/widgets/test_renderer_screen.dart`
- **Features:**
  - 6 hardcoded test ingredients
  - Toggle: US (Standard) vs. Metric
  - Toggle: Country (🇺🇸 US, 🇬🇧 GB, 🇨🇦 CA)
  - Slider: Serving multiplier (0.5× to 4.0×)
  - Live rendering updates
  - Shows canonical vs. display format side-by-side

---

## 📱 How to Test

### **Step 1: Access Test Screens**

Open your app and go to **Profile Settings**. You'll see two new buttons in the "General" section:

1. **🧪 Test Reference Data** (Cyan)
   - Verifies data download from Firebase
   - Shows ingredient counts, densities, etc.

2. **🎨 Test Ingredient Renderer** (Purple) ← **THIS IS THE NEW ONE!**
   - Visual rendering test screen
   - Try different countries and servings

### **Step 2: Test Rendering**

Tap **🎨 Test Ingredient Renderer**

**What You'll See:**
- 6 test ingredients (flour, milk, cinnamon, banana, sugar, olive oil)
- Each shows:
  - **Canonical:** `150 g` (what's stored in database)
  - **Display:** `1 cup flour` (what users see)

**Try These Tests:**

#### **Test 1: Unit System Toggle**
1. Set to **US (Standard)**
   - Flour should show as cups/oz
   - Milk should show as cups
   - Cinnamon should show as tsp (small-measure rule!)
2. Set to **Metric**
   - Everything should show as g/mL/L
   - Cinnamon still might show as tsp if < 15g

#### **Test 2: Country Toggle**
1. Try **🇺🇸 US**
   - Milk: prefer volume (cups)
2. Try **🇬🇧 GB**
   - Milk: might prefer mass (grams) if policy has locale override

#### **Test 3: Serving Multiplier**
1. Set slider to **× 0.5** (half the recipe)
   - All quantities should halve
   - Unit might change (e.g., 1 cup → ½ cup)
2. Set slider to **× 2.0** (double the recipe)
   - All quantities should double
   - Unit might switch (e.g., 1 cup → 2 cups, or 150 g → 300 g)
3. Set slider to **× 3.0**
   - Watch for unit ladder: tsp → tbsp → cup transitions

#### **Test 4: Fractions**
- Look for: ⅛, ¼, ⅓, ½, ⅝, ⅔, ¾, ⅞
- US mode should show fractions
- Metric mode should show decimals

---

## 🔍 What to Look For

### **✅ Good Signs:**
- Quantities scale correctly with serving multiplier
- Units switch at thresholds (e.g., 1000g → 1 kg)
- Fractions display properly in US mode
- Small spices (< 15g) show as tsp/tbsp even in Metric
- Counts (banana) always show as numbers

### **❌ Potential Issues:**
- **"Error: ..."** - Missing ingredient/density in Firebase
- **"[INGR_xxxxx]"** - Fallback rendering (ingredient not found)
- **Incorrect quantities** - Rounding or conversion bug
- **Wrong units** - Display policy not working
- **No fractions** - Fraction formatting not working

---

## 🐛 If You Find Issues

### **Issue: Ingredient Not Found**
```
Display: [INGR_00123]
```
**Fix:** That ingredient ID is missing from Firebase. You can:
1. Check if it's in `Ingredient_Table_Populated_Master 251202.xlsx`
2. If not, add it
3. Re-run `export_reference_data.py`
4. Re-run `upload_reference_data_to_firebase.js`

### **Issue: Missing Density**
```
Error: No density found for INGR_00456
```
**Fix:** Add density to `Density_Table_Populated - Final 251202.xlsx`:
- Ingredient ID: `INGR_00456`
- Form ID: (if applicable)
- Density (g/mL): (value)
- Then re-export and re-upload

### **Issue: Rendering Looks Wrong**
- Check `Ingredient Display Policy 251202.xlsx`
- Verify the ingredient has a policy entry
- Check `default_display_rule` and `locale_overrides`

---

## 📊 Test Ingredients Explained (UPDATED)

| Ingredient | Canonical | Expected Display (US) | Expected Display (Metric) | Notes |
|------------|-----------|----------------------|---------------------------|-------|
| Water | 1892.7 mL | ~8 cups | 1.89 L | Tests L/quart conversion |
| Coconut Milk | 122.5 g | ~½ cup | 122.5 g or 0.12 kg | Tests mass/volume policy |
| Cinnamon | 0.33 g | ~⅛ tsp | ~⅛ tsp | Small-measure rule! |
| Chia Seeds | 118.3 mL | ~½ cup | 118.3 mL | Volume → Volume |
| Coconut Sugar | 10.6 g | ~2 tsp or 0.4 oz | 10.6 g | Tests rounding |
| Blackberries | 36.0 g | ~¼ cup | 36.0 g | Tests mass/volume |
| Goji Berries | 10.0 g | ~2 tsp | 10.0 g | Tests fractions |

---

## 🎯 Next Steps After Testing

Once you confirm rendering works:

1. ✅ **Test with real recipe data**
   - Upload `test_recipes_canonical.json` to Firebase
   - Create a screen to display actual recipes

2. ✅ **Integrate into meal plans**
   - Update meal plan generation to use canonical data
   - Replace string-based ingredient parsing

3. ✅ **Update grocery list**
   - Aggregate canonical SI quantities (numbers, not strings!)
   - Render for display using renderer service

4. ✅ **Add user preference UI**
   - Let users select Metric vs. Standard
   - Store preference in user profile

5. ✅ **Batch process remaining recipes**
   - Run all 300 recipes through Stage 2
   - Upload canonical data to Firebase
   - Deploy!

---

## 💬 Questions to Consider

1. **Does rendering look correct for all 6 test ingredients?**
2. **Do fractions display nicely in US mode?**
3. **Does the small-measure rule work for cinnamon?**
4. **Do quantities scale correctly with serving multiplier?**
5. **Do units switch at the right thresholds?**

---

## 🚀 You're Almost There!

**What's working:**
- ✅ Reference data downloads from Firebase
- ✅ Caching works (instant on 2nd load)
- ✅ Renderer service is complete
- ✅ Test UI is functional

**What's next:**
- 🔄 Test rendering in the app
- 🔄 Fix any data issues (missing ingredients/densities)
- 🔄 Integrate into meal plan generation
- 🔄 Update grocery list to use canonical data

---

**Take it slow, test thoroughly, and report back!** 🐢

