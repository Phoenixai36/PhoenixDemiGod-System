# Phoenix Hydra Podman Comprehensive Guide

This comprehensive guide provides complete instructions for migrating from Docker to Podman, deploying Phoenix Hydra services, troubleshooting common issues, performance tuning, and implementing security best practices for rootless container execution.

## Table of Contents

1. [Migration Guide](#migration-guide)
2. [Installation and Setup](#installation-and-setup)
3. [Deployment Methods](#deployment-methods)
4. [Troubleshooting](#troubleshooting)
5. [Performance Tuning](#performance-tuning)
6. [Security Best Practices](#security-best-practices)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Advanced Configuration](#advanced-configuration)

## Migration Guide

### Overview

Phoenix Hydra has migrated from Docker to Podman to provide:
- **Enhanced Security**: Rootless container execution without daemon
- **Better Resource Management**: Improved memory and CPU efficiency
- **Simplified Architecture**: Daemon-less design reduces complexity
- **Compliance**: Better alignment with enterprise security requirements

### Pre-Migration Checklist

Before starting the migration, ensure you have:

- [ ] Current Docker setup documented and backed up
- [ ] All data volumes identified and backed up
- [ ] Network configurations documented
- [ ] Service dependencies mapped
- [ ] Rollback plan prepared

### Migration Steps

#### Step 1: Backup Current Docker Environment

```bash
# Stop all Docker services
docker-compose down

# Backup Docker volumes
sudo mkdir -p /backup/docker-volumes
sudo cp -r /var/lib/docker/volumes/* /backup/docker-volumes/

# Export current configuration
docker-compose config > docker-backup-config.yaml

# List all Docker images for reference
docker images > docker-images-backup.txt
```

#### Step 2: Install Podman

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y podman podman-compose fuse-overlayfs slirp4netns
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install -y podman podman-docker podman-compose fuse-overlayfs slirp4netns
```

**macOS:**
```bash
brew install podman
podman machine init
podman machine start
```

**Windows:**
```powershell
# Using Chocolatey
choco install podman-desktop

# Or using winget
winget install RedHat.Podman-Desktop
```

#### Step 3: Configure Rootless Environment

```bash
# Enable user lingering (keeps services running after logout)
loginctl enable-linger $USER

# Enable Podman socket
systemctl --user enable --now podman.socket

# Create necessary directories
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.local/share/phoenix-hydra/db_data

# Set proper permissions
chmod 755 ~/.local/share/phoenix-hydra
chmod 700 ~/.local/share/phoenix-hydra/db_data
```

#### Step 4: Migrate Data

```bash
# Copy Docker volume data to Podman location
sudo cp -r /backup/docker-volumes/phoenix_db_data/_data/* ~/.local/share/phoenix-hydra/db_data/

# Fix ownership for rootless execution
sudo chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra/db_data

# Verify data integrity
ls -la ~/.local/share/phoenix-hydra/db_data
```

#### Step 5: Deploy with Podman

```bash
# Navigate to Podman configuration
cd infra/podman

# Start services
podman-compose -f podman-compose.yaml up -d

# Verify deployment
podman-compose ps
```

#### Step 6: Validation

```bash
# Test service connectivity
curl -f http://localhost:8080/health  # nginx
curl -f http://localhost:8000/health  # gap-detector
curl -f http://localhost:3000/api/version  # windmill
curl -f http://localhost:5000/health  # analysis-engine

# Check container status
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Verify data persistence
podman exec phoenix-hydra_db_1 psql -U postgres -c "\l"
```

### Rollback Procedure

If migration fails, you can rollback to Docker:

```bash
# Stop Podman services
podman-compose -f infra/podman/podman-compose.yaml down

# Restore Docker volumes
sudo cp -r /backup/docker-volumes/* /var/lib/docker/volumes/

# Start Docker services
docker-compose up -d

# Verify rollback
docker-compose ps
```

## Installation and Setup

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB free space
- OS: Linux (Ubuntu 20.04+, RHEL 8+, Fedora 35+)

**Recommended Requirements:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- OS: Recent Linux distribution with systemd

### Detailed Installation

#### Linux Installation

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt-get update

# Install Podman and dependencies
sudo apt-get install -y \
    podman \
    podman-compose \
    fuse-overlayfs \
    slirp4netns \
    uidmap \
    dbus-user-session

# Install additional tools
sudo apt-get install -y \
    buildah \
    skopeo \
    crun
```

**RHEL/CentOS/Fedora:**
```bash
# Install Podman suite
sudo dnf install -y \
    podman \
    podman-docker \
    podman-compose \
    buildah \
    skopeo \
    fuse-overlayfs \
    slirp4netns

# Enable additional repositories if needed
sudo dnf config-manager --add-repo https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/CentOS_8/devel:kubic:libcontainers:stable.repo
```

#### Configuration Files

**Podman Configuration (`~/.config/containers/containers.conf`):**
```toml
[containers]
# Default user for containers
default_user = "1000:1000"

# Security options
no_new_privileges = true
seccomp_profile = "/usr/share/containers/seccomp.json"

# Resource limits
default_ulimits = [
    "nofile=65536:65536",
    "nproc=4096:4096"
]

[engine]
# Container engine settings
cgroup_manager = "systemd"
events_logger = "journald"
runtime = "crun"

[network]
# Network settings
default_network = "podman"
network_cmd_path = "/usr/bin/slirp4netns"
```

**Storage Configuration (`~/.config/containers/storage.conf`):**
```toml
[storage]
driver = "overlay"
runroot = "/run/user/1000/containers"
graphroot = "/home/user/.local/share/containers/storage"

[storage.options]
# Overlay driver options
mount_program = "/usr/bin/fuse-overlayfs"
mountopt = "nodev,fsync=0"

[storage.options.overlay]
# Overlay-specific options
mountopt = "nodev"
size = "50G"
```

### Environment Setup

#### User Namespace Configuration

```bash
# Check current user namespace limits
cat /proc/sys/user/max_user_namespaces

# If too low, increase (requires root)
echo 'user.max_user_namespaces = 28633' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Configure subuid and subgid
echo "$(whoami):100000:65536" | sudo tee -a /etc/subuid
echo "$(whoami):100000:65536" | sudo tee -a /etc/subgid

# Verify configuration
podman system migrate
podman info --format '{{.Host.Security.Rootless}}'
```

#### Systemd Integration

```bash
# Enable user services
systemctl --user daemon-reload

# Enable Podman socket
systemctl --user enable --now podman.socket

# Create systemd drop-in directory
mkdir -p ~/.config/systemd/user/podman.service.d

# Configure service overrides
cat > ~/.config/systemd/user/podman.service.d/override.conf << EOF
[Service]
Environment=PODMAN_SYSTEMD_UNIT=%i
KillMode=mixed
ExecReload=/bin/kill -HUP \$MAINPID
Type=notify
NotifyAccess=all
EOF
```

## Deployment Methods

### Method 1: Podman Compose (Development)

Best for development and testing environments.

```bash
# Navigate to Podman directory
cd infra/podman

# Start all services
podman-compose -f podman-compose.yaml up -d

# View logs
podman-compose logs -f

# Scale specific services
podman-compose up -d --scale gap-detector=2

# Stop services
podman-compose down
```

### Method 2: Systemd with Quadlet (Production)

Recommended for production environments with automatic startup and management.

#### Create Quadlet Files

**Phoenix Hydra Pod (`~/.config/containers/systemd/phoenix-hydra.pod`):**
```ini
[Unit]
Description=Phoenix Hydra Pod
Wants=network-online.target
After=network-online.target

[Pod]
PodName=phoenix-hydra
Network=phoenix-net
PublishPort=8080:8080
PublishPort=8000:8000
PublishPort=3000:3000
PublishPort=5000:5000

[Install]
WantedBy=default.target
```

**Database Service (`~/.config/containers/systemd/phoenix-db.container`):**
```ini
[Unit]
Description=Phoenix Hydra Database
Wants=phoenix-hydra.pod
After=phoenix-hydra.pod

[Container]
ContainerName=phoenix-db
Image=postgres:15-alpine
Pod=phoenix-hydra.pod
Environment=POSTGRES_DB=phoenix_hydra
Environment=POSTGRES_USER=phoenix
Environment=POSTGRES_PASSWORD=secure_password
Volume=%h/.local/share/phoenix-hydra/db_data:/var/lib/postgresql/data:Z
HealthCmd=pg_isready -U phoenix -d phoenix_hydra
HealthInterval=30s
HealthRetries=3
HealthStartPeriod=60s

[Service]
Restart=always
RestartSec=30

[Install]
WantedBy=default.target
```

#### Deploy with Systemd

```bash
# Reload systemd configuration
systemctl --user daemon-reload

# Enable and start services
systemctl --user enable --now phoenix-hydra.pod
systemctl --user enable --now phoenix-db.container

# Check status
systemctl --user status phoenix-hydra.pod
systemctl --user list-units --type=service --state=running | grep phoenix
```

### Method 3: Manual Container Management

For fine-grained control and debugging.

```bash
# Create network
podman network create phoenix-net

# Start database
podman run -d \
    --name phoenix-db \
    --network phoenix-net \
    -e POSTGRES_DB=phoenix_hydra \
    -e POSTGRES_USER=phoenix \
    -e POSTGRES_PASSWORD=secure_password \
    -v ~/.local/share/phoenix-hydra/db_data:/var/lib/postgresql/data:Z \
    postgres:15-alpine

# Start gap detector
podman run -d \
    --name gap-detector \
    --network phoenix-net \
    -p 8000:8000 \
    --health-cmd="curl -f http://localhost:8000/health || exit 1" \
    --health-interval=30s \
    phoenix-hydra/gap-detector:latest

# Start nginx
podman run -d \
    --name nginx \
    --network phoenix-net \
    -p 8080:8080 \
    -v ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro,Z \
    phoenix-hydra/nginx:latest
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Permission Denied Errors

**Problem:** Container cannot access mounted volumes
```
Error: OCI runtime error: container_linux.go:380: starting container process caused: process_linux.go:545: container init caused: rootfs_linux.go:76: mounting "/home/user/data" to rootfs at "/data" caused: mount through procfd: permission denied
```

**Solution:**
```bash
# Fix directory permissions
sudo chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra

# Use proper SELinux labels
podman run -v ~/.local/share/phoenix-hydra/data:/data:Z image_name

# Check SELinux context
ls -laZ ~/.local/share/phoenix-hydra
```

#### 2. Network Connectivity Issues

**Problem:** Services cannot communicate with each other

**Diagnosis:**
```bash
# Check network configuration
podman network ls
podman network inspect phoenix-net

# Test connectivity from container
podman exec -it container_name ping other_service_name

# Check DNS resolution
podman exec -it container_name nslookup other_service_name
```

**Solution:**
```bash
# Recreate network
podman network rm phoenix-net
podman network create phoenix-net

# Restart services with proper network
podman-compose down
podman-compose up -d
```

#### 3. Port Binding Failures

**Problem:** Cannot bind to privileged ports (< 1024)

**Solution:**
```bash
# Use unprivileged ports (recommended)
# Change port mapping from 80:80 to 8080:80

# Or enable port binding for rootless (less secure)
echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### 4. Container Build Failures

**Problem:** Buildah/Podman build fails with permission errors

**Solution:**
```bash
# Use buildah for complex builds
buildah bud -t image_name .

# Check build context permissions
ls -la Containerfile
chmod 644 Containerfile

# Use multi-stage builds to avoid permission issues
```

#### 5. Systemd Service Failures

**Problem:** Systemd services fail to start

**Diagnosis:**
```bash
# Check service status
systemctl --user status phoenix-hydra.pod

# View detailed logs
journalctl --user -u phoenix-hydra.pod -f

# Check Quadlet file syntax
systemctl --user daemon-reload
```

**Solution:**
```bash
# Fix Quadlet file syntax
# Ensure proper file permissions
chmod 644 ~/.config/containers/systemd/*.container
chmod 644 ~/.config/containers/systemd/*.pod

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart phoenix-hydra.pod
```

### Debugging Tools and Commands

#### Container Inspection

```bash
# List all containers
podman ps -a

# Inspect container configuration
podman inspect container_name

# View container logs
podman logs -f container_name

# Execute commands in container
podman exec -it container_name /bin/bash

# Check resource usage
podman stats container_name
```

#### Network Debugging

```bash
# List networks
podman network ls

# Inspect network configuration
podman network inspect phoenix-net

# Test network connectivity
podman run --rm --network phoenix-net alpine ping -c 3 other_service

# Check port bindings
podman port container_name
netstat -tulpn | grep -E ':(8000|3000|5000|8080)'
```

#### Storage Debugging

```bash
# List volumes
podman volume ls

# Inspect volume
podman volume inspect volume_name

# Check storage usage
podman system df

# Clean up unused resources
podman system prune -a
```

### Log Analysis

#### Centralized Logging

```bash
# View all Phoenix Hydra logs
journalctl --user -u 'phoenix-*' -f

# Filter by service
journalctl --user -u phoenix-db.container -f

# Search for errors
journalctl --user -u 'phoenix-*' --since "1 hour ago" | grep -i error

# Export logs for analysis
journalctl --user -u 'phoenix-*' --since "24 hours ago" > phoenix-logs.txt
```

#### Container-Specific Logs

```bash
# Real-time logs
podman logs -f --tail 100 container_name

# Logs with timestamps
podman logs -t container_name

# Filter logs by level
podman logs container_name 2>&1 | grep -i error

# Export container logs
podman logs container_name > container-logs.txt
```

## Performance Tuning

### Container Resource Management

#### CPU Optimization

```yaml
# In podman-compose.yaml
services:
  gap-detector:
    deploy:
      resources:
        limits:
          cpus: '2.0'
        reservations:
          cpus: '1.0'
    cpuset: '0-1'  # Pin to specific CPU cores
```

```bash
# Set CPU limits manually
podman run --cpus="1.5" --cpuset-cpus="0-1" image_name

# Monitor CPU usage
podman stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

#### Memory Optimization

```yaml
# Memory limits and reservations
services:
  analysis-engine:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    shm_size: 1G  # Shared memory for ML workloads
```

```bash
# Set memory limits
podman run --memory="4g" --memory-swap="6g" image_name

# Monitor memory usage
podman stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

### Storage Performance

#### Volume Optimization

```bash
# Use tmpfs for temporary data
podman run --tmpfs /tmp:rw,noexec,nosuid,size=1g image_name

# Optimize overlay storage
echo 'storage.options.overlay.mount_program = "/usr/bin/fuse-overlayfs"' >> ~/.config/containers/storage.conf

# Use bind mounts for better performance
podman run -v /host/path:/container/path:O image_name
```

#### Image Optimization

```dockerfile
# Multi-stage build example
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
USER appuser
ENV PATH="/home/appuser/.local/bin:$PATH"
CMD ["python", "app.py"]
```

### Network Performance

#### Network Optimization

```bash
# Use host networking for performance-critical services
podman run --network host image_name

# Optimize network buffer sizes
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Use macvlan for direct network access
podman network create -d macvlan --subnet=192.168.1.0/24 --gateway=192.168.1.1 -o parent=eth0 macvlan-net
```

### Build Performance

#### Buildah Optimization

```bash
# Use buildah for faster builds
buildah bud --layers -t image_name .

# Parallel builds
buildah bud --jobs 4 -t image_name .

# Use build cache
buildah bud --cache-from image_name:latest -t image_name:new .

# Optimize build context
echo -e "node_modules\n.git\n*.log" > .containerignore
```

### Monitoring and Metrics

#### Performance Monitoring

```bash
# Real-time resource monitoring
watch -n 1 'podman stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"'

# System resource usage
htop
iotop
nethogs

# Container-specific metrics
podman exec container_name top
podman exec container_name free -h
podman exec container_name df -h
```

#### Automated Performance Testing

```bash
#!/bin/bash
# performance-test.sh

echo "Starting performance test..."

# Start services
podman-compose -f infra/podman/podman-compose.yaml up -d

# Wait for services to be ready
sleep 30

# Run load tests
echo "Testing gap-detector performance..."
ab -n 1000 -c 10 http://localhost:8000/health

echo "Testing nginx performance..."
ab -n 5000 -c 50 http://localhost:8080/health

# Collect metrics
podman stats --no-stream > performance-metrics.txt

echo "Performance test completed. Results in performance-metrics.txt"
```

## Security Best Practices

### Rootless Security Model

#### User Namespace Configuration

```bash
# Verify rootless setup
podman info --format '{{.Host.Security.Rootless}}'

# Check user namespace mapping
cat /proc/self/uid_map
cat /proc/self/gid_map

# Verify no root processes
podman exec container_name ps aux | grep root
```

#### Container Security

```yaml
# Secure container configuration
services:
  secure-service:
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed
```

### Network Security

#### Network Isolation

```bash
# Create isolated networks
podman network create --internal backend-net
podman network create --internal frontend-net

# Use network policies
podman run --network backend-net --network-alias db postgres:15
podman run --network frontend-net --network backend-net app:latest
```

#### Firewall Configuration

```bash
# Configure firewall for Podman
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# Restrict access to specific IPs
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port protocol="tcp" port="8080" accept'
```

### Secrets Management

#### Podman Secrets

```bash
# Create secrets
echo "secure_password" | podman secret create db_password -

# Use secrets in containers
podman run --secret db_password,type=env,target=DB_PASSWORD postgres:15

# List secrets
podman secret ls

# Remove secrets
podman secret rm db_password
```

#### Environment Variable Security

```bash
# Use secret files instead of environment variables
podman run -v /path/to/secrets:/secrets:ro,Z image_name

# Avoid logging sensitive data
podman run --log-driver=none image_name
```

### Image Security

#### Secure Base Images

```dockerfile
# Use minimal, security-focused base images
FROM registry.access.redhat.com/ubi8/ubi-minimal:latest

# Or use distroless images
FROM gcr.io/distroless/python3

# Scan images for vulnerabilities
podman run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/tmp anchore/grype:latest /tmp/Containerfile
```

#### Image Signing and Verification

```bash
# Sign images
podman push --sign-by user@example.com localhost/image:tag

# Verify signatures
podman pull --signature-policy policy.json localhost/image:tag

# Create signature policy
cat > policy.json << EOF
{
    "default": [
        {
            "type": "signedBy",
            "keyType": "GPGKeys",
            "keyPath": "/path/to/pubkey.gpg"
        }
    ]
}
EOF
```

### Compliance and Auditing

#### Security Scanning

```bash
# Scan containers for vulnerabilities
podman run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/tmp aquasec/trivy:latest image image_name

# Scan Containerfiles
podman run --rm -v $(pwd):/tmp hadolint/hadolint:latest hadolint /tmp/Containerfile

# Security benchmarks
podman run --rm --privileged --pid host \
  -v /etc:/host/etc:ro \
  -v /var:/host/var:ro \
  docker/docker-bench-security
```

#### Audit Logging

```bash
# Enable audit logging
sudo auditctl -w /usr/bin/podman -p x -k podman_exec

# View audit logs
sudo ausearch -k podman_exec

# Configure persistent audit rules
echo '-w /usr/bin/podman -p x -k podman_exec' | sudo tee -a /etc/audit/rules.d/podman.rules
sudo systemctl restart auditd
```

## Monitoring and Maintenance

### Health Monitoring

#### Service Health Checks

```yaml
# Comprehensive health checks
services:
  gap-detector:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

#### Automated Health Monitoring

```bash
#!/bin/bash
# health-monitor.sh

SERVICES=("gap-detector" "analysis-engine" "nginx" "windmill")
ENDPOINTS=("http://localhost:8000/health" "http://localhost:5000/health" "http://localhost:8080/health" "http://localhost:3000/api/version")

for i in "${!SERVICES[@]}"; do
    SERVICE="${SERVICES[$i]}"
    ENDPOINT="${ENDPOINTS[$i]}"
    
    if curl -f -s "$ENDPOINT" > /dev/null; then
        echo "✓ $SERVICE is healthy"
    else
        echo "✗ $SERVICE is unhealthy"
        # Restart unhealthy service
        podman restart "phoenix-hydra_${SERVICE}_1"
        
        # Send notification (implement your notification method)
        # send_alert "$SERVICE is unhealthy and has been restarted"
    fi
done
```

### Maintenance Tasks

#### Regular Cleanup

```bash
#!/bin/bash
# maintenance.sh

echo "Starting Phoenix Hydra maintenance..."

# Clean up unused containers
podman container prune -f

# Clean up unused images
podman image prune -f

# Clean up unused volumes
podman volume prune -f

# Clean up unused networks
podman network prune -f

# Clean up build cache
podman system prune -a -f

# Restart services to apply updates
podman-compose -f infra/podman/podman-compose.yaml restart

echo "Maintenance completed."
```

#### Backup Procedures

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/phoenix-hydra/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
podman exec phoenix-hydra_db_1 pg_dump -U phoenix phoenix_hydra > "$BACKUP_DIR/database.sql"

# Backup volumes
cp -r ~/.local/share/phoenix-hydra "$BACKUP_DIR/volumes"

# Backup configuration
cp -r infra/podman "$BACKUP_DIR/config"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"
```

#### Update Procedures

```bash
#!/bin/bash
# update.sh

echo "Updating Phoenix Hydra..."

# Pull latest images
podman-compose -f infra/podman/podman-compose.yaml pull

# Backup before update
./backup.sh

# Stop services
podman-compose -f infra/podman/podman-compose.yaml down

# Start with new images
podman-compose -f infra/podman/podman-compose.yaml up -d

# Verify health
sleep 30
./health-monitor.sh

echo "Update completed."
```

## Advanced Configuration

### Custom Network Configuration

#### Advanced Networking

```bash
# Create custom bridge network with specific subnet
podman network create \
    --driver bridge \
    --subnet 172.30.0.0/16 \
    --gateway 172.30.0.1 \
    --ip-range 172.30.1.0/24 \
    phoenix-custom-net

# Create macvlan network for direct host access
podman network create \
    --driver macvlan \
    --subnet 192.168.1.0/24 \
    --gateway 192.168.1.1 \
    -o parent=eth0 \
    phoenix-macvlan
```

### Integration with External Systems

#### Prometheus Monitoring

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'phoenix-hydra'
    static_configs:
      - targets: ['localhost:8080', 'localhost:8000', 'localhost:5000']
    metrics_path: /metrics
    scrape_interval: 30s
```

#### Log Aggregation

```yaml
# fluentd configuration for log aggregation
services:
  fluentd:
    image: fluentd:latest
    volumes:
      - ./fluentd.conf:/fluentd/etc/fluent.conf:ro,Z
      - /var/log:/var/log:ro,Z
    ports:
      - "24224:24224"
    networks:
      - phoenix-net
```

### CI/CD Integration

#### GitHub Actions

```yaml
# .github/workflows/podman-deploy.yml
name: Deploy with Podman
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Podman
        run: |
          sudo apt-get update
          sudo apt-get install -y podman
          
      - name: Build images
        run: |
          podman build -t phoenix-hydra/gap-detector:latest -f infra/podman/gap-detector/Containerfile .
          
      - name: Deploy services
        run: |
          podman-compose -f infra/podman/podman-compose.yaml up -d
          
      - name: Run tests
        run: |
          ./scripts/test-services.sh
```

This comprehensive guide provides all the necessary information for successfully migrating to and operating Phoenix Hydra with Podman. Regular updates to this documentation should be made as the system evolves and new best practices are discovered.