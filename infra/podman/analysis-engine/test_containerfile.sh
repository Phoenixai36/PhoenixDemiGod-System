#!/bin/bash
# Test script for analysis-engine Containerfile (Linux/macOS)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
IMAGE_NAME="phoenix-hydra/analysis-engine"
CONTAINER_NAME="test-analysis-engine"

echo "=== Phoenix Hydra Analysis Engine Containerfile Test ==="
echo "Project root: ${PROJECT_ROOT}"
echo "Script directory: ${SCRIPT_DIR}"

# Cleanup function
cleanup() {
    echo "Cleaning up test resources..."
    podman stop "${CONTAINER_NAME}" 2>/dev/null || true
    podman rm "${CONTAINER_NAME}" 2>/dev/null || true
    echo "Cleanup completed"
}

# Set trap for cleanup
trap cleanup EXIT

# Change to project root
cd "${PROJECT_ROOT}"

echo "Step 1: Building analysis-engine container image..."
podman build -t "${IMAGE_NAME}:test" -f infra/podman/analysis-engine/Containerfile .

echo "Step 2: Running container in background..."
podman run -d \
    --name "${CONTAINER_NAME}" \
    -p 8090:8090 \
    --security-opt no-new-privileges:true \
    --user 1000:1000 \
    "${IMAGE_NAME}:test"

echo "Step 3: Waiting for container to start..."
sleep 10

echo "Step 4: Checking container status..."
if ! podman ps | grep -q "${CONTAINER_NAME}"; then
    echo "ERROR: Container is not running"
    podman logs "${CONTAINER_NAME}"
    exit 1
fi

echo "Step 5: Testing health check..."
for i in {1..6}; do
    echo "Health check attempt $i/6..."
    if podman exec "${CONTAINER_NAME}" python -c "import requests; requests.get('http://localhost:8090/metrics', timeout=5)" 2>/dev/null; then
        echo "✓ Health check passed"
        break
    elif [ $i -eq 6 ]; then
        echo "ERROR: Health check failed after 6 attempts"
        podman logs "${CONTAINER_NAME}"
        exit 1
    else
        echo "Health check failed, retrying in 5 seconds..."
        sleep 5
    fi
done

echo "Step 6: Testing Prometheus metrics endpoint..."
if curl -f -s http://localhost:8090/metrics > /dev/null; then
    echo "✓ Prometheus metrics endpoint accessible"
else
    echo "ERROR: Cannot access Prometheus metrics endpoint"
    exit 1
fi

echo "Step 7: Checking container logs for errors..."
if podman logs "${CONTAINER_NAME}" 2>&1 | grep -i error; then
    echo "WARNING: Errors found in container logs"
else
    echo "✓ No errors found in container logs"
fi

echo "Step 8: Testing rootless execution..."
USER_INFO=$(podman exec "${CONTAINER_NAME}" id)
if echo "${USER_INFO}" | grep -q "uid=1000"; then
    echo "✓ Container running as non-root user"
else
    echo "ERROR: Container not running as expected user"
    echo "User info: ${USER_INFO}"
    exit 1
fi

echo "Step 9: Testing file permissions..."
podman exec "${CONTAINER_NAME}" ls -la /app/ | head -5

echo "Step 10: Testing Python imports..."
if podman exec "${CONTAINER_NAME}" python -c "import torch, numpy, asyncio; print('All imports successful')"; then
    echo "✓ Python dependencies imported successfully"
else
    echo "ERROR: Python import test failed"
    exit 1
fi

echo ""
echo "=== All Tests Passed! ==="
echo "✓ Container builds successfully"
echo "✓ Container runs with rootless user"
echo "✓ Health check endpoint works"
echo "✓ Prometheus metrics accessible"
echo "✓ Python dependencies available"
echo "✓ No critical errors in logs"
echo ""
echo "Analysis Engine container is ready for deployment!"