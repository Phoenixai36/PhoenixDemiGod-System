# Phoenix Hydra Podman Network Configuration

This document describes the network configuration for the Phoenix Hydra system running on Podman.

## Network Overview

The Phoenix Hydra system uses a custom bridge network called `phoenix-net` to enable communication between all services while maintaining security isolation.

### Network Specifications

- **Network Name**: `phoenix-net`
- **Driver**: `bridge`
- **Subnet**: `172.20.0.0/16`
- **Gateway**: `172.20.0.1`
- **IP Range**: `172.20.1.0/24` (for container assignment)
- **Bridge Name**: `phoenix-br0`
- **MTU**: `1500`

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    phoenix-net (172.20.0.0/16)             │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │gap-detector │  │recurrent-   │  │analysis-    │        │
│  │:8000        │  │processor    │  │engine:5000  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │db:5432      │  │windmill:3000│  │rubik-agent  │        │
│  │(PostgreSQL) │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐                                           │
│  │nginx:8080   │                                           │
│  │(Reverse     │                                           │
│  │Proxy)       │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## DNS Resolution

### Automatic Service Discovery

All services within the `phoenix-net` network can resolve each other by their service names:

- `db` → PostgreSQL database
- `windmill` → Windmill workflow engine
- `gap-detector` → Gap detection service
- `recurrent-processor` → Recurrent processing service
- `rubik-agent` → Rubik agent service
- `nginx` → Nginx reverse proxy
- `analysis-engine` → Analysis engine service

### DNS Configuration

The network is configured with:
- **IPv6**: Disabled for simplicity and performance
- **Internal**: False (allows external connectivity)
- **Attachable**: True (allows manual container attachment)
- **DNS Resolution**: Automatic via Podman's netavark/aardvark-dns

## Network Security

### Security Features

1. **Network Isolation**: Services are isolated from the host network
2. **Controlled Access**: Only specified ports are exposed to the host
3. **No Privileged Access**: All containers run without root privileges
4. **Security Options**: `no-new-privileges:true` for all services

### Exposed Ports

| Service         | Internal Port | External Port | Purpose                  |
| --------------- | ------------- | ------------- | ------------------------ |
| gap-detector    | 8000          | 8000          | API endpoint             |
| analysis-engine | 5000          | 5000          | Analysis API             |
| windmill        | 3000          | 3000          | Workflow UI              |
| nginx           | 8080          | 8080          | Reverse proxy            |
| db              | 5432          | -             | Database (internal only) |

## Network Testing

### Testing Scripts

Two network testing scripts are provided:

1. **Linux/macOS**: `test-network.sh`
2. **Windows**: `test-network.ps1`

### Running Network Tests

```bash
# Linux/macOS
./infra/podman/test-network.sh

# Windows PowerShell
.\infra\podman\test-network.ps1
```

### Test Coverage

The network tests verify:
- ✅ Service availability
- ✅ DNS resolution between services
- ✅ Network connectivity (TCP connections)
- ✅ External connectivity
- ✅ Network configuration details

## Troubleshooting

### Common Issues

#### DNS Resolution Failures

**Symptoms**: Services cannot resolve each other by name
**Solutions**:
1. Ensure all services are running and healthy
2. Check network configuration in `podman-compose.yaml`
3. Verify Podman's DNS service is running
4. Restart the network: `podman network rm phoenix-hydra_phoenix-net && podman-compose up -d`

#### Network Connectivity Issues

**Symptoms**: Services cannot connect to each other
**Solutions**:
1. Check firewall settings on the host
2. Verify port configurations in compose file
3. Ensure services are listening on correct interfaces (0.0.0.0, not 127.0.0.1)
4. Check container logs for binding errors

#### External Connectivity Issues

**Symptoms**: Containers cannot reach external services
**Solutions**:
1. Check host network connectivity
2. Verify DNS configuration on the host
3. Check proxy settings if behind corporate firewall
4. Ensure IP forwarding is enabled

### Diagnostic Commands

```bash
# List all networks
podman network ls

# Inspect the phoenix-net network
podman network inspect phoenix-hydra_phoenix-net

# Check container network configuration
podman inspect <container-name> --format '{{.NetworkSettings}}'

# Test DNS resolution from within a container
podman exec -it <container-name> nslookup <service-name>

# Test network connectivity
podman exec -it <container-name> nc -zv <service-name> <port>
```

## Network Performance

### Optimization Settings

The network is configured with the following optimizations:

- **MTU**: Set to 1500 for optimal performance
- **IP Masquerading**: Enabled for external connectivity
- **IPv6**: Disabled to reduce overhead
- **Bridge Configuration**: Optimized for container-to-container communication

### Performance Monitoring

Monitor network performance using:

```bash
# Network statistics
podman stats --format "table {{.Container}}\t{{.NetIO}}"

# Network interface statistics
ip -s link show phoenix-br0

# Container network usage
podman exec -it <container> cat /proc/net/dev
```

## Advanced Configuration

### Custom Network Settings

To modify network settings, edit the `networks` section in `podman-compose.yaml`:

```yaml
networks:
  phoenix-net:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: phoenix-br0
      com.docker.network.driver.mtu: "1500"
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

### Network Policies

For production deployments, consider implementing network policies:

```yaml
# Example network policy (requires additional configuration)
networks:
  phoenix-net:
    driver: bridge
    internal: true  # Disable external access
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"  # Disable inter-container communication
```

## Migration from Docker

### Key Differences

When migrating from Docker to Podman networking:

1. **Rootless Operation**: Networks run without root privileges
2. **DNS Backend**: Uses netavark/aardvark-dns instead of Docker's DNS
3. **Network Drivers**: Compatible with Docker network drivers
4. **Security**: Enhanced security with user namespaces

### Migration Checklist

- [x] Convert network configuration to Podman format
- [x] Update service DNS references (if any hardcoded IPs)
- [x] Test DNS resolution between services
- [x] Verify external connectivity
- [x] Update monitoring and logging configurations
- [x] Create network testing scripts
- [x] Document network architecture

## References

- [Podman Network Documentation](https://docs.podman.io/en/latest/markdown/podman-network.1.html)
- [Netavark Network Backend](https://github.com/containers/netavark)
- [Aardvark DNS](https://github.com/containers/aardvark-dns)
- [Phoenix Hydra Architecture Documentation](./README.md)