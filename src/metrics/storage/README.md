# Metrics Storage and Retrieval System

This module provides a comprehensive system for storing, retrieving, and managing time series metrics data with configurable retention policies.

## Features

- **Time Series Storage**: Store and retrieve time series metrics data
- **Retention Policies**: Configure how long metrics data should be stored
- **Query Interface**: Advanced query capabilities for metrics data
- **Storage Statistics**: Get information about storage usage
- **Health Checks**: Monitor the health of the storage system
- **Export/Import**: Export metrics data to JSON or CSV files

## Usage

### Basic Usage

```python
import asyncio
from datetime import datetime, timedelta
from src.metrics.models import MetricValue
from src.metrics.storage import create_metrics_storage_system

async def main():
    # Create storage system
    storage_system = create_metrics_storage_system({
        "storage_type": "memory",  # Use in-memory storage
        "auto_cleanup": True,
        "cleanup_interval_hours": 1
    })
    
    # Initialize storage system
    await storage_system.initialize()
    
    try:
        # Store a metric
        metric = MetricValue(
            name="container_cpu_usage_percent",
            value=42.0,
            timestamp=datetime.now(),
            labels={"container_id": "container_123", "host": "host_1"},
            unit="percent"
        )
        await storage_system.store_metric(metric)
        
        # Query metrics
        metrics = await storage_system.query_metrics(
            metric_name="container_cpu_usage_percent",
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            labels={"container_id": "container_123"}
        )
        
        # Get latest metric value
        latest = await storage_system.query_latest(
            metric_name="container_cpu_usage_percent",
            labels={"container_id": "container_123"}
        )
        
        # Get storage statistics
        stats = await storage_system.get_storage_stats()
        
    finally:
        # Clean up
        await storage_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### Retention Policies

```python
# Add a retention rule
storage_system.add_retention_rule(
    metric_pattern="container_cpu_*",
    retention_days=7,
    labels={"host": "host_1"},
    priority=10
)

# Apply retention policy
await storage_system.apply_retention_policy()

# Get retention summary
summary = storage_system.get_retention_summary()
```

### Advanced Queries

```python
# Query with time range
data_points = await storage_system.query_range(
    metric_name="system_load_1m",
    start_time=datetime.now() - timedelta(hours=24),
    end_time=datetime.now(),
    step=timedelta(minutes=5),
    aggregation="avg"
)

# Export metrics to file
await storage_system.export_metrics(
    output_path="metrics_export.json",
    metric_name="container_cpu_usage_percent",
    start_time=datetime.now() - timedelta(days=7),
    format="json"
)
```

## Components

- **MetricsStorageSystem**: Main class that integrates all components
- **TimeSeriesStorage**: Base class for time series storage backends
- **RetentionManager**: Manages data retention policies
- **QueryEngine**: Provides advanced query capabilities
- **StorageFactory**: Creates storage backends based on configuration

## Storage Backends

- **InMemoryTimeSeriesStorage**: In-memory storage for testing and development
- **SQLiteTimeSeriesStorage**: SQLite-based storage for production use
- **FileTimeSeriesStorage**: File-based storage for simple deployments

## Configuration

```python
config = {
    # Storage configuration
    "storage_type": "sqlite",  # memory, sqlite, file
    "storage_config": {
        "db_path": "data/metrics.db"  # For SQLite
    },
    
    # Retention configuration
    "retention_enabled": True,
    "setup_default_retention": True,
    "auto_cleanup": True,
    "cleanup_interval_hours": 1
}

storage_system = create_metrics_storage_system(config)
```