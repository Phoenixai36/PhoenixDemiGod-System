"""
Tests for the time series storage system.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
import random
import string

from src.metrics.models import MetricValue
from src.metrics.storage import RetentionPolicy, InMemoryTimeSeriesStorage


@pytest.fixture
def retention_policy():
    """Create a retention policy for testing."""
    return RetentionPolicy(
        name="test_policy",
        retention_period=timedelta(hours=24),
        downsampling_interval=timedelta(minutes=5),
        max_points_per_series=1000
    )


@pytest.fixture
def storage(retention_policy):
    """Create an in-memory storage for testing."""
    return InMemoryTimeSeriesStorage(retention_policy)


@pytest.fixture
def sample_metrics():
    """Create sample metrics for testing."""
    now = datetime.now()
    metrics = []
    
    # Create metrics with different names and labels
    for i in range(3):
        metric_name = f"test_metric_{i}"
        
        for j in range(2):
            labels = {
                "service": f"service_{j}",
                "instance": f"instance_{j}"
            }
            
            # Create metrics with different timestamps
            for k in range(5):
                timestamp = now - timedelta(minutes=k * 5)
                value = random.uniform(0, 100)
                
                metrics.append(MetricValue(
                    name=metric_name,
                    value=value,
                    timestamp=timestamp,
                    labels=labels,
                    unit="count"
                ))
    
    return metrics


@pytest.mark.asyncio
async def test_store_and_query_metrics(storage, sample_metrics):
    """Test storing and querying metrics."""
    # Store metrics
    result = await storage.store_metrics(sample_metrics)
    assert result is True
    
    # Query all metrics for the first metric name
    metric_name = "test_metric_0"
    now = datetime.now()
    start_time = now - timedelta(hours=1)
    end_time = now
    
    results = await storage.query_metrics(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time
    )
    
    # Should have 10 metrics (5 timestamps * 2 label combinations)
    assert len(results) == 10
    assert all(r.name == metric_name for r in results)
    
    # Query with label filter
    results = await storage.query_metrics(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        labels={"service": "service_0"}
    )
    
    # Should have 5 metrics (5 timestamps * 1 label combination)
    assert len(results) == 5
    assert all(r.name == metric_name for r in results)
    assert all(r.labels["service"] == "service_0" for r in results)
    
    # Query with aggregation
    results = await storage.query_metrics(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        aggregation="avg"
    )
    
    # Should have 2 metrics (1 per label combination)
    assert len(results) == 2
    assert all(r.name == metric_name for r in results)
    
    # Query with limit
    results = await storage.query_metrics(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        limit=3
    )
    
    # Should have 3 metrics
    assert len(results) == 3
    assert all(r.name == metric_name for r in results)


@pytest.mark.asyncio
async def test_get_metric_names(storage, sample_metrics):
    """Test getting metric names."""
    # Store metrics
    await storage.store_metrics(sample_metrics)
    
    # Get metric names
    names = await storage.get_metric_names()
    
    # Should have 3 metric names
    assert len(names) == 3
    assert "test_metric_0" in names
    assert "test_metric_1" in names
    assert "test_metric_2" in names


@pytest.mark.asyncio
async def test_get_label_keys(storage, sample_metrics):
    """Test getting label keys."""
    # Store metrics
    await storage.store_metrics(sample_metrics)
    
    # Get label keys
    keys = await storage.get_label_keys()
    
    # Should have 2 label keys
    assert len(keys) == 2
    assert "service" in keys
    assert "instance" in keys
    
    # Get label keys for specific metric
    keys = await storage.get_label_keys("test_metric_0")
    
    # Should have 2 label keys
    assert len(keys) == 2
    assert "service" in keys
    assert "instance" in keys


@pytest.mark.asyncio
async def test_get_label_values(storage, sample_metrics):
    """Test getting label values."""
    # Store metrics
    await storage.store_metrics(sample_metrics)
    
    # Get label values
    values = await storage.get_label_values("service")
    
    # Should have 2 label values
    assert len(values) == 2
    assert "service_0" in values
    assert "service_1" in values
    
    # Get label values for specific metric
    values = await storage.get_label_values("service", "test_metric_0")
    
    # Should have 2 label values
    assert len(values) == 2
    assert "service_0" in values
    assert "service_1" in values


@pytest.mark.asyncio
async def test_apply_retention_policy(storage):
    """Test applying retention policy."""
    now = datetime.now()
    
    # Create metrics with different timestamps
    metrics = []
    
    # Recent metrics (within retention period)
    for i in range(5):
        metrics.append(MetricValue(
            name="test_metric",
            value=i,
            timestamp=now - timedelta(hours=i),
            labels={"service": "test"}
        ))
    
    # Old metrics (outside retention period)
    for i in range(5):
        metrics.append(MetricValue(
            name="test_metric",
            value=i,
            timestamp=now - timedelta(hours=48 + i),  # 48+ hours old
            labels={"service": "test"}
        ))
    
    # Store metrics
    await storage.store_metrics(metrics)
    
    # Apply retention policy
    removed = await storage.apply_retention_policy()
    
    # Should have removed 5 metrics
    assert removed == 5
    
    # Query all metrics
    results = await storage.query_metrics(
        metric_name="test_metric",
        start_time=now - timedelta(days=7),
        end_time=now
    )
    
    # Should have 5 metrics (the recent ones)
    assert len(results) == 5
    assert all((now - r.timestamp).total_seconds() < 24 * 3600 for r in results)


@pytest.mark.asyncio
async def test_get_storage_stats(storage, sample_metrics):
    """Test getting storage statistics."""
    # Store metrics
    await storage.store_metrics(sample_metrics)
    
    # Get storage stats
    stats = await storage.get_storage_stats()
    
    # Check stats
    assert stats["metric_count"] == 3
    assert stats["series_count"] == 6  # 3 metrics * 2 label combinations
    assert stats["point_count"] == 30  # 3 metrics * 2 label combinations * 5 timestamps
    assert "memory_bytes" in stats
    assert "retention_policy" in stats
    assert stats["retention_policy"]["name"] == "test_policy"