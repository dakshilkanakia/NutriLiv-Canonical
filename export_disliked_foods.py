#!/usr/bin/env python3
"""
Export Disliked Foods from Excel to JSON.

Input:  Disliked Food.xlsx
Output: flutter_assets/disliked_foods.json

Structure:
{
  "disliked_foods": {
    "Cilantro": {
      "ingredient_ids": ["INGR_00024"]
    },
    "Mushrooms": {
      "ingredient_ids": ["INGR_00053", "INGR_01138", ...]
    },
    ...
  },
  "metadata": {
    "export_date": "...",
    "total_dislikes": 22
  }
}
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def export_disliked_foods():
    base_path = Path(__file__).parent
    excel_path = base_path / "Disliked Food.xlsx"
    output_path = base_path / "flutter_assets" / "disliked_foods.json"

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    # Read the Excel file (single sheet)
    df = pd.read_excel(excel_path)
    
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

    if "ingredient_id" not in col_map or "primary_name" not in col_map:
        raise ValueError(
            f"Expected columns 'ingredient_id' and 'primary_name'. Found: {df.columns.tolist()}"
        )

    disliked_foods = {}

    for _, row in df.iterrows():
        primary_name = str(row[col_map["primary_name"]]).strip()
        ingredient_id_str = str(row[col_map["ingredient_id"]]).strip()

        if not primary_name or primary_name.lower() == "nan":
            continue
        if not ingredient_id_str or ingredient_id_str.lower() == "nan":
            continue

        # Split comma-separated ingredient IDs
        ingredient_ids = [
            ing_id.strip()
            for ing_id in ingredient_id_str.split(",")
            if ing_id.strip()
        ]

        if primary_name not in disliked_foods:
            disliked_foods[primary_name] = {
                "ingredient_ids": []
            }

        # Add all ingredient IDs for this primary_name
        disliked_foods[primary_name]["ingredient_ids"].extend(ingredient_ids)

    # Remove duplicates while preserving order
    for name in disliked_foods:
        disliked_foods[name]["ingredient_ids"] = list(dict.fromkeys(disliked_foods[name]["ingredient_ids"]))

    # Build output structure
    output = {
        "disliked_foods": disliked_foods,
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "total_dislikes": len(disliked_foods)
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported {len(disliked_foods)} disliked foods to {output_path}")
    print(f"  Total ingredient IDs: {sum(len(v['ingredient_ids']) for v in disliked_foods.values())}")


if __name__ == "__main__":
    export_disliked_foods()
