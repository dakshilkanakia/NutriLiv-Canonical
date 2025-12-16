#!/usr/bin/env node

/**
 * Check if test recipes exist in Firebase
 */

const admin = require("firebase-admin");
const serviceAccount = require("/Users/dakshilkanakia/Desktop/Personalized Medicine/secretkey.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

// Test recipe IDs from test_recipes_canonical.json
const testRecipeIds = [127, 129, 130, 131, 133, 134, 136, 137, 139, 140, 143];

async function checkRecipes() {
  console.log("\n🔍 Checking if test recipes exist in Firebase...\n");
  
  const found = [];
  const missing = [];
  
  for (const id of testRecipeIds) {
    try {
      const snapshot = await db.collection("recipes_with_scores")
        .where("recipe_id", "==", id)
        .limit(1)
        .get();
      
      if (!snapshot.empty) {
        const doc = snapshot.docs[0];
        const data = doc.data();
        found.push({
          recipe_id: id,
          doc_id: doc.id,
          recipe_title: data.recipe_title || "Unknown"
        });
        console.log(`✅ Found: ${id} - "${data.recipe_title || "Unknown"}"`);
      } else {
        missing.push(id);
        console.log(`❌ Missing: ${id}`);
      }
    } catch (error) {
      console.log(`❌ Error checking ${id}: ${error.message}`);
      missing.push(id);
    }
  }
  
  console.log("\n" + "=".repeat(60));
  console.log(`📊 Summary: ${found.length}/${testRecipeIds.length} recipes found`);
  console.log("=".repeat(60));
  
  if (found.length > 0) {
    console.log("\n✅ Found recipes:");
    found.forEach(r => console.log(`   • ${r.recipe_id}: ${r.recipe_title}`));
  }
  
  if (missing.length > 0) {
    console.log("\n❌ Missing recipes:");
    console.log(`   • ${missing.join(", ")}`);
  }
  
  process.exit(0);
}

checkRecipes();

