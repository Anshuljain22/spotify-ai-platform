$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Spotify Intelligence Platform" -ForegroundColor Cyan
Write-Host " Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# ----------------------------------------
# Environment
# ----------------------------------------

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found." -ForegroundColor Red
    exit 1
}

& ".venv\Scripts\Activate.ps1"

Write-Host "[OK] Virtual environment activated." -ForegroundColor Green

try {
    docker version | Out-Null
}
catch {
    Write-Host "ERROR: Docker is not available." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Docker is available." -ForegroundColor Green

# ----------------------------------------
# Kafka
# ----------------------------------------

$kafka = docker ps --filter "name=github-de-kafka" --format "{{.Names}}"

if ($kafka -eq "github-de-kafka") {
    Write-Host "[OK] Existing Kafka container is already running." -ForegroundColor Green
}
else {
    $kafkaExists = docker ps -a --filter "name=github-de-kafka" --format "{{.Names}}"

    if ($kafkaExists -eq "github-de-kafka") {
        Write-Host "[START] Starting existing Kafka container..." -ForegroundColor Yellow
        docker start github-de-kafka | Out-Null
    }
    else {
        Write-Host "ERROR: github-de-kafka was not found." -ForegroundColor Red
        Write-Host "The startup script will not create a second Kafka instance." -ForegroundColor Yellow
        exit 1
    }
}

# ----------------------------------------
# Spotify Batch Pipeline
# ----------------------------------------

Write-Host ""
Write-Host "[BATCH] Running Spotify batch pipeline..." -ForegroundColor Cyan

python -m src.pipeline

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Spotify batch pipeline failed." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Spotify batch pipeline completed." -ForegroundColor Green

# ----------------------------------------
# Spotify Live Poller
# ----------------------------------------

Write-Host ""
Write-Host "[STREAM] Starting Spotify live poller..." -ForegroundColor Cyan

$pollerProcess = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -like "*src.streaming.spotify_live*"
    }

if ($pollerProcess) {
    Write-Host "[OK] Spotify live poller is already running." -ForegroundColor Green
}
else {
    Start-Process powershell `
        -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; & '$PSScriptRoot\.venv\Scripts\python.exe' -m src.streaming.spotify_live" `
        -WindowStyle Normal

    Write-Host "[START] Spotify live poller started." -ForegroundColor Green
}

# ----------------------------------------
# Spark Streaming → Iceberg
# ----------------------------------------

Write-Host ""
Write-Host "[SPARK] Starting Spark → Iceberg streaming..." -ForegroundColor Cyan

$sparkProcess = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -like "*src.streaming.spark_to_iceberg*"
    }

if ($sparkProcess) {
    Write-Host "[OK] Spark streaming is already running." -ForegroundColor Green
}
else {
    Start-Process powershell `
        -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; `$env:PYSPARK_PYTHON='$PSScriptRoot\.venv\Scripts\python.exe'; `$env:PYSPARK_DRIVER_PYTHON='$PSScriptRoot\.venv\Scripts\python.exe'; `$env:HADOOP_HOME='C:\hadoop'; `$env:PATH='C:\hadoop\bin;' + `$env:PATH; & '$PSScriptRoot\.venv\Scripts\python.exe' -m src.streaming.spark_to_iceberg" `
        -WindowStyle Normal

    Write-Host "[START] Spark streaming started." -ForegroundColor Green
}

Write-Host ""
Write-Host "Startup stages completed successfully." -ForegroundColor Green
Write-Host ""