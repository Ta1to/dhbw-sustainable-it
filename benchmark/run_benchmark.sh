#!/bin/bash

DURATION=60
CONNECTIONS=50
PAUSE=30

mkdir -p results

run_test() {
    local name=$1
    local compose_file=$2
    local url=$3

    echo "========================================"
    echo "  Test: $name"
    echo "========================================"

    # Alte Container stoppen
    docker compose -f $compose_file down -v

    # Nur diesen Server starten
    docker compose -f $compose_file up --build -d

    # Warten bis Server bereit ist
    echo "Warte 15s auf Server-Start..."
    sleep 15

    # Scaphandre Pushgateway leeren
    curl -s -X PUT http://localhost:9091/api/v1/admin/wipe

    echo "Start: $(date)"
    
    # Lasttest
    npx autocannon -c $CONNECTIONS -d $DURATION -j $url > results/${name}.json

    echo "Ende: $(date)"

    # Prometheus Snapshot der Metriken
    curl -s "http://localhost:9090/api/v1/query?query=scaph_host_power_microwatts" > results/${name}_power.json
    curl -s "http://localhost:9090/api/v1/query?query=scaph_process_power_consumption_microwatts" >> results/${name}_power.json

    # Container stoppen
    docker compose -f $compose_file down

    echo "Pause ${PAUSE}s..."
    sleep $PAUSE
}

# Tests einzeln ausführen
run_test "astro"   "docker-compose.astro.yml"   "http://localhost:4321"
run_test "next"    "docker-compose.next.yml"    "http://localhost:3000"
run_test "svelte"  "docker-compose.svelte.yml"  "http://localhost:5173"

echo "========================================"
echo "  Alle Tests abgeschlossen!"
echo "  Ergebnisse in benchmark/results/"
echo "========================================"