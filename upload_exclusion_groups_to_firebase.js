/**
 * Upload Exclusion Groups to Firebase
 * 
 * Uploads exclusion_groups.json to Firebase Firestore.
 * Each exclusion group becomes a document in exclusion_groups collection.
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

async function uploadExclusionGroups() {
  try {
    console.log('📖 Reading exclusion_groups.json...');
    
    const jsonPath = path.join(__dirname, 'flutter_assets', 'exclusion_groups.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    
    const exclusionGroups = jsonData.exclusion_groups || {};
    const metadata = jsonData.metadata || {};
    
    console.log(`📤 Uploading ${Object.keys(exclusionGroups).length} exclusion groups to Firebase...`);
    
    const batch = db.batch();
    let batchCount = 0;
    const BATCH_SIZE = 500;
    
    // Upload each group as a separate document
    for (const [groupName, ingredientIds] of Object.entries(exclusionGroups)) {
      const docRef = db.collection('exclusion_groups').doc(groupName);
      
      batch.set(docRef, {
        group_name: groupName,
        ingredient_ids: ingredientIds,
        ingredient_count: ingredientIds.length,
      });
      
      batchCount++;
      
      // Commit batch if it reaches the limit
      if (batchCount >= BATCH_SIZE) {
        await batch.commit();
        console.log(`   ✅ Committed batch of ${batchCount} documents`);
        batchCount = 0;
        // Re-initialize batch
        const newBatch = db.batch();
        Object.assign(batch, newBatch);
      }
    }
    
    // Commit remaining documents
    if (batchCount > 0) {
      await batch.commit();
      console.log(`   ✅ Committed final batch of ${batchCount} documents`);
    }
    
    // Upload metadata
    const metadataRef = db.collection('exclusion_data_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });
    
    console.log('\n✅ Successfully uploaded exclusion groups to Firebase!');
    console.log(`📊 Total groups: ${Object.keys(exclusionGroups).length}`);
    console.log(`📊 Total ingredients: ${metadata.total_ingredients || 0}`);
    
  } catch (error) {
    console.error('❌ Error uploading exclusion groups:', error);
    process.exit(1);
  }
}

uploadExclusionGroups()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });

