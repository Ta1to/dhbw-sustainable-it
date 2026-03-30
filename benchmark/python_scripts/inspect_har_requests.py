#!/usr/bin/env python3
"""
HAR Requests Data Inspector
Extracts and displays all request/response data from a browsertime.har file.
"""

import json
import sys
from pathlib import Path


def inspect_har_requests(har_path: str, limit: int = None):
    """Load HAR file and output all request/response data."""
    har_file = Path(har_path)
    
    if not har_file.exists():
        print(f"Error: File not found: {har_path}")
        sys.exit(1)
    
    if not har_file.suffix == ".har":
        print(f"Warning: File does not have .har extension")
    
    try:
        with open(har_file) as f:
            data = json.load(f)
        
        entries = data.get("log", {}).get("entries", [])
        
        if not entries:
            print("No entries found in HAR file")
            sys.exit(1)
        
        print(f"Found {len(entries)} request(s) in HAR file\n")
        
        display_limit = limit if limit else len(entries)
        
        # Output request data for each entry
        for i, entry in enumerate(entries[:display_limit], 1):
            print(f"{'='*80}")
            print(f"REQUEST {i}")
            print(f"{'='*80}")
            
            # Extract key request info
            request = entry.get("request", {})
            response = entry.get("response", {})
            cache = entry.get("cache", {})
            timings = entry.get("timings", {})
            
            # Print request summary
            method = request.get("method", "N/A")
            url = request.get("url", "N/A")
            
            print(f"\nURL: {url}")
            print(f"Method: {method}")
            
            # Print headers
            headers = request.get("headers", [])
            if headers:
                print(f"\nRequest Headers ({len(headers)}):")
                for header in headers[:5]:  # Show first 5 headers
                    print(f"  {header.get('name')}: {header.get('value')}")
                if len(headers) > 5:
                    print(f"  ... and {len(headers) - 5} more headers")
            
            # Print response info
            status = response.get("status", "N/A")
            status_text = response.get("statusText", "N/A")
            
            print(f"\nResponse Status: {status} {status_text}")
            
            # Print response content
            content = response.get("content", {})
            size = content.get("size", 0)
            compressed_size = content.get("compression", 0)
            mime_type = content.get("mimeType", "N/A")
            
            print(f"Content Type: {mime_type}")
            print(f"Transfer Size: {size:,} bytes ({size/1024:.2f} KB)")
            if compressed_size > 0:
                print(f"Compression: {compressed_size:,} bytes saved")
            
            # Print cache headers
            if cache:
                print(f"\nCache:")
                print(json.dumps(cache, indent=2))
            
            # Print timings
            if timings:
                print(f"\nTimings (milliseconds):")
                for timing_name, timing_value in timings.items():
                    if timing_value >= 0:  # -1 means not applicable
                        print(f"  {timing_name}: {timing_value:.2f}ms")
            
            print()
        
        if limit and len(entries) > limit:
            print(f"\nShowing first {limit} entries out of {len(entries)} total")
            print(f"To see all entries, run without the --limit argument")
    
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in HAR file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 python_scripts/inspect_har_requests.py <path_to_har_file> [--limit N] [--raw]")
        print("\nArguments:")
        print("  --limit N    Show only first N requests (default: all)")
        print("  --raw        Output raw JSON structure (no summary)")
        print("\nExample:")
        print("  python3 python_scripts/inspect_har_requests.py results/sitespeed_bench_20260324_100353/astro/pages/localhost/products/data/browsertime.har --limit 5")
        sys.exit(1)
    
    har_path = sys.argv[1]
    limit = None
    raw_mode = False
    
    # Parse optional arguments
    if len(sys.argv) > 2:
        for i in range(2, len(sys.argv)):
            if sys.argv[i] == "--limit" and i + 1 < len(sys.argv):
                try:
                    limit = int(sys.argv[i + 1])
                except ValueError:
                    print(f"Error: --limit value must be a number")
                    sys.exit(1)
            elif sys.argv[i] == "--raw":
                raw_mode = True
    
    if raw_mode:
        # Raw JSON output mode
        try:
            with open(har_path) as f:
                data = json.load(f)
            entries = data.get("log", {}).get("entries", [])
            display_limit = limit if limit else len(entries)
            
            for i, entry in enumerate(entries[:display_limit], 1):
                print(f"\n{'='*80}\nREQUEST {i}\n{'='*80}")
                print(json.dumps(entry, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        inspect_har_requests(har_path, limit)
