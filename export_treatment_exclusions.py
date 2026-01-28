#!/usr/bin/env python3
"""
Export Treatment Exclusions from Excel to JSON

Reads Treatments With Exclusion Sample.xlsx and exports
treatment type/drug -> exclusions mapping for Firebase.
"""

import pandas as pd
import json
import os
from pathlib import Path

def parse_exclusion_list(value):
    """Parse comma-separated exclusion list, handling NaN and empty strings"""
    if pd.isna(value) or value == "" or str(value).strip() == "":
        return []
    # Split by comma and strip whitespace
    items = [item.strip() for item in str(value).split(',') if item.strip()]
    return items

def export_treatment_exclusions():
    """Export treatment exclusions from Excel to JSON"""
    
    base_path = Path(__file__).parent
    excel_file = base_path / "Treatments With Exclusion Sample.xlsx"
    output_file = base_path / "flutter_assets" / "treatment_exclusions.json"
    
    print("=" * 80)
    print("EXPORTING TREATMENT EXCLUSIONS")
    print("=" * 80)
    
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    xl_file = pd.ExcelFile(excel_file)
    print(f"\n📊 Found {len(xl_file.sheet_names)} sheets:")
    for name in xl_file.sheet_names:
        print(f"   - {name}")
    
    # Map drug/regimen sheets to treatment types
    sheet_to_treatment = {
        "Chemo Drugs": "Chemotherapy",
        "Hormone Therapy": "Hormone Therapy",
        "Targeted Therapy": "Targeted Therapy",
        "Immunotherapy": "Immunotherapy"
    }
    
    treatment_exclusions = {}
    
    # Step 1: Process "Standard Treatments" sheet (treatment type-level exclusions)
    print("\n" + "=" * 80)
    print("PROCESSING STANDARD TREATMENTS")
    print("=" * 80)
    
    df_standard = pd.read_excel(xl_file, sheet_name="Standard Treatments")
    
    for _, row in df_standard.iterrows():
        treatment_type = str(row['Standard Treatments']).strip()
        
        if pd.isna(treatment_type) or treatment_type == "":
            continue
        
        # Parse exclusions
        excluded_ingredients = parse_exclusion_list(row.get('Excluded Ingredients'))
        excluded_supplements = parse_exclusion_list(row.get('Excluded Supplements'))
        excluded_teas = parse_exclusion_list(row.get('Excluded Teas'))
        note = str(row.get('Note', '')).strip() if pd.notna(row.get('Note')) else ""
        links = str(row.get('Links', '')).strip() if pd.notna(row.get('Links')) else ""
        
        # Initialize treatment type structure
        if treatment_type not in treatment_exclusions:
            treatment_exclusions[treatment_type] = {
                "type_level": {
                    "excluded_ingredients": [],
                    "excluded_supplements": [],
                    "excluded_teas": [],
                    "note": "",
                    "links": ""
                },
                "drugs": {}
            }
        
        # Set type-level exclusions (only if they exist)
        if excluded_ingredients or excluded_supplements or excluded_teas:
            treatment_exclusions[treatment_type]["type_level"]["excluded_ingredients"] = excluded_ingredients
            treatment_exclusions[treatment_type]["type_level"]["excluded_supplements"] = excluded_supplements
            treatment_exclusions[treatment_type]["type_level"]["excluded_teas"] = excluded_teas
            treatment_exclusions[treatment_type]["type_level"]["note"] = note
            treatment_exclusions[treatment_type]["type_level"]["links"] = links
            
            print(f"\n✅ {treatment_type} (type-level):")
            print(f"   Ingredients: {len(excluded_ingredients)}")
            print(f"   Supplements: {len(excluded_supplements)}")
            print(f"   Teas: {len(excluded_teas)}")
        else:
            print(f"\nℹ️  {treatment_type} (type-level): No exclusions")
    
    # Step 2: Process drug/regimen sheets
    print("\n" + "=" * 80)
    print("PROCESSING DRUG/REGIMEN SHEETS")
    print("=" * 80)
    
    for sheet_name in xl_file.sheet_names:
        if sheet_name == "Standard Treatments":
            continue
        
        treatment_type = sheet_to_treatment.get(sheet_name)
        if not treatment_type:
            print(f"\n⚠️  Skipping unknown sheet: {sheet_name}")
            continue
        
        # Ensure treatment type exists
        if treatment_type not in treatment_exclusions:
            treatment_exclusions[treatment_type] = {
                "type_level": {
                    "excluded_ingredients": [],
                    "excluded_supplements": [],
                    "excluded_teas": [],
                    "note": "",
                    "links": ""
                },
                "drugs": {}
            }
        
        df_drugs = pd.read_excel(xl_file, sheet_name=sheet_name)
        drug_column = df_drugs.columns[0]  # First column is drug/regimen name
        
        print(f"\n📋 Processing {sheet_name} → {treatment_type}")
        
        for _, row in df_drugs.iterrows():
            drug_name = str(row[drug_column]).strip()
            
            if pd.isna(drug_name) or drug_name == "":
                continue
            
            # Parse exclusions
            excluded_ingredients = parse_exclusion_list(row.get('Excluded Ingredients'))
            excluded_supplements = parse_exclusion_list(row.get('Excluded Supplements'))
            excluded_teas = parse_exclusion_list(row.get('Excluded Teas'))
            note = str(row.get('Note', '')).strip() if pd.notna(row.get('Note')) else ""
            links = str(row.get('Links', '')).strip() if pd.notna(row.get('Links')) else ""
            
            # Only add if there are exclusions
            if excluded_ingredients or excluded_supplements or excluded_teas:
                treatment_exclusions[treatment_type]["drugs"][drug_name] = {
                    "excluded_ingredients": excluded_ingredients,
                    "excluded_supplements": excluded_supplements,
                    "excluded_teas": excluded_teas,
                    "note": note,
                    "links": links
                }
                print(f"   ✅ {drug_name}: {len(excluded_ingredients)} ingredients, {len(excluded_supplements)} supplements, {len(excluded_teas)} teas")
    
    # Create output structure
    output_data = {
        "treatment_exclusions": treatment_exclusions,
        "metadata": {
            "export_date": pd.Timestamp.now().isoformat(),
            "total_treatment_types": len(treatment_exclusions),
            "total_drugs": sum(len(t["drugs"]) for t in treatment_exclusions.values())
        }
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Write JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Exported to: {output_file}")
    print(f"📊 Total treatment types: {len(treatment_exclusions)}")
    print(f"📊 Total drugs/regimens: {sum(len(t['drugs']) for t in treatment_exclusions.values())}")
    print("=" * 80)
    
    return output_data

if __name__ == "__main__":
    export_treatment_exclusions()
