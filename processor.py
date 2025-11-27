"""
Stage 2 Processor - Main Orchestrator
Processes Stage 1 JSONL through the complete 9-step pipeline
"""

import json
import os
from typing import Dict, List
from datetime import datetime

# Import all modules
from data_loader import load_all_reference_data
from step2_quantity_parser import parse_quantity
from step3_unit_normalizer import normalize_unit
from step5_ingredient_linking import extract_ingredient_name, match_ingredient
from steps6_9_form_and_conversion import (
    resolve_form, select_canonical_dimension, 
    lookup_density, convert_to_canonical
)


class ErrorTracker:
    """Track all errors encountered during processing"""
    def __init__(self):
        self.errors = {
            "missing_ingredients": [],
            "missing_densities": [],
            "parsing_failures": [],
            "unit_not_recognized": [],
            "multi_ingredient_lines": [],
            "other_errors": []
        }
        self.successful = 0
        self.failed = 0
    
    def add_error(self, error_type: str, data: Dict):
        """Add an error to tracking"""
        if error_type in self.errors:
            self.errors[error_type].append(data)
        else:
            self.errors["other_errors"].append({"type": error_type, "data": data})
        self.failed += 1
    
    def add_success(self):
        """Increment success counter"""
        self.successful += 1
    
    def get_summary(self) -> Dict:
        """Get error summary"""
        total = self.successful + self.failed
        return {
            "total": total,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.successful / total if total > 0 else 0,
            "error_counts": {k: len(v) for k, v in self.errors.items() if v}
        }


def process_ingredient_line(stage1_data: Dict, reference_data, error_tracker: ErrorTracker) -> Dict:
    """
    Process a single ingredient line through all 9 steps
    
    Args:
        stage1_data: Dict with Stage 1 fields
        reference_data: Reference data loaded from Excel
        error_tracker: Error tracking object
    
    Returns:
        Dict with all Stage 2 fields, or None if critical error
    """
    stage2_data = {**stage1_data}  # Start with Stage 1 data
    
    # Extract input fields
    recipe_id = stage1_data.get("recipe_id")
    line_number = stage1_data.get("ingredient_line_number")
    ingredient_text = stage1_data.get("ingredient_original_text", "")
    qty_original = stage1_data.get("qty_value_original", "")
    unit_original = stage1_data.get("unit_original", "")
    form_hint_raw = stage1_data.get("form_hint_raw", "")
    
    # ========================================================================
    # STEP 1: INTAKE & VALIDATION (already done in Stage 1, skip)
    # ========================================================================
    
    # ========================================================================
    # STEP 2: QUANTITY PARSING
    # ========================================================================
    qty_result = parse_quantity(qty_original)
    stage2_data.update(qty_result)
    
    qty_min = qty_result["qty_min"]
    qty_max = qty_result["qty_max"]
    
    if qty_min is None and qty_max is None:
        # Check if this is a special case
        pass  # Continue - might be "to taste" or similar
    
    # ========================================================================
    # STEP 3: UNIT NORMALIZATION
    # ========================================================================
    unit_result = normalize_unit(unit_original)
    stage2_data.update(unit_result)
    
    unit_enum = unit_result["unit_enum"]
    original_dimension = unit_result["original_dimension"]
    
    # ========================================================================
    # STEP 4: PACKAGE PARSING (skip for now - not critical)
    # ========================================================================
    # TODO: Implement if needed
    
    # ========================================================================
    # STEP 5: INGREDIENT LINKING
    # ========================================================================
    extraction_result = extract_ingredient_name(
        ingredient_text, qty_original, unit_original, reference_data.meaning_tokens
    )
    
    candidate_name = extraction_result["candidate_normalized"]
    extraction_notes = extraction_result["extraction_notes"]
    
    match_result = match_ingredient(candidate_name, reference_data, extraction_notes)
    stage2_data.update(match_result)
    
    ingredient_id = match_result["ingredient_id"]
    
    # Check for linking errors
    if match_result.get("link_error"):
        error_type = match_result["link_error"]
        error_data = {
            "recipe_id": recipe_id,
            "line_number": line_number,
            "original_text": ingredient_text,
            "candidate_name": candidate_name,
            "error": error_type
        }
        
        if error_type == "NO_MATCH":
            error_tracker.add_error("missing_ingredients", error_data)
        elif error_type == "MULTI_INGREDIENT_LINE":
            error_tracker.add_error("multi_ingredient_lines", error_data)
        elif error_type == "LOW_CONFIDENCE":
            error_data["candidates"] = match_result.get("match_candidates", [])
            error_tracker.add_error("missing_ingredients", error_data)
        
        # Can't continue without ingredient
        error_tracker.add_error("parsing_failures", error_data)
        return stage2_data
    
    # ========================================================================
    # STEP 6: FORM RESOLUTION
    # ========================================================================
    form_result = resolve_form(
        ingredient_text, form_hint_raw, ingredient_id, unit_enum,
        reference_data, reference_data.meaning_tokens
    )
    stage2_data.update(form_result)
    
    resolved_form_id = form_result["resolved_form_id"]
    
    # Also add default_form_id for reference
    if ingredient_id in reference_data.ingredients:
        stage2_data["default_form_id"] = reference_data.ingredients[ingredient_id].get("default_form_id")
    
    # ========================================================================
    # STEP 7: CANONICAL DIMENSION SELECTION
    # ========================================================================
    dimension_result = select_canonical_dimension(
        unit_enum, original_dimension, resolved_form_id, reference_data
    )
    stage2_data.update(dimension_result)
    
    canonical_unit = dimension_result["canonical_unit"]
    bridge_required = dimension_result["bridge_required"]
    
    # ========================================================================
    # STEP 8: BRIDGING DATA LOOKUP
    # ========================================================================
    density_result = lookup_density(
        ingredient_id, resolved_form_id, bridge_required, reference_data
    )
    stage2_data.update(density_result)
    
    density_g_per_ml = density_result["density_g_per_ml"]
    bridge_inputs_ready = density_result["bridge_inputs_ready"]
    
    # Track missing densities
    if density_result.get("flag_needs_density_lookup"):
        error_data = {
            "recipe_id": recipe_id,
            "line_number": line_number,
            "original_text": ingredient_text,
            "ingredient_id": ingredient_id,
            "ingredient_name": stage2_data.get("ingredient_canonical_name"),
            "form_id": resolved_form_id,
            "conversion_needed": bridge_required
        }
        error_tracker.add_error("missing_densities", error_data)
    
    # ========================================================================
    # STEP 9: DETERMINISTIC CONVERSION TO CANONICAL SI
    # ========================================================================
    conversion_result = convert_to_canonical(
        qty_min, qty_max, unit_enum, canonical_unit,
        bridge_required, density_g_per_ml, original_dimension, reference_data
    )
    stage2_data.update(conversion_result)
    
    # Check if conversion succeeded
    if conversion_result["canonical_qty"] is None and original_dimension != "special":
        error_data = {
            "recipe_id": recipe_id,
            "line_number": line_number,
            "original_text": ingredient_text,
            "conversion_notes": conversion_result.get("conversion_notes")
        }
        error_tracker.add_error("parsing_failures", error_data)
        return stage2_data
    
    # Success!
    error_tracker.add_success()
    return stage2_data


def process_stage1_file(input_file: str, output_file: str, reference_data) -> ErrorTracker:
    """
    Process entire Stage 1 JSONL file
    
    Args:
        input_file: Path to Stage 1 JSONL
        output_file: Path to write Stage 2 JSONL
        reference_data: Loaded reference data
    
    Returns:
        ErrorTracker with all errors
    """
    print("\n" + "=" * 80)
    print(f"PROCESSING STAGE 1 FILE: {input_file}")
    print("=" * 80)
    
    error_tracker = ErrorTracker()
    stage2_results = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_idx, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                stage1_data = json.loads(line)
                stage2_data = process_ingredient_line(stage1_data, reference_data, error_tracker)
                stage2_results.append(stage2_data)
                
                if line_idx % 10 == 0:
                    print(f"  Processed {line_idx} lines...", end='\r')
            
            except json.JSONDecodeError as e:
                print(f"\nError parsing JSON on line {line_idx}: {e}")
                error_tracker.add_error("parsing_failures", {
                    "line_number": line_idx,
                    "error": str(e)
                })
            except Exception as e:
                print(f"\nError processing line {line_idx}: {e}")
                error_tracker.add_error("other_errors", {
                    "line_number": line_idx,
                    "error": str(e)
                })
    
    print(f"\n  Processed {line_idx} lines total")
    
    # Write output
    print(f"\nWriting output to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in stage2_results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print(f"  Wrote {len(stage2_results)} results")
    
    return error_tracker


def write_error_reports(error_tracker: ErrorTracker, txt_file: str, json_file: str):
    """Write error reports in both human and machine-readable formats"""
    summary = error_tracker.get_summary()
    
    # Write text report
    print(f"\nWriting error report (text): {txt_file}")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("STAGE 2 PROCESSING ERROR REPORT\n")
        f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total ingredients processed: {summary['total']}\n")
        f.write(f"✓ Successful: {summary['successful']} ({summary['success_rate']*100:.1f}%)\n")
        f.write(f"✗ Failed: {summary['failed']} ({(1-summary['success_rate'])*100:.1f}%)\n\n")
        
        # Missing ingredients
        if error_tracker.errors["missing_ingredients"]:
            f.write("=" * 80 + "\n")
            f.write(f"MISSING INGREDIENTS ({len(error_tracker.errors['missing_ingredients'])})\n")
            f.write("=" * 80 + "\n")
            for err in error_tracker.errors["missing_ingredients"]:
                f.write(f"Recipe {err['recipe_id']}, Line {err['line_number']}: \"{err['original_text']}\"\n")
                f.write(f"  → Candidate name: {err.get('candidate_name', 'N/A')}\n")
                f.write(f"  → Error: {err['error']}\n")
                if 'candidates' in err:
                    f.write(f"  → Top candidates:\n")
                    for cand in err['candidates'][:3]:
                        f.write(f"     - {cand['primary_name']} (score: {cand['score']:.2f})\n")
                f.write(f"  → Action: Add ingredient to Ingredient Table\n\n")
        
        # Missing densities
        if error_tracker.errors["missing_densities"]:
            f.write("=" * 80 + "\n")
            f.write(f"MISSING DENSITIES ({len(error_tracker.errors['missing_densities'])})\n")
            f.write("=" * 80 + "\n")
            for err in error_tracker.errors["missing_densities"]:
                f.write(f"Recipe {err['recipe_id']}, Line {err['line_number']}: \"{err['original_text']}\"\n")
                f.write(f"  → Ingredient: {err['ingredient_name']} ({err['ingredient_id']})\n")
                f.write(f"  → Form: {err['form_id']}\n")
                f.write(f"  → Conversion needed: {err['conversion_needed']}\n")
                f.write(f"  → Action: Add density for {err['ingredient_id']} + {err['form_id']}\n\n")
        
        # Multi-ingredient lines
        if error_tracker.errors["multi_ingredient_lines"]:
            f.write("=" * 80 + "\n")
            f.write(f"MULTI-INGREDIENT LINES ({len(error_tracker.errors['multi_ingredient_lines'])})\n")
            f.write("=" * 80 + "\n")
            for err in error_tracker.errors["multi_ingredient_lines"]:
                f.write(f"Recipe {err['recipe_id']}, Line {err['line_number']}: \"{err['original_text']}\"\n")
                f.write(f"  → Action: Split into separate ingredient lines in Stage 1\n\n")
        
        # Unrecognized units
        if error_tracker.errors["unit_not_recognized"]:
            f.write("=" * 80 + "\n")
            f.write(f"UNRECOGNIZED UNITS ({len(error_tracker.errors['unit_not_recognized'])})\n")
            f.write("=" * 80 + "\n")
            for err in error_tracker.errors["unit_not_recognized"]:
                f.write(f"{err}\n")
    
    # Write JSON report
    print(f"Writing error report (JSON): {json_file}")
    with open(json_file, 'w', encoding='utf-8') as f:
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "errors": error_tracker.errors
        }
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\nError reports written successfully!")


if __name__ == "__main__":
    # This will be imported by main.py
    pass
