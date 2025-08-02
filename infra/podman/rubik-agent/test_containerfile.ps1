# Test script for RUBIK Agent Containerfile (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\..\..\..\"

Write-Host "🧬 Testing RUBIK Agent Containerfile" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

try {
    # Build the container image
    Write-Host "Building RUBIK Agent container image..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    
    podman build `
        -f infra/podman/rubik-agent/Containerfile `
        -t phoenix-hydra/rubik-agent:test `
        .
    
    Write-Host "✅ Container image built successfully" -ForegroundColor Green
    
    # Test the container
    Write-Host "Testing container startup..." -ForegroundColor Yellow
    $ContainerId = podman run -d `
        --name rubik-agent-test `
        -p 8080:8080 `
        phoenix-hydra/rubik-agent:test
    
    Write-Host "Container started with ID: $ContainerId" -ForegroundColor Green
    
    # Wait for service to start
    Write-Host "Waiting for service to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Test health endpoint
    Write-Host "Testing health endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Health check passed" -ForegroundColor Green
        } else {
            throw "Health check returned status code: $($response.StatusCode)"
        }
    } catch {
        Write-Host "❌ Health check failed: $_" -ForegroundColor Red
        podman logs rubik-agent-test
        throw
    }
    
    # Test status endpoint
    Write-Host "Testing status endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/status" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Status endpoint working" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Status endpoint failed: $_" -ForegroundColor Red
    }
    
    # Test agents endpoint
    Write-Host "Testing agents endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/agents" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Agents endpoint working" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Agents endpoint failed: $_" -ForegroundColor Red
    }
    
    # Show container logs
    Write-Host "Container logs:" -ForegroundColor Yellow
    podman logs rubik-agent-test | Select-Object -Last 10
    
    Write-Host "🎉 RUBIK Agent Containerfile test completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Test failed: $_" -ForegroundColor Red
    exit 1
} finally {
    # Cleanup
    Write-Host "Cleaning up test container..." -ForegroundColor Yellow
    try {
        podman stop rubik-agent-test 2>$null
        podman rm rubik-agent-test 2>$null
    } catch {
        # Ignore cleanup errors
    }
}