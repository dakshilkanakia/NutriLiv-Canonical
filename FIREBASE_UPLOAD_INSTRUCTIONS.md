# Firebase Upload Instructions

## 📋 Overview

This guide shows how to upload reference data (ingredients, policies, densities, conversions) to Firebase Firestore.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/dakshilkanakia/Downloads/files
npm init -y
npm install firebase-admin
```

### 2. Run Upload Script

```bash
node upload_reference_data_to_firebase.js
```

---

## 📦 What Gets Uploaded

The script creates **5 Firebase collections**:

### 1. `ingredients` (965 documents)
```
Document ID: INGR_00001
{
  name: "Apple",
  category: "Produce",
  default_form: "FORM_WHOLE",
  aliases: ["apples"]
}
```

### 2. `display_policies` (965 documents)
```
Document ID: INGR_00001
{
  default_rule: "prefer_mass",
  locale_overrides: {
    "en-US": "prefer_volume",
    "en-CA": "prefer_volume"
  },
  rationale: "..."
}
```

### 3. `densities` (961 documents)
```
Document ID: INGR_00001_FORM_DRIED
{
  density_id: "DENS_00001",
  ingredient_id: "INGR_00001",
  form_id: "FORM_DRIED",
  g_per_ml: 0.364
}
```

### 4. `conversion_constants` (1 document)
```
Document ID: constants
{
  version: "1.0",
  mass_to_grams: {...},
  volume_to_ml: {...},
  unit_dimensions: {...}
}
```

### 5. `reference_data_metadata` (1 document)
```
Document ID: current
{
  version: "1.0.0",
  last_updated: Timestamp,
  updated_at_iso: "2024-12-01T15:30:00Z",
  stats: {
    total_ingredients: 965,
    total_policies: 965,
    total_densities: 961
  }
}
```

---

## 🔄 Updating Data

When you update Excel files:

1. **Export new JSON:**
   ```bash
   python export_reference_data.py
   ```

2. **Upload to Firebase:**
   ```bash
   node upload_reference_data_to_firebase.js
   ```

3. **Automatic cache invalidation:**
   - `last_updated` timestamp changes
   - Flutter app detects change
   - Downloads fresh data automatically

---

## 🔍 Verification

After upload, check Firebase Console:
1. Go to: https://console.firebase.google.com
2. Select project: `nutri-liv-wvo8t4`
3. Navigate to Firestore Database
4. Verify collections exist:
   - ✅ ingredients
   - ✅ display_policies
   - ✅ densities
   - ✅ conversion_constants
   - ✅ reference_data_metadata

5. Check metadata document for `last_updated` timestamp

---

## 📱 Flutter Integration

In your Flutter app, check for updates:

```dart
// 1. Check metadata for version
final metadataDoc = await FirebaseFirestore.instance
    .collection('reference_data_metadata')
    .doc('current')
    .get();

final firebaseTimestamp = metadataDoc.data()!['updated_at_iso'];
final localTimestamp = await getLocalTimestamp();

// 2. If different, download fresh data
if (firebaseTimestamp != localTimestamp) {
  await downloadReferenceData();
}
```

---

## ⚠️ Important Notes

1. **Service Account Key:** 
   - Path in script: `/Users/dakshilkanakia/Desktop/Personalized Medicine/secretkey.json`
   - Keep this file secure (never commit to Git!)

2. **Batch Limits:**
   - Firestore batches are limited to 500 operations
   - Script automatically handles batching

3. **Upload Time:**
   - ~30-60 seconds for all data
   - Progress shown during upload

4. **Costs:**
   - Upload: ~2,900 write operations (~$0.06)
   - One-time cost per update

---

## 🐛 Troubleshooting

### Error: "File not found"
```bash
# Run export script first
python export_reference_data.py
```

### Error: "firebase-admin not found"
```bash
npm install firebase-admin
```

### Error: "Permission denied"
- Check `secretkey.json` path
- Verify service account has Firestore permissions

---

## 📊 Cost Estimates

**Initial Upload:**
- ~2,900 writes = ~$0.06

**User Downloads (per week per user):**
- 5 collections × 1 read each = ~$0.0000036 per user
- 1000 users/week = ~$0.004/week

**Very cheap!** ✅

---

## ✅ Checklist

Before running:
- [ ] Ran `python export_reference_data.py`
- [ ] Installed `firebase-admin` npm package
- [ ] Verified `secretkey.json` path
- [ ] Checked Firebase Console access

After running:
- [ ] Verified data in Firebase Console
- [ ] Checked `reference_data_metadata/current` timestamp
- [ ] Ready to integrate with Flutter app

---

**Ready to upload!** 🚀

