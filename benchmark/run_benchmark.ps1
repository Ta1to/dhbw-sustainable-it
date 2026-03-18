# ══════════════════════════════════════════════════════════
#  Benchmark: JS Framework Energieverbrauch mit Scaphandre
#  Scaphandre laeuft als Windows-Service (prometheus-push)
#  Muss als Administrator ausgefuehrt werden!
# ══════════════════════════════════════════════════════════

$duration = 60
$connections = 50
$pause = 30
$maxRetries = 30
$retryInterval = 3

New-Item -ItemType Directory -Force -Path results | Out-Null

function Wait-ForServer {
    param($name, $url)

    Write-Host "  Warte auf $name ($url)..."
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
            Write-Host "  -> $name erreichbar! (Status: $($response.StatusCode))" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "  Versuch $i/$maxRetries..." -ForegroundColor Yellow
            Start-Sleep -Seconds $retryInterval
        }
    }
    Write-Host "  -> $name NICHT erreichbar nach $maxRetries Versuchen!" -ForegroundColor Red
    return $false
}

function Run-Test {
    param($name, $composeFile, $url)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Test: $name" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # Alte Container stoppen
    docker compose -f $composeFile down -v 2>$null

    # Container starten (Pushgateway + Prometheus + Grafana + Server)
    Write-Host "  Container starten..."
    docker compose -f $composeFile up --build -d

    # Warten bis Server erreichbar ist
    $serverReady = Wait-ForServer $name $url
    if (-not $serverReady) {
        Write-Host "  FEHLER: $name nicht erreichbar. Logs:" -ForegroundColor Red
        docker compose -f $composeFile logs
        docker compose -f $composeFile down
        return
    }

    # Warten bis Pushgateway erreichbar ist
    Wait-ForServer "Pushgateway" "http://localhost:9091/metrics" | Out-Null

    # Scaphandre Windows-Service starten
    Write-Host "  Scaphandre Service starten..."
    sc.exe start Scaphandre 2>$null
    Start-Sleep -Seconds 5

    # Pruefen ob Scaphandre Metriken pusht
    try {
        $pgMetrics = (Invoke-WebRequest -Uri "http://localhost:9091/metrics" -UseBasicParsing).Content
        if ($pgMetrics -match "scaph") {
            Write-Host "  -> Scaphandre Metriken vorhanden!" -ForegroundColor Green
        } else {
            Write-Host "  -> Warnung: Keine scaph-Metriken im Pushgateway" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  -> Warnung: Pushgateway nicht erreichbar" -ForegroundColor Yellow
    }

    # Lasttest starten
    Write-Host ""
    Write-Host "  Lasttest: $connections Verbindungen, ${duration}s" -ForegroundColor White
    Write-Host "  Start: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor White

    & npx autocannon -c $connections -d $duration -j $url | Out-File "results/$name.json" -Encoding utf8
    & npx autocannon -c $connections -d $duration $url

    Write-Host "  Ende: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor White

    # Metriken aus Prometheus speichern
    Write-Host "  Metriken speichern..."
    try {
        # Alle verfuegbaren Metrik-Namen holen
        $labels = Invoke-RestMethod "http://localhost:9090/api/v1/label/__name__/values"
        $scaphMetrics = $labels.data | Where-Object { $_ -like "scaph*" }

        if ($scaphMetrics.Count -gt 0) {
            Write-Host "  -> Scaphandre Metriken: $($scaphMetrics -join ', ')" -ForegroundColor Green

            # Aktuelle Werte speichern
            $power = Invoke-RestMethod "http://localhost:9090/api/v1/query?query=scaph_host_power_microwatts"
            $power | ConvertTo-Json -Depth 10 | Out-File "results/${name}_power.json" -Encoding utf8

            $processPower = Invoke-RestMethod "http://localhost:9090/api/v1/query?query=scaph_process_power_consumption_microwatts"
            $processPower | ConvertTo-Json -Depth 10 | Out-File "results/${name}_process_power.json" -Encoding utf8

            # Zeitreihe der letzten 2 Minuten
            $end = [DateTimeOffset]::Now.ToUnixTimeSeconds()
            $start = $end - 120
            $range = Invoke-RestMethod "http://localhost:9090/api/v1/query_range?query=scaph_host_power_microwatts&start=$start&end=$end&step=5"
            $range | ConvertTo-Json -Depth 10 | Out-File "results/${name}_power_range.json" -Encoding utf8
        } else {
            Write-Host "  -> Keine scaph-Metriken gefunden" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  -> Warnung: Metriken konnten nicht gespeichert werden: $_" -ForegroundColor Yellow
    }

    # Scaphandre stoppen
    Write-Host "  Scaphandre Service stoppen..."
    sc.exe stop Scaphandre 2>$null

    # Container stoppen
    docker compose -f $composeFile down

    Write-Host "  Pause ${pause}s..." -ForegroundColor Yellow
    Start-Sleep -Seconds $pause
}

# ── Tests einzeln ausfuehren ──
Run-Test "astro"  "docker-compose.astro.yml"  "http://localhost:4321"
Run-Test "next"   "docker-compose.next.yml"   "http://localhost:3000"
Run-Test "svelte" "docker-compose.svelte.yml" "http://localhost:5173"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Alle Tests abgeschlossen!" -ForegroundColor Green
Write-Host "  Ergebnisse in benchmark/results/" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan