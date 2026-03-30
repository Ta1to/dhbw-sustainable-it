#!/usr/bin/env python3
"""
Energy Analysis Visualization
Creates matplotlib/seaborn visualizations of energy usage per framework.
Reuses data extraction from energy_per_request.py
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


BENCHMARK_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BENCHMARK_DIR / "images"


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


def load_benchmark_data(run_dir: Path) -> Dict[str, Dict]:
    """Load perf and watts data for a single benchmark run."""
    data = {}
    
    perf_files = list(run_dir.glob("*_perf.json"))
    watts_files = list(run_dir.glob("*-server_watts.json"))
    
    for perf_file in perf_files:
        framework = extract_framework_name(perf_file.name)
        if not framework:
            continue
        
        try:
            with open(perf_file) as f:
                perf_data = json.load(f)
            
            if framework not in data:
                data[framework] = {"perf": [], "watts": []}
            
            data[framework]["perf"].append(perf_data)
        except Exception as e:
            pass
    
    for watts_file in watts_files:
        framework = extract_framework_name(watts_file.name)
        if not framework:
            continue
        
        try:
            with open(watts_file) as f:
                watts_data = json.load(f)
            
            if framework not in data:
                data[framework] = {"perf": [], "watts": []}
            
            result = watts_data.get("data", {}).get("result", [])
            if result and len(result) > 0:
                watts_value = float(result[0].get("value", [0, 0])[1])
                data[framework]["watts"].append(watts_value)
        except Exception as e:
            pass
    
    return data


def aggregate_all_runs():
    """Process all benchmark runs and aggregate data."""
    
    aggregated = defaultdict(lambda: {
        "requests": [],
        "watts": [],
        "latency": [],
        "throughput": [],
    })
    
    runs = discover_benchmark_runs()
    
    for run_dir in runs:
        data = load_benchmark_data(run_dir)
        
        for framework, metrics in data.items():
            for perf in metrics["perf"]:
                requests_total = perf.get("requests", {}).get("total", 0)
                latency_avg = perf.get("latency", {}).get("average", 0)
                throughput_avg = perf.get("throughput", {}).get("average", 0)
                
                aggregated[framework]["requests"].append(requests_total)
                aggregated[framework]["latency"].append(latency_avg)
                aggregated[framework]["throughput"].append(throughput_avg)
            
            for watts in metrics["watts"]:
                aggregated[framework]["watts"].append(watts)
    
    return aggregated


def create_visualizations(aggregated):
    """Create comprehensive energy usage visualizations."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate metrics for each framework
    metrics = {}
    for framework in aggregated.keys():
        data = aggregated[framework]
        
        if not data["requests"] or not data["watts"]:
            continue
        
        avg_requests = sum(data["requests"]) / len(data["requests"])
        avg_watts = sum(data["watts"]) / len(data["watts"])
        avg_latency = sum(data["latency"]) / len(data["latency"])
        
        energy_per_request = (avg_watts * 60) / avg_requests
        
        metrics[framework] = {
            "watts": avg_watts,
            "requests": avg_requests,
            "latency": avg_latency,
            "energy_per_1k": energy_per_request * 1000,
            "energy_per_10k": energy_per_request * 10000,
            "energy_per_100k": energy_per_request * 100000,
            "req_per_watt": avg_requests / avg_watts,
        }
    
    if not metrics:
        print("No data to visualize")
        return
    
    frameworks = sorted(metrics.keys())
    
    # Set style
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle("Energy Efficiency Analysis: Product Benchmark Load Testing", 
                 fontsize=16, fontweight="bold", y=0.98)
    
    # ============ 1. Average Power Consumption ============
    ax1 = plt.subplot(2, 3, 1)
    watts_data = {fw: metrics[fw]["watts"] for fw in frameworks}
    bars = ax1.bar(watts_data.keys(), watts_data.values(), 
                   color=sns.color_palette("husl", len(frameworks)))
    ax1.set_ylabel("Power (Watts)", fontweight="bold")
    ax1.set_title("1. Average Power Consumption", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}W',
                ha='center', va='bottom', fontweight='bold')
    
    # ============ 2. Average Requests per Framework ============
    ax2 = plt.subplot(2, 3, 2)
    requests_data = {fw: metrics[fw]["requests"] for fw in frameworks}
    bars = ax2.bar(requests_data.keys(), requests_data.values(), 
                   color=sns.color_palette("rocket", len(frameworks)))
    ax2.set_ylabel("Number of Requests", fontweight="bold")
    ax2.set_title("2. Average Requests per Framework", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}',
                ha='center', va='bottom', fontweight='bold')
    
    # ============ 3. Energy per 1,000 Requests ============
    ax3 = plt.subplot(2, 3, 3)
    energy_1k = {fw: metrics[fw]["energy_per_1k"] for fw in frameworks}
    bars = ax3.bar(energy_1k.keys(), energy_1k.values(), 
                   color=sns.color_palette("mako", len(frameworks)))
    ax3.set_ylabel("Energy (Joules)", fontweight="bold")
    ax3.set_title("3. Energy per 1,000 Requests", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}J',
                ha='center', va='bottom', fontweight='bold')
    
    # ============ 4. Energy per 10,000 Requests ============
    ax4 = plt.subplot(2, 3, 4)
    energy_10k = {fw: metrics[fw]["energy_per_10k"] for fw in frameworks}
    bars = ax4.bar(energy_10k.keys(), energy_10k.values(), 
                   color=sns.color_palette("viridis", len(frameworks)))
    ax4.set_ylabel("Energy (Joules)", fontweight="bold")
    ax4.set_title("4. Energy per 10,000 Requests", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}J',
                ha='center', va='bottom', fontweight='bold')
    
    # ============ 5. Requests per Watt (Efficiency) ============
    ax5 = plt.subplot(2, 3, 5)
    req_per_watt = {fw: metrics[fw]["req_per_watt"] for fw in frameworks}
    bars = ax5.bar(req_per_watt.keys(), req_per_watt.values(), 
                   color=sns.color_palette("coolwarm", len(frameworks)))
    ax5.set_ylabel("Requests per Watt", fontweight="bold")
    ax5.set_title("5. Energy Efficiency (Requests/Watt)", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontweight='bold')

    
    # ============ 6. Average Response Latency ============
    ax6 = plt.subplot(2, 3, 6)
    latency = {fw: metrics[fw]["latency"] for fw in frameworks}
    bars = ax6.bar(latency.keys(), latency.values(), 
                   color=sns.color_palette("coolwarm", len(frameworks)))
    ax6.set_ylabel("Latency (ms)", fontweight="bold")
    ax6.set_title("6. Average Response Latency", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}ms',
                ha='center', va='bottom', fontweight='bold')
    
    plt.subplots_adjust(hspace=0.35, wspace=0.3)
    
    # Save figure
    output_path = IMAGES_DIR / "energy_analysis_report.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_path}")
    plt.close()


def create_efficiency_heatmap(aggregated):
    """Create a heatmap of energy metrics."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    metrics = {}
    for framework in aggregated.keys():
        data = aggregated[framework]
        
        if not data["requests"] or not data["watts"]:
            continue
        
        avg_requests = sum(data["requests"]) / len(data["requests"])
        avg_watts = sum(data["watts"]) / len(data["watts"])
        
        energy_per_request = (avg_watts * 60) / avg_requests
        
        metrics[framework] = {
            "Average Watts": avg_watts,
            "Requests/Watt": avg_requests / avg_watts,
            "Energy/1K Req (J)": energy_per_request * 1000,
            "Energy/10K Req (J)": energy_per_request * 10000,
        }
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 6))
    df = pd.DataFrame(metrics).T
    
    sns.heatmap(df, annot=True, fmt='.2f', cmap='RdYlGn_r', 
                cbar_kws={'label': 'Metric Value'}, ax=ax, linewidths=0.5)
    
    ax.set_title("Energy Metrics Heatmap (Lower energy = Greener = Better)", 
                 fontweight="bold", fontsize=14, pad=20)
    ax.set_ylabel("Framework", fontweight="bold")
    
    plt.tight_layout()
    
    # Save figure
    output_path = IMAGES_DIR / "energy_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Heatmap saved to: {output_path}")
    plt.close()


def create_efficiency_ranking(aggregated):
    """Create a ranking visualization of energy efficiency."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    metrics = {}
    for framework in aggregated.keys():
        data = aggregated[framework]
        
        if not data["requests"] or not data["watts"]:
            continue
        
        avg_requests = sum(data["requests"]) / len(data["requests"])
        avg_watts = sum(data["watts"]) / len(data["watts"])
        
        metrics[framework] = avg_requests / avg_watts  # Requests per watt
    
    ranked = sorted(metrics.items(), key=lambda x: x[1], reverse=True)
    names, values = zip(*ranked)
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#2ecc71', '#f39c12', '#e74c3c'][:len(ranked)]
    bars = ax.barh(names, values, color=colors)
    
    ax.set_xlabel("Requests per Watt (Higher = More Efficient)", fontweight="bold")
    ax.set_title("Energy Efficiency Ranking", fontweight="bold", fontsize=14)
    ax.invert_yaxis()
    
    # Add value labels
    medals = ["🥇", "🥈", "🥉"]
    for i, (bar, (name, value)) in enumerate(zip(bars, ranked)):
        medal = medals[i] if i < len(medals) else "  "
        width = bar.get_width()
        pct_diff = ""
        
        if i > 0:
            best_value = values[0]
            pct_diff = f" ({((value - best_value) / best_value * 100):+.1f}%)"
        
        ax.text(width, bar.get_y() + bar.get_height()/2.,
               f' {medal} {value:.1f} req/W{pct_diff}',
               ha='left', va='center', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    
    # Save figure
    output_path = IMAGES_DIR / "efficiency_ranking.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Efficiency ranking saved to: {output_path}")
    plt.close()


def main():
    """Main entry point."""
    benchmark_dir = BENCHMARK_DIR
    
    print(f"📊 Energy Analysis Visualization Tool")
    print(f"📁 Searching for benchmarks in: {benchmark_dir / 'results' / 'products'}\n")
    
    runs = discover_benchmark_runs()
    
    if not runs:
        print(f"❌ No benchmark runs found in results/products/")
        return
    
    print(f"✓ Found {len(runs)} benchmark run(s)\n")
    
    # Aggregate data
    print("📈 Processing benchmark data...\n")
    aggregated = aggregate_all_runs()
    
    if not aggregated:
        print("❌ No data found to visualize")
        return
    
    # Create visualizations
    print("Creating visualizations...\n")
    create_visualizations(aggregated)
    create_efficiency_heatmap(aggregated)
    create_efficiency_ranking(aggregated)
    
    print("\n✓ All visualizations created successfully!")


if __name__ == "__main__":
    main()
