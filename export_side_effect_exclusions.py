#!/usr/bin/env python3
"""
Export Side Effect Exclusions from Excel to JSON.

Input:  Side Effects Exclusions.xlsx
Output: flutter_assets/side_effect_exclusions.json

Structure:
{
  "side_effect_exclusions": {
    "Nausea Vomiting": {
      "ingredient_ids": ["INGR_00022", "INGR_00040", ...]
    },
    "Mouth Sores": {
      "ingredient_ids": ["INGR_00001", ...]
    },
    ...
  },
  "metadata": {
    "export_date": "...",
    "total_side_effects": 8
  }
}

Note: Sheet names use normalized format (e.g., "Nausea Vomiting" instead of "Nausea/Vomiting")
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def normalize_side_effect_name(name):
    """
    Normalize side effect name from Flutter format to sheet name format.
    - "Nausea/Vomiting" -> "Nausea Vomiting"
    - "Heartburn/Reflux" -> "Heartburn Reflux"
    - "Lactose Intolerance" -> "Lactose Intolerence" (handles typo in sheet name)
    """
    # Replace / with space
    normalized = name.replace('/', ' ')
    
    # Handle specific typo case
    if normalized == "Lactose Intolerance":
        normalized = "Lactose Intolerence"
    
    return normalized


def export_side_effect_exclusions():
    base_path = Path(__file__).parent
    excel_path = base_path / "Side Effects Exclusions.xlsx"
    output_path = base_path / "flutter_assets" / "side_effect_exclusions.json"

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    xl = pd.ExcelFile(excel_path)
    sheets = xl.sheet_names

    # Skip the "Side Effects" sheet (it's just a list)
    side_effect_sheets = [s for s in sheets if s != "Side Effects"]

    side_effect_exclusions = {}

    for sheet_name in side_effect_sheets:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Drop fully empty columns
        df = df.dropna(axis=1, how="all")
        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]

        # Expect columns ingredient_id and primary_name
        col_map = {}
        for col in df.columns:
            lc = col.lower()
            if "ingredient_id" in lc:
                col_map["ingredient_id"] = col
            elif "primary" in lc and "name" in lc:
                col_map["primary_name"] = col

        if "ingredient_id" not in col_map:
            print(f"⚠️ Warning: Sheet '{sheet_name}' missing ingredient_id column. Skipping.")
            continue

        ingredient_ids = []
        for _, row in df.iterrows():
            ingredient_id_str = str(row[col_map["ingredient_id"]]).strip()
            
            if not ingredient_id_str or ingredient_id_str.lower() == "nan":
                continue

            # Handle comma-separated ingredient IDs (if any)
            ids = [
                ing_id.strip()
                for ing_id in ingredient_id_str.split(",")
                if ing_id.strip()
            ]
            ingredient_ids.extend(ids)

        # Remove duplicates while preserving order
        ingredient_ids = list(dict.fromkeys(ingredient_ids))

        if sheet_name not in side_effect_exclusions:
            side_effect_exclusions[sheet_name] = {
                "ingredient_ids": []
            }

        side_effect_exclusions[sheet_name]["ingredient_ids"] = ingredient_ids

    # Build output structure
    output = {
        "side_effect_exclusions": side_effect_exclusions,
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "total_side_effects": len(side_effect_exclusions)
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported {len(side_effect_exclusions)} side effect exclusions to {output_path}")
    total_ingredients = sum(len(v['ingredient_ids']) for v in side_effect_exclusions.values())
    print(f"  Total ingredient IDs: {total_ingredients}")


if __name__ == "__main__":
    export_side_effect_exclusions()
