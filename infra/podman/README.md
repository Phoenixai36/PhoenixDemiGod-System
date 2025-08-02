# Phoenix Hydra Podman Compose Configuration

This directory contains the Podman-compatible compose configuration for the Phoenix Hydra system, providing rootless container execution with improved security and performance.

## Files

- `podman-compose.yaml` - Main compose configuration with all Phoenix Hydra services
- `test-compose.sh` - Linux/macOS test script for validating the configuration
- `test-compose.ps1` - Windows PowerShell test script for validating the configuration

## Services

The compose configuration includes the following services:

### Core Services
- **gap-detector** (port 8000) - Gap detection system with SSM analysis
- **analysis-engine** (port 5000) - Advanced analysis engine for data processing
- **recurrent-processor** - Background processing service
- **rubik-agent** - Rubik agent service for task orchestration

### Infrastructure Services
- **db** - PostgreSQL database for data persistence
- **windmill** (port 3000) - Workflow management system
- **nginx** (port 8080) - Reverse proxy and load balancer

## Key Features

### Security Enhancements
- **Rootless execution**: All containers run without root privileges
- **User namespace mapping**: Proper UID/GID mapping for security
- **Security options**: `no-new-privileges` flag enabled for all services
- **Network isolation**: Services communicate through dedicated `phoenix-net` network

### Podman-Specific Optimizations
- **Volume mounting**: Rootless-compatible volume definitions with proper SELinux labels
- **Health checks**: Comprehensive health monitoring for all services
- **Dependency management**: Proper service startup ordering with health conditions
- **Restart policies**: Automatic restart on failure (unless-stopped)

### Networking
- **Custom bridge network**: `phoenix-net` with dedicated subnet (172.20.0.0/16)
- **DNS resolution**: Automatic service discovery between containers
- **Port mapping**: External access via ports 8000, 3000, 5000, and 8080

## Prerequisites

1. **Podman**: Install Podman container runtime
   ```bash
   # Ubuntu/Debian
   sudo apt-get install podman
   
   # RHEL/CentOS/Fedora
   sudo dnf install podman
   
   # macOS
   brew install podman
   ```

2. **podman-compose**: Install compose compatibility
   ```bash
   pip install podman-compose
   ```

3. **Directory setup**: Create data directories
   ```bash
   mkdir -p ~/.local/share/phoenix-hydra/db_data
   chmod 755 ~/.local/share/phoenix-hydra
   chmod 700 ~/.local/share/phoenix-hydra/db_data
   ```

## Usage

### Testing Configuration
Before deploying, validate the configuration:

```bash
# Linux/macOS
./test-compose.sh

# Windows PowerShell
.\test-compose.ps1
```

### Starting Services
```bash
# Start all services in detached mode
podman-compose -f podman-compose.yaml up -d

# Start specific service
podman-compose -f podman-compose.yaml up -d gap-detector

# View logs
podman-compose -f podman-compose.yaml logs -f
```

### Managing Services
```bash
# Check service status
podman-compose -f podman-compose.yaml ps

# Stop all services
podman-compose -f podman-compose.yaml down

# Restart specific service
podman-compose -f podman-compose.yaml restart nginx

# Scale services (if supported)
podman-compose -f podman-compose.yaml up -d --scale gap-detector=2
```

### Health Monitoring
All services include health checks accessible via:

- Gap Detector: `http://localhost:8000/health`
- Analysis Engine: `http://localhost:5000/health`
- Windmill: `http://localhost:3000/api/version`
- Nginx: `http://localhost:8080/health`

### Volume Management
Data persistence is handled through:

- **Database data**: `~/.local/share/phoenix-hydra/db_data`
- **Configuration**: Mounted from local `nginx/` directory

## Troubleshooting

### Common Issues

1. **Permission denied errors**
   ```bash
   # Fix data directory permissions
   sudo chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra
   ```

2. **Network conflicts**
   ```bash
   # Remove existing network
   podman network rm phoenix-net
   # Restart compose
   podman-compose -f podman-compose.yaml up -d
   ```

3. **Port conflicts**
   ```bash
   # Check what's using the ports
   netstat -tulpn | grep -E ':(8000|3000|5000|8080)'
   # Stop conflicting services or change ports in compose file
   ```

4. **SELinux issues (RHEL/CentOS/Fedora)**
   ```bash
   # Set SELinux context for volumes
   sudo setsebool -P container_manage_cgroup on
   ```

### Debugging

1. **Check container logs**
   ```bash
   podman-compose -f podman-compose.yaml logs [service-name]
   ```

2. **Inspect service configuration**
   ```bash
   podman-compose -f podman-compose.yaml config
   ```

3. **Test network connectivity**
   ```bash
   # Enter container shell
   podman exec -it phoenix-hydra_gap-detector_1 /bin/bash
   # Test connectivity
   curl http://db:5432
   ```

## Migration from Docker

If migrating from Docker Compose:

1. **Stop Docker services**
   ```bash
   docker-compose down
   ```

2. **Migrate data** (if needed)
   ```bash
   # Copy Docker volumes to Podman location
   sudo cp -r /var/lib/docker/volumes/phoenix_db_data/_data/* ~/.local/share/phoenix-hydra/db_data/
   sudo chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra/db_data
   ```

3. **Start Podman services**
   ```bash
   podman-compose -f podman-compose.yaml up -d
   ```

## Performance Tuning

### Resource Limits
Add resource constraints to services:

```yaml
services:
  gap-detector:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Optimization Tips
- Use multi-stage builds in Containerfiles
- Enable BuildKit for faster builds
- Use volume caching for dependencies
- Monitor resource usage with `podman stats`

## Security Considerations

- All containers run as non-root users
- Network traffic is isolated within `phoenix-net`
- Volumes use proper SELinux labeling (`:Z` flag)
- Security options prevent privilege escalation
- Health checks ensure service availability

## Contributing

When modifying the compose configuration:

1. Test changes with the validation scripts
2. Update this README if adding new services
3. Ensure all services have proper health checks
4. Follow rootless security best practices
5. Document any new environment variables or volumes