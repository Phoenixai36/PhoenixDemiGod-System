"""
Container lifecycle metrics collector.

This module provides collectors for tracking container lifecycle events
including start/stop events, restart counts, and uptime tracking.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum

from ..collector_interface import MetricsCollector, ContainerMetricsCollector
from ..models import MetricValue, MetricType, CollectorConfig


class ContainerEvent(Enum):
    """Container lifecycle event types."""
    STARTED = "started"
    STOPPED = "stopped"
    RESTARTED = "restarted"
    DIED = "died"
    KILLED = "killed"
    PAUSED = "paused"
    UNPAUSED = "unpaused"


@dataclass
class ContainerLifecycleEvent:
    """Represents a container lifecycle event."""
    container_id: str
    container_name: str
    event_type: ContainerEvent
    timestamp: datetime
    exit_code: Optional[int] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContainerState:
    """Tracks the current state of a container."""
    container_id: str
    container_name: str
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    restart_count: int = 0
    total_uptime: timedelta = field(default_factory=lambda: timedelta(0))
    current_uptime_start: Optional[datetime] = None
    is_running: bool = False
    last_event: Optional[ContainerLifecycleEvent] = None
    exit_codes: List[int] = field(default_factory=list)


class ContainerLifecycleCollector(ContainerMetricsCollector):
    """Collects container lifecycle metrics including events, uptime, and restart counts."""
    
    def __init__(self, config: CollectorConfig, container_client=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.container_client = container_client
        self.container_states: Dict[str, ContainerState] = {}
        self.event_history: List[ContainerLifecycleEvent] = []
        self.max_history_size = config.parameters.get('max_history_size', 10000)
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Initialize the collector."""
        try:
            # Try to connect to container runtime
            if self.container_client:
                # Test connection
                self.logger.info("Lifecycle collector initialized successfully")
                return True
            else:
                self.logger.warning("No container client provided, lifecycle collector will have limited functionality")
                return True
        except Exception as e:
            self.logger.error(f"Failed to initialize lifecycle collector: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.stop_monitoring()
        self.logger.info("Lifecycle collector cleaned up")
    
    def get_metric_types(self) -> List[MetricType]:
        """Get the types of metrics this collector can gather."""
        return [MetricType.CONTAINER_LIFECYCLE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect lifecycle metrics for a specific container."""
        state = self.container_states.get(container_id)
        if not state:
            return []
        
        metrics = []
        current_time = datetime.now()
        
        # Update current uptime if container is running
        if state.is_running and state.current_uptime_start:
            current_session_uptime = current_time - state.current_uptime_start
            total_uptime = state.total_uptime + current_session_uptime
        else:
            total_uptime = state.total_uptime
        
        # Container uptime metric
        metrics.append(MetricValue(
            name="container_uptime_seconds",
            value=total_uptime.total_seconds(),
            timestamp=current_time,
            labels={
                "container_id": container_id,
                "container_name": state.container_name,
                "status": "running" if state.is_running else "stopped"
            }
        ))
        
        # Container restart count metric
        metrics.append(MetricValue(
            name="container_restart_count",
            value=state.restart_count,
            timestamp=current_time,
            labels={
                "container_id": container_id,
                "container_name": state.container_name
            }
        ))
        
        # Container running status metric
        metrics.append(MetricValue(
            name="container_running",
            value=1 if state.is_running else 0,
            timestamp=current_time,
            labels={
                "container_id": container_id,
                "container_name": state.container_name
            }
        ))
        
        # Time since last restart (if applicable)
        if state.started_at:
            time_since_start = (current_time - state.started_at).total_seconds()
            metrics.append(MetricValue(
                name="container_time_since_start_seconds",
                value=time_since_start,
                timestamp=current_time,
                labels={
                    "container_id": container_id,
                    "container_name": state.container_name
                }
            ))
        
        return metrics
    
    async def collect_metrics(self) -> List[MetricValue]:
        """Collect current lifecycle metrics for all tracked containers."""
        metrics = []
        current_time = datetime.now()
        
        for container_id, state in self.container_states.items():
            # Update current uptime if container is running
            if state.is_running and state.current_uptime_start:
                current_session_uptime = current_time - state.current_uptime_start
                total_uptime = state.total_uptime + current_session_uptime
            else:
                total_uptime = state.total_uptime
            
            # Container uptime metric
            metrics.append(MetricValue(
                name="container_uptime_seconds",
                value=total_uptime.total_seconds(),
                timestamp=current_time,
                labels={
                    "container_id": container_id,
                    "container_name": state.container_name,
                    "status": "running" if state.is_running else "stopped"
                }
            ))
            
            # Container restart count metric
            metrics.append(MetricValue(
                name="container_restart_count",
                value=state.restart_count,
                timestamp=current_time,
                labels={
                    "container_id": container_id,
                    "container_name": state.container_name
                }
            ))
            
            # Container running status metric
            metrics.append(MetricValue(
                name="container_running",
                value=1 if state.is_running else 0,
                timestamp=current_time,
                labels={
                    "container_id": container_id,
                    "container_name": state.container_name
                }
            ))
            
            # Time since last restart (if applicable)
            if state.started_at:
                time_since_start = (current_time - state.started_at).total_seconds()
                metrics.append(MetricValue(
                    name="container_time_since_start_seconds",
                    value=time_since_start,
                    timestamp=current_time,
                    labels={
                        "container_id": container_id,
                        "container_name": state.container_name
                    }
                ))
        
        # Global metrics
        total_containers = len(self.container_states)
        running_containers = sum(1 for state in self.container_states.values() if state.is_running)
        
        metrics.extend([
            MetricValue(
                name="containers_total",
                value=total_containers,
                timestamp=current_time,
                labels={}
            ),
            MetricValue(
                name="containers_running",
                value=running_containers,
                timestamp=current_time,
                labels={}
            ),
            MetricValue(
                name="containers_stopped",
                value=total_containers - running_containers,
                timestamp=current_time,
                labels={}
            )
        ])
        
        return metrics
    
    def record_event(self, event: ContainerLifecycleEvent) -> None:
        """Record a container lifecycle event and update container state."""
        self.logger.info(f"Recording lifecycle event: {event.event_type.value} for {event.container_name}")
        
        # Add to event history
        self.event_history.append(event)
        
        # Trim history if it gets too large
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Update container state
        container_id = event.container_id
        if container_id not in self.container_states:
            self.container_states[container_id] = ContainerState(
                container_id=container_id,
                container_name=event.container_name
            )\n        \n        state = self.container_states[container_id]\n        state.last_event = event\n        \n        # Handle different event types\n        if event.event_type == ContainerEvent.STARTED:\n            self._handle_container_start(state, event)\n        elif event.event_type == ContainerEvent.STOPPED:\n            self._handle_container_stop(state, event)\n        elif event.event_type == ContainerEvent.RESTARTED:\n            self._handle_container_restart(state, event)\n        elif event.event_type in [ContainerEvent.DIED, ContainerEvent.KILLED]:\n            self._handle_container_death(state, event)\n        elif event.event_type == ContainerEvent.PAUSED:\n            self._handle_container_pause(state, event)\n        elif event.event_type == ContainerEvent.UNPAUSED:\n            self._handle_container_unpause(state, event)\n    \n    def _handle_container_start(self, state: ContainerState, event: ContainerLifecycleEvent) -> None:\n        \"\"\"Handle container start event.\"\"\"\n        state.is_running = True\n        state.started_at = event.timestamp\n        state.current_uptime_start = event.timestamp\n        \n        # If this is a restart (container was previously stopped)\n        if state.stopped_at is not None:\n            state.restart_count += 1\n    \n    def _handle_container_stop(self, state: ContainerState, event: ContainerLifecycleEvent) -> None:\n        \"\"\"Handle container stop event.\"\"\"\n        state.is_running = False\n        state.stopped_at = event.timestamp\n        \n        # Update total uptime\n        if state.current_uptime_start:\n            session_uptime = event.timestamp - state.current_uptime_start\n            state.total_uptime += session_uptime\n            state.current_uptime_start = None\n        \n        # Record exit code if provided\n        if event.exit_code is not None:\n            state.exit_codes.append(event.exit_code)\n    \n    def _handle_container_restart(self, state: ContainerState, event: ContainerLifecycleEvent) -> None:\n        \"\"\"Handle container restart event.\"\"\"\n        # First handle the implicit stop\n        if state.is_running:\n            self._handle_container_stop(state, event)\n        \n        # Then handle the start\n        state.restart_count += 1\n        self._handle_container_start(state, event)\n    \n    def _handle_container_death(self, state: ContainerState, event: ContainerLifecycleEvent) -> None:\n        \"\"\"Handle container death/kill event.\"\"\"\n        self._handle_container_stop(state, event)\n    \n    def _handle_container_pause(self, state: ContainerState, event: ContainerLifecycleEvent) -> None:\n        \"\"\"Handle container pause event.\"\"\"\n        # Pause doesn't change running status but stops uptime tracking\n        if state.current_uptime_start:\n            session_uptime = event.timestamp - state.current_uptime_start\n            state.total_uptime += session_uptime\n            state.current_uptime_start = None\n    \n    def _handle_container_unpause(self, state: ContainerState, event: ContainerLifecycleEvent) -> None:\n        \"\"\"Handle container unpause event.\"\"\"\n        # Resume uptime tracking\n        if state.is_running:\n            state.current_uptime_start = event.timestamp\n    \n    def get_container_state(self, container_id: str) -> Optional[ContainerState]:\n        \"\"\"Get the current state of a container.\"\"\"\n        return self.container_states.get(container_id)\n    \n    def get_container_events(self, container_id: str = None, \n                           event_type: ContainerEvent = None,\n                           since: datetime = None,\n                           limit: int = None) -> List[ContainerLifecycleEvent]:\n        \"\"\"Get container events with optional filtering.\"\"\"\n        events = self.event_history\n        \n        # Filter by container ID\n        if container_id:\n            events = [e for e in events if e.container_id == container_id]\n        \n        # Filter by event type\n        if event_type:\n            events = [e for e in events if e.event_type == event_type]\n        \n        # Filter by timestamp\n        if since:\n            events = [e for e in events if e.timestamp >= since]\n        \n        # Sort by timestamp (most recent first)\n        events.sort(key=lambda e: e.timestamp, reverse=True)\n        \n        # Apply limit\n        if limit:\n            events = events[:limit]\n        \n        return events\n    \n    def get_restart_statistics(self, container_id: str = None, \n                             since: datetime = None) -> Dict[str, Any]:\n        \"\"\"Get restart statistics for containers.\"\"\"\n        if container_id:\n            containers = {container_id: self.container_states.get(container_id)}\n        else:\n            containers = self.container_states\n        \n        stats = {\n            \"total_containers\": len(containers),\n            \"containers_with_restarts\": 0,\n            \"total_restarts\": 0,\n            \"average_restarts_per_container\": 0.0,\n            \"containers\": {}\n        }\n        \n        for cid, state in containers.items():\n            if state is None:\n                continue\n            \n            # Filter restarts by time if specified\n            restart_count = state.restart_count\n            if since:\n                restart_events = self.get_container_events(\n                    container_id=cid,\n                    event_type=ContainerEvent.RESTARTED,\n                    since=since\n                )\n                restart_count = len(restart_events)\n            \n            stats[\"containers\"][cid] = {\n                \"name\": state.container_name,\n                \"restart_count\": restart_count,\n                \"is_running\": state.is_running,\n                \"total_uptime_seconds\": state.total_uptime.total_seconds()\n            }\n            \n            if restart_count > 0:\n                stats[\"containers_with_restarts\"] += 1\n            \n            stats[\"total_restarts\"] += restart_count\n        \n        if stats[\"total_containers\"] > 0:\n            stats[\"average_restarts_per_container\"] = stats[\"total_restarts\"] / stats[\"total_containers\"]\n        \n        return stats\n    \n    def get_uptime_statistics(self, container_id: str = None) -> Dict[str, Any]:\n        \"\"\"Get uptime statistics for containers.\"\"\"\n        if container_id:\n            containers = {container_id: self.container_states.get(container_id)}\n        else:\n            containers = self.container_states\n        \n        current_time = datetime.now()\n        total_uptime = timedelta(0)\n        running_containers = 0\n        container_stats = {}\n        \n        for cid, state in containers.items():\n            if state is None:\n                continue\n            \n            # Calculate current total uptime\n            uptime = state.total_uptime\n            if state.is_running and state.current_uptime_start:\n                current_session = current_time - state.current_uptime_start\n                uptime += current_session\n            \n            container_stats[cid] = {\n                \"name\": state.container_name,\n                \"uptime_seconds\": uptime.total_seconds(),\n                \"is_running\": state.is_running,\n                \"started_at\": state.started_at.isoformat() if state.started_at else None,\n                \"stopped_at\": state.stopped_at.isoformat() if state.stopped_at else None\n            }\n            \n            total_uptime += uptime\n            if state.is_running:\n                running_containers += 1\n        \n        return {\n            \"total_containers\": len(containers),\n            \"running_containers\": running_containers,\n            \"total_uptime_seconds\": total_uptime.total_seconds(),\n            \"average_uptime_seconds\": total_uptime.total_seconds() / len(containers) if containers else 0,\n            \"containers\": container_stats\n        }\n    \n    async def start_monitoring(self) -> None:\n        \"\"\"Start monitoring container events (if container client is available).\"\"\"\n        if self.container_client is None:\n            self.logger.warning(\"No container client provided, cannot start event monitoring\")\n            return\n        \n        if self._monitoring:\n            self.logger.warning(\"Monitoring already started\")\n            return\n        \n        self._monitoring = True\n        self._monitor_task = asyncio.create_task(self._monitor_events())\n        self.logger.info(\"Started container lifecycle monitoring\")\n    \n    async def stop_monitoring(self) -> None:\n        \"\"\"Stop monitoring container events.\"\"\"\n        if not self._monitoring:\n            return\n        \n        self._monitoring = False\n        if self._monitor_task:\n            self._monitor_task.cancel()\n            try:\n                await self._monitor_task\n            except asyncio.CancelledError:\n                pass\n        \n        self.logger.info(\"Stopped container lifecycle monitoring\")\n    \n    async def _monitor_events(self) -> None:\n        \"\"\"Monitor container events from the container client.\"\"\"\n        try:\n            # This would integrate with Docker/Podman API to listen for events\n            # For now, this is a placeholder that would be implemented based on\n            # the specific container runtime being used\n            while self._monitoring:\n                # In a real implementation, this would:\n                # 1. Listen to container events from Docker/Podman API\n                # 2. Parse events and create ContainerLifecycleEvent objects\n                # 3. Call self.record_event() for each event\n                \n                await asyncio.sleep(1)  # Placeholder polling interval\n                \n        except asyncio.CancelledError:\n            raise\n        except Exception as e:\n            self.logger.error(f\"Error in event monitoring: {str(e)}\")\n            self._monitoring = False\n    \n    def clear_history(self, container_id: str = None, before: datetime = None) -> int:\n        \"\"\"Clear event history with optional filtering.\"\"\"\n        initial_count = len(self.event_history)\n        \n        if container_id and before:\n            self.event_history = [\n                e for e in self.event_history \n                if not (e.container_id == container_id and e.timestamp < before)\n            ]\n        elif container_id:\n            self.event_history = [\n                e for e in self.event_history \n                if e.container_id != container_id\n            ]\n        elif before:\n            self.event_history = [\n                e for e in self.event_history \n                if e.timestamp >= before\n            ]\n        else:\n            self.event_history.clear()\n        \n        cleared_count = initial_count - len(self.event_history)\n        self.logger.info(f\"Cleared {cleared_count} events from history\")\n        return cleared_count\n    \n    def get_name(self) -> str:\n        \"\"\"Get the collector name.\"\"\"\n        return \"container_lifecycle\""