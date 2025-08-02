#!/bin/bash

# Test script for gap-detector Containerfile
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "Testing gap-detector Containerfile..."
echo "Project root: ${PROJECT_ROOT}"

# Change to project root for build context
cd "${PROJECT_ROOT}"

# Build the container image
echo "Building gap-detector container image..."
podman build -f infra/podman/gap-detector/Containerfile -t phoenix-hydra/gap-detector:test .

# Test that the image was built successfully
echo "Verifying image was built..."
podman images | grep phoenix-hydra/gap-detector

# Test running the container (dry run)
echo "Testing container execution (dry run)..."
podman run --rm --name gap-detector-test \
    -e PROJECT_PATH=/app \
    -e REPORT_OUTPUT_PATH=/app/data/test_report.json \
    -e CI_REPORT_OUTPUT_PATH=/app/data/test_ci_report.json \
    --user 1000:1000 \
    phoenix-hydra/gap-detector:test python -c "print('Container runs successfully')"

echo "Gap-detector Containerfile test completed successfully!"

# Clean up test image
echo "Cleaning up test image..."
podman rmi phoenix-hydra/gap-detector:test

echo "Test cleanup completed."