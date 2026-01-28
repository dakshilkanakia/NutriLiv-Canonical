/**
 * Upload allergy exclusions to Firebase.
 * Source: flutter_assets/allergy_exclusions.json
 * Target:
 *   - Collection: allergy_exclusions (one doc per allergen)
 *   - Metadata: allergy_exclusions_metadata/metadata
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

async function uploadAllergyExclusions() {
  try {
    console.log('📖 Reading allergy_exclusions.json...');
    const jsonPath = path.join(__dirname, 'flutter_assets', 'allergy_exclusions.json');
    const jsonData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

    const allergyExclusions = jsonData.allergy_exclusions || {};
    const metadata = jsonData.metadata || {};

    console.log(`📤 Uploading allergy exclusions for ${Object.keys(allergyExclusions).length} allergens...`);

    // Upload each allergen as a doc
    for (const [allergen, data] of Object.entries(allergyExclusions)) {
      const docRef = db.collection('allergy_exclusions').doc(allergen);
      await docRef.set({
        description: data.description || '',
        ingredient_ids: data.ingredient_ids || [],
        primary_names: data.primary_names || [],
      });
    }

    // Upload metadata separately for cache invalidation
    const metadataRef = db.collection('allergy_exclusions_metadata').doc('metadata');
    await metadataRef.set({
      ...metadata,
      last_updated: admin.firestore.FieldValue.serverTimestamp(),
    });

    console.log('\n✅ Successfully uploaded allergy exclusions to Firebase!');
    console.log(`📊 Total allergens: ${Object.keys(allergyExclusions).length}`);
  } catch (error) {
    console.error('❌ Error uploading allergy exclusions:', error);
    process.exit(1);
  }
}

uploadAllergyExclusions()
  .then(() => {
    console.log('\n✅ Upload complete!');
    process.exit(0);
  })
  .catch((err) => {
    console.error('❌ Unexpected error:', err);
    process.exit(1);
  });
