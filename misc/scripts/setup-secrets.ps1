# Phoenix Hydra Secrets Setup - PowerShell Script
# This script provides a Windows-friendly way to configure Phoenix Hydra secrets

param(
    [switch]$Test,
    [switch]$Export,
    [string]$MasterKey = $env:PHOENIX_MASTER_KEY
)

Write-Host "🔐 Phoenix Hydra Secrets Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not detected." -ForegroundColor Yellow
    $activateVenv = Read-Host "Would you like to activate the virtual environment? [y/N]"
    
    if ($activateVenv -eq 'y' -or $activateVenv -eq 'Y') {
        if (Test-Path "venv\Scripts\Activate.ps1") {
            Write-Host "🔄 Activating virtual environment..." -ForegroundColor Blue
            & "venv\Scripts\Activate.ps1"
        } elseif (Test-Path ".venv\Scripts\Activate.ps1") {
            Write-Host "🔄 Activating virtual environment..." -ForegroundColor Blue
            & ".venv\Scripts\Activate.ps1"
        } else {
            Write-Host "❌ Virtual environment not found. Please create one first." -ForegroundColor Red
            exit 1
        }
    }
}

# Install required dependencies
Write-Host "📦 Installing required dependencies..." -ForegroundColor Blue
try {
    pip install cryptography keyring psutil | Out-Null
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
    exit 1
}

# Set master key if provided
if ($MasterKey) {
    $env:PHOENIX_MASTER_KEY = $MasterKey
    Write-Host "🔑 Master key set from parameter" -ForegroundColor Green
}

# Run the appropriate Python script
try {
    if ($Test) {
        Write-Host "🧪 Testing secrets configuration..." -ForegroundColor Blue
        python -c "from scripts.setup_secrets import test_secrets; test_secrets()"
    } elseif ($Export) {
        Write-Host "📄 Exporting environment file..." -ForegroundColor Blue
        python -c "
from scripts.setup_secrets import SecretsManager
import os
master_key = os.getenv('PHOENIX_MASTER_KEY')
if master_key:
    sm = SecretsManager(master_key=master_key)
    sm.export_environment_file('.env.secrets')
    print('Environment file exported to .env.secrets')
else:
    print('PHOENIX_MASTER_KEY not found in environment')
"
    } else {
        Write-Host "🚀 Starting secrets setup..." -ForegroundColor Blue
        python scripts/setup_secrets.py
    }
    
    Write-Host "✅ Operation completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Operation failed: $_" -ForegroundColor Red
    exit 1
}

# Show usage instructions
if (-not $Test -and -not $Export) {
    Write-Host ""
    Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Set PHOENIX_MASTER_KEY environment variable permanently:"
    Write-Host "   [Environment]::SetEnvironmentVariable('PHOENIX_MASTER_KEY', 'your-master-key', 'User')"
    Write-Host ""
    Write-Host "2. Test your configuration:"
    Write-Host "   .\scripts\setup-secrets.ps1 -Test"
    Write-Host ""
    Write-Host "3. Export environment file for development:"
    Write-Host "   .\scripts\setup-secrets.ps1 -Export"
    Write-Host ""
    Write-Host "4. Start Phoenix Hydra services:"
    Write-Host "   podman-compose -f infra/podman/compose.secrets.yaml up -d"
}

Write-Host ""
Write-Host "🔒 Security Reminders:" -ForegroundColor Yellow
Write-Host "- Never commit .secrets/ directory to version control"
Write-Host "- Keep your master key secure and backed up"
Write-Host "- Use environment variables in production"
Write-Host "- Regularly rotate your credentials"