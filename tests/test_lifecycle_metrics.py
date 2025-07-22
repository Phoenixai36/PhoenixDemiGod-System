"""
Unit tests for container lifecycle metrics.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.metrics.lifecycle import (
    ContainerEventCollector,
    RestartTracker,
    UptimeTracker,
    LifecycleManager
)
from src.metrics.lifecycle.event_collector import ContainerEvent, ContainerEventType
from src.metrics.models import CollectorConfig


class TestContainerEventCollector:
    """Test cases for ContainerEventCollector."""
    
    @pytest.fixture
    def event_collector(self):
        """Create event collector for testing."""
        config = CollectorConfig(name="test_event_collector")
        return ContainerEventCollector(config)
    
    @pytest.mark.asyncio
    async def test_initialize_docker(self, event_collector):
        """Test Docker initialization."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client
            
            success = await event_collector.initialize()
            
            assert success is True
            assert event_collector.runtime_type == "docker"
    
    def test_parse_docker_event(self, event_collector):
        """Test parsing Docker events."""
        docker_event = {
            'Action': 'start',
            'Actor': {
                'ID': 'container123',
                'Attributes': {
                    'name': 'test-container',
                    'image': 'nginx:latest'
                }
            },
            'time': 1640995200
        }
        
        container_event = event_collector._parse_docker_event(docker_event)
        
        assert container_event is not None
        assert container_event.container_id == 'container123'
        assert container_event.container_name == 'test-container'
        assert container_event.image == 'nginx:latest'
        assert container_event.event_type == ContainerEventType.START
    
    def test_parse_podman_event(self, event_collector):
        """Test parsing Podman events."""
        podman_event = {
            'Action': 'start',
            'ID': 'container123',
            'Attributes': {
                'name': 'test-container',
                'image': 'nginx:latest'
            },
            'Time': '2022-01-01T12:00:00Z'
        }
        
        container_event = event_collector._parse_podman_event(podman_event)
        
        assert container_event is not None
        assert container_event.container_id == 'container123'
        assert container_event.container_name == 'test-container'
        assert container_event.image == 'nginx:latest'
        assert container_event.event_type == ContainerEventType.START
    
    @pytest.mark.asyncio
    async def test_event_callback(self, event_collector):
        """Test event callbacks."""
        callback_called = False
        received_event = None
        
        def test_callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event
        
        event_collector.add_event_callback(test_callback)
        
        # Create test event
        test_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=datetime.now()
        )
        
        await event_collector._handle_event(test_event)
        
        assert callback_called is True
        assert received_event == test_event
    
    def test_event_history_limit(self, event_collector):
        """Test event history size limit."""
        event_collector.max_history_size = 3
        
        # Add more events than the limit
        for i in range(5):
            event = ContainerEvent(
                container_id=f"container{i}",
                container_name=f"test-{i}",
                image="nginx:latest",
                event_type=ContainerEventType.START,
                timestamp=datetime.now()
            )
            asyncio.run(event_collector._handle_event(event))
        
        # Should only keep the last 3 events
        assert len(event_collector.event_history) == 3
        assert event_collector.event_history[0].container_id == "container2"
        assert event_collector.event_history[-1].container_id == "container4"


class TestRestartTracker:
    """Test cases for RestartTracker."""
    
    @pytest.fixture
    def restart_tracker(self):
        """Create restart tracker for testing."""
        return RestartTracker(analysis_window=timedelta(hours=1))
    
    def test_single_restart_no_pattern(self, restart_tracker):
        """Test single restart doesn't create pattern."""
        event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=datetime.now()
        )
        
        restart_tracker.add_event(event)
        
        # Single event shouldn't create a pattern
        pattern = restart_tracker.get_restart_pattern("test123")
        assert pattern is None
    
    def test_restart_pattern_creation(self, restart_tracker):
        """Test restart pattern creation."""
        base_time = datetime.now()
        
        # Add multiple restart events
        for i in range(3):
            event = ContainerEvent(
                container_id="test123",
                container_name="test-container",
                image="nginx:latest",
                event_type=ContainerEventType.START,
                timestamp=base_time + timedelta(minutes=i * 2)
            )
            restart_tracker.add_event(event)
        
        pattern = restart_tracker.get_restart_pattern("test123")
        
        assert pattern is not None
        assert pattern.container_id == "test123"
        assert pattern.restart_count == 3
        assert len(pattern.restart_intervals) == 2
        assert pattern.restart_intervals[0] == 120  # 2 minutes in seconds
    
    def test_restart_loop_detection(self, restart_tracker):
        """Test restart loop detection."""
        base_time = datetime.now()
        
        # Add rapid restarts (restart loop)
        for i in range(5):
            event = ContainerEvent(
                container_id="test123",
                container_name="test-container",
                image="nginx:latest",
                event_type=ContainerEventType.START,
                timestamp=base_time + timedelta(seconds=i * 30)  # 30 seconds apart
            )
            restart_tracker.add_event(event)
        
        pattern = restart_tracker.get_restart_pattern("test123")
        
        assert pattern is not None
        assert pattern.is_restart_loop is True
        assert pattern.severity == "critical"
    
    def test_restart_loop_callback(self, restart_tracker):
        """Test restart loop callback."""
        callback_called = False
        received_pattern = None
        
        def loop_callback(pattern):
            nonlocal callback_called, received_pattern
            callback_called = True
            received_pattern = pattern
        
        restart_tracker.add_restart_loop_callback(loop_callback)
        
        base_time = datetime.now()
        
        # Add rapid restarts to trigger callback
        for i in range(4):
            event = ContainerEvent(
                container_id="test123",
                container_name="test-container",
                image="nginx:latest",
                event_type=ContainerEventType.START,
                timestamp=base_time + timedelta(seconds=i * 30)
            )
            restart_tracker.add_event(event)
        
        assert callback_called is True
        assert received_pattern.is_restart_loop is True
    
    def test_restart_statistics(self, restart_tracker):
        """Test restart statistics."""
        # Add events for multiple containers
        containers = ["container1", "container2", "container3"]
        base_time = datetime.now()
        
        for container_id in containers:
            for i in range(2):  # 2 restarts each
                event = ContainerEvent(
                    container_id=container_id,
                    container_name=f"test-{container_id}",
                    image="nginx:latest",
                    event_type=ContainerEventType.START,
                    timestamp=base_time + timedelta(minutes=i * 10)
                )
                restart_tracker.add_event(event)
        
        stats = restart_tracker.get_restart_statistics()
        
        assert stats["total_containers"] == 3
        assert stats["containers_with_restarts"] == 3
        assert stats["total_restarts"] == 6
        assert stats["average_restarts_per_container"] == 2.0


class TestUptimeTracker:
    """Test cases for UptimeTracker."""
    
    @pytest.fixture
    def uptime_tracker(self):
        """Create uptime tracker for testing."""
        return UptimeTracker(tracking_window=timedelta(days=1))
    
    def test_start_event_tracking(self, uptime_tracker):
        """Test container start event tracking."""
        start_time = datetime.now()
        event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=start_time
        )
        
        uptime_tracker.add_event(event)
        
        assert uptime_tracker.is_container_running("test123") is True
        
        current_uptime = uptime_tracker.get_current_uptime("test123")
        assert current_uptime is not None
        assert current_uptime >= 0
    
    def test_stop_event_tracking(self, uptime_tracker):
        """Test container stop event tracking."""
        start_time = datetime.now()
        stop_time = start_time + timedelta(minutes=30)
        
        # Start event
        start_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=start_time
        )
        uptime_tracker.add_event(start_event)
        
        # Stop event
        stop_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.STOP,
            timestamp=stop_time
        )
        uptime_tracker.add_event(stop_event)
        
        assert uptime_tracker.is_container_running("test123") is False
        
        stats = uptime_tracker.get_uptime_statistics("test123")
        assert stats is not None
        assert stats.total_uptime_seconds == 1800  # 30 minutes
        assert stats.uptime_sessions == 1
    
    def test_uptime_statistics(self, uptime_tracker):
        """Test uptime statistics calculation."""
        base_time = datetime.now()
        
        # Multiple uptime sessions
        sessions = [
            (base_time, base_time + timedelta(minutes=30)),  # 30 min
            (base_time + timedelta(hours=1), base_time + timedelta(hours=2)),  # 1 hour
            (base_time + timedelta(hours=3), None)  # Currently running
        ]
        
        for start_time, end_time in sessions:
            # Start event
            start_event = ContainerEvent(
                container_id="test123",
                container_name="test-container",
                image="nginx:latest",
                event_type=ContainerEventType.START,
                timestamp=start_time
            )
            uptime_tracker.add_event(start_event)
            
            # Stop event (if not currently running)
            if end_time:
                stop_event = ContainerEvent(
                    container_id="test123",
                    container_name="test-container",
                    image="nginx:latest",
                    event_type=ContainerEventType.STOP,
                    timestamp=end_time
                )
                uptime_tracker.add_event(stop_event)
        
        stats = uptime_tracker.get_uptime_statistics("test123")
        
        assert stats is not None
        assert stats.uptime_sessions == 3
        assert stats.total_uptime_seconds >= 5400  # At least 1.5 hours
        assert stats.current_uptime_seconds > 0  # Currently running
    
    def test_availability_score(self, uptime_tracker):
        """Test availability score calculation."""
        base_time = datetime.now()
        
        # High uptime session
        start_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=base_time
        )
        uptime_tracker.add_event(start_event)
        
        # Short downtime
        stop_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.STOP,
            timestamp=base_time + timedelta(hours=23, minutes=50)  # 99.6% uptime
        )
        uptime_tracker.add_event(stop_event)
        
        stats = uptime_tracker.get_uptime_statistics("test123")
        
        assert stats is not None
        assert stats.uptime_percentage > 99.0
        assert stats.availability_score in ["excellent", "good"]


class TestLifecycleManager:
    """Test cases for LifecycleManager."""
    
    @pytest.fixture
    def lifecycle_manager(self):
        """Create lifecycle manager for testing."""
        config = CollectorConfig(name="test_lifecycle_manager")
        return LifecycleManager(config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, lifecycle_manager):
        """Test lifecycle manager initialization."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_client.events.return_value = iter([])  # Empty event stream
            mock_docker.return_value = mock_client
            
            success = await lifecycle_manager.initialize()
            
            assert success is True
            assert lifecycle_manager.event_collector.runtime_type == "docker"
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, lifecycle_manager):
        """Test comprehensive metrics collection."""
        # Mock initialization
        lifecycle_manager.event_collector.runtime_type = "docker"
        
        # Add some test data
        test_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=datetime.now()
        )
        
        lifecycle_manager._handle_lifecycle_event(test_event)
        
        metrics = await lifecycle_manager.collect_container_metrics("test123")
        
        assert len(metrics) > 0
        
        # Check for different types of metrics
        metric_names = [m.name for m in metrics]
        assert any("lifecycle_event" in name for name in metric_names)
    
    def test_lifecycle_callback(self, lifecycle_manager):
        """Test lifecycle event callbacks."""
        callback_called = False
        received_event_type = None
        received_data = None
        
        def test_callback(event_type, data):
            nonlocal callback_called, received_event_type, received_data
            callback_called = True
            received_event_type = event_type
            received_data = data
        
        lifecycle_manager.add_lifecycle_callback(test_callback)
        
        # Trigger an event
        test_event = ContainerEvent(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            event_type=ContainerEventType.START,
            timestamp=datetime.now()
        )
        
        lifecycle_manager._handle_lifecycle_event(test_event)
        
        assert callback_called is True
        assert received_event_type == "lifecycle_event"
        assert received_data["container_id"] == "test123"
    
    def test_health_analysis(self, lifecycle_manager):
        """Test container health analysis."""
        # Add some problematic restart pattern
        base_time = datetime.now()
        
        for i in range(5):  # Multiple rapid restarts
            event = ContainerEvent(
                container_id="test123",
                container_name="test-container",
                image="nginx:latest",
                event_type=ContainerEventType.START,
                timestamp=base_time + timedelta(seconds=i * 30)
            )
            lifecycle_manager._handle_lifecycle_event(event)
        
        health = lifecycle_manager.analyze_container_health("test123")
        
        assert health["container_id"] == "test123"
        assert health["health_score"] < 100  # Should be reduced due to restarts
        assert len(health["issues"]) > 0
        assert len(health["recommendations"]) > 0
    
    def test_lifecycle_summary(self, lifecycle_manager):
        """Test lifecycle summary generation."""
        # Add some test events
        events = [
            ContainerEvent("test1", "container1", "nginx", ContainerEventType.START, datetime.now()),
            ContainerEvent("test2", "container2", "redis", ContainerEventType.START, datetime.now()),
            ContainerEvent("test1", "container1", "nginx", ContainerEventType.STOP, datetime.now())
        ]
        
        for event in events:
            lifecycle_manager._handle_lifecycle_event(event)
        
        summary = lifecycle_manager.get_lifecycle_summary()
        
        assert "events" in summary
        assert "restarts" in summary
        assert "uptime" in summary
        assert "timestamp" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])