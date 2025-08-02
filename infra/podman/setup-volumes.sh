#!/bin/bash
set -euo pipefail

# Phoenix Hydra Podman Volume Setup Script
# This script creates and configures volumes with proper rootless permissions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_DATA_DIR="${HOME}/.local/share/phoenix-hydra"
NGINX_CONFIG_SOURCE="${SCRIPT_DIR}/nginx"

echo "Setting up Phoenix Hydra Podman volumes..."

# Create base directory structure
echo "Creating base directories..."
mkdir -p "${PHOENIX_DATA_DIR}"
mkdir -p "${PHOENIX_DATA_DIR}/db_data"
mkdir -p "${PHOENIX_DATA_DIR}/nginx_config"
mkdir -p "${PHOENIX_DATA_DIR}/logs"

# Set proper permissions for db_data volume
echo "Setting up db_data volume permissions..."
chmod 755 "${PHOENIX_DATA_DIR}"
chmod 700 "${PHOENIX_DATA_DIR}/db_data"

# PostgreSQL requires specific ownership for data directory
# In rootless mode, we need to ensure the directory is writable by the postgres user (999:999)
# Since we're running rootless, we'll set it to be writable by the current user
# and let Podman handle the user namespace mapping
chown -R $(id -u):$(id -g) "${PHOENIX_DATA_DIR}/db_data"

echo "Setting up nginx_config volume..."
# Copy nginx configuration files to the volume directory
if [ -f "${NGINX_CONFIG_SOURCE}/nginx.conf" ]; then
    cp "${NGINX_CONFIG_SOURCE}/nginx.conf" "${PHOENIX_DATA_DIR}/nginx_config/default.conf"
    echo "Copied nginx.conf to volume directory"
else
    echo "Warning: nginx.conf not found at ${NGINX_CONFIG_SOURCE}/nginx.conf"
fi

# Set proper permissions for nginx config volume
# nginx runs as user 101:101 in the container, but in rootless mode
# we need to ensure the files are readable by the mapped user
chmod 755 "${PHOENIX_DATA_DIR}/nginx_config"
chmod 644 "${PHOENIX_DATA_DIR}/nginx_config"/*.conf 2>/dev/null || true
chown -R $(id -u):$(id -g) "${PHOENIX_DATA_DIR}/nginx_config"

# Create logs directory with proper permissions
echo "Setting up logs directory..."
chmod 755 "${PHOENIX_DATA_DIR}/logs"
chown -R $(id -u):$(id -g) "${PHOENIX_DATA_DIR}/logs"

# Verify directory structure
echo "Volume setup complete. Directory structure:"
ls -la "${PHOENIX_DATA_DIR}"
echo ""
echo "db_data permissions:"
ls -la "${PHOENIX_DATA_DIR}/db_data"
echo ""
echo "nginx_config permissions:"
ls -la "${PHOENIX_DATA_DIR}/nginx_config"

echo "✅ Phoenix Hydra volumes configured successfully!"
echo ""
echo "Volume locations:"
echo "  - Database data: ${PHOENIX_DATA_DIR}/db_data"
echo "  - Nginx config: ${PHOENIX_DATA_DIR}/nginx_config"
echo "  - Logs: ${PHOENIX_DATA_DIR}/logs"
echo ""
echo "Note: In rootless Podman, user namespace mapping will handle"
echo "      container user permissions automatically."