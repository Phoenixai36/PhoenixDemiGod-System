#!/usr/bin/env pwsh
# Phoenix Hydra 2025 Advanced AI Model Stack Downloader
# Automated download script for the complete 2025 model ecosystem

param(
    [switch]$SkipValidation,
    [switch]$Parallel,
    [string]$OutputPath = "models/2025-stack",
    [int]$MaxConcurrent = 3
)

Write-Host "🚀 Phoenix Hydra 2025 Model Stack Downloader" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if Ollama is installed
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Ollama not found. Please install Ollama first: https://ollama.ai"
    exit 1
}

# 2025 Advanced Model Ecosystem
$ModelStack = @{
    "Core SSM/Mamba Models" = @(
        "mamba-7b",
        "mamba-13b", 
        "mamba-30b",
        "state-spaces/mamba-130m",
        "state-spaces/mamba-370m",
        "state-spaces/mamba-790m"
    )
    "2025 Flagship Models" = @(
        "minimax/abab6.5s-chat",
        "minimax/abab6.5g-chat", 
        "kimi/moonshot-v1-8k",
        "kimi/moonshot-v1-32k",
        "kimi/moonshot-v1-128k",
        "flux/kontext-7b",
        "flux/kontext-13b",
        "glm-4.5-chat",
        "glm-4.5-coder",
        "qwen2.5-coder:7b",
        "qwen2.5-coder:14b",
        "qwen2.5-coder:32b"
    )
    "Specialized Coding Models" = @(
        "deepseek-coder-v2:16b",
        "deepseek-coder-v2:236b",
        "codestral:22b",
        "codegemma:7b",
        "starcoder2:7b",
        "starcoder2:15b"
    )
    "Local Processing Optimized" = @(
        "phi3:mini",
        "phi3:medium", 
        "gemma2:2b",
        "gemma2:9b",
        "llama3.2:1b",
        "llama3.2:3b",
        "mistral-nemo:12b"
    )
    "Biomimetic Agent Models" = @(
        "neural-chat:7b",
        "orca-mini:3b",
        "orca-mini:7b",
        "vicuna:7b",
        "vicuna:13b"
    )
    "Energy Efficient Models" = @(
        "tinyllama:1.1b",
        "stablelm2:1.6b", 
        "stablelm2:12b",
        "openchat:7b",
        "solar:10.7b"
    )
}

# Create output directory
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
Write-Host "📁 Created model directory: $OutputPath" -ForegroundColor Green

# Download function
function Download-Model {
    param($ModelName, $Category)
    
    Write-Host "⬇️  Downloading $Category`: $ModelName" -ForegroundColor Yellow
    
    try {
        $result = ollama pull $ModelName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully downloaded: $ModelName" -ForegroundColor Green
            return @{ Model = $ModelName; Status = "Success"; Category = $Category }
        } else {
            Write-Host "❌ Failed to download: $ModelName" -ForegroundColor Red
            return @{ Model = $ModelName; Status = "Failed"; Category = $Category; Error = $result }
        }
    } catch {
        Write-Host "❌ Error downloading $ModelName`: $_" -ForegroundColor Red
        return @{ Model = $ModelName; Status = "Error"; Category = $Category; Error = $_.Exception.Message }
    }
}

# Download models
$Results = @()
$TotalModels = ($ModelStack.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum

Write-Host "🎯 Starting download of $TotalModels models..." -ForegroundColor Cyan

if ($Parallel) {
    Write-Host "🔄 Using parallel downloads (max $MaxConcurrent concurrent)" -ForegroundColor Blue
    
    $Jobs = @()
    foreach ($Category in $ModelStack.Keys) {
        foreach ($Model in $ModelStack[$Category]) {
            while ((Get-Job -State Running).Count -ge $MaxConcurrent) {
                Start-Sleep -Seconds 2
            }
            
            $Job = Start-Job -ScriptBlock {
                param($ModelName, $Category)
                ollama pull $ModelName
                return @{ Model = $ModelName; Category = $Category; Status = if ($LASTEXITCODE -eq 0) { "Success" } else { "Failed" } }
            } -ArgumentList $Model, $Category
            
            $Jobs += $Job
        }
    }
    
    # Wait for all jobs to complete
    Write-Host "⏳ Waiting for downloads to complete..." -ForegroundColor Yellow
    $Results = $Jobs | Wait-Job | Receive-Job
    $Jobs | Remove-Job
    
} else {
    # Sequential downloads
    $Current = 0
    foreach ($Category in $ModelStack.Keys) {
        Write-Host "`n📦 Downloading $Category models..." -ForegroundColor Magenta
        
        foreach ($Model in $ModelStack[$Category]) {
            $Current++
            Write-Progress -Activity "Downloading 2025 Model Stack" -Status "$Current of $TotalModels" -PercentComplete (($Current / $TotalModels) * 100)
            
            $Result = Download-Model -ModelName $Model -Category $Category
            $Results += $Result
        }
    }
}

# Generate summary report
Write-Host "`n📊 Download Summary Report" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

$Successful = ($Results | Where-Object { $_.Status -eq "Success" }).Count
$Failed = ($Results | Where-Object { $_.Status -ne "Success" }).Count

Write-Host "✅ Successful downloads: $Successful" -ForegroundColor Green
Write-Host "❌ Failed downloads: $Failed" -ForegroundColor Red
Write-Host "📈 Success rate: $([math]::Round(($Successful / $TotalModels) * 100, 2))%" -ForegroundColor Blue

# Save detailed report
$ReportPath = Join-Path $OutputPath "download_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$Results | ConvertTo-Json -Depth 3 | Out-File -FilePath $ReportPath -Encoding UTF8

Write-Host "`n📄 Detailed report saved to: $ReportPath" -ForegroundColor Green

# Verify installations if not skipped
if (-not $SkipValidation) {
    Write-Host "`n🔍 Verifying model installations..." -ForegroundColor Yellow
    
    $InstalledModels = ollama list | Select-String -Pattern "^[a-zA-Z]" | ForEach-Object { ($_ -split '\s+')[0] }
    
    foreach ($Result in $Results | Where-Object { $_.Status -eq "Success" }) {
        $ModelFound = $InstalledModels | Where-Object { $_ -like "*$($Result.Model)*" }
        if ($ModelFound) {
            Write-Host "✅ Verified: $($Result.Model)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Not found in list: $($Result.Model)" -ForegroundColor Yellow
        }
    }
}

# Display failed downloads
if ($Failed -gt 0) {
    Write-Host "`n❌ Failed Downloads:" -ForegroundColor Red
    $Results | Where-Object { $_.Status -ne "Success" } | ForEach-Object {
        Write-Host "  - $($_.Model) ($($_.Category))" -ForegroundColor Red
        if ($_.Error) {
            Write-Host "    Error: $($_.Error)" -ForegroundColor DarkRed
        }
    }
}

# Phoenix Hydra integration commands
Write-Host "`n🔧 Phoenix Hydra Integration Commands:" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "# Start Phoenix Hydra with 2025 models:" -ForegroundColor Gray
Write-Host "podman-compose -f infra/podman/compose.yaml up -d" -ForegroundColor White
Write-Host "`n# Test local processing pipeline:" -ForegroundColor Gray  
Write-Host "python examples/local_processing_demo.py" -ForegroundColor White
Write-Host "`n# Run RUBIK biomimetic agents:" -ForegroundColor Gray
Write-Host "python examples/rubik_ecosystem_demo.py" -ForegroundColor White
Write-Host "`n# Test SSM analysis engines:" -ForegroundColor Gray
Write-Host "python examples/ssm_analysis_demo.py" -ForegroundColor White

Write-Host "`n🎉 Phoenix Hydra 2025 Model Stack download complete!" -ForegroundColor Green
Write-Host "Ready for 100% local AI processing with energy-efficient SSM architecture!" -ForegroundColor Cyan