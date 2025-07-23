# Phoenix Hydra Agent Hooks System

Agent Hooks provide event-driven automation capabilities for the Phoenix Hydra system, enabling automatic responses to file changes, container events, API status changes, and other system events. This system is built on a robust event bus architecture with support for filtering, debouncing, and parallel execution.

## Core Architecture

### Event Bus System
The heart of the Agent Hooks system is an asynchronous event bus (`src/hooks/core/events.py`) that handles:
- Event distribution and filtering
- Subscription management with custom filters
- Event persistence and replay capabilities
- Backpressure handling and queue management
- Priority-based event processing

### Event Sources
Multiple event sources monitor different aspects of the system:

#### File System Watcher (`src/hooks/event_sources/file_watcher.py`)
- Monitors file changes with debouncing to avoid duplicate events
- Supports pattern-based filtering (include/exclude patterns)
- Content hash verification to detect actual changes
- Categorizes files by type (Python, Terraform, Windmill, configuration)
- Default patterns include: `*.py`, `*.tf`, `*.yaml`, `*.js`, `*.ts`, `*.sql`, `*.sh`, `*.ps1`

#### Container Event Listener (`src/containers/event_listener.py`)
- Monitors Podman/Docker container lifecycle events
- Tracks container health, resource usage, and logs
- Supports filtering by container names and labels
- Integrates with Phoenix Hydra container stack

## Hook Configuration

### File Watcher Configuration
```python
file_watcher:
  watch_paths:
    - "src/"
    - "infra/terraform/"
    - "infra/windmill-scripts/"
    - "configs/"
    - "scripts/"
  include_patterns:
    - "*.py"      # Python files
    - "*.tf"      # Terraform files
    - "*.yaml"    # Configuration files
    - "*.js"      # Windmill scripts
  exclude_patterns:
    - "*.pyc"
    - "__pycache__/*"
    - ".git/*"
    - "node_modules/*"
  debounce_delay: 0.5
  recursive: true
```

### Container Monitor Configuration
```python
container_monitor:
  runtime: "podman"
  container_labels:
    project: "phoenix-hydra"
    component: "agent"
  health_check_interval: 30.0
  cpu_threshold_percent: 80.0
  memory_threshold_percent: 90.0
```

## Common Hook Patterns

### 1. Code Quality Hooks
Automatically run tests and formatting when Python files change:

```python
async def on_python_file_changed(event):
    file_path = event.data['file_path']
    if event.data['change_type'] == 'modified':
        # Run tests
        await run_command(f"pytest tests/ -v")
        # Format code
        await run_command(f"black {file_path}")
        # Check with ruff
        await run_command(f"ruff check {file_path}")
```

### 2. Infrastructure Automation
Deploy changes when Terraform files are modified:

```python
async def on_terraform_file_changed(event):
    if event.data['change_type'] in ['created', 'modified']:
        terraform_dir = Path(event.data['file_path']).parent
        # Plan changes
        await run_command(f"terraform plan", cwd=terraform_dir)
        # Auto-apply in development
        if is_development_environment():
            await run_command(f"terraform apply -auto-approve", cwd=terraform_dir)
```

### 3. Workflow Synchronization
Update n8n workflows when Windmill scripts change:

```python
async def on_windmill_script_changed(event):
    script_path = event.data['file_path']
    if 'windmill-scripts' in script_path:
        # Sync to n8n
        await sync_windmill_to_n8n(script_path)
        # Update workflow documentation
        await generate_workflow_docs(script_path)
```

### 4. Revenue Tracking Automation
Monitor monetization metrics when configuration changes:

```python
async def on_monetization_config_changed(event):
    if 'phoenix-monetization.json' in event.data['file_path']:
        # Update revenue tracking
        await run_command("node scripts/revenue-tracking.js")
        # Deploy affiliate badges
        await run_command("node scripts/deploy-badges.js")
        # Generate grant applications
        await run_command("python scripts/neotec-generator.py")
```

### 5. Container Health Monitoring
Respond to container events and health issues:

```python
async def on_container_unhealthy(event):
    container_name = event.data['container_name']
    if container_name.startswith('phoenix-hydra'):
        # Restart unhealthy container
        await run_command(f"podman restart {container_name}")
        # Send notification
        await send_notification(f"Container {container_name} restarted due to health check failure")
```

## VS Code Integration

The system integrates with VS Code tasks for manual hook execution:

### Available Tasks
- **Deploy Phoenix Badges**: Updates affiliate program badges in README
- **Generate NEOTEC Application**: Creates grant application documents
- **Update Revenue Metrics**: Tracks revenue across all monetization channels
- **Start Phoenix Hydra**: Launches all services with Podman Compose
- **Phoenix Health Check**: Verifies all services are responding

### Task Configuration
Tasks are defined in `.vscode/tasks.json` and can be triggered via:
- Command Palette: `Ctrl+Shift+P` → "Tasks: Run Task"
- Keyboard shortcuts (can be configured)
- Agent hooks (automated execution)

## Event Types and Data Structure

### File Change Events
```json
{
  "event_type": "code.file.modified",
  "source": "file_watcher",
  "data": {
    "file_path": "src/core/router.py",
    "change_type": "modified",
    "file_hash": "sha256:abc123...",
    "metadata": {
      "category": "python",
      "file_extension": ".py",
      "directory": "src/core"
    }
  }
}
```

### Container Events
```json
{
  "event_type": "container.health.unhealthy",
  "source": "container_monitor",
  "data": {
    "container_name": "phoenix-hydra_phoenix-core_1",
    "container_id": "abc123...",
    "status": "unhealthy",
    "cpu_percent": 85.2,
    "memory_percent": 92.1
  }
}
```

## Hook Development Guidelines

### 1. Event Filtering
Use event filters to target specific events:

```python
# Filter for Python files only
python_filter = EventFilter(
    event_types=["code.file.modified", "code.file.created"],
    custom_filter=lambda e: e.data.get('metadata', {}).get('category') == 'python'
)

event_bus.subscribe(on_python_file_changed, python_filter)
```

### 2. Error Handling
Always include proper error handling in hooks:

```python
async def robust_hook(event):
    try:
        # Hook logic here
        await process_event(event)
    except Exception as e:
        logger.error(f"Hook failed for event {event.event_id}: {e}")
        # Optional: Send notification about failure
        await send_error_notification(event, e)
```

### 3. Resource Management
Be mindful of resource usage in hooks:

```python
# Use semaphores to limit concurrent executions
semaphore = asyncio.Semaphore(5)

async def resource_limited_hook(event):
    async with semaphore:
        # Resource-intensive operation
        await heavy_processing(event)
```

### 4. Testing Hooks
Create unit tests for hook functions:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_python_file_hook():
    event = create_test_event("code.file.modified", {"file_path": "test.py"})
    
    with patch('subprocess.run') as mock_run:
        await on_python_file_changed(event)
        mock_run.assert_called_with(["pytest", "tests/", "-v"])
```

## Best Practices

### 1. Idempotent Operations
Ensure hooks can be run multiple times safely:

```python
async def idempotent_deployment_hook(event):
    # Check current state before making changes
    if not needs_deployment():
        return
    
    await deploy_changes()
```

### 2. Graceful Degradation
Handle missing dependencies gracefully:

```python
async def optional_integration_hook(event):
    try:
        await external_service_call()
    except ServiceUnavailableError:
        logger.warning("External service unavailable, skipping hook")
        # Continue with local operations
        await local_fallback()
```

### 3. Configuration-Driven Behavior
Make hooks configurable:

```python
async def configurable_hook(event):
    config = get_hook_config('deployment')
    
    if config.get('auto_deploy', False):
        await deploy_automatically()
    else:
        await create_deployment_notification()
```

### 4. Monitoring and Observability
Include metrics and logging:

```python
async def monitored_hook(event):
    start_time = time.time()
    
    try:
        await hook_logic(event)
        metrics.increment('hooks.success', tags={'hook': 'deployment'})
    except Exception as e:
        metrics.increment('hooks.failure', tags={'hook': 'deployment'})
        raise
    finally:
        duration = time.time() - start_time
        metrics.histogram('hooks.duration', duration, tags={'hook': 'deployment'})
```

## Phoenix Hydra Specific Hooks

### Revenue Optimization Hooks
- Monitor affiliate program performance
- Auto-generate grant applications when deadlines approach
- Update marketplace listings when features are added
- Track revenue metrics and send alerts for targets

### Infrastructure Automation Hooks
- Auto-scale containers based on load
- Deploy infrastructure changes in staging environments
- Update monitoring configurations when services change
- Backup critical data when schemas change

### Development Workflow Hooks
- Run comprehensive tests on code changes
- Update documentation when APIs change
- Sync configurations between environments
- Generate deployment packages when releases are tagged

The Agent Hooks system provides a powerful foundation for automating the Phoenix Hydra development and deployment workflow, enabling the team to focus on core AI development while maintaining high operational standards.