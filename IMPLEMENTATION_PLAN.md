# 🎯 Canonical Ingredient System - Implementation Plan

## 📋 Overview

**Goal:** Convert NutriLiv app from string-based ingredients to canonical SI system with proper unit conversion and display policies.

**Timeline:** No rush - build it right, step by step  
**Current Status:** ✅ Reference data uploaded to Firebase  
**Risk Level:** Medium (touching core features)  
**Strategy:** Incremental, testable, with fallbacks

---

## 🗺️ The Big Picture

### What We're Changing:

**FROM (Current):**
```
Recipe stores: "2 celery stalks, 1 tbsp peanut butter" (string)
              ↓
Display:      "2 celery stalks, 1 tbsp peanut butter" (same string)
```

**TO (New System):**
```
Recipe stores: canonical_qty: 2.0, canonical_unit: "ea" (numbers!)
              ↓
Download reference data (weekly)
              ↓
Display:      "2 celery stalks" (US) or "2 ea celery" (others)
```

---

## 📊 Phase Breakdown

### ✅ **Phase 0: Foundation** (COMPLETE!)
- [x] Stage 2 processor working (86% success rate)
- [x] Excel files → JSON export script
- [x] Upload script to Firebase
- [x] Reference data in Firebase

**Status:** ✅ DONE

---

### 🔄 **Phase 1: Recipe Data Migration** (Python - Backend)

**Goal:** Convert 300 recipes to canonical format

**Complexity:** ⭐⭐ (Medium - mostly automated)  
**Time Estimate:** 2-3 hours  
**Risk:** Low (doesn't touch production yet)

#### Tasks:

**1.1 Export Recipe Data from Firebase**
- Create script to download all recipes
- Convert `ingredients_list` to Stage 1 format
- Generate 300 JSONL files (one per recipe)

**1.2 Process All Recipes Through Stage 2**
- Run Stage 2 processor on each recipe
- Review error rates
- Add missing ingredients/densities if needed
- Target: 85%+ success rate

**1.3 Create Upload Script for Canonical Data**
- Read Stage 2 outputs
- Format for Firebase
- Upload as `ingredients_canonical` field (NEW field, keep old!)
- Don't replace existing data yet

**Deliverables:**
- [ ] All 300 recipes have `ingredients_canonical` field
- [ ] Old `ingredients_list` still intact (fallback)
- [ ] Python scripts committed to repo

**Checkpoint:** Test in Firebase Console - verify data looks good

---

### 🏗️ **Phase 2: Flutter Foundation Services** (Flutter - New Code)

**Goal:** Build core services WITHOUT touching existing features

**Complexity:** ⭐⭐⭐ (Medium-High - new architecture)  
**Time Estimate:** 1-2 days  
**Risk:** Low (new files, don't modify existing)

#### Tasks:

**2.1 Create Reference Data Service**
```dart
lib/recipe_plan/services/reference_data_service.dart
```
- Download from Firebase (ingredients, policies, densities, constants)
- Cache in local storage (SharedPreferences or Hive)
- Check timestamp for updates
- Provide lookup methods

**2.2 Create Data Models**
```dart
lib/recipe_plan/models/reference_data_models.dart
```
- Ingredient model
- DisplayPolicy model
- Density model
- ConversionConstants model

**2.3 Create Unit Converter Utility**
```dart
lib/recipe_plan/services/unit_converter_service.dart
```
- Convert g → oz, lb, kg
- Convert mL → cup, tsp, tbsp, fl oz, L
- Use conversion constants from reference data
- Pure math functions (easy to test)

**2.4 Create Rendering Service**
```dart
lib/recipe_plan/services/ingredient_renderer_service.dart
```
- 9-step rendering pipeline
- Scale for servings
- Apply display policies
- Convert units
- Round properly
- Handle small-measure rule

**Deliverables:**
- [ ] 4 new service files (well-tested)
- [ ] Unit tests for converters
- [ ] Sample usage examples
- [ ] No existing code modified yet

**Checkpoint:** Test services independently - verify conversions match expected values

---

### 🔌 **Phase 3: Integration (Non-Critical Paths)** (Flutter - Low Risk)

**Goal:** Integrate new services in non-critical areas first

**Complexity:** ⭐⭐ (Medium)  
**Time Estimate:** 1 day  
**Risk:** Low (test features only)

#### Tasks:

**3.1 Create Test Screen**
```dart
lib/recipe_plan/widgets/ingredient_renderer_test_screen.dart
```
- Test ingredient rendering
- Compare old vs new display
- Verify all edge cases
- User can toggle between old/new

**3.2 Update Recipe Detail Screen (View Only)**
```dart
lib/recipe_plan/widgets/recipe_details_screen.dart
```
- Add "Canonical View" toggle button
- Show ingredients using new renderer
- Keep old view as default (safe!)
- Users can compare both

**Deliverables:**
- [ ] Test screen working
- [ ] Can view recipes in canonical format
- [ ] Old functionality still works (untouched)
- [ ] Visual QA passed

**Checkpoint:** You and team test the new display - verify it looks correct

---

### ⚙️ **Phase 4: Integration (Meal Plan Generation)** (Flutter - Medium Risk)

**Goal:** Use canonical data for meal plan generation

**Complexity:** ⭐⭐⭐⭐ (High - core feature)  
**Time Estimate:** 2-3 days  
**Risk:** Medium (touches meal plan generation)

#### Tasks:

**4.1 Update Meal Plan Service**
```dart
meal_plan_service.dart (MODIFY)
```
- On meal plan generation: Download reference data first
- Store canonical ingredients with meal plan
- Calculate scaled quantities properly (math on numbers!)
- Keep old format as fallback

**4.2 Add Serving Scaler**
```dart
lib/recipe_plan/services/serving_scaler_service.dart (NEW)
```
- Scale canonical quantities for different servings
- Handle ranges properly
- Preserve precision

**4.3 Update Meal Plan Model**
```dart
meal_plan_model.dart (MODIFY)
```
- Add reference_data_version field
- Add cached_reference_data (optional)
- Keep backward compatibility

**Deliverables:**
- [ ] Meal plans use canonical data
- [ ] Serving scaling works correctly
- [ ] Old meal plans still load (backward compatible)
- [ ] Test meal plan generated successfully

**Checkpoint:** Generate test meal plan - verify all ingredients display correctly

---

### 🛒 **Phase 5: Integration (Grocery Lists)** (Flutter - High Risk)

**Goal:** Aggregate grocery lists using canonical data

**Complexity:** ⭐⭐⭐⭐⭐ (Highest - complex aggregation)  
**Time Estimate:** 2-3 days  
**Risk:** High (core feature users depend on)

#### Tasks:

**5.1 Update Grocery List Service**
```dart
grocery_list_service.dart (MAJOR REWRITE)
```
- Aggregate using canonical quantities (sum numbers!)
- Convert to display units at the end
- Group by ingredient_id (not string names)
- Handle different forms (chopped vs whole)
- Apply pantry rules on canonical data

**5.2 Update Grocery List Screen**
```dart
grocery_list_screen.dart (MODIFY)
```
- Display using rendered ingredients
- Show proper units based on user locale
- Keep checkbox functionality
- Add unit conversion toggle (optional)

**Deliverables:**
- [ ] Grocery lists aggregate correctly
- [ ] Quantities sum properly ("1 cup + 2 tbsp" works!)
- [ ] Display matches user's region
- [ ] Existing features (checkboxes, editing) still work

**Checkpoint:** Generate full meal plan → grocery list → verify totals are correct

---

### 🎨 **Phase 6: UI Polish & Edge Cases** (Flutter - Low Risk)

**Goal:** Handle all edge cases and improve UX

**Complexity:** ⭐⭐ (Medium)  
**Time Estimate:** 1-2 days  
**Risk:** Low

#### Tasks:

**6.1 Edge Case Handling**
- Zero quantities → show minimum
- Ranges ("1-2 cups") → display properly
- Approximations ("about 1 tsp") → show ~
- Special units ("to taste") → handle gracefully

**6.2 User Settings**
- Add unit system toggle (Metric/Standard)
- Save preference to Firebase
- Apply on all ingredient displays

**6.3 Error Handling**
- Fallback to old strings if canonical missing
- Show warning if reference data outdated
- Graceful degradation

**Deliverables:**
- [ ] All edge cases handled
- [ ] User can choose unit system
- [ ] Graceful fallbacks work
- [ ] Error messages helpful

---

### 🧪 **Phase 7: Testing & Rollout** (Testing)

**Goal:** Comprehensive testing before full rollout

**Complexity:** ⭐⭐⭐ (Medium-High)  
**Time Estimate:** 3-5 days  
**Risk:** Critical (production stability)

#### Tasks:

**7.1 Unit Testing**
- Test all converters (50+ test cases)
- Test rendering pipeline (100+ test cases)
- Test aggregation logic
- Test caching/invalidation

**7.2 Integration Testing**
- Generate meal plans (10+ different scenarios)
- Test serving scaling (1x, 2x, 4x)
- Test grocery lists (multiple recipes)
- Test US vs non-US users

**7.3 Beta Testing**
- Deploy to TestFlight / Internal Testing
- Your team tests thoroughly
- Collect feedback
- Fix issues

**7.4 Gradual Rollout**
- Release to 10% of users
- Monitor for issues
- Increase to 50%
- Full rollout if stable

**Deliverables:**
- [ ] All tests passing
- [ ] Team approved
- [ ] Beta feedback addressed
- [ ] Production rollout successful

---

## 📊 Summary

### Total Effort Estimate:
- **Python work:** ~1 day
- **Flutter work:** ~7-10 days
- **Testing:** ~3-5 days
- **Total:** ~2-3 weeks of focused work

### Phases Ranked by Risk:
1. ✅ Phase 0, 1, 2: Low risk (foundation)
2. ⚠️ Phase 3, 4: Medium risk (integration)
3. 🔴 Phase 5: High risk (grocery lists)
4. ✅ Phase 6, 7: Controlled risk (polish & testing)

### Can We Reduce Risk?

**YES!** By doing this:
1. **Feature flag** - toggle canonical system on/off
2. **Parallel systems** - run old & new simultaneously
3. **Gradual migration** - phase out old system slowly
4. **Rollback plan** - can revert if issues

---

## 🎯 Dependencies

```
Phase 0 ✅
  ↓
Phase 1 (Recipe migration) → Must complete first
  ↓
Phase 2 (Flutter services) → Can build in parallel
  ↓
Phase 3 (Test integration) → Low risk testing
  ↓
Phase 4 (Meal plan) → Medium risk
  ↓
Phase 5 (Grocery) → Highest risk, do last
  ↓
Phase 6 (Polish) → After core works
  ↓
Phase 7 (Testing) → Final step before rollout
```

---

## 🤔 What I Need From You:

### 1. **Phase 1 Requirements:**
   - Do you have all 300 recipes' `ingredients_list` accessible?
   - Can I download them programmatically?
   - Or should I create a Firebase download script?

### 2. **Timeline:**
   - Want to do this in one stretch (2-3 weeks)?
   - Or slowly over time (1 phase per week)?

### 3. **Testing Strategy:**
   - Can you test each phase before next one?
   - Do you have test Firebase project or use production?
   - Who will do QA testing?

### 4. **Risk Tolerance:**
   - Comfortable with parallel systems (old + new)?
   - Or full migration at once?
   - Want feature flag to toggle on/off?

---

## 💬 Let's Discuss:

**Tell me:**
1. Is this plan clear?
2. What concerns you most?
3. Which phase seems hardest?
4. Ready to start Phase 1?

No coding yet - let's finalize the plan! 🎯
