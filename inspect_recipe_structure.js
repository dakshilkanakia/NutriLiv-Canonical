#!/usr/bin/env node

/**
 * Inspect Recipe Structure
 * 
 * Quick script to fetch a sample recipe from recipes_with_scores
 * to understand the data structure before building the upload script.
 */

const admin = require("firebase-admin");
const fs = require("fs");

// Initialize Firebase (reuse service account from previous script)
const serviceAccount = require("/Users/dakshilkanakia/Desktop/Personalized Medicine/secretkey.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function inspectRecipe() {
  console.log("\n" + "=".repeat(80));
  console.log("🔍 INSPECTING RECIPE STRUCTURE");
  console.log("=".repeat(80) + "\n");

  try {
    // Try to fetch recipe with recipe_id = 127 (first in our canonical data)
    console.log("📖 Searching for recipe with recipe_id = 127...\n");
    
    const snapshot = await db.collection("recipes_with_scores")
      .where("recipe_id", "==", "127")
      .limit(1)
      .get();

    if (snapshot.empty) {
      console.log("⚠️  No recipe found with recipe_id = 127");
      console.log("Let me try fetching ANY recipe to show structure...\n");
      
      const anySnapshot = await db.collection("recipes_with_scores")
        .limit(1)
        .get();
      
      if (anySnapshot.empty) {
        console.log("❌ Collection 'recipes_with_scores' is empty or doesn't exist!");
        return;
      }
      
      const doc = anySnapshot.docs[0];
      console.log("✅ Found a sample recipe (doc ID: " + doc.id + ")\n");
      console.log("📊 RECIPE STRUCTURE:");
      console.log("=".repeat(80));
      console.log(JSON.stringify(doc.data(), null, 2));
      console.log("=".repeat(80));
      
    } else {
      const doc = snapshot.docs[0];
      console.log("✅ Found recipe with recipe_id = 127 (doc ID: " + doc.id + ")\n");
      console.log("📊 RECIPE STRUCTURE:");
      console.log("=".repeat(80));
      console.log(JSON.stringify(doc.data(), null, 2));
      console.log("=".repeat(80));
      
      // Show field summary
      const data = doc.data();
      console.log("\n📋 FIELD SUMMARY:");
      console.log("=".repeat(80));
      Object.keys(data).forEach(key => {
        const value = data[key];
        const type = Array.isArray(value) ? `array[${value.length}]` : typeof value;
        console.log(`  • ${key}: ${type}`);
      });
      console.log("=".repeat(80));
    }
    
    // Save to file for reference
    const outputFile = "sample_recipe_structure.json";
    if (!snapshot.empty) {
      fs.writeFileSync(outputFile, JSON.stringify(snapshot.docs[0].data(), null, 2));
      console.log(`\n💾 Saved sample recipe structure to: ${outputFile}`);
    }
    
  } catch (error) {
    console.error("❌ Error fetching recipe:", error);
  }
  
  console.log("\n" + "=".repeat(80));
  console.log("✅ INSPECTION COMPLETE");
  console.log("=".repeat(80) + "\n");
  
  process.exit(0);
}

inspectRecipe();

