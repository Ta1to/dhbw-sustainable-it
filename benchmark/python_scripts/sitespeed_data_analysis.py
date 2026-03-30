#!/usr/bin/env python3
"""
Analyze sitespeed.io HAR files to extract data transfer metrics.
Similar to data_per_request.py but for browser-side measurements.
"""

import json
import os
import glob
from pathlib import Path
from collections import defaultdict


BENCHMARK_DIR = Path(__file__).resolve().parent.parent

def discover_sitespeed_runs():
    """Find all sitespeed.io benchmark directories."""
    pattern = str(BENCHMARK_DIR / "results" / "sitespeed_bench_*")
    directories = glob.glob(pattern)
    return sorted(directories)

def extract_framework_from_path(har_path):
    """Extract framework name from HAR file path."""
    # Path like: results/sitespeed_bench_20260324_100353/next/pages/localhost/products/data/browsertime.har
    parts = har_path.split(os.sep)
    if len(parts) > 2:
        return parts[2]  # Framework is at index 2
    return None

def load_har_file(har_path):
    """Load and parse a HAR file, extract transfer size data."""
    try:
        with open(har_path, 'r') as f:
            data = json.load(f)
        
        entries = data.get('log', {}).get('entries', [])
        total_size = 0
        request_count = 0
        request_details = []
        
        for entry in entries:
            size = entry.get('response', {}).get('content', {}).get('size', 0)
            total_size += size
            request_count += 1
            url = entry.get('request', {}).get('url', '')
            request_details.append({'url': url, 'size': size})
        
        return {
            'total_bytes': total_size,
            'request_count': request_count,
            'avg_per_request': total_size / request_count if request_count > 0 else 0,
            'requests': request_details
        }
    except Exception as e:
        print(f"Error loading {har_path}: {e}")
        return None

def analyze_sitespeed_benchmarks():
    """Analyze all sitespeed.io benchmark runs."""
    runs = discover_sitespeed_runs()
    
    if not runs:
        print("No sitespeed.io benchmark runs found")
        return
    
    print(f"Found {len(runs)} sitespeed.io benchmark run(s)\n")
    
    # Aggregate data by framework
    framework_data = defaultdict(lambda: {
        'total_bytes': [],
        'request_counts': [],
        'avg_sizes': []
    })
    
    for run_dir in runs:
        print(f"Analyzing: {run_dir}")
        timestamp = os.path.basename(run_dir)
        
        # Find all frameworks in this run
        frameworks = [d for d in os.listdir(run_dir) 
                     if os.path.isdir(os.path.join(run_dir, d))]
        
        for framework in frameworks:
            har_path = os.path.join(run_dir, framework, 'pages', 'localhost', 
                                   'products', 'data', 'browsertime.har')
            
            if os.path.exists(har_path):
                result = load_har_file(har_path)
                if result:
                    framework_data[framework]['total_bytes'].append(result['total_bytes'])
                    framework_data[framework]['request_counts'].append(result['request_count'])
                    framework_data[framework]['avg_sizes'].append(result['avg_per_request'])
                    
                    print(f"  {framework:10} - {result['total_bytes']:>12,} bytes | "
                          f"{result['request_count']:>5} requests | "
                          f"{result['avg_per_request']:>8.1f} bytes/req")
        print()
    
    # Print aggregated summary
    print("\n" + "="*80)
    print("AGGREGATED SITESPEED.IO METRICS (Across all benchmark runs)")
    print("="*80)
    print(f"{'Framework':<12} {'Total MB':>12} {'Requests':>10} {'Bytes/Req':>12} {'KB/Req':>10}")
    print("-"*80)
    
    for framework in sorted(framework_data.keys()):
        data = framework_data[framework]
        avg_total = sum(data['total_bytes']) / len(data['total_bytes'])
        avg_requests = sum(data['request_counts']) / len(data['request_counts'])
        avg_bytes_per_req = sum(data['avg_sizes']) / len(data['avg_sizes'])
        
        print(f"{framework:<12} {avg_total/1024/1024:>12.2f} {avg_requests:>10.0f} "
              f"{avg_bytes_per_req:>12.1f} {avg_bytes_per_req/1024:>10.2f}")
    
    print("\n" + "="*80)
    print("Comparison Summary:")
    print("="*80)
    
    # Find min and max
    if framework_data:
        frameworks = list(framework_data.keys())
        totals = {fw: sum(framework_data[fw]['total_bytes']) / len(framework_data[fw]['total_bytes']) 
                 for fw in frameworks}
        
        min_fw = min(totals, key=totals.get)
        max_fw = max(totals, key=totals.get)
        
        print(f"\nMost efficient (least data):   {min_fw} ({totals[min_fw]/1024/1024:.2f} MB)")
        print(f"Least efficient (most data):   {max_fw} ({totals[max_fw]/1024/1024:.2f} MB)")
        print(f"Difference:                    {(totals[max_fw] - totals[min_fw])/1024/1024:.2f} MB "
              f"({((totals[max_fw] / totals[min_fw]) - 1) * 100:.1f}% more)")

if __name__ == "__main__":
    analyze_sitespeed_benchmarks()
