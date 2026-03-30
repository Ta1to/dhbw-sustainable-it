#!/usr/bin/env python3
"""
Visualize Data Transfer Metrics from sitespeed.io
Analyzes HAR files and creates visualizations of network data consumption.
Accounts for -n 20 (20 runs) by dividing total bytes by 20.
"""

import json
import os
import glob
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


BENCHMARK_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BENCHMARK_DIR / "images"

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'

def discover_sitespeed_runs():
    """Find all sitespeed.io benchmark directories."""
    pattern = str(BENCHMARK_DIR / "results" / "sitespeed_bench_*")
    directories = glob.glob(pattern)
    return sorted(directories)

def load_har_file(har_path):
    """Load and parse HAR file, extract all metrics."""
    try:
        with open(har_path, 'r') as f:
            data = json.load(f)
        
        entries = data.get('log', {}).get('entries', [])
        
        request_types = defaultdict(lambda: {'count': 0, 'size': 0})
        total_size = 0
        
        for entry in entries:
            url = entry['request']['url']
            mime_type = entry['response']['content'].get('mimeType', 'unknown')
            size = entry['response']['content'].get('size', 0)
            total_size += size
            
            # Categorize request type
            if 'image' in mime_type:
                req_type = 'image'
            elif 'text/html' in mime_type:
                req_type = 'html'
            elif 'javascript' in mime_type or '.js' in url:
                req_type = 'javascript'
            elif 'css' in mime_type or '.css' in url:
                req_type = 'css'
            elif 'font' in mime_type or 'woff' in url or 'ttf' in url:
                req_type = 'font'
            else:
                req_type = 'other'
            
            request_types[req_type]['count'] += 1
            request_types[req_type]['size'] += size
        
        return {
            'total_bytes': total_size,
            'request_count': len(entries),
            'request_types': dict(request_types),
            'avg_bytes_per_request': total_size / len(entries) if len(entries) > 0 else 0
        }
    except Exception as e:
        print(f"Error loading {har_path}: {e}")
        return None

def analyze_all_frameworks():
    """Analyze all frameworks from sitespeed.io results."""
    runs = discover_sitespeed_runs()
    
    if not runs:
        print("No sitespeed.io benchmark runs found")
        return None
    
    framework_data = defaultdict(lambda: {
        'total_bytes': [],
        'request_counts': [],
        'avg_bytes_per_req': [],
        'request_types': defaultdict(lambda: {'count': 0, 'size': 0})
    })
    
    for run_dir in runs:
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
                    framework_data[framework]['avg_bytes_per_req'].append(result['avg_bytes_per_request'])
                    
                    # Aggregate request types
                    for req_type, data in result['request_types'].items():
                        framework_data[framework]['request_types'][req_type]['count'] += data['count']
                        framework_data[framework]['request_types'][req_type]['size'] += data['size']
    
    return framework_data

def create_visualizations(framework_data, runs_per_benchmark=20):
    """Create visualizations of data transfer metrics."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate averages
    frameworks = sorted(framework_data.keys())
    avg_mb_per_run = {}
    avg_requests = {}
    avg_bytes_per_req = {}
    
    for fw in frameworks:
        data = framework_data[fw]
        avg_total_bytes = sum(data['total_bytes']) / len(data['total_bytes']) if data['total_bytes'] else 0
        avg_mb_per_run[fw] = (avg_total_bytes / runs_per_benchmark) / (1024 * 1024)
        avg_total_requests = sum(data['request_counts']) / len(data['request_counts']) if data['request_counts'] else 0
        avg_requests[fw] = avg_total_requests / runs_per_benchmark
        avg_bytes_per_req[fw] = sum(data['avg_bytes_per_req']) / len(data['avg_bytes_per_req']) if data['avg_bytes_per_req'] else 0
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Data Transfer per Page Load (MB)
    ax1 = plt.subplot(2, 3, 1)
    bars1 = ax1.bar(frameworks, [avg_mb_per_run[fw] for fw in frameworks], 
                     color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
    ax1.set_ylabel('Data Transfer (MB)', fontsize=11, fontweight='bold')
    ax1.set_title('Data Transfer per Page Load', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, max([avg_mb_per_run[fw] for fw in frameworks]) * 1.15)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}MB',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # 2. Total Number of Requests
    ax2 = plt.subplot(2, 3, 2)
    bars2 = ax2.bar(frameworks, [avg_requests[fw] for fw in frameworks],
                     color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
    ax2.set_ylabel('Request Count', fontsize=11, fontweight='bold')
    ax2.set_title('HTTP Requests per Page Load', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, max([avg_requests[fw] for fw in frameworks]) * 1.15)
    
    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # 3. Average Bytes per Request
    ax3 = plt.subplot(2, 3, 3)
    bars3 = ax3.bar(frameworks, [avg_bytes_per_req[fw] / 1024 for fw in frameworks],
                     color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
    ax3.set_ylabel('Bytes per Request (KB)', fontsize=11, fontweight='bold')
    ax3.set_title('Average Request Size per Page Load', fontsize=12, fontweight='bold')
    ax3.set_ylim(0, max([avg_bytes_per_req[fw] / 1024 for fw in frameworks]) * 1.15)
    
    # Add value labels on bars
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}KB',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # 4. Request Type Breakdown (Stacked Bar Chart)
    ax4 = plt.subplot(2, 3, 4)
    request_type_names = set()
    for fw in frameworks:
        request_type_names.update(framework_data[fw]['request_types'].keys())
    request_type_names = sorted(list(request_type_names))
    
    colors = {'html': '#1f77b4', 'css': '#ff7f0e', 'javascript': '#2ca02c', 
              'image': '#d62728', 'font': '#9467bd', 'other': '#8c564b'}
    
    bottom = np.zeros(len(frameworks))
    for req_type in request_type_names:
        values = []
        for fw in frameworks:
            if req_type in framework_data[fw]['request_types']:
                count = framework_data[fw]['request_types'][req_type]['count'] / runs_per_benchmark
            else:
                count = 0
            values.append(count)
        
        ax4.bar(frameworks, values, bottom=bottom, label=req_type,
               color=colors.get(req_type, '#7f7f7f'), alpha=0.85)
        bottom += np.array(values)
    
    ax4.set_ylabel('Number of Requests', fontsize=11, fontweight='bold')
    ax4.set_title('Request Type Breakdown', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right', fontsize=9)
    
    # 5. Data Transfer by Type (Stacked Bar Chart - MB)
    ax5 = plt.subplot(2, 3, 5)
    bottom = np.zeros(len(frameworks))
    for req_type in request_type_names:
        values = []
        for fw in frameworks:
            if req_type in framework_data[fw]['request_types']:
                size_mb = (framework_data[fw]['request_types'][req_type]['size'] / runs_per_benchmark) / (1024 * 1024)
            else:
                size_mb = 0
            values.append(size_mb)
        
        ax5.bar(frameworks, values, bottom=bottom, label=req_type,
               color=colors.get(req_type, '#7f7f7f'), alpha=0.85)
        bottom += np.array(values)
    
    ax5.set_ylabel('Data Transfer (MB)', fontsize=11, fontweight='bold')
    ax5.set_title('Data Transfer by Request Type', fontsize=12, fontweight='bold')
    ax5.legend(loc='upper right', fontsize=9)
    
    # 6. Efficiency Metric (MB per Request)
    ax6 = plt.subplot(2, 3, 6)
    mb_per_req = {fw: avg_mb_per_run[fw] / (avg_requests[fw] / 1000) if avg_requests[fw] > 0 else 0 
                  for fw in frameworks}
    bars6 = ax6.bar(frameworks, [mb_per_req[fw] for fw in frameworks],
                     color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
    ax6.set_ylabel('Data Transfer Efficiency\n(MB per 1000 requests)', fontsize=11, fontweight='bold')
    ax6.set_title('Network Efficiency', fontsize=12, fontweight='bold')
    ax6.set_ylim(0, max([mb_per_req[fw] for fw in frameworks]) * 1.15)
    
    # Add value labels on bars
    for bar in bars6:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}MB',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    plt.suptitle('sitespeed.io Data Transfer Analysis (Per Page Load)', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    # Save figure
    output_file = IMAGES_DIR / 'data_transfer_report.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # Create detailed heatmap (request types)
    create_request_type_heatmap(framework_data, frameworks, request_type_names)

def create_request_type_heatmap(framework_data, frameworks, request_type_names):
    """Create heatmap of request types and sizes."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Heatmap 1: Request counts
    data_counts = []
    for fw in frameworks:
        row = []
        for req_type in request_type_names:
            if req_type in framework_data[fw]['request_types']:
                count = framework_data[fw]['request_types'][req_type]['count']
            else:
                count = 0
            row.append(count)
        data_counts.append(row)
    
    sns.heatmap(data_counts, annot=True, fmt='d', cmap='YlOrRd', 
               xticklabels=request_type_names, yticklabels=frameworks, 
               ax=ax1, cbar_kws={'label': 'Count'})
    ax1.set_title('Request Count by Type', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Framework', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Request Type', fontsize=11, fontweight='bold')
    
    # Heatmap 2: Data transfer size (MB)
    data_sizes = []
    for fw in frameworks:
        row = []
        for req_type in request_type_names:
            if req_type in framework_data[fw]['request_types']:
                size_mb = framework_data[fw]['request_types'][req_type]['size'] / (1024 * 1024)
            else:
                size_mb = 0
            row.append(size_mb)
        data_sizes.append(row)
    
    sns.heatmap(data_sizes, annot=True, fmt='.2f', cmap='Blues',
               xticklabels=request_type_names, yticklabels=frameworks,
               ax=ax2, cbar_kws={'label': 'MB'})
    ax2.set_title('Data Transfer by Type (MB)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Framework', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Request Type', fontsize=11, fontweight='bold')
    
    plt.suptitle('Request Type Breakdown Heatmaps', fontsize=13, fontweight='bold')
    plt.tight_layout()
    
    output_file = IMAGES_DIR / 'data_transfer_heatmap.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

if __name__ == "__main__":
    print("Analyzing sitespeed.io data transfer metrics...")
    framework_data = analyze_all_frameworks()
    
    if framework_data:
        print("\nCreating visualizations...")
        create_visualizations(framework_data, runs_per_benchmark=20)
        print(f"\n✓ Done! Check {IMAGES_DIR / 'data_transfer_report.png'} and {IMAGES_DIR / 'data_transfer_heatmap.png'}")
    else:
        print("No data found to visualize")
