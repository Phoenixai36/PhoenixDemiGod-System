# Gap Detector Service

This directory contains the Podman configuration for the gap-detector service, which implements comprehensive gap detection for validating the migration from Transformer to SSM/Mamba architectures and ensuring 100% local processing capabilities.

## Overview

The gap-detector service analyzes the Phoenix Hydra codebase to identify:
- Remaining Transformer implementations that should be converted to SSM/Mamba
- Cloud dependencies that violate local processing requirements
- Energy efficiency gaps and optimization opportunities
- Biomimetic agent system readiness

## Security Features

The Containerfile implements several security best practices:
- **Rootless execution**: Runs as non-root user (appuser:1000)
- **User namespace mapping**: Proper UID/GID mapping for security
- **Minimal privileges**: No unnecessary capabilities or privileges
- **Read-only filesystem**: Application runs with minimal write access
- **Health checks**: Built-in health monitoring

## Build and Run

### Building the Container

```bash
# From project root
podman build -f infra/podman/gap-detector/Containerfile -t phoenix-hydra/gap-detector .
```

### Running the Container

```bash
# Basic run
podman run --rm --name gap-detector \
    -v $(pwd):/app/project:ro \
    -e PROJECT_PATH=/app/project \
    phoenix-hydra/gap-detector

# With custom output paths
podman run --rm --name gap-detector \
    -v $(pwd):/app/project:ro \
    -v $(pwd)/reports:/app/data \
    -e PROJECT_PATH=/app/project \
    -e REPORT_OUTPUT_PATH=/app/data/gap_report.json \
    -e CI_REPORT_OUTPUT_PATH=/app/data/ci_report.json \
    phoenix-hydra/gap-detector
```

### Environment Variables

- `PROJECT_PATH`: Path to the project to analyze (default: '.')
- `REPORT_OUTPUT_PATH`: Path for detailed analysis report (default: '/app/data/gap_detection_report.json')
- `CI_REPORT_OUTPUT_PATH`: Path for CI/CD compatible report (default: '/app/data/ci_gap_report.json')

## Testing

Run the test script to verify the Containerfile works correctly:

```powershell
# Windows PowerShell
.\infra\podman\gap-detector\test_containerfile.ps1

# Skip cleanup for debugging
.\infra\podman\gap-detector\test_containerfile.ps1 -SkipCleanup
```

```bash
# Linux/macOS
./infra/podman/gap-detector/test_containerfile.sh
```

## Output Reports

The service generates two types of reports:

### Detailed Analysis Report
Contains comprehensive analysis including:
- Transformer residuals with file locations and recommendations
- Cloud dependencies that need to be addressed
- Energy efficiency metrics and targets
- Biomimetic system readiness assessment

### CI/CD Report
Simplified report for automated pipelines:
- PASS/FAIL status
- Critical issue count
- Energy reduction percentage
- Summary recommendations

## Integration with Phoenix Hydra

The gap-detector integrates with the Phoenix Hydra event system and can be triggered by:
- Code changes (via file watcher hooks)
- CI/CD pipeline stages
- Manual analysis requests
- Scheduled health checks

## Dependencies

- Python 3.11+
- numpy >= 1.24.0
- torch >= 2.0.0

Dependencies are managed via `requirements-gap-detector.txt` in the project root.