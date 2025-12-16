# 📐 NutriLiv Recipe Plan Architecture Analysis

## 🔍 Current System Overview

Generated: December 14, 2024

---

## 📂 Directory Structure

```
lib/recipe_plan/
├── models/
│   ├── meal_plan_model.dart    # MealPlan, DayMealPlan, MealSlot
│   └── recipe_model.dart        # Recipe
├── services/
│   ├── meal_plan_service.dart   # Core meal plan generation & serving calculations
│   ├── recipe_service.dart      # Recipe fetching & ingredient benefits
│   ├── grocery_list_service.dart # Grocery aggregation & conversions
│   ├── recipe_scoring_service.dart
│   ├── tea_scoring_service.dart
│   ├── juice_scoring_service.dart
│   ├── gemini_integration_service.dart
│   ├── meal_plan_cache_service.dart
│   └── recipe_cache_service.dart
└── widgets/
    ├── meal_plan_widget.dart
    ├── recipe_details_screen.dart
    ├── recipe_detail_edit_screen.dart
    ├── grocery_list_screen.dart
    ├── recipe_swap_screen.dart
    ├── recipe_swap_detail_screen.dart
    ├── edit_meal_plan_screen.dart
    ├── past_plans_screen.dart
    ├── view_old_meal_plan_screen.dart
    └── liked_disliked_recipes_screen.dart
```

---

## 📊 Data Models

### Recipe Model
```dart
class Recipe {
  final String id;
  final String? recipeTitle;
  final String? ingredientsList;     // ⚠️ CURRENT: String format (comma-separated)
  final String? ingredientsClean;    // Used for display
  final String? mealPlanning;        // e.g., "Breakfast,Lunch"
  final String? mainOrSide;          // "Main" or "Side"
  final String? cuisine;
  final String? dietPlan;
  final int? servings;               // ⚠️ Base servings from recipe
  final Map<String, dynamic>? nutritionInfo; // calories, carbs, fats, proteins
  final List<String>? allergens;
  ...
}
```

**Key Issue:** `ingredientsList` is a STRING, not structured data with quantities!

---

### MealPlan Model
```dart
class MealPlan {
  final String id;
  final String userId;
  final DateTime startDate;
  final DateTime endDate;
  final List<DayMealPlan> days;
  final Map<String, dynamic>? userPreferences;
  final Map<String, List<String>>? groceryItems;      // ⚠️ String-based aggregation
  final Map<String, List<String>>? purchaseFromStore; // ⚠️ String-based store items
  ...
}
```

---

### MealSlot Model (THE CRITICAL ONE!)
```dart
class MealSlot {
  final String mealType;                              // "Breakfast", "Lunch", etc.
  
  // NEW: 3-recipe structure
  final Recipe? mainRecipe;
  final String? mainRecipeId;
  final Recipe? sideRecipe1;
  final String? sideRecipe1Id;
  final Recipe? sideRecipe2;
  final String? sideRecipe2Id;
  
  // OLD: Backward compatibility
  final Recipe? recipe;
  final String? recipeId;
  
  // ⚠️ CURRENT: Serving calculations
  final Map<String, double>? userServings;            // {"main": 1.5, "side1": 0.5}
  final Map<String, double>? additionalPersonServings;
  final Map<String, double>? totalServings;           // Final combined servings
  
  // ⚠️ CRITICAL: String-based ingredient recalculations!
  final Map<String, String>? updatedIngredients;      // {"main": "recalculated list"}
  
  final bool isCompleted;
  final DateTime? completedAt;
  final String? notes;
  final double? portionServings;  // DEPRECATED
  ...
}
```

**Key Discovery:** `updatedIngredients` is a STRING-BASED recalculation! Not SI units.

---

## 🔄 Current Data Flow

### 1️⃣ **Meal Plan Generation**
**File:** `meal_plan_service.dart` → `generateWeeklyMealPlan()`

```
1. Get user preferences (diet, meal types, people count)
   ↓
2. Check if recipe scoring needed (Firebase function)
   ↓
3. Fetch pre-scored recipes from recipes_with_scores collection
   ↓
4. Apply variety patterns (predictable vs variety preference)
   ↓
5. Create DayMealPlan with MealSlots
   ↓
6. Save to Firebase
   ↓
7. **START BACKGROUND SERVING CALCULATIONS** ← KEY STEP!
```

---

### 2️⃣ **Serving Size Calculations**
**File:** `meal_plan_service.dart` → `calculateAndStoreServingSizes()`

**THIS IS WHERE THE MAGIC HAPPENS!**

```dart
// 1. Get user's target calories (from user preferences)
final userTargetCalories = userPreferences['recipe_target_calories']; // e.g., 600

// 2. Get additional people count per meal type
final additionalPeopleByMeal = {
  "Breakfast": 2,
  "Lunch": 1,
  "Dinner": 3
};

// 3. For each meal:
//    A. Calculate USER servings to hit target calories (-3% to +10%)
final userServings = calculateMealServings(meal, userTargetCalories);
// Returns: {"main": 1.5, "side1": 0.5, "side2": 1.0}

//    B. Calculate ADDITIONAL PERSON servings (always 700 cal target)
final additionalPersonServings = calculateMealServings(meal, 700.0);
// Returns: {"main": 2.0, "side1": 1.0, "side2": 1.5}

//    C. Calculate TOTAL servings (user + additionalPeople * additionalPersonServings)
final totalServings = userServings + (additionalPeopleByMeal[mealType] * additionalPersonServings);
// Returns: {"main": 5.5, "side1": 2.5, "side2": 4.0}

// 4. **⚠️ RECALCULATE INGREDIENTS AS STRINGS!**
final updatedIngredients = calculateUpdatedIngredients(meal);
// Returns: {"main": "2.5 cups flour\n3 eggs\n1.5 tbsp butter", ...}

// 5. Update MealSlot with new data
mealSlot.userServings = userServings;
mealSlot.additionalPersonServings = additionalPersonServings;
mealSlot.totalServings = totalServings;
mealSlot.updatedIngredients = updatedIngredients; // ← STRING LISTS!

// 6. Save back to Firebase
```

**Key Algorithm:**
```dart
Map<String, double> calculateMealServings(MealSlot meal, double targetCalories) {
  // Uses iterative adjustment to hit target calories (-3% to +10% range)
  // Adjusts side dishes first (by ±0.5), then main dish
  // Returns servings map when total calories are in acceptable range
}
```

---

### 3️⃣ **Ingredient Recalculation** ⚠️ **THIS IS CRITICAL!**
**File:** `meal_plan_service.dart` → `calculateUpdatedIngredients()`

**Current Process:**
```dart
String _recalculateRecipeIngredients(Recipe recipe, double multiplier) {
  // 1. Split ingredientsList string by comma
  final originalIngredients = recipe.ingredientsList!.split(',');
  
  // 2. For each ingredient STRING:
  final updatedIngredients = originalIngredients.map((ingredient) {
    // Parse "1/2 cup flour" → extract "0.5" and "cup"
    final parsed = _parseIngredientQuantity(ingredient);
    
    // Multiply: 0.5 × 2.5 = 1.25
    final newQuantity = parsed['quantity'] * multiplier;
    
    // Convert back to fraction: 1.25 → "1 1/4"
    final friendlyQuantity = _convertToFriendlyQuantity(newQuantity);
    
    // Reconstruct: "1 1/4 cup flour"
    return '$friendlyQuantity ${parsed['unit']} ${parsed['ingredient']}';
  });
  
  // 3. Join back into string with newlines
  return updatedIngredients.join('\n');
}
```

**Example:**
```
Original: "1/2 cup flour, 2 eggs, 1 tbsp butter"
Multiplier: 2.5
Result: "1 1/4 cups flour\n5 eggs\n2 1/2 tablespoons butter"
```

**⚠️ Problems:**
- String parsing is fragile (breaks with complex ingredients)
- No SI conversion - stays in original units
- No density awareness
- No proper unit consolidation

---

### 4️⃣ **Grocery List Generation**
**File:** `grocery_list_service.dart` → `generateGroceryList()`

**Current Process:**
```dart
Future<Map<String, List<String>>> generateGroceryList(MealPlan mealPlan) async {
  Map<String, List<String>> groceryItems = {};
  
  // For each day → each meal → each recipe:
  for (day in mealPlan.days) {
    for (meal in day.meals) {
      // Use updatedIngredients if available, else original ingredientsList
      String ingredientsList = meal.updatedIngredients?['main'] 
          ?? meal.mainRecipe!.ingredientsList;
      
      // Parse each ingredient line
      for (ingredient in ingredientsList.split('\n')) {
        // Extract: "2.5 cups flour" → name="flour", quantity="2.5 cups"
        final parsed = _parseIngredient(ingredient);
        
        // Aggregate by ingredient name
        if (groceryItems.containsKey(parsed['name'])) {
          groceryItems[parsed['name']].add(parsed['quantity']);
        } else {
          groceryItems[parsed['name']] = [parsed['quantity']];
        }
      }
    }
  }
  
  // Result: {"flour": ["2.5 cups", "1.5 cups", "3 cups"], ...}
  return groceryItems;
}
```

**Then:**
1. `convertFractionsToDecimals()` → "1 1/2 cups" → "1.5 cups"
2. `convertToGrams()` → "1.5 cups flour" → "180 grams flour" (uses hardcoded conversions!)
3. `aggregateSimilarUnits()` → Sums grams for same ingredient
4. `convertGramsToPurchaseOptions()` → "450g flour" → "500g bag of all-purpose flour"

---

## 🎯 Display Flow

### Recipe Details Screen
**File:** `recipe_details_screen.dart`

```dart
// Shows ingredient list from updatedIngredients OR original
String displayIngredients = widget.mealSlot.updatedIngredients?['main']
    ?? widget.mealSlot.mainRecipe!.ingredientsList;

// Splits by newline and displays each line
final ingredientLines = displayIngredients.split('\n');
ListView(
  children: ingredientLines.map((line) => Text(line)).toList(),
);
```

**Current Display:** Shows recalculated STRING values (e.g., "2 1/2 cups flour")

---

### Grocery List Screen
**File:** `grocery_list_screen.dart`

```dart
// Displays aggregated grocery items from meal plan
Map<String, List<String>> groceryItems = mealPlan.groceryItems;

// Shows each ingredient with its quantities
groceryItems.forEach((ingredient, quantities) {
  // Display: "Flour - 450 grams"
  Text('$ingredient - ${quantities.join(", ")}');
});

// Also shows purchaseFromStore
Map<String, List<String>> storeItems = mealPlan.purchaseFromStore;
```

---

## 🔥 Critical Issues for New System

### 1. **No Canonical SI Storage**
- Recipes store ingredients as strings: `"1/2 cup flour, 2 eggs"`
- NO `ingredients_canonical` field with SI units!
- **Impact:** Can't do numeric aggregation, unit conversion is string-based

### 2. **String-Based Serving Recalculation**
- `calculateUpdatedIngredients()` multiplies string quantities
- Fragile parsing: `"1 (1-inch) piece fresh ginger"` → ???
- No density awareness for mass ↔ volume conversions

### 3. **String-Based Grocery Aggregation**
- Grocery list aggregates by string matching: `"flour"` → `["2.5 cups", "1.5 cups"]`
- Then converts strings to grams using HARDCODED conversion factors!
- **No canonical data used!**

### 4. **Hardcoded Unit Conversions**
**File:** `grocery_list_service.dart` lines ~600-900

```dart
double _convertToGrams(double quantity, String unit, String ingredientName) {
  // ⚠️ HARDCODED MASS CONVERSIONS
  if (unit == 'ounces') return quantity * 28.35;
  if (unit == 'pounds') return quantity * 453.592;
  
  // ⚠️ HARDCODED VOLUME → MASS (assumes densities!)
  if (unit == 'cups') {
    if (ingredientName.contains('flour')) return quantity * 120;  // ← HARDCODED!
    if (ingredientName.contains('sugar')) return quantity * 200;  // ← HARDCODED!
    return quantity * 240; // Default to water density
  }
  
  if (unit == 'tablespoons') return quantity * 15;
  if (unit == 'teaspoons') return quantity * 5;
  // ... MORE HARDCODED VALUES
}
```

**This is exactly what we need to replace with canonical data!**

---

## ✅ What Works Well

### 1. **Serving Size Calculation Algorithm**
- The calorie-based iterative adjustment is SOLID
- Can be reused in new system

### 2. **3-Recipe Structure**
- `MealSlot` already supports main + 2 sides
- Future-proof architecture

### 3. **Background Processing**
- Serving calculations run async after meal plan creation
- Good UX pattern to keep

### 4. **Firebase Integration**
- Everything saves to Firebase properly
- Good separation of concerns

---

## 🚀 Path Forward (New System)

### Phase 1: Add Canonical Data to Firebase
```
recipes_with_scores/
  {recipe_id}/
    ingredients_list: "1/2 cup flour, 2 eggs"  # Keep for display
    ingredients_canonical: [                     # NEW!
      {
        ingredient_id: "INGR_00123",
        canonical_qty: 60.0,
        canonical_unit: "g",
        resolved_form_id: "FORM_GROUND",
        ...
      },
      {
        ingredient_id: "INGR_00456",
        canonical_qty: 2.0,
        canonical_unit: "ea",
        ...
      }
    ]
```

### Phase 2: Create New Services (recipe_plan_v2/)
```
lib/recipe_plan_v2/
├── services/
│   ├── reference_data_service.dart       # Download & cache from Firebase
│   ├── ingredient_renderer_service.dart  # SI → Display units
│   └── canonical_meal_plan_service.dart  # Uses canonical data
└── widgets/
    └── test_canonical_display.dart       # Test screen
```

### Phase 3: Parallel Integration
- Keep `meal_plan_service.dart` as-is (OLD SYSTEM UNTOUCHED)
- Add feature flag: `useCanonicalSystem`
- Test with separate button

### Phase 4: Gradual Rollout
- You test first
- Beta users
- Full migration when stable

---

## 📝 Key Takeaways

1. **Current system is STRING-BASED throughout**
   - Ingredients stored as strings
   - Serving calculations manipulate strings
   - Grocery aggregation matches strings
   - Unit conversions hardcoded

2. **updatedIngredients is NOT canonical!**
   - It's recalculated STRING values
   - Used for display and grocery list
   - This is what we need to replace

3. **Grocery service has the logic we need to replicate**
   - Ingredient parsing
   - Unit conversions (but hardcoded)
   - Aggregation logic
   - Store purchase options

4. **Safe migration path exists**
   - New field: `ingredients_canonical`
   - New directory: `recipe_plan_v2/`
   - Feature flag for testing
   - OLD SYSTEM KEEPS WORKING

---

## 🎯 Next Steps

1. ✅ Understanding complete (THIS DOCUMENT)
2. ⏳ Upload canonical data to Firebase (reference tables)
3. ⏳ Build `reference_data_service.dart` (download & cache)
4. ⏳ Build `ingredient_renderer_service.dart` (SI → display)
5. ⏳ Create test screen to verify
6. ⏳ Integrate into meal plan flow

---

**Ready to proceed when you are!** 🚀

