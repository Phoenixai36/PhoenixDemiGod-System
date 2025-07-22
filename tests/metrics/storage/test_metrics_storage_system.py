"""
Tests for the metrics storage and retrieval system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.metrics.models import MetricValue
from src.metrics.storage.metrics_storage_system import MetricsStorageSystem, create_metrics_storage_system


@pytest.fixture
def mock_storage():
    """Create a mock storage backend."""
    mock = MagicMock()
    
    # Mock store_metrics
    async def mock_store_metrics(metrics):
        return True
    
    mock.store_metrics.side_effect = mock_store_metrics
    
    # Mock query_metrics
    async def mock_query_metrics(metric_name=None, start_time=None, end_time=None, 
                               labels=None, aggregation=None, limit=None):
        return [
            MetricValue(
                name=metric_name or "test_metric",
                value=42.0,
                timestamp=datetime.now(),
                labels=labels or {"test": "true"}
            )
        ]
    
    mock.query_metrics.side_effect = mock_query_metrics
    
    # Mock get_metric_names
    async def mock_get_metric_names():
        return ["test_metric", "system_cpu", "container_memory"]
    
    mock.get_metric_names.side_effect = mock_get_metric_names
    
    # Mock get_label_keys
    async def mock_get_label_keys(metric_name=None):
        return ["test", "container_id", "host"]
    
    mock.get_label_keys.side_effect = mock_get_label_keys
    
    # Mock get_label_values
    async def mock_get_label_values(label_key, metric_name=None):
        return ["true", "container_123", "host_1"]
    
    mock.get_label_values.side_effect = mock_get_label_values
    
    # Mock get_storage_stats
    async def mock_get_storage_stats():
        return {
            "total_metrics": 100,
            "database_size_mb": 1.5
        }
    
    mock.get_storage_stats.side_effect = mock_get_storage_stats
    
    return mock


@pytest.fixture
def storage_system(mock_storage):
    """Create a storage system with mocked components."""
    system = MetricsStorageSystem({"storage_type": "memory"})
    system.storage = mock_storage
    system.query_engine.storage = mock_storage
    
    return system


@pytest.mark.asyncio
async def test_store_metrics(storage_system):
    """Test storing metrics."""
    metrics = [
        MetricValue(
            name="test_metric",
            value=42.0,
            timestamp=datetime.now(),
            labels={"test": "true"}
        ),
        MetricValue(
            name="another_metric",
            value=123.0,
            timestamp=datetime.now(),
            labels={"test": "false"}
        )
    ]
    
    result = await storage_system.store_metrics(metrics)
    assert result is True
    storage_system.storage.store_metrics.assert_called_once_with(metrics)


@pytest.mark.asyncio
async def test_query_metrics(storage_system):
    """Test querying metrics."""
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    metrics = await storage_system.query_metrics(
        metric_name="test_metric",
        start_time=start_time,
        end_time=end_time,
        labels={"test": "true"},
        limit=10
    )
    
    assert len(metrics) == 1
    assert metrics[0].name == "test_metric"
    assert metrics[0].value == 42.0
    
    storage_system.storage.query_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_query_latest(storage_system):
    """Test querying latest metric value."""
    metric = await storage_system.query_latest(
        metric_name="test_metric",
        labels={"test": "true"}
    )
    
    assert metric is not None
    assert metric.name == "test_metric"
    assert metric.value == 42.0


@pytest.mark.asyncio
async def test_get_metric_names(storage_system):
    """Test getting metric names."""
    names = await storage_system.get_metric_names()
    
    assert len(names) == 3
    assert "test_metric" in names
    assert "system_cpu" in names
    assert "container_memory" in names


@pytest.mark.asyncio
async def test_get_label_keys(storage_system):
    """Test getting label keys."""
    keys = await storage_system.get_label_keys()
    
    assert len(keys) == 3
    assert "test" in keys
    assert "container_id" in keys
    assert "host" in keys


@pytest.mark.asyncio
async def test_get_label_values(storage_system):
    """Test getting label values."""
    values = await storage_system.get_label_values("test")
    
    assert len(values) == 3
    assert "true" in values
    assert "container_123" in values
    assert "host_1" in values


@pytest.mark.asyncio
async def test_get_storage_stats(storage_system):
    """Test getting storage statistics."""
    stats = await storage_system.get_storage_stats()
    
    assert stats["total_metrics"] == 100
    assert stats["database_size_mb"] == 1.5


@pytest.mark.asyncio
async def test_health_check(storage_system):
    """Test health check."""
    health = await storage_system.health_check()
    
    assert health["status"] == "healthy"
    assert "checks" in health
    assert health["checks"]["write"] == "pass"
    assert health["checks"]["read"] == "pass"


@pytest.mark.asyncio
async def test_create_metrics_storage_system():
    """Test creating a metrics storage system."""
    with patch("src.metrics.storage.metrics_storage_system.StorageFactory") as mock_factory:
        mock_factory.return_value.create_storage.return_value = MagicMock()
        
        system = create_metrics_storage_system({"storage_type": "memory"})
        
        assert system is not None
        assert isinstance(system, MetricsStorageSystem)
        mock_factory.return_value.create_storage.assert_called_once()