$duration = 60
$connections = 50
$pause = 30

New-Item -ItemType Directory -Force -Path results | Out-Null

function Run-Test {
    param($name, $composeFile, $url)

    Write-Host "========================================"
    Write-Host "  Test: $name"
    Write-Host "========================================"

    docker compose -f $composeFile down -v
    docker compose -f $composeFile up --build -d

    Write-Host "Warte 15s auf Server-Start..."
    Start-Sleep -Seconds 15

    Write-Host "Start: $(Get-Date)"

    # Lasttest mit autocannon
    & npx autocannon -c $connections -d $duration -j $url | Out-File "results/$name.json"

    Write-Host "Ende: $(Get-Date)"

    # Metriken speichern
    try {
        $power = Invoke-RestMethod "http://localhost:9090/api/v1/query?query=scaph_host_power_microwatts"
        $power | ConvertTo-Json -Depth 10 | Out-File "results/${name}_power.json"
        
        $process_power = Invoke-RestMethod "http://localhost:9090/api/v1/query?query=scaph_process_power_consumption_microwatts"
        $process_power | ConvertTo-Json -Depth 10 | Out-File "results/${name}_process_power.json"
    } catch {
        Write-Host "Warnung: Metriken konnten nicht gespeichert werden"
    }

    docker compose -f $composeFile down

    Write-Host "Pause ${pause}s..."
    Start-Sleep -Seconds $pause
}

Run-Test "astro"  "docker-compose.astro.yml"  "http://localhost:4321"
Run-Test "next"   "docker-compose.next.yml"   "http://localhost:3000"
Run-Test "svelte" "docker-compose.svelte.yml" "http://localhost:5173"

Write-Host "========================================"
Write-Host "  Alle Tests abgeschlossen!"
Write-Host "  Ergebnisse in benchmark/results/"
Write-Host "========================================"