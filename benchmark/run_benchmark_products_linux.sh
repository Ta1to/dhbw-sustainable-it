#!/bin/bash
# ══════════════════════════════════════════════════════════
#  Benchmark: JS Framework Energy (PID-Specific)
#  Target: Samsung Book3 (Live USB)
#  Method: Capturing Container Host PID for Prometheus Filtering
# ══════════════════════════════════════════════════════════

DURATION=60
CONNECTIONS=50
PAUSE=30
MAX_RETRIES=30
RETRY_INTERVAL=3
PROMETHEUS_URL="http://localhost:9090"

# Create timestamped results directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/products/${TIMESTAMP}"
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

run_test() {
    local name=$1           # e.g., "svelte"
    local compose_file=$2    # e.g., "docker-compose.svelte.yml"
    local url=$3            # e.g., "http://localhost:5173"
    local container_name="${name}-server" # Adjust if your container name is different

    echo -e "\n========================================"
    echo "  Testing: $name"
    echo "========================================"

    # 1. Start Environment
    docker compose -f "$compose_file" down -v 2>/dev/null
    docker compose -f "$compose_file" up --build -d

    # 2. Health Check
    if ! wait_for_server "$name" "$url"; then
        echo "  ERROR: $name unreachable."
        return
    fi

    sudo systemctl start scaphandre.service
    sleep 5 

    echo "  Running Load Test for ${DURATION}s..."
    START_TIME=$(date +%s)
    
    autocannon -c $CONNECTIONS -d $DURATION -j "$url" > "$RESULTS_DIR/${name}_perf.json"
    
    END_TIME=$(date +%s)
    echo "  Test Finished at $END_TIME"

    echo "  Waiting for Prometheus to scrape data for 30s ..."
    sleep 30

    echo "  Querying Prometheus for container_name: $container_name..."
    
    curl -s -G "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=avg_over_time(scaph_process_power_consumption_microwatts{container_names='$container_name'}[${DURATION}s] @ ${END_TIME}) / 1000000" \
        > "$RESULTS_DIR/${container_name}_watts.json"

    # 7. Cleanup
    sudo systemctl stop scaphandre.service
    docker compose -f "$compose_file" down

    echo "  Cooling down (${PAUSE}s)..."
    sleep $PAUSE
}

# Run the suite
run_test "astro"   "docker-compose.astro.yml"   "http://localhost:4321/products"
run_test "next"    "docker-compose.next.yml"    "http://localhost:3000/products"
run_test "svelte"  "docker-compose.svelte.yml"  "http://localhost:5173/products"