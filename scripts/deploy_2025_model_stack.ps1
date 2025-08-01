#!/usr/bin/env pwsh
# Phoenix Hydra 2025 Model Stack Deployment
# Complete automated deployment using Podman volumes

param(
    [switch]$SkipOllama,
    [switch]$SkipHuggingFace,
    [switch]$Parallel,
    [string]$HfToken = "",
    [int]$MaxConcurrent = 3
)

Write-Host "🚀 Phoenix Hydra 2025 Model Stack Deployment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check prerequisites
$Prerequisites = @("podman", "podman-compose")
foreach ($cmd in $Prerequisites) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "❌ $cmd not found. Please install Podman first."
        exit 1
    }
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Create model directories
$ModelDirs = @("models", "models/ollama", "models/huggingface")
foreach ($dir in $ModelDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "📁 Created directory: $dir" -ForegroundColor Green
    }
}

# Set environment variables for compose
$env:PWD = Get-Location
$env:HF_TOKEN = $HfToken

Write-Host "`n🐳 Starting Phoenix Hydra model downloader services..." -ForegroundColor Cyan

try {
    # Start the model downloader stack
    $ComposeFile = "infra/podman/model-downloader-compose.yaml"
    
    if (-not (Test-Path $ComposeFile)) {
        Write-Error "❌ Compose file not found: $ComposeFile"
        exit 1
    }
    
    # Pull images first
    Write-Host "📥 Pulling container images..." -ForegroundColor Yellow
    podman-compose -f $ComposeFile pull
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to pull images"
        exit 1
    }
    
    # Start services
    Write-Host "🚀 Starting model downloader services..." -ForegroundColor Yellow
    podman-compose -f $ComposeFile up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to start services"
        exit 1
    }
    
    Write-Host "✅ Services started successfully" -ForegroundColor Green
    
    # Wait for services to be ready
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check service health
    $Services = @("phoenix-model-downloader", "phoenix-hf-downloader", "phoenix-model-manager")
    foreach ($service in $Services) {
        $status = podman ps --filter "name=$service" --format "{{.Status}}"
        if ($status -like "*Up*") {
            Write-Host "✅ $service is running" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $service status: $status" -ForegroundColor Yellow
        }
    }
    
    # Download Ollama models if not skipped
    if (-not $SkipOllama) {
        Write-Host "`n🦙 Starting Ollama model downloads..." -ForegroundColor Cyan
        
        # Execute the PowerShell script inside the container
        $OllamaArgs = @()
        if ($Parallel) { $OllamaArgs += "--parallel" }
        if ($MaxConcurrent -ne 3) { $OllamaArgs += "--max-concurrent", $MaxConcurrent }
        
        $OllamaCommand = "pwsh /scripts/download_2025_model_stack.ps1 " + ($OllamaArgs -join " ")
        
        podman exec phoenix-model-downloader bash -c "curl -fsSL https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/powershell-7.4.0-linux-x64.tar.gz | tar -xzC /opt && ln -sf /opt/powershell /usr/local/bin/pwsh"
        podman exec phoenix-model-downloader $OllamaCommand
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Ollama models downloaded successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Some Ollama models may have failed to download" -ForegroundColor Yellow
        }
    }
    
    # Download Hugging Face models if not skipped
    if (-not $SkipHuggingFace) {
        Write-Host "`n🤗 Starting Hugging Face model downloads..." -ForegroundColor Cyan
        
        # The HF downloader runs automatically as part of the compose stack
        # Monitor its progress
        $timeout = 300  # 5 minutes timeout
        $elapsed = 0
        
        do {
            $hfStatus = podman ps --filter "name=phoenix-hf-downloader" --format "{{.Status}}"
            if ($hfStatus -like "*Exited (0)*") {
                Write-Host "✅ Hugging Face models downloaded successfully" -ForegroundColor Green
                break
            } elseif ($hfStatus -like "*Exited*") {
                Write-Host "❌ Hugging Face downloader failed" -ForegroundColor Red
                podman logs phoenix-hf-downloader
                break
            }
            
            Start-Sleep -Seconds 10
            $elapsed += 10
            Write-Host "⏳ HF Downloader still running... ($elapsed/$timeout seconds)" -ForegroundColor Yellow
            
        } while ($elapsed -lt $timeout)
        
        if ($elapsed -ge $timeout) {
            Write-Host "⚠️  HF Downloader timeout reached" -ForegroundColor Yellow
        }
    }
    
    # Generate model inventory
    Write-Host "`n📋 Generating model inventory..." -ForegroundColor Cyan
    
    # Wait for model manager to complete
    $timeout = 120  # 2 minutes timeout
    $elapsed = 0
    
    do {
        $managerStatus = podman ps --filter "name=phoenix-model-manager" --format "{{.Status}}"
        if ($managerStatus -like "*Exited (0)*") {
            Write-Host "✅ Model inventory generated successfully" -ForegroundColor Green
            break
        } elseif ($managerStatus -like "*Exited*") {
            Write-Host "❌ Model manager failed" -ForegroundColor Red
            podman logs phoenix-model-manager
            break
        }
        
        Start-Sleep -Seconds 5
        $elapsed += 5
        Write-Host "⏳ Model manager still running... ($elapsed/$timeout seconds)" -ForegroundColor Yellow
        
    } while ($elapsed -lt $timeout)
    
    # Display results
    Write-Host "`n📊 Deployment Results:" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    
    # Check model directories
    $OllamaModels = Get-ChildItem -Path "models/ollama" -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count
    $HfModels = Get-ChildItem -Path "models/huggingface" -Recurse -Directory | Measure-Object | Select-Object -ExpandProperty Count
    
    Write-Host "📁 Ollama models directory: $OllamaModels files" -ForegroundColor Green
    Write-Host "📁 Hugging Face models directory: $HfModels directories" -ForegroundColor Green
    
    # Show inventory files
    $InventoryFiles = Get-ChildItem -Path "models" -Filter "*inventory*" | Select-Object -ExpandProperty Name
    if ($InventoryFiles) {
        Write-Host "📄 Inventory files created:" -ForegroundColor Green
        foreach ($file in $InventoryFiles) {
            Write-Host "  - $file" -ForegroundColor White
        }
    }
    
    # Phoenix Hydra integration
    Write-Host "`n🔧 Phoenix Hydra Integration:" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host "# Start Phoenix Hydra with downloaded models:" -ForegroundColor Gray
    Write-Host "podman-compose -f infra/podman/compose.yaml up -d" -ForegroundColor White
    Write-Host "`n# Test local processing:" -ForegroundColor Gray
    Write-Host "python examples/local_processing_demo.py" -ForegroundColor White
    Write-Host "`n# Run RUBIK biomimetic agents:" -ForegroundColor Gray
    Write-Host "python examples/rubik_ecosystem_demo.py" -ForegroundColor White
    
    Write-Host "`n🎉 Phoenix Hydra 2025 Model Stack deployment complete!" -ForegroundColor Green
    Write-Host "Ready for 100% local AI processing!" -ForegroundColor Cyan
    
} catch {
    Write-Error "❌ Deployment failed: $_"
    
    # Show logs for debugging
    Write-Host "`n📋 Container logs for debugging:" -ForegroundColor Yellow
    podman logs phoenix-model-downloader --tail 20
    podman logs phoenix-hf-downloader --tail 20
    podman logs phoenix-model-manager --tail 20
    
} finally {
    # Cleanup option
    Write-Host "`n🧹 Cleanup options:" -ForegroundColor Yellow
    Write-Host "# Stop services: podman-compose -f $ComposeFile down" -ForegroundColor Gray
    Write-Host "# Remove volumes: podman volume rm phoenix-models phoenix-hf-cache" -ForegroundColor Gray
}