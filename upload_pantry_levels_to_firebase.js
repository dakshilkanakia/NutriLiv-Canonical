/**
 * Upload Pantry Levels to Firebase
 * 
 * Uploads pantry_levels.json to Firebase Firestore.
 * Creates a single document in pantry_levels/pantry_levels collection.
 * 
 * Created: December 29, 2024
 */

const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

// Initialize Firebase Admin
const serviceAccount = require('./nutri-liv-wvo8t4-firebase-adminsdk-67fhs-c9e90d4e40.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const db = admin.firestore();

async function uploadPantryLevels() {
  try {
    console.log('📖 Reading pantry_levels.json...');
    
    const jsonPath = path.join(__dirname, 'flutter_assets', 'pantry_levels.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    
    console.log('📤 Uploading pantry levels to Firebase...');
    
    // Flatten structure for Firestore:
    //  - Read from jsonData.pantry_levels
    //  - Write Basic / Average / Well-stocked at top level
    const pantryLevels = jsonData.pantry_levels || {};
    const basicList = pantryLevels.Basic || [];
    const averageList = pantryLevels.Average || [];
    const wellStockedList = pantryLevels['Well-stocked'] || pantryLevels.Well_stocked || [];
    
    const flattened = {
      Basic: basicList,
      Average: averageList,
      'Well-stocked': wellStockedList,
      metadata: jsonData.metadata || {},
    };
    
    // Upload as a single flattened document
    const docRef = db.collection('pantry_levels').doc('pantry_levels');
    await docRef.set(flattened);

    console.log('✅ Successfully uploaded pantry levels to Firebase');
    console.log(`   Collection: pantry_levels/pantry_levels`);
    console.log(`   Basic: ${basicList.length} ingredients`);
    console.log(`   Average: ${averageList.length} ingredients`);
    console.log(`   Well-stocked: ${wellStockedList.length} ingredients`);
    
    // Also create metadata document for cache invalidation
    const metadataRef = db.collection('pantry_data_metadata').doc('metadata');
    await metadataRef.set({
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
      version: jsonData.metadata?.export_date ?? new Date().toISOString(),
      basic_count: basicList.length,
      average_count: averageList.length,
      well_stocked_count: wellStockedList.length,
    });
    
    console.log('✅ Created metadata document');
    
    process.exit(0);
  } catch (error) {
    console.error('❌ Error uploading pantry levels:', error);
    process.exit(1);
  }
}

uploadPantryLevels();

