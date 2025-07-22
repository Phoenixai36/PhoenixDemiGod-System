"""
Container event listener for real-time monitoring.

This module provides event listening capabilities for container lifecycle events,
supporting both Podman and Docker with automatic discovery and failover.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .models import ContainerEvent, Container, ContainerStatus
from .podman_client import PodmanClient, PodmanConfig, PodmanAPIError
from .registry import ContainerRegistry


class EventType(Enum):
    """Container event types."""
    CONTAINER_START = "start"
    CONTAINER_STOP = "stop"
    CONTAINER_DIE = "die"
    CONTAINER_KILL = "kill"
    CONTAINER_RESTART = "restart"
    CONTAINER_PAUSE = "pause"
    CONTAINER_UNPAUSE = "unpause"
    CONTAINER_CREATE = "create"
    CONTAINER_DESTROY = "destroy"
    CONTAINER_REMOVE = "remove"
    CONTAINER_RENAME = "rename"
    CONTAINER_ATTACH = "attach"
    CONTAINER_DETACH = "detach"
    CONTAINER_EXEC_CREATE = "exec_create"
    CONTAINER_EXEC_START = "exec_start"
    CONTAINER_EXEC_DIE = "exec_die"
    CONTAINER_OOM = "oom"
    CONTAINER_HEALTH_STATUS = "health_status"


@dataclass
class EventListenerConfig:
    """Configuration for container event listener."""
    # Connection settings
    podman_config: Optional[PodmanConfig] = None
    
    # Event filtering
    event_types: Optional[Set[EventType]] = None  # None = all events
    container_filters: Optional[Dict[str, str]] = None
    
    # Behavior
    auto_reconnect: bool = True
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 10
    
    # Buffer settings
    event_buffer_size: int = 1000
    event_batch_size: int = 10
    event_batch_timeout: float = 1.0
    
    # Startup behavior
    discover_existing_containers: bool = True
    sync_on_startup: bool = True


class ContainerEventListener:
    """
    Container event listener with support for Podman and Docker.
    
    Features:
    - Real-time event streaming
    - Automatic reconnection
    - Event filtering and batching
    - Container discovery on startup
    - Registry synchronization
    """
    
    def __init__(self, config: EventListenerConfig = None, registry: Optional[ContainerRegistry] = None):
        self.config = config or EventListenerConfig()
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        
        # Client and connection
        self.client: Optional[PodmanClient] = None
        self._event_stream: Optional[AsyncGenerator] = None
        self._running = False
        self._reconnect_count = 0
        
        # Event handling
        self._event_handlers: List[Callable[[ContainerEvent], None]] = []
        self._async_event_handlers: List[Callable[[ContainerEvent], Any]] = []
        self._event_buffer: List[ContainerEvent] = []
        self._last_event_time = datetime.now()
        
        # Background tasks
        self._listener_task: Optional[asyncio.Task] = None
        self._batch_processor_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "events_received": 0,
            "events_processed": 0,
            "reconnections": 0,
            "errors": 0,
            "last_event_time": None,
            "uptime_start": None
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    def add_event_handler(self, handler: Callable[[ContainerEvent], None]) -> None:
        """Add a synchronous event handler."""
        self._event_handlers.append(handler)
        self.logger.info(f"Added event handler: {handler.__name__}")
    
    def add_async_event_handler(self, handler: Callable[[ContainerEvent], Any]) -> None:
        """Add an asynchronous event handler."""
        self._async_event_handlers.append(handler)
        self.logger.info(f"Added async event handler: {handler.__name__}")
    
    def remove_event_handler(self, handler: Callable) -> bool:
        """Remove an event handler."""
        try:
            if handler in self._event_handlers:
                self._event_handlers.remove(handler)
                return True
            elif handler in self._async_event_handlers:
                self._async_event_handlers.remove(handler)
                return True
            return False
        except ValueError:
            return False
    
    async def start(self) -> None:
        """Start the event listener."""
        if self._running:
            self.logger.warning("Event listener is already running")
            return
        
        self.logger.info("Starting container event listener")
        self._running = True
        self._stats["uptime_start"] = datetime.now()
        
        # Initialize client
        await self._initialize_client()
        
        # Discover existing containers if configured
        if self.config.discover_existing_containers:
            await self._discover_existing_containers()
        
        # Start background tasks
        self._listener_task = asyncio.create_task(self._event_listener_loop())
        self._batch_processor_task = asyncio.create_task(self._batch_processor_loop())
        
        self.logger.info("Container event listener started successfully")
    
    async def stop(self) -> None:
        """Stop the event listener."""
        if not self._running:
            return
        
        self.logger.info("Stopping container event listener")
        self._running = False
        
        # Cancel background tasks
        tasks = [self._listener_task, self._batch_processor_task, self._reconnect_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Process remaining events
        if self._event_buffer:
            await self._process_event_batch(self._event_buffer.copy())
            self._event_buffer.clear()
        
        # Close client
        if self.client:
            await self.client.close()
            self.client = None
        
        self.logger.info("Container event listener stopped")
    
    async def _initialize_client(self) -> None:
        """Initialize the container client."""
        podman_config = self.config.podman_config or PodmanConfig()
        self.client = PodmanClient(podman_config)
        
        try:
            await self.client.connect()
            self.logger.info("Connected to container runtime")
        except Exception as e:
            self.logger.error(f"Failed to connect to container runtime: {str(e)}")
            raise
    
    async def _discover_existing_containers(self) -> None:
        """Discover and register existing containers."""
        if not self.client:
            return
        
        try:
            self.logger.info("Discovering existing containers...")
            containers = await self.client.list_containers(all_containers=True)
            
            discovered_count = 0
            for container in containers:
                # Create synthetic start event for running containers
                if container.status == ContainerStatus.RUNNING:
                    event = ContainerEvent(
                        timestamp=container.created_at or datetime.now(),
                        container_id=container.id,
                        container_name=container.name,
                        action="start",
                        image=container.image,
                        labels=container.labels,
                        raw_data={"synthetic": True, "discovery": True}
                    )
                    
                    # Add to buffer for processing
                    self._event_buffer.append(event)
                    discovered_count += 1
                
                # Update registry if available
                if self.registry and self.config.sync_on_startup:
                    await self.registry.register_container(container)
            
            self.logger.info(f"Discovered {discovered_count} running containers")
            
        except Exception as e:
            self.logger.error(f"Failed to discover existing containers: {str(e)}")
    
    async def _event_listener_loop(self) -> None:
        """Main event listening loop with reconnection logic."""
        while self._running:
            try:
                await self._listen_for_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._stats["errors"] += 1
                self.logger.error(f"Event listener error: {str(e)}")
                
                if self.config.auto_reconnect and self._running:
                    await self._handle_reconnection()
                else:
                    break
    
    async def _listen_for_events(self) -> None:
        """Listen for container events."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        self.logger.info("Starting event stream...")
        
        try:
            # Get event stream
            event_stream = self.client.get_events()
            
            async for event in event_stream:
                if not self._running:
                    break
                
                # Filter events if configured
                if self._should_process_event(event):
                    self._stats["events_received"] += 1
                    self._stats["last_event_time"] = event.timestamp.isoformat()
                    self._last_event_time = datetime.now()
                    
                    # Add to buffer
                    self._event_buffer.append(event)
                    
                    # Log event
                    self.logger.debug(
                        f"Received event: {event.action} for container "
                        f"{event.container_name} ({event.container_id[:12]})"
                    )
                
        except Exception as e:
            self.logger.error(f"Event stream error: {str(e)}")
            raise
    
    async def _batch_processor_loop(self) -> None:
        """Process events in batches."""
        while self._running:
            try:
                # Wait for events or timeout
                await asyncio.sleep(self.config.event_batch_timeout)
                
                # Process batch if we have events
                if self._event_buffer:
                    batch_size = min(len(self._event_buffer), self.config.event_batch_size)
                    batch = self._event_buffer[:batch_size]
                    self._event_buffer = self._event_buffer[batch_size:]
                    
                    await self._process_event_batch(batch)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Batch processor error: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _process_event_batch(self, events: List[ContainerEvent]) -> None:
        """Process a batch of events."""
        if not events:
            return
        
        self.logger.debug(f"Processing batch of {len(events)} events")
        
        for event in events:
            try:
                await self._process_single_event(event)
                self._stats["events_processed"] += 1
            except Exception as e:
                self.logger.error(f"Error processing event {event.container_id}: {str(e)}")
    
    async def _process_single_event(self, event: ContainerEvent) -> None:
        """Process a single container event."""
        # Update registry if available
        if self.registry:
            await self._update_registry_from_event(event)
        
        # Call synchronous handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Error in sync event handler {handler.__name__}: {str(e)}")
        
        # Call asynchronous handlers
        for handler in self._async_event_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self.logger.error(f"Error in async event handler {handler.__name__}: {str(e)}")
    
    async def _update_registry_from_event(self, event: ContainerEvent) -> None:
        """Update container registry based on event."""
        try:
            if event.action in ["start", "create", "restart"]:
                # Get full container info and register
                container = await self.client.get_container(event.container_id)
                await self.registry.register_container(container)
                
            elif event.action in ["stop", "die", "kill"]:
                # Update container status
                await self.registry.update_container_status(
                    event.container_id, 
                    ContainerStatus.STOPPED
                )
                
            elif event.action in ["remove", "destroy"]:
                # Remove from registry
                await self.registry.unregister_container(event.container_id)
                
            elif event.action == "pause":
                await self.registry.update_container_status(
                    event.container_id, 
                    ContainerStatus.PAUSED
                )
                
            elif event.action == "unpause":
                await self.registry.update_container_status(
                    event.container_id, 
                    ContainerStatus.RUNNING
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update registry for event {event.action}: {str(e)}")
    
    def _should_process_event(self, event: ContainerEvent) -> bool:
        """Check if event should be processed based on filters."""
        # Check event type filter
        if self.config.event_types:
            try:
                event_type = EventType(event.action)
                if event_type not in self.config.event_types:
                    return False
            except ValueError:
                # Unknown event type, process if no filter is set
                pass
        
        # Check container filters
        if self.config.container_filters:
            for key, value in self.config.container_filters.items():
                if key == "name" and value not in event.container_name:
                    return False
                elif key == "image" and value not in event.image:
                    return False
                elif key in event.labels and event.labels[key] != value:
                    return False
        
        return True
    
    async def _handle_reconnection(self) -> None:
        """Handle reconnection logic."""
        if self._reconnect_count >= self.config.max_reconnect_attempts:
            self.logger.error("Maximum reconnection attempts reached, stopping listener")
            self._running = False
            return
        
        self._reconnect_count += 1
        self._stats["reconnections"] += 1
        
        self.logger.info(f"Attempting reconnection {self._reconnect_count}/{self.config.max_reconnect_attempts}")
        
        # Close existing client
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass
        
        # Wait before reconnecting
        await asyncio.sleep(self.config.reconnect_delay)
        
        # Reinitialize client
        try:
            await self._initialize_client()
            self._reconnect_count = 0  # Reset on successful connection
            self.logger.info("Reconnection successful")
        except Exception as e:
            self.logger.error(f"Reconnection failed: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get listener statistics."""
        uptime = None
        if self._stats["uptime_start"]:
            uptime = (datetime.now() - self._stats["uptime_start"]).total_seconds()
        
        return {
            **self._stats,
            "running": self._running,
            "uptime_seconds": uptime,
            "event_buffer_size": len(self._event_buffer),
            "handlers_count": len(self._event_handlers) + len(self._async_event_handlers),
            "reconnect_count": self._reconnect_count,
            "last_event_age_seconds": (datetime.now() - self._last_event_time).total_seconds()
        }
    
    async def force_sync(self) -> None:
        """Force synchronization with container runtime."""
        self.logger.info("Forcing container synchronization...")
        await self._discover_existing_containers()
        
        # Process any buffered events immediately
        if self._event_buffer:
            batch = self._event_buffer.copy()
            self._event_buffer.clear()
            await self._process_event_batch(batch)


# Convenience functions for common use cases

async def create_event_listener(
    registry: Optional[ContainerRegistry] = None,
    event_types: Optional[List[EventType]] = None,
    container_name_filter: Optional[str] = None
) -> ContainerEventListener:
    """Create and configure an event listener with common settings."""
    
    config = EventListenerConfig()
    
    if event_types:
        config.event_types = set(event_types)
    
    if container_name_filter:
        config.container_filters = {"name": container_name_filter}
    
    return ContainerEventListener(config, registry)


def log_event_handler(event: ContainerEvent) -> None:
    """Simple event handler that logs events."""
    logger = logging.getLogger("container_events")
    logger.info(
        f"Container {event.action}: {event.container_name} "
        f"({event.container_id[:12]}) - {event.image}"
    )


async def registry_sync_handler(event: ContainerEvent, registry: ContainerRegistry) -> None:
    """Event handler that keeps registry in sync."""
    # This is handled automatically by the listener if registry is provided
    pass