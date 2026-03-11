#!/bin/bash

# autocannon installieren falls nicht vorhanden
npm install -g autocannon

DURATION=60       # Sekunden pro Test
CONNECTIONS=50    # gleichzeitige Verbindungen
WARM_UP=10        # Aufwärmphase

echo "========================================"
echo "  Benchmark: JS Framework Energieverbrauch"
echo "========================================"

echo ""
echo "--- Aufwärmphase ---"
sleep $WARM_UP

echo ""
echo "=== [1/3] Astro Server (Port 4321) ==="
echo "Start: $(date)"
autocannon -c $CONNECTIONS -d $DURATION -j http://localhost:4321 > results/astro.json
echo "Ende: $(date)"

echo ""
echo "--- Pause 30s ---"
sleep 30

echo ""
echo "=== [2/3] Next Server (Port 3000) ==="
echo "Start: $(date)"
autocannon -c $CONNECTIONS -d $DURATION -j http://localhost:3000 > results/next.json
echo "Ende: $(date)"

echo ""
echo "--- Pause 30s ---"
sleep 30

echo ""
echo "=== [3/3] Svelte Server (Port 5173) ==="
echo "Start: $(date)"
autocannon -c $CONNECTIONS -d $DURATION -j http://localhost:5173 > results/svelte.json
echo "Ende: $(date)"

echo ""
echo "========================================"
echo "  Fertig! Ergebnisse in results/"
echo "========================================"