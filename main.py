#!/usr/bin/env python3
"""
Stage 2 Processor - Main Entry Point

Usage:
    python main.py

Configuration:
    Edit config.py to set input/output file paths
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import INPUT_FILE, OUTPUT_FILE, ERROR_TXT_FILE, ERROR_JSON_FILE
from data_loader import load_all_reference_data
from processor import process_stage1_file, write_error_reports


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("STAGE 2 INGREDIENT PROCESSOR")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Determine base path for reference files
    # Check if files are in /mnt/project
    if os.path.exists("/mnt/project"):
        base_path = "/mnt/project"
    else:
        base_path = "."
    
    print(f"\nBase path for reference files: {base_path}")
    
    # Check if input file exists
    input_path = os.path.join(base_path, INPUT_FILE)
    if not os.path.exists(input_path):
        # Try current directory
        input_path = INPUT_FILE
        if not os.path.exists(input_path):
            print(f"\nERROR: Input file not found: {INPUT_FILE}")
            print("Please ensure the Stage 1 JSONL file is in the correct location.")
            sys.exit(1)
    
    print(f"Input file: {input_path}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Error reports: {ERROR_TXT_FILE}, {ERROR_JSON_FILE}")
    
    try:
        # Load reference data
        print("\n" + "=" * 80)
        print("STEP 1: LOADING REFERENCE DATA")
        print("=" * 80)
        reference_data = load_all_reference_data(base_path)
        
        # Process Stage 1 file
        print("\n" + "=" * 80)
        print("STEP 2: PROCESSING INGREDIENTS")
        print("=" * 80)
        error_tracker = process_stage1_file(input_path, OUTPUT_FILE, reference_data)
        
        # Generate reports
        print("\n" + "=" * 80)
        print("STEP 3: GENERATING ERROR REPORTS")
        print("=" * 80)
        write_error_reports(error_tracker, ERROR_TXT_FILE, ERROR_JSON_FILE)
        
        # Print summary
        summary = error_tracker.get_summary()
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Total ingredients: {summary['total']}")
        print(f"✓ Successful: {summary['successful']} ({summary['success_rate']*100:.1f}%)")
        print(f"✗ Failed: {summary['failed']} ({(1-summary['success_rate'])*100:.1f}%)")
        print("\nError breakdown:")
        for error_type, count in summary['error_counts'].items():
            print(f"  - {error_type}: {count}")
        
        print("\n" + "=" * 80)
        print("OUTPUT FILES:")
        print("=" * 80)
        print(f"✓ Stage 2 data: {OUTPUT_FILE}")
        print(f"✓ Error report (text): {ERROR_TXT_FILE}")
        print(f"✓ Error report (JSON): {ERROR_JSON_FILE}")
        print("\n" + "=" * 80)
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
