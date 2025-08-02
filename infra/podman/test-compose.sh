#!/bin/bash

# Test script for Podman compose configuration
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/podman-compose.yaml"

echo "Testing Podman compose configuration..."

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo "Error: podman-compose is not installed"
    echo "Install with: pip install podman-compose"
    exit 1
fi

# Validate compose file syntax
echo "Validating compose file syntax..."
if podman-compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
    echo "✓ Compose file syntax is valid"
else
    echo "✗ Compose file syntax validation failed"
    podman-compose -f "$COMPOSE_FILE" config
    exit 1
fi

# Check if required directories exist
echo "Checking required directories..."
if [ ! -d "${HOME}/.local/share/phoenix-hydra" ]; then
    echo "Creating Phoenix Hydra data directory..."
    mkdir -p "${HOME}/.local/share/phoenix-hydra/db_data"
    chmod 755 "${HOME}/.local/share/phoenix-hydra"
    chmod 700 "${HOME}/.local/share/phoenix-hydra/db_data"
    echo "✓ Created data directories"
fi

# Test network creation (dry run)
echo "Testing network configuration..."
if podman network exists phoenix-net 2>/dev/null; then
    echo "✓ Phoenix network already exists"
else
    echo "ℹ Phoenix network will be created on first run"
fi

echo "✓ All tests passed! Compose configuration is ready."
echo ""
echo "To start the services:"
echo "  cd ${SCRIPT_DIR}"
echo "  podman-compose -f podman-compose.yaml up -d"
echo ""
echo "To check service status:"
echo "  podman-compose -f podman-compose.yaml ps"