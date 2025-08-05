# Phoenix Hydra Rollback Mechanism

This document describes the comprehensive rollback mechanism implemented for the Phoenix Hydra Docker-to-Podman migration. The rollback system provides multiple recovery options and automated procedures to handle various failure scenarios.

## Overview

The rollback mechanism consists of four main components:

1. **Backup System** - Creates comprehensive backups of Docker configuration
2. **Validation System** - Validates prerequisites before migration
3. **Recovery System** - Provides targeted recovery for specific failure scenarios
4. **Rollback System** - Performs complete rollback to Docker configuration

## Components

### 1. Backup System (`scripts/backup-docker-config.sh`)

Creates a comprehensive backup of the current Docker configuration before migration.

#### Features:
- Backs up all Docker configuration files
- Preserves Dockerfiles and compose configurations
- Optionally includes Docker volume data
- Creates integrity verification manifest
- Provides detailed backup reporting

#### Usage:
```bash
# Basic backup
./scripts/backup-docker-config.sh

# Include Docker volume data
./scripts/backup-docker-config.sh --include-data

# Force overwrite existing backup
./scripts/backup-docker-config.sh --force

# Verify what would be backed up
./scripts/backup-docker-config.sh --verify-only
```

#### Backup Contents:
- `compose.yaml` - Main Docker Compose configuration
- `compose/` directory - All Dockerfiles and configurations
- `deploy.sh`, `teardown.sh`, `verify.sh` - Deployment scripts
- `requirements*.txt` - Python dependency files
- `compose/nginx/nginx.conf` - Nginx configuration
- Optional: Docker volume data

### 2. Validation System (`scripts/validate-migration-prerequisites.sh`)

Validates that all prerequisites are met before attempting migration.

#### Validation Categories:
- **System Requirements** - OS, memory, disk space
- **Docker Configuration** - Installation, daemon status, services
- **Podman Installation** - Podman, podman-compose, rootless setup
- **File System Permissions** - Directory access, user namespaces
- **Network Requirements** - Port availability, network namespaces
- **Security Requirements** - Non-root execution, SELinux/AppArmor
- **Backup Requirements** - Backup script availability, disk space

#### Usage:
```bash
# Full validation
./scripts/validate-migration-prerequisites.sh

# Attempt automatic fixes
./scripts/validate-migration-prerequisites.sh --fix-issues

# Export validation report
./scripts/validate-migration-prerequisites.sh --export-report

# Verify prerequisites only
./scripts/validate-migration-prerequisites.sh --verify-only
```

#### Validation Results:
- ✅ **READY** - All prerequisites met, migration can proceed
- 🟡 **READY WITH WARNINGS** - Migration possible but review warnings
- 🔴 **NOT READY** - Critical issues must be resolved first

### 3. Recovery System (`scripts/migration-recovery.sh`)

Provides targeted recovery procedures for specific failure scenarios.

#### Recovery Scenarios:

##### Failed Build Recovery
- Cleans up failed build artifacts
- Validates Containerfile syntax
- Attempts individual service builds
- Provides detailed error diagnosis

```bash
./scripts/migration-recovery.sh failed-build
```

##### Failed Startup Recovery
- Stops all services cleanly
- Checks for port conflicts
- Verifies service dependencies
- Starts services in correct order

```bash
./scripts/migration-recovery.sh failed-startup
```

##### Network Issues Recovery
- Removes and recreates networks
- Tests network connectivity
- Verifies DNS resolution
- Restarts services with new network

```bash
./scripts/migration-recovery.sh network-issues
```

##### Volume Issues Recovery
- Fixes directory permissions
- Sets SELinux contexts if needed
- Tests volume mounting
- Recreates volumes in compose

```bash
./scripts/migration-recovery.sh volume-issues
```

##### Permission Issues Recovery
- Checks user namespace mapping
- Resets Podman configuration
- Creates proper containers.conf
- Restarts Podman system

```bash
./scripts/migration-recovery.sh permission-issues
```

##### System Diagnosis
- Analyzes current system state
- Checks Docker and Podman status
- Verifies configuration files
- Reports network and data status

```bash
./scripts/migration-recovery.sh diagnose
```

### 4. Rollback System (`scripts/rollback-to-docker.sh`)

Performs complete rollback from Podman to Docker configuration.

#### Rollback Process:
1. **Stop Podman Services** - Cleanly stops all Podman containers and networks
2. **Backup Podman Data** - Optionally preserves Podman data for migration
3. **Restore Docker Config** - Restores all Docker files from backup
4. **Migrate Data Volumes** - Transfers data from Podman to Docker volumes
5. **Start Docker Services** - Builds and starts Docker services
6. **Verify Rollback** - Tests all services and endpoints
7. **Cleanup Artifacts** - Optionally removes Podman configuration

#### Usage:
```bash
# Interactive rollback
./scripts/rollback-to-docker.sh

# Force rollback without confirmation
./scripts/rollback-to-docker.sh --force

# Keep and migrate data volumes
./scripts/rollback-to-docker.sh --keep-data

# Verify rollback prerequisites only
./scripts/rollback-to-docker.sh --verify-only
```

#### PowerShell Version (`scripts/rollback-to-docker.ps1`)
Windows-compatible PowerShell version with identical functionality:

```powershell
# Interactive rollback
.\scripts\rollback-to-docker.ps1

# Force rollback with data migration
.\scripts\rollback-to-docker.ps1 -Force -KeepData
```

## Failure Scenarios and Recovery

### Scenario 1: Container Build Failures

**Symptoms:**
- Podman build commands fail
- Missing dependencies or syntax errors
- Image creation errors

**Recovery:**
```bash
# Diagnose the issue
./scripts/migration-recovery.sh diagnose

# Attempt build recovery
./scripts/migration-recovery.sh failed-build

# If recovery fails, rollback
./scripts/rollback-to-docker.sh --keep-data
```

### Scenario 2: Service Startup Failures

**Symptoms:**
- Services fail to start
- Port conflicts
- Dependency issues

**Recovery:**
```bash
# Attempt startup recovery
./scripts/migration-recovery.sh failed-startup

# Check for port conflicts
netstat -tuln | grep -E ':(8000|3000|8080|5000)'

# If recovery fails, rollback
./scripts/rollback-to-docker.sh
```

### Scenario 3: Network Connectivity Issues

**Symptoms:**
- Services can't communicate
- DNS resolution failures
- Network isolation problems

**Recovery:**
```bash
# Recover network configuration
./scripts/migration-recovery.sh network-issues

# Test network connectivity
podman network ls
podman run --rm --network phoenix-hydra_phoenix-net alpine:latest ping -c 1 172.20.0.1
```

### Scenario 4: Volume Mounting Problems

**Symptoms:**
- Data persistence failures
- Permission denied errors
- Volume mounting failures

**Recovery:**
```bash
# Fix volume issues
./scripts/migration-recovery.sh volume-issues

# Check directory permissions
ls -la ~/.local/share/phoenix-hydra/
```

### Scenario 5: Permission and Security Issues

**Symptoms:**
- Rootless execution failures
- User namespace mapping errors
- SELinux/AppArmor conflicts

**Recovery:**
```bash
# Fix permission issues
./scripts/migration-recovery.sh permission-issues

# Check user namespace mapping
grep "$(whoami)" /etc/subuid /etc/subgid
```

### Scenario 6: Complete Migration Failure

**Symptoms:**
- Multiple systems failing
- Unrecoverable errors
- Need to revert completely

**Recovery:**
```bash
# Complete rollback to Docker
./scripts/rollback-to-docker.sh --force --keep-data
```

## Best Practices

### Before Migration

1. **Create Backup:**
   ```bash
   ./scripts/backup-docker-config.sh --include-data
   ```

2. **Validate Prerequisites:**
   ```bash
   ./scripts/validate-migration-prerequisites.sh --export-report
   ```

3. **Test in Development:**
   - Run migration in a test environment first
   - Verify all services work correctly
   - Test rollback procedures

### During Migration

1. **Monitor Closely:**
   - Watch for error messages
   - Check service logs regularly
   - Verify network connectivity

2. **Use Recovery Scripts:**
   - Don't manually fix issues
   - Use provided recovery scripts
   - Document any custom fixes

### After Migration Issues

1. **Diagnose First:**
   ```bash
   ./scripts/migration-recovery.sh diagnose
   ```

2. **Use Targeted Recovery:**
   - Identify specific failure scenario
   - Use appropriate recovery script
   - Verify fix before proceeding

3. **Rollback if Necessary:**
   - Don't hesitate to rollback
   - Preserve data when possible
   - Document lessons learned

## Troubleshooting

### Common Issues

#### "Prerequisites not met" Error
```bash
# Check what's missing
./scripts/validate-migration-prerequisites.sh --detailed

# Attempt automatic fixes
./scripts/validate-migration-prerequisites.sh --fix-issues
```

#### "Backup directory not found" Error
```bash
# Create backup first
./scripts/backup-docker-config.sh

# Then retry rollback
./scripts/rollback-to-docker.sh
```

#### "Podman services won't stop" Error
```bash
# Force stop all containers
podman stop $(podman ps -q) || true
podman rm $(podman ps -aq) || true

# Remove networks
podman network prune -f
```

#### "Docker services won't start" Error
```bash
# Check Docker daemon
docker info

# Check port conflicts
netstat -tuln | grep -E ':(8000|3000|8080)'

# Check compose file syntax
docker-compose config
```

### Log Files

- **Recovery Log:** `migration-recovery.log`
- **Backup Manifest:** `.docker-backup/backup-manifest.txt`
- **Validation Report:** `migration-prerequisites-report.txt`

### Getting Help

1. **Check Logs:** Review all log files for error details
2. **Run Diagnosis:** Use `migration-recovery.sh diagnose`
3. **Consult Documentation:** Review this document and related docs
4. **Use Recovery Scripts:** Don't attempt manual fixes first

## Security Considerations

### Backup Security
- Backups contain configuration files (no secrets)
- Volume data may contain sensitive information
- Store backups securely and limit access

### Rollback Security
- Rollback preserves original security posture
- Docker configuration restored exactly as backed up
- No privilege escalation during rollback

### Recovery Security
- All recovery operations run as non-root user
- No modification of system-level configurations
- Respects existing security boundaries

## Testing the Rollback Mechanism

### Test Scenarios

1. **Backup and Restore Test:**
   ```bash
   # Create backup
   ./scripts/backup-docker-config.sh --include-data
   
   # Simulate migration
   mv compose.yaml compose.yaml.bak
   
   # Test rollback
   ./scripts/rollback-to-docker.sh --force
   
   # Verify restoration
   diff compose.yaml.bak compose.yaml
   ```

2. **Prerequisites Validation Test:**
   ```bash
   # Test with missing dependencies
   sudo apt remove podman
   ./scripts/validate-migration-prerequisites.sh
   
   # Test automatic fixes
   ./scripts/validate-migration-prerequisites.sh --fix-issues
   ```

3. **Recovery Scenarios Test:**
   ```bash
   # Test each recovery scenario
   ./scripts/migration-recovery.sh diagnose
   ./scripts/migration-recovery.sh failed-build
   ./scripts/migration-recovery.sh network-issues
   ```

## Maintenance

### Regular Tasks

1. **Update Scripts:** Keep rollback scripts updated with system changes
2. **Test Procedures:** Regularly test rollback procedures
3. **Review Logs:** Monitor recovery logs for patterns
4. **Update Documentation:** Keep this document current

### Version Compatibility

- Scripts are compatible with Docker 20.10+
- Podman 3.0+ support for all features
- PowerShell 5.1+ for Windows scripts
- Bash 4.0+ for Linux scripts

This rollback mechanism provides comprehensive protection against migration failures and ensures that Phoenix Hydra can always be restored to a working Docker configuration.