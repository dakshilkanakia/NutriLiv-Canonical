#!/usr/bin/env python3
"""
Group Stage 2 Output by Recipe

Takes stage2_output.jsonl (flat list of ingredient lines)
and groups them by recipe_id to create structured recipe objects.

Output: test_recipes_canonical.json
"""

import json
from collections import defaultdict

def group_recipes():
    """Group stage2 output lines by recipe"""
    print("=" * 80)
    print("GROUPING STAGE 2 OUTPUT BY RECIPE")
    print("=" * 80)
    
    # Read stage2_output.jsonl
    input_file = "stage2_output.jsonl"
    print(f"\n📖 Reading: {input_file}")
    
    recipes = defaultdict(lambda: {
        "recipe_id": None,
        "recipe_name": None,
        "base_servings": None,
        "ingredients_canonical": []
    })
    
    total_lines = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            data = json.loads(line)
            recipe_id = data.get('recipe_id')
            
            if not recipe_id:
                print(f"⚠️  Skipping line without recipe_id: {line[:50]}...")
                continue
            
            # Initialize recipe metadata if first time seeing this recipe
            if recipes[recipe_id]["recipe_id"] is None:
                recipes[recipe_id]["recipe_id"] = recipe_id
                recipes[recipe_id]["recipe_name"] = data.get('recipe_name', 'Unknown Recipe')
                recipes[recipe_id]["base_servings"] = data.get('servings', 4)  # Default 4 if not specified
            
            # Add ingredient line to this recipe (extract from stage2 output format)
            ingredient = {
                "line_number": data.get('ingredient_line_number'),
                "original_text": data.get('ingredient_original_text'),
                "ingredient_id": data.get('ingredient_id'),
                "ingredient_name": data.get('ingredient_canonical_name'),
                "canonical_qty": data.get('canonical_qty'),
                "canonical_unit": data.get('canonical_unit'),
                "form_id": data.get('resolved_form_id'),
                "quantity_original": data.get('qty_value_original'),
                "unit_original": data.get('unit_original'),
                # Include useful metadata for rendering
                "density_g_per_ml": data.get('density_g_per_ml'),
                "conversion_path": data.get('conversion_path')
            }
            
            recipes[recipe_id]["ingredients_canonical"].append(ingredient)
            total_lines += 1
    
    # Convert to regular dict and sort ingredients by line_number
    recipes_dict = {}
    for recipe_id, recipe_data in recipes.items():
        # Sort ingredients by line number (handle None values)
        recipe_data["ingredients_canonical"].sort(
            key=lambda x: x.get("line_number") if x.get("line_number") is not None else 999
        )
        recipes_dict[recipe_id] = recipe_data
    
    print(f"\n✅ Processed {total_lines} ingredient lines")
    print(f"✅ Grouped into {len(recipes_dict)} recipes")
    
    # Print summary
    print(f"\n📊 Recipe Summary:")
    for recipe_id, recipe_data in sorted(recipes_dict.items()):
        name = recipe_data['recipe_name']
        servings = recipe_data['base_servings']
        num_ingredients = len(recipe_data['ingredients_canonical'])
        print(f"   • {recipe_id}: {name} ({num_ingredients} ingredients, {servings} servings)")
    
    # Write output
    output_file = "test_recipes_canonical.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recipes_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved to: {output_file}")
    
    # Calculate file size
    import os
    file_size = os.path.getsize(output_file)
    print(f"📦 Size: {file_size / 1024:.1f} KB")
    
    print("\n" + "=" * 80)
    print("✅ GROUPING COMPLETE!")
    print("=" * 80)
    
    return recipes_dict

if __name__ == "__main__":
    recipes = group_recipes()
    
    # Print a sample recipe for verification
    if recipes:
        sample_id = list(recipes.keys())[0]
        sample = recipes[sample_id]
        print(f"\n📋 SAMPLE RECIPE: {sample['recipe_name']}")
        print(f"   Base servings: {sample['base_servings']}")
        print(f"   Ingredients:")
        for ing in sample['ingredients_canonical'][:3]:  # Show first 3
            print(f"      {ing['line_number']}. {ing['canonical_qty']} {ing['canonical_unit']} {ing['ingredient_name']}")
        if len(sample['ingredients_canonical']) > 3:
            print(f"      ... and {len(sample['ingredients_canonical']) - 3} more")

