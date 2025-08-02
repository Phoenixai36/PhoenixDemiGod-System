#!/bin/bash
set -euo pipefail

# Phoenix Hydra Podman Volume Cleanup Script
# This script removes volume directories and data (use with caution!)

PHOENIX_DATA_DIR="${HOME}/.local/share/phoenix-hydra"

echo "⚠️  Phoenix Hydra Volume Cleanup"
echo "This will remove all volume data including:"
echo "  - Database data: ${PHOENIX_DATA_DIR}/db_data"
echo "  - Nginx config: ${PHOENIX_DATA_DIR}/nginx_config"
echo "  - Logs: ${PHOENIX_DATA_DIR}/logs"
echo ""

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo "Stopping any running containers..."
podman-compose -f "$(dirname "$0")/podman-compose.yaml" down 2>/dev/null || true

echo "Removing volume directories..."
if [ -d "${PHOENIX_DATA_DIR}" ]; then
    rm -rf "${PHOENIX_DATA_DIR}/db_data"
    rm -rf "${PHOENIX_DATA_DIR}/nginx_config"
    rm -rf "${PHOENIX_DATA_DIR}/logs"
    
    # Remove parent directory if empty
    rmdir "${PHOENIX_DATA_DIR}" 2>/dev/null || true
    
    echo "✅ Volume directories removed successfully!"
else
    echo "Volume directory does not exist: ${PHOENIX_DATA_DIR}"
fi

echo "Cleanup complete."