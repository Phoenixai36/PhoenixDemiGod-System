# Phoenix Hydra Podman Security Best Practices

This guide provides comprehensive security best practices for running Phoenix Hydra with Podman, focusing on rootless execution, container security, network isolation, and compliance requirements.

## Security Architecture Overview

Phoenix Hydra's security model is built on the principle of defense in depth, utilizing Podman's rootless architecture as the foundation:

```
┌─────────────────────────────────────────────────────────────┐
│                    Host System Security                     │
├─────────────────────────────────────────────────────────────┤
│  User Namespace Isolation (Rootless Containers)            │
├─────────────────────────────────────────────────────────────┤
│  Network Segmentation (Custom Networks)                    │
├─────────────────────────────────────────────────────────────┤
│  Container Security (Capabilities, SELinux, Seccomp)       │
├─────────────────────────────────────────────────────────────┤
│  Application Security (Non-root users, Secrets)            │
└─────────────────────────────────────────────────────────────┘
```

## Rootless Security Model

### User Namespace Configuration

#### Verify Rootless Setup

```bash
# Verify Podman is running rootless
podman info --format '{{.Host.Security.Rootless}}'
# Expected output: true

# Check user namespace mapping
cat /proc/self/uid_map
cat /proc/self/gid_map

# Verify no root processes in containers
podman exec container_name ps aux | grep -v "^USER" | awk '$1 == "root" {print "WARNING: Root process found:", $0}'
```

#### Secure User Namespace Setup

```bash
# Configure subuid and subgid ranges
echo "$(whoami):100000:65536" | sudo tee -a /etc/subuid
echo "$(whoami):100000:65536" | sudo tee -a /etc/subgid

# Verify configuration
grep $(whoami) /etc/subuid /etc/subgid

# Migrate Podman storage to use new mappings
podman system migrate

# Enable user lingering for systemd services
loginctl enable-linger $(whoami)
```

#### User Namespace Isolation

```yaml
# Secure service configuration
services:
  gap-detector:
    user: "1000:1000"  # Non-root user
    security_opt:
      - no-new-privileges:true
      - label=type:container_runtime_t
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
```

## Container Security Hardening

### Security Options and Capabilities

#### Minimal Privilege Configuration

```yaml
# Maximum security container configuration
services:
  secure-service:
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined  # Or use custom seccomp profile
      - apparmor:unconfined  # Or use custom AppArmor profile
    user: "1000:1000"
    read_only: true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed for port binding
      - CHOWN            # Only if needed for file ownership
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/tmp:noexec,nosuid,size=50m
```

#### Custom Seccomp Profiles

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close", "stat", "fstat", "lstat",
        "poll", "lseek", "mmap", "mprotect", "munmap", "brk",
        "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "ioctl",
        "pread64", "pwrite64", "readv", "writev", "access", "pipe",
        "select", "sched_yield", "mremap", "msync", "mincore",
        "madvise", "shmget", "shmat", "shmctl", "dup", "dup2",
        "pause", "nanosleep", "getitimer", "alarm", "setitimer",
        "getpid", "sendfile", "socket", "connect", "accept", "sendto",
        "recvfrom", "sendmsg", "recvmsg", "shutdown", "bind", "listen",
        "getsockname", "getpeername", "socketpair", "setsockopt",
        "getsockopt", "clone", "fork", "vfork", "execve", "exit",
        "wait4", "kill", "uname", "semget", "semop", "semctl",
        "shmdt", "msgget", "msgsnd", "msgrcv", "msgctl", "fcntl",
        "flock", "fsync", "fdatasync", "truncate", "ftruncate",
        "getdents", "getcwd", "chdir", "fchdir", "rename", "mkdir",
        "rmdir", "creat", "link", "unlink", "symlink", "readlink",
        "chmod", "fchmod", "chown", "fchown", "lchown", "umask",
        "gettimeofday", "getrlimit", "getrusage", "sysinfo", "times",
        "ptrace", "getuid", "syslog", "getgid", "setuid", "setgid",
        "geteuid", "getegid", "setpgid", "getppid", "getpgrp",
        "setsid", "setreuid", "setregid", "getgroups", "setgroups",
        "setresuid", "getresuid", "setresgid", "getresgid", "getpgid",
        "setfsuid", "setfsgid", "getsid", "capget", "capset",
        "rt_sigpending", "rt_sigtimedwait", "rt_sigqueueinfo",
        "rt_sigsuspend", "sigaltstack", "utime", "mknod", "uselib",
        "personality", "ustat", "statfs", "fstatfs", "sysfs",
        "getpriority", "setpriority", "sched_setparam", "sched_getparam",
        "sched_setscheduler", "sched_getscheduler", "sched_get_priority_max",
        "sched_get_priority_min", "sched_rr_get_interval", "mlock",
        "munlock", "mlockall", "munlockall", "vhangup", "modify_ldt",
        "pivot_root", "prctl", "arch_prctl", "adjtimex", "setrlimit",
        "chroot", "sync", "acct", "settimeofday", "mount", "umount2",
        "swapon", "swapoff", "reboot", "sethostname", "setdomainname",
        "iopl", "ioperm", "create_module", "init_module", "delete_module",
        "get_kernel_syms", "query_module", "quotactl", "nfsservctl",
        "getpmsg", "putpmsg", "afs_syscall", "tuxcall", "security",
        "gettid", "readahead", "setxattr", "lsetxattr", "fsetxattr",
        "getxattr", "lgetxattr", "fgetxattr", "listxattr", "llistxattr",
        "flistxattr", "removexattr", "lremovexattr", "fremovexattr",
        "tkill", "time", "futex", "sched_setaffinity", "sched_getaffinity",
        "set_thread_area", "io_setup", "io_destroy", "io_getevents",
        "io_submit", "io_cancel", "get_thread_area", "lookup_dcookie",
        "epoll_create", "epoll_ctl_old", "epoll_wait_old", "remap_file_pages",
        "getdents64", "set_tid_address", "restart_syscall", "semtimedop",
        "fadvise64", "timer_create", "timer_settime", "timer_gettime",
        "timer_getoverrun", "timer_delete", "clock_settime", "clock_gettime",
        "clock_getres", "clock_nanosleep", "exit_group", "epoll_wait",
        "epoll_ctl", "tgkill", "utimes", "vserver", "mbind", "set_mempolicy",
        "get_mempolicy", "mq_open", "mq_unlink", "mq_timedsend",
        "mq_timedreceive", "mq_notify", "mq_getsetattr", "kexec_load",
        "waitid", "add_key", "request_key", "keyctl", "ioprio_set",
        "ioprio_get", "inotify_init", "inotify_add_watch", "inotify_rm_watch",
        "migrate_pages", "openat", "mkdirat", "mknodat", "fchownat",
        "futimesat", "newfstatat", "unlinkat", "renameat", "linkat",
        "symlinkat", "readlinkat", "fchmodat", "faccessat", "pselect6",
        "ppoll", "unshare", "set_robust_list", "get_robust_list",
        "splice", "tee", "sync_file_range", "vmsplice", "move_pages",
        "utimensat", "epoll_pwait", "signalfd", "timerfd_create", "eventfd",
        "fallocate", "timerfd_settime", "timerfd_gettime", "accept4",
        "signalfd4", "eventfd2", "epoll_create1", "dup3", "pipe2",
        "inotify_init1", "preadv", "pwritev", "rt_tgsigqueueinfo",
        "perf_event_open", "recvmmsg", "fanotify_init", "fanotify_mark",
        "prlimit64", "name_to_handle_at", "open_by_handle_at", "clock_adjtime",
        "syncfs", "sendmmsg", "setns", "getcpu", "process_vm_readv",
        "process_vm_writev", "kcmp", "finit_module"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### Image Security

#### Secure Base Images

```dockerfile
# Use minimal, security-focused base images
FROM registry.access.redhat.com/ubi8/ubi-minimal:latest

# Or use distroless images for production
FROM gcr.io/distroless/python3-debian11:latest

# Avoid using 'latest' tags in production
FROM python:3.11.7-slim-bullseye

# Create non-root user early in build
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Set secure file permissions
COPY --chown=appuser:appuser . /app
RUN chmod -R 755 /app && \
    chmod -R 644 /app/*.py

# Switch to non-root user
USER appuser

# Use absolute paths for executables
CMD ["/usr/local/bin/python", "/app/main.py"]
```

#### Image Scanning and Verification

```bash
# Scan images for vulnerabilities using Trivy
podman run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd):/tmp aquasec/trivy:latest image \
    --severity HIGH,CRITICAL \
    localhost/phoenix-hydra/gap-detector:latest

# Scan Containerfiles for best practices
podman run --rm -v $(pwd):/tmp hadolint/hadolint:latest \
    hadolint /tmp/infra/podman/gap-detector/Containerfile

# Sign images for integrity verification
podman push --sign-by security@phoenix-hydra.local \
    localhost/phoenix-hydra/gap-detector:latest

# Create signature policy
cat > /etc/containers/policy.json << EOF
{
    "default": [
        {
            "type": "signedBy",
            "keyType": "GPGKeys",
            "keyPath": "/etc/pki/containers/security@phoenix-hydra.local.pub"
        }
    ],
    "transports": {
        "docker-daemon": {
            "": [{"type": "insecureAcceptAnything"}]
        }
    }
}
EOF
```

## Network Security

### Network Segmentation

#### Isolated Networks

```yaml
# Network segmentation configuration
networks:
  frontend-net:
    driver: bridge
    internal: false  # Allows external access
    ipam:
      config:
        - subnet: 172.20.0.0/24
          gateway: 172.20.0.1
          
  backend-net:
    driver: bridge
    internal: true   # No external access
    ipam:
      config:
        - subnet: 172.21.0.0/24
          gateway: 172.21.0.1
          
  database-net:
    driver: bridge
    internal: true   # Isolated database network
    ipam:
      config:
        - subnet: 172.22.0.0/24
          gateway: 172.22.0.1

services:
  nginx:
    networks:
      - frontend-net
      - backend-net
      
  gap-detector:
    networks:
      - backend-net
      
  database:
    networks:
      - database-net
```

#### Network Policies and Firewall

```bash
# Configure host firewall
sudo firewall-cmd --permanent --new-zone=phoenix-containers
sudo firewall-cmd --permanent --zone=phoenix-containers --add-source=172.20.0.0/16

# Allow only necessary ports
sudo firewall-cmd --permanent --zone=phoenix-containers --add-port=8080/tcp
sudo firewall-cmd --permanent --zone=phoenix-containers --add-port=8000/tcp
sudo firewall-cmd --permanent --zone=phoenix-containers --add-port=3000/tcp

# Block direct database access from external networks
sudo firewall-cmd --permanent --zone=phoenix-containers --remove-port=5432/tcp

# Apply rules
sudo firewall-cmd --reload

# Create iptables rules for container networks
sudo iptables -I FORWARD -s 172.20.0.0/16 -d 172.22.0.0/24 -j DROP
sudo iptables -I FORWARD -s 172.21.0.0/24 -d 172.22.0.0/24 -j ACCEPT
```

### TLS and Encryption

#### TLS Configuration

```yaml
# TLS-enabled services
services:
  nginx:
    volumes:
      - ./certs:/etc/nginx/certs:ro,Z
      - ./nginx/nginx-tls.conf:/etc/nginx/nginx.conf:ro,Z
    environment:
      - SSL_CERT_PATH=/etc/nginx/certs/server.crt
      - SSL_KEY_PATH=/etc/nginx/certs/server.key
```

```nginx
# nginx-tls.conf
server {
    listen 443 ssl http2;
    server_name phoenix-hydra.local;
    
    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    
    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    location / {
        proxy_pass http://backend-services;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Secrets Management

### Podman Secrets

#### Creating and Using Secrets

```bash
# Create secrets securely
echo "secure_database_password" | podman secret create db_password -
echo "jwt_signing_key_$(openssl rand -hex 32)" | podman secret create jwt_key -

# List secrets
podman secret ls

# Use secrets in containers
podman run --secret db_password,type=env,target=DB_PASSWORD \
    --secret jwt_key,type=mount,target=/run/secrets/jwt_key \
    phoenix-hydra/gap-detector:latest
```

#### Secrets in Compose

```yaml
# Secure secrets configuration
secrets:
  db_password:
    external: true
  jwt_key:
    external: true
  ssl_cert:
    file: ./certs/server.crt
  ssl_key:
    file: ./certs/server.key

services:
  database:
    secrets:
      - source: db_password
        target: /run/secrets/db_password
        mode: 0400
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      
  gap-detector:
    secrets:
      - source: jwt_key
        target: /run/secrets/jwt_key
        mode: 0400
    environment:
      - JWT_KEY_FILE=/run/secrets/jwt_key
```

### Environment Variable Security

```bash
# Avoid logging sensitive environment variables
podman run --log-driver=none \
    -e SENSITIVE_VAR=secret_value \
    image_name

# Use init files instead of environment variables
cat > /tmp/init-secrets.sh << 'EOF'
#!/bin/bash
export DB_PASSWORD=$(cat /run/secrets/db_password)
export JWT_KEY=$(cat /run/secrets/jwt_key)
exec "$@"
EOF

podman run --secret db_password --secret jwt_key \
    -v /tmp/init-secrets.sh:/init-secrets.sh:ro,Z \
    --entrypoint /init-secrets.sh \
    image_name python app.py
```

## Access Control and Authentication

### RBAC and User Management

#### Service Account Configuration

```yaml
# Service-specific user configuration
services:
  gap-detector:
    user: "1001:1001"  # Dedicated service user
    
  analysis-engine:
    user: "1002:1002"  # Different user for isolation
    
  database:
    user: "999:999"    # PostgreSQL user
```

#### Host User Management

```bash
# Create dedicated service users
sudo useradd -r -s /bin/false phoenix-gap-detector
sudo useradd -r -s /bin/false phoenix-analysis-engine

# Configure subuid/subgid for service users
echo "phoenix-gap-detector:200000:65536" | sudo tee -a /etc/subuid
echo "phoenix-gap-detector:200000:65536" | sudo tee -a /etc/subgid

# Set up service user directories
sudo mkdir -p /var/lib/phoenix-hydra/{gap-detector,analysis-engine}
sudo chown phoenix-gap-detector:phoenix-gap-detector /var/lib/phoenix-hydra/gap-detector
sudo chown phoenix-analysis-engine:phoenix-analysis-engine /var/lib/phoenix-hydra/analysis-engine
```

### Authentication and Authorization

#### API Authentication

```python
# Secure API authentication example
import jwt
import bcrypt
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
            
        try:
            # Remove 'Bearer ' prefix
            token = token.replace('Bearer ', '')
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user = payload
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/secure-endpoint')
@require_auth
def secure_endpoint():
    return jsonify({'message': 'Access granted', 'user': request.user})
```

## Compliance and Auditing

### Security Scanning and Compliance

#### Automated Security Scanning

```bash
#!/bin/bash
# security-scan.sh

echo "=== Phoenix Hydra Security Scan ==="
echo "Date: $(date)"
echo

# Container vulnerability scanning
echo "=== Container Vulnerability Scan ==="
for image in $(podman images --format "{{.Repository}}:{{.Tag}}" | grep phoenix-hydra); do
    echo "Scanning $image..."
    podman run --rm -v /var/run/docker.sock:/var/run/docker.sock \
        aquasec/trivy:latest image --severity HIGH,CRITICAL "$image"
done

# Configuration security check
echo "=== Configuration Security Check ==="
podman run --rm -v $(pwd):/tmp \
    -v /var/run/docker.sock:/var/run/docker.sock \
    docker/docker-bench-security

# Secrets audit
echo "=== Secrets Audit ==="
echo "Checking for exposed secrets in containers..."
for container in $(podman ps --format "{{.Names}}"); do
    echo "Container: $container"
    podman exec "$container" env | grep -E "(PASSWORD|SECRET|KEY|TOKEN)" || echo "  No exposed secrets found"
done

# Network security check
echo "=== Network Security Check ==="
echo "Open ports:"
netstat -tulpn | grep -E ':(8000|3000|5000|8080)'

echo "Firewall status:"
sudo firewall-cmd --list-all

echo "=== Security Scan Complete ==="
```

#### Compliance Reporting

```python
#!/usr/bin/env python3
# compliance-report.py

import json
import subprocess
import datetime
from pathlib import Path

def generate_compliance_report():
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "phoenix_hydra_version": "1.0.0",
        "compliance_checks": {}
    }
    
    # Check rootless execution
    try:
        result = subprocess.run(['podman', 'info', '--format', '{{.Host.Security.Rootless}}'], 
                              capture_output=True, text=True)
        report["compliance_checks"]["rootless_execution"] = {
            "status": "PASS" if result.stdout.strip() == "true" else "FAIL",
            "details": "Containers running in rootless mode"
        }
    except Exception as e:
        report["compliance_checks"]["rootless_execution"] = {
            "status": "ERROR",
            "details": str(e)
        }
    
    # Check for non-root users in containers
    containers = subprocess.run(['podman', 'ps', '--format', '{{.Names}}'], 
                               capture_output=True, text=True).stdout.strip().split('\n')
    
    non_root_check = {"status": "PASS", "details": []}
    for container in containers:
        if container:
            try:
                result = subprocess.run(['podman', 'exec', container, 'id', '-u'], 
                                      capture_output=True, text=True)
                uid = result.stdout.strip()
                if uid == "0":
                    non_root_check["status"] = "FAIL"
                    non_root_check["details"].append(f"{container}: running as root (UID 0)")
                else:
                    non_root_check["details"].append(f"{container}: running as UID {uid}")
            except:
                non_root_check["details"].append(f"{container}: unable to check UID")
    
    report["compliance_checks"]["non_root_users"] = non_root_check
    
    # Check for security options
    security_check = {"status": "PASS", "details": []}
    for container in containers:
        if container:
            try:
                result = subprocess.run(['podman', 'inspect', container], 
                                      capture_output=True, text=True)
                config = json.loads(result.stdout)[0]
                security_opts = config.get('HostConfig', {}).get('SecurityOpt', [])
                
                has_no_new_privs = any('no-new-privileges:true' in opt for opt in security_opts)
                if not has_no_new_privs:
                    security_check["status"] = "WARN"
                    security_check["details"].append(f"{container}: missing no-new-privileges")
                else:
                    security_check["details"].append(f"{container}: security options configured")
            except:
                security_check["details"].append(f"{container}: unable to check security options")
    
    report["compliance_checks"]["security_options"] = security_check
    
    # Generate report file
    report_file = f"compliance-report-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Compliance report generated: {report_file}")
    return report

if __name__ == "__main__":
    generate_compliance_report()
```

### Audit Logging

#### System Audit Configuration

```bash
# Configure auditd for container monitoring
sudo tee -a /etc/audit/rules.d/podman.rules << EOF
# Monitor Podman binary execution
-w /usr/bin/podman -p x -k podman_exec

# Monitor container configuration changes
-w /home/$(whoami)/.config/containers/ -p wa -k container_config

# Monitor systemd service changes
-w /home/$(whoami)/.config/systemd/user/ -p wa -k systemd_config

# Monitor secrets access
-w /run/user/$(id -u)/containers/secrets/ -p ra -k secrets_access
EOF

# Restart auditd
sudo systemctl restart auditd

# View audit logs
sudo ausearch -k podman_exec
sudo ausearch -k container_config
```

#### Container Audit Logging

```yaml
# Centralized logging configuration
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
      
  gap-detector:
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: phoenix.gap-detector
```

## Incident Response

### Security Incident Procedures

#### Incident Detection

```bash
#!/bin/bash
# security-monitor.sh

# Monitor for suspicious activities
while true; do
    # Check for privilege escalation attempts
    if podman exec container_name ps aux | grep -q "sudo\|su "; then
        echo "ALERT: Privilege escalation attempt detected in container_name"
        # Send alert notification
    fi
    
    # Check for unusual network connections
    if netstat -an | grep -E ":(22|23|3389)" | grep -q ESTABLISHED; then
        echo "ALERT: Suspicious network connection detected"
    fi
    
    # Check for failed authentication attempts
    if journalctl --since "1 minute ago" | grep -q "authentication failure"; then
        echo "ALERT: Authentication failure detected"
    fi
    
    sleep 60
done
```

#### Incident Response Playbook

```bash
#!/bin/bash
# incident-response.sh

INCIDENT_TYPE="$1"
CONTAINER_NAME="$2"

case "$INCIDENT_TYPE" in
    "compromise")
        echo "=== Container Compromise Response ==="
        
        # Isolate container
        podman network disconnect phoenix-net "$CONTAINER_NAME"
        echo "Container $CONTAINER_NAME isolated from network"
        
        # Collect forensic data
        podman exec "$CONTAINER_NAME" ps aux > "forensics-${CONTAINER_NAME}-processes.txt"
        podman exec "$CONTAINER_NAME" netstat -an > "forensics-${CONTAINER_NAME}-network.txt"
        podman logs "$CONTAINER_NAME" > "forensics-${CONTAINER_NAME}-logs.txt"
        
        # Stop container
        podman stop "$CONTAINER_NAME"
        echo "Container $CONTAINER_NAME stopped"
        
        # Preserve container state
        podman commit "$CONTAINER_NAME" "forensics-${CONTAINER_NAME}-$(date +%Y%m%d_%H%M%S)"
        echo "Container state preserved for forensic analysis"
        ;;
        
    "breach")
        echo "=== Security Breach Response ==="
        
        # Stop all services
        podman-compose -f infra/podman/podman-compose.yaml down
        echo "All services stopped"
        
        # Collect system logs
        journalctl --since "24 hours ago" > "forensics-system-logs.txt"
        
        # Backup current state
        tar -czf "breach-backup-$(date +%Y%m%d_%H%M%S).tar.gz" \
            ~/.local/share/phoenix-hydra \
            ~/.config/containers \
            infra/podman
        
        echo "System secured and forensic data collected"
        ;;
esac
```

## Security Maintenance

### Regular Security Tasks

#### Weekly Security Checklist

```bash
#!/bin/bash
# weekly-security-check.sh

echo "=== Weekly Security Maintenance ==="
echo "Date: $(date)"

# Update base images
echo "Updating base images..."
podman pull python:3.11-slim
podman pull postgres:15-alpine
podman pull nginx:alpine

# Rebuild images with latest security updates
echo "Rebuilding images..."
podman build -t phoenix-hydra/gap-detector:latest -f infra/podman/gap-detector/Containerfile .
podman build -t phoenix-hydra/analysis-engine:latest -f infra/podman/analysis-engine/Containerfile .

# Run security scans
echo "Running security scans..."
./security-scan.sh

# Check for configuration drift
echo "Checking configuration..."
git status infra/podman/

# Rotate secrets (if applicable)
echo "Checking secret rotation..."
# Implement secret rotation logic here

# Generate compliance report
echo "Generating compliance report..."
python3 compliance-report.py

echo "Weekly security maintenance completed"
```

#### Security Monitoring Dashboard

```python
#!/usr/bin/env python3
# security-dashboard.py

import json
import subprocess
import time
from datetime import datetime, timedelta

class SecurityDashboard:
    def __init__(self):
        self.metrics = {}
    
    def collect_metrics(self):
        # Container security status
        containers = self.get_container_status()
        self.metrics['containers'] = containers
        
        # Network security
        network_status = self.check_network_security()
        self.metrics['network'] = network_status
        
        # System security
        system_status = self.check_system_security()
        self.metrics['system'] = system_status
        
        # Vulnerability status
        vuln_status = self.check_vulnerabilities()
        self.metrics['vulnerabilities'] = vuln_status
    
    def get_container_status(self):
        try:
            result = subprocess.run(['podman', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True)
            containers = json.loads(result.stdout)
            
            status = {
                'total': len(containers),
                'rootless': 0,
                'non_root_user': 0,
                'security_opts': 0
            }
            
            for container in containers:
                # Check if rootless
                info_result = subprocess.run(['podman', 'info', '--format', '{{.Host.Security.Rootless}}'], 
                                           capture_output=True, text=True)
                if info_result.stdout.strip() == 'true':
                    status['rootless'] += 1
                
                # Check user
                try:
                    user_result = subprocess.run(['podman', 'exec', container['Names'][0], 'id', '-u'], 
                                               capture_output=True, text=True)
                    if user_result.stdout.strip() != '0':
                        status['non_root_user'] += 1
                except:
                    pass
            
            return status
        except Exception as e:
            return {'error': str(e)}
    
    def check_network_security(self):
        # Check firewall status
        try:
            fw_result = subprocess.run(['sudo', 'firewall-cmd', '--state'], 
                                     capture_output=True, text=True)
            firewall_active = fw_result.returncode == 0
        except:
            firewall_active = False
        
        # Check open ports
        try:
            port_result = subprocess.run(['netstat', '-tulpn'], 
                                       capture_output=True, text=True)
            open_ports = len([line for line in port_result.stdout.split('\n') 
                            if ':8000' in line or ':8080' in line or ':3000' in line or ':5000' in line])
        except:
            open_ports = 0
        
        return {
            'firewall_active': firewall_active,
            'monitored_ports_open': open_ports
        }
    
    def check_system_security(self):
        # Check for security updates
        try:
            update_result = subprocess.run(['apt', 'list', '--upgradable'], 
                                         capture_output=True, text=True)
            security_updates = len([line for line in update_result.stdout.split('\n') 
                                  if 'security' in line.lower()])
        except:
            security_updates = 0
        
        return {
            'security_updates_available': security_updates,
            'last_check': datetime.now().isoformat()
        }
    
    def check_vulnerabilities(self):
        # This would integrate with vulnerability scanning tools
        return {
            'last_scan': datetime.now().isoformat(),
            'high_severity': 0,
            'medium_severity': 0,
            'low_severity': 0
        }
    
    def generate_report(self):
        self.collect_metrics()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'security_score': self.calculate_security_score(),
            'metrics': self.metrics,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def calculate_security_score(self):
        score = 100
        
        # Deduct points for security issues
        containers = self.metrics.get('containers', {})
        if containers.get('total', 0) > 0:
            rootless_ratio = containers.get('rootless', 0) / containers['total']
            non_root_ratio = containers.get('non_root_user', 0) / containers['total']
            
            score -= (1 - rootless_ratio) * 30  # 30 points for rootless
            score -= (1 - non_root_ratio) * 20  # 20 points for non-root users
        
        network = self.metrics.get('network', {})
        if not network.get('firewall_active', False):
            score -= 20  # 20 points for firewall
        
        system = self.metrics.get('system', {})
        security_updates = system.get('security_updates_available', 0)
        if security_updates > 0:
            score -= min(security_updates * 5, 30)  # Up to 30 points for updates
        
        return max(0, score)
    
    def generate_recommendations(self):
        recommendations = []
        
        containers = self.metrics.get('containers', {})
        if containers.get('rootless', 0) < containers.get('total', 0):
            recommendations.append("Ensure all containers are running in rootless mode")
        
        if containers.get('non_root_user', 0) < containers.get('total', 0):
            recommendations.append("Configure all containers to run with non-root users")
        
        network = self.metrics.get('network', {})
        if not network.get('firewall_active', False):
            recommendations.append("Enable and configure host firewall")
        
        system = self.metrics.get('system', {})
        if system.get('security_updates_available', 0) > 0:
            recommendations.append("Install available security updates")
        
        return recommendations

if __name__ == "__main__":
    dashboard = SecurityDashboard()
    report = dashboard.generate_report()
    
    print("=== Phoenix Hydra Security Dashboard ===")
    print(f"Security Score: {report['security_score']}/100")
    print(f"Timestamp: {report['timestamp']}")
    print()
    
    print("Container Security:")
    containers = report['metrics']['containers']
    print(f"  Total Containers: {containers.get('total', 0)}")
    print(f"  Rootless: {containers.get('rootless', 0)}")
    print(f"  Non-root Users: {containers.get('non_root_user', 0)}")
    print()
    
    print("Network Security:")
    network = report['metrics']['network']
    print(f"  Firewall Active: {network.get('firewall_active', False)}")
    print(f"  Monitored Ports Open: {network.get('monitored_ports_open', 0)}")
    print()
    
    if report['recommendations']:
        print("Recommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    else:
        print("No security recommendations at this time.")
```

This comprehensive security guide provides the foundation for maintaining a secure Phoenix Hydra deployment with Podman. Regular review and updates of these practices ensure continued security posture improvement.