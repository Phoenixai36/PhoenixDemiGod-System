#!/bin/bash
# Test script for RUBIK Agent Containerfile

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "🧬 Testing RUBIK Agent Containerfile"
echo "=================================="

# Build the container image
echo "Building RUBIK Agent container image..."
cd "${PROJECT_ROOT}"

podman build \
    -f infra/podman/rubik-agent/Containerfile \
    -t phoenix-hydra/rubik-agent:test \
    .

echo "✅ Container image built successfully"

# Test the container
echo "Testing container startup..."
CONTAINER_ID=$(podman run -d \
    --name rubik-agent-test \
    -p 8080:8080 \
    phoenix-hydra/rubik-agent:test)

echo "Container started with ID: ${CONTAINER_ID}"

# Wait for service to start
echo "Waiting for service to start..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    podman logs rubik-agent-test
    exit 1
fi

# Test status endpoint
echo "Testing status endpoint..."
if curl -f http://localhost:8080/status > /dev/null 2>&1; then
    echo "✅ Status endpoint working"
else
    echo "❌ Status endpoint failed"
fi

# Test agents endpoint
echo "Testing agents endpoint..."
if curl -f http://localhost:8080/agents > /dev/null 2>&1; then
    echo "✅ Agents endpoint working"
else
    echo "❌ Agents endpoint failed"
fi

# Show container logs
echo "Container logs:"
podman logs rubik-agent-test | tail -10

# Cleanup
echo "Cleaning up test container..."
podman stop rubik-agent-test
podman rm rubik-agent-test

echo "🎉 RUBIK Agent Containerfile test completed successfully!"