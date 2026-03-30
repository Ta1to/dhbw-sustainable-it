#!/usr/bin/env python3
"""
Data Per Request Calculator
Analyzes how much data is sent per request using autocannon performance data.
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


BENCHMARK_DIR = Path(__file__).resolve().parent.parent


def discover_benchmark_runs() -> List[Path]:
    """Find all benchmark run directories in results/products/"""
    results_path = BENCHMARK_DIR / "results" / "products"
    
    if not results_path.exists():
        return []
    
    runs = sorted([d for d in results_path.iterdir() if d.is_dir()])
    return runs


def extract_framework_name(filename: str) -> str:
    """Extract framework name from filename (astro, next, svelte)"""
    if "astro" in filename.lower():
        return "Astro"
    elif "next" in filename.lower():
        return "Next.js"
    elif "svelte" in filename.lower():
        return "Svelte"
    return None


def load_perf_data(run_dir: Path) -> Dict[str, Dict]:
    """Load performance data from _perf.json files."""
    data = {}
    
    perf_files = list(run_dir.glob("*_perf.json"))
    
    for perf_file in perf_files:
        framework = extract_framework_name(perf_file.name)
        if not framework:
            continue
        
        try:
            with open(perf_file) as f:
                perf_data = json.load(f)
            
            if framework not in data:
                data[framework] = []
            
            data[framework].append(perf_data)
        except Exception as e:
            print(f"Error loading {perf_file}: {e}")
    
    return data


def analyze_all_runs():
    """Process all benchmark runs and calculate data per request."""
    
    # Aggregate data across all runs
    aggregated = defaultdict(lambda: {
        "total_requests": [],
        "total_bytes": [],
        "latency": [],
        "throughput_bytes_sec": [],
    })
    
    runs = discover_benchmark_runs()
    
    if not runs:
        print("Error: No benchmark runs found in results/products/")
        return
    
    print(f"📊 Data Per Request Analysis")
    print(f"📁 Found {len(runs)} benchmark run(s)\n")
    
    # Process each run
    for run_dir in runs:
        run_name = run_dir.name
        print(f"Processing: {run_name}")
        
        data = load_perf_data(run_dir)
        
        for framework, perf_list in data.items():
            for perf in perf_list:
                requests_total = perf.get("requests", {}).get("total", 0)
                throughput_total = perf.get("throughput", {}).get("total", 0)
                latency_avg = perf.get("latency", {}).get("average", 0)
                throughput_bytes_sec = perf.get("throughput", {}).get("average", 0)
                
                aggregated[framework]["total_requests"].append(requests_total)
                aggregated[framework]["total_bytes"].append(throughput_total)
                aggregated[framework]["latency"].append(latency_avg)
                aggregated[framework]["throughput_bytes_sec"].append(throughput_bytes_sec)
    
    # Calculate and display statistics
    print("\n" + "=" * 120)
    print("DATA TRANSFER ANALYSIS - AVERAGED ACROSS ALL PRODUCT BENCHMARK RUNS")
    print("=" * 120 + "\n")
    
    header = f"{'Framework':<15} {'Avg Requests':<15} {'Total Data (GB)':<18} {'Data/Request':<18} {'Data/Request (KB)':<20}"
    print(header)
    print("-" * 120)
    
    frameworks = sorted(aggregated.keys())
    
    for framework in frameworks:
        metrics = aggregated[framework]
        
        if not metrics["total_requests"] or not metrics["total_bytes"]:
            print(f"{framework:<15} {'N/A':<15} {'N/A':<18} {'N/A':<18} {'N/A':<20}")
            continue
        
        avg_requests = sum(metrics["total_requests"]) / len(metrics["total_requests"])
        avg_bytes = sum(metrics["total_bytes"]) / len(metrics["total_bytes"])
        avg_latency = sum(metrics["latency"]) / len(metrics["latency"])
        
        # Calculate data per request
        data_per_request = avg_bytes / avg_requests  # in bytes
        data_per_request_kb = data_per_request / 1024  # in KB
        total_gb = avg_bytes / (1024 ** 3)  # in GB
        
        print(f"{framework:<15} {avg_requests:>14.0f} {total_gb:>17.2f} {data_per_request:>17.0f}B {data_per_request_kb:>19.2f}")
    
    # Detailed breakdown
    print("\n" + "=" * 120)
    print("DETAILED BREAKDOWN PER FRAMEWORK")
    print("=" * 120 + "\n")
    
    for framework in frameworks:
        metrics = aggregated[framework]
        
        if not metrics["total_requests"] or not metrics["total_bytes"]:
            print(f"{framework}: No data available\n")
            continue
        
        avg_requests = sum(metrics["total_requests"]) / len(metrics["total_requests"])
        avg_bytes = sum(metrics["total_bytes"]) / len(metrics["total_bytes"])
        avg_latency = sum(metrics["latency"]) / len(metrics["latency"])
        avg_throughput = sum(metrics["throughput_bytes_sec"]) / len(metrics["throughput_bytes_sec"])
        
        data_per_request = avg_bytes / avg_requests
        
        print(f"{framework}")
        print(f"  Total Data Transferred:        {avg_bytes:>15.0f} bytes ({avg_bytes / (1024**3):>8.2f} GB)")
        print(f"  Average Requests per Test:     {avg_requests:>15.0f} req")
        print(f"  Data per Single Request:       {data_per_request:>15.0f} bytes ({data_per_request/1024:>8.2f} KB)")
        print(f"  Average Response Latency:      {avg_latency:>15.2f} ms")
        print(f"  Average Throughput:            {avg_throughput:>15.0f} bytes/sec ({avg_throughput/(1024**2):>8.2f} MB/sec)")
        print(f"  Test Runs Analyzed:            {len(metrics['total_requests']):>15} runs")
        
        # Extra calculations
        data_per_1k_req = data_per_request * 1000
        data_per_1m_req = data_per_request * 1000000
        
        print(f"  Total Data for 1K requests:    {data_per_1k_req:>15.0f} bytes ({data_per_1k_req/1024:>8.2f} KB)")
        print(f"  Total Data for 1M requests:    {data_per_1m_req:>15.0f} bytes ({data_per_1m_req/(1024**3):>8.2f} GB)")
        print()
    
    # Comparative analysis
    print("=" * 120)
    print("COMPARATIVE ANALYSIS")
    print("=" * 120 + "\n")
    
    # Calculate efficiency scores
    data_per_req = {}
    for framework in frameworks:
        metrics = aggregated[framework]
        if metrics["total_requests"] and metrics["total_bytes"]:
            avg_requests = sum(metrics["total_requests"]) / len(metrics["total_requests"])
            avg_bytes = sum(metrics["total_bytes"]) / len(metrics["total_bytes"])
            data_per_req[framework] = avg_bytes / avg_requests
    
    ranked = sorted(data_per_req.items(), key=lambda x: x[1])
    
    print("Data Transfer Efficiency (Lower = Better/More Efficient):\n")
    medals = ["🥇", "🥈", "🥉"]
    
    for rank, (framework, bytes_per_req) in enumerate(ranked):
        medal = medals[rank] if rank < len(medals) else "  "
        kb = bytes_per_req / 1024
        print(f"{medal} {rank + 1}. {framework:<15} {bytes_per_req:>10.0f} bytes/req ({kb:>8.2f} KB/req)")
        
        if rank == 0:
            best_fw = framework
            best_bytes = bytes_per_req
        elif rank > 0:
            overhead = ((bytes_per_req - best_bytes) / best_bytes * 100)
            print(f"   ({overhead:+.1f}% more data than {best_fw})")
    
    print("\n" + "=" * 120)
    print("INTERPRETATION")
    print("=" * 120 + "\n")
    
    best_framework = ranked[0][0] if ranked else "Unknown"
    best_bytes = ranked[0][1] if ranked else 0
    worst_bytes = ranked[-1][1] if ranked else 0
    
    print(f"""
Data per request measures how many bytes are transferred for each HTTP request.
This includes HTML, CSS, JavaScript, images, and other assets.

KEY FINDINGS:
  Framework with Smallest Response:   {best_framework:<15} {best_bytes:>10.0f} bytes ({best_bytes/1024:>8.2f} KB)
""")
    
    if len(ranked) > 1:
        worst_fw = ranked[-1][0]
        overhead = ((worst_bytes - best_bytes) / best_bytes * 100)
        print(f"  Framework with Largest Response:  {worst_fw:<15} {worst_bytes:>10.0f} bytes ({worst_bytes/1024:>8.2f} KB)")
        print(f"  Difference:                       {worst_bytes - best_bytes:>10.0f} bytes ({overhead:.1f}% more data)\n")
    
    print("""USABLE FOR:
  - Estimating bandwidth required: data_per_request × daily_requests = bandwidth usage
  - Mobile data usage: total_data / total_requests × monthly_requests = monthly MB
  - Content delivery: identifying which framework sends most data
  - Page bloat analysis: larger data = more bloat = slower for users
  - Optimization target: minimize data per request to improve performance and sustainability
""")


def main():
    """Main entry point."""
    analyze_all_runs()


if __name__ == "__main__":
    main()
