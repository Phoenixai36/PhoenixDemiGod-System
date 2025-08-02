#!/bin/bash
# Test script for the enhanced deployment script

echo "Testing deployment script functionality..."

# Test help functionality
echo "1. Testing help functionality..."
bash deploy.sh --help

echo ""
echo "2. Testing syntax validation..."
bash -n deploy.sh
if [ $? -eq 0 ]; then
    echo "✓ Bash script syntax is valid"
else
    echo "✗ Bash script syntax error"
    exit 1
fi

# Test PowerShell script syntax (if available)
if command -v pwsh &> /dev/null; then
    echo ""
    echo "3. Testing PowerShell script syntax..."
    pwsh -Command "& { . ./deploy.ps1 -Help }" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ PowerShell script syntax is valid"
    else
        echo "✗ PowerShell script syntax error"
    fi
fi

echo ""
echo "4. Testing compose file detection..."
if [ -f "infra/podman/podman-compose.yaml" ]; then
    echo "✓ Podman compose file exists"
else
    echo "✗ Podman compose file not found"
fi

echo ""
echo "Deployment script tests completed!"