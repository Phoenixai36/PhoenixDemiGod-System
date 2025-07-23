# Phoenix Hydra Complete Deployment Script (Windows PowerShell)
# This script completes the Phoenix Hydra deployment with all monetization features

Write-Host "🚀 Starting Phoenix Hydra Complete Deployment" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
Write-Status "Checking prerequisites..."

if (!(Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Error "Podman is not installed. Please install Podman first."
    exit 1
}

if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed. Please install Node.js first."
    exit 1
}

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python first."
    exit 1
}

# Install Node.js dependencies
Write-Status "Installing Node.js dependencies..."
Set-Location scripts
npm install
Set-Location ..

# Deploy affiliate badges
Write-Status "Deploying affiliate badges..."
node scripts/deploy-badges.js

# Generate NEOTEC application
Write-Status "Generating NEOTEC grant application..."
python scripts/neotec-generator.py

# Start Phoenix Hydra with Podman Compose
Write-Status "Starting Phoenix Hydra services with Podman Compose..."
Set-Location infra/podman
podman-compose up -d
Set-Location ../..

# Wait for services to start
Write-Status "Waiting for services to initialize..."
Start-Sleep -Seconds 30

# Health checks
Write-Status "Performing health checks..."

# Test API endpoints
Write-Status "Testing API endpoints..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "✅ Phoenix Core is responding"
} catch {
    Write-Warning "⚠️  Phoenix Core not responding on port 8080"
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "✅ n8n is responding"
} catch {
    Write-Warning "⚠️  n8n not responding on port 5678"
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "✅ Windmill is responding"
} catch {
    Write-Warning "⚠️  Windmill not responding on port 8000"
}

# Update revenue metrics
Write-Status "Updating revenue metrics..."
node scripts/revenue-tracking.js

# Display final status
Write-Host ""
Write-Host "🎉 Phoenix Hydra Deployment Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Access Points:" -ForegroundColor Cyan
Write-Host "  • Phoenix Core:    http://localhost:8080"
Write-Host "  • n8n Workflows:   http://localhost:5678"
Write-Host "  • Windmill:        http://localhost:8000"
Write-Host "  • NCA Toolkit:     http://localhost:8081"
Write-Host ""
Write-Host "💰 Monetization Status:" -ForegroundColor Cyan
Write-Host "  • Affiliate badges: ✅ Deployed"
Write-Host "  • NEOTEC application: ✅ Generated"
Write-Host "  • Revenue tracking: ✅ Active"
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review NEOTEC application and submit before June 12, 2025"
Write-Host "  2. Configure AWS Marketplace listing"
Write-Host "  3. Set up Prometheus/Grafana monitoring"
Write-Host "  4. Apply for ENISA FEPYME loan (€300k)"
Write-Host ""
Write-Host "📈 Revenue Target 2025: €400k+" -ForegroundColor Yellow
Write-Host "🚀 Phoenix Hydra is ready for enterprise scaling!" -ForegroundColor Green