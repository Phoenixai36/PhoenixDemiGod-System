# Test script for Podman compose configuration
param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"

Write-Host "Testing Podman compose configuration..." -ForegroundColor Green

# Check if podman-compose is available
try {
    $null = Get-Command podman-compose -ErrorAction Stop
    Write-Host "✓ podman-compose is available" -ForegroundColor Green
} catch {
    Write-Host "✗ podman-compose is not installed" -ForegroundColor Red
    Write-Host "Install with: pip install podman-compose" -ForegroundColor Yellow
    exit 1
}

# Validate compose file syntax
Write-Host "Validating compose file syntax..." -ForegroundColor Cyan
try {
    $configOutput = & podman-compose -f $ComposeFile config 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Compose file syntax is valid" -ForegroundColor Green
        if ($Verbose) {
            Write-Host "Configuration output:" -ForegroundColor Gray
            Write-Host $configOutput -ForegroundColor Gray
        }
    } else {
        throw "Validation failed"
    }
} catch {
    Write-Host "✗ Compose file syntax validation failed" -ForegroundColor Red
    Write-Host $configOutput -ForegroundColor Red
    exit 1
}

# Check if required directories exist
Write-Host "Checking required directories..." -ForegroundColor Cyan
$phoenixDataDir = Join-Path $env:USERPROFILE ".local\share\phoenix-hydra"
$dbDataDir = Join-Path $phoenixDataDir "db_data"

if (-not (Test-Path $phoenixDataDir)) {
    Write-Host "Creating Phoenix Hydra data directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dbDataDir -Force | Out-Null
    Write-Host "✓ Created data directories" -ForegroundColor Green
} else {
    Write-Host "✓ Phoenix Hydra data directory exists" -ForegroundColor Green
}

# Test network configuration
Write-Host "Testing network configuration..." -ForegroundColor Cyan
try {
    $networkExists = & podman network exists phoenix-net 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Phoenix network already exists" -ForegroundColor Green
    } else {
        Write-Host "ℹ Phoenix network will be created on first run" -ForegroundColor Blue
    }
} catch {
    Write-Host "ℹ Phoenix network will be created on first run" -ForegroundColor Blue
}

Write-Host ""
Write-Host "✓ All tests passed! Compose configuration is ready." -ForegroundColor Green
Write-Host ""
Write-Host "To start the services:" -ForegroundColor Cyan
Write-Host "  cd $ScriptDir" -ForegroundColor Gray
Write-Host "  podman-compose -f podman-compose.yaml up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "To check service status:" -ForegroundColor Cyan
Write-Host "  podman-compose -f podman-compose.yaml ps" -ForegroundColor Gray