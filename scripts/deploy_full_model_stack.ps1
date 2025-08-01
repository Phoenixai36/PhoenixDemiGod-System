#!/usr/bin/env pwsh
<#
.SYNOPSIS
Phoenix Hydra 2025 Full Model Stack Deployment
Deploys complete Phoenix Hydra stack with comprehensive model downloads

.DESCRIPTION
This script:
1. Sets up the environment and directories
2. Downloads all Hugging Face models via phoenix_hugger.py
3. Starts Ollama and downloads all specified models
4. Launches all Phoenix Hydra services
5. Provides monitoring and health checks

.PARAMETER ModelDir
Directory for model storage (default: ./models)

.PARAMETER Workers
Number of parallel download workers (default: 6)

.PARAMETER SkipHF
Skip Hugging Face model downloads

.PARAMETER SkipOllama
Skip Ollama model downloads

.PARAMETER TestMode
Run in test mode with limited models

.EXAMPLE
.\scripts\deploy_full_model_stack.ps1
.\scripts\deploy_full_model_stack.ps1 -ModelDir "D:\models" -Workers 8
.\scripts\deploy_full_model_stack.ps1 -TestMode
#>

param(
    [string]$ModelDir = "./models",
    [int]$Workers = 6,
    [switch]$SkipHF,
    [switch]$SkipOllama,
    [switch]$TestMode,
    [string]$HFToken = $env:HF_TOKEN
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Magenta = "`e[35m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Reset)
    Write-Host "$Color$Message$Reset"
}

function Show-Banner {
    Write-ColorOutput @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 Phoenix Hydra 2025 Full Model Stack Deployment        ║
║                                                              ║
║    • Complete Hugging Face model ecosystem                  ║
║    • Full Ollama model collection                           ║
║    • All Phoenix Hydra services                             ║
║    • Monitoring and health checks                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ $Cyan
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." $Blue
    
    $missing = @()
    
    if (!(Get-Command podman -ErrorAction SilentlyContinue)) {
        $missing += "podman"
    }
    
    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        $missing += "python"
    }
    
    if ($missing.Count -gt 0) {
        Write-ColorOutput "❌ Missing prerequisites: $($missing -join ', ')" $Red
        Write-ColorOutput "Please install missing tools and try again." $Yellow
        exit 1
    }
    
    Write-ColorOutput "✅ All prerequisites found" $Green
}

function Setup-Environment {
    Write-ColorOutput "⚙️ Setting up environment..." $Blue
    
    # Create model directory
    $modelPath = Resolve-Path $ModelDir -ErrorAction SilentlyContinue
    if (!$modelPath) {
        New-Item -ItemType Directory -Path $ModelDir -Force | Out-Null
        $modelPath = Resolve-Path $ModelDir
    }
    
    Write-ColorOutput "📁 Model directory: $modelPath" $Green
    
    # Set environment variables
    $env:PHX_HYDRA_MODELDIR = $modelPath
    $env:PHX_HYDRA_WORKERS = $Workers
    if ($HFToken) {
        $env:HF_TOKEN = $HFToken
        Write-ColorOutput "🔑 Hugging Face token configured" $Green
    }
    
    # Create monitoring directory
    if (!(Test-Path "monitoring")) {
        New-Item -ItemType Directory -Path "monitoring" -Force | Out-Null
    }
    
    # Create basic Prometheus config if it doesn't exist
    if (!(Test-Path "monitoring/prometheus.yml")) {
        @"
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'phoenix-hydra'
    static_configs:
      - targets: ['phoenix-core:8080', 'nca-toolkit:8081', 'ollama:11434']
  
  - job_name: 'model-api'
    static_configs:
      - targets: ['model-api:8090']
"@ | Out-File -FilePath "monitoring/prometheus.yml" -Encoding UTF8
    }
    
    Write-ColorOutput "✅ Environment setup complete" $Green
}

function Start-ModelDownloads {
    if ($SkipHF -and $SkipOllama) {
        Write-ColorOutput "⏭️ Skipping all model downloads" $Yellow
        return
    }
    
    Write-ColorOutput "📥 Starting model downloads..." $Blue
    
    # Install Python dependencies
    Write-ColorOutput "📦 Installing Python dependencies..." $Blue
    python -m pip install -r requirements-models.txt
    
    if (!$SkipHF) {
        Write-ColorOutput "🤗 Starting Hugging Face model downloads..." $Magenta
        
        $hfArgs = @(
            "scripts/phoenix_hugger.py"
            "--out", $ModelDir
            "--workers", $Workers
        )
        
        if ($TestMode) { $hfArgs += "--test-mode" }
        if ($SkipOllama) { $hfArgs += "--skip-ollama" }
        if ($HFToken) { $hfArgs += "--hf-token", $HFToken }
        
        python @hfArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Hugging Face models downloaded successfully" $Green
        } else {
            Write-ColorOutput "⚠️ Some Hugging Face models may have failed" $Yellow
        }
    }
}

function Start-Services {
    Write-ColorOutput "🐳 Starting Phoenix Hydra services..." $Blue
    
    # Stop any existing services
    podman-compose -f infra/podman/compose-full-models.yaml down 2>$null
    
    # Start services
    Write-ColorOutput "🚀 Launching all services..." $Magenta
    podman-compose -f infra/podman/compose-full-models.yaml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ All services started successfully" $Green
    } else {
        Write-ColorOutput "❌ Failed to start some services" $Red
        return $false
    }
    
    return $true
}

function Wait-ForServices {
    Write-ColorOutput "⏳ Waiting for services to be ready..." $Blue
    
    $services = @(
        @{ Name = "Phoenix Core"; Url = "http://localhost:8080/health"; Timeout = 30 }
        @{ Name = "NCA Toolkit"; Url = "http://localhost:8081"; Timeout = 30 }
        @{ Name = "n8n"; Url = "http://localhost:5678"; Timeout = 60 }
        @{ Name = "Windmill"; Url = "http://localhost:8000"; Timeout = 60 }
        @{ Name = "Ollama"; Url = "http://localhost:11434"; Timeout = 120 }
        @{ Name = "Model API"; Url = "http://localhost:8090/models/status"; Timeout = 60 }
    )
    
    foreach ($service in $services) {
        Write-ColorOutput "🔍 Checking $($service.Name)..." $Blue
        
        $timeout = $service.Timeout
        $elapsed = 0
        $ready = $false
        
        while ($elapsed -lt $timeout -and !$ready) {
            try {
                $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-ColorOutput "✅ $($service.Name) is ready" $Green
                    $ready = $true
                } else {
                    Start-Sleep -Seconds 2
                    $elapsed += 2
                }
            } catch {
                Start-Sleep -Seconds 2
                $elapsed += 2
            }
        }
        
        if (!$ready) {
            Write-ColorOutput "⚠️ $($service.Name) not ready after $timeout seconds" $Yellow
        }
    }
}

function Show-ServiceStatus {
    Write-ColorOutput @"

🎉 Phoenix Hydra 2025 Full Stack Deployment Complete!

📊 Service URLs:
┌─────────────────────────────────────────────────────────────┐
│ Phoenix Core:     http://localhost:8080                     │
│ NCA Toolkit:      http://localhost:8081                     │
│ n8n Workflows:    http://localhost:5678                     │
│ Windmill:         http://localhost:8000                     │
│ Ollama API:       http://localhost:11434                    │
│ Model API:        http://localhost:8090                     │
│ Prometheus:       http://localhost:9090                     │
│ PostgreSQL:       localhost:5432                            │
└─────────────────────────────────────────────────────────────┘

🔧 Management Commands:
• View logs:          podman-compose -f infra/podman/compose-full-models.yaml logs
• Stop services:      podman-compose -f infra/podman/compose-full-models.yaml down
• Restart services:   podman-compose -f infra/podman/compose-full-models.yaml restart
• Check status:       podman-compose -f infra/podman/compose-full-models.yaml ps

📁 Model Storage: $ModelDir

🚀 Ready for Phoenix Hydra development and deployment!
"@ $Green
}

function Show-ModelStats {
    Write-ColorOutput "📊 Checking model statistics..." $Blue
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8090/models/status" -TimeoutSec 10
        Write-ColorOutput @"

📈 Model Statistics:
• Hugging Face Models: $($response.huggingface_models)
• Total Storage Used: $($response.total_size_gb) GB
• Ollama Available: $($response.ollama_available)
"@ $Cyan
    } catch {
        Write-ColorOutput "⚠️ Could not retrieve model statistics" $Yellow
    }
}

# Main execution
try {
    Show-Banner
    Test-Prerequisites
    Setup-Environment
    Start-ModelDownloads
    
    if (Start-Services) {
        Wait-ForServices
        Show-ServiceStatus
        Show-ModelStats
        
        Write-ColorOutput @"

🎯 Next Steps:
1. Test the complete stack: python examples/complete_2025_stack_demo.py
2. Run system analysis: python src/ssm_analysis/advanced_gap_detection.py
3. Check revenue tracking: node scripts/revenue-tracking.js
4. Deploy to production: Follow docs/deployment-guide.md

Happy coding with Phoenix Hydra! 🚀
"@ $Magenta
    } else {
        Write-ColorOutput "❌ Deployment failed. Check logs for details." $Red
        exit 1
    }
    
} catch {
    Write-ColorOutput "💥 Unexpected error: $_" $Red
    Write-ColorOutput "Check the logs and try again." $Yellow
    exit 1
}