/**
 * Upload Supplements to Firebase
 * 
 * Uploads supplements.json to Firebase Firestore.
 * Creates individual documents in supplements collection, keyed by supplement_id.
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

async function uploadSupplements() {
  try {
    console.log('📖 Reading supplements.json...');
    
    const jsonPath = path.join(__dirname, 'flutter_assets', 'supplements.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    
    const supplements = jsonData.supplements || {};
    const metadata = jsonData.metadata || {};
    
    console.log(`📤 Uploading ${Object.keys(supplements).length} supplements...`);
    
    const batch = db.batch();
    let count = 0;
    const startTime = Date.now();
    
    // Upload each supplement as a document
    for (const [supplementId, supplementData] of Object.entries(supplements)) {
      const docRef = db.collection('supplements').doc(supplementId);
      batch.set(docRef, supplementData);
      count++;
      
      // Firestore batch limit is 500, commit and create new batch
      if (count % 500 === 0) {
        await batch.commit();
        batch = db.batch();
        
        const elapsed = (Date.now() - startTime) / 1000;
        const rate = count / elapsed;
        const progress = (count / Object.keys(supplements).length) * 100;
        
        console.log(`   ⏳ Uploaded ${count}/${Object.keys(supplements).length} supplements (${progress.toFixed(1)}%)`);
      }
    }
    
    // Commit remaining
    if (count % 500 !== 0) {
      await batch.commit();
    }
    
    // Upload metadata
    const metadataRef = db.collection('supplements_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });
    
    const totalTime = (Date.now() - startTime) / 1000;
    console.log('\n✅ Successfully uploaded supplements to Firebase!');
    console.log(`📊 Total supplements: ${count}`);
    console.log(`⏱️  Total time: ${totalTime.toFixed(1)} seconds`);
    
  } catch (error) {
    console.error('❌ Error uploading supplements:', error);
    process.exit(1);
  }
}

uploadSupplements()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
