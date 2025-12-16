const admin = require("firebase-admin");
const fs = require("fs");
const path = require("path");

// Path to your Firebase service account key
// UPDATE THIS PATH to point to your secretkey.json
const serviceAccount = require("/Users/dakshilkanakia/Desktop/Personalized Medicine/secretkey.json");

// Initialize Firebase
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});
const db = admin.firestore();

// Paths to JSON files
const JSON_DIR = "./flutter_assets";
const INGREDIENTS_FILE = path.join(JSON_DIR, "ingredients.json");
const POLICIES_FILE = path.join(JSON_DIR, "display_policies.json");
const DENSITIES_FILE = path.join(JSON_DIR, "densities.json");
const CONSTANTS_FILE = path.join(JSON_DIR, "conversion_constants.json");

// Collection names in Firebase
const COLLECTIONS = {
  ingredients: "ingredients",
  displayPolicies: "display_policies",
  densities: "densities",
  conversionConstants: "conversion_constants",
  metadata: "reference_data_metadata"
};

/**
 * Upload ingredients to Firebase
 */
async function uploadIngredients() {
  console.log("\n📦 Uploading Ingredients...");
  
  const data = JSON.parse(fs.readFileSync(INGREDIENTS_FILE, "utf-8"));
  const entries = Object.entries(data);
  
  let count = 0;
  let batch = db.batch();
  
  for (const [ingredientId, ingredientData] of entries) {
    const docRef = db.collection(COLLECTIONS.ingredients).doc(ingredientId);
    batch.set(docRef, ingredientData);
    count++;
    
    // Firestore batch limit is 500, commit and create new batch
    if (count % 500 === 0) {
      await batch.commit();
      batch = db.batch(); // Create new batch!
      console.log(`   ✅ Uploaded ${count}/${entries.length} ingredients...`);
    }
  }
  
  // Commit remaining
  if (count % 500 !== 0) {
    await batch.commit();
  }
  
  console.log(`✅ Uploaded ${count} ingredients`);
  return count;
}

/**
 * Upload display policies to Firebase
 */
async function uploadDisplayPolicies() {
  console.log("\n📋 Uploading Display Policies...");
  
  const data = JSON.parse(fs.readFileSync(POLICIES_FILE, "utf-8"));
  const entries = Object.entries(data);
  
  let count = 0;
  let batch = db.batch();
  
  for (const [ingredientId, policyData] of entries) {
    const docRef = db.collection(COLLECTIONS.displayPolicies).doc(ingredientId);
    batch.set(docRef, policyData);
    count++;
    
    if (count % 500 === 0) {
      await batch.commit();
      batch = db.batch(); // Create new batch
      console.log(`   ✅ Uploaded ${count}/${entries.length} policies...`);
    }
  }
  
  if (count % 500 !== 0) {
    await batch.commit();
  }
  
  console.log(`✅ Uploaded ${count} display policies`);
  return count;
}

/**
 * Upload densities to Firebase
 */
async function uploadDensities() {
  console.log("\n🔬 Uploading Densities...");
  
  const data = JSON.parse(fs.readFileSync(DENSITIES_FILE, "utf-8"));
  const entries = Object.entries(data);
  
  let count = 0;
  let batch = db.batch();
  
  for (const [key, densityData] of entries) {
    const docRef = db.collection(COLLECTIONS.densities).doc(key);
    batch.set(docRef, densityData);
    count++;
    
    if (count % 500 === 0) {
      await batch.commit();
      batch = db.batch();
      console.log(`   ✅ Uploaded ${count}/${entries.length} densities...`);
    }
  }
  
  if (count % 500 !== 0) {
    await batch.commit();
  }
  
  console.log(`✅ Uploaded ${count} densities`);
  return count;
}

/**
 * Upload conversion constants to Firebase
 */
async function uploadConversionConstants() {
  console.log("\n🔢 Uploading Conversion Constants...");
  
  const data = JSON.parse(fs.readFileSync(CONSTANTS_FILE, "utf-8"));
  
  // Store as single document
  await db.collection(COLLECTIONS.conversionConstants).doc("constants").set(data);
  
  console.log(`✅ Uploaded conversion constants`);
  console.log(`   - Mass conversions: ${Object.keys(data.mass_to_grams).length} units`);
  console.log(`   - Volume conversions: ${Object.keys(data.volume_to_ml).length} units`);
  console.log(`   - Unit dimensions: ${Object.keys(data.unit_dimensions).length} units`);
}

/**
 * Update metadata with version and timestamp
 */
async function updateMetadata(stats) {
  console.log("\n📝 Updating Metadata...");
  
  const metadata = {
    version: "1.0.0",
    last_updated: admin.firestore.FieldValue.serverTimestamp(),
    updated_at_iso: new Date().toISOString(),
    stats: {
      total_ingredients: stats.ingredients,
      total_policies: stats.policies,
      total_densities: stats.densities
    },
    collections: COLLECTIONS
  };
  
  await db.collection(COLLECTIONS.metadata).doc("current").set(metadata);
  
  console.log(`✅ Updated metadata`);
  console.log(`   Version: ${metadata.version}`);
  console.log(`   Timestamp: ${metadata.updated_at_iso}`);
}

/**
 * Main upload function
 */
async function uploadAllReferenceData() {
  console.log("=" * 80);
  console.log("🔥 FIREBASE REFERENCE DATA UPLOAD");
  console.log("Uploading to separate collections for flexibility");
  console.log("=" * 80);
  
  try {
    // Check if files exist
    const files = [INGREDIENTS_FILE, POLICIES_FILE, DENSITIES_FILE, CONSTANTS_FILE];
    for (const file of files) {
      if (!fs.existsSync(file)) {
        console.error(`❌ ERROR: File not found: ${file}`);
        console.log("\nPlease run 'python export_reference_data.py' first!");
        process.exit(1);
      }
    }
    
    // Upload each collection
    const stats = {};
    stats.ingredients = await uploadIngredients();
    stats.policies = await uploadDisplayPolicies();
    stats.densities = await uploadDensities();
    await uploadConversionConstants();
    
    // Update metadata
    await updateMetadata(stats);
    
    // Summary
    console.log("\n" + "=" * 80);
    console.log("🎉 UPLOAD COMPLETE!");
    console.log("=" * 80);
    console.log(`\n✅ Firebase Collections Created:`);
    console.log(`   - ${COLLECTIONS.ingredients} (${stats.ingredients} documents)`);
    console.log(`   - ${COLLECTIONS.displayPolicies} (${stats.policies} documents)`);
    console.log(`   - ${COLLECTIONS.densities} (${stats.densities} documents)`);
    console.log(`   - ${COLLECTIONS.conversionConstants} (1 document)`);
    console.log(`   - ${COLLECTIONS.metadata} (1 document with version & timestamp)`);
    
    console.log(`\n📱 Next Steps:`);
    console.log(`   1. Test Firebase data in Firebase Console`);
    console.log(`   2. Create Flutter service to download & cache this data`);
    console.log(`   3. Check metadata timestamp for cache invalidation`);
    
    console.log("\n" + "=" * 80);
    
  } catch (error) {
    console.error("\n❌ ERROR during upload:", error.message);
    console.error(error);
    process.exit(1);
  }
}

// Run the upload
uploadAllReferenceData()
  .then(() => {
    console.log("\n✅ Script completed successfully!");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\n❌ Script failed:", error);
    process.exit(1);
  });

