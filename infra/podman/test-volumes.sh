#!/bin/bash
set -euo pipefail

# Phoenix Hydra Podman Volume Test Script
# This script validates that volumes are properly configured

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_DATA_DIR="${HOME}/.local/share/phoenix-hydra"

echo "🧪 Testing Phoenix Hydra Podman volumes..."

# Test 1: Check if volume directories exist
echo "Test 1: Checking volume directory structure..."
REQUIRED_DIRS=(
    "${PHOENIX_DATA_DIR}"
    "${PHOENIX_DATA_DIR}/db_data"
    "${PHOENIX_DATA_DIR}/nginx_config"
    "${PHOENIX_DATA_DIR}/logs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ Directory exists: $dir"
    else
        echo "  ❌ Directory missing: $dir"
        exit 1
    fi
done

# Test 2: Check permissions
echo ""
echo "Test 2: Checking directory permissions..."

# Check db_data permissions (should be 700)
DB_PERMS=$(stat -c "%a" "${PHOENIX_DATA_DIR}/db_data" 2>/dev/null || echo "unknown")
if [ "$DB_PERMS" = "700" ]; then
    echo "  ✅ db_data permissions correct: $DB_PERMS"
else
    echo "  ⚠️  db_data permissions: $DB_PERMS (expected: 700)"
fi

# Check nginx_config permissions (should be 755)
NGINX_PERMS=$(stat -c "%a" "${PHOENIX_DATA_DIR}/nginx_config" 2>/dev/null || echo "unknown")
if [ "$NGINX_PERMS" = "755" ]; then
    echo "  ✅ nginx_config permissions correct: $NGINX_PERMS"
else
    echo "  ⚠️  nginx_config permissions: $NGINX_PERMS (expected: 755)"
fi

# Test 3: Check nginx configuration file
echo ""
echo "Test 3: Checking nginx configuration..."
NGINX_CONFIG_FILE="${PHOENIX_DATA_DIR}/nginx_config/default.conf"
if [ -f "$NGINX_CONFIG_FILE" ]; then
    echo "  ✅ Nginx config file exists: $NGINX_CONFIG_FILE"
    
    # Check if config file is readable
    if [ -r "$NGINX_CONFIG_FILE" ]; then
        echo "  ✅ Nginx config file is readable"
        
        # Check for basic nginx directives
        if grep -q "listen 8080" "$NGINX_CONFIG_FILE"; then
            echo "  ✅ Nginx config contains listen directive"
        else
            echo "  ⚠️  Nginx config missing listen directive"
        fi
        
        if grep -q "location /health" "$NGINX_CONFIG_FILE"; then
            echo "  ✅ Nginx config contains health check endpoint"
        else
            echo "  ⚠️  Nginx config missing health check endpoint"
        fi
    else
        echo "  ❌ Nginx config file is not readable"
        exit 1
    fi
else
    echo "  ❌ Nginx config file missing: $NGINX_CONFIG_FILE"
    exit 1
fi

# Test 4: Check ownership
echo ""
echo "Test 4: Checking file ownership..."
CURRENT_USER=$(id -u)
CURRENT_GROUP=$(id -g)

for dir in "${REQUIRED_DIRS[@]}"; do
    OWNER=$(stat -c "%u:%g" "$dir" 2>/dev/null || echo "unknown")
    if [ "$OWNER" = "${CURRENT_USER}:${CURRENT_GROUP}" ]; then
        echo "  ✅ Correct ownership for $(basename "$dir"): $OWNER"
    else
        echo "  ⚠️  Ownership for $(basename "$dir"): $OWNER (expected: ${CURRENT_USER}:${CURRENT_GROUP})"
    fi
done

# Test 5: Test write permissions
echo ""
echo "Test 5: Testing write permissions..."

# Test db_data write permission
TEST_FILE="${PHOENIX_DATA_DIR}/db_data/.test_write"
if touch "$TEST_FILE" 2>/dev/null; then
    echo "  ✅ db_data directory is writable"
    rm -f "$TEST_FILE"
else
    echo "  ❌ db_data directory is not writable"
    exit 1
fi

# Test logs write permission
TEST_FILE="${PHOENIX_DATA_DIR}/logs/.test_write"
if touch "$TEST_FILE" 2>/dev/null; then
    echo "  ✅ logs directory is writable"
    rm -f "$TEST_FILE"
else
    echo "  ❌ logs directory is not writable"
    exit 1
fi

echo ""
echo "🎉 All volume tests passed!"
echo ""
echo "Volume summary:"
echo "  - Database data: ${PHOENIX_DATA_DIR}/db_data ($(stat -c "%a" "${PHOENIX_DATA_DIR}/db_data"))"
echo "  - Nginx config: ${PHOENIX_DATA_DIR}/nginx_config ($(stat -c "%a" "${PHOENIX_DATA_DIR}/nginx_config"))"
echo "  - Logs: ${PHOENIX_DATA_DIR}/logs ($(stat -c "%a" "${PHOENIX_DATA_DIR}/logs"))"
echo ""
echo "Ready for Podman deployment!"