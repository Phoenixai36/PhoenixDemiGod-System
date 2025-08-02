#!/usr/bin/env pwsh

# Phoenix Hydra Podman Volume Cleanup Script (PowerShell)
# This script removes volume directories and data (use with caution!)

$PhoenixDataDir = Join-Path $env:USERPROFILE ".local/share/phoenix-hydra"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"

Write-Host "⚠️  Phoenix Hydra Volume Cleanup" -ForegroundColor Yellow
Write-Host "This will remove all volume data including:"
Write-Host "  - Database data: $(Join-Path $PhoenixDataDir 'db_data')"
Write-Host "  - Nginx config: $(Join-Path $PhoenixDataDir 'nginx_config')"
Write-Host "  - Logs: $(Join-Path $PhoenixDataDir 'logs')"
Write-Host ""

$confirmation = Read-Host "Are you sure you want to continue? (y/N)"
if ($confirmation -notmatch "^[Yy]$") {
    Write-Host "Cleanup cancelled." -ForegroundColor Green
    exit 0
}

Write-Host "Stopping any running containers..." -ForegroundColor Blue
try {
    & podman-compose -f $ComposeFile down 2>$null
} catch {
    # Ignore errors if compose file doesn't exist or containers aren't running
}

Write-Host "Removing volume directories..." -ForegroundColor Blue
if (Test-Path $PhoenixDataDir) {
    $dbDataDir = Join-Path $PhoenixDataDir "db_data"
    $nginxConfigDir = Join-Path $PhoenixDataDir "nginx_config"
    $logsDir = Join-Path $PhoenixDataDir "logs"
    
    # Remove subdirectories
    if (Test-Path $dbDataDir) {
        Remove-Item -Path $dbDataDir -Recurse -Force
        Write-Host "Removed db_data directory" -ForegroundColor Green
    }
    
    if (Test-Path $nginxConfigDir) {
        Remove-Item -Path $nginxConfigDir -Recurse -Force
        Write-Host "Removed nginx_config directory" -ForegroundColor Green
    }
    
    if (Test-Path $logsDir) {
        Remove-Item -Path $logsDir -Recurse -Force
        Write-Host "Removed logs directory" -ForegroundColor Green
    }
    
    # Remove parent directory if empty
    try {
        $remainingItems = Get-ChildItem -Path $PhoenixDataDir -ErrorAction SilentlyContinue
        if (-not $remainingItems) {
            Remove-Item -Path $PhoenixDataDir -Force
            Write-Host "Removed empty phoenix-hydra directory" -ForegroundColor Green
        }
    } catch {
        # Directory not empty or other issue, leave it
    }
    
    Write-Host "✅ Volume directories removed successfully!" -ForegroundColor Green
} else {
    Write-Host "Volume directory does not exist: $PhoenixDataDir" -ForegroundColor Yellow
}

Write-Host "Cleanup complete." -ForegroundColor Blue