# Phoenix Hydra Nginx Containerfile

This directory contains the Podman-compatible Containerfile for the nginx reverse proxy service in the Phoenix Hydra stack.

## Features

- **Rootless execution**: Runs as non-root user (nginx-user:1000)
- **Security optimized**: Uses Alpine base image with minimal attack surface
- **Non-privileged port**: Listens on port 8080 instead of port 80
- **Health check endpoint**: Provides `/health` endpoint for monitoring
- **WebSocket support**: Configured for real-time connections
- **Security headers**: Includes standard security headers

## Configuration

### Port Mapping
- Container port: 8080 (non-privileged)
- Host port: 8080 (mapped in compose configuration)

### Volume Mounts
- Configuration: `./nginx.conf:/etc/nginx/conf.d/default.conf`

### Proxy Configuration
- `/windmill/` → `http://windmill:3000/`
- `/health` → Health check endpoint
- `/` → Default Phoenix Hydra gateway response

## Building

```bash
# Build the image
podman build -t phoenix-hydra/nginx -f Containerfile .

# Run standalone (for testing)
podman run -d --name nginx-test -p 8080:8080 phoenix-hydra/nginx
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test default endpoint
curl http://localhost:8080/

# Test proxy (requires windmill service)
curl http://localhost:8080/windmill/
```

## Security Features

1. **Non-root execution**: All processes run as nginx-user (UID 1000)
2. **Minimal permissions**: Only necessary directories are writable
3. **Security headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
4. **Non-privileged port**: Uses port 8080 to avoid requiring root privileges
5. **Alpine base**: Minimal attack surface with Alpine Linux

## Troubleshooting

### Permission Issues
If you encounter permission issues, ensure the nginx-user has proper access:
```bash
podman exec -it <container-name> ls -la /var/log/nginx
podman exec -it <container-name> ls -la /var/cache/nginx
```

### Configuration Issues
Check nginx configuration syntax:
```bash
podman exec -it <container-name> nginx -t
```

### Log Access
View nginx logs:
```bash
podman logs <container-name>
podman exec -it <container-name> tail -f /var/log/nginx/access.log
podman exec -it <container-name> tail -f /var/log/nginx/error.log
```