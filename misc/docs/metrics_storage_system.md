# Metrics Storage and Retrieval System

## Overview

The metrics storage and retrieval system provides a flexible and efficient way to store, manage, and query time series metrics data. It is designed to handle container metrics with high throughput and efficient querying capabilities.

## Components

### RetentionPolicy

The `RetentionPolicy` class defines how long metrics data should be stored and provides mechanisms for downsampling data to manage storage growth.

Key features:
- Configurable retention period
- Optional downsampling interval
- Maximum points per series limit
- Serialization to/from dictionary for persistence

### TimeSeriesStorage

The `TimeSeriesStorage` abstract base class defines the interface for metrics storage implementations. It provides methods for storing, querying, and managing metrics data.

Key methods:
- `store_metrics`: Store multiple metrics
- `query_metrics`: Query metrics by name, time range, and optional filters
- `get_metric_names`: Get all available metric names
- `get_label_keys`: Get all available label keys
- `get_label_values`: Get all available values for a label key
- `apply_retention_policy`: Apply retention policy to stored metrics
- `get_storage_stats`: Get statistics about the storage

### InMemoryTimeSeriesStorage

The `InMemoryTimeSeriesStorage` class implements the `TimeSeriesStorage` interface using in-memory data structures. It provides efficient storage and querying of metrics data for development and testing purposes.

Key features:
- Efficient label indexing for fast queries
- Automatic retention policy application
- Support for aggregation functions (avg, sum, min, max, last)
- Memory usage tracking

### QueryEngine

The `QueryEngine` class provides a high-level interface for querying metrics data with additional features beyond the basic storage interface.

Key features:
- Flexible time range specification (start/end time or duration)
- Query latest metrics
- Query metrics at regular time intervals
- Simplified access to storage metadata

### API

The metrics API provides RESTful endpoints for accessing metrics data from the storage system.

Key endpoints:
- `GET /metrics/`: Get all available metric names
- `GET /metrics/{metric_name}`: Query metrics by name, time range, and optional filters
- `GET /metrics/{metric_name}/latest`: Get the latest value for a metric
- `GET /metrics/{metric_name}/range`: Query metrics with regular time intervals
- `GET /metrics/labels/keys`: Get all available label keys
- `GET /metrics/labels/values/{label_key}`: Get all available values for a label key
- `GET /metrics/storage/stats`: Get statistics about the metrics storage

## Usage

### Basic Usage

```python
from datetime import datetime, timedelta
from src.metrics.models import MetricValue
from src.metrics.storage import RetentionPolicy, InMemoryTimeSeriesStorage, QueryEngine

# Create retention policy
policy = RetentionPolicy(
    name="demo_policy",
    retention_period=timedelta(hours=24),
    downsampling_interval=timedelta(minutes=5),
    max_points_per_series=1000
)

# Create storage
storage = InMemoryTimeSeriesStorage(policy)

# Create query engine
query_engine = QueryEngine(storage)

# Store metrics
metrics = [
    MetricValue(
        name="container_cpu_usage_percent",
        value=42.5,
        timestamp=datetime.now(),
        labels={"container_name": "web", "host": "server1"},
        unit="percent"
    )
]
await storage.store_metrics(metrics)

# Query metrics
results = await query_engine.query_metrics(
    metric_name="container_cpu_usage_percent",
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now(),
    labels={"container_name": "web"}
)
```

### API Integration

```python
from fastapi import FastAPI
from src.metrics.api import create_metrics_router

app = FastAPI()

# Create metrics router
metrics_router = create_metrics_router(query_engine)

# Add router to app
app.include_router(metrics_router)
```

## Future Enhancements

1. **Persistent Storage**: Implement a file-based or database-backed storage implementation for production use.
2. **Distributed Storage**: Support for distributed storage across multiple nodes.
3. **Advanced Querying**: Support for more complex query patterns like rate calculations and forecasting.
4. **Caching**: Add caching layer for frequently accessed metrics.
5. **Compression**: Implement data compression for efficient storage.
6. **Batch Processing**: Optimize for batch processing of metrics.
7. **Streaming**: Support for streaming metrics updates in real-time.