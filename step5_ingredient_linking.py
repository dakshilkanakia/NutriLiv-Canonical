"""
Stage 2 Processor - Step 5: Ingredient Linking
Extract ingredient name and match against Ingredient Table
"""

import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from config import FUZZY_MATCH_THRESHOLD_ACCEPT, FUZZY_MATCH_THRESHOLD_REVIEW


def extract_ingredient_name(ingredient_text: str, qty_str: str, unit_str: str, 
                            meaning_tokens: Dict) -> Dict:
    """
    Extract clean ingredient name from full ingredient text
    
    Args:
        ingredient_text: Full ingredient line text
        qty_str: Quantity string to remove
        unit_str: Unit string to remove
        meaning_tokens: Dict of meaning-carrying tokens to preserve/remove
    
    Returns:
        Dict with candidate_text_raw, candidate_normalized, extraction_notes
    """
    result = {
        "candidate_text_raw": "",
        "candidate_normalized": "",
        "extraction_notes": []
    }
    
    if not ingredient_text:
        return result
    
    # Start with full text
    text = ingredient_text.strip()
    
    # Remove quantity
    if qty_str and qty_str.strip():
        # Escape special regex characters
        qty_pattern = re.escape(qty_str.strip())
        text = re.sub(f'^{qty_pattern}\\s*', '', text, flags=re.IGNORECASE)
    
    # Remove unit
    if unit_str and unit_str.strip():
        unit_pattern = re.escape(unit_str.strip())
        text = re.sub(f'^{unit_pattern}\\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(f'\\s+{unit_pattern}\\s+', ' ', text, flags=re.IGNORECASE)
    
    # Remove "of" after unit (e.g., "1 cup of sugar" -> "sugar")
    text = re.sub(r'^of\s+', '', text, flags=re.IGNORECASE)
    
    result["candidate_text_raw"] = text.strip()
    
    # Check for "or" (multi-ingredient)
    if re.search(r'\bor\b', text, re.IGNORECASE):
        result["extraction_notes"].append("MULTI_INGREDIENT_OR")
    
    if re.search(r'\band\b', text, re.IGNORECASE):
        result["extraction_notes"].append("MULTI_INGREDIENT_AND")
    
    # Normalize for matching
    normalized = normalize_ingredient_name(text, meaning_tokens)
    result["candidate_normalized"] = normalized
    
    return result


def normalize_ingredient_name(text: str, meaning_tokens: Dict) -> str:
    """
    Normalize ingredient name for matching
    - Lowercase
    - Remove prep modifiers (but keep meaning-carrying descriptors)
    - Singularize
    """
    if not text:
        return ""
    
    text = text.lower().strip()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove prep/quality modifiers that don't identify the ingredient
    remove_modifiers = [
        'fresh', 'organic', 'large', 'small', 'medium',
        'chopped', 'diced', 'minced', 'sliced', 'shredded', 'grated',
        'finely', 'coarsely', 'roughly', 'thinly', 'thickly',
        'ripe', 'unripe', 'raw', 'cooked',
        'peeled', 'unpeeled', 'pitted', 'seeded',
        'trimmed', 'cleaned', 'rinsed', 'drained',
        'thawed', 'frozen',
        'room temperature', 'cold', 'warm',
        'cut into pieces', 'cut into', 'pieces',
        'plus more', 'as needed', 'to taste'
    ]
    
    for modifier in remove_modifiers:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(modifier) + r'\b'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove extra spaces again
    text = ' '.join(text.split())
    
    # Basic singularization
    if text.endswith('ies') and len(text) > 4:
        text = text[:-3] + 'y'
    elif text.endswith('es') and len(text) > 3:
        # Don't remove 'es' from words ending in 'es' naturally
        if not any(text.endswith(ending) for ending in ['oes', 'ses', 'xes', 'zes', 'ches', 'shes']):
            text = text[:-2]
    elif text.endswith('s') and not text.endswith('ss') and len(text) > 2:
        text = text[:-1]
    
    return text.strip()


def match_ingredient(candidate_name: str, reference_data, extraction_notes: List[str]) -> Dict:
    """
    Match ingredient name against reference table using layered approach
    
    Returns dict with:
        - ingredient_id: str or None
        - ingredient_canonical_name: str or None
        - match_score: float
        - match_method: str (exact|alias|normalized|fuzzy|manual)
        - needs_review: bool
        - match_candidates: list of top candidates (if review needed)
    """
    result = {
        "ingredient_id": None,
        "ingredient_canonical_name": None,
        "match_score": 0.0,
        "match_method": None,
        "needs_review": False,
        "match_candidates": [],
        "link_error": None
    }
    
    # Check for multi-ingredient (should be flagged)
    if "MULTI_INGREDIENT_OR" in extraction_notes or "MULTI_INGREDIENT_AND" in extraction_notes:
        result["link_error"] = "MULTI_INGREDIENT_LINE"
        result["needs_review"] = True
        return result
    
    if not candidate_name or candidate_name.strip() == "":
        result["link_error"] = "EMPTY_INGREDIENT_NAME"
        result["needs_review"] = True
        return result
    
    candidate_normalized = candidate_name.lower().strip()
    
    # Layer 0: Exact match on primary name
    if candidate_normalized in reference_data.ingredients_by_name:
        ing_id = reference_data.ingredients_by_name[candidate_normalized]
        result["ingredient_id"] = ing_id
        result["ingredient_canonical_name"] = reference_data.ingredients[ing_id]["primary_name"]
        result["match_score"] = 1.0
        result["match_method"] = "exact"
        return result
    
    # Layer 1: Exact match on alias
    if candidate_normalized in reference_data.ingredients_aliases:
        ing_id = reference_data.ingredients_aliases[candidate_normalized]
        result["ingredient_id"] = ing_id
        result["ingredient_canonical_name"] = reference_data.ingredients[ing_id]["primary_name"]
        result["match_score"] = 0.99
        result["match_method"] = "alias"
        return result
    
    # Layer 2: Fuzzy matching (token-set approach)
    candidates = []
    candidate_tokens = set(candidate_normalized.split())
    
    for ing_id, ing_data in reference_data.ingredients.items():
        primary_name = ing_data["primary_name"].lower()
        primary_tokens = set(primary_name.split())
        
        # Jaccard similarity
        intersection = candidate_tokens & primary_tokens
        union = candidate_tokens | primary_tokens
        
        if len(union) > 0:
            score = len(intersection) / len(union)
            
            if score > 0.5:  # Only consider reasonable matches
                candidates.append({
                    "ingredient_id": ing_id,
                    "primary_name": ing_data["primary_name"],
                    "score": score
                })
    
    # Sort by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    if candidates:
        best = candidates[0]
        
        if best["score"] >= FUZZY_MATCH_THRESHOLD_ACCEPT:
            # Auto-accept
            result["ingredient_id"] = best["ingredient_id"]
            result["ingredient_canonical_name"] = best["primary_name"]
            result["match_score"] = best["score"]
            result["match_method"] = "fuzzy"
            return result
        
        elif best["score"] >= FUZZY_MATCH_THRESHOLD_REVIEW:
            # Needs review
            result["needs_review"] = True
            result["match_candidates"] = candidates[:3]  # Top 3
            result["link_error"] = "LOW_CONFIDENCE"
            return result
    
    # No match found
    result["link_error"] = "NO_MATCH"
    result["needs_review"] = True
    return result


def test_ingredient_extractor():
    """Test ingredient name extraction"""
    test_cases = [
        ("1/2 cup chia seeds", "1/2", "cup", "chia seeds"),
        ("1 tbsp dried goji berries", "1", "tbsp", "goji berries"),
        ("2 tbsp chopped fresh mint leaves", "2", "tbsp", "mint leaves"),
        ("1 ripe banana cut into pieces", "1", "", "banana"),
        ("4 cups minced red onions", "4", "cups", "red onions"),
        ("2 green onions minced", "2", "", "green onions"),
    ]
    
    print("Testing Ingredient Name Extraction:")
    print("=" * 80)
    
    meaning_tokens = {}  # Empty for now
    
    for text, qty, unit, expected in test_cases:
        result = extract_ingredient_name(text, qty, unit, meaning_tokens)
        candidate = result["candidate_text_raw"]
        
        print(f"Input: '{text}'")
        print(f"  -> Raw: '{candidate}'")
        print(f"  -> Normalized: '{result['candidate_normalized']}'")
        print(f"  -> Expected: '{expected}'")
        print()


if __name__ == "__main__":
    test_ingredient_extractor()
