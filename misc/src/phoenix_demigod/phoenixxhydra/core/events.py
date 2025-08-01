"""
Event system for PHOENIXxHYDRA system.

Provides event-driven communication between Phoenix Core, HYDRA heads, 
cells, and orchestrating agents.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from phoenix_demigod.core.interfaces import Message
from phoenix_demigod.utils.logging import get_logger


class EventType(Enum):
    """Types of system events in PHOENIXxHYDRA."""
    
    # System lifecycle events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    
    # Cell lifecycle events
    CELL_SPAWN = "cell_spawn"
    CELL_DEATH = "cell_death"
    CELL_REGENERATION = "cell_regeneration"
    CELL_EVOLUTION = "cell_evolution"
    CELL_COMMUNICATION = "cell_communication"
    
    # HYDRA head events
    HEAD_ACTIVATION = "head_activation"
    HEAD_DEACTIVATION = "head_deactivation"
    HEAD_COORDINATION = "head_coordination"
    HEAD_TASK_ASSIGNMENT = "head_task_assignment"
    HEAD_TASK_COMPLETION = "head_task_completion"
    
    # Network events
    NETWORK_PARTITION = "network_partition"
    NETWORK_HEALING = "network_healing"
    MESH_REORGANIZATION = "mesh_reorganization"
    P2P_CONNECTION = "p2p_connection"
    P2P_DISCONNECTION = "p2p_disconnection"
    
    # Evolutionary events
    GENETIC_MUTATION = "genetic_mutation"
    NATURAL_SELECTION = "natural_selection"
    FITNESS_EVALUATION = "fitness_evaluation"
    POPULATION_EVOLUTION = "population_evolution"
    
    # Agent events
    CHAOS_SCENARIO = "chaos_scenario"
    DEBATE_ARENA = "debate_arena"
    ECONOMIC_TRANSACTION = "economic_transaction"
    ORCHESTRATION_PLAN = "orchestration_plan"
    
    # External integration events
    DEPLOYMENT_REQUEST = "deployment_request"
    WORKFLOW_TRIGGER = "workflow_trigger"
    MONITORING_ALERT = "monitoring_alert"
    API_REQUEST = "api_request"


@dataclass
class SystemEvent:
    """
    Represents an event in the PHOENIXxHYDRA system.
    
    Extends the base Message class with system-specific functionality.
    """
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_HEALTH_CHECK
    source_component: str = ""
    target_components: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # 0=low, 5=normal, 10=high
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    requires_response: bool = False
    ttl_seconds: int = 3600
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_message(self) -> Message:
        """Convert SystemEvent to base Message for compatibility."""
        return Message(
            message_type=self.event_type.value,
            payload={
                "event_id": self.event_id,
                "source_component": self.source_component,
                "payload": self.payload,
                "correlation_id": self.correlation_id,
                "requires_response": self.requires_response,
                "metadata": self.metadata
            },
            sender=self.source_component,
            recipients=self.target_components,
            priority=self.priority,
            ttl=self.ttl_seconds
        )
    
    @classmethod
    def from_message(cls, message: Message) -> 'SystemEvent':
        """Create SystemEvent from base Message."""
        payload = message.payload
        return cls(
            event_id=payload.get("event_id", str(uuid.uuid4())),
            event_type=EventType(message.message_type),
            source_component=message.sender,
            target_components=message.recipients,
            payload=payload.get("payload", {}),
            priority=message.priority,
            timestamp=message.timestamp,
            correlation_id=payload.get("correlation_id"),
            requires_response=payload.get("requires_response", False),
            ttl_seconds=message.ttl,
            metadata=payload.get("metadata", {})
        )


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    async def handle_event(self, event: SystemEvent) -> Optional[SystemEvent]:
        """
        Handle a system event.
        
        Args:
            event: The event to handle
            
        Returns:
            Optional response event
        """
        pass
    
    @abstractmethod
    def get_supported_events(self) -> Set[EventType]:
        """Get the set of event types this handler supports."""
        pass


class EventBus:
    """
    Central event bus for PHOENIXxHYDRA system.
    
    Manages event routing, handler registration, and event persistence.
    """
    
    def __init__(self):
        self.logger = get_logger("phoenixxhydra.eventbus")
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[SystemEvent] = []
        self._max_history_size = 10000
        self._running = False
        self._event_queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the event bus processor."""
        if self._running:
            return
            
        self.logger.info("Starting PHOENIXxHYDRA event bus")
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        
    async def stop(self):
        """Stop the event bus processor."""
        if not self._running:
            return
            
        self.logger.info("Stopping PHOENIXxHYDRA event bus")
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
                
    def register_handler(self, handler: EventHandler):
        """Register an event handler for specific event types."""
        supported_events = handler.get_supported_events()
        
        for event_type in supported_events:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            
        self.logger.info(
            f"Registered handler {handler.__class__.__name__} for events: "
            f"{[e.value for e in supported_events]}"
        )
        
    def unregister_handler(self, handler: EventHandler):
        """Unregister an event handler."""
        for event_type, handlers in self._handlers.items():
            if handler in handlers:
                handlers.remove(handler)
                
        self.logger.info(f"Unregistered handler {handler.__class__.__name__}")
        
    async def publish_event(self, event: SystemEvent):
        """Publish an event to the bus."""
        if not self._running:
            self.logger.warning("Event bus not running, dropping event")
            return
            
        await self._event_queue.put(event)
        
    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                # Wait for event with timeout to allow graceful shutdown
                event = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=1.0
                )
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing event: {e}", exc_info=True)
                
    async def _handle_event(self, event: SystemEvent):
        """Handle a single event by routing to registered handlers."""
        try:
            # Add to history
            self._add_to_history(event)
            
            # Get handlers for this event type
            handlers = self._handlers.get(event.event_type, [])
            
            if not handlers:
                self.logger.debug(f"No handlers for event type: {event.event_type.value}")
                return
                
            self.logger.debug(
                f"Processing event {event.event_id} of type {event.event_type.value} "
                f"with {len(handlers)} handlers"
            )
            
            # Process handlers concurrently
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(
                    self._safe_handle_event(handler, event)
                )
                tasks.append(task)
                
            # Wait for all handlers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process any response events
            for result in results:
                if isinstance(result, SystemEvent):
                    await self.publish_event(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Handler error: {result}", exc_info=True)
                    
        except Exception as e:
            self.logger.error(f"Error handling event {event.event_id}: {e}", exc_info=True)
            
    async def _safe_handle_event(self, handler: EventHandler, event: SystemEvent) -> Optional[SystemEvent]:
        """Safely handle an event with error handling."""
        try:
            return await handler.handle_event(event)
        except Exception as e:
            self.logger.error(
                f"Handler {handler.__class__.__name__} failed for event "
                f"{event.event_id}: {e}", exc_info=True
            )
            return None
            
    def _add_to_history(self, event: SystemEvent):
        """Add event to history with size management."""
        self._event_history.append(event)
        
        # Trim history if too large
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
            
    def get_event_history(self, 
                         event_type: Optional[EventType] = None,
                         limit: int = 100) -> List[SystemEvent]:
        """Get event history, optionally filtered by type."""
        history = self._event_history
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
            
        return history[-limit:]
        
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        handler_counts = {
            event_type.value: len(handlers) 
            for event_type, handlers in self._handlers.items()
        }
        
        return {
            "running": self._running,
            "total_handlers": sum(len(handlers) for handlers in self._handlers.values()),
            "handler_counts": handler_counts,
            "event_history_size": len(self._event_history),
            "queue_size": self._event_queue.qsize()
        }


class EventFilter:
    """Filter events based on various criteria."""
    
    def __init__(self, 
                 event_types: Optional[Set[EventType]] = None,
                 source_components: Optional[Set[str]] = None,
                 min_priority: int = 0,
                 max_age_seconds: Optional[int] = None):
        self.event_types = event_types
        self.source_components = source_components
        self.min_priority = min_priority
        self.max_age_seconds = max_age_seconds
        
    def matches(self, event: SystemEvent) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
            
        # Check source component
        if self.source_components and event.source_component not in self.source_components:
            return False
            
        # Check priority
        if event.priority < self.min_priority:
            return False
            
        # Check age
        if self.max_age_seconds:
            age = (datetime.now() - event.timestamp).total_seconds()
            if age > self.max_age_seconds:
                return False
                
        return True


class EventCorrelator:
    """Correlate related events for complex event processing."""
    
    def __init__(self):
        self._correlations: Dict[str, List[SystemEvent]] = {}
        
    def add_event(self, event: SystemEvent):
        """Add event to correlation tracking."""
        if event.correlation_id:
            if event.correlation_id not in self._correlations:
                self._correlations[event.correlation_id] = []
            self._correlations[event.correlation_id].append(event)
            
    def get_correlated_events(self, correlation_id: str) -> List[SystemEvent]:
        """Get all events with the same correlation ID."""
        return self._correlations.get(correlation_id, [])
        
    def cleanup_old_correlations(self, max_age_seconds: int = 3600):
        """Remove old correlation data."""
        cutoff_time = datetime.now().timestamp() - max_age_seconds
        
        to_remove = []
        for correlation_id, events in self._correlations.items():
            if all(event.timestamp.timestamp() < cutoff_time for event in events):
                to_remove.append(correlation_id)
                
        for correlation_id in to_remove:
            del self._correlations[correlation_id]