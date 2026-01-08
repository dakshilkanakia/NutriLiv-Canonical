"""
Stage 2 Processor - Step 3: Unit Normalization
Maps unit_original to canonical unit_enum and determines dimension
"""

import re
from typing import Dict, Optional
from config import UNIT_SYNONYMS, UNIT_DIMENSIONS


def normalize_unit(unit_str: str) -> Dict:
    """
    Normalize unit string to canonical enum
    
    Returns dict with:
        - unit_enum: str (canonical unit code)
        - original_dimension: str (mass|volume|count|special)
        - flag_nonstandard_unit: bool
        - unit_normalization_notes: str
    """
    result = {
        "unit_enum": None,
        "original_dimension": None,
        "flag_nonstandard_unit": False,
        "unit_normalization_notes": ""
    }
    
    if not unit_str or unit_str.strip() == "":
        # Empty unit - will be EA (each) by default
        result["unit_enum"] = "EA"
        result["original_dimension"] = "count"
        result["unit_normalization_notes"] = "empty_unit_defaulted_to_ea"
        return result
    
    # Normalize the token
    normalized = unit_str.lower().strip()
    
    # Remove trailing periods
    normalized = normalized.rstrip('.')
    
    # Collapse multiple spaces
    normalized = ' '.join(normalized.split())
    
    # Special check for fl oz (must have "fl" to be fluid ounce)
    if 'fl' in normalized and 'oz' in normalized:
        normalized = 'fl oz'
    
    # Look up in synonym dictionary
    if normalized in UNIT_SYNONYMS:
        unit_enum = UNIT_SYNONYMS[normalized]
        result["unit_enum"] = unit_enum
        result["original_dimension"] = UNIT_DIMENSIONS.get(unit_enum, "unknown")
        return result
    
    # Try without pluralization
    if normalized.endswith('s') and len(normalized) > 2:
        singular = normalized[:-1]
        if singular in UNIT_SYNONYMS:
            unit_enum = UNIT_SYNONYMS[singular]
            result["unit_enum"] = unit_enum
            result["original_dimension"] = UNIT_DIMENSIONS.get(unit_enum, "unknown")
            return result
    
    # Not found - flag as nonstandard but default to 'EA' (count) to keep pipeline moving
    result["flag_nonstandard_unit"] = True
    result["unit_enum"] = "EA"
    result["original_dimension"] = "count"
    result["unit_normalization_notes"] = f"unrecognized_unit:{normalized}|defaulted_to_ea"
    return result


def test_unit_normalizer():
    """Test the unit normalizer"""
    test_cases = [
        # Mass
        ("g", "G", "mass"),
        ("grams", "G", "mass"),
        ("kg", "KG", "mass"),
        ("oz", "OZ", "mass"),
        ("lbs", "LB", "mass"),
        
        # Volume
        ("ml", "ML", "volume"),
        ("cup", "CUP", "volume"),
        ("cups", "CUP", "volume"),
        ("tbsp", "TBSP", "volume"),
        ("tsp", "TSP", "volume"),
        ("fl oz", "FLOZ", "volume"),
        
        # Count
        ("eggs", "EGG", "count"),
        ("cloves", "CLOVE", "count"),
        ("bunch", "BUNCH", "count"),
        ("can", "CAN", "count"),
        ("stalks", "STALK", "count"),
        ("", "EA", "count"),  # Empty unit
        
        # Specials
        ("to taste", "TO_TASTE", "special"),
        ("pinch", "PINCH", "special"),
        ("dash", "DASH", "special"),
    ]
    
    print("Testing Unit Normalizer:")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for unit_str, expected_enum, expected_dim in test_cases:
        result = normalize_unit(unit_str)
        
        success = (
            result["unit_enum"] == expected_enum and
            result["original_dimension"] == expected_dim
        )
        
        if success:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} '{unit_str}' -> {result['unit_enum']} ({result['original_dimension']})")
    
    print("=" * 80)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()


if __name__ == "__main__":
    test_unit_normalizer()
