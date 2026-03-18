# ══════════════════════════════════════════════════════════
#  Benchmark: JS Framework Vergleich via docker stats
#  Misst CPU%, Memory, Network pro Container isoliert
#  Mehrere Durchlaeufe + Median fuer zuverlaessige Werte
# ══════════════════════════════════════════════════════════

$duration = 60          # Sekunden pro Lasttest
$connections = 200      # Gleichzeitige Verbindungen (hoch fuer mehr Last)
$pause = 30             # Pause zwischen Durchlaeufen
$runs = 3               # Durchlaeufe pro Framework
$maxRetries = 30        # Max Wartezyklen auf Server
$retryInterval = 3      # Sekunden zwischen Retries

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsDir = "results/$timestamp"
New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null

# ══════════════════════════════════════
#  Hilfsfunktionen
# ══════════════════════════════════════

function Wait-ForServer {
    param($name, $url)
    Write-Host "  Warte auf $name ($url)..."
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop | Out-Null
            Write-Host "  -> $name erreichbar!" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "  Versuch $i/$maxRetries..." -ForegroundColor Yellow
            Start-Sleep -Seconds $retryInterval
        }
    }
    Write-Host "  -> FEHLER: $name nicht erreichbar!" -ForegroundColor Red
    return $false
}

function Get-ContainerStats {
    param($containerName)
    $raw = docker stats $containerName --no-stream --format "{{.CPUPerc}};{{.MemUsage}};{{.NetIO}};{{.PIDs}}" 2>$null
    if (-not $raw) { return $null }

    $parts = $raw.Split(";")
    $cpuPercent = [double]($parts[0].Trim() -replace '%', '')

    # Memory parsen: "123.4MiB / 7.77GiB"
    $memRaw = $parts[1].Trim().Split("/")[0].Trim()
    $memMiB = 0
    if ($memRaw -match '([\d.]+)\s*GiB') { $memMiB = [double]$Matches[1] * 1024 }
    elseif ($memRaw -match '([\d.]+)\s*MiB') { $memMiB = [double]$Matches[1] }
    elseif ($memRaw -match '([\d.]+)\s*KiB') { $memMiB = [double]$Matches[1] / 1024 }

    # Network parsen: "1.23kB / 4.56kB"
    $netParts = $parts[2].Trim().Split("/")

    return @{
        timestamp  = (Get-Date).ToString("o")
        cpuPercent = $cpuPercent
        memoryMiB  = [math]::Round($memMiB, 2)
        memoryRaw  = $memRaw
        netRx      = $netParts[0].Trim()
        netTx      = $netParts[1].Trim()
        pids       = [int]($parts[3].Trim())
    }
}

function Get-Median {
    param([double[]]$values)
    if ($values.Count -eq 0) { return 0 }
    $sorted = $values | Sort-Object
    $count = $sorted.Count
    if ($count % 2 -eq 0) {
        return ($sorted[$count / 2 - 1] + $sorted[$count / 2]) / 2
    } else {
        return $sorted[[math]::Floor($count / 2)]
    }
}

function Get-StdDev {
    param([double[]]$values)
    if ($values.Count -le 1) { return 0 }
    $avg = ($values | Measure-Object -Average).Average
    $sqDiffs = $values | ForEach-Object { ($_ - $avg) * ($_ - $avg) }
    return [math]::Sqrt(($sqDiffs | Measure-Object -Sum).Sum / ($values.Count - 1))
}

# ══════════════════════════════════════
#  Einzelner Testdurchlauf
# ══════════════════════════════════════

function Run-SingleTest {
    param($name, $containerName, $url, $runNumber, $runDir)

    New-Item -ItemType Directory -Force -Path $runDir | Out-Null

    Write-Host "    Run $runNumber : " -NoNewline

    # ── Idle messen (10s, keine Last) ──
    Write-Host "idle " -NoNewline -ForegroundColor Yellow
    $idleSamples = @()
    for ($i = 0; $i -lt 10; $i++) {
        $stat = Get-ContainerStats $containerName
        if ($stat) { $idleSamples += $stat }
        Start-Sleep -Seconds 1
    }
    $idleSamples | ConvertTo-Json -Depth 5 | Out-File "$runDir/idle_stats.json" -Encoding utf8

    $idleCpuMedian = Get-Median ($idleSamples | ForEach-Object { $_.cpuPercent })
    $idleMemMedian = Get-Median ($idleSamples | ForEach-Object { $_.memoryMiB })

    # ── docker stats Sammler im Hintergrund starten ──
    $absRunDir = (Resolve-Path $runDir).Path
    $statsFile = Join-Path $absRunDir "load_stats.csv"
    "timestamp,cpu_percent,memory_mib" | Out-File $statsFile -Encoding utf8

    # Start-Process statt Start-Job, damit docker im PATH ist
    $dockerPath = (Get-Command docker).Source
    $collectorScript = Join-Path $absRunDir "_collector.ps1"
    @"
`$end = (Get-Date).AddSeconds($($duration + 5))
while ((Get-Date) -lt `$end) {
    `$raw = & "$dockerPath" stats $containerName --no-stream --format "{{.CPUPerc}};{{.MemUsage}}" 2>`$null
    if (`$raw) {
        `$parts = `$raw.Split(";")
        `$cpu = [double](`$parts[0].Trim() -replace '%', '')
        `$memRaw = `$parts[1].Trim().Split("/")[0].Trim()
        `$mem = 0
        if (`$memRaw -match '([\d.]+)\s*GiB') { `$mem = [double]`$Matches[1] * 1024 }
        elseif (`$memRaw -match '([\d.]+)\s*MiB') { `$mem = [double]`$Matches[1] }
        elseif (`$memRaw -match '([\d.]+)\s*KiB') { `$mem = [double]`$Matches[1] / 1024 }
        `$ts = (Get-Date).ToString("o")
        "`$ts,`$cpu,`$([math]::Round(`$mem,2))" | Out-File "$statsFile" -Append -Encoding utf8
    }
    Start-Sleep -Seconds 1
}
"@ | Out-File $collectorScript -Encoding utf8

    $statsProc = Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$collectorScript`"" -WindowStyle Hidden -PassThru

    # ── Lasttest ──
    Write-Host "load " -NoNewline -ForegroundColor Cyan
    $startTime = Get-Date

    # Haupttest auf /products (DB-Query, erzeugt genuegend Last)
    $autocannonOutput = & npx autocannon -c $connections -d $duration -j "$url/products" 2>$null
    $autocannonOutput | Out-File "$runDir/autocannon.json" -Encoding utf8

    $endTime = Get-Date

    # ── Stats-Sammler beenden ──
    if ($statsProc -and !$statsProc.HasExited) {
        $statsProc | Wait-Process -Timeout ($duration + 20) -ErrorAction SilentlyContinue
        $statsProc | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $collectorScript -Force -ErrorAction SilentlyContinue

    # ── Load-Stats auswerten ──
    $loadCpuValues = @()
    $loadMemValues = @()
    if (Test-Path $statsFile) {
        $csvData = Import-Csv $statsFile
        $loadCpuValues = $csvData | ForEach-Object { [double]$_.cpu_percent }
        $loadMemValues = $csvData | ForEach-Object { [double]$_.memory_mib }
    }

    $loadCpuMedian = Get-Median $loadCpuValues
    $loadMemMedian = Get-Median $loadMemValues

    # ── Autocannon auswerten ──
    $reqPerSec = 0; $latencyAvg = 0; $totalRequests = 0; $throughput = 0; $errors = 0
    try {
        $ac = $autocannonOutput | ConvertFrom-Json
        if ($ac.requests) {
            $reqPerSec = $ac.requests.average
            $totalRequests = $ac.requests.total
        }
        if ($ac.latency) { $latencyAvg = $ac.latency.average }
        if ($ac.throughput) { $throughput = $ac.throughput.average }
        if ($ac.errors) { $errors = $ac.errors }
    } catch {}

    # ── Ergebnis zusammenstellen ──
    $result = @{
        run       = $runNumber
        startTime = $startTime.ToString("o")
        endTime   = $endTime.ToString("o")
        idle      = @{
            cpuPercent = [math]::Round($idleCpuMedian, 2)
            memoryMiB  = [math]::Round($idleMemMedian, 2)
        }
        load      = @{
            cpuPercent = [math]::Round($loadCpuMedian, 2)
            memoryMiB  = [math]::Round($loadMemMedian, 2)
            samples    = $loadCpuValues.Count
        }
        diff      = @{
            cpuPercent = [math]::Round($loadCpuMedian - $idleCpuMedian, 2)
            memoryMiB  = [math]::Round($loadMemMedian - $idleMemMedian, 2)
        }
        performance = @{
            reqPerSec     = [math]::Round($reqPerSec, 1)
            latencyAvgMs  = [math]::Round($latencyAvg, 2)
            totalRequests = $totalRequests
            throughputBps = $throughput
            errors        = $errors
        }
    }
    $result | ConvertTo-Json -Depth 5 | Out-File "$runDir/result.json" -Encoding utf8

    Write-Host "-> CPU: $($result.load.cpuPercent)% (+$($result.diff.cpuPercent)%) | Mem: $($result.load.memoryMiB)MiB | $($result.performance.reqPerSec) req/s | $($result.performance.latencyAvgMs)ms" -ForegroundColor Green

    return $result
}

# ══════════════════════════════════════
#  Framework-Test (mehrere Durchlaeufe)
# ══════════════════════════════════════

function Run-FrameworkTest {
    param($name, $composeFile, $url, $containerName)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Framework: $name ($runs Durchlaeufe)" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan

    $fwDir = "$resultsDir/$name"
    New-Item -ItemType Directory -Force -Path $fwDir | Out-Null

    # Container starten
    docker compose -f $composeFile down -v 2>$null
    Write-Host "  Container bauen und starten..."
    docker compose -f $composeFile up --build -d

    # Warten auf Server
    $reachable = Wait-ForServer $name $url
    if (-not $reachable) {
        Write-Host "  SKIP: $name nicht erreichbar" -ForegroundColor Red
        docker compose -f $composeFile logs $containerName
        docker compose -f $composeFile down
        return
    }

    # Aufwaermphase: 1 kurzer Request damit JIT/Caches warm sind
    Write-Host "  Aufwaermphase (5s)..."
    try { Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 | Out-Null } catch {}
    Start-Sleep -Seconds 5

    # Mehrere Durchlaeufe
    $allResults = @()
    for ($run = 1; $run -le $runs; $run++) {
        $runDir = "$fwDir/run_$run"
        $result = Run-SingleTest $name $containerName $url $run $runDir
        $allResults += $result

        if ($run -lt $runs) {
            Write-Host "    Pause ${pause}s..." -ForegroundColor Yellow
            Start-Sleep -Seconds $pause
        }
    }

    # ── Statistische Auswertung ──
    $cpuVals = $allResults | ForEach-Object { $_.load.cpuPercent }
    $memVals = $allResults | ForEach-Object { $_.load.memoryMiB }
    $rpsVals = $allResults | ForEach-Object { $_.performance.reqPerSec }
    $latVals = $allResults | ForEach-Object { $_.performance.latencyAvgMs }
    $diffCpuVals = $allResults | ForEach-Object { $_.diff.cpuPercent }

    $summary = @{
        framework   = $name
        runs        = $runs
        connections  = $connections
        durationSec = $duration
        cpu         = @{
            medianPercent = [math]::Round((Get-Median $cpuVals), 2)
            avgPercent    = [math]::Round(($cpuVals | Measure-Object -Average).Average, 2)
            minPercent    = [math]::Round(($cpuVals | Measure-Object -Minimum).Minimum, 2)
            maxPercent    = [math]::Round(($cpuVals | Measure-Object -Maximum).Maximum, 2)
            stddev        = [math]::Round((Get-StdDev $cpuVals), 3)
            values        = $cpuVals | ForEach-Object { [math]::Round($_, 2) }
        }
        cpuDiff     = @{
            medianPercent = [math]::Round((Get-Median $diffCpuVals), 2)
            values        = $diffCpuVals | ForEach-Object { [math]::Round($_, 2) }
        }
        memory      = @{
            medianMiB = [math]::Round((Get-Median $memVals), 2)
            avgMiB    = [math]::Round(($memVals | Measure-Object -Average).Average, 2)
            minMiB    = [math]::Round(($memVals | Measure-Object -Minimum).Minimum, 2)
            maxMiB    = [math]::Round(($memVals | Measure-Object -Maximum).Maximum, 2)
        }
        performance = @{
            medianRps     = [math]::Round((Get-Median $rpsVals), 1)
            avgRps        = [math]::Round(($rpsVals | Measure-Object -Average).Average, 1)
            medianLatency = [math]::Round((Get-Median $latVals), 2)
            avgLatency    = [math]::Round(($latVals | Measure-Object -Average).Average, 2)
        }
    }
    $summary | ConvertTo-Json -Depth 5 | Out-File "$fwDir/summary.json" -Encoding utf8

    Write-Host ""
    Write-Host "  ── $name Zusammenfassung ──" -ForegroundColor Cyan
    Write-Host "    CPU (Median):      $($summary.cpu.medianPercent)% (StdDev: $($summary.cpu.stddev)%)" -ForegroundColor Green
    Write-Host "    Memory (Median):   $($summary.memory.medianMiB) MiB" -ForegroundColor Green
    Write-Host "    Req/s (Median):    $($summary.performance.medianRps)" -ForegroundColor Green
    Write-Host "    Latency (Median):  $($summary.performance.medianLatency) ms" -ForegroundColor Green

    # Container stoppen
    docker compose -f $composeFile down

    Write-Host "  Pause ${pause}s (System beruhigen)..." -ForegroundColor Yellow
    Start-Sleep -Seconds $pause
}

# ══════════════════════════════════════
#  Hauptprogramm
# ══════════════════════════════════════

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Benchmark: Framework Vergleich" -ForegroundColor Green
Write-Host "  Methode: docker stats pro Container" -ForegroundColor Yellow
Write-Host "  $runs Durchlaeufe, ${duration}s Last" -ForegroundColor Yellow
Write-Host "  $connections Verbindungen" -ForegroundColor Yellow
Write-Host "  Ergebnisse: $resultsDir" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# System-Info speichern
@{
    timestamp   = (Get-Date).ToString("o")
    hostname    = $env:COMPUTERNAME
    cpu         = (Get-WmiObject Win32_Processor).Name
    cores       = (Get-WmiObject Win32_Processor).NumberOfLogicalProcessors
    ram         = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
    os          = (Get-WmiObject Win32_OperatingSystem).Caption
    docker      = (docker version --format "{{.Server.Version}}" 2>$null)
    node        = (node --version 2>$null)
    config      = @{
        runs        = $runs
        duration    = $duration
        connections = $connections
        pause       = $pause
    }
} | ConvertTo-Json -Depth 3 | Out-File "$resultsDir/system_info.json" -Encoding utf8

# Tests ausfuehren
Run-FrameworkTest "astro"  "docker-compose.astro.yml"  "http://localhost:4321" "astro-server"
Run-FrameworkTest "next"   "docker-compose.next.yml"   "http://localhost:3000" "next-server"
Run-FrameworkTest "svelte" "docker-compose.svelte.yml" "http://localhost:5173" "svelte-server"

# ══════════════════════════════════════
#  Gesamtergebnis
# ══════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  GESAMTERGEBNIS" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host ("  {0,-10} | {1,12} | {2,12} | {3,10} | {4,10}" -f "Framework", "CPU (Med.)", "Memory", "Req/s", "Latency") -ForegroundColor White
Write-Host ("  {0,-10} | {1,12} | {2,12} | {3,10} | {4,10}" -f "----------", "------------", "------------", "----------", "----------") -ForegroundColor White

$allSummaries = @()
foreach ($fw in @("astro", "next", "svelte")) {
    $file = "$resultsDir/$fw/summary.json"
    if (Test-Path $file) {
        $d = Get-Content $file | ConvertFrom-Json
        $allSummaries += $d
        $line = "  {0,-10} | {1,10}%  | {2,8} MiB  | {3,7} r/s | {4,7} ms" -f `
            $fw, $d.cpu.medianPercent, $d.memory.medianMiB, $d.performance.medianRps, $d.performance.medianLatency
        Write-Host $line -ForegroundColor Green
    } else {
        Write-Host ("  {0,-10} | Keine Daten" -f $fw) -ForegroundColor Red
    }
}

$allSummaries | ConvertTo-Json -Depth 5 | Out-File "$resultsDir/final_results.json" -Encoding utf8

Write-Host ""
Write-Host "  Ergebnisse gespeichert in: $resultsDir/" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
