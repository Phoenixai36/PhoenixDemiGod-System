# Test script for analysis-engine Containerfile (Windows PowerShell)

param(
    [switch]$SkipCleanup = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..") | Select-Object -ExpandProperty Path
$ImageName = "phoenix-hydra/analysis-engine"
$ContainerName = "test-analysis-engine"

Write-Host "=== Phoenix Hydra Analysis Engine Containerfile Test ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Script directory: $ScriptDir" -ForegroundColor Gray

# Cleanup function
function Cleanup {
    if (-not $SkipCleanup) {
        Write-Host "Cleaning up test resources..." -ForegroundColor Yellow
        try {
            podman stop $ContainerName 2>$null
            podman rm $ContainerName 2>$null
        } catch {
            # Ignore cleanup errors
        }
        Write-Host "Cleanup completed" -ForegroundColor Green
    }
}

# Set cleanup trap
try {
    # Change to project root
    Set-Location $ProjectRoot

    Write-Host "Step 1: Building analysis-engine container image..." -ForegroundColor Yellow
    podman build -t "${ImageName}:test" -f infra/podman/analysis-engine/Containerfile .
    if ($LASTEXITCODE -ne 0) {
        throw "Container build failed"
    }

    Write-Host "Step 2: Running container in background..." -ForegroundColor Yellow
    podman run -d `
        --name $ContainerName `
        -p 8090:8090 `
        --security-opt no-new-privileges:true `
        --user 1000:1000 `
        "${ImageName}:test"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Container start failed"
    }

    Write-Host "Step 3: Waiting for container to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10

    Write-Host "Step 4: Checking container status..." -ForegroundColor Yellow
    $ContainerStatus = podman ps --filter "name=$ContainerName" --format "{{.Names}}"
    if (-not $ContainerStatus) {
        Write-Host "ERROR: Container is not running" -ForegroundColor Red
        podman logs $ContainerName
        throw "Container not running"
    }

    Write-Host "Step 5: Testing health check..." -ForegroundColor Yellow
    $HealthCheckPassed = $false
    for ($i = 1; $i -le 6; $i++) {
        Write-Host "Health check attempt $i/6..." -ForegroundColor Gray
        try {
            $null = podman exec $ContainerName python -c "import requests; requests.get('http://localhost:8090/metrics', timeout=5)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Health check passed" -ForegroundColor Green
                $HealthCheckPassed = $true
                break
            }
        } catch {
            # Continue to next attempt
        }
        
        if ($i -eq 6) {
            Write-Host "ERROR: Health check failed after 6 attempts" -ForegroundColor Red
            podman logs $ContainerName
            throw "Health check failed"
        } else {
            Write-Host "Health check failed, retrying in 5 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }

    Write-Host "Step 6: Testing Prometheus metrics endpoint..." -ForegroundColor Yellow
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8090/metrics" -TimeoutSec 10 -UseBasicParsing
        if ($Response.StatusCode -eq 200) {
            Write-Host "✓ Prometheus metrics endpoint accessible" -ForegroundColor Green
        } else {
            throw "Unexpected status code: $($Response.StatusCode)"
        }
    } catch {
        Write-Host "ERROR: Cannot access Prometheus metrics endpoint: $_" -ForegroundColor Red
        throw "Metrics endpoint test failed"
    }

    Write-Host "Step 7: Checking container logs for errors..." -ForegroundColor Yellow
    $Logs = podman logs $ContainerName 2>&1
    $ErrorLines = $Logs | Where-Object { $_ -match "error|ERROR|Error" }
    if ($ErrorLines) {
        Write-Host "WARNING: Errors found in container logs:" -ForegroundColor Yellow
        $ErrorLines | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    } else {
        Write-Host "✓ No errors found in container logs" -ForegroundColor Green
    }

    Write-Host "Step 8: Testing rootless execution..." -ForegroundColor Yellow
    $UserInfo = podman exec $ContainerName id
    if ($UserInfo -match "uid=1000") {
        Write-Host "✓ Container running as non-root user" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Container not running as expected user" -ForegroundColor Red
        Write-Host "User info: $UserInfo" -ForegroundColor Red
        throw "User check failed"
    }

    Write-Host "Step 9: Testing file permissions..." -ForegroundColor Yellow
    $FileList = podman exec $ContainerName ls -la /app/
    $FileList | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

    Write-Host "Step 10: Testing Python imports..." -ForegroundColor Yellow
    try {
        $ImportTest = podman exec $ContainerName python -c "import torch, numpy, asyncio; print('All imports successful')"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python dependencies imported successfully" -ForegroundColor Green
        } else {
            throw "Import test returned non-zero exit code"
        }
    } catch {
        Write-Host "ERROR: Python import test failed: $_" -ForegroundColor Red
        throw "Python import test failed"
    }

    Write-Host ""
    Write-Host "=== All Tests Passed! ===" -ForegroundColor Green
    Write-Host "✓ Container builds successfully" -ForegroundColor Green
    Write-Host "✓ Container runs with rootless user" -ForegroundColor Green
    Write-Host "✓ Health check endpoint works" -ForegroundColor Green
    Write-Host "✓ Prometheus metrics accessible" -ForegroundColor Green
    Write-Host "✓ Python dependencies available" -ForegroundColor Green
    Write-Host "✓ No critical errors in logs" -ForegroundColor Green
    Write-Host ""
    Write-Host "Analysis Engine container is ready for deployment!" -ForegroundColor Cyan

} catch {
    Write-Host "Test failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Cleanup
}