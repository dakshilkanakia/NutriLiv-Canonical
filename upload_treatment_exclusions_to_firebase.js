/**
 * Upload Treatment Exclusions to Firebase
 * 
 * Uploads treatment_exclusions.json to Firebase Firestore.
 * Creates a single document in treatment_exclusions/treatment_exclusions collection.
 * 
 * Created: January 11, 2025
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

async function uploadTreatmentExclusions() {
  try {
    console.log('📖 Reading treatment_exclusions.json...');
    
    const jsonPath = path.join(__dirname, 'flutter_assets', 'treatment_exclusions.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    
    const treatmentExclusions = jsonData.treatment_exclusions || {};
    const metadata = jsonData.metadata || {};
    
    console.log(`📤 Uploading treatment exclusions for ${Object.keys(treatmentExclusions).length} treatment types...`);
    
    // Upload as a single document
    const docRef = db.collection('treatment_exclusions').doc('treatment_exclusions');
    await docRef.set({
      ...treatmentExclusions,
      metadata: metadata,
    });
    
    // Upload metadata separately for cache invalidation
    const metadataRef = db.collection('treatment_exclusions_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });
    
    console.log('\n✅ Successfully uploaded treatment exclusions to Firebase!');
    console.log(`📊 Total treatment types: ${Object.keys(treatmentExclusions).length}`);
    
    // Print summary
    let totalDrugs = 0;
    for (const treatmentType of Object.values(treatmentExclusions)) {
      if (treatmentType.drugs) {
        totalDrugs += Object.keys(treatmentType.drugs).length;
      }
    }
    console.log(`📊 Total drugs/regimens: ${totalDrugs}`);
    
  } catch (error) {
    console.error('❌ Error uploading treatment exclusions:', error);
    process.exit(1);
  }
}

uploadTreatmentExclusions()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
