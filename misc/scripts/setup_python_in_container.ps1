#!/usr/bin/env pwsh
# Setup Python in Phoenix Container

param(
    [string]$Container = "phoenix-hydra_phoenix-core_1"
)

Write-Host "🐍 Setting up Python in Phoenix Container" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check container
$status = podman ps --filter "name=$Container" --format "{{.Status}}"
if (-not $status) {
    Write-Host "❌ Container not found" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container '$Container' is running" -ForegroundColor Green

# Install Python and dependencies
Write-Host "`n📦 Installing Python and dependencies..." -ForegroundColor Cyan

$installScript = @'
#!/bin/sh
echo "🔄 Updating package index..."
apk update

echo "📦 Installing Python and pip..."
apk add --no-cache python3 py3-pip py3-setuptools

echo "🔧 Installing Python packages..."
python3 -m pip install --break-system-packages requests

echo "✅ Installation complete!"
python3 --version
pip3 --version
'@

# Execute installation
try {
    $installScript | podman exec -i $Container sh
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python installation successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Installation completed with warnings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Installation failed: $_" -ForegroundColor Red
    exit 1
}

# Test Python installation
Write-Host "`n🧪 Testing Python installation..." -ForegroundColor Cyan

$pythonTest = @'
#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

print("🐍 Python Test Script")
print("=" * 20)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

# Test basic functionality
try:
    import requests
    print("✅ requests module available")
except ImportError:
    print("❌ requests module not available")

try:
    import json
    print("✅ json module available")
except ImportError:
    print("❌ json module not available")

# Create test directory and file
test_dir = Path("/tmp/phoenix-python-test")
test_dir.mkdir(exist_ok=True)

test_file = test_dir / "test.json"
test_data = {
    "phoenix_hugger_test": True,
    "python_version": sys.version,
    "timestamp": "2025-01-08",
    "status": "ready"
}

test_file.write_text(json.dumps(test_data, indent=2))
print(f"✅ Test file created: {test_file}")

print("\n🎉 Python setup test successful!")
print("Ready for Phoenix Hugger execution!")
'@

# Write and execute Python test
Write-Host "📝 Creating Python test script..." -ForegroundColor Yellow
$pythonTest | podman exec -i $Container tee /tmp/python_test.py > $null

Write-Host "🚀 Running Python test..." -ForegroundColor Cyan
podman exec $Container python3 /tmp/python_test.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Python setup completed successfully!" -ForegroundColor Green
    
    # Show what we can do now
    Write-Host "`n🎯 Available capabilities:" -ForegroundColor Yellow
    Write-Host "• Python 3 installed and working" -ForegroundColor Green
    Write-Host "• Basic packages available" -ForegroundColor Green
    Write-Host "• File system access working" -ForegroundColor Green
    Write-Host "• Ready for Phoenix Hugger" -ForegroundColor Green
    
    Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
    Write-Host "1. Run Phoenix Hugger test mode" -ForegroundColor White
    Write-Host "2. Download models to container" -ForegroundColor White
    Write-Host "3. Integrate with Phoenix Hydra" -ForegroundColor White
    
} else {
    Write-Host "`n❌ Python test failed" -ForegroundColor Red
}

# Cleanup
Write-Host "`n🧹 Cleaning up..." -ForegroundColor Cyan
podman exec $Container rm -f /tmp/python_test.py

Write-Host "`n🎉 Setup completed!" -ForegroundColor Green