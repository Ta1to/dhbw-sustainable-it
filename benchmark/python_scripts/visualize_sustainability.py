#!/usr/bin/env python3
"""
Sustainability Analysis Visualization
Creates matplotlib/seaborn visualizations of CPU resource consumption across frameworks.
Reuses the SustainabilityAnalyzer class from sustainability_analysis.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Import the analyzer from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from sustainability_analysis import SustainabilityAnalyzer


BENCHMARK_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BENCHMARK_DIR / "images"


def create_visualizations(analyzer: SustainabilityAnalyzer):
    """Create comprehensive visualizations of CPU metrics."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    if not analyzer.load_all_metrics():
        print("Failed to load metrics")
        return
    
    # Set style
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    
    # Prepare data
    frameworks = sorted(analyzer.data.keys())
    metrics = {
        "Total CPU": "total",
        "JavaScript Evaluation": "js_eval",
        "Garbage Collection": "gc",
        "Script Parse/Compile": "script_parse",
        "Style & Layout": "style_layout",
        "Paint & Composite": "paint_composite",
        "RunTask": "runtask",
        "RunMicrotasks": "microtasks",
        "Other": "other",
    }
    
    # Create a large figure with subplots
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle("Sustainability Analysis: CPU Resource Consumption Across Frameworks", 
                 fontsize=16, fontweight="bold", y=0.995)
    
    # ============ 1. Total CPU Comparison ============
    ax1 = plt.subplot(2, 3, 1)
    total_data = {fw: analyzer.data[fw]["total"] for fw in frameworks}
    bars = ax1.bar(total_data.keys(), total_data.values(), color=sns.color_palette("husl", len(frameworks)))
    ax1.set_ylabel("Total CPU (ms)", fontweight="bold")
    ax1.set_title("1. Total CPU Time per Page Load", fontweight="bold")
    ax1.set_ylim(0, max(total_data.values()) * 1.15)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}ms',
                ha='center', va='bottom', fontweight='bold')
    
    # ============ 2. CPU Breakdown by Framework (Stacked Bar) ============
    ax2 = plt.subplot(2, 3, 2)
    breakdown_data = {}
    for fw in frameworks:
        breakdown_data[fw] = {metric: analyzer.data[fw].get(key, 0) 
                             for metric, key in metrics.items() if key != "total"}
    
    df_breakdown = pd.DataFrame(breakdown_data).T
    df_breakdown.plot(kind='bar', stacked=True, ax=ax2, 
                     colormap='Set3', legend=True)
    ax2.set_ylabel("CPU (ms)", fontweight="bold")
    ax2.set_title("2. CPU Breakdown by Category", fontweight="bold")
    ax2.set_xlabel("")
    ax2.legend(title="Metrics", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # ============ 3. JavaScript Evaluation Comparison ============
    ax3 = plt.subplot(2, 3, 3)
    js_data = {fw: analyzer.data[fw]["js_eval"] for fw in frameworks}
    bars = ax3.bar(js_data.keys(), js_data.values(), color=sns.color_palette("rocket", len(frameworks)))
    ax3.set_ylabel("CPU (ms)", fontweight="bold")
    ax3.set_title("3. JavaScript Evaluation Overhead", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # ============ 4. Garbage Collection Comparison ============
    ax4 = plt.subplot(2, 3, 4)
    gc_data = {fw: analyzer.data[fw]["gc"] for fw in frameworks}
    bars = ax4.bar(gc_data.keys(), gc_data.values(), color=sns.color_palette("mako", len(frameworks)))
    ax4.set_ylabel("CPU (ms)", fontweight="bold")
    ax4.set_title("4. Garbage Collection Overhead", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # ============ 5. RunMicrotasks (Framework Scheduler) ============
    ax5 = plt.subplot(2, 3, 5)
    micro_data = {fw: analyzer.data[fw]["microtasks"] for fw in frameworks}
    bars = ax5.bar(micro_data.keys(), micro_data.values(), color=sns.color_palette("viridis", len(frameworks)))
    ax5.set_ylabel("CPU (ms)", fontweight="bold")
    ax5.set_title("5. RunMicrotasks (Framework Scheduler Overhead)", fontweight="bold")
    
    for bar in bars:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}ms',
                ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    # ============ 6. Sustainability Ranking ============
    ax6 = plt.subplot(2, 3, 6)
    ranked = sorted(
        [(fw, analyzer.data[fw]["total"]) for fw in frameworks],
        key=lambda x: x[1]
    )
    rank_names, rank_values = zip(*ranked)
    colors = ['#2ecc71', '#f39c12', '#e74c3c'][:len(ranked)]
    bars = ax6.barh(rank_names, rank_values, color=colors)
    ax6.set_xlabel("Total CPU (ms)", fontweight="bold")
    ax6.set_title("6. Sustainability Ranking (Lower = Better)", fontweight="bold")
    ax6.invert_yaxis()
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        pct = ((rank_values[i] - rank_values[0]) / rank_values[0] * 100) if i > 0 else 0
        label = f'{width:.1f}ms'
        if i > 0:
            label += f' (+{pct:.0f}%)'
        ax6.text(width, bar.get_y() + bar.get_height()/2.,
                f' {label}',
                ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    
    # Save figure
    output_path = IMAGES_DIR / "sustainability_report.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_path}")


def create_detailed_heatmap(analyzer: SustainabilityAnalyzer):
    """Create a heatmap showing all metrics for all frameworks."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    if not analyzer.data:
        print("No data to visualize")
        return
    
    frameworks = sorted(analyzer.data.keys())
    
    # Prepare data for heatmap
    heatmap_data = []
    metric_names = []
    
    metrics_dict = {
        "Total CPU": "total",
        "JavaScript Evaluation": "js_eval",
        "Garbage Collection": "gc",
        "Script Parse/Compile": "script_parse",
        "Style & Layout": "style_layout",
        "Paint & Composite": "paint_composite",
        "RunTask": "runtask",
        "RunMicrotasks": "microtasks",
        "Other": "other",
    }
    
    for metric_name, key in metrics_dict.items():
        row = []
        for fw in frameworks:
            row.append(analyzer.data[fw].get(key, 0))
        heatmap_data.append(row)
        metric_names.append(metric_name)
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    df_heatmap = pd.DataFrame(heatmap_data, columns=frameworks, index=metric_names)
    
    sns.heatmap(df_heatmap, annot=True, fmt='.2f', cmap='RdYlGn_r', 
                cbar_kws={'label': 'CPU Time (ms)'}, ax=ax, linewidths=0.5)
    
    ax.set_title("CPU Metrics Heatmap (Lower values = Greener = Better)", 
                 fontweight="bold", fontsize=14, pad=20)
    ax.set_ylabel("Metrics", fontweight="bold")
    ax.set_xlabel("Frameworks", fontweight="bold")
    
    plt.tight_layout()
    
    # Save figure
    output_path = IMAGES_DIR / "sustainability_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Heatmap saved to: {output_path}")


def main():
    """Main entry point."""
    benchmark_dir = BENCHMARK_DIR
    
    analyzer = SustainabilityAnalyzer(str(benchmark_dir))
    
    print(f"📊 Sustainability Analysis Visualization Tool")
    print(f"📁 Searching for benchmarks in: {benchmark_dir / 'results'}\n")
    
    if not analyzer.frameworks:
        print(f"❌ No frameworks discovered. Make sure HAR files exist in:")
        print(f"   {benchmark_dir}/results/sitespeed_bench_*/*/pages/localhost/products/data/browsertime.har")
        return
    
    print(f"✓ Discovered {len(analyzer.frameworks)} frameworks: {', '.join(analyzer.frameworks)}\n")
    
    # Create visualizations
    print("📈 Creating visualizations...\n")
    create_visualizations(analyzer)
    create_detailed_heatmap(analyzer)
    print("\n✓ All visualizations created successfully!")


if __name__ == "__main__":
    main()
