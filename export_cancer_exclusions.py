#!/usr/bin/env python3
"""
Export Cancer Exclusions from Excel to JSON

Reads Cancer and Treatment Exclusions - Sample.xlsx and exports
cancer type/subtype -> exclusion groups mapping for Firebase.
"""

import pandas as pd
import json
import os
from pathlib import Path

def export_cancer_exclusions():
    """Export cancer exclusions from Excel to JSON"""
    
    base_path = Path(__file__).parent
    excel_file = base_path / "Cancer and Treatment Exclusions - Sample.xlsx"
    output_file = base_path / "flutter_assets" / "cancer_exclusions.json"
    
    print("=" * 80)
    print("EXPORTING CANCER EXCLUSIONS")
    print("=" * 80)
    
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    df = pd.read_excel(excel_file)
    print(f"\n📊 Found {len(df)} rows")
    
    # Structure: {cancer_type: {subtype: {groups: [...], note: "...", links: "..."}}}
    cancer_exclusions = {}
    
    for _, row in df.iterrows():
        cancer_type = str(row['Cancer Type']).strip()
        subtype = str(row['Common Subtypes']).strip() if pd.notna(row['Common Subtypes']) else None
        excluded_ingredients = str(row['Excluded Ingredients']).strip() if pd.notna(row['Excluded Ingredients']) else ""
        note = str(row['Note']).strip() if pd.notna(row['Note']) else ""
        links = str(row['Links']).strip() if pd.notna(row['Links']) else ""
        
        # Parse excluded ingredients (comma-separated group names)
        group_names = [g.strip() for g in excluded_ingredients.split(',') if g.strip()] if excluded_ingredients else []
        
        # Initialize cancer type if not exists
        if cancer_type not in cancer_exclusions:
            cancer_exclusions[cancer_type] = {
                "type_level": {
                    "exclusion_groups": [],
                    "note": "",
                    "links": ""
                },
                "subtypes": {}
            }
        
        # If subtype is None/NaN, this is a type-level exclusion
        if subtype is None or subtype == "nan" or subtype == "":
            cancer_exclusions[cancer_type]["type_level"]["exclusion_groups"] = group_names
            cancer_exclusions[cancer_type]["type_level"]["note"] = note
            cancer_exclusions[cancer_type]["type_level"]["links"] = links
            print(f"\n✅ {cancer_type} (type-level): {len(group_names)} groups")
        else:
            # Subtype-specific exclusion
            cancer_exclusions[cancer_type]["subtypes"][subtype] = {
                "exclusion_groups": group_names,
                "note": note,
                "links": links
            }
            print(f"   ✅ {cancer_type} → {subtype}: {len(group_names)} groups")
    
    # Create output structure
    output_data = {
        "cancer_exclusions": cancer_exclusions,
        "metadata": {
            "export_date": pd.Timestamp.now().isoformat(),
            "total_cancer_types": len(cancer_exclusions)
        }
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Exported to: {output_file}")
    print(f"📊 Total cancer types: {len(cancer_exclusions)}")
    print("=" * 80)
    
    return output_data

if __name__ == "__main__":
    export_cancer_exclusions()

