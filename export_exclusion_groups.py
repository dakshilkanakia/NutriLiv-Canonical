#!/usr/bin/env python3
"""
Export Exclusion Groups from Excel to JSON

Reads Exclusion Groups.xlsx where each sheet name is a group name
and contains ingredient_id rows. Exports to JSON format for Firebase.
"""

import pandas as pd
import json
import os
from pathlib import Path

def export_exclusion_groups():
    """Export exclusion groups from Excel to JSON"""
    
    base_path = Path(__file__).parent
    excel_file = base_path / "Exclusion Groups.xlsx"
    output_file = base_path / "flutter_assets" / "exclusion_groups.json"
    
    print("=" * 80)
    print("EXPORTING EXCLUSION GROUPS")
    print("=" * 80)
    
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    # Read all sheets
    xl_file = pd.ExcelFile(excel_file)
    print(f"\n📊 Found {len(xl_file.sheet_names)} exclusion groups:")
    for name in xl_file.sheet_names:
        print(f"   - {name}")
    
    exclusion_groups = {}
    
    for sheet_name in xl_file.sheet_names:
        df = pd.read_excel(xl_file, sheet_name=sheet_name)
        
        # Extract ingredient_ids (ignore primary_name, only use ingredient_id)
        ingredient_ids = df['ingredient_id'].dropna().unique().tolist()
        
        # Filter out any invalid ingredient IDs
        ingredient_ids = [str(id).strip() for id in ingredient_ids 
                         if str(id).strip().startswith('INGR_')]
        
        if ingredient_ids:
            exclusion_groups[sheet_name] = ingredient_ids
            print(f"\n✅ {sheet_name}: {len(ingredient_ids)} ingredients")
        else:
            print(f"\n⚠️  {sheet_name}: No valid ingredient IDs found")
    
    # Create output structure
    output_data = {
        "exclusion_groups": exclusion_groups,
        "metadata": {
            "export_date": pd.Timestamp.now().isoformat(),
            "total_groups": len(exclusion_groups),
            "total_ingredients": sum(len(ids) for ids in exclusion_groups.values())
        }
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Exported to: {output_file}")
    print(f"📊 Total groups: {len(exclusion_groups)}")
    print(f"📊 Total ingredients: {sum(len(ids) for ids in exclusion_groups.values())}")
    print("=" * 80)
    
    return output_data

if __name__ == "__main__":
    export_exclusion_groups()

