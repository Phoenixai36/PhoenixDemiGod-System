#!/usr/bin/env pwsh
# Phoenix Hugger Pod Execution Script
# Ejecuta phoenix_hugger.py en tu pod Podman existente

param(
    [switch]$TestMode,
    [switch]$SkipHF,
    [switch]$SkipOllama,
    [int]$Workers = 2,
    [string]$HfToken = $env:HF_TOKEN,
    [string]$PodName = "pod_phoenix-hydra",
    [string]$OllamaContainer = "phoenix-hydra_phoenix-core_1"
)

Write-Host "🚀 Phoenix Hugger Pod Execution" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if Podman is available
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Podman not found. Please install Podman first."
    exit 1
}

Write-Host "✅ Podman found" -ForegroundColor Green

# Check pod status
Write-Host "`n🔍 Checking pod status..." -ForegroundColor Cyan
try {
    $podStatus = podman pod inspect $PodName | ConvertFrom-Json
    Write-Host "✅ Pod '$PodName' found - State: $($podStatus.State)" -ForegroundColor Green
    
    # Show containers
    Write-Host "`n📦 Containers in pod:" -ForegroundColor Blue
    foreach ($container in $podStatus.Containers) {
        $status = if ($container.State -eq "running") { "✅" } else { "❌" }
        Write-Host "  $status $($container.Name) - $($container.State)" -ForegroundColor White
    }
    
} catch {
    Write-Error "❌ Pod '$PodName' not found or not accessible"
    exit 1
}

# Check Ollama container
Write-Host "`n🦙 Checking Ollama container..." -ForegroundColor Cyan
try {
    $ollamaCheck = podman exec $OllamaContainer ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Ollama accessible in container" -ForegroundColor Green
        
        # Count current models
        $modelLines = ($ollamaCheck -split "`n" | Where-Object { $_ -match "^\w" -and $_ -notmatch "^NAME" }).Count
        Write-Host "📊 Current models: $modelLines" -ForegroundColor Blue
    } else {
        Write-Host "⚠️  Ollama not responding, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check Ollama, but continuing..." -ForegroundColor Yellow
}

# Prepare phoenix_hugger.py execution
Write-Host "`n📋 Preparing Phoenix Hugger execution..." -ForegroundColor Cyan

# Copy script to container
Write-Host "📁 Copying phoenix_hugger.py to container..." -ForegroundColor Yellow
try {
    podman cp "scripts/phoenix_hugger.py" "${OllamaContainer}:/tmp/phoenix_hugger.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy script"
    }
    Write-Host "✅ Script copied successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Failed to copy script to container: $_"
    exit 1
}

# Install dependencies in container
Write-Host "📦 Installing dependencies in container..." -ForegroundColor Yellow
$installCmd = @"
python3 -m pip install --user rich click huggingface_hub requests
"@

try {
    podman exec $OllamaContainer bash -c $installCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Some dependencies may have failed, continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Dependency installation issues, continuing..." -ForegroundColor Yellow
}

# Build execution command
$execArgs = @(
    "exec", "-it"
)

# Add environment variables
if ($HfToken) {
    $execArgs += @("-e", "HF_TOKEN=$HfToken")
}
$execArgs += @("-e", "PHX_HYDRA_MODELDIR=/models")
$execArgs += @("-e", "PHX_HYDRA_WORKERS=$Workers")

# Add container name
$execArgs += $OllamaContainer

# Add Python command
$pythonArgs = @(
    "python3", "/tmp/phoenix_hugger.py",
    "--out", "/models",
    "--workers", $Workers.ToString(),
    "--ollama-host", "localhost:11434"
)

# Add optional flags
if ($TestMode) {
    $pythonArgs += "--test-mode"
    Write-Host "🧪 Test mode enabled - limited models" -ForegroundColor Yellow
}

if ($SkipHF) {
    $pythonArgs += "--skip-hf"
    Write-Host "⏭️  Skipping Hugging Face downloads" -ForegroundColor Yellow
}

if ($SkipOllama) {
    $pythonArgs += "--skip-ollama"
    Write-Host "⏭️  Skipping Ollama downloads" -ForegroundColor Yellow
}

$execArgs += $pythonArgs

# Show execution summary
Write-Host "`n⚙️  Execution Configuration:" -ForegroundColor Cyan
Write-Host "  Pod: $PodName" -ForegroundColor White
Write-Host "  Container: $OllamaContainer" -ForegroundColor White
Write-Host "  Workers: $Workers" -ForegroundColor White
Write-Host "  Test Mode: $(if ($TestMode) { 'Yes' } else { 'No' })" -ForegroundColor White
Write-Host "  HF Token: $(if ($HfToken) { 'Provided' } else { 'Not provided' })" -ForegroundColor White

# Execute phoenix_hugger
Write-Host "`n🚀 Executing Phoenix Hugger..." -ForegroundColor Bold -ForegroundColor Cyan
Write-Host "Command: podman $($execArgs -join ' ')" -ForegroundColor Gray

try {
    $startTime = Get-Date
    
    # Execute the command
    & podman @execArgs
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Phoenix Hugger completed successfully!" -ForegroundColor Green
        Write-Host "⏱️  Total time: $($duration.ToString('mm\:ss'))" -ForegroundColor Blue
        
        # Show next steps
        Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Check downloaded models:" -ForegroundColor Green
        Write-Host "   podman exec $OllamaContainer ollama list" -ForegroundColor Gray
        Write-Host "2. Run complete demo:" -ForegroundColor Green
        Write-Host "   python examples/complete_2025_stack_demo.py" -ForegroundColor Gray
        Write-Host "3. Check gap analysis:" -ForegroundColor Green
        Write-Host "   python src/ssm_analysis/advanced_gap_detection.py" -ForegroundColor Gray
        
        if ($TestMode) {
            Write-Host "`n💡 To download all models, run without --TestMode" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "`n❌ Phoenix Hugger failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        
        # Show troubleshooting
        Write-Host "`n🔧 Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Check container logs:" -ForegroundColor White
        Write-Host "   podman logs $OllamaContainer" -ForegroundColor Gray
        Write-Host "2. Check container status:" -ForegroundColor White
        Write-Host "   podman ps -a" -ForegroundColor Gray
        Write-Host "3. Try with --TestMode first" -ForegroundColor White
    }
    
} catch {
    Write-Error "❌ Execution failed: $_"
    
    Write-Host "`n🔧 Debug Information:" -ForegroundColor Yellow
    Write-Host "Pod Status:" -ForegroundColor White
    podman pod ps
    Write-Host "`nContainer Status:" -ForegroundColor White
    podman ps -a --filter "pod=$PodName"
}

# Cleanup
Write-Host "`n🧹 Cleaning up temporary files..." -ForegroundColor Cyan
try {
    podman exec $OllamaContainer rm -f /tmp/phoenix_hugger.py
    Write-Host "✅ Cleanup completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Cleanup warning: $_" -ForegroundColor Yellow
}

Write-Host "`n🎉 Phoenix Hugger Pod execution completed!" -ForegroundColor Bold -ForegroundColor Green