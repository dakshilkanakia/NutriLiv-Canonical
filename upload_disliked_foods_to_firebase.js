/**
 * Upload disliked foods to Firebase.
 * Source: flutter_assets/disliked_foods.json
 * Target:
 *   - Collection: disliked_foods (one doc per dislike)
 *   - Metadata: disliked_foods_metadata/metadata
 */

const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

// Service account key used for Firebase Admin SDK (kept out of git via .gitignore)
const serviceAccountPath = path.join(
  __dirname,
  'nutri-liv-wvo8t4-firebase-adminsdk-67fhs-c9e90d4e40.json',
);

if (!fs.existsSync(serviceAccountPath)) {
  console.error('❌ Service account key not found:', serviceAccountPath);
  process.exit(1);
}

admin.initializeApp({
  credential: admin.credential.cert(require(serviceAccountPath)),
});

const db = admin.firestore();

async function uploadDislikedFoods() {
  try {
    console.log('📖 Reading disliked_foods.json...');
    const jsonPath = path.join(__dirname, 'flutter_assets', 'disliked_foods.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

    const dislikedFoods = jsonData.disliked_foods || {};
    const metadata = jsonData.metadata || {};

    console.log(`📤 Uploading disliked foods for ${Object.keys(dislikedFoods).length} items...`);

    // Upload each dislike as a doc (using primary_name as doc ID)
    for (const [primaryName, data] of Object.entries(dislikedFoods)) {
      const docRef = db.collection('disliked_foods').doc(primaryName);
      await docRef.set({
        ingredient_ids: data.ingredient_ids || [],
      });
    }

    // Upload metadata separately for cache invalidation
    const metadataRef = db.collection('disliked_foods_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });

    console.log('\n✅ Successfully uploaded disliked foods to Firebase!');
    console.log(`📊 Total disliked foods: ${Object.keys(dislikedFoods).length}`);
  } catch (error) {
    console.error('❌ Error uploading disliked foods:', error);
    process.exit(1);
  }
}

uploadDislikedFoods()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((err) => {
    console.error('❌ Unexpected error:', err);
    process.exit(1);
  });
