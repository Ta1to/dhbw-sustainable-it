#!/bin/bash
# ══════════════════════════════════════════════════════════
#  Benchmark: JS Framework Client-Side Performance
#  Target: Samsung Book3 (Live USB)
#  Method: sitespeed.io (11 iterations, Cold Start)
# ══════════════════════════════════════════════════════════

PAUSE=30
MAX_RETRIES=30
RETRY_INTERVAL=3

# Create timestamped results directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/sitespeed_bench_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

wait_for_server() {
    local name=$1
    local url=$2
    echo "  Waiting for $name ($url)..."
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -qE "200|301|302|304"; then
            return 0
        fi
        sleep $RETRY_INTERVAL
    done
    return 1
}

run_sitespeed_test() {
    local name=$1           
    local compose_file=$2    
    local url=$3            

    echo -e "\n========================================"
    echo "  Running Sitespeed.io: $name"
    echo "========================================"

    # 1. Start Environment (Clean build)
    docker compose -f "$compose_file" down -v 2>/dev/null
    docker compose -f "$compose_file" up --build -d

    # 2. Health Check
    if ! wait_for_server "$name" "$url"; then
        echo "  ERROR: $name unreachable."
        return
    fi

    # 3. Execute Sitespeed.io Command
    # This measures Hydration, TBT, and Page Load over 11 runs
    sitespeed.io "$url" \
        -b chrome \
        --browsertime.chrome.binaryPath /snap/bin/chromium \
        --browsertime.chrome.args no-sandbox \
        --browsertime.chrome.timeline true \
        --browsertime.headless true \
        -n 20 \
        --browsertime.cacheClearRaw true \
        --browsertime.connectivity.profile native \
        --browsertime.cpuThrottleRate 2 \
        --sustainable.enable true \
        --video false \
        --screenshot false \
        --outputFolder "$RESULTS_DIR/${name}"

    # 4. Cleanup
    docker compose -f "$compose_file" down

    echo "  Cooling down (${PAUSE}s)..."
    sleep $PAUSE
}

# Run the suite on the /products route
run_sitespeed_test "astro"   "docker-compose.astro.yml"   "http://localhost:4321/products"
run_sitespeed_test "next"    "docker-compose.next.yml"    "http://localhost:3000/products"
run_sitespeed_test "svelte"  "docker-compose.svelte.yml"  "http://localhost:5173/products"

echo -e "\n Sitespeed benchmarks complete. Check $RESULTS_DIR for HTML reports."