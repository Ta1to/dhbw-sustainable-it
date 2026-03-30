#!/usr/bin/env python3
"""
HAR CPU Data Inspector
Extracts and displays all CPU metrics from a single browsertime.har file.
"""

import json
import sys
from pathlib import Path


def inspect_har_cpu(har_path: str):
    """Load HAR file and output all CPU data."""
    har_file = Path(har_path)
    
    if not har_file.exists():
        print(f"Error: File not found: {har_path}")
        sys.exit(1)
    
    if not har_file.suffix == ".har":
        print(f"Warning: File does not have .har extension")
    
    try:
        with open(har_file) as f:
            data = json.load(f)
        
        pages = data.get("log", {}).get("pages", [])
        
        if not pages:
            print("No pages found in HAR file")
            sys.exit(1)
        
        print(f"Found {len(pages)} page(s) in HAR file\n")
        
        # Output CPU data for each page
        for i, page in enumerate(pages, 1):
            print(f"{'='*80}")
            print(f"PAGE {i}: {page.get('title', 'Untitled')}")
            print(f"{'='*80}")
            
            cpu_data = page.get("_cpu")
            
            if cpu_data:
                print(json.dumps(cpu_data, indent=2))
            else:
                print("No CPU data found for this page")
            
            print()
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in HAR file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 python_scripts/inspect_har_cpu.py <path_to_har_file>")
        print("\nExample:")
        print("  python3 python_scripts/inspect_har_cpu.py results/sitespeed_bench_20260324_100353/astro/pages/localhost/products/data/browsertime.har")
        sys.exit(1)
    
    har_path = sys.argv[1]
    inspect_har_cpu(har_path)
