# Phoenix Hydra Security Boundaries and Network Isolation

This document describes the security boundaries and network isolation implemented for the Phoenix Hydra Podman infrastructure.

## Overview

The security boundaries system implements comprehensive network isolation, volume security, and container hardening to ensure the Phoenix Hydra system runs with minimal privileges and maximum security while maintaining full functionality.

## Security Architecture

### Network Security Zones

The Phoenix Hydra system is organized into security zones with controlled access:

```
┌─────────────────────────────────────────────────────────────┐
│                    External Network                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                Public Zone                              ││
│  │  ┌─────────────┐                                        ││
│  │  │nginx:8080   │ ← External Access                      ││
│  │  │(Reverse     │                                        ││
│  │  │Proxy)       │                                        ││
│  │  └─────────────┘                                        ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                API Zone                                 ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │gap-detector │  │windmill:3000│  │analysis-    │    ││
│  │  │:8000        │  │             │  │engine:5000  │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Processing Zone                            ││
│  │  ┌─────────────┐  ┌─────────────┐                      ││
│  │  │recurrent-   │  │rubik-agent  │                      ││
│  │  │processor    │  │             │                      ││
│  │  └─────────────┘  └─────────────┘                      ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                Data Zone                                ││
│  │  ┌─────────────┐                                        ││
│  │  │db:5432      │ ← Internal Only                        ││
│  │  │(PostgreSQL) │                                        ││
│  │  └─────────────┘                                        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Port Exposure Policy

#### External Ports (Host Accessible)
- **8000**: Gap Detector API - Direct external access
- **3000**: Windmill UI - Direct external access  
- **8080**: Nginx Reverse Proxy - Main entry point
- **5000**: Analysis Engine API - Direct external access

#### Internal Ports (Container-to-Container Only)
- **5432**: PostgreSQL Database - Isolated from external access
- **8080**: Recurrent Processor Internal API - Processing zone only

## Security Features

### 1. Network Isolation

#### Custom Bridge Network
- **Network Name**: `phoenix-hydra_phoenix-net`
- **Subnet**: `172.20.0.0/16`
- **Gateway**: `172.20.0.1`
- **IP Range**: `172.20.1.0/24`
- **Bridge Name**: `phoenix-br0`

#### Network Security Options
```yaml
driver_opts:
  com.docker.network.bridge.enable_icc: "true"          # Inter-container communication
  com.docker.network.bridge.enable_ip_tables: "true"    # IP filtering
  com.docker.network.bridge.enable_ip_masquerade: "true" # NAT for external access
  com.docker.network.driver.mtu: "1500"                 # Optimized MTU
```

#### DNS Resolution
- Automatic service discovery within the network
- Services resolve each other by name (e.g., `db`, `windmill`, `nginx`)
- External DNS resolution available for internet access

### 2. Container Security

#### Rootless Execution
All containers run without root privileges using user namespace mapping:

| Service             | Container User | Description               |
| ------------------- | -------------- | ------------------------- |
| gap-detector        | 1000:1000      | Non-root application user |
| analysis-engine     | 1000:1000      | Non-root application user |
| recurrent-processor | 1000:1000      | Non-root application user |
| rubik-agent         | 1000:1000      | Non-root application user |
| nginx               | 101:101        | Nginx user                |
| db                  | 999:999        | PostgreSQL user           |

#### Security Options
All containers enforce:
- `no-new-privileges:true` - Prevents privilege escalation
- `seccomp=unconfined` - System call filtering (where applicable)
- Non-privileged execution
- Read-only root filesystem (where applicable)

#### Capability Restrictions
- Default: All capabilities dropped
- Nginx: Only `NET_BIND_SERVICE` for port binding
- Database: Only `SETUID` and `SETGID` for user switching

### 3. Volume Security

#### Volume Permissions
```
${HOME}/.local/share/phoenix-hydra/
├── db_data/          # Mode: 700 (owner only)
├── nginx_config/     # Mode: 755 (owner write, others read)
└── logs/             # Mode: 755 (owner write, others read)
```

#### SELinux Labels (if enabled)
- `db_data`: `:Z` (private unshared)
- `nginx_config`: `:ro,Z` (read-only, private unshared)
- `logs`: `:z` (shared)

#### Access Control
- All volumes owned by current user
- Database volume has restrictive permissions (700)
- Configuration volumes are read-only in containers
- No external volume mounts from untrusted sources

### 4. Firewall Integration

#### Supported Firewalls
- **UFW** (Ubuntu/Debian)
- **firewalld** (RHEL/CentOS/Fedora)
- **Windows Firewall** (Windows)

#### Firewall Rules
**Allowed (Inbound)**:
- TCP 8000 - Gap Detector API
- TCP 3000 - Windmill UI
- TCP 8080 - Nginx Proxy
- TCP 5000 - Analysis Engine API

**Blocked (Inbound)**:
- TCP 5432 - Direct database access

## Implementation

### Setup Scripts

#### Linux/macOS
```bash
# Apply security boundaries
./infra/podman/apply-security-boundaries.sh

# Test network isolation
./infra/podman/test-network-isolation.sh

# Monitor security status
./infra/podman/monitor-security.sh
```

#### Windows
```powershell
# Apply security boundaries
.\infra\podman\apply-security-boundaries.ps1

# Test network isolation
.\infra\podman\test-network-isolation.ps1

# Monitor security status
.\infra\podman\monitor-security.ps1
```

### Configuration Files

#### Security Policy Definition
- `security-boundaries.yaml` - Comprehensive security policy configuration
- Defines network zones, access rules, and security policies
- Used as reference for security implementation

#### Network Configuration
- Enhanced `podman-compose.yaml` with security labels
- Network isolation settings
- Container security options

## Security Testing

### Automated Tests

The security boundary implementation includes comprehensive testing:

#### Network Isolation Tests
- ✅ External port accessibility (8000, 3000, 8080, 5000)
- ✅ Database port isolation (5432 blocked externally)
- ✅ HTTP endpoint accessibility
- ✅ Inter-container DNS resolution
- ✅ Network configuration validation

#### Volume Security Tests
- ✅ Directory permissions (700 for db_data, 755 for others)
- ✅ File ownership (current user)
- ✅ Write access validation
- ✅ SELinux context verification (if enabled)

#### Container Security Tests
- ✅ Non-root execution verification
- ✅ Security options validation (no-new-privileges)
- ✅ Privileged access prevention
- ✅ User namespace mapping

### Manual Verification

#### Check Network Status
```bash
# List networks
podman network ls

# Inspect phoenix-net
podman network inspect phoenix-hydra_phoenix-net

# Check container networking
podman ps --format "table {{.Names}}\t{{.Ports}}"
```

#### Verify Container Security
```bash
# Check container users
podman inspect <container> --format "{{.Config.User}}"

# Check security options
podman inspect <container> --format "{{.HostConfig.SecurityOpt}}"

# Verify non-privileged execution
podman inspect <container> --format "{{.HostConfig.Privileged}}"
```

#### Test Port Accessibility
```bash
# Test external ports (should work)
curl -f http://localhost:8000/health
curl -f http://localhost:3000/api/version
curl -f http://localhost:8080/health
curl -f http://localhost:5000/health

# Test database port (should fail)
nc -z localhost 5432  # Should return non-zero exit code
```

## Monitoring and Alerting

### Security Monitoring

The system includes monitoring for:
- Unauthorized connection attempts
- Port scanning detection
- Unusual traffic patterns
- Privilege escalation attempts
- Capability violations
- Filesystem modifications
- Network policy violations
- Unauthorized volume access

### Log Analysis

Security events are logged and can be monitored:
```bash
# Container logs
podman logs <container-name>

# System logs (if systemd integration)
journalctl -u container-<service-name>

# Network traffic (if monitoring enabled)
tcpdump -i phoenix-br0
```

## Troubleshooting

### Common Issues

#### Permission Denied Errors
**Symptoms**: Container fails to start with permission errors
**Solutions**:
1. Check volume ownership: `ls -la ~/.local/share/phoenix-hydra`
2. Reset permissions: `./setup-volumes.sh` or `.\setup-volumes.ps1`
3. Verify user namespace mapping

#### Network Connectivity Issues
**Symptoms**: Services cannot communicate
**Solutions**:
1. Check network exists: `podman network ls`
2. Verify DNS resolution: `podman exec <container> nslookup <service>`
3. Test connectivity: `podman exec <container> nc -zv <service> <port>`

#### Firewall Blocking Access
**Symptoms**: External services not accessible
**Solutions**:
1. Check firewall rules: `ufw status` or `firewall-cmd --list-all`
2. Verify port binding: `netstat -tlnp | grep <port>`
3. Test local access: `curl localhost:<port>`

### Diagnostic Commands

```bash
# Network diagnostics
podman network inspect phoenix-hydra_phoenix-net
ip addr show phoenix-br0
iptables -L -n | grep phoenix

# Container diagnostics
podman inspect <container> | jq '.[] | {User: .Config.User, SecurityOpt: .HostConfig.SecurityOpt, Privileged: .HostConfig.Privileged}'

# Volume diagnostics
ls -la ~/.local/share/phoenix-hydra
stat ~/.local/share/phoenix-hydra/db_data
```

## Security Best Practices

### Development Environment
- Use the provided security scripts for consistent setup
- Regularly test network isolation
- Monitor security logs for anomalies
- Keep Podman and containers updated

### Production Environment
- Enable SELinux/AppArmor if available
- Implement additional network monitoring
- Use secrets management for sensitive data
- Regular security audits and penetration testing
- Backup security configurations

### Maintenance
- Regular security boundary testing
- Update firewall rules as needed
- Monitor for new security vulnerabilities
- Review and update security policies
- Document any security exceptions

## Compliance and Standards

### Security Standards Alignment
- **NIST Cybersecurity Framework**: Identify, Protect, Detect, Respond, Recover
- **CIS Controls**: Network segmentation, access control, monitoring
- **OWASP**: Container security best practices
- **Phoenix Hydra Principles**: Offline-first, privacy-focused, energy-efficient

### Audit Trail
- All security configurations are version controlled
- Changes tracked through Git history
- Security tests automated and documented
- Regular security reviews scheduled

This security boundary implementation ensures that Phoenix Hydra operates with defense-in-depth security while maintaining the system's core principles of privacy, local processing, and energy efficiency.