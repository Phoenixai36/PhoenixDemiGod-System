# Enhanced Deployment Script for Podman

This document describes the enhanced deployment script that has been updated for Podman compatibility as part of the Docker-to-Podman migration.

## Overview

The deployment script (`deploy.sh` and `deploy.ps1`) has been completely rewritten to:
- Prioritize Podman over Docker
- Include comprehensive environment checks
- Set up rootless execution environment
- Provide enhanced error handling and user guidance
- Support both Linux/macOS (Bash) and Windows (PowerShell)

## Features

### 1. Podman Installation Verification
- Checks for `podman` and `podman-compose` availability
- Provides installation instructions for different platforms
- Exits gracefully with helpful error messages if tools are missing

### 2. Rootless Environment Setup
- Creates necessary directories in user's home directory
- Sets proper permissions for rootless execution
- Enables systemd lingering (where available)
- Configures container storage locations

### 3. Enhanced Error Handling
- Colored output for better readability
- Comprehensive error messages with solutions
- Graceful handling of interruptions
- Detailed status reporting throughout deployment

### 4. Service Management
- Checks for existing running services
- Offers to restart services if already running
- Builds images before starting services
- Provides deployment verification

### 5. Cross-Platform Support
- `deploy.sh`: Bash script for Linux/macOS/WSL
- `deploy.ps1`: PowerShell script for Windows

## Usage

### Bash Script (Linux/macOS/WSL)
```bash
# Basic deployment
./deploy.sh

# Show help
./deploy.sh --help

# Skip environment checks (use with caution)
./deploy.sh --skip-checks

# Skip deployment verification
./deploy.sh --no-verify
```

### PowerShell Script (Windows)
```powershell
# Basic deployment
.\deploy.ps1

# Show help
.\deploy.ps1 -Help

# Skip environment checks
.\deploy.ps1 -SkipChecks

# Skip deployment verification
.\deploy.ps1 -NoVerify
```

## Directory Structure Created

The script creates the following directory structure for rootless execution:

```
$HOME/.local/share/phoenix-hydra/
├── db_data/          # PostgreSQL data directory
└── logs/             # Application logs

$HOME/.config/containers/  # Podman configuration
```

## Service Verification

After deployment, the script verifies:
- Service status using `podman-compose ps`
- Health endpoints for key services:
  - Gap Detector: http://localhost:8000/health
  - Nginx: http://localhost:8080

## Error Recovery

If deployment fails:
1. Check the error message for specific guidance
2. Verify Podman installation: `podman --version`
3. Check compose file exists: `ls infra/podman/podman-compose.yaml`
4. Review service logs: `podman-compose -f infra/podman/podman-compose.yaml logs`

## Requirements Satisfied

This enhanced deployment script satisfies the following requirements from the migration specification:

- **Requirement 4.1**: Detects and uses podman-compose instead of docker-compose
- **Requirement 4.4**: Provides clear status messages and error handling
- **Requirement 6.1**: Implements rootless environment preparation
- **Requirement 6.2**: Sets up proper user namespace mapping and permissions

## Testing

A test script (`test-deploy.sh`) is provided to verify:
- Script syntax validation
- Help functionality
- Compose file detection
- Cross-platform compatibility

Run tests with:
```bash
bash test-deploy.sh
```

## Migration Notes

### Changes from Original Script
- **Language**: Changed from Spanish to English for consistency
- **Error Handling**: Added comprehensive error checking and recovery guidance
- **Environment Setup**: Added rootless environment preparation
- **Verification**: Added post-deployment health checks
- **Cross-Platform**: Added PowerShell version for Windows users
- **User Experience**: Added colored output and progress indicators

### Backward Compatibility
The script maintains the same basic functionality as the original but with enhanced features. The original simple usage (`./deploy.sh`) still works without any additional parameters.

## Troubleshooting

### Common Issues

1. **"podman-compose not found"**
   - Install with: `pip install podman-compose`

2. **Permission denied errors**
   - Ensure script is executable: `chmod +x deploy.sh`
   - Check rootless setup completed successfully

3. **Services fail to start**
   - Check logs: `podman-compose -f infra/podman/podman-compose.yaml logs`
   - Verify all Containerfiles are present
   - Ensure no port conflicts with existing services

4. **Network connectivity issues**
   - Verify Podman network configuration
   - Check firewall settings
   - Ensure no conflicting Docker networks

For additional support, refer to the main Phoenix Hydra documentation or the Podman migration guide.