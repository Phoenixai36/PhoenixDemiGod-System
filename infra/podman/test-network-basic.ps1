# Basic Phoenix Hydra Network Test Script (PowerShell)
# Simple validation of network configuration

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"

Write-Host "Phoenix Hydra Network Test" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Check if compose file exists
if (Test-Path $ComposeFile) {
    Write-Host "✅ Compose file found" -ForegroundColor Green
    
    $content = Get-Content $ComposeFile -Raw
    
    # Check for network definition
    if ($content -like "*phoenix-net:*") {
        Write-Host "✅ Network definition found" -ForegroundColor Green
    } else {
        Write-Host "❌ Network definition missing" -ForegroundColor Red
    }
    
    # Check for subnet
    if ($content -like "*172.20.0.0/16*") {
        Write-Host "✅ Subnet configured correctly" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Subnet configuration may be missing" -ForegroundColor Yellow
    }
    
    # Check for gateway
    if ($content -like "*172.20.0.1*") {
        Write-Host "✅ Gateway configured correctly" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Gateway configuration may be missing" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "❌ Compose file not found: $ComposeFile" -ForegroundColor Red
}

Write-Host ""
Write-Host "Network test completed!" -ForegroundColor Green