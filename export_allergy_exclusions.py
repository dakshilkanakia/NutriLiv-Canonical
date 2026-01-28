#!/usr/bin/env python3
"""
Export Allergy Exclusions from Excel to JSON.

Input:  Exclusions based on Allergy.xlsx
Output: flutter_assets/allergy_exclusions.json

Structure:
{
  "allergy_exclusions": {
    "Cow's Milk": {
      "description": "...",
      "ingredient_ids": ["INGR_00126", ...],
      "primary_names": ["Butter", ...]
    },
    ...
  },
  "metadata": {
    "export_date": "...",
    "total_allergens": 17
  }
}
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def export_allergy_exclusions():
    base_path = Path(__file__).parent
    excel_path = base_path / "Exclusions based on Allergy.xlsx"
    output_path = base_path / "flutter_assets" / "allergy_exclusions.json"

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    xl = pd.ExcelFile(excel_path)
    sheets = xl.sheet_names

    if "Allergens" not in sheets:
        raise ValueError("Expected sheet 'Allergens' listing allergen names/descriptions")

    # Build allergen description map
    allergens_df = xl.parse("Allergens")
    # Normalize columns
    allergens_df.columns = [c.strip() for c in allergens_df.columns]
    desc_map = {}
    for _, row in allergens_df.iterrows():
        name = str(row.get("Allergen Name", "")).strip()
        if not name or name.lower() == "nan":
            continue
        desc = str(row.get("Description", "")).strip()
        desc_map[name] = desc

    allergy_exclusions = {}

    # Process each allergen sheet (skip the "Allergens" sheet)
    for sheet in sheets:
        if sheet == "Allergens":
            continue

        df = xl.parse(sheet)
        # Drop fully empty columns
        df = df.dropna(axis=1, how="all")
        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]

        # Expect columns ingredient_id and primary_name (case-insensitive)
        # Try to find the best match
        col_map = {}
        for col in df.columns:
            lc = col.lower()
            if "ingredient_id" in lc:
                col_map["ingredient_id"] = col
            elif "primary" in lc and "name" in lc:
                col_map["primary_name"] = col

        if "ingredient_id" not in col_map:
            raise ValueError(f"Sheet '{sheet}' missing ingredient_id column")
        if "primary_name" not in col_map:
            # Not fatal; we can still proceed with IDs
            col_map["primary_name"] = None

        ids = []
        names = []
        for _, row in df.iterrows():
            ingr_id = row.get(col_map["ingredient_id"])
            if pd.isna(ingr_id):
                continue
            ingr_id = str(ingr_id).strip()
            if not ingr_id:
                continue
            ids.append(ingr_id)

            if col_map["primary_name"]:
                name_val = row.get(col_map["primary_name"])
                name_val = "" if pd.isna(name_val) else str(name_val).strip()
            else:
                name_val = ""
            names.append(name_val)

        # Deduplicate while preserving order
        seen = set()
        unique_ids = []
        unique_names = []
        for i, ingr_id in enumerate(ids):
            if ingr_id in seen:
                continue
            seen.add(ingr_id)
            unique_ids.append(ingr_id)
            unique_names.append(names[i] if i < len(names) else "")

        allergy_exclusions[sheet] = {
            "description": desc_map.get(sheet, ""),
            "ingredient_ids": unique_ids,
            "primary_names": unique_names,
        }

    output = {
        "allergy_exclusions": allergy_exclusions,
        "metadata": {
            "export_date": datetime.utcnow().isoformat(),
            "total_allergens": len(allergy_exclusions),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Exported {len(allergy_exclusions)} allergens to {output_path}")


if __name__ == "__main__":
    export_allergy_exclusions()
