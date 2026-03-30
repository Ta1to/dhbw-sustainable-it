#!/usr/bin/env python3
"""
Sustainability Analysis Tool for Framework Comparison
Analyzes CPU resource consumption across frameworks for sustainable IT metrics.
Dynamically discovers and analyzes all available benchmark results.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set


BENCHMARK_DIR = Path(__file__).resolve().parent.parent


class SustainabilityAnalyzer:
    """Analyzes framework sustainability based on CPU consumption."""

    def __init__(self, results_dir: str):
        """Initialize analyzer with results directory."""
        self.results_dir = Path(results_dir)
        self.data = {}
        self.frameworks = []
        self.discover_frameworks()

    def discover_frameworks(self) -> List[str]:
        """Dynamically discover all available frameworks from benchmark results."""
        results_path = self.results_dir / "results"
        
        if not results_path.exists():
            print(f"Warning: Results directory not found at {results_path}")
            return []

        frameworks = set()
        
        # Look for benchmark directories (e.g., sitespeed_bench_20260324_100353)
        for bench_dir in results_path.glob("sitespeed_bench_*"):
            if bench_dir.is_dir():
                # Each benchmark directory contains framework subdirectories
                for framework_dir in bench_dir.iterdir():
                    if framework_dir.is_dir() and (framework_dir / "pages").exists():
                        frameworks.add(framework_dir.name)

        self.frameworks = sorted(list(frameworks))
        return self.frameworks

    def find_har_files(self) -> Dict[str, Path]:
        """Dynamically find all HAR files for discovered frameworks."""
        har_files = {}
        results_path = self.results_dir / "results"

        if not results_path.exists():
            return har_files

        for bench_dir in results_path.glob("sitespeed_bench_*"):
            if bench_dir.is_dir():
                for framework_dir in bench_dir.iterdir():
                    if framework_dir.is_dir():
                        har_path = (
                            framework_dir
                            / "pages"
                            / "localhost"
                            / "products"
                            / "data"
                            / "browsertime.har"
                        )
                        if har_path.exists():
                            framework_name = framework_dir.name
                            # Store first found HAR file for each framework
                            if framework_name not in har_files:
                                har_files[framework_name] = har_path

        return har_files

    def extract_cpu_metrics(self, har_path: Path) -> Dict[str, float]:
        """Extract CPU metrics from HAR file."""
        try:
            with open(har_path) as f:
                data = json.load(f)

            pages = data.get("log", {}).get("pages", [])

            if not pages:
                return {}

            # Average CPU metrics across all pages
            avg_metrics = {
                "js_eval": 0,
                "script_parse": 0,
                "style_layout": 0,
                "paint_composite": 0,
                "gc": 0,
                "runtask": 0,
                "microtasks": 0,
                "other": 0,
            }

            for page in pages:
                cpu = page.get("_cpu", {})
                if isinstance(cpu, dict):
                    categories = cpu.get("categories", {})
                    events = cpu.get("events", {})

                    avg_metrics["js_eval"] += categories.get("scriptEvaluation", 0)
                    avg_metrics["script_parse"] += categories.get("scriptParseCompile", 0)
                    avg_metrics["style_layout"] += categories.get("styleLayout", 0)
                    avg_metrics["paint_composite"] += categories.get(
                        "paintCompositeRender", 0
                    )
                    avg_metrics["gc"] += categories.get("garbageCollection", 0)
                    avg_metrics["runtask"] += events.get("RunTask", 0)
                    avg_metrics["microtasks"] += events.get("RunMicrotasks", 0)
                    avg_metrics["other"] += categories.get("other", 0)

            # Calculate averages
            if pages:
                for key in avg_metrics:
                    avg_metrics[key] = avg_metrics[key] / len(pages)

            # Calculate total CPU
            avg_metrics["total"] = sum(
                v for k, v in avg_metrics.items() if k != "total"
            )

            return avg_metrics

        except Exception as e:
            print(f"Error processing {har_path}: {e}")
            return {}

    def load_all_metrics(self):
        """Load metrics for all discovered frameworks."""
        har_files = self.find_har_files()
        
        if not har_files:
            print("Error: No HAR files found in results directory")
            return False

        for framework, har_path in har_files.items():
            metrics = self.extract_cpu_metrics(har_path)
            if metrics:
                self.data[framework.capitalize()] = metrics
                print(f"✓ Loaded metrics for {framework.capitalize()}")

        if not self.data:
            print("Error: Could not load metrics for any frameworks")
            return False

        return True

    def print_sustainability_report(self):
        """Print comprehensive sustainability report."""
        if not self.load_all_metrics():
            return

        print("\n" + "=" * 140)
        print(" " * 30 + "SUSTAINABILITY ANALYSIS: CPU RESOURCE CONSUMPTION")
        print(f" " * 20 + f"Analyzing {len(self.data)} frameworks")
        print("=" * 140 + "\n")

        stats_order = [
            ("1. TOTAL CPU TIME", "total", "Sum of all CPU-consuming operations"),
            ("2. JavaScript Evaluation", "js_eval", "CPU spent executing JavaScript code"),
            (
                "3. Garbage Collection Overhead",
                "gc",
                "CPU wasted on memory management",
            ),
            ("4. Script Parse/Compile", "script_parse", "CPU spent parsing/compiling JS"),
            (
                "5. Style & Layout Calculations",
                "style_layout",
                "CPU for DOM operations",
            ),
            (
                "6. Paint & Composite Rendering",
                "paint_composite",
                "CPU for pixel rendering",
            ),
            ("7. RunTask (Main Thread Work)", "runtask", "Total main thread CPU time"),
            (
                "8. RunMicrotasks (Framework Scheduler)",
                "microtasks",
                "CPU for framework scheduling",
            ),
            ("9. Other/Miscellaneous CPU", "other", "CPU for other operations"),
        ]

        # Get framework names dynamically
        framework_names = sorted(self.data.keys())
        
        # Build header dynamically
        header = f"{'Metric':<50}"
        for fw in framework_names:
            header += f" {fw:<15}"
        header += f" {'Winner':<15}"
        
        print(header)
        print("-" * (50 + 15 * len(framework_names) + 15))

        for stat_name, key, description in stats_order:
            values = {fw: self.data[fw].get(key, 0) for fw in self.data.keys()}
            
            # Skip if this metric doesn't exist in any framework
            if not any(values.values()):
                continue
                
            winner = min(values, key=values.get)
            formatted = {fw: f"{val:.2f}" for fw, val in values.items()}

            line = f"{stat_name:<50}"
            for fw in framework_names:
                line += f" {formatted.get(fw, '0.00'):<15}"
            line += f" {winner:<15}"
            
            print(line)
            print()

        # Sustainability ranking
        print("=" * 140)
        print("SUSTAINABILITY RANKING (Lower CPU = More Sustainable)")
        print("=" * 140 + "\n")

        ranked = sorted(
            [(fw, self.data[fw].get("total", 0)) for fw in self.data.keys()],
            key=lambda x: x[1],
        )
        best_cpu = ranked[0][1] if ranked else 1
        medals = ["🥇", "🥈", "🥉"]

        for rank, (fw, cpu_time) in enumerate(ranked):
            medal = medals[rank] if rank < len(medals) else "  "
            if rank == 0:
                print(
                    f"{medal} {rank + 1}. {fw:<15} Total CPU: {cpu_time:>7.2f} ms  (MOST SUSTAINABLE)"
                )
            else:
                extra = ((cpu_time - best_cpu) / best_cpu * 100)
                print(
                    f"{medal} {rank + 1}. {fw:<15} Total CPU: {cpu_time:>7.2f} ms  (+{extra:.1f}% more CPU than {ranked[0][0]})"
                )

        # Detailed insights
        print("\n" + "=" * 140)
        print("DETAILED ANALYSIS")
        print("=" * 140 + "\n")

        for rank, (fw, cpu_time) in enumerate(ranked):
            medal_emoji = medals[rank] if rank < len(medals) else "  "
            extra_pct = ((cpu_time - best_cpu) / best_cpu * 100) if rank > 0 else 0
            
            print(f"{medal_emoji} {fw} ({cpu_time:.2f} ms total CPU)")
            if rank > 0:
                print(f"   {extra_pct:.1f}% more CPU than best performer")
            
            # Show breakdown
            metrics = self.data[fw]
            print(f"   Breakdown:")
            sorted_metrics = sorted(
                [(k, v) for k, v in metrics.items() if k != "total"],
                key=lambda x: x[1],
                reverse=True
            )
            for metric_name, value in sorted_metrics[:5]:  # Show top 5
                pct_of_total = (value / cpu_time * 100) if cpu_time > 0 else 0
                print(f"      • {metric_name:20} {value:>7.2f} ms ({pct_of_total:>5.1f}%)")
            print()

        # Energy impact
        print("=" * 140)
        print("ENERGY IMPACT CALCULATION")
        print("=" * 140 + "\n")

        print("Per page load (estimated: 1 CPU ms ≈ 1 mJ of energy):\n")

        ranked = sorted(
            [(fw, self.data[fw].get("total", 0)) for fw in self.data.keys()],
            key=lambda x: x[1],
        )

        for fw, cpu_ms in ranked:
            mj_per_load = cpu_ms

            print(f"{fw:<15}")
            print(f"  • Per page load:    {mj_per_load:.0f} mJ")
            print(f"  • Per 1,000 loads:  {mj_per_load * 1000:.0f} mJ ({mj_per_load / 1000:.1f} J)")
            print(f"  • Per 1M loads:     {mj_per_load * 1000000 / 1000000:.1f} J ({mj_per_load / 1000:.1f} kJ)")
            print()

        # Recommendation
        print("=" * 140)
        print("SUSTAINABILITY RECOMMENDATION")
        print("=" * 140)
        
        best_fw = ranked[0][0]
        worst_fw = ranked[-1][0] if len(ranked) > 1 else None
        savings = (ranked[-1][1] - ranked[0][1]) if worst_fw else 0
        
        print(f"""
FOR YOUR SUSTAINABLE IT PROJECT:

FINDINGS:
  Framework with lowest CPU: {best_fw:<15} {ranked[0][1]:.2f} ms per page
""")
        
        if worst_fw:
            print(f"  Framework with highest CPU: {worst_fw:<12} {ranked[-1][1]:.2f} ms per page")
            print(f"  Potential savings: {savings:.2f} ms per page load ({savings / ranked[-1][1] * 100:.1f}% reduction)")
            print(f"  Per 1M page loads: {savings * 1000000 / 1000000:.1f} J ({savings / 1000:.1f} kJ) saved")

        print(f"""
ACTIONABLE METRICS TO TRACK:
  1. Total CPU per page       ← Most important
  2. JavaScript evaluation    ← Framework overhead
  3. Garbage collection       ← Memory efficiency
  4. RunMicrotasks            ← Framework scheduler cost
  5. Script parse/compile     ← JS parsing overhead
""")


def main():
    """Main entry point."""
    # Benchmark root directory (one level above scripts directory)
    benchmark_dir = BENCHMARK_DIR
    
    analyzer = SustainabilityAnalyzer(str(benchmark_dir))
    
    print(f"📊 Sustainability Analysis Tool")
    print(f"📁 Searching for benchmarks in: {benchmark_dir / 'results'}\n")
    
    if not analyzer.frameworks:
        print(f"❌ No frameworks discovered. Make sure HAR files exist in:")
        print(f"   {benchmark_dir}/results/sitespeed_bench_*/*/pages/localhost/products/data/browsertime.har")
        return
    
    print(f"✓ Discovered {len(analyzer.frameworks)} frameworks: {', '.join(analyzer.frameworks)}\n")
    
    analyzer.print_sustainability_report()


if __name__ == "__main__":
    main()
