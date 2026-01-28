/**
 * Upload side effect exclusions to Firebase.
 * Source: flutter_assets/side_effect_exclusions.json
 * Target:
 *   - Collection: side_effect_exclusions (one doc per side effect)
 *   - Metadata: side_effect_exclusions_metadata/metadata
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

async function uploadSideEffectExclusions() {
  try {
    console.log('📖 Reading side_effect_exclusions.json...');
    const jsonPath = path.join(__dirname, 'flutter_assets', 'side_effect_exclusions.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

    const sideEffectExclusions = jsonData.side_effect_exclusions || {};
    const metadata = jsonData.metadata || {};

    console.log(`📤 Uploading side effect exclusions for ${Object.keys(sideEffectExclusions).length} side effects...`);

    // Upload each side effect as a doc (using normalized sheet name as doc ID)
    for (const [sideEffectName, data] of Object.entries(sideEffectExclusions)) {
      const docRef = db.collection('side_effect_exclusions').doc(sideEffectName);
      await docRef.set({
        ingredient_ids: data.ingredient_ids || [],
      });
    }

    // Upload metadata separately for cache invalidation
    const metadataRef = db.collection('side_effect_exclusions_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });

    console.log('\n✅ Successfully uploaded side effect exclusions to Firebase!');
    console.log(`📊 Total side effects: ${Object.keys(sideEffectExclusions).length}`);
  } catch (error) {
    console.error('❌ Error uploading side effect exclusions:', error);
    process.exit(1);
  }
}

uploadSideEffectExclusions()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((err) => {
    console.error('❌ Unexpected error:', err);
    process.exit(1);
  });
