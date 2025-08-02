# Phoenix Hydra Podman Compose Reference

## Quick Start Commands

```bash
# Start all services
podman-compose -f podman-compose.yaml up -d

# Check service status
podman-compose -f podman-compose.yaml ps

# View logs
podman-compose -f podman-compose.yaml logs -f

# Stop all services
podman-compose -f podman-compose.yaml down

# Restart specific service
podman-compose -f podman-compose.yaml restart [service-name]
```

## Service Endpoints

| Service             | Port | Health Check   | Description          |
| ------------------- | ---- | -------------- | -------------------- |
| gap-detector        | 8000 | `/health`      | Gap detection system |
| analysis-engine     | 5000 | `/health`      | Analysis engine      |
| windmill            | 3000 | `/api/version` | Workflow management  |
| nginx               | 8080 | `/health`      | Reverse proxy        |
| db                  | 5432 | Internal       | PostgreSQL database  |
| recurrent-processor | -    | Internal       | Background processor |
| rubik-agent         | -    | Internal       | Task orchestration   |

## Network Configuration

- **Network Name**: `phoenix-net`
- **Subnet**: `172.20.0.0/16`
- **Gateway**: `172.20.0.1`
- **Driver**: `bridge`

## Volume Configuration

- **Database Data**: `~/.local/share/phoenix-hydra/db_data`
- **Nginx Config**: `./nginx/nginx.conf` (read-only)

## Security Features

- **Rootless Execution**: All containers run as non-root users
- **User Mapping**: Services use UID/GID 1000:1000 or service-specific users
- **Security Options**: `no-new-privileges:true` enabled
- **Network Isolation**: Services communicate only through `phoenix-net`
- **SELinux Labels**: Volumes use `:Z` flag for proper labeling

## Environment Variables

### Database Configuration
- `POSTGRES_USER=windmill_user`
- `POSTGRES_PASSWORD=phoenix_demigod`
- `POSTGRES_DB=windmill`

### Application Configuration
- `APP_ENV=development`
- `PYTHONPATH=/app`
- `DATABASE_URL=postgresql://windmill_user:phoenix_demigod@db:5432/windmill`

## Health Checks

All services include comprehensive health monitoring:

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3-5 attempts
- **Start Period**: 30-60 seconds

## Dependency Chain

```
nginx
├── windmill (healthy)
├── recurrent-processor (healthy)
├── db (healthy)
└── rubik-agent (healthy)

windmill
└── db (healthy)

gap-detector
└── recurrent-processor

recurrent-processor
└── db
```

## Troubleshooting

### Service Won't Start
1. Check logs: `podman-compose logs [service-name]`
2. Verify Containerfile exists
3. Check port conflicts
4. Validate volume permissions

### Network Issues
1. Verify network exists: `podman network ls`
2. Check service connectivity: `podman exec -it [container] ping [service]`
3. Restart network: `podman network rm phoenix-net && podman-compose up -d`

### Volume Issues
1. Check permissions: `ls -la ~/.local/share/phoenix-hydra/`
2. Fix ownership: `chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra/`
3. Verify SELinux context (RHEL/CentOS): `ls -Z ~/.local/share/phoenix-hydra/`

## Performance Monitoring

```bash
# Resource usage
podman stats

# Service-specific stats
podman stats phoenix-hydra_gap-detector_1

# Network traffic
podman network inspect phoenix-net
```