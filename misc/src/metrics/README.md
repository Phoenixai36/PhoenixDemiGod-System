# Metrics Collector Framework

A comprehensive framework for collecting metrics from containerized applications in the Phoenix system. This framework provides a flexible, extensible architecture for gathering performance and health metrics from Docker and Podman containers.

## Features

- **Multi-Runtime Support**: Works with both Docker and Podman container runtimes
- **Extensible Architecture**: Easy to add new collector types and metrics
- **Error Handling**: Robust error handling with retry mechanisms and health monitoring
- **Prometheus Integration**: Built-in support for Prometheus metric format
- **Async/Await Support**: Fully asynchronous for high performance
- **Factory Pattern**: Easy collector creation and configuration
- **Registry System**: Centralized collector management

## Architecture

The framework consists of several key components:

### Core Models

- **MetricValue**: Represents a single metric with timestamp, labels, and metadata
- **ContainerMetrics**: Container-specific metrics collection
- **CollectorConfig**: Configuration for individual collectors
- **CollectorStatus**: Status tracking for collector health

### Collector Interface

- **MetricsCollector**: Abstract base class for all collectors
- **ContainerMetricsCollector**: Base class for container-specific collectors
- **SystemMetricsCollector**: Base class for system-wide collectors
- **CollectorRegistry**: Manages multiple collectors

### Built-in Collectors

- **CPUCollector**: Collects CPU usage metrics
- **MemoryCollector**: Collects memory usage and limits
- **NetworkCollector**: Collects network I/O statistics
- **DiskCollector**: Collects disk I/O statistics
- **LifecycleCollector**: Collects container lifecycle metrics (uptime, restarts, status)

## Quick Start

### Basic Usage

```python
import asyncio
from src.metrics import collector_factory, CollectorRegistry

async def collect_metrics():
    # Create a registry
    registry = CollectorRegistry()
    
    # Create default collectors
    collectors = collector_factory.create_default_collectors()
    
    # Register collectors
    for name, collector in collectors.items():
        registry.register_collector(collector)
    
    # Initialize all collectors
    await registry.initialize_all()
    
    # Collect metrics for a container
    container_id = "your_container_id"
    metrics = await registry.collect_all_metrics(container_id)
    
    # Process metrics
    for metric in metrics:
        print(f"{metric.name}: {metric.value} {metric.unit}")
    
    # Cleanup
    await registry.cleanup_all()

# Run the example
asyncio.run(collect_metrics())
```

### Custom Collector Creation

```python
from src.metrics import create_collector_builder

# Create a custom collector using the builder pattern
collector = (create_collector_builder()
            .name("custom_cpu_monitor")
            .enabled(True)
            .interval(30)  # Collect every 30 seconds
            .timeout(10)   # 10 second timeout
            .custom_labels({"environment": "production"})
            .build("cpu"))

if collector:
    await collector.initialize()
    metrics = await collector.collect_with_error_handling("container_id")
    await collector.cleanup()
```

### Creating Custom Collectors

```python
from src.metrics.collector_interface import ContainerMetricsCollector
from src.metrics.models import MetricValue, MetricType, CollectorConfig

class CustomCollector(ContainerMetricsCollector):
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
    
    async def initialize(self) -> bool:
        # Initialize your collector
        return True
    
    async def cleanup(self) -> None:
        # Clean up resources
        pass
    
    def get_metric_types(self) -> List[MetricType]:
        return [MetricType.CUSTOM]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        # Implement your metric collection logic
        return [
            MetricValue(
                name="custom_metric",
                value=42.0,
                timestamp=datetime.now(),
                labels={"container_id": container_id}
            )
        ]

# Register your custom collector
from src.metrics import collector_factory
collector_factory.register_collector_type("custom", CustomCollector)
```

## Configuration

### Collector Configuration

Each collector can be configured with the following parameters:

```python
from src.metrics.models import CollectorConfig

config = CollectorConfig(
    name="my_collector",
    enabled=True,
    collection_interval=30,  # seconds
    timeout=10,              # seconds
    retry_attempts=3,
    retry_delay=5,           # seconds
    custom_labels={"env": "prod"},
    parameters={"custom_param": "value"}
)
```

### Environment Variables

The collectors can be configured using environment variables:

- `METRICS_COLLECTION_INTERVAL`: Default collection interval (seconds)
- `METRICS_TIMEOUT`: Default timeout for collection operations (seconds)
- `METRICS_RETRY_ATTEMPTS`: Number of retry attempts on failure
- `METRICS_LOG_LEVEL`: Logging level for collectors

## Metrics

### CPU Metrics

- `container_cpu_usage_percent`: CPU usage percentage

### Memory Metrics

- `container_memory_usage_bytes`: Memory usage in bytes
- `container_memory_limit_bytes`: Memory limit in bytes
- `container_memory_usage_percent`: Memory usage percentage

### Network Metrics

- `container_network_receive_bytes_total`: Total bytes received
- `container_network_transmit_bytes_total`: Total bytes transmitted
- `container_network_receive_packets_total`: Total packets received
- `container_network_transmit_packets_total`: Total packets transmitted

### Disk Metrics

- `container_disk_read_bytes_total`: Total bytes read from disk
- `container_disk_write_bytes_total`: Total bytes written to disk
- `container_disk_read_ops_total`: Total disk read operations
- `container_disk_write_ops_total`: Total disk write operations

### Lifecycle Metrics

- `container_uptime_seconds`: Container uptime in seconds
- `container_restarts_total`: Total number of container restarts
- `container_status`: Container status as numeric value
- `container_exit_code`: Exit code for stopped containers

## Prometheus Integration

All metrics are automatically formatted for Prometheus consumption:

```python
# Get metrics in Prometheus format
for metric in metrics:
    prometheus_line = metric.to_prometheus_format()
    print(prometheus_line)
```

Example output:
```
container_cpu_usage_percent{container_id="abc123",container_name="web-server",image="nginx:latest"} 45.2 1640995200000
container_memory_usage_bytes{container_id="abc123",container_name="web-server",image="nginx:latest"} 134217728 1640995200000
```

## Error Handling

The framework includes comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff
- **Health Monitoring**: Collectors are marked unhealthy after repeated failures
- **Graceful Degradation**: System continues operating even if some collectors fail
- **Detailed Logging**: Comprehensive logging for troubleshooting

## Testing

Run the unit tests:

```bash
python -m pytest tests/test_metrics_collector.py -v
```

Run the demo script:

```bash
python examples/metrics_collector_demo.py
```

## Performance Considerations

- **Async Operations**: All collection operations are asynchronous
- **Configurable Intervals**: Adjust collection frequency based on needs
- **Resource Monitoring**: Built-in monitoring of collector resource usage
- **Batch Collection**: Efficient batch collection from multiple containers

## Extending the Framework

### Adding New Metric Types

1. Add new metric type to `MetricType` enum
2. Create a new collector class inheriting from appropriate base class
3. Register the collector type with the factory
4. Implement the required abstract methods

### Adding New Container Runtimes

1. Extend existing collectors to support new runtime
2. Add runtime detection logic
3. Implement runtime-specific metric collection methods

## Troubleshooting

### Common Issues

1. **Container Runtime Not Available**
   - Ensure Docker or Podman is installed and running
   - Check permissions for accessing container runtime

2. **Permission Denied**
   - Ensure the application has permissions to access container APIs
   - For Docker, user may need to be in the `docker` group

3. **High Resource Usage**
   - Increase collection intervals
   - Disable unnecessary collectors
   - Monitor collector health status

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("collector").setLevel(logging.DEBUG)
```

Check collector status:

```python
status = collector.get_status()
print(f"Healthy: {status.is_healthy}")
print(f"Last error: {status.last_error}")
print(f"Error count: {status.error_count}")
```

## Contributing

1. Follow the existing code patterns
2. Add unit tests for new functionality
3. Update documentation
4. Ensure all tests pass
5. Follow Python PEP 8 style guidelines

## License

This framework is part of the Phoenix DemiGod system and follows the same licensing terms.