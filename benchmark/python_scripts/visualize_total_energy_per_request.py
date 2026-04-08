#!/usr/bin/env python3
"""
Visualize total energy usage per request across frameworks.

This script combines:
1) Server-side energy per request from autocannon benchmark results.
2) Client-side CPU energy per request from HAR CPU timing data.
3) Client-side network transfer energy per request using SWDM v4 (operational network).

Outputs:
- benchmark/images/total_energy_per_request_report.png
- benchmark/images/total_energy_per_request_heatmap.png
"""

import json
from pathlib import Path
from collections import defaultdict
from statistics import pstdev
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


BENCHMARK_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BENCHMARK_DIR / "images"

# -----------------------------
# Constants and assumptions
# -----------------------------

# Autocannon benchmark duration in seconds (used in existing scripts).
AUTOCANNON_RUN_SECONDS = 60.0

# Assumed average client device power draw while actively loading/rendering.
# You can tune this if you have measured device power.
CLIENT_DEVICE_POWER_WATTS = 15.0

# SWDM v4 values from Green Web Foundation update (operational only):
# - Network operational energy: 310 TWh
# - Total internet data transfer: 5.29 ZB
SWDM_V4_NETWORK_OPERATIONAL_ENERGY_TWH = 310.0
SWDM_V4_TOTAL_DATA_ZB = 5.29

SWDM_V4_TWH_BY_DOMAIN = {
    "data_centers": {"operational": 290.0, "embodied": 62.0},
    "networks": {"operational": 310.0, "embodied": 68.0},
    "user_devices": {"operational": 421.0, "embodied": 430.0},
}

# SWDM uses decimal data units in internet-scale reporting.
BYTES_PER_GB_DECIMAL = 1_000_000_000
BYTES_PER_MIB = 1024 * 1024
JOULES_PER_KWH = 3_600_000
TWH_TO_KWH = 1_000_000_000
ZB_TO_GB_DECIMAL = 1_000_000_000_000
UWH_PER_JOULE = 1_000_000 / 3600
REQUEST_SCALE_LARGE = 1_000_000


def twh_to_kwh_per_gb(twh_value: float) -> float:
    """Convert TWh over global transfer baseline to kWh/GB."""
    return (twh_value * TWH_TO_KWH) / (SWDM_V4_TOTAL_DATA_ZB * ZB_TO_GB_DECIMAL)


def swdm_v4_domain_energy_components_j(transfer_bytes_per_request: float):
    """Calculate SWDM v4 energy per request for every domain and component."""
    gb_per_request = transfer_bytes_per_request / BYTES_PER_GB_DECIMAL
    components = {}

    for domain, parts in SWDM_V4_TWH_BY_DOMAIN.items():
        op_j = gb_per_request * twh_to_kwh_per_gb(parts["operational"]) * JOULES_PER_KWH
        emb_j = gb_per_request * twh_to_kwh_per_gb(parts["embodied"]) * JOULES_PER_KWH
        components[f"{domain}_operational_j_per_req"] = op_j
        components[f"{domain}_embodied_j_per_req"] = emb_j

    components["swdm_v4_total_j_per_req"] = sum(components.values())
    return components


def normalize_framework_name(name: str) -> str:
    """Normalize framework names to a consistent display format."""
    lower = name.lower()
    if "astro" in lower:
        return "Astro"
    if "next" in lower:
        return "Next.js"
    if "svelte" in lower:
        return "Svelte"
    return name.capitalize()


def discover_product_runs():
    """Find product benchmark runs used for server-side power data."""
    results_path = BENCHMARK_DIR / "results" / "products"
    if not results_path.exists():
        return []
    return sorted([d for d in results_path.iterdir() if d.is_dir()])


def discover_sitespeed_runs():
    """Find sitespeed benchmark runs used for client-side HAR data."""
    results_path = BENCHMARK_DIR / "results"
    if not results_path.exists():
        return []
    return sorted([d for d in results_path.glob("sitespeed_bench_*") if d.is_dir()])


def load_json_file(path: Path):
    """Load JSON safely and return None on failure."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def collect_server_energy_per_request():
    """
    Compute server-side energy per request (J/request) from product runs.

    Also returns average server-side request counts per framework so other metrics
    can be normalized with the same baseline as visualize_energy.py.
    """
    data = defaultdict(list)
    avg_requests_by_framework = defaultdict(list)

    for run_dir in discover_product_runs():
        perf_files = list(run_dir.glob("*_perf.json"))
        watts_files = list(run_dir.glob("*-server_watts.json"))

        perf_by_framework = defaultdict(list)
        watts_by_framework = defaultdict(list)

        for perf_file in perf_files:
            framework = normalize_framework_name(perf_file.name)
            perf_json = load_json_file(perf_file)
            if perf_json is None:
                continue
            requests_total = perf_json.get("requests", {}).get("total", 0)
            if requests_total and requests_total > 0:
                perf_by_framework[framework].append(float(requests_total))

        for watts_file in watts_files:
            framework = normalize_framework_name(watts_file.name)
            watts_json = load_json_file(watts_file)
            if watts_json is None:
                continue
            result = watts_json.get("data", {}).get("result", [])
            if result:
                value = result[0].get("value", [0, 0])
                if len(value) > 1:
                    try:
                        watts_by_framework[framework].append(float(value[1]))
                    except (ValueError, TypeError):
                        pass

        for framework in set(perf_by_framework.keys()) | set(watts_by_framework.keys()):
            requests_values = perf_by_framework.get(framework, [])
            watts_values = watts_by_framework.get(framework, [])
            if not requests_values or not watts_values:
                continue

            avg_requests = sum(requests_values) / len(requests_values)
            avg_watts = sum(watts_values) / len(watts_values)
            if avg_requests <= 0:
                continue

            # Existing approach: energy = power * time, then divide by requests.
            energy_per_request_j = (avg_watts * AUTOCANNON_RUN_SECONDS) / avg_requests
            data[framework].append(energy_per_request_j)
            avg_requests_by_framework[framework].append(avg_requests)

    # Average across all discovered runs.
    energy_per_req = {
        framework: sum(values) / len(values)
        for framework, values in data.items()
        if values
    }

    requests_avg = {
        framework: sum(values) / len(values)
        for framework, values in avg_requests_by_framework.items()
        if values
    }

    return energy_per_req, requests_avg


def extract_cpu_and_transfer_from_har(har_path: Path):
    """
    Extract average total CPU time per page (ms) and average transfer bytes per page
    from a HAR file.

    For client metrics, we treat one full page load as one user request.
    """
    payload = load_json_file(har_path)
    if payload is None:
        return None

    log = payload.get("log", {})
    pages = log.get("pages", [])
    entries = log.get("entries", [])

    if not pages:
        return None

    total_cpu_ms = 0.0
    for page in pages:
        cpu = page.get("_cpu", {})
        categories = cpu.get("categories", {}) if isinstance(cpu, dict) else {}
        events = cpu.get("events", {}) if isinstance(cpu, dict) else {}

        page_cpu_ms = (
            categories.get("scriptEvaluation", 0)
            + categories.get("scriptParseCompile", 0)
            + categories.get("styleLayout", 0)
            + categories.get("paintCompositeRender", 0)
            + categories.get("garbageCollection", 0)
            + events.get("RunTask", 0)
            + events.get("RunMicrotasks", 0)
            + categories.get("other", 0)
        )
        total_cpu_ms += float(page_cpu_ms)

    total_bytes = 0.0
    for entry in entries:
        response = entry.get("response", {})
        content = response.get("content", {})
        content_size = content.get("size", 0)
        body_size = response.get("bodySize", 0)

        # Prefer positive content size and fall back to positive body size.
        if isinstance(content_size, (int, float)) and content_size > 0:
            total_bytes += float(content_size)
        elif isinstance(body_size, (int, float)) and body_size > 0:
            total_bytes += float(body_size)

    page_count = len(pages)
    avg_cpu_ms_per_page = total_cpu_ms / page_count
    avg_transfer_bytes_per_page = total_bytes / page_count if page_count > 0 else 0.0
    return {
        "cpu_ms_per_page": avg_cpu_ms_per_page,
        "transfer_bytes_per_page": avg_transfer_bytes_per_page,
        "page_count": page_count,
    }


def collect_client_energy_per_request():
    """
    Compute client-side CPU and network energy per request from sitespeed HAR files.

    Important: "per request" on client side means per page-load request (one user
    page visit), not per individual HTTP asset request in the HAR.

    Returns per-framework averages for:
    - CPU energy (J/request)
    - Network energy (J/request, operational network only)
    - CPU time (ms/page load)
    - Data transfer (bytes/page load)
    """
    cpu_energy_by_framework = defaultdict(list)
    network_energy_by_framework = defaultdict(list)
    cpu_ms_by_framework = defaultdict(list)
    transfer_bytes_by_framework = defaultdict(list)
    client_energy_1k_by_framework = defaultdict(list)

    # Network energy intensity derived from SWDM v4 operational network energy only.
    # Convert TWh/ZB to kWh/GB explicitly to avoid unit mistakes.
    # kWh/GB = (TWh * 1e9 kWh/TWh) / (ZB * 1e12 GB/ZB)
    network_kwh_per_gb = (
        (SWDM_V4_NETWORK_OPERATIONAL_ENERGY_TWH * TWH_TO_KWH)
        / (SWDM_V4_TOTAL_DATA_ZB * ZB_TO_GB_DECIMAL)
    )

    for run_dir in discover_sitespeed_runs():
        for framework_dir in run_dir.iterdir():
            if not framework_dir.is_dir():
                continue

            har_path = (
                framework_dir
                / "pages"
                / "localhost"
                / "products"
                / "data"
                / "browsertime.har"
            )
            if not har_path.exists():
                continue

            framework = normalize_framework_name(framework_dir.name)
            metrics = extract_cpu_and_transfer_from_har(har_path)
            if not metrics:
                continue

            # CPU energy per page-load request in Joules.
            cpu_seconds_per_request = metrics["cpu_ms_per_page"] / 1000.0
            cpu_energy_per_request_j = CLIENT_DEVICE_POWER_WATTS * cpu_seconds_per_request

            # Network energy per page-load request in Joules from SWDM v4 network share.
            gb_per_request = metrics["transfer_bytes_per_page"] / BYTES_PER_GB_DECIMAL
            network_energy_per_request_j = gb_per_request * network_kwh_per_gb * JOULES_PER_KWH

            cpu_energy_by_framework[framework].append(cpu_energy_per_request_j)
            network_energy_by_framework[framework].append(network_energy_per_request_j)
            cpu_ms_by_framework[framework].append(metrics["cpu_ms_per_page"])
            transfer_bytes_by_framework[framework].append(metrics["transfer_bytes_per_page"])
            client_energy_1k_by_framework[framework].append(
                (cpu_energy_per_request_j + network_energy_per_request_j) * 1000
            )

    cpu_avg = {
        fw: sum(values) / len(values)
        for fw, values in cpu_energy_by_framework.items()
        if values
    }
    network_avg = {
        fw: sum(values) / len(values)
        for fw, values in network_energy_by_framework.items()
        if values
    }

    cpu_ms_avg = {
        fw: sum(values) / len(values)
        for fw, values in cpu_ms_by_framework.items()
        if values
    }

    transfer_bytes_avg = {
        fw: sum(values) / len(values)
        for fw, values in transfer_bytes_by_framework.items()
        if values
    }

    client_1k_std = {
        fw: pstdev(values) if len(values) > 1 else 0.0
        for fw, values in client_energy_1k_by_framework.items()
        if values
    }

    sample_count = {
        fw: len(values)
        for fw, values in client_energy_1k_by_framework.items()
        if values
    }

    return cpu_avg, network_avg, cpu_ms_avg, transfer_bytes_avg, client_1k_std, sample_count


def combine_metrics(
    server,
    server_requests_avg,
    client_cpu,
    client_network,
    client_cpu_ms,
    transfer_bytes,
    client_1k_std,
    sample_count,
):
    """Combine all components into a single per-framework metric dictionary."""
    frameworks = sorted(
        set(server.keys())
        | set(client_cpu.keys())
        | set(client_network.keys())
        | set(client_cpu_ms.keys())
        | set(transfer_bytes.keys())
    )

    combined = {}
    for fw in frameworks:
        server_j = server.get(fw, 0.0)
        client_cpu_j = client_cpu.get(fw, 0.0)
        client_network_j = client_network.get(fw, 0.0)
        server_requests_avg_value = server_requests_avg.get(fw, 0.0)
        cpu_ms_per_page = client_cpu_ms.get(fw, 0.0)
        transfer_bytes_per_page = transfer_bytes.get(fw, 0.0)
        total_j = server_j + client_cpu_j + client_network_j
        swdm_components = swdm_v4_domain_energy_components_j(transfer_bytes_per_page)

        client_total_j_per_1k_req = (client_cpu_j + client_network_j) * 1000.0
        
        client_total_j_per_1k_req_std = client_1k_std.get(fw, 0.0)

        combined[fw] = {
            "server_j_per_req": server_j,
            "server_j_per_1k_req": server_j * 1000.0,
            "client_cpu_j_per_req": client_cpu_j,
            "client_network_j_per_req": client_network_j,
            "client_cpu_ms_per_page": cpu_ms_per_page,
            "data_transfer_mib_per_page": transfer_bytes_per_page / BYTES_PER_MIB,
            "client_total_j_per_req": client_cpu_j + client_network_j,
            "client_total_j_per_1k_req": client_total_j_per_1k_req,
            "client_total_j_per_1k_req_std": client_total_j_per_1k_req_std,
            "sample_count": sample_count.get(fw, 0),
            "total_j_per_req": total_j,
            "total_uwh_per_req": total_j * UWH_PER_JOULE,
            "total_kwh_per_1m_req": (total_j * REQUEST_SCALE_LARGE) / JOULES_PER_KWH,
            "server_avg_requests": server_requests_avg_value,
        }
        combined[fw].update(swdm_components)

    return combined


def create_report_figure(combined):
    """Create a multi-panel report figure for total energy per request."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if not combined:
        print("No data available to visualize")
        return

    frameworks = sorted(combined.keys())
    server_vals = [combined[fw]["server_j_per_req"] for fw in frameworks]
    cpu_vals = [combined[fw]["client_cpu_j_per_req"] for fw in frameworks]
    network_vals = [combined[fw]["client_network_j_per_req"] for fw in frameworks]
    server_1k_vals = [combined[fw]["server_j_per_1k_req"] for fw in frameworks]
    cpu_ms_vals = [combined[fw]["client_cpu_ms_per_page"] for fw in frameworks]
    transfer_mib_vals = [combined[fw]["data_transfer_mib_per_page"] for fw in frameworks]

    # Theme aligned with the presentation cover (teal/green, high-contrast text)
    COLOR_BG = "#255D59"
    COLOR_PANEL = "#2C6A65"
    COLOR_TEXT = "#ECF4EF"
    COLOR_GRID = "#79A89A"
    COLOR_SERVER = "#67C26F"
    COLOR_CPU = "#3DB3A2"
    COLOR_NETWORK = "#8FD7C9"
    COLOR_HL1 = "#5FD38B"
    COLOR_HL2 = "#9BE564"
    COLOR_HL3 = "#FFB86C"

    sns.set_style("darkgrid")
    fig = plt.figure(figsize=(20, 11), facecolor=COLOR_BG)
    fig.suptitle(
        "Total Energy per Request Across Frameworks",
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXT,
        y=0.98,
    )

    def style_axis(ax):
        ax.set_facecolor(COLOR_PANEL)
        for spine in ax.spines.values():
            spine.set_color(COLOR_GRID)
            spine.set_alpha(0.5)
        ax.grid(axis="y", color=COLOR_GRID, alpha=0.25, linewidth=0.8)
        ax.tick_params(colors=COLOR_TEXT)
        ax.xaxis.label.set_color(COLOR_TEXT)
        ax.yaxis.label.set_color(COLOR_TEXT)
        ax.title.set_color(COLOR_TEXT)

    # 1) Client-side energy per 1,000 requests
    ax1 = plt.subplot(2, 3, 1)
    bars = ax1.bar(frameworks, server_1k_vals, color=COLOR_HL1, edgecolor="#224E41", linewidth=1.0)
    ax1.set_ylabel("Energy (J/1,000 requests)", fontweight="bold")
    ax1.set_title("1. Server-side Energy per 1,000 Requests", fontweight="bold")
    style_axis(ax1)

    for bar in bars:
        h = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            h,
            f"{h:.2f} J",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=9,
            color=COLOR_TEXT,
        )

    # 2) Total CPU time per page load
    ax2 = plt.subplot(2, 3, 2)
    bars = ax2.bar(frameworks, cpu_ms_vals, color=COLOR_HL2, edgecolor="#456A2B", linewidth=1.0)
    ax2.set_ylabel("CPU Time (ms/page load)", fontweight="bold")
    ax2.set_title("2. Total CPU Time per Page Load", fontweight="bold")
    style_axis(ax2)

    for bar in bars:
        h = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            h,
            f"{h:.1f}ms",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=9,
            color=COLOR_TEXT,
        )

    # 3) Data transfer per page load
    ax3 = plt.subplot(2, 3, 3)
    bars = ax3.bar(frameworks, transfer_mib_vals, color=COLOR_HL3, edgecolor="#7D5428", linewidth=1.0)
    ax3.set_ylabel("Data Transfer (MiB/page load)", fontweight="bold")
    ax3.set_title("3. Data Transfer per Page Load", fontweight="bold")
    style_axis(ax3)

    for bar in bars:
        h = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            h,
            f"{h:.2f} MiB",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=9,
            color=COLOR_TEXT,
        )

    # 5) Stacked components in J/request
    ax4 = plt.subplot(2, 3, 5)
    ax4.bar(frameworks, server_vals, label="Server", color=COLOR_SERVER, edgecolor="#2F7E48", linewidth=0.8)
    ax4.bar(frameworks, cpu_vals, bottom=server_vals, label="Client CPU", color=COLOR_CPU, edgecolor="#1E7568", linewidth=0.8)

    bottoms = [server_vals[i] + cpu_vals[i] for i in range(len(frameworks))]
    ax4.bar(
        frameworks,
        network_vals,
        bottom=bottoms,
        label="Client Network",
        color=COLOR_NETWORK,
        edgecolor="#4E8C82",
        linewidth=0.8,
    )

    ax4.set_ylabel("Energy (J/request)", fontweight="bold")
    ax4.set_title("5. Energy Components per Request", fontweight="bold")
    style_axis(ax4)
    legend4 = ax4.legend(fontsize=8, facecolor=COLOR_PANEL, edgecolor=COLOR_GRID)
    for t in legend4.get_texts():
        t.set_color(COLOR_TEXT)

    # 4) Energy usage per request (server vs client CPU)
    ax5 = plt.subplot(2, 3, 4)
    server_j_per_req_from_stat1 = server_vals
    client_j_per_req_from_stat2 = [(ms / 1000.0) * CLIENT_DEVICE_POWER_WATTS for ms in cpu_ms_vals]

    def format_joule(val: float) -> str:
        if val >= 1:
            return f"{val:.2f} J"
        if val >= 0.01:
            return f"{val:.3f} J"
        return f"{val:.6f} J"

    bars_server = ax5.bar(
        frameworks,
        server_j_per_req_from_stat1,
        label="Server-side",
        color=COLOR_SERVER,
        edgecolor="#2F7E48",
        linewidth=0.8,
    )
    bars_client = ax5.bar(
        frameworks,
        client_j_per_req_from_stat2,
        bottom=server_j_per_req_from_stat1,
        label=f"Client-side CPU ({CLIENT_DEVICE_POWER_WATTS:.0f}W)",
        color=COLOR_CPU,
        edgecolor="#1E7568",
        linewidth=0.8,
    )

    ax5.set_ylabel("Energy (J/request)", fontweight="bold")
    ax5.set_title("4. Energy Usage per Request (Stacked: Server + Client CPU)", fontweight="bold")
    style_axis(ax5)

    for bar in bars_server:
        h = bar.get_height()
        ax5.text(
            bar.get_x() + bar.get_width() / 2.0,
            h,
            format_joule(h),
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=8,
            color=COLOR_TEXT,
        )

    for i, bar in enumerate(bars_client):
        h = bar.get_height()
        top = server_j_per_req_from_stat1[i] + h
        ax5.text(
            bar.get_x() + bar.get_width() / 2.0,
            top,
            format_joule(h),
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=8,
            color=COLOR_TEXT,
        )

    # Use logarithmic scaling for better readability when framework values differ
    # by orders of magnitude.
    positive_vals = [v for v in server_j_per_req_from_stat1 + client_j_per_req_from_stat2 if v > 0]
    if positive_vals:
        min_positive = min(positive_vals)
        max_stacked = max(
            server_j_per_req_from_stat1[i] + client_j_per_req_from_stat2[i]
            for i in range(len(frameworks))
        )
        ax5.set_yscale("log")
        ax5.set_ylim(min_positive * 0.8, max_stacked * 1.6)

    legend5 = ax5.legend(
        fontsize=8,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        facecolor=COLOR_PANEL,
        edgecolor=COLOR_GRID,
    )
    for t in legend5.get_texts():
        t.set_color(COLOR_TEXT)

    # 6) SWDM v4 total by domain and component (operational + embodied)
    ax6 = plt.subplot(2, 3, 6)
    swdm_components = [
        ("data_centers_operational_j_per_req", "Datacenter Operational", "#1f77b4"),
        ("data_centers_embodied_j_per_req", "Datacenter Embodied", "#aec7e8"),
        ("networks_operational_j_per_req", "Network Operational", "#2ca02c"),
        ("networks_embodied_j_per_req", "Network Embodied", "#98df8a"),
        ("user_devices_operational_j_per_req", "Device Operational", "#ff7f0e"),
        ("user_devices_embodied_j_per_req", "Device Embodied", "#ffbb78"),
    ]
    bottoms = [0.0] * len(frameworks)
    for key, label, color in swdm_components:
        values = [combined[fw][key] for fw in frameworks]
        ax6.bar(frameworks, values, bottom=bottoms, label=label, color=color)
        bottoms = [bottoms[i] + values[i] for i in range(len(values))]

    ax6.set_ylabel("Energy (J/request)", fontweight="bold")
    ax6.set_title("6. SWDM v4 Domains (Operational + Embodied)", fontweight="bold")
    style_axis(ax6)
    legend6 = ax6.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.02, 1.0), facecolor=COLOR_PANEL, edgecolor=COLOR_GRID)
    for t in legend6.get_texts():
        t.set_color(COLOR_TEXT)

    plt.tight_layout()

    output_path = IMAGES_DIR / "total_energy_per_request_report.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Visualization saved to: {output_path}")
    plt.close()


def create_heatmap(combined):
    """Create heatmap comparing component energy per request."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if not combined:
        return

    df = pd.DataFrame.from_dict(combined, orient="index")
    heatmap_df = df[[
        "server_j_per_1k_req",
        "client_cpu_ms_per_page",
        "data_transfer_mib_per_page",
        "server_j_per_req",
        "client_cpu_j_per_req",
        "client_network_j_per_req",
        "total_j_per_req",
        "total_kwh_per_1m_req",
        "data_centers_operational_j_per_req",
        "data_centers_embodied_j_per_req",
        "networks_operational_j_per_req",
        "networks_embodied_j_per_req",
        "user_devices_operational_j_per_req",
        "user_devices_embodied_j_per_req",
        "swdm_v4_total_j_per_req",
    ]].rename(columns={
        "server_j_per_1k_req": "Server Energy (J/1k req)",
        "client_cpu_ms_per_page": "CPU Time (ms/page)",
        "data_transfer_mib_per_page": "Transfer (MiB/page)",
        "server_j_per_req": "Server (J/req)",
        "client_cpu_j_per_req": "Client CPU (J/req)",
        "client_network_j_per_req": "Client Network (J/req)",
        "total_j_per_req": "Total (J/req)",
        "total_kwh_per_1m_req": "Total (kWh/1M req)",
        "data_centers_operational_j_per_req": "SWDM DC Op (J/req)",
        "data_centers_embodied_j_per_req": "SWDM DC Emb (J/req)",
        "networks_operational_j_per_req": "SWDM Net Op (J/req)",
        "networks_embodied_j_per_req": "SWDM Net Emb (J/req)",
        "user_devices_operational_j_per_req": "SWDM Dev Op (J/req)",
        "user_devices_embodied_j_per_req": "SWDM Dev Emb (J/req)",
        "swdm_v4_total_j_per_req": "SWDM Total (J/req)",
    })

    plt.figure(figsize=(11, 6), facecolor="#255D59")
    ax = plt.gca()
    ax.set_facecolor("#2C6A65")
    sns.heatmap(
        heatmap_df,
        annot=True,
        fmt=".6f",
        cmap="YlGn",
        linewidths=0.5,
        cbar_kws={"label": "Relative scale (mixed column units)"},
        annot_kws={"color": "#123126", "fontsize": 8, "fontweight": "bold"},
    )
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_color("#ECF4EF")
    cbar.ax.tick_params(color="#ECF4EF", labelcolor="#ECF4EF")
    plt.title("Total Energy per Request Heatmap", fontweight="bold", pad=16, color="#ECF4EF")
    plt.ylabel("Framework", fontweight="bold", color="#ECF4EF")
    plt.xlabel("Energy Components", fontweight="bold", color="#ECF4EF")
    ax.tick_params(colors="#ECF4EF")
    plt.tight_layout()

    output_path = IMAGES_DIR / "total_energy_per_request_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Heatmap saved to: {output_path}")
    plt.close()


def print_summary(combined):
    """Print console summary table for quick inspection."""
    if not combined:
        print("No combined data found")
        return

    print("\n" + "=" * 160)
    print("TOTAL ENERGY PER REQUEST SUMMARY")
    print("=" * 160)
    print(
        f"{'Framework':<12} {'Server J/1k':>14} {'CPU ms/page':>12} {'Transfer MiB/page':>16} "
        f"{'Server J/req':>12} {'Client CPU J':>14} {'Client Net J':>14} {'kWh/1M req':>12} {'SWDM total J':>14}"
    )
    print("-" * 160)

    for fw in sorted(combined.keys()):
        m = combined[fw]
        print(
            f"{fw:<12} {m['server_j_per_1k_req']:>14.6f} {m['client_cpu_ms_per_page']:>12.2f} "
            f"{m['data_transfer_mib_per_page']:>16.3f} {m['server_j_per_req']:>12.6f} "
            f"{m['client_cpu_j_per_req']:>14.6f} {m['client_network_j_per_req']:>14.6f} "
            f"{m['total_kwh_per_1m_req']:>12.4f} {m['swdm_v4_total_j_per_req']:>14.6f}"
        )


def main():
    """Main entry point."""
    print("📊 Total Energy per Request Visualization Tool")
    print(f"📁 Benchmark root: {BENCHMARK_DIR}\n")

    server, server_requests_avg = collect_server_energy_per_request()
    client_cpu, client_network, client_cpu_ms, transfer_bytes, client_1k_std, sample_count = collect_client_energy_per_request()

    combined = combine_metrics(
        server,
        server_requests_avg,
        client_cpu,
        client_network,
        client_cpu_ms,
        transfer_bytes,
        client_1k_std,
        sample_count,
    )

    if not combined:
        print("❌ No data available. Ensure product and sitespeed benchmark results exist.")
        return

    print_summary(combined)
    print("\n📈 Creating figures...\n")
    create_report_figure(combined)
    create_heatmap(combined)
    print("\n✓ Done")


if __name__ == "__main__":
    main()
