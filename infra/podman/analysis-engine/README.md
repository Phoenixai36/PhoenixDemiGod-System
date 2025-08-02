# Phoenix Hydra Analysis Engine

SSM-based (State Space Model) analysis engine for system component analysis with energy-efficient processing.

## Overview

The Analysis Engine provides non-Transformer based AI analysis using State Space Models (SSM) for:
- Component health monitoring
- Temporal pattern analysis
- Performance optimization suggestions
- Energy consumption tracking

## Features

- **Energy Efficient**: 60-70% less energy consumption compared to Transformer-based models
- **Rootless Execution**: Runs without root privileges for enhanced security
- **Local Processing**: No external dependencies or cloud connectivity required
- **Prometheus Metrics**: Built-in metrics collection and monitoring
- **Async Processing**: Non-blocking analysis with concurrent component processing

## Configuration

### Environment Variables

- `PROMETHEUS_PORT`: Port for Prometheus metrics (default: 8090)
- `ANALYSIS_INTERVAL`: Analysis interval in seconds (default: 30)
- `PYTHONUNBUFFERED`: Enable unbuffered Python output (default: 1)

### SSM Configuration

The engine uses the following SSM parameters optimized for local processing:
- Model dimension: 256 (reduced for efficiency)
- State dimension: 32
- Convolution width: 4
- Memory efficient mode: enabled

## Building and Running

### Build Container Image

```bash
# Build with Podman
podman build -t phoenix-hydra/analysis-engine -f infra/podman/analysis-engine/Containerfile .

# Build with specific tag
podman build -t phoenix-hydra/analysis-engine:latest -f infra/podman/analysis-engine/Containerfile .
```

### Run Container

```bash
# Run standalone
podman run -d \
  --name analysis-engine \
  -p 8090:8090 \
  --security-opt no-new-privileges:true \
  --user 1000:1000 \
  phoenix-hydra/analysis-engine:latest

# Run with custom configuration
podman run -d \
  --name analysis-engine \
  -p 8090:8090 \
  -e ANALYSIS_INTERVAL=60 \
  -e PROMETHEUS_PORT=8090 \
  --security-opt no-new-privileges:true \
  --user 1000:1000 \
  phoenix-hydra/analysis-engine:latest
```

### Run with Podman Compose

The analysis-engine is integrated into the Phoenix Hydra stack via `podman-compose.yaml`:

```yaml
services:
  analysis-engine:
    build:
      context: .
      dockerfile: infra/podman/analysis-engine/Containerfile
    ports:
      - "8090:8090"
    environment:
      - ANALYSIS_INTERVAL=30
      - PROMETHEUS_PORT=8090
    networks:
      - phoenix-net
    security_opt:
      - no-new-privileges:true
    user: "1000:1000"
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8090/metrics', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

## API Endpoints

### Prometheus Metrics
- **URL**: `http://localhost:8090/metrics`
- **Method**: GET
- **Description**: Prometheus-compatible metrics endpoint

### Available Metrics

- `analysis_requests_total`: Total number of analysis requests
- `analysis_duration_seconds`: Analysis duration histogram
- `energy_consumption_watts`: Current energy consumption estimate
- `component_health_score`: Health score per component

## Component Analysis

The engine analyzes components with the following data structure:

```python
component = {
    "id": "component-name",
    "performance": {
        "cpu_usage": 45.2,      # CPU usage percentage
        "memory_usage": 62.1,   # Memory usage percentage
        "latency": 150.5,       # Response latency in ms
        "throughput": 120.3     # Requests per second
    },
    "system_state": {
        "temperature": 55.0,    # Temperature in Celsius
        "power_consumption": 85.2, # Power consumption in Watts
        "error_rate": 0.01      # Error rate (0-1)
    },
    "health": {
        "uptime": 0.99,         # Uptime percentage
        "response_time": 120.5, # Average response time in ms
        "success_rate": 0.995   # Success rate (0-1)
    }
}
```

## Analysis Output

The engine provides comprehensive analysis results:

```python
{
    "timestamp": 1640995200.0,
    "component_analysis": {
        "component-id": {
            "component_health": {
                "health_score": 0.85,
                "stability_score": 0.92,
                "status": "healthy",
                "anomaly_count": 0
            },
            "temporal_behavior": {
                "trend": 0.02,
                "stability": 0.88,
                "temporal_score": 0.75
            },
            "optimization_suggestions": [
                "Component operating within normal parameters"
            ]
        }
    },
    "temporal_patterns": {
        "patterns": ["temporal_analysis_available"],
        "overall_trend": 0.01,
        "stability": 0.89
    },
    "performance_metrics": {
        "system_cpu_percent": 35.2,
        "system_memory_percent": 58.1,
        "analysis_engine_uptime": 3600.0,
        "total_analyses_performed": 120,
        "components_in_memory": 5
    },
    "energy_consumption": {
        "current_power_watts": 45.2,
        "efficiency_score": 0.85
    },
    "health_summary": {
        "overall_status": "healthy",
        "average_health_score": 0.82,
        "healthy_components": 4,
        "total_components": 5,
        "health_percentage": 80.0
    }
}
```

## Security Features

- **Rootless execution**: Runs as non-root user (analysisuser)
- **No new privileges**: Container cannot escalate privileges
- **Minimal base image**: Uses Python slim image for reduced attack surface
- **User namespace mapping**: Proper UID/GID mapping for rootless containers
- **Health checks**: Built-in health monitoring

## Monitoring and Logging

- **Structured logging**: JSON-formatted logs for easy parsing
- **Prometheus integration**: Comprehensive metrics collection
- **Health checks**: Container and application health monitoring
- **Energy tracking**: Power consumption estimation and reporting

## Troubleshooting

### Common Issues

1. **Permission denied errors**
   - Ensure proper user namespace mapping
   - Check file ownership and permissions

2. **Health check failures**
   - Verify Prometheus metrics endpoint is accessible
   - Check if the analysis engine is running properly

3. **High memory usage**
   - Reduce model dimensions in SSMAnalysisConfig
   - Enable memory-efficient mode

4. **Analysis errors**
   - Check component data format
   - Verify all required fields are present

### Debug Commands

```bash
# Check container logs
podman logs analysis-engine

# Execute shell in container
podman exec -it analysis-engine /bin/bash

# Check metrics endpoint
curl http://localhost:8090/metrics

# Monitor resource usage
podman stats analysis-engine
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements-analysis-engine.txt

# Run locally
python src/core/ssm_analysis_engine.py

# Run tests
pytest tests/unit/test_analysis_engine.py
```

### Testing

```bash
# Build and test container
podman build -t test-analysis-engine -f infra/podman/analysis-engine/Containerfile .
podman run --rm -p 8090:8090 test-analysis-engine

# Verify metrics endpoint
curl http://localhost:8090/metrics
```

## Integration

The Analysis Engine integrates with other Phoenix Hydra components:
- **Gap Detector**: Provides component data for analysis
- **Recurrent Processor**: Shares temporal analysis capabilities
- **Monitoring Stack**: Exports metrics to Prometheus
- **Event Bus**: Publishes analysis results to system events

## Performance

- **Startup time**: < 10 seconds
- **Analysis latency**: < 500ms per component
- **Memory usage**: < 512MB typical
- **CPU usage**: < 20% on modern hardware
- **Energy efficiency**: 60-70% reduction vs Transformer models