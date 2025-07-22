"""
Container event collector for tracking start/stop/restart events.
"""

import asyncio
import docker
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import logging

from ..models import MetricValue, CollectorConfig
from ..collector_interface import ContainerMetricsCollector


class ContainerEventType(Enum):
    """Types of container events."""
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    DIE = "die"
    KILL = "kill"
    PAUSE = "pause"
    UNPAUSE = "unpause"
    CREATE = "create"
    DESTROY = "destroy"
    HEALTH_STATUS = "health_status"


@dataclass
class ContainerEvent:
    """Represents a container lifecycle event."""
    container_id: str
    container_name: str
    image: str
    event_type: ContainerEventType
    timestamp: datetime
    exit_code: Optional[int] = None
    signal: Optional[str] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
    
    def to_metric_value(self) -> MetricValue:
        """Convert event to MetricValue for storage."""
        labels = {
            "container_id": self.container_id,
            "container_name": self.container_name,
            "image": self.image,
            "event_type": self.event_type.value
        }
        
        if self.exit_code is not None:
            labels["exit_code"] = str(self.exit_code)
        
        if self.signal:
            labels["signal"] = self.signal
        
        # Add custom attributes as labels
        for key, value in self.attributes.items():
            if isinstance(value, (str, int, float, bool)):
                labels[f"attr_{key}"] = str(value)
        
        return MetricValue(
            name="container_lifecycle_event",
            value=1,  # Event occurrence
            timestamp=self.timestamp,
            labels=labels,
            unit="event"
        )


class ContainerEventCollector(ContainerMetricsCollector):
    """Collector for container lifecycle events."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.docker_client = None
        self.runtime_type = None
        self.event_listeners = []
        self.event_callbacks: List[Callable[[ContainerEvent], None]] = []
        self.event_history: List[ContainerEvent] = []
        self.max_history_size = config.parameters.get('max_history_size', 1000)
        self._listening = False
        self._listen_task = None
    
    async def initialize(self) -> bool:
        """Initialize the event collector."""
        try:
            # Try Docker first
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.runtime_type = "docker"
                self.logger.info("Event collector connected to Docker daemon")
                return True
            except Exception as docker_error:
                self.logger.debug(f"Docker connection failed: {docker_error}")
            
            # Try Podman fallback
            try:
                self.runtime_type = "podman"
                self.logger.info("Event collector using Podman runtime")
                return True
            except Exception as podman_error:
                self.logger.debug(f"Podman connection failed: {podman_error}")
            
            self.logger.error("No container runtime available for event collector")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize event collector: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.stop_listening()
        
        if self.docker_client:
            try:
                self.docker_client.close()
            except Exception as e:
                self.logger.error(f"Error closing Docker client: {str(e)}")
    
    def get_metric_types(self) -> List:
        """Get metric types this collector provides."""
        from ..models import MetricType
        return [MetricType.CONTAINER_LIFECYCLE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect lifecycle metrics for a specific container.
        This returns recent events for the container.
        """
        # Filter events for this container
        container_events = [
            event for event in self.event_history 
            if event.container_id == container_id
        ]
        
        # Convert events to metrics
        metrics = [event.to_metric_value() for event in container_events]
        
        # Add summary metrics
        if container_events:
            # Count events by type
            event_counts = {}
            for event in container_events:
                event_type = event.event_type.value
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Create count metrics
            for event_type, count in event_counts.items():
                labels = {
                    "container_id": container_id,
                    "event_type": event_type
                }
                
                metrics.append(MetricValue(
                    name="container_lifecycle_event_count",
                    value=count,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="count"
                ))
        
        return metrics
    
    def add_event_callback(self, callback: Callable[[ContainerEvent], None]) -> None:
        """Add a callback to be called when events are received."""
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[ContainerEvent], None]) -> None:
        """Remove an event callback."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    async def start_listening(self) -> bool:
        """Start listening for container events."""
        if self._listening:
            self.logger.warning("Already listening for events")
            return True
        
        try:
            if self.runtime_type == "docker":
                self._listen_task = asyncio.create_task(self._listen_docker_events())
            elif self.runtime_type == "podman":
                self._listen_task = asyncio.create_task(self._listen_podman_events())
            else:
                self.logger.error("No runtime available for event listening")
                return False
            
            self._listening = True
            self.logger.info("Started listening for container events")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start event listening: {str(e)}")
            return False
    
    async def stop_listening(self) -> None:
        """Stop listening for container events."""
        if not self._listening:
            return
        
        self._listening = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
        
        self.logger.info("Stopped listening for container events")
    
    async def _listen_docker_events(self) -> None:
        """Listen for Docker container events."""
        try:
            # Filter for container events only
            filters = {'type': 'container'}
            
            for event in self.docker_client.events(filters=filters, decode=True):
                if not self._listening:
                    break
                
                try:
                    container_event = self._parse_docker_event(event)
                    if container_event:
                        await self._handle_event(container_event)
                        
                except Exception as e:
                    self.logger.error(f"Error processing Docker event: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error in Docker event listener: {str(e)}")
    
    async def _listen_podman_events(self) -> None:
        """Listen for Podman container events."""
        try:
            # Use podman events command
            proc = await asyncio.create_subprocess_exec(
                'podman', 'events', '--format', 'json', '--filter', 'type=container',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            while self._listening and proc.returncode is None:
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
                    if not line:
                        break
                    
                    event_data = json.loads(line.decode().strip())
                    container_event = self._parse_podman_event(event_data)
                    
                    if container_event:
                        await self._handle_event(container_event)
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing Podman event: {str(e)}")
            
            # Clean up process
            if proc.returncode is None:
                proc.terminate()
                await proc.wait()
                
        except Exception as e:
            self.logger.error(f"Error in Podman event listener: {str(e)}")
    
    def _parse_docker_event(self, event: Dict[str, Any]) -> Optional[ContainerEvent]:
        """Parse Docker event into ContainerEvent."""
        try:
            action = event.get('Action', '')
            
            # Map Docker actions to our event types
            event_type_map = {
                'start': ContainerEventType.START,
                'stop': ContainerEventType.STOP,
                'restart': ContainerEventType.RESTART,
                'die': ContainerEventType.DIE,
                'kill': ContainerEventType.KILL,
                'pause': ContainerEventType.PAUSE,
                'unpause': ContainerEventType.UNPAUSE,
                'create': ContainerEventType.CREATE,
                'destroy': ContainerEventType.DESTROY,
                'health_status': ContainerEventType.HEALTH_STATUS
            }
            
            if action not in event_type_map:
                return None  # Skip unknown events
            
            actor = event.get('Actor', {})
            attributes = actor.get('Attributes', {})
            
            container_id = actor.get('ID', '')
            container_name = attributes.get('name', '')
            image = attributes.get('image', '')
            
            # Parse timestamp
            timestamp_str = event.get('time')
            if timestamp_str:
                timestamp = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Extract exit code and signal if available
            exit_code = None
            signal = None
            
            if 'exitCode' in attributes:
                try:
                    exit_code = int(attributes['exitCode'])
                except (ValueError, TypeError):
                    pass
            
            if 'signal' in attributes:
                signal = attributes['signal']
            
            return ContainerEvent(
                container_id=container_id,
                container_name=container_name,
                image=image,
                event_type=event_type_map[action],
                timestamp=timestamp,
                exit_code=exit_code,
                signal=signal,
                attributes=attributes
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing Docker event: {str(e)}")
            return None
    
    def _parse_podman_event(self, event: Dict[str, Any]) -> Optional[ContainerEvent]:
        """Parse Podman event into ContainerEvent."""
        try:
            action = event.get('Action', '')
            
            # Map Podman actions to our event types
            event_type_map = {
                'start': ContainerEventType.START,
                'stop': ContainerEventType.STOP,
                'restart': ContainerEventType.RESTART,
                'died': ContainerEventType.DIE,
                'kill': ContainerEventType.KILL,
                'pause': ContainerEventType.PAUSE,
                'unpause': ContainerEventType.UNPAUSE,
                'create': ContainerEventType.CREATE,
                'remove': ContainerEventType.DESTROY,
                'health_status': ContainerEventType.HEALTH_STATUS
            }
            
            if action not in event_type_map:
                return None
            
            container_id = event.get('ID', '')
            
            # Get container details
            attributes = event.get('Attributes', {})
            container_name = attributes.get('name', '')
            image = attributes.get('image', '')
            
            # Parse timestamp
            timestamp_str = event.get('Time')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Extract exit code and signal
            exit_code = None
            signal = None
            
            if 'exit_code' in attributes:
                try:
                    exit_code = int(attributes['exit_code'])
                except (ValueError, TypeError):
                    pass
            
            if 'signal' in attributes:
                signal = attributes['signal']
            
            return ContainerEvent(
                container_id=container_id,
                container_name=container_name,
                image=image,
                event_type=event_type_map[action],
                timestamp=timestamp,
                exit_code=exit_code,
                signal=signal,
                attributes=attributes
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing Podman event: {str(e)}")
            return None
    
    async def _handle_event(self, event: ContainerEvent) -> None:
        """Handle a received container event."""
        # Add to history
        self.event_history.append(event)
        
        # Maintain history size limit
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Log the event
        self.logger.info(
            f"Container event: {event.container_name} ({event.container_id[:12]}) "
            f"{event.event_type.value} at {event.timestamp}"
        )
        
        # Call registered callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in event callback: {str(e)}")
    
    def get_recent_events(self, container_id: Optional[str] = None, 
                         event_type: Optional[ContainerEventType] = None,
                         limit: int = 100) -> List[ContainerEvent]:
        """
        Get recent events with optional filtering.
        
        Args:
            container_id: Filter by container ID
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of ContainerEvent objects
        """
        events = self.event_history
        
        # Apply filters
        if container_id:
            events = [e for e in events if e.container_id == container_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (most recent first) and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected events."""
        if not self.event_history:
            return {"total_events": 0}
        
        stats = {
            "total_events": len(self.event_history),
            "events_by_type": {},
            "containers_seen": set(),
            "time_range": {
                "earliest": min(e.timestamp for e in self.event_history),
                "latest": max(e.timestamp for e in self.event_history)
            }
        }
        
        # Count events by type
        for event in self.event_history:
            event_type = event.event_type.value
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            stats["containers_seen"].add(event.container_id)
        
        # Convert set to count
        stats["unique_containers"] = len(stats["containers_seen"])
        del stats["containers_seen"]  # Remove set for JSON serialization
        
        return stats