"""
Stage 2 Processor - Configuration
Stores all constants, file paths, and conversion factors
"""

# ============================================================================
# FILE PATHS - Edit these to match your setup
# ============================================================================

INPUT_FILE = "recipe_sample_251212.jsonl"  # This file should be in the same directory or /mnt/project
OUTPUT_FILE = "stage2_output.jsonl"
ERROR_TXT_FILE = "stage2_errors.txt"
ERROR_JSON_FILE = "stage2_errors.json"

# Reference table paths
INGREDIENT_TABLE = "Ingredient_Table_Populated_Master 251202.xlsx"
FORM_TABLE = "Form_Table_Populated_Complete.xlsx"
DENSITY_TABLE = "Density_Table_Populated - Final 251202.xlsx"
CONVERSION_TABLE = "Unit_Conversion_Constants_Table_Populated.xlsx"
MEANING_TOKENS_FILE = "Meaning-carrying tokens - allow list.txt"

# ============================================================================
# UNIT CONVERSION CONSTANTS (from spec - exact values)
# ============================================================================

# Mass to grams
MASS_TO_GRAMS = {
    "MG": 0.001,
    "G": 1.0,
    "KG": 1000.0,
    "OZ": 28.349523125,
    "LB": 453.59237
}

# Volume to milliliters
VOLUME_TO_ML = {
    "TSP": 4.92892159375,
    "TBSP": 14.78676478125,
    "CUP": 236.5882365,
    "FLOZ": 29.5735295625,
    "PINT": 473.176473,
    "QUART": 946.352946,
    "GALLON": 3785.411784,
    "ML": 1.0,
    "L": 1000.0
}

# ============================================================================
# UNIT SYNONYMS (from spec)
# ============================================================================

UNIT_SYNONYMS = {
    # Mass
    "g": "G", "gram": "G", "grams": "G",
    "kg": "KG", "kilogram": "KG", "kilograms": "KG",
    "mg": "MG", "milligram": "MG", "milligrams": "MG",
    "oz": "OZ", "ounce": "OZ", "ounces": "OZ",
    "lb": "LB", "lbs": "LB", "pound": "LB", "pounds": "LB",
    
    # Volume
    "ml": "ML", "milliliter": "ML", "milliliters": "ML", "millilitre": "ML", "millilitres": "ML",
    "l": "L", "liter": "L", "liters": "L", "litre": "L", "litres": "L",
    "tsp": "TSP", "teaspoon": "TSP", "teaspoons": "TSP",
    "tbsp": "TBSP", "tablespoon": "TBSP", "tablespoons": "TBSP", "t": "TBSP", "tbl": "TBSP", "tbs": "TBSP",
    "cup": "CUP", "cups": "CUP", "c": "CUP",
    "fl oz": "FLOZ", "fl. oz": "FLOZ", "fl. oz.": "FLOZ", "fluid ounce": "FLOZ", "fluid ounces": "FLOZ",
    "pt": "PINT", "pint": "PINT", "pints": "PINT",
    "qt": "QUART", "quart": "QUART", "quarts": "QUART",
    "gal": "GALLON", "gallon": "GALLON", "gallons": "GALLON",
    
    # Count
    "each": "EA", "ea": "EA", "piece": "EA", "pieces": "EA",
    "clove": "CLOVE", "cloves": "CLOVE",
    "egg": "EGG", "eggs": "EGG",
    "leaf": "LEAF", "leaves": "LEAF",
    "sprig": "SPRIG", "sprigs": "SPRIG",
    "stalk": "STALK", "stalks": "STALK",
    "head": "HEAD", "heads": "HEAD",
    "ear": "EAR", "ears": "EAR",
    "slice": "SLICE", "slices": "SLICE",
    "bunch": "BUNCH", "bunches": "BUNCH",
    "can": "CAN", "cans": "CAN",
    "jar": "JAR", "jars": "JAR",
    "bottle": "BOTTLE", "bottles": "BOTTLE",
    "package": "PACKAGE", "pkg": "PACKAGE", "pack": "PACKAGE", "packet": "PACKAGE",
    "stick": "STICK", "sticks": "STICK",
    
    # Specials
    "to taste": "TO_TASTE",
    "as needed": "AS_NEEDED",
    "pinch": "PINCH",
    "dash": "DASH",
    "handful": "HANDFUL",
    "splash": "SPLASH",
    "drizzle": "DRIZZLE"
}

# ============================================================================
# DIMENSION MAPPING
# ============================================================================

UNIT_DIMENSIONS = {
    # Mass
    "G": "mass", "KG": "mass", "MG": "mass", "OZ": "mass", "LB": "mass",
    
    # Volume
    "ML": "volume", "L": "volume", "TSP": "volume", "TBSP": "volume",
    "CUP": "volume", "FLOZ": "volume", "PINT": "volume", "QUART": "volume", "GALLON": "volume",
    
    # Count
    "EA": "count", "CLOVE": "count", "EGG": "count", "LEAF": "count", "SPRIG": "count",
    "STALK": "count", "HEAD": "count", "EAR": "count", "SLICE": "count", "BUNCH": "count",
    "CAN": "count", "JAR": "count", "BOTTLE": "count", "PACKAGE": "count", "STICK": "count",
    
    # Specials
    "TO_TASTE": "special", "AS_NEEDED": "special", "PINCH": "special",
    "DASH": "special", "HANDFUL": "special", "SPLASH": "special", "DRIZZLE": "special"
}

# ============================================================================
# UNICODE FRACTION MAP (from spec)
# ============================================================================

UNICODE_FRACTIONS = {
    "¼": "1/4",
    "½": "1/2",
    "¾": "3/4",
    "⅐": "1/7",
    "⅑": "1/9",
    "⅒": "1/10",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8"
}

# ============================================================================
# FORM TOKEN MAPPING (from spec)
# ============================================================================

FORM_TOKEN_MAP = {
    # Ground/Powder
    "ground": "FORM_GROUND",
    "powder": "FORM_POWDER",
    "powdered": "FORM_POWDER",
    
    # Whole
    "whole": "FORM_WHOLE",
    
    # Cut/Chopped
    "sliced": "FORM_SLICED",
    "chopped": "FORM_CHOPPED",
    "diced": "FORM_CHOPPED",
    "minced": "FORM_CHOPPED",
    
    # Grated
    "grated": "FORM_GRATED",
    "shredded": "FORM_GRATED",
    
    # Mashed
    "mashed": "FORM_MASHED",
    "puree": "FORM_MASHED",
    "purée": "FORM_MASHED",
    
    # Dried
    "dried": "FORM_DRIED",
    "dehydrated": "FORM_DRIED",
    
    # Canned/Jarred
    "canned": "FORM_CANNED",
    "tinned": "FORM_CANNED",
    "jarred": "FORM_JARRED",
    
    # Seeds
    "seed": "FORM_SEEDS",
    "seeds": "FORM_SEEDS",
}

# ============================================================================
# MATCHING THRESHOLDS
# ============================================================================

FUZZY_MATCH_THRESHOLD_ACCEPT = 0.88  # Lowered from 0.92 for better matching
FUZZY_MATCH_THRESHOLD_REVIEW = 0.75  # Lowered from 0.80

# ============================================================================
# PRECISION SETTINGS
# ============================================================================

DECIMAL_PRECISION = 6
ROUNDING_EPSILON = 1e-9
