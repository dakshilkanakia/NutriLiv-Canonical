#!/usr/bin/env python3
"""
Export Pantry Levels to JSON

Converts Pantry_Levels_completed.xlsx to JSON format for Firebase upload.
Groups ingredients by stock level (Basic, Average, Well-stocked).

Created: December 29, 2024
"""

import json
import pandas as pd
import sys
from pathlib import Path

def export_pantry_levels():
    """Export pantry levels Excel to JSON"""
    
    input_file = Path('Pantry_Levels_completed.xlsx')
    output_file = Path('flutter_assets/pantry_levels.json')
    
    if not input_file.exists():
        print(f'❌ Error: {input_file} not found')
        sys.exit(1)
    
    print(f'📖 Reading {input_file}...')
    
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f'❌ Error reading Excel: {e}')
        sys.exit(1)
    
    # Validate columns
    required_cols = ['ingredient_name', 'stock_level', 'Ingredient_ID']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f'❌ Missing columns: {missing_cols}')
        sys.exit(1)
    
    # Group by stock level
    pantry_levels = {
        'Basic': [],
        'Average': [],
        'Well-stocked': [],
    }
    
    for _, row in df.iterrows():
        stock_level = str(row['stock_level']).strip()
        ingredient_id = str(row['Ingredient_ID']).strip()
        ingredient_name = str(row['ingredient_name']).strip()
        
        if not ingredient_id or ingredient_id == 'nan':
            continue
        
        if stock_level not in pantry_levels:
            print(f'⚠️ Unknown stock level: {stock_level}, skipping')
            continue
        
        pantry_levels[stock_level].append({
            'ingredient_id': ingredient_id,
            'ingredient_name': ingredient_name,
        })
    
    # Create final structure
    output_data = {
        'pantry_levels': pantry_levels,
        'metadata': {
            'total_ingredients': len(df),
            'basic_count': len(pantry_levels['Basic']),
            'average_count': len(pantry_levels['Average']),
            'well_stocked_count': len(pantry_levels['Well-stocked']),
            'export_date': pd.Timestamp.now().isoformat(),
        }
    }
    
    # Write JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f'✅ Exported to {output_file}')
    print(f'   Basic: {len(pantry_levels["Basic"])} ingredients')
    print(f'   Average: {len(pantry_levels["Average"])} ingredients')
    print(f'   Well-stocked: {len(pantry_levels["Well-stocked"])} ingredients')
    print(f'   Total: {len(df)} ingredients')
    
    return output_file

if __name__ == '__main__':
    export_pantry_levels()

