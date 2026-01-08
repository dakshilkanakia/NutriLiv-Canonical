/**
 * Upload Cancer Exclusions to Firebase
 * 
 * Uploads cancer_exclusions.json to Firebase Firestore.
 * Creates a single document in cancer_exclusions/cancer_exclusions collection.
 * 
 * Created: January 8, 2025
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

async function uploadCancerExclusions() {
  try {
    console.log('📖 Reading cancer_exclusions.json...');
    
    const jsonPath = path.join(__dirname, 'flutter_assets', 'cancer_exclusions.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    
    const cancerExclusions = jsonData.cancer_exclusions || {};
    const metadata = jsonData.metadata || {};
    
    console.log(`📤 Uploading cancer exclusions for ${Object.keys(cancerExclusions).length} cancer types...`);
    
    // Upload as a single document
    const docRef = db.collection('cancer_exclusions').doc('cancer_exclusions');
    await docRef.set({
      ...cancerExclusions,
      metadata: metadata,
    });
    
    // Upload metadata separately for cache invalidation
    const metadataRef = db.collection('cancer_exclusions_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });
    
    console.log('\n✅ Successfully uploaded cancer exclusions to Firebase!');
    console.log(`📊 Total cancer types: ${Object.keys(cancerExclusions).length}`);
    
    // Print summary
    let totalSubtypes = 0;
    for (const cancerType of Object.values(cancerExclusions)) {
      if (cancerType.subtypes) {
        totalSubtypes += Object.keys(cancerType.subtypes).length;
      }
    }
    console.log(`📊 Total subtypes: ${totalSubtypes}`);
    
  } catch (error) {
    console.error('❌ Error uploading cancer exclusions:', error);
    process.exit(1);
  }
}

uploadCancerExclusions()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });

