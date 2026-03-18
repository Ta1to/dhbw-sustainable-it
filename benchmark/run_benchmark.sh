#!/bin/bash
# ══════════════════════════════════════════════════════════
#  Benchmark: JS Framework Energieverbrauch mit Scaphandre
#  Scaphandre laeuft als Windows-Service (prometheus-push)
#  PowerShell-Version: run_benchmark.ps1
# ══════════════════════════════════════════════════════════

DURATION=60
CONNECTIONS=50
PAUSE=30
MAX_RETRIES=30
RETRY_INTERVAL=3

mkdir -p results

wait_for_server() {
    local name=$1
    local url=$2

    echo "  Warte auf $name ($url)..."
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -qE "200|301|302|304"; then
            echo "  -> $name erreichbar!"
            return 0
        fi
        echo "  Versuch $i/$MAX_RETRIES..."
        sleep $RETRY_INTERVAL
    done
    echo "  -> FEHLER: $name nicht erreichbar!"
    return 1
}

run_test() {
    local name=$1
    local compose_file=$2
    local url=$3

    echo ""
    echo "========================================"
    echo "  Test: $name"
    echo "========================================"

    # Alte Container stoppen
    docker compose -f $compose_file down -v 2>/dev/null

    # Container starten
    echo "  Container starten..."
    docker compose -f $compose_file up --build -d

    # Warten bis Server erreichbar
    if ! wait_for_server "$name" "$url"; then
        echo "  FEHLER: $name nicht erreichbar. Logs:"
        docker compose -f $compose_file logs
        docker compose -f $compose_file down
        return
    fi

    # Warten bis Pushgateway erreichbar
    wait_for_server "Pushgateway" "http://localhost:9091/metrics"

    # Scaphandre Windows-Service starten
    echo "  Scaphandre Service starten..."
    sc.exe start Scaphandre 2>/dev/null || true
    sleep 5

    # Lasttest
    echo ""
    echo "  Lasttest: $CONNECTIONS Verbindungen, ${DURATION}s"
    echo "  Start: $(date +%H:%M:%S)"

    npx autocannon -c $CONNECTIONS -d $DURATION -j $url > results/${name}.json
    npx autocannon -c $CONNECTIONS -d $DURATION $url

    echo "  Ende: $(date +%H:%M:%S)"

    # Metriken speichern
    echo "  Metriken speichern..."
    curl -s "http://localhost:9090/api/v1/query?query=scaph_host_power_microwatts" > results/${name}_power.json
    curl -s "http://localhost:9090/api/v1/query?query=scaph_process_power_consumption_microwatts" > results/${name}_process_power.json

    # Scaphandre stoppen
    echo "  Scaphandre Service stoppen..."
    sc.exe stop Scaphandre 2>/dev/null || true

    # Container stoppen
    docker compose -f $compose_file down

    echo "  Pause ${PAUSE}s..."
    sleep $PAUSE
}

# Tests einzeln ausfuehren
run_test "astro"   "docker-compose.astro.yml"   "http://localhost:4321"
run_test "next"    "docker-compose.next.yml"    "http://localhost:3000"
run_test "svelte"  "docker-compose.svelte.yml"  "http://localhost:5173"

echo ""
echo "========================================"
echo "  Alle Tests abgeschlossen!"
echo "  Ergebnisse in benchmark/results/"
echo "========================================"