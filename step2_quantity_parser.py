"""
Stage 2 Processor - Step 2: Quantity Parsing
Converts qty_value_original to numeric qty_min and qty_max
"""

import re
from typing import Tuple, Dict, List
from config import UNICODE_FRACTIONS


def parse_quantity(qty_str: str) -> Dict:
    """
    Parse quantity string to numeric values
    
    Returns dict with:
        - qty_min: float
        - qty_max: float
        - qty_is_range: bool
        - qty_approx_flag: bool
        - qty_precision_code: str
        - qty_parse_warnings: list
    """
    result = {
        "qty_min": None,
        "qty_max": None,
        "qty_is_range": False,
        "qty_approx_flag": False,
        "qty_precision_code": "exact",
        "qty_parse_warnings": []
    }
    
    if not qty_str or qty_str.strip() == "":
        return result
    
    # Normalize
    qty_str = qty_str.strip()
    
    # Check for approximation markers
    approx_patterns = [r'about\s+', r'≈\s*', r'~\s*', r'around\s+', r'\+$']
    for pattern in approx_patterns:
        if re.search(pattern, qty_str, re.IGNORECASE):
            result["qty_approx_flag"] = True
            qty_str = re.sub(pattern, '', qty_str, flags=re.IGNORECASE).strip()
    
    # Handle text numbers
    text_numbers = {
        'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'half': 0.5, 'quarter': 0.25, 'third': 0.3333
    }
    
    qty_lower = qty_str.lower().strip()
    if qty_lower in text_numbers:
        value = text_numbers[qty_lower]
        result["qty_min"] = value
        result["qty_max"] = value
        result["qty_precision_code"] = "text_number"
        result["qty_parse_warnings"].append("TEXT_NUMBER_FALLBACK")
        return result
    
    # Special case: "pinch", "dash", etc - these are handled as special units
    special_qty = ['pinch', 'dash', 'handful', 'splash', 'drizzle']
    if qty_lower in special_qty:
        # Return null - will be handled as special unit
        return result
    
    # Replace Unicode fractions
    for unicode_char, ascii_frac in UNICODE_FRACTIONS.items():
        qty_str = qty_str.replace(unicode_char, f" {ascii_frac} ")
    
    # Remove commas (thousands separator)
    qty_str = qty_str.replace(',', '')
    
    # Check for range patterns
    range_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:--|—|to|-)\s*(\d+(?:\.\d+)?)',  # 1-2, 1--2, 1 to 2
        r'(\d+\s+\d+/\d+)\s*(?:--|—|to|-)\s*(\d+\s+\d+/\d+)',    # 1 1/2--2 1/2
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, qty_str)
        if match:
            min_str = match.group(1).strip()
            max_str = match.group(2).strip()
            
            result["qty_min"] = parse_single_number(min_str)
            result["qty_max"] = parse_single_number(max_str)
            result["qty_is_range"] = True
            
            if result["qty_min"] is not None and result["qty_max"] is not None:
                return result
    
    # Try to parse as single number
    value = parse_single_number(qty_str)
    
    if value is not None:
        result["qty_min"] = value
        result["qty_max"] = value
        return result
    
    # Failed to parse
    result["qty_parse_warnings"].append("PARSE_FAILED")
    return result


def parse_single_number(num_str: str) -> float:
    """
    Parse a single number (can be mixed, fraction, or decimal)
    
    Examples:
        "1 1/2" -> 1.5
        "1-1/2" -> 1.5
        "3/4" -> 0.75
        "2.5" -> 2.5
    """
    if not num_str:
        return None
    
    num_str = num_str.strip()
    
    # Mixed number with hyphen: "1-1/2"
    match = re.match(r'^(\d+)-(\d+)/(\d+)$', num_str)
    if match:
        whole = int(match.group(1))
        numerator = int(match.group(2))
        denominator = int(match.group(3))
        if denominator == 0:
            return None
        return whole + (numerator / denominator)
    
    # Mixed number with space: "1 1/2"
    match = re.match(r'^(\d+)\s+(\d+)/(\d+)$', num_str)
    if match:
        whole = int(match.group(1))
        numerator = int(match.group(2))
        denominator = int(match.group(3))
        if denominator == 0:
            return None
        return whole + (numerator / denominator)
    
    # Simple fraction: "3/4"
    match = re.match(r'^(\d+)/(\d+)$', num_str)
    if match:
        numerator = int(match.group(1))
        denominator = int(match.group(2))
        if denominator == 0:
            return None
        return numerator / denominator
    
    # Decimal or integer
    try:
        return float(num_str)
    except ValueError:
        return None


def test_quantity_parser():
    """Test the quantity parser"""
    test_cases = [
        ("1", 1, 1, False),
        ("1/2", 0.5, 0.5, False),
        ("½", 0.5, 0.5, False),
        ("1 1/2", 1.5, 1.5, False),
        ("1-1/2", 1.5, 1.5, False),
        ("2½", 2.5, 2.5, False),
        ("2.25", 2.25, 2.25, False),
        ("1-2", 1, 2, True),
        ("1--2", 1, 2, True),
        ("1 to 2", 1, 2, True),
        ("about 2", 2, 2, False),
        ("~2", 2, 2, False),
        ("2+", 2, 2, False),
        ("one", 1, 1, False),
        ("", None, None, False),
    ]
    
    print("Testing Quantity Parser:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for qty_str, expected_min, expected_max, expected_range in test_cases:
        result = parse_quantity(qty_str)
        
        success = (
            result["qty_min"] == expected_min and
            result["qty_max"] == expected_max and
            result["qty_is_range"] == expected_range
        )
        
        if success:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        print(f"{status} '{qty_str}' -> min={result['qty_min']}, max={result['qty_max']}, range={result['qty_is_range']}")
    
    print("=" * 60)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()


if __name__ == "__main__":
    test_quantity_parser()
