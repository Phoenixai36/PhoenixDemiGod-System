# Container Lifecycle Metrics

This module provides comprehensive container lifecycle monitoring capabilities, including event tracking, uptime monitoring, restart counting, and real-time event listening for Docker and Podman containers.

## Features

- **Real-time Event Monitoring**: Listen to container start, stop, restart, pause, and other lifecycle events
- **Uptime Tracking**: Track total uptime and current session uptime for containers
- **Restart Counting**: Monitor container restart patterns and frequencies
- **Event History**: Maintain a searchable history of container lifecycle events
- **Multi-Runtime Support**: Support for both Docker and Podman container runtimes
- **Metrics Collection**: Export metrics in Prometheus-compatible format
- **Statistical Analysis**: Generate restart and uptime statistics

## Components

### ContainerLifecycleCollector

The main collector class that tracks container states and generates metrics.

```python
from src.metrics.lifecycle import ContainerLifecycleCollector

collector = ContainerLifecycleCollector()

# Record events manually
event = ContainerLifecycleEvent(
    container_id="container123",
    container_name="my-app",
    event_type=ContainerEvent.STARTED,
    timestamp=datetime.now()
)
collector.record_event(event)

# Collect metrics
metrics = await collector.collect_metrics()
```

### Event Listeners

Event listeners integrate with container runtimes to capture real-time events.

#### Docker Event Listener

```python
from src.metrics.lifecycle import DockerEventListener

def handle_event(event):
    print(f"Container {event.container_name} {event.event_type.value}")

listener = DockerEventListener(handle_event)
await listener.start_listening()
```

#### Podman Event Listener

```python
from src.metrics.lifecycle import PodmanEventListener

listener = PodmanEventListener(handle_event)
await listener.start_listening()
```

### Integration Monitor

The `ContainerLifecycleMonitor` class provides a complete monitoring solution.

```python
from src.metrics.lifecycle.integration_example import ContainerLifecycleMonitor

monitor = ContainerLifecycleMonitor(container_runtime="docker")
await monitor.start_monitoring()

# Get statistics
restart_stats = monitor.get_restart_statistics()
uptime_stats = monitor.get_uptime_statistics()
recent_events = monitor.get_recent_events()

await monitor.stop_monitoring()
```

## Metrics Generated

The lifecycle collector generates the following metrics:

### Container-Specific Metrics

- `container_uptime_seconds`: Total uptime for each container
- `container_restart_count`: Number of restarts for each container
- `container_running`: Whether the container is currently running (0 or 1)
- `container_time_since_start_seconds`: Time since the container was last started

### Global Metrics

- `containers_total`: Total number of tracked containers
- `containers_running`: Number of currently running containers
- `containers_stopped`: Number of currently stopped containers

## Event Types

The following container events are tracked:

- `STARTED`: Container was started
- `STOPPED`: Container was stopped
- `RESTARTED`: Container was restarted
- `DIED`: Container died unexpectedly
- `KILLED`: Container was killed
- `PAUSED`: Container was paused
- `UNPAUSED`: Container was unpaused

## Configuration

### Docker Configuration

For Docker integration, ensure the Docker daemon is running and accessible:

```bash
# Check Docker daemon status
docker info

# Install Docker Python SDK
pip install docker
```

### Podman Configuration

For Podman integration, ensure the Podman socket is available:

```bash
# Enable Podman socket
systemctl --user enable podman.socket
systemctl --user start podman.socket

# Install aiohttp for HTTP API access
pip install aiohttp
```

## Usage Examples

### Basic Event Tracking

```python
import asyncio
from datetime import datetime
from src.metrics.lifecycle import (
    ContainerLifecycleCollector,
    ContainerLifecycleEvent,
    ContainerEvent
)

async def basic_example():
    collector = ContainerLifecycleCollector()
    
    # Simulate container lifecycle
    start_event = ContainerLifecycleEvent(
        container_id="app123",
        container_name="my-web-app",
        event_type=ContainerEvent.STARTED,
        timestamp=datetime.now()
    )
    collector.record_event(start_event)
    
    # Collect metrics
    metrics = await collector.collect_metrics()
    for metric in metrics:
        print(f"{metric.name}: {metric.value}")

asyncio.run(basic_example())
```

### Real-time Monitoring

```python
import asyncio
from src.metrics.lifecycle import EventListenerFactory, ContainerLifecycleCollector

async def realtime_example():
    collector = ContainerLifecycleCollector()
    
    # Create event listener
    listener = EventListenerFactory.create_listener(
        "docker", 
        collector.record_event
    )
    
    # Start listening
    await listener.start_listening()
    
    # Monitor for 60 seconds
    await asyncio.sleep(60)
    
    # Get statistics
    stats = collector.get_restart_statistics()
    print(f"Monitored {stats['total_containers']} containers")
    print(f"Total restarts: {stats['total_restarts']}")
    
    await listener.stop_listening()

asyncio.run(realtime_example())
```

### Statistical Analysis

```python
from datetime import datetime, timedelta
from src.metrics.lifecycle import ContainerLifecycleCollector

collector = ContainerLifecycleCollector()
# ... add some events ...

# Get restart statistics
restart_stats = collector.get_restart_statistics()
print(f"Containers with restarts: {restart_stats['containers_with_restarts']}")
print(f"Average restarts per container: {restart_stats['average_restarts_per_container']}")

# Get uptime statistics
uptime_stats = collector.get_uptime_statistics()
print(f"Total uptime: {uptime_stats['total_uptime_seconds']} seconds")
print(f"Running containers: {uptime_stats['running_containers']}")

# Get recent events
recent_events = collector.get_container_events(limit=10)
for event in recent_events:
    print(f"{event.timestamp}: {event.container_name} - {event.event_type.value}")
```

## Testing

Run the test suite to verify functionality:

```bash
# Run lifecycle collector tests
pytest tests/test_lifecycle_collector.py -v

# Run event listener tests
pytest tests/test_event_listener.py -v

# Run all lifecycle tests
pytest tests/test_*lifecycle* -v
```

## Integration with Metrics System

The lifecycle collector integrates with the broader metrics collection system:

```python
from src.metrics.collector_factory import collector_factory

# Register the lifecycle collector
collector_factory.register_collector_type("lifecycle", ContainerLifecycleCollector)

# Create via factory
config = CollectorConfig(
    name="container_lifecycle",
    enabled=True,
    collection_interval=30
)
collector = collector_factory.create_collector("lifecycle", config)
```

## Troubleshooting

### Docker Connection Issues

```python
# Check Docker availability
from src.metrics.lifecycle import EventListenerFactory

available = EventListenerFactory.get_available_runtimes()
if not available["docker"]:
    print("Docker SDK not available. Install with: pip install docker")
```

### Podman Connection Issues

```python
# Check Podman socket
import aiohttp
import asyncio

async def check_podman():
    try:
        connector = aiohttp.UnixConnector(path="/run/podman/podman.sock")
        session = aiohttp.ClientSession(connector=connector)
        async with session.get("http://localhost/v1.0.0/libpod/info") as response:
            if response.status == 200:
                print("Podman API accessible")
            else:
                print(f"Podman API error: {response.status}")
        await session.close()
    except Exception as e:
        print(f"Podman connection failed: {e}")

asyncio.run(check_podman())
```

### Event History Management

```python
# Clear old events to manage memory
from datetime import datetime, timedelta

collector = ContainerLifecycleCollector()

# Clear events older than 1 hour
one_hour_ago = datetime.now() - timedelta(hours=1)
cleared_count = collector.clear_history(before=one_hour_ago)
print(f"Cleared {cleared_count} old events")

# Set maximum history size
collector.max_history_size = 5000  # Keep last 5000 events
```

## Performance Considerations

- **Event History Size**: Configure `max_history_size` to prevent memory issues
- **Collection Interval**: Adjust collection interval based on monitoring needs
- **Event Filtering**: Use event filtering to focus on relevant events
- **Resource Usage**: Monitor the collector's own resource usage in production

## Security Considerations

- **Container Runtime Access**: Ensure proper permissions for Docker/Podman access
- **Event Data**: Be aware that events may contain sensitive container information
- **Network Access**: Podman HTTP API access should be properly secured
- **Log Sanitization**: Sanitize container names and metadata in logs if needed