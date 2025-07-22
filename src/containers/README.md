# Container Management System

A comprehensive container management system with support for both Podman and Docker, featuring real-time event monitoring, container discovery, and lifecycle management.

## Features

### 🐳 **Podman-First Design**
- **Rootless Containers**: Better security with rootless operation
- **Daemonless Architecture**: No background daemon required
- **Pod Support**: Kubernetes-like pod management
- **OCI Compliance**: Full OCI container specification support
- **Docker Fallback**: Automatic fallback to Docker when Podman unavailable

### 📡 **Real-Time Event Monitoring**
- **Event Streaming**: Real-time container lifecycle events
- **Event Filtering**: Filter by event type, container name, labels
- **Batch Processing**: Efficient event batching and processing
- **Auto-Reconnection**: Automatic reconnection with exponential backoff
- **Event Handlers**: Synchronous and asynchronous event handlers

### 🔍 **Container Discovery**
- **Automatic Discovery**: Discover existing containers on startup
- **Registry Integration**: Maintain container registry with current state
- **Status Synchronization**: Keep container status in sync
- **Metadata Extraction**: Extract and store container metadata

### 📊 **Resource Monitoring**
- **Real-Time Stats**: CPU, memory, network, and disk I/O statistics
- **Streaming Stats**: Continuous statistics streaming
- **Historical Data**: Store and retrieve historical metrics
- **Performance Monitoring**: Track container performance over time

## Quick Start

### Basic Container Operations

```python
import asyncio
from src.containers import PodmanClient, PodmanConfig

async def main():
    # Create client with auto-detection
    config = PodmanConfig(auto_detect=True, fallback_to_docker=True)
    
    async with PodmanClient(config) as client:
        # List all containers
        containers = await client.list_containers()
        
        for container in containers:
            print(f"{container.name}: {container.status.value}")
            
            # Get detailed stats for running containers
            if container.status.value == "running":
                stats = await client.get_container_stats(container.id)
                print(f"  CPU: {stats.cpu_percent:.1f}%")
                print(f"  Memory: {stats.memory_percent:.1f}%")

asyncio.run(main())
```

### Event Monitoring

```python
import asyncio
from src.containers import ContainerEventListener, EventListenerConfig, EventType

async def main():
    # Configure event listener
    config = EventListenerConfig(
        event_types={EventType.CONTAINER_START, EventType.CONTAINER_STOP},
        discover_existing_containers=True
    )
    
    listener = ContainerEventListener(config)
    
    # Add event handler
    def on_container_event(event):
        print(f"Container {event.action}: {event.container_name}")
    
    listener.add_event_handler(on_container_event)
    
    # Start listening
    async with listener:
        await asyncio.sleep(60)  # Listen for 1 minute

asyncio.run(main())
```

## Components

### PodmanClient

The main client for interacting with Podman/Docker APIs.

#### Configuration

```python
from src.containers import PodmanConfig

config = PodmanConfig(
    # Connection settings
    socket_path="/run/user/1000/podman/podman.sock",  # Auto-detected
    remote_url="http://remote-host:8080",             # For remote Podman
    api_version="v4.0.0",                             # API version
    
    # Authentication (for remote)
    username="user",
    password="pass",
    identity_file="/path/to/ssh/key",
    
    # Behavior
    auto_detect=True,           # Auto-detect Podman installation
    fallback_to_docker=True,    # Fallback to Docker if needed
    use_cli_fallback=True,      # Use CLI if API unavailable
    
    # Timeouts
    connect_timeout=10.0,
    request_timeout=30.0
)
```

#### Container Operations

```python
async with PodmanClient(config) as client:
    # Container lifecycle
    await client.start_container("container_id")
    await client.stop_container("container_id", timeout=10)
    await client.restart_container("container_id")
    await client.remove_container("container_id", force=True)
    
    # Information gathering
    containers = await client.list_containers(all_containers=True)
    container = await client.get_container("container_id")
    stats = await client.get_container_stats("container_id")
    logs = await client.get_container_logs("container_id", tail=100)
    
    # Podman-specific features
    pods = await client.list_pods()
    
    # System information
    version = await client.get_version()
    info = await client.get_system_info()
```

#### Streaming Operations

```python
# Stream container statistics
stats_stream = await client.get_container_stats("container_id", stream=True)
async for stats in stats_stream:
    print(f"CPU: {stats.cpu_percent:.1f}%")

# Stream container logs
logs_stream = await client.get_container_logs("container_id", follow=True)
async for log_line in logs_stream:
    print(log_line)

# Stream system events
events_stream = client.get_events()
async for event in events_stream:
    print(f"Event: {event.action} - {event.container_name}")
```

### ContainerEventListener

Real-time container event monitoring with filtering and processing capabilities.

#### Configuration

```python
from src.containers import EventListenerConfig, EventType

config = EventListenerConfig(
    # Event filtering
    event_types={
        EventType.CONTAINER_START,
        EventType.CONTAINER_STOP,
        EventType.CONTAINER_DIE,
        EventType.CONTAINER_REMOVE
    },
    container_filters={"name": "web-", "label.app": "production"},
    
    # Connection behavior
    auto_reconnect=True,
    reconnect_delay=5.0,
    max_reconnect_attempts=10,
    
    # Event processing
    event_buffer_size=1000,
    event_batch_size=10,
    event_batch_timeout=1.0,
    
    # Startup behavior
    discover_existing_containers=True,
    sync_on_startup=True
)
```

#### Event Handlers

```python
listener = ContainerEventListener(config)

# Synchronous handler
def sync_handler(event):
    print(f"Sync: {event.action} - {event.container_name}")

# Asynchronous handler
async def async_handler(event):
    # Perform async operations
    await some_async_operation(event)
    print(f"Async: {event.action} - {event.container_name}")

listener.add_event_handler(sync_handler)
listener.add_async_event_handler(async_handler)
```

#### Registry Integration

```python
from src.containers import ContainerRegistry

registry = ContainerRegistry()
listener = ContainerEventListener(config, registry)

# The listener will automatically update the registry
# based on container events
```

### Container Models

#### Container

```python
@dataclass
class Container:
    id: str
    name: str
    image: str
    status: ContainerStatus
    created_at: Optional[datetime]
    ports: List[str]
    labels: Dict[str, str]
    raw_data: Dict[str, Any]
```

#### ContainerStats

```python
@dataclass
class ContainerStats:
    timestamp: datetime
    cpu_percent: float
    memory_usage_bytes: int
    memory_limit_bytes: int
    memory_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    block_read_bytes: int
    block_write_bytes: int
    raw_data: Dict[str, Any]
```

#### ContainerEvent

```python
@dataclass
class ContainerEvent:
    timestamp: datetime
    container_id: str
    container_name: str
    action: str
    image: str
    labels: Dict[str, str]
    raw_data: Dict[str, Any]
```

## Advanced Usage

### Custom Event Processing

```python
class MetricsCollector:
    def __init__(self):
        self.stats = {}
    
    async def handle_event(self, event):
        if event.action == "start":
            # Collect initial metrics
            await self.collect_startup_metrics(event.container_id)
        elif event.action in ["stop", "die"]:
            # Collect final metrics
            await self.collect_shutdown_metrics(event.container_id)

collector = MetricsCollector()
listener.add_async_event_handler(collector.handle_event)
```

### Container Health Monitoring

```python
class HealthMonitor:
    def __init__(self, client):
        self.client = client
        self.unhealthy_containers = set()
    
    async def monitor_health(self):
        containers = await self.client.list_containers()
        
        for container in containers:
            if container.status.value == "running":
                stats = await self.client.get_container_stats(container.id)
                
                # Check for high resource usage
                if stats.cpu_percent > 90 or stats.memory_percent > 95:
                    await self.handle_unhealthy_container(container)
    
    async def handle_unhealthy_container(self, container):
        print(f"⚠️  Unhealthy container detected: {container.name}")
        # Implement remediation logic
```

### Multi-Runtime Support

```python
class MultiRuntimeManager:
    def __init__(self):
        self.clients = {}
    
    async def add_runtime(self, name, config):
        client = PodmanClient(config)
        await client.connect()
        self.clients[name] = client
    
    async def list_all_containers(self):
        all_containers = []
        for name, client in self.clients.items():
            containers = await client.list_containers()
            for container in containers:
                container.runtime = name
                all_containers.append(container)
        return all_containers

# Usage
manager = MultiRuntimeManager()
await manager.add_runtime("podman", PodmanConfig(socket_path="/run/podman/podman.sock"))
await manager.add_runtime("docker", PodmanConfig(socket_path="/var/run/docker.sock"))

all_containers = await manager.list_all_containers()
```

## Error Handling

### PodmanAPIError

```python
from src.containers import PodmanAPIError

try:
    container = await client.get_container("nonexistent")
except PodmanAPIError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response Data: {e.response_data}")
```

### Connection Failures

```python
config = PodmanConfig(
    auto_detect=True,
    fallback_to_docker=True,
    use_cli_fallback=True
)

try:
    async with PodmanClient(config) as client:
        # Operations here
        pass
except PodmanAPIError as e:
    if "connection" in str(e).lower():
        print("Connection failed - check if Podman/Docker is running")
    else:
        print(f"API error: {e}")
```

## Testing

### Unit Tests

```bash
# Run all container tests
pytest tests/test_podman_client.py tests/test_event_listener.py -v

# Run with coverage
pytest tests/test_podman_client.py --cov=src.containers --cov-report=html
```

### Integration Tests

```bash
# Run integration tests (requires Podman/Docker)
pytest tests/test_podman_client.py::TestPodmanClientIntegration -v

# Run with specific runtime
CONTAINER_RUNTIME=podman pytest tests/test_podman_client.py -v
```

### Mock Testing

```python
from unittest.mock import AsyncMock, patch

@patch('src.containers.podman_client.aiohttp.ClientSession')
async def test_with_mock(mock_session_class):
    mock_session = AsyncMock()
    mock_session_class.return_value = mock_session
    
    # Configure mock responses
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"containers": []}
    mock_session.request.return_value.__aenter__.return_value = mock_response
    
    # Test your code
    client = PodmanClient()
    containers = await client.list_containers()
    assert containers == []
```

## Performance Considerations

### Connection Pooling

```python
# Reuse client connections
class ContainerManager:
    def __init__(self):
        self.client = None
    
    async def get_client(self):
        if not self.client:
            config = PodmanConfig(auto_detect=True)
            self.client = PodmanClient(config)
            await self.client.connect()
        return self.client
    
    async def close(self):
        if self.client:
            await self.client.close()
```

### Event Processing Optimization

```python
# Batch event processing
config = EventListenerConfig(
    event_batch_size=50,        # Process events in larger batches
    event_batch_timeout=2.0,    # Wait longer to accumulate events
    event_buffer_size=5000      # Larger buffer for high-volume environments
)
```

### Resource Monitoring

```python
# Monitor listener performance
stats = listener.get_stats()
print(f"Events/sec: {stats['events_processed'] / stats['uptime_seconds']:.2f}")
print(f"Buffer utilization: {stats['event_buffer_size'] / config.event_buffer_size * 100:.1f}%")
```

## Best Practices

1. **Use Context Managers**: Always use `async with` for automatic cleanup
2. **Handle Errors Gracefully**: Implement proper error handling for network issues
3. **Monitor Performance**: Track event processing rates and buffer usage
4. **Filter Events**: Use event filtering to reduce processing overhead
5. **Batch Operations**: Process events in batches for better performance
6. **Connection Reuse**: Reuse client connections when possible
7. **Graceful Shutdown**: Ensure proper cleanup on application shutdown

## Examples

See the `example.py` file for comprehensive examples including:

- Basic container operations
- Real-time event monitoring
- Container statistics streaming
- Health monitoring implementation
- Multi-runtime management

Run the examples:

```bash
python -m src.containers.example
```

This container management system provides a robust foundation for building container-aware applications with excellent support for both Podman and Docker environments.