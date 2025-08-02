# Validation script to check service definitions and Containerfiles
param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"

Write-Host "Validating Phoenix Hydra Podman services..." -ForegroundColor Green

# Parse compose file to get service definitions
try {
    $composeContent = Get-Content $ComposeFile -Raw
    Write-Host "✓ Compose file loaded successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to load compose file: $ComposeFile" -ForegroundColor Red
    exit 1
}

# Check required Containerfiles
$requiredContainerfiles = @(
    "gap-detector/Containerfile",
    "analysis-engine/Containerfile", 
    "recurrent-processor/Containerfile",
    "rubik-agent/Containerfile",
    "nginx/Containerfile"
)

Write-Host "Checking Containerfiles..." -ForegroundColor Cyan
foreach ($containerfile in $requiredContainerfiles) {
    $fullPath = Join-Path $ScriptDir $containerfile
    if (Test-Path $fullPath) {
        Write-Host "✓ $containerfile exists" -ForegroundColor Green
        
        # Basic validation of Containerfile content
        $content = Get-Content $fullPath -Raw
        if ($content -match "FROM\s+\w+") {
            Write-Host "  ✓ Valid FROM instruction found" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ No valid FROM instruction found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ $containerfile missing" -ForegroundColor Red
    }
}

# Check nginx configuration
$nginxConf = Join-Path $ScriptDir "nginx/nginx.conf"
if (Test-Path $nginxConf) {
    Write-Host "✓ nginx.conf exists" -ForegroundColor Green
} else {
    Write-Host "✗ nginx.conf missing" -ForegroundColor Red
}

# Validate compose syntax with podman-compose
Write-Host "Validating compose syntax..." -ForegroundColor Cyan
try {
    $configOutput = & podman-compose -f $ComposeFile config 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Compose syntax validation passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Compose syntax validation failed" -ForegroundColor Red
        Write-Host $configOutput -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Failed to validate compose syntax" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Check for required environment variables
Write-Host "Checking environment setup..." -ForegroundColor Cyan
$homeDir = $env:USERPROFILE
$phoenixDataDir = Join-Path $homeDir ".local\share\phoenix-hydra\db_data"

if (Test-Path $phoenixDataDir) {
    Write-Host "✓ Phoenix data directory exists: $phoenixDataDir" -ForegroundColor Green
} else {
    Write-Host "ℹ Phoenix data directory will be created: $phoenixDataDir" -ForegroundColor Blue
}

Write-Host ""
Write-Host "✓ Service validation completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Services configured:" -ForegroundColor Cyan
Write-Host "  - gap-detector (port 8000)" -ForegroundColor Gray
Write-Host "  - analysis-engine (port 5000)" -ForegroundColor Gray
Write-Host "  - recurrent-processor" -ForegroundColor Gray
Write-Host "  - rubik-agent" -ForegroundColor Gray
Write-Host "  - db (PostgreSQL)" -ForegroundColor Gray
Write-Host "  - windmill (port 3000)" -ForegroundColor Gray
Write-Host "  - nginx (port 8080)" -ForegroundColor Gray
Write-Host ""
Write-Host "Network: phoenix-net (172.20.0.0/16)" -ForegroundColor Gray
Write-Host "Volume: db_data -> $phoenixDataDir" -ForegroundColor Gray