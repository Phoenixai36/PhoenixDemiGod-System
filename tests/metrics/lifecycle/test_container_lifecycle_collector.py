"""
Tests for the container lifecycle metrics collector.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.metrics.models import CollectorConfig, MetricValue
from src.metrics.lifecycle.container_lifecycle_collector import ContainerLifecycleMetricsCollector
from src.metrics.lifecycle.event_collector import ContainerEvent, ContainerEventType


@pytest.fixture
def mock_lifecycle_manager():
    """Create a mock lifecycle manager."""
    mock = MagicMock()
    
    # Mock collect_container_metrics
    async def mock_collect_metrics(container_id):
        return [
            MetricValue(
                name="container_uptime_seconds",
                value=3600.0,
                timestamp=datetime.now(),
                labels={
                    "container_id": container_id,
                    "container_name": f"container_{container_id}",
                    "status": "running"
                }
            ),
            MetricValue(
                name="container_restart_count",
                value=2,
                timestamp=datetime.now(),
                labels={
                    "container_id": container_id,
                    "container_name": f"container_{container_id}"
                }
            )
        ]
    
    mock.collect_container_metrics.side_effect = mock_collect_metrics
    
    # Mock initialize and cleanup
    async def mock_initialize():
        return True
    
    async def mock_cleanup():
        pass
    
    mock.initialize.side_effect = mock_initialize
    mock.cleanup.side_effect = mock_cleanup
    
    return mock


@pytest.fixture
def collector(mock_lifecycle_manager):
    """Create a collector with mocked lifecycle manager."""
    config = CollectorConfig(
        name="container_lifecycle",
        collection_interval=30,
        parameters={"max_history_size": 100}
    )
    
    collector = ContainerLifecycleMetricsCollector(config)
    collector.lifecycle_manager = mock_lifecycle_manager
    
    return collector


@pytest.mark.asyncio
async def test_initialize(collector, mock_lifecycle_manager):
    """Test collector initialization."""
    result = await collector.initialize()
    
    assert result is True
    mock_lifecycle_manager.initialize.assert_called_once()
    assert len(collector.known_containers) == 0


@pytest.mark.asyncio
async def test_cleanup(collector, mock_lifecycle_manager):
    """Test collector cleanup."""
    await collector.cleanup()
    
    mock_lifecycle_manager.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_collect_container_metrics(collector, mock_lifecycle_manager):
    """Test collecting metrics for a specific container."""
    container_id = "test_container_123"
    
    metrics = await collector.collect_container_metrics(container_id)
    
    assert len(metrics) == 2
    assert container_id in collector.known_containers
    mock_lifecycle_manager.collect_container_metrics.assert_called_once_with(container_id)
    
    # Check metric values
    uptime_metric = next(m for m in metrics if m.name == "container_uptime_seconds")
    restart_metric = next(m for m in metrics if m.name == "container_restart_count")
    
    assert uptime_metric.value == 3600.0
    assert restart_metric.value == 2
    assert uptime_metric.labels["container_id"] == container_id
    assert restart_metric.labels["container_id"] == container_id


@pytest.mark.asyncio
async def test_handle_lifecycle_event(collector):
    """Test handling lifecycle events."""
    # Test with valid event
    event_data = {
        "type": "lifecycle_event",
        "container_id": "new_container_456",
        "event_type": "start"
    }
    
    collector._handle_lifecycle_event("lifecycle_event", event_data)
    assert "new_container_456" in collector.known_containers
    
    # Test with invalid event type
    collector._handle_lifecycle_event("unknown_event", event_data)
    
    # Test with missing container_id
    collector._handle_lifecycle_event("lifecycle_event", {"type": "lifecycle_event"})
    assert len(collector.known_containers) == 1  # No change


@pytest.mark.asyncio
async def test_get_metric_types(collector):
    """Test getting metric types."""
    from src.metrics.models import MetricType
    
    metric_types = collector.get_metric_types()
    assert MetricType.CONTAINER_LIFECYCLE in metric_types


@pytest.mark.asyncio
async def test_additional_methods(collector, mock_lifecycle_manager):
    """Test additional accessor methods."""
    container_id = "test_container_123"
    
    # Setup mock return values
    mock_lifecycle_manager.get_container_restart_pattern.return_value = {"restart_count": 2}
    mock_lifecycle_manager.get_container_uptime_statistics.return_value = {"uptime_percentage": 99.5}
    mock_lifecycle_manager.get_restart_loops.return_value = []
    mock_lifecycle_manager.get_running_containers.return_value = [{"container_id": container_id}]
    mock_lifecycle_manager.get_recent_events.return_value = [{"event_type": "start"}]
    mock_lifecycle_manager.get_lifecycle_summary.return_value = {"events": {}, "restarts": {}, "uptime": {}}
    mock_lifecycle_manager.analyze_container_health.return_value = {"health_score": 100}
    
    # Test methods
    assert collector.get_container_restart_pattern(container_id) == {"restart_count": 2}
    assert collector.get_container_uptime_statistics(container_id) == {"uptime_percentage": 99.5}
    assert collector.get_restart_loops() == []
    assert collector.get_running_containers() == [{"container_id": container_id}]
    assert collector.get_recent_events(container_id) == [{"event_type": "start"}]
    assert "events" in collector.get_lifecycle_summary()
    assert collector.analyze_container_health(container_id) == {"health_score": 100}
    
    # Verify calls
    mock_lifecycle_manager.get_container_restart_pattern.assert_called_once_with(container_id)
    mock_lifecycle_manager.get_container_uptime_statistics.assert_called_once_with(container_id)
    mock_lifecycle_manager.get_restart_loops.assert_called_once()
    mock_lifecycle_manager.get_running_containers.assert_called_once()
    mock_lifecycle_manager.get_recent_events.assert_called_once_with(container_id, 100)
    mock_lifecycle_manager.get_lifecycle_summary.assert_called_once()
    mock_lifecycle_manager.analyze_container_health.assert_called_once_with(container_id)


@pytest.mark.asyncio
async def test_error_handling(collector, mock_lifecycle_manager):
    """Test error handling in the collector."""
    container_id = "test_container_123"
    
    # Make the lifecycle manager raise an exception
    mock_lifecycle_manager.collect_container_metrics.side_effect = Exception("Test error")
    
    # Should return empty list and not propagate the exception
    metrics = await collector.collect_container_metrics(container_id)
    assert metrics == []