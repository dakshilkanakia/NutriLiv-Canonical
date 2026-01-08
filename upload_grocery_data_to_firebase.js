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
const GROCERY_CATALOG_FILE = path.join(JSON_DIR, "grocery_item_catalog.json");

// Collection names in Firebase
const COLLECTIONS = {
  groceryCatalog: "grocery_item_catalog",
  metadata: "grocery_data_metadata"
};

/**
 * Upload grocery item catalog to Firebase
 */
async function uploadGroceryCatalog() {
  console.log("\n🛒 Uploading Grocery Item Catalog...");
  
  if (!fs.existsSync(GROCERY_CATALOG_FILE)) {
    console.log(`❌ ERROR: File not found: ${GROCERY_CATALOG_FILE}`);
    console.log(`   Please run export_grocery_catalog.py first`);
    return 0;
  }
  
  const data = JSON.parse(fs.readFileSync(GROCERY_CATALOG_FILE, "utf-8"));
  
  if (!Array.isArray(data)) {
    console.log("❌ ERROR: Expected array format in JSON file");
    return 0;
  }
  
  console.log(`📋 Found ${data.length} grocery items to upload`);
  
  let count = 0;
  let batch = db.batch();
  const startTime = Date.now();
  
  console.log(`📤 Starting upload of ${data.length} items...`);
  console.log(`⏱️  Progress updates every 500 items\n`);
  
  for (const item of data) {
    // Generate document ID: ingredient_id + region_code + priority_rank + index
    const docId = `${item.ingredient_id}_${item.region_code}_${item.priority_rank || 99}_${count}`;
    const docRef = db.collection(COLLECTIONS.groceryCatalog).doc(docId);
    
    batch.set(docRef, {
      grocery_item_id: item.grocery_item_id || docId,
      ingredient_id: item.ingredient_id,
      primary_name: item.primary_name || "",
      category: item.category || "",
      region_code: item.region_code,
      package_size_value_SI: item.package_size_value_SI,
      package_unit_SI: item.package_unit_SI || "",
      package_label_display: item.package_label_display || "",
      priority_rank: item.priority_rank || 99,
      typical_use: item.typical_use || "",
      buy_as: item.buy_as || "",
      notes_internal: item.notes_internal || "",
      piece_size_SI_value: item.piece_size_SI_value || null,
    });
    
    count++;
    
    // Firestore batch limit is 500, commit and create new batch
    if (count % 500 === 0) {
      await batch.commit();
      batch = db.batch(); // Create new batch!
      
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = count / elapsed;
      const remaining = (data.length - count) / rate;
      const progress = (count / data.length) * 100;
      
      console.log(`   ⏳ Uploaded ${count}/${data.length} items (${progress.toFixed(1)}%)} | Rate: ${rate.toFixed(0)} items/sec | ETA: ${Math.round(remaining)}s`);
    }
  }
  
  // Commit remaining
  if (count % 500 !== 0) {
    await batch.commit();
  }
  
  const totalTime = (Date.now() - startTime) / 1000;
  console.log(`\n✅ Uploaded ${count} grocery catalog items`);
  console.log(`⏱️  Total time: ${totalTime.toFixed(1)} seconds (${(totalTime/60).toFixed(1)} minutes)`);
  return count;
}

/**
 * Upload metadata document
 */
async function uploadMetadata() {
  console.log("\n📊 Uploading Grocery Data Metadata...");
  
  const metadataDoc = db.collection(COLLECTIONS.metadata).doc("metadata");
  
  await metadataDoc.set({
    version: "2025-12-26",
    updated_at: admin.firestore.FieldValue.serverTimestamp(),
    grocery_catalog_count: await db.collection(COLLECTIONS.groceryCatalog).get().then(snap => snap.size),
  });
  
  console.log("✅ Uploaded grocery data metadata");
}

/**
 * Main execution
 */
async function main() {
  console.log("=".repeat(80));
  console.log("GROCERY DATA FIREBASE UPLOADER");
  console.log("=".repeat(80));
  
  try {
    const catalogCount = await uploadGroceryCatalog();
    
    if (catalogCount > 0) {
      await uploadMetadata();
    }
    
    console.log("\n" + "=".repeat(80));
    console.log("✅ UPLOAD COMPLETE");
    console.log("=".repeat(80));
    
  } catch (error) {
    console.error("\n❌ ERROR:", error);
    process.exit(1);
  }
}

// Run
main();

