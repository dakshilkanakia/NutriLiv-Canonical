#!/usr/bin/env node

/**
 * Upload Canonical Recipes to Firebase
 * 
 * This script:
 * 1. Reads canonical ingredient data from test_recipes_canonical.json
 * 2. Fetches original recipe from recipes_with_scores collection
 * 3. Merges canonical data with original recipe data
 * 4. Uploads to recipes_canonical collection
 * 
 * Usage: node upload_canonical_recipes.js
 */

const admin = require("firebase-admin");
const fs = require("fs");
const path = require("path");

// Initialize Firebase
const serviceAccount = require("/Users/dakshilkanakia/Desktop/Personalized Medicine/secretkey.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

// Input file
const CANONICAL_DATA_FILE = "./test_recipes_canonical.json";

// Collection names
const SOURCE_COLLECTION = "recipes_with_scores";  // Where to fetch original recipes
const TARGET_COLLECTION = "recipes_canonical";    // Where to upload merged recipes

/**
 * Main upload function
 */
async function uploadCanonicalRecipes() {
  console.log("\n" + "=".repeat(80));
  console.log("🚀 UPLOADING CANONICAL RECIPES TO FIREBASE");
  console.log("=".repeat(80) + "\n");

  // Read canonical data
  console.log(`📖 Reading canonical data from: ${CANONICAL_DATA_FILE}`);
  const canonicalData = JSON.parse(fs.readFileSync(CANONICAL_DATA_FILE, "utf-8"));
  const recipeIds = Object.keys(canonicalData);
  
  console.log(`✅ Found ${recipeIds.length} recipes with canonical data\n`);

  let successCount = 0;
  let errorCount = 0;
  const errors = [];

  for (const recipeIdStr of recipeIds) {
    const recipeId = parseInt(recipeIdStr);
    const canonical = canonicalData[recipeIdStr];
    
    console.log(`\n${"─".repeat(80)}`);
    console.log(`📝 Processing Recipe ID: ${recipeId}`);
    console.log(`${"─".repeat(80)}`);

    try {
      // Step 1: Fetch original recipe from recipes_with_scores
      console.log(`   🔍 Fetching original recipe from ${SOURCE_COLLECTION}...`);
      
      const snapshot = await db.collection(SOURCE_COLLECTION)
        .where("recipe_id", "==", recipeId)
        .limit(1)
        .get();

      if (snapshot.empty) {
        throw new Error(`Recipe not found in ${SOURCE_COLLECTION}`);
      }

      const originalDoc = snapshot.docs[0];
      const originalData = originalDoc.data();
      
      console.log(`   ✅ Found: "${originalData.recipe_title || "Unknown"}"`);

      // Step 2: Merge canonical data with original data
      console.log(`   🔄 Merging canonical data...`);
      
      // Note: yield field comes from originalData (already in recipes_with_scores)
      // We don't add base_servings - only use yield as source of truth
      
      const mergedData = {
        // Copy ALL original fields (including yield)
        ...originalData,
        
        // Add canonical fields
        ingredients_canonical: canonical.ingredients_canonical || [],
        
        // Add metadata
        canonical_processed_date: new Date().toISOString(),
        canonical_version: "1.0",
        canonical_source: "stage2_processor"
      };

      // Clean up null ingredients (lines that failed processing)
      const validIngredients = mergedData.ingredients_canonical.filter(
        ing => ing.ingredient_id != null && ing.canonical_qty != null
      );
      
      const invalidCount = mergedData.ingredients_canonical.length - validIngredients.length;
      mergedData.ingredients_canonical = validIngredients;
      
      console.log(`   📊 Canonical ingredients: ${validIngredients.length} valid${invalidCount > 0 ? `, ${invalidCount} skipped (null)` : ""}`);

      // Step 2b: Build human-readable canonical_ingredients_list (for debugging / display)
      // Format: "118 mL chia seeds; 10 g dried goji berries; ..."
      const canonicalListParts = validIngredients.map((ing) => {
        const qty = ing.canonical_qty;
        const unit = ing.canonical_unit || "";
        const name = ing.ingredient_name || ing.ingredient_id || "";

        // Simple rounding for storage-level string (UI will still apply precise rules)
        let displayQty = qty;
        if (typeof displayQty === "number") {
          if (displayQty >= 1000) {
            displayQty = Math.round(displayQty); // e.g., 1892.7 → 1893
          } else if (displayQty >= 10) {
            displayQty = Math.round(displayQty * 10) / 10; // 1 decimal
          } else {
            displayQty = Math.round(displayQty * 100) / 100; // 2 decimals
          }
        }

        return `${displayQty} ${unit} ${name}`.trim();
      });

      mergedData.canonical_ingredients_list = canonicalListParts.join("; ");
      console.log(`   🧾 canonical_ingredients_list: ${mergedData.canonical_ingredients_list}`);

      // Step 3: Upload to recipes_canonical
      console.log(`   💾 Uploading to ${TARGET_COLLECTION}...`);
      
      // Use recipe_id as document ID for easy lookup
      await db.collection(TARGET_COLLECTION)
        .doc(recipeId.toString())
        .set(mergedData);

      console.log(`   ✅ Successfully uploaded recipe ${recipeId}`);
      successCount++;

    } catch (error) {
      console.error(`   ❌ Error processing recipe ${recipeId}: ${error.message}`);
      errorCount++;
      errors.push({
        recipe_id: recipeId,
        error: error.message
      });
    }
  }

  // Summary
  console.log("\n" + "=".repeat(80));
  console.log("📊 UPLOAD SUMMARY");
  console.log("=".repeat(80));
  console.log(`   ✅ Successful: ${successCount}/${recipeIds.length}`);
  console.log(`   ❌ Errors: ${errorCount}/${recipeIds.length}`);

  if (errors.length > 0) {
    console.log("\n❌ Errors encountered:");
    errors.forEach(e => {
      console.log(`   • Recipe ${e.recipe_id}: ${e.error}`);
    });
    
    // Save errors to file
    const errorFile = "canonical_upload_errors.json";
    fs.writeFileSync(errorFile, JSON.stringify(errors, null, 2));
    console.log(`\n💾 Errors saved to: ${errorFile}`);
  }

  console.log("\n" + "=".repeat(80));
  console.log("🎉 UPLOAD COMPLETE!");
  console.log("=".repeat(80));
  console.log(`\n📍 Check Firebase Console → Firestore → ${TARGET_COLLECTION}\n`);

  process.exit(errors.length > 0 ? 1 : 0);
}

// Run the upload
uploadCanonicalRecipes().catch(error => {
  console.error("\n❌ Fatal error:", error);
  process.exit(1);
});

