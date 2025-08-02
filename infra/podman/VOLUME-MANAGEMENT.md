# Phoenix Hydra Podman Volume Management

This document describes the volume management system for Phoenix Hydra's Podman-based container infrastructure.

## Overview

Phoenix Hydra uses persistent volumes to store:
- **Database data** (`db_data`): PostgreSQL data files
- **Nginx configuration** (`nginx_config`): Web server configuration files
- **Logs** (`logs`): Application and container logs

All volumes are configured for rootless Podman execution with proper user namespace mapping.

## Volume Configuration

### Volume Definitions

The volumes are defined in `podman-compose.yaml`:

```yaml
volumes:
  db_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${HOME}/.local/share/phoenix-hydra/db_data
  nginx_config:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${HOME}/.local/share/phoenix-hydra/nginx_config
```

### Directory Structure

```
${HOME}/.local/share/phoenix-hydra/
├── db_data/          # PostgreSQL data (permissions: 700)
├── nginx_config/     # Nginx configuration (permissions: 755)
│   └── default.conf  # Main nginx configuration file
└── logs/             # Application logs (permissions: 755)
```

## Setup and Management

### Initial Setup

**Linux/macOS:**
```bash
cd infra/podman
./setup-volumes.sh
```

**Windows:**
```powershell
cd infra/podman
.\setup-volumes.ps1
```

### Testing Volume Configuration

**Linux/macOS:**
```bash
./test-volumes.sh
```

**Windows:**
```powershell
.\test-volumes.ps1
```

### Cleanup (⚠️ Destructive)

**Linux/macOS:**
```bash
./cleanup-volumes.sh
```

**Windows:**
```powershell
.\cleanup-volumes.ps1
```

## Volume Details

### Database Volume (`db_data`)

- **Purpose**: Stores PostgreSQL database files
- **Container Path**: `/var/lib/postgresql/data`
- **Host Path**: `${HOME}/.local/share/phoenix-hydra/db_data`
- **Permissions**: `700` (owner read/write/execute only)
- **Container User**: `999:999` (postgres user)
- **SELinux Context**: `:Z` (private unshared)

**Configuration in compose:**
```yaml
db:
  volumes:
    - db_data:/var/lib/postgresql/data:Z
  user: "999:999"
```

### Nginx Configuration Volume (`nginx_config`)

- **Purpose**: Stores nginx configuration files
- **Container Path**: `/etc/nginx/conf.d`
- **Host Path**: `${HOME}/.local/share/phoenix-hydra/nginx_config`
- **Permissions**: `755` (owner full, group/other read/execute)
- **Container User**: `101:101` (nginx user)
- **SELinux Context**: `:ro,Z` (read-only, private unshared)

**Configuration in compose:**
```yaml
nginx:
  volumes:
    - nginx_config:/etc/nginx/conf.d:ro,Z
  user: "101:101"
```

## Rootless Considerations

### User Namespace Mapping

In rootless Podman:
- Container user IDs are mapped to host user namespace
- Host directories must be owned by the current user
- Podman handles the mapping between host and container users automatically

### Permission Strategy

1. **Host Level**: All directories owned by current user (`$(id -u):$(id -g)`)
2. **Container Level**: Services run as specific users (postgres: 999, nginx: 101)
3. **Mapping**: Podman maps container users to host user namespace ranges

### SELinux Labels

- `:Z` - Private unshared label (recommended for data volumes)
- `:z` - Shared label (use with caution)
- `:ro` - Read-only mount

## Troubleshooting

### Common Issues

#### Permission Denied Errors

**Symptoms:**
```
Error: mounting volume: permission denied
```

**Solutions:**
1. Ensure directories are owned by current user:
   ```bash
   chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra
   ```

2. Check SELinux context (if enabled):
   ```bash
   ls -Z ~/.local/share/phoenix-hydra
   ```

3. Verify directory permissions:
   ```bash
   ls -la ~/.local/share/phoenix-hydra
   ```

#### Database Initialization Failures

**Symptoms:**
```
initdb: could not create directory "/var/lib/postgresql/data": Permission denied
```

**Solutions:**
1. Ensure `db_data` directory has correct permissions (700)
2. Verify the directory is empty for initial setup
3. Check that the directory is writable by the current user

#### Nginx Configuration Not Loading

**Symptoms:**
```
nginx: [emerg] open() "/etc/nginx/conf.d/default.conf" failed
```

**Solutions:**
1. Verify nginx config file exists in volume directory
2. Check file permissions (should be readable)
3. Validate nginx configuration syntax:
   ```bash
   podman run --rm -v nginx_config:/etc/nginx/conf.d:ro nginx:alpine nginx -t
   ```

### Diagnostic Commands

**Check volume mounts:**
```bash
podman inspect <container_name> | jq '.[0].Mounts'
```

**List volumes:**
```bash
podman volume ls
```

**Inspect volume:**
```bash
podman volume inspect <volume_name>
```

**Check container user mapping:**
```bash
podman exec <container_name> id
```

## Backup and Recovery

### Backup Volumes

**Database backup:**
```bash
# Create database dump
podman exec phoenix-hydra_db_1 pg_dump -U windmill_user windmill > backup.sql

# Or backup entire data directory
tar -czf db_backup.tar.gz -C ~/.local/share/phoenix-hydra db_data
```

**Configuration backup:**
```bash
tar -czf config_backup.tar.gz -C ~/.local/share/phoenix-hydra nginx_config
```

### Restore Volumes

**Database restore:**
```bash
# From SQL dump
podman exec -i phoenix-hydra_db_1 psql -U windmill_user windmill < backup.sql

# From directory backup
tar -xzf db_backup.tar.gz -C ~/.local/share/phoenix-hydra
```

**Configuration restore:**
```bash
tar -xzf config_backup.tar.gz -C ~/.local/share/phoenix-hydra
```

## Security Considerations

### Access Control

- Volumes are only accessible to the current user
- Database directory has restrictive permissions (700)
- Configuration files are read-only in containers
- No privileged access required

### Data Protection

- All data stored locally (no cloud dependencies)
- Proper file permissions prevent unauthorized access
- SELinux labels provide additional isolation
- Regular backups recommended for critical data

### Network Isolation

- Volumes are not exposed to external networks
- Container-to-container communication only within phoenix-net
- No external volume mounts from untrusted sources

## Performance Optimization

### I/O Performance

- Use local storage for best performance
- Avoid network-mounted volumes for database
- Consider SSD storage for database volumes
- Monitor disk space usage regularly

### Volume Sizing

- **Database**: Plan for data growth (recommend 10GB+ free space)
- **Logs**: Implement log rotation to prevent disk fill
- **Config**: Minimal space required (< 100MB)

### Monitoring

Monitor volume usage:
```bash
# Check disk usage
df -h ~/.local/share/phoenix-hydra

# Check directory sizes
du -sh ~/.local/share/phoenix-hydra/*

# Monitor in real-time
watch -n 5 'df -h ~/.local/share/phoenix-hydra'
```

## Integration with Phoenix Hydra

### Event System Integration

Volume events can trigger Phoenix Hydra hooks:
- Database backup completion
- Configuration file changes
- Disk space alerts
- Volume mount/unmount events

### Monitoring Integration

Volume metrics are collected for:
- Disk usage tracking
- I/O performance monitoring
- Access pattern analysis
- Backup status verification

### Automation Integration

Volume management integrates with:
- Automated backup scripts
- Configuration deployment pipelines
- Health check systems
- Alert notification systems

This volume management system ensures reliable, secure, and performant storage for the Phoenix Hydra container infrastructure while maintaining rootless operation and following security best practices.