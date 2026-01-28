#!/usr/bin/env python3
"""
Export Supplements from Excel to JSON

Reads Supplements Table.xlsx and exports supplement data for Firebase.
"""

import pandas as pd
import json
import os
from pathlib import Path

def parse_list_field(value):
    """Parse JSON-like list string or return empty list"""
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return []
    
    value_str = str(value).strip()
    
    # Check if it's a JSON array string
    if value_str.startswith('[') and value_str.endswith(']'):
        try:
            import ast
            return ast.literal_eval(value_str)
        except:
            pass
    
    # Fallback: split by comma
    return [item.strip() for item in value_str.split(',') if item.strip()]

def export_supplements():
    """Export supplements from Excel to JSON"""
    
    base_path = Path(__file__).parent
    excel_file = base_path / "Supplements Table.xlsx"
    output_file = base_path / "flutter_assets" / "supplements.json"
    
    print("=" * 80)
    print("EXPORTING SUPPLEMENTS")
    print("=" * 80)
    
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    df = pd.read_excel(excel_file)
    print(f"\n📊 Found {len(df)} supplements")
    print(f"📋 Columns: {list(df.columns)}")
    
    supplements = {}
    
    for _, row in df.iterrows():
        supplement_id = str(row['Supplement_ID']).strip()
        
        if pd.isna(supplement_id) or supplement_id == "":
            continue
        
        # Parse list fields
        metabolic_pathways = parse_list_field(row.get('Metabolic pathways blocked'))
        improved_treatments = parse_list_field(row.get('Improved standard treatments'))
        reduced_effects = parse_list_field(row.get('Reduced adverse effects'))
        
        supplement_data = {
            "supplement_id": supplement_id,
            "item_name": str(row.get('Item name', '')).strip() if pd.notna(row.get('Item name')) else "",
            "anti_cancer_stem_cell": str(row.get('Anti cancer stem cell', '')).strip() if pd.notna(row.get('Anti cancer stem cell')) else "",
            "metabolic_pathways_blocked": metabolic_pathways,
            "improved_standard_treatments": improved_treatments,
            "reduced_adverse_effects": reduced_effects,
            "nutri_points": int(row.get('Nutri points', 0)) if pd.notna(row.get('Nutri points')) else 0
        }
        
        supplements[supplement_id] = supplement_data
    
    # Create output structure
    output_data = {
        "supplements": supplements,
        "metadata": {
            "export_date": pd.Timestamp.now().isoformat(),
            "total_supplements": len(supplements)
        }
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Exported to: {output_file}")
    print(f"📊 Total supplements: {len(supplements)}")
    print("=" * 80)
    
    # Show sample
    if supplements:
        sample_id = list(supplements.keys())[0]
        print(f"\n📝 Sample supplement ({sample_id}):")
        print(json.dumps(supplements[sample_id], indent=2))
    
    return output_data

if __name__ == "__main__":
    export_supplements()
