# Phoenix Hydra Podman Performance Tuning Guide

This guide provides comprehensive performance optimization strategies for running Phoenix Hydra with Podman, covering container resource management, storage optimization, network performance, and system-level tuning.

## Performance Monitoring Baseline

Before implementing optimizations, establish performance baselines:

```bash
#!/bin/bash
# performance-baseline.sh

echo "=== Phoenix Hydra Performance Baseline ==="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo

# System resources
echo "=== System Resources ==="
echo "CPU: $(nproc) cores"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Storage: $(df -h / | tail -1 | awk '{print $4}') available"
echo

# Container resources
echo "=== Container Resources ==="
podman stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
echo

# Service response times
echo "=== Service Response Times ==="
for service in "localhost:8080/health" "localhost:8000/health" "localhost:5000/health" "localhost:3000/api/version"; do
    response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://$service" 2>/dev/null || echo "N/A")
    echo "$service: ${response_time}s"
done
echo

# Storage performance
echo "=== Storage Performance ==="
podman system df
echo
```

## Container Resource Optimization

### CPU Optimization

#### CPU Limits and Reservations

```yaml
# podman-compose.yaml - CPU optimization
services:
  gap-detector:
    deploy:
      resources:
        limits:
          cpus: '2.0'          # Maximum CPU cores
        reservations:
          cpus: '1.0'          # Guaranteed CPU cores
    cpuset: '0-1'              # Pin to specific CPU cores
    
  analysis-engine:
    deploy:
      resources:
        limits:
          cpus: '4.0'          # ML workloads need more CPU
        reservations:
          cpus: '2.0'
    cpuset: '2-5'              # Use different cores
```

#### CPU Affinity and NUMA Optimization

```bash
# Check NUMA topology
numactl --hardware

# Run containers with NUMA awareness
podman run --cpuset-cpus="0-3" --cpuset-mems="0" \
    --memory="4g" image_name

# For multi-socket systems, bind to specific NUMA nodes
podman run --cpuset-cpus="0-7" --cpuset-mems="0" \
    --memory="8g" cpu_intensive_service
```

#### CPU Governor Optimization

```bash
# Check current CPU governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set performance governor for better response times
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Or use powersave for energy efficiency
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Make permanent
echo 'GOVERNOR="performance"' | sudo tee -a /etc/default/cpufrequtils
```

### Memory Optimization

#### Memory Limits and Swap Configuration

```yaml
# Memory optimization in compose
services:
  analysis-engine:
    deploy:
      resources:
        limits:
          memory: 8G           # Hard limit
        reservations:
          memory: 4G           # Guaranteed memory
    shm_size: 2G               # Shared memory for ML workloads
    
  gap-detector:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    mem_swappiness: 10         # Reduce swap usage
```

#### Memory Management Tuning

```bash
# Optimize memory management
echo 'vm.swappiness = 10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio = 15' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio = 5' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure = 50' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p

# For containers with large memory requirements
echo 'vm.max_map_count = 262144' | sudo tee -a /etc/sysctl.conf
echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf
```

#### Memory Monitoring and Optimization

```bash
# Monitor memory usage patterns
watch -n 1 'podman stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"'

# Check for memory leaks
podman exec container_name ps aux --sort=-%mem | head -10

# Optimize JVM memory (for Java services)
podman run -e JAVA_OPTS="-Xms2g -Xmx4g -XX:+UseG1GC -XX:MaxGCPauseMillis=200" java_service
```

### I/O and Storage Optimization

#### Storage Driver Optimization

```bash
# Configure optimal storage driver
mkdir -p ~/.config/containers
cat > ~/.config/containers/storage.conf << EOF
[storage]
driver = "overlay"
runroot = "/run/user/$(id -u)/containers"
graphroot = "$HOME/.local/share/containers/storage"

[storage.options]
mount_program = "/usr/bin/fuse-overlayfs"
mountopt = "nodev,fsync=0"

[storage.options.overlay]
mountopt = "nodev"
size = "50G"
skip_mount_home = "true"
EOF
```

#### Volume Performance Optimization

```yaml
# High-performance volume configurations
services:
  database:
    volumes:
      # Use bind mounts for better performance
      - type: bind
        source: ~/.local/share/phoenix-hydra/db_data
        target: /var/lib/postgresql/data
        bind:
          propagation: rprivate
      # Use tmpfs for temporary data
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 1G
          mode: 1777
          
  analysis-engine:
    volumes:
      # Optimize for ML workloads
      - type: bind
        source: ~/.local/share/phoenix-hydra/models
        target: /app/models
        bind:
          propagation: rprivate
      # Fast scratch space
      - type: tmpfs
        target: /tmp/processing
        tmpfs:
          size: 4G
```

#### Disk I/O Optimization

```bash
# Optimize I/O scheduler for SSDs
echo noop | sudo tee /sys/block/sda/queue/scheduler

# For HDDs, use deadline scheduler
echo deadline | sudo tee /sys/block/sda/queue/scheduler

# Increase I/O queue depth
echo 32 | sudo tee /sys/block/sda/queue/nr_requests

# Optimize filesystem mount options
# Add to /etc/fstab:
# /dev/sda1 / ext4 defaults,noatime,nodiratime 0 1
```

## Network Performance Optimization

### Network Configuration

#### High-Performance Networking

```yaml
# Network optimization in compose
networks:
  phoenix-net:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: phoenix-br0
      com.docker.network.driver.mtu: 9000  # Jumbo frames
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

#### Network Buffer Tuning

```bash
# Optimize network buffers
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_default = 65536' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_default = 65536' | sudo tee -a /etc/sysctl.conf
echo 'net.core.netdev_max_backlog = 5000' | sudo tee -a /etc/sysctl.conf

# TCP optimization
echo 'net.ipv4.tcp_rmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_congestion_control = bbr' | sudo tee -a /etc/sysctl.conf

sudo sysctl -p
```

#### Container Network Modes

```bash
# Use host networking for maximum performance (less secure)
podman run --network host high_performance_service

# Use macvlan for direct network access
podman network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 macvlan-net

podman run --network macvlan-net service_name
```

### Load Balancing and Scaling

#### Nginx Performance Tuning

```nginx
# nginx.conf optimization
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Connection optimization
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    
    # Buffer optimization
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;
    
    # Caching
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

#### Service Scaling

```yaml
# Horizontal scaling configuration
services:
  gap-detector:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

## Build Performance Optimization

### Multi-Stage Build Optimization

```dockerfile
# Optimized multi-stage Containerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Build application
COPY . .
RUN python setup.py build

# Runtime stage
FROM python:3.11-slim as runtime

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only necessary files from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder --chown=appuser:appuser /app/dist /app/

USER appuser
WORKDIR /app

ENV PATH="/home/appuser/.local/bin:$PATH"
CMD ["python", "app.py"]
```

### Build Cache Optimization

```bash
# Use buildah for better caching
buildah bud --layers --cache-from localhost/image:latest -t localhost/image:new .

# Parallel builds
buildah bud --jobs $(nproc) -t image_name .

# Optimize build context
cat > .containerignore << EOF
.git
node_modules
*.log
.pytest_cache
__pycache__
*.pyc
.coverage
EOF
```

## System-Level Optimization

### Kernel Parameters

```bash
# Optimize kernel parameters for containers
cat > /etc/sysctl.d/99-phoenix-hydra.conf << EOF
# Network optimization
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535

# Memory optimization
vm.max_map_count = 262144
vm.overcommit_memory = 1
vm.swappiness = 10

# File system optimization
fs.file-max = 2097152
fs.nr_open = 1048576

# Container optimization
user.max_user_namespaces = 28633
user.max_inotify_watches = 524288
EOF

sudo sysctl -p /etc/sysctl.d/99-phoenix-hydra.conf
```

### Resource Limits

```bash
# Optimize user limits
cat > /etc/security/limits.d/phoenix-hydra.conf << EOF
$(whoami) soft nofile 65536
$(whoami) hard nofile 65536
$(whoami) soft nproc 32768
$(whoami) hard nproc 32768
$(whoami) soft memlock unlimited
$(whoami) hard memlock unlimited
EOF
```

### Systemd Optimization

```ini
# ~/.config/systemd/user/phoenix-hydra.service.d/performance.conf
[Service]
# CPU optimization
CPUAccounting=true
CPUQuota=400%
CPUWeight=100

# Memory optimization
MemoryAccounting=true
MemoryMax=16G
MemorySwapMax=8G

# I/O optimization
IOAccounting=true
IOWeight=100

# Process optimization
TasksMax=4096
LimitNOFILE=65536
LimitNPROC=32768
```

## Application-Specific Optimizations

### Python/ML Workload Optimization

```dockerfile
# Python optimization
FROM python:3.11-slim

# Install optimized Python packages
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    torch==2.0.1+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html

# Optimize Python runtime
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PYTHONIOENCODING=utf-8

# Use faster JSON library
RUN pip install --no-cache-dir orjson

# Optimize for CPU-bound tasks
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4
ENV NUMEXPR_NUM_THREADS=4
```

### Database Optimization

```yaml
# PostgreSQL optimization
services:
  db:
    image: postgres:15-alpine
    environment:
      # Connection optimization
      POSTGRES_MAX_CONNECTIONS: 200
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
      POSTGRES_WORK_MEM: 4MB
      POSTGRES_MAINTENANCE_WORK_MEM: 64MB
      
      # WAL optimization
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
      POSTGRES_RANDOM_PAGE_COST: 1.1
      
    volumes:
      - type: bind
        source: ~/.local/share/phoenix-hydra/db_data
        target: /var/lib/postgresql/data
        bind:
          propagation: rprivate
      # Separate WAL on faster storage
      - type: bind
        source: ~/.local/share/phoenix-hydra/db_wal
        target: /var/lib/postgresql/wal
        bind:
          propagation: rprivate
```

## Performance Monitoring and Profiling

### Continuous Monitoring

```bash
#!/bin/bash
# performance-monitor.sh

LOGFILE="performance-$(date +%Y%m%d_%H%M%S).log"

while true; do
    echo "=== $(date) ===" >> "$LOGFILE"
    
    # System metrics
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)" >> "$LOGFILE"
    echo "Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')" >> "$LOGFILE"
    echo "Load: $(uptime | awk -F'load average:' '{print $2}')" >> "$LOGFILE"
    
    # Container metrics
    podman stats --no-stream --format "{{.Container}}: CPU={{.CPUPerc}} MEM={{.MemPerc}}" >> "$LOGFILE"
    
    # Service response times
    for service in "localhost:8080/health" "localhost:8000/health"; do
        response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://$service" 2>/dev/null || echo "N/A")
        echo "$service: ${response_time}s" >> "$LOGFILE"
    done
    
    echo "" >> "$LOGFILE"
    sleep 60
done
```

### Performance Testing

```bash
#!/bin/bash
# performance-test.sh

echo "Starting Phoenix Hydra performance test..."

# Start services
podman-compose -f infra/podman/podman-compose.yaml up -d

# Wait for services to be ready
sleep 30

# Test gap-detector performance
echo "Testing gap-detector..."
ab -n 1000 -c 10 -g gap-detector-results.tsv http://localhost:8000/health

# Test nginx performance
echo "Testing nginx..."
ab -n 5000 -c 50 -g nginx-results.tsv http://localhost:8080/health

# Test analysis-engine performance
echo "Testing analysis-engine..."
ab -n 500 -c 5 -g analysis-engine-results.tsv http://localhost:5000/health

# Collect resource usage
podman stats --no-stream > performance-stats.txt

# Generate report
python3 << EOF
import json
import subprocess

# Collect metrics
stats = subprocess.check_output(['podman', 'stats', '--no-stream', '--format', 'json']).decode()
containers = json.loads(stats)

print("=== Performance Test Results ===")
for container in containers:
    print(f"Container: {container['Name']}")
    print(f"  CPU: {container['CPUPerc']}")
    print(f"  Memory: {container['MemUsage']}")
    print(f"  Network I/O: {container['NetIO']}")
    print(f"  Block I/O: {container['BlockIO']}")
    print()
EOF

echo "Performance test completed. Check *-results.tsv files for detailed results."
```

## Optimization Checklist

### Pre-Deployment Checklist

- [ ] System resources adequate (CPU, RAM, storage)
- [ ] Kernel parameters optimized
- [ ] Storage driver configured (overlay with fuse-overlayfs)
- [ ] Network buffers tuned
- [ ] User limits increased
- [ ] Container resource limits set
- [ ] Multi-stage builds implemented
- [ ] Volume mounts optimized

### Runtime Optimization Checklist

- [ ] CPU affinity configured for critical services
- [ ] Memory limits prevent OOM kills
- [ ] Network performance meets requirements
- [ ] Storage I/O optimized
- [ ] Service scaling configured
- [ ] Health checks tuned
- [ ] Monitoring in place

### Ongoing Maintenance Checklist

- [ ] Regular performance monitoring
- [ ] Resource usage trending
- [ ] Bottleneck identification
- [ ] Capacity planning
- [ ] Performance regression testing
- [ ] Configuration tuning based on metrics

## Performance Troubleshooting

### Common Performance Issues

1. **High CPU Usage**
   - Check for CPU-bound processes
   - Verify CPU limits are appropriate
   - Consider CPU affinity settings
   - Profile application code

2. **Memory Issues**
   - Monitor for memory leaks
   - Adjust memory limits
   - Optimize garbage collection
   - Use memory profiling tools

3. **I/O Bottlenecks**
   - Check disk utilization
   - Optimize storage configuration
   - Use faster storage devices
   - Implement caching strategies

4. **Network Latency**
   - Monitor network utilization
   - Optimize network configuration
   - Consider network topology
   - Implement connection pooling

This performance tuning guide provides comprehensive optimization strategies for Phoenix Hydra running on Podman. Regular monitoring and iterative optimization based on actual usage patterns will yield the best results.