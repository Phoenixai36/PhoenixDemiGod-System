#!/usr/bin/env pwsh
# Phoenix Hugger Local Execution
# Ejecuta phoenix_hugger.py directamente en tu máquina

param(
    [switch]$TestMode,
    [switch]$SkipHF,
    [switch]$SkipOllama,
    [int]$Workers = 4,
    [string]$OutputDir = "models",
    [string]$HfToken = $env:HF_TOKEN
)

Write-Host "🚀 Phoenix Hugger Local Execution" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if we're in virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  No virtual environment detected" -ForegroundColor Yellow
}

# Check Python dependencies
Write-Host "`n📦 Checking dependencies..." -ForegroundColor Cyan
$requiredPackages = @("rich", "click", "huggingface_hub", "requests")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $result = pip show $package 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $package installed" -ForegroundColor Green
    } else {
        Write-Host "❌ $package missing" -ForegroundColor Red
        $missingPackages += $package
    }
}

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host "`n📥 Installing missing packages..." -ForegroundColor Yellow
    pip install $missingPackages
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "📁 Created output directory: $OutputDir" -ForegroundColor Green
}

# Build command arguments
$args = @(
    "scripts/phoenix_hugger.py",
    "--out", $OutputDir,
    "--workers", $Workers.ToString()
)

if ($TestMode) {
    $args += "--test-mode"
    Write-Host "🧪 Test mode enabled" -ForegroundColor Yellow
}

if ($SkipHF) {
    $args += "--skip-hf"
    Write-Host "⏭️  Skipping Hugging Face" -ForegroundColor Yellow
}

if ($SkipOllama) {
    $args += "--skip-ollama"
    Write-Host "⏭️  Skipping Ollama" -ForegroundColor Yellow
}

# Set environment variables
if ($HfToken) {
    $env:HF_TOKEN = $HfToken
    Write-Host "🔑 HF Token configured" -ForegroundColor Green
}

# Show execution info
Write-Host "`n⚙️  Execution Configuration:" -ForegroundColor Cyan
Write-Host "Output Directory: $OutputDir" -ForegroundColor White
Write-Host "Workers: $Workers" -ForegroundColor White
Write-Host "Test Mode: $(if ($TestMode) { 'Yes' } else { 'No' })" -ForegroundColor White
Write-Host "HF Token: $(if ($HfToken) { 'Provided' } else { 'Not provided' })" -ForegroundColor White

# Execute Phoenix Hugger
Write-Host "`n🚀 Executing Phoenix Hugger..." -ForegroundColor Cyan
Write-Host "Command: python $($args -join ' ')" -ForegroundColor Gray

$startTime = Get-Date

try {
    python @args
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Phoenix Hugger completed successfully!" -ForegroundColor Green
        Write-Host "⏱️  Total time: $($duration.ToString('mm\:ss'))" -ForegroundColor Blue
        
        # Show results
        Write-Host "`n📊 Results:" -ForegroundColor Cyan
        if (Test-Path "$OutputDir/huggingface") {
            $hfModels = Get-ChildItem "$OutputDir/huggingface" -Recurse -Directory | Measure-Object | Select-Object -ExpandProperty Count
            Write-Host "📁 HF Models downloaded: $hfModels directories" -ForegroundColor Green
        }
        
        # Check for reports
        $reports = Get-ChildItem $OutputDir -Filter "*report*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($reports) {
            Write-Host "📄 Latest report: $($reports.Name)" -ForegroundColor Green
        }
        
        Write-Host "`n🎯 Next Steps:" -ForegroundColor Yellow
        Write-Host "1. Check downloaded models in: $OutputDir" -ForegroundColor Green
        Write-Host "2. Run complete demo: python examples/complete_2025_stack_demo.py" -ForegroundColor Green
        Write-Host "3. Check gap analysis: python src/ssm_analysis/advanced_gap_detection.py" -ForegroundColor Green
        
        if ($TestMode) {
            Write-Host "4. Run full download: Remove -TestMode flag" -ForegroundColor Green
        }
        
    } else {
        Write-Host "`n❌ Phoenix Hugger failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
    
} catch {
    Write-Host "`n❌ Execution error: $_" -ForegroundColor Red
}

Write-Host "`n🎉 Phoenix Hugger local execution completed!" -ForegroundColor Green