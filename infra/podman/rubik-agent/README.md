# RUBIK Agent Service

This directory contains the Podman configuration for the RUBIK Agent service, which provides an HTTP API gateway for the Phoenix Hydra RUBIK biomimetic agent system.

## Structure

- `Containerfile` - Container build definition for Podman with Alpine base and rootless execution
- `config/` - Service-specific configuration files
  - `rubik-agent.yaml` - Main service configuration
- `test_containerfile.sh` - Linux/macOS test script for the Containerfile
- `test_containerfile.ps1` - Windows PowerShell test script for the Containerfile
- `requirements-rubik-agent.txt` - Python dependencies (located in project root)

## Purpose

The RUBIK Agent service serves as an HTTP API gateway for the Phoenix Hydra RUBIK biomimetic agent system. It provides:

- Health check endpoints for container orchestration
- RESTful API for agent management and task submission
- Prometheus metrics for monitoring
- Status reporting and ecosystem information
- Integration with the 20-base logarithmic matrix genetic system

## Features

- **Rootless Execution**: Runs as non-root user (appuser:1000) for enhanced security
- **Alpine Base**: Lightweight Alpine Linux base image for minimal attack surface
- **Health Checks**: Built-in health check endpoint for container orchestration
- **Metrics**: Prometheus metrics endpoint for monitoring and observability
- **Structured Logging**: JSON-formatted structured logging with configurable levels
- **API Gateway**: RESTful API for interacting with RUBIK biomimetic agents

## API Endpoints

- `GET /health` - Health check for container orchestration
- `GET /status` - Detailed service status information
- `GET /metrics` - Prometheus metrics endpoint
- `GET /agents` - List active RUBIK agents
- `POST /agents/task` - Submit tasks to the RUBIK ecosystem
- `GET /ecosystem/status` - Get RUBIK ecosystem status
- `GET /` - Service information and API documentation

## Building and Testing

### Build the container image:
```bash
# From project root
podman build -f infra/podman/rubik-agent/Containerfile -t phoenix-hydra/rubik-agent .
```

### Run tests:
```bash
# Linux/macOS
./infra/podman/rubik-agent/test_containerfile.sh

# Windows PowerShell
.\infra\podman\rubik-agent\test_containerfile.ps1
```

### Run the container:
```bash
podman run -d \
  --name rubik-agent \
  -p 8080:8080 \
  -v ./infra/podman/rubik-agent/config:/app/config:ro \
  phoenix-hydra/rubik-agent
```

## Configuration

The service can be configured through:
- Environment variables (RUBIK_AGENT_HOST, RUBIK_AGENT_PORT)
- Configuration file at `/app/config/rubik-agent.yaml`
- Command line arguments (future enhancement)

## Security Features

- Non-root user execution (UID/GID 1000)
- Minimal Alpine Linux base image
- No privileged operations required
- Health check integration
- Resource usage monitoring
- Structured logging for security auditing

## Integration

This service integrates with:
- Phoenix Hydra RUBIK biomimetic agent ecosystem
- Prometheus monitoring stack
- Container orchestration systems (Podman Compose, Kubernetes)
- Phoenix Hydra event bus system
- 2025 advanced AI model stack