"""
Tests for the metrics query engine.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
import random

from src.metrics.models import MetricValue
from src.metrics.storage import RetentionPolicy, InMemoryTimeSeriesStorage, QueryEngine


@pytest.fixture
def storage():
    """Create an in-memory storage for testing."""
    policy = RetentionPolicy(
        name="test_policy",
        retention_period=timedelta(hours=24),
        downsampling_interval=timedelta(minutes=5),
        max_points_per_series=1000
    )
    return InMemoryTimeSeriesStorage(policy)


@pytest.fixture
def query_engine(storage):
    """Create a query engine for testing."""
    return QueryEngine(storage)


@pytest.fixture
async def sample_data(storage):
    """Create and store sample data for testing."""
    now = datetime.now()
    metrics = []
    
    # Create metrics with different timestamps
    for i in range(60):  # 1 hour of data at 1-minute intervals
        timestamp = now - timedelta(minutes=i)
        
        # CPU metrics
        metrics.append(MetricValue(
            name="cpu_usage_percent",
            value=random.uniform(0, 100),
            timestamp=timestamp,
            labels={"container": "web", "host": "server1"},
            unit="percent"
        ))
        
        metrics.append(MetricValue(
            name="cpu_usage_percent",
            value=random.uniform(0, 100),
            timestamp=timestamp,
            labels={"container": "db", "host": "server1"},
            unit="percent"
        ))
        
        # Memory metrics
        metrics.append(MetricValue(
            name="memory_usage_bytes",
            value=random.randint(1000000, 10000000),
            timestamp=timestamp,
            labels={"container": "web", "host": "server1"},
            unit="bytes"
        ))
        
        metrics.append(MetricValue(
            name="memory_usage_bytes",
            value=random.randint(1000000, 10000000),
            timestamp=timestamp,
            labels={"container": "db", "host": "server1"},
            unit="bytes"
        ))
    
    # Store metrics
    await storage.store_metrics(metrics)
    
    return now


@pytest.mark.asyncio
async def test_query_metrics(query_engine, sample_data):
    """Test querying metrics with different parameters."""
    now = sample_data
    
    # Query with explicit time range
    start_time = now - timedelta(minutes=30)
    end_time = now
    
    results = await query_engine.query_metrics(
        metric_name="cpu_usage_percent",
        start_time=start_time,
        end_time=end_time
    )
    
    # Should have 62 metrics (31 timestamps * 2 containers)
    assert len(results) == 62
    assert all(r.name == "cpu_usage_percent" for r in results)
    assert all(start_time <= r.timestamp <= end_time for r in results)
    
    # Query with duration
    results = await query_engine.query_metrics(
        metric_name="cpu_usage_percent",
        end_time=now,
        duration=timedelta(minutes=15)
    )
    
    # Should have 32 metrics (16 timestamps * 2 containers)
    assert len(results) == 32
    assert all(r.name == "cpu_usage_percent" for r in results)
    assert all((now - r.timestamp).total_seconds() <= 15 * 60 for r in results)
    
    # Query with labels
    results = await query_engine.query_metrics(
        metric_name="cpu_usage_percent",
        start_time=start_time,
        end_time=end_time,
        labels={"container": "web"}
    )
    
    # Should have 31 metrics (31 timestamps * 1 container)
    assert len(results) == 31
    assert all(r.name == "cpu_usage_percent" for r in results)
    assert all(r.labels["container"] == "web" for r in results)
    
    # Query with aggregation
    results = await query_engine.query_metrics(
        metric_name="cpu_usage_percent",
        start_time=start_time,
        end_time=end_time,
        aggregation="avg"
    )
    
    # Should have 2 metrics (1 per container)
    assert len(results) == 2
    assert all(r.name == "cpu_usage_percent" for r in results)
    
    # Query with limit
    results = await query_engine.query_metrics(
        metric_name="cpu_usage_percent",
        start_time=start_time,
        end_time=end_time,
        limit=5
    )
    
    # Should have 5 metrics
    assert len(results) == 5
    assert all(r.name == "cpu_usage_percent" for r in results)


@pytest.mark.asyncio
async def test_query_latest(query_engine, sample_data):
    """Test querying latest metrics."""
    # Query latest CPU usage for web container
    result = await query_engine.query_latest(
        metric_name="cpu_usage_percent",
        labels={"container": "web"}
    )
    
    # Should have a result
    assert result is not None
    assert result.name == "cpu_usage_percent"
    assert result.labels["container"] == "web"
    
    # Query latest for non-existent metric
    result = await query_engine.query_latest(
        metric_name="non_existent_metric"
    )
    
    # Should not have a result
    assert result is None


@pytest.mark.asyncio
async def test_query_range(query_engine, sample_data):
    """Test querying metrics with regular time intervals."""
    now = sample_data
    start_time = now - timedelta(minutes=30)
    end_time = now
    step = timedelta(minutes=5)
    
    # Query range for CPU usage
    results = await query_engine.query_range(
        metric_name="cpu_usage_percent",
        start_time=start_time,
        end_time=end_time,
        step=step,
        labels={"container": "web"},
        aggregation="avg"
    )
    
    # Should have 7 points (0, 5, 10, 15, 20, 25, 30 minutes)
    assert len(results) == 7
    
    # Check timestamps are at 5-minute intervals
    for i in range(len(results) - 1):
        time_diff = (results[i][0] - results[i+1][0]).total_seconds()
        assert abs(time_diff - 300) < 1  # 5 minutes = 300 seconds
    
    # All values should be numeric
    assert all(isinstance(r[1], (int, float)) for r in results if r[1] is not None)


@pytest.mark.asyncio
async def test_get_metric_names(query_engine, sample_data):
    """Test getting metric names."""
    names = await query_engine.get_metric_names()
    
    # Should have 2 metric names
    assert len(names) == 2
    assert "cpu_usage_percent" in names
    assert "memory_usage_bytes" in names


@pytest.mark.asyncio
async def test_get_label_keys(query_engine, sample_data):
    """Test getting label keys."""
    keys = await query_engine.get_label_keys()
    
    # Should have 2 label keys
    assert len(keys) == 2
    assert "container" in keys
    assert "host" in keys
    
    # Get label keys for specific metric
    keys = await query_engine.get_label_keys("cpu_usage_percent")
    
    # Should have 2 label keys
    assert len(keys) == 2
    assert "container" in keys
    assert "host" in keys


@pytest.mark.asyncio
async def test_get_label_values(query_engine, sample_data):
    """Test getting label values."""
    values = await query_engine.get_label_values("container")
    
    # Should have 2 label values
    assert len(values) == 2
    assert "web" in values
    assert "db" in values
    
    # Get label values for specific metric
    values = await query_engine.get_label_values("container", "cpu_usage_percent")
    
    # Should have 2 label values
    assert len(values) == 2
    assert "web" in values
    assert "db" in values


@pytest.mark.asyncio
async def test_get_storage_stats(query_engine, sample_data):
    """Test getting storage statistics."""
    stats = await query_engine.get_storage_stats()
    
    # Check stats
    assert "metric_count" in stats
    assert "series_count" in stats
    assert "point_count" in stats
    assert "memory_bytes" in stats
    assert "retention_policy" in stats