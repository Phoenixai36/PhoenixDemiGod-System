"""
Tests for container event listener.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.containers.event_listener import (
    ContainerEventListener, EventListenerConfig, EventType, log_event_handler
)
from src.containers.models import ContainerEvent, Container, ContainerStatus
from src.containers.registry import ContainerRegistry


class TestEventListenerConfig:
    """Test cases for EventListenerConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = EventListenerConfig()
        
        assert config.podman_config is None
        assert config.event_types is None
        assert config.container_filters is None
        assert config.auto_reconnect is True
        assert config.reconnect_delay == 5.0
        assert config.max_reconnect_attempts == 10
        assert config.event_buffer_size == 1000
        assert config.event_batch_size == 10
        assert config.event_batch_timeout == 1.0
        assert config.discover_existing_containers is True
        assert config.sync_on_startup is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = EventListenerConfig(
            event_types={EventType.CONTAINER_START, EventType.CONTAINER_STOP},
            container_filters={"name": "test"},
            auto_reconnect=False,
            event_buffer_size=500
        )
        
        assert config.event_types == {EventType.CONTAINER_START, EventType.CONTAINER_STOP}
        assert config.container_filters == {"name": "test"}
        assert config.auto_reconnect is False
        assert config.event_buffer_size == 500


class TestContainerEventListener:
    """Test cases for ContainerEventListener."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return EventListenerConfig(
            auto_reconnect=False,
            discover_existing_containers=False,
            event_batch_timeout=0.1  # Fast for testing
        )
    
    @pytest.fixture
    def registry(self):
        """Create mock registry."""
        return AsyncMock(spec=ContainerRegistry)
    
    @pytest.fixture
    def listener(self, config, registry):
        """Create test listener."""
        return ContainerEventListener(config, registry)
    
    @pytest.fixture
    def sample_event(self):
        """Create sample container event."""
        return ContainerEvent(
            timestamp=datetime.now(),
            container_id="abc123",
            container_name="test-container",
            action="start",
            image="nginx:latest",
            labels={"app": "test"},
            raw_data={}
        )
    
    def test_listener_creation(self, listener, config, registry):
        """Test listener creation."""
        assert listener.config == config
        assert listener.registry == registry
        assert listener.client is None
        assert not listener._running
        assert len(listener._event_handlers) == 0
        assert len(listener._async_event_handlers) == 0
    
    def test_add_event_handlers(self, listener):
        """Test adding event handlers."""
        def sync_handler(event):
            pass
        
        async def async_handler(event):
            pass
        
        listener.add_event_handler(sync_handler)
        listener.add_async_event_handler(async_handler)
        
        assert len(listener._event_handlers) == 1
        assert len(listener._async_event_handlers) == 1
        assert sync_handler in listener._event_handlers
        assert async_handler in listener._async_event_handlers
    
    def test_remove_event_handlers(self, listener):
        """Test removing event handlers."""
        def sync_handler(event):
            pass
        
        async def async_handler(event):
            pass
        
        listener.add_event_handler(sync_handler)
        listener.add_async_event_handler(async_handler)
        
        assert listener.remove_event_handler(sync_handler) is True
        assert listener.remove_event_handler(async_handler) is True
        assert len(listener._event_handlers) == 0
        assert len(listener._async_event_handlers) == 0
        
        # Try to remove non-existent handler
        assert listener.remove_event_handler(sync_handler) is False
    
    @pytest.mark.asyncio
    async def test_context_manager(self, listener):
        """Test async context manager."""
        with patch.object(listener, 'start') as mock_start, \
             patch.object(listener, 'stop') as mock_stop:
            
            async with listener:
                mock_start.assert_called_once()
            
            mock_stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_stop(self, listener):
        """Test start and stop operations."""
        with patch.object(listener, '_initialize_client') as mock_init, \
             patch.object(listener, '_discover_existing_containers') as mock_discover:
            
            # Test start
            await listener.start()
            
            assert listener._running is True
            assert listener._stats["uptime_start"] is not None
            mock_init.assert_called_once()
            
            # Test stop
            await listener.stop()
            
            assert listener._running is False
    
    @pytest.mark.asyncio
    async def test_initialize_client(self, listener):
        """Test client initialization."""
        mock_client = AsyncMock()
        
        with patch('src.containers.event_listener.PodmanClient', return_value=mock_client):
            await listener._initialize_client()
            
            assert listener.client == mock_client
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discover_existing_containers(self, listener):
        """Test discovering existing containers."""
        mock_client = AsyncMock()
        listener.client = mock_client
        
        # Mock containers
        containers = [
            Container(
                id="abc123",
                name="test1",
                image="nginx:latest",
                status=ContainerStatus.RUNNING,
                created_at=datetime.now(),
                ports=[],
                labels={"app": "test"}
            ),
            Container(
                id="def456",
                name="test2",
                image="redis:latest",
                status=ContainerStatus.STOPPED,
                created_at=datetime.now(),
                ports=[],
                labels={}
            )
        ]
        
        mock_client.list_containers.return_value = containers
        
        await listener._discover_existing_containers()
        
        # Should have added one event for running container
        assert len(listener._event_buffer) == 1
        event = listener._event_buffer[0]
        assert event.container_id == "abc123"
        assert event.action == "start"
        assert event.raw_data["synthetic"] is True
    
    @pytest.mark.asyncio
    async def test_should_process_event(self, listener, sample_event):
        """Test event filtering."""
        # No filters - should process all events
        assert listener._should_process_event(sample_event) is True
        
        # Event type filter
        listener.config.event_types = {EventType.CONTAINER_START}
        assert listener._should_process_event(sample_event) is True
        
        sample_event.action = "stop"
        assert listener._should_process_event(sample_event) is False
        
        # Container name filter
        listener.config.event_types = None
        listener.config.container_filters = {"name": "test"}
        sample_event.action = "start"
        assert listener._should_process_event(sample_event) is True
        
        sample_event.container_name = "other-container"
        assert listener._should_process_event(sample_event) is False
    
    @pytest.mark.asyncio
    async def test_process_single_event(self, listener, sample_event, registry):
        """Test processing a single event."""
        # Add handlers
        sync_handler = Mock()
        async_handler = AsyncMock()
        
        listener.add_event_handler(sync_handler)
        listener.add_async_event_handler(async_handler)
        
        # Mock client for registry update
        mock_client = AsyncMock()
        mock_container = Container(
            id="abc123",
            name="test-container",
            image="nginx:latest",
            status=ContainerStatus.RUNNING,
            created_at=datetime.now(),
            ports=[],
            labels={}
        )
        mock_client.get_container.return_value = mock_container
        listener.client = mock_client
        
        await listener._process_single_event(sample_event)
        
        # Check handlers were called
        sync_handler.assert_called_once_with(sample_event)
        async_handler.assert_called_once_with(sample_event)
        
        # Check registry was updated
        registry.register_container.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_registry_from_event(self, listener, registry):
        """Test registry updates from events."""
        mock_client = AsyncMock()
        mock_container = Container(
            id="abc123",
            name="test",
            image="nginx",
            status=ContainerStatus.RUNNING,
            created_at=datetime.now(),
            ports=[],
            labels={}
        )
        mock_client.get_container.return_value = mock_container
        listener.client = mock_client
        
        # Test start event
        start_event = ContainerEvent(
            timestamp=datetime.now(),
            container_id="abc123",
            container_name="test",
            action="start",
            image="nginx",
            labels={},
            raw_data={}
        )
        
        await listener._update_registry_from_event(start_event)
        registry.register_container.assert_called_once_with(mock_container)
        
        # Test stop event
        stop_event = ContainerEvent(
            timestamp=datetime.now(),
            container_id="abc123",
            container_name="test",
            action="stop",
            image="nginx",
            labels={},
            raw_data={}
        )
        
        await listener._update_registry_from_event(stop_event)
        registry.update_container_status.assert_called_with("abc123", ContainerStatus.STOPPED)
        
        # Test remove event
        remove_event = ContainerEvent(
            timestamp=datetime.now(),
            container_id="abc123",
            container_name="test",
            action="remove",
            image="nginx",
            labels={},
            raw_data={}
        )
        
        await listener._update_registry_from_event(remove_event)
        registry.unregister_container.assert_called_with("abc123")
    
    @pytest.mark.asyncio
    async def test_process_event_batch(self, listener, sample_event):
        """Test batch event processing."""
        events = [sample_event] * 3
        
        with patch.object(listener, '_process_single_event') as mock_process:
            await listener._process_event_batch(events)
            
            assert mock_process.call_count == 3
            listener._stats["events_processed"] == 3
    
    def test_get_stats(self, listener):
        """Test getting listener statistics."""
        stats = listener.get_stats()
        
        assert "events_received" in stats
        assert "events_processed" in stats
        assert "running" in stats
        assert "uptime_seconds" in stats
        assert "event_buffer_size" in stats
        assert "handlers_count" in stats
        
        assert stats["running"] is False
        assert stats["handlers_count"] == 0
        assert stats["event_buffer_size"] == 0
    
    @pytest.mark.asyncio
    async def test_force_sync(self, listener):
        """Test force synchronization."""
        with patch.object(listener, '_discover_existing_containers') as mock_discover, \
             patch.object(listener, '_process_event_batch') as mock_process:
            
            # Add some events to buffer
            listener._event_buffer = [Mock(), Mock()]
            
            await listener.force_sync()
            
            mock_discover.assert_called_once()
            mock_process.assert_called_once()
            assert len(listener._event_buffer) == 0


class TestEventType:
    """Test cases for EventType enum."""
    
    def test_event_types(self):
        """Test event type values."""
        assert EventType.CONTAINER_START.value == "start"
        assert EventType.CONTAINER_STOP.value == "stop"
        assert EventType.CONTAINER_DIE.value == "die"
        assert EventType.CONTAINER_KILL.value == "kill"
        assert EventType.CONTAINER_RESTART.value == "restart"
        assert EventType.CONTAINER_PAUSE.value == "pause"
        assert EventType.CONTAINER_UNPAUSE.value == "unpause"
        assert EventType.CONTAINER_CREATE.value == "create"
        assert EventType.CONTAINER_DESTROY.value == "destroy"
        assert EventType.CONTAINER_REMOVE.value == "remove"


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_create_event_listener(self):
        """Test create_event_listener function."""
        from src.containers.event_listener import create_event_listener
        
        registry = AsyncMock()
        event_types = [EventType.CONTAINER_START, EventType.CONTAINER_STOP]
        
        listener = await create_event_listener(
            registry=registry,
            event_types=event_types,
            container_name_filter="test"
        )
        
        assert listener.registry == registry
        assert listener.config.event_types == set(event_types)
        assert listener.config.container_filters == {"name": "test"}
    
    def test_log_event_handler(self, sample_event):
        """Test log event handler."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            log_event_handler(sample_event)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Container start" in call_args
            assert "test-container" in call_args


@pytest.mark.integration
class TestEventListenerIntegration:
    """Integration tests for event listener (require actual container runtime)."""
    
    @pytest.fixture
    async def listener(self):
        """Create listener for integration tests."""
        config = EventListenerConfig(
            discover_existing_containers=True,
            event_batch_timeout=0.5
        )
        
        listener = ContainerEventListener(config)
        
        try:
            await listener.start()
            yield listener
        except Exception as e:
            pytest.skip(f"Container runtime not available: {str(e)}")
        finally:
            if listener:
                await listener.stop()
    
    @pytest.mark.asyncio
    async def test_real_event_listening(self, listener):
        """Test real event listening."""
        events_received = []
        
        def event_handler(event):
            events_received.append(event)
        
        listener.add_event_handler(event_handler)
        
        # Let it run for a short time
        await asyncio.sleep(2)
        
        # Check stats
        stats = listener.get_stats()
        assert stats["running"] is True
        
        # If there are any containers running, we might have received events
        # This is not guaranteed, so we just check the listener is working
        assert isinstance(stats["events_received"], int)
        assert isinstance(stats["events_processed"], int)