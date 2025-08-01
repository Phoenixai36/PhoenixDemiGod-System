#!/usr/bin/env pwsh
# Restart Phoenix Hydra Pod Script

param(
    [string]$PodName = "pod_phoenix-hydra"
)

Write-Host "🔄 Restarting Phoenix Hydra Pod" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Check current pod status
Write-Host "🔍 Checking current pod status..." -ForegroundColor Yellow
podman pod ps

# Start the pod
Write-Host "`n🚀 Starting pod '$PodName'..." -ForegroundColor Cyan
try {
    podman pod start $PodName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Pod started successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Pod start returned code: $LASTEXITCODE" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error starting pod: $_" -ForegroundColor Red
}

# Wait a moment for containers to initialize
Write-Host "⏳ Waiting for containers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check final status
Write-Host "`n📊 Final pod status:" -ForegroundColor Cyan
podman pod ps

Write-Host "`n📦 Container status:" -ForegroundColor Cyan
podman ps --filter "pod=$PodName"

# Check if we can find an Ollama-compatible container
Write-Host "`n🔍 Looking for suitable containers..." -ForegroundColor Cyan
$containers = podman ps --filter "pod=$PodName" --format "{{.Names}}" | Where-Object { $_ -match "n8n|phoenix|core" }

if ($containers) {
    Write-Host "📋 Available containers for Phoenix Hugger:" -ForegroundColor Green
    foreach ($container in $containers) {
        Write-Host "  • $container" -ForegroundColor White
    }
    
    # Suggest the best container
    $bestContainer = $containers | Where-Object { $_ -match "phoenix-core" } | Select-Object -First 1
    if (-not $bestContainer) {
        $bestContainer = $containers | Select-Object -First 1
    }
    
    Write-Host "`n💡 Recommended container for Phoenix Hugger: $bestContainer" -ForegroundColor Yellow
    Write-Host "Update the script with: -OllamaContainer '$bestContainer'" -ForegroundColor Gray
} else {
    Write-Host "⚠️  No suitable containers found" -ForegroundColor Yellow
}

Write-Host "`n✅ Pod restart process completed!" -ForegroundColor Green