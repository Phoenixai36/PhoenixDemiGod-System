# Phoenix Hydra Podman Troubleshooting Guide

This guide provides detailed troubleshooting information for common issues encountered when running Phoenix Hydra with Podman.

## Quick Diagnostic Commands

Before diving into specific issues, run these diagnostic commands to gather system information:

```bash
# System information
podman info
podman version

# Container status
podman ps -a
podman-compose ps

# Network information
podman network ls
podman network inspect phoenix-net

# Volume information
podman volume ls
podman system df

# Service logs
podman-compose logs --tail=50
```

## Common Issues and Solutions

### 1. Container Startup Issues

#### Issue: Container fails to start with "permission denied"

**Symptoms:**
```
Error: OCI runtime error: container_linux.go:380: starting container process caused: process_linux.go:545: container init caused: rootfs_linux.go:76: mounting "/home/user/data" to rootfs at "/data" caused: mount through procfd: permission denied
```

**Diagnosis:**
```bash
# Check directory permissions
ls -la ~/.local/share/phoenix-hydra/
ls -laZ ~/.local/share/phoenix-hydra/  # Check SELinux context

# Check user namespace mapping
cat /proc/self/uid_map
cat /proc/self/gid_map
```

**Solutions:**

1. **Fix directory ownership:**
```bash
sudo chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra
chmod -R 755 ~/.local/share/phoenix-hydra
```

2. **Fix SELinux labels:**
```bash
# For RHEL/CentOS/Fedora systems
sudo setsebool -P container_manage_cgroup on
restorecon -R ~/.local/share/phoenix-hydra

# Or use :Z flag in volume mounts
podman run -v ~/.local/share/phoenix-hydra/data:/data:Z image_name
```

3. **Check subuid/subgid configuration:**
```bash
# Verify entries exist
grep $(whoami) /etc/subuid
grep $(whoami) /etc/subgid

# If missing, add them
echo "$(whoami):100000:65536" | sudo tee -a /etc/subuid
echo "$(whoami):100000:65536" | sudo tee -a /etc/subgid

# Migrate Podman storage
podman system migrate
```

#### Issue: Container exits immediately with code 125

**Symptoms:**
```
Error: container create failed (no logs from the container): container create failed: time="2024-01-01T12:00:00Z" level=error msg="container_linux.go:380: starting container process caused \"exec: \\\"python\\\": executable file not found in $PATH\""
```

**Diagnosis:**
```bash
# Check container image
podman inspect image_name

# Test container interactively
podman run -it --entrypoint /bin/bash image_name

# Check PATH and executable
podman run --rm image_name which python
podman run --rm image_name ls -la /usr/bin/python*
```

**Solutions:**

1. **Fix Containerfile:**
```dockerfile
# Ensure proper base image
FROM python:3.11-slim

# Install required packages
RUN apt-get update && apt-get install -y python3 python3-pip

# Set proper PATH
ENV PATH="/usr/local/bin:$PATH"

# Use absolute path for executables
CMD ["/usr/bin/python3", "app.py"]
```

2. **Rebuild image:**
```bash
podman build -t image_name -f Containerfile .
```

### 2. Network Connectivity Issues

#### Issue: Services cannot communicate with each other

**Symptoms:**
- HTTP requests between services fail
- DNS resolution not working
- Connection timeouts

**Diagnosis:**
```bash
# Check network configuration
podman network inspect phoenix-net

# Test connectivity from container
podman exec -it container_name ping other_service_name
podman exec -it container_name nslookup other_service_name
podman exec -it container_name curl -v http://other_service_name:port/health

# Check if services are on the same network
podman inspect container_name | grep NetworkMode
```

**Solutions:**

1. **Recreate network:**
```bash
# Stop all services
podman-compose down

# Remove and recreate network
podman network rm phoenix-net
podman network create phoenix-net

# Restart services
podman-compose up -d
```

2. **Fix network configuration in compose file:**
```yaml
networks:
  phoenix-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

services:
  service1:
    networks:
      - phoenix-net
  service2:
    networks:
      - phoenix-net
```

3. **Check firewall rules:**
```bash
# Check if firewall is blocking connections
sudo firewall-cmd --list-all

# Allow Podman networks
sudo firewall-cmd --permanent --add-source=172.20.0.0/16
sudo firewall-cmd --reload
```

#### Issue: Cannot access services from host

**Symptoms:**
- `curl localhost:8080` fails
- Browser cannot connect to services
- Port binding errors

**Diagnosis:**
```bash
# Check port bindings
podman port container_name
netstat -tulpn | grep -E ':(8000|3000|5000|8080)'

# Check if ports are in use
lsof -i :8080
ss -tulpn | grep :8080
```

**Solutions:**

1. **Fix port conflicts:**
```bash
# Find what's using the port
sudo lsof -i :8080

# Stop conflicting service
sudo systemctl stop service_name

# Or change port in compose file
```

2. **Fix rootless port binding:**
```bash
# For ports < 1024, use unprivileged ports
# Change 80:80 to 8080:80 in compose file

# Or enable unprivileged port binding (less secure)
echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 3. Volume and Storage Issues

#### Issue: Data not persisting between container restarts

**Symptoms:**
- Database data lost after restart
- Configuration changes not saved
- Files disappear when container stops

**Diagnosis:**
```bash
# Check volume mounts
podman inspect container_name | grep -A 10 "Mounts"

# Check volume existence
podman volume ls
podman volume inspect volume_name

# Check directory permissions
ls -la ~/.local/share/phoenix-hydra/
```

**Solutions:**

1. **Fix volume configuration:**
```yaml
services:
  db:
    volumes:
      - ~/.local/share/phoenix-hydra/db_data:/var/lib/postgresql/data:Z
      # Ensure :Z flag for SELinux systems
```

2. **Create missing directories:**
```bash
mkdir -p ~/.local/share/phoenix-hydra/db_data
chmod 700 ~/.local/share/phoenix-hydra/db_data
```

3. **Fix ownership issues:**
```bash
# Find container user ID
podman exec container_name id

# Fix ownership (example for postgres user)
sudo chown -R 999:999 ~/.local/share/phoenix-hydra/db_data
```

#### Issue: "No space left on device" errors

**Symptoms:**
```
Error: error creating container storage: mkdir /home/user/.local/share/containers/storage/overlay: no space left on device
```

**Diagnosis:**
```bash
# Check disk space
df -h
df -h ~/.local/share/containers/

# Check Podman storage usage
podman system df
podman system df -v
```

**Solutions:**

1. **Clean up unused resources:**
```bash
# Remove unused containers
podman container prune -f

# Remove unused images
podman image prune -a -f

# Remove unused volumes
podman volume prune -f

# Complete cleanup
podman system prune -a -f --volumes
```

2. **Move storage location:**
```bash
# Stop all containers
podman-compose down

# Edit storage configuration
mkdir -p ~/.config/containers
cat > ~/.config/containers/storage.conf << EOF
[storage]
driver = "overlay"
graphroot = "/path/to/larger/disk/containers/storage"
EOF

# Migrate existing data
podman system migrate
```

### 4. Performance Issues

#### Issue: Containers running slowly or consuming too much memory

**Symptoms:**
- High CPU usage
- Memory exhaustion
- Slow response times
- Container OOM kills

**Diagnosis:**
```bash
# Monitor resource usage
podman stats
htop
free -h

# Check container limits
podman inspect container_name | grep -A 10 "Resources"

# Check for memory leaks
podman exec container_name ps aux --sort=-%mem
```

**Solutions:**

1. **Set resource limits:**
```yaml
services:
  service_name:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

2. **Optimize container configuration:**
```bash
# Use crun runtime for better performance
podman run --runtime crun image_name

# Optimize storage driver
echo 'storage.driver = "overlay"' >> ~/.config/containers/storage.conf
echo 'storage.options.overlay.mount_program = "/usr/bin/fuse-overlayfs"' >> ~/.config/containers/storage.conf
```

3. **Tune system parameters:**
```bash
# Increase memory limits
echo 'vm.max_map_count = 262144' | sudo tee -a /etc/sysctl.conf
echo 'fs.file-max = 65536' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 5. Build Issues

#### Issue: Image build fails with dependency errors

**Symptoms:**
```
Error: error building at STEP "RUN pip install -r requirements.txt": error while running runtime: exit status 1
```

**Diagnosis:**
```bash
# Check build context
ls -la Containerfile
cat requirements.txt

# Test build interactively
podman run -it --rm python:3.11-slim /bin/bash
# Then manually run the failing commands
```

**Solutions:**

1. **Fix Containerfile dependencies:**
```dockerfile
# Update package lists first
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Use specific package versions
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

2. **Use multi-stage builds:**
```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
CMD ["python", "app.py"]
```

### 6. Systemd Integration Issues

#### Issue: Systemd services fail to start

**Symptoms:**
- Services don't start automatically
- Systemd status shows failed
- Services don't restart after failure

**Diagnosis:**
```bash
# Check service status
systemctl --user status phoenix-hydra.pod

# View detailed logs
journalctl --user -u phoenix-hydra.pod -f

# Check Quadlet file syntax
systemctl --user daemon-reload
```

**Solutions:**

1. **Fix Quadlet file syntax:**
```ini
# Correct format for .pod file
[Unit]
Description=Phoenix Hydra Pod
Wants=network-online.target
After=network-online.target

[Pod]
PodName=phoenix-hydra
Network=phoenix-net

[Install]
WantedBy=default.target
```

2. **Enable user lingering:**
```bash
# Allow user services to run without login
loginctl enable-linger $USER

# Check lingering status
loginctl show-user $USER | grep Linger
```

3. **Fix service dependencies:**
```bash
# Reload systemd configuration
systemctl --user daemon-reload

# Enable and start services in correct order
systemctl --user enable --now phoenix-hydra.pod
systemctl --user enable --now phoenix-db.container
```

## Advanced Troubleshooting

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Enable debug logging
export PODMAN_LOG_LEVEL=debug

# Run with debug output
podman --log-level debug run image_name

# Check debug logs
journalctl --user -u podman -f
```

### Container Inspection

Deep dive into container configuration:

```bash
# Full container inspection
podman inspect container_name | jq '.'

# Check specific configuration
podman inspect container_name | jq '.Config.Env'
podman inspect container_name | jq '.NetworkSettings'
podman inspect container_name | jq '.Mounts'

# Check container processes
podman top container_name
podman exec container_name ps aux
```

### Network Troubleshooting

Advanced network debugging:

```bash
# Check network interfaces
podman exec container_name ip addr show
podman exec container_name ip route show

# Test network connectivity
podman exec container_name nc -zv other_service 8080
podman exec container_name telnet other_service 8080

# Check DNS resolution
podman exec container_name cat /etc/resolv.conf
podman exec container_name dig other_service
```

### Performance Profiling

Profile container performance:

```bash
# CPU profiling
podman exec container_name top -p 1
podman exec container_name cat /proc/1/stat

# Memory profiling
podman exec container_name cat /proc/meminfo
podman exec container_name free -h

# I/O profiling
podman exec container_name iostat -x 1
podman exec container_name iotop
```

## Getting Help

### Log Collection

Collect comprehensive logs for support:

```bash
#!/bin/bash
# collect-logs.sh

LOG_DIR="phoenix-hydra-logs-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# System information
podman info > "$LOG_DIR/podman-info.txt"
podman version > "$LOG_DIR/podman-version.txt"
uname -a > "$LOG_DIR/system-info.txt"

# Container information
podman ps -a > "$LOG_DIR/containers.txt"
podman images > "$LOG_DIR/images.txt"
podman network ls > "$LOG_DIR/networks.txt"
podman volume ls > "$LOG_DIR/volumes.txt"

# Service logs
podman-compose logs > "$LOG_DIR/compose-logs.txt"

# System logs
journalctl --user -u 'phoenix-*' --since "24 hours ago" > "$LOG_DIR/systemd-logs.txt"

# Configuration files
cp -r infra/podman "$LOG_DIR/config"

# Create archive
tar -czf "$LOG_DIR.tar.gz" "$LOG_DIR"
rm -rf "$LOG_DIR"

echo "Logs collected in $LOG_DIR.tar.gz"
```

### Support Checklist

Before seeking support, ensure you have:

- [ ] Collected system information (`podman info`)
- [ ] Gathered container logs (`podman logs`)
- [ ] Checked system resources (`df -h`, `free -h`)
- [ ] Verified network connectivity
- [ ] Reviewed configuration files
- [ ] Attempted basic troubleshooting steps
- [ ] Created log archive with `collect-logs.sh`

### Community Resources

- **Podman Documentation**: https://docs.podman.io/
- **Podman GitHub Issues**: https://github.com/containers/podman/issues
- **Phoenix Hydra Documentation**: `docs/` directory
- **Container Best Practices**: https://developers.redhat.com/blog/2019/04/25/podman-basics-cheat-sheet

This troubleshooting guide should help resolve most common issues encountered when running Phoenix Hydra with Podman. Keep this document updated as new issues and solutions are discovered.