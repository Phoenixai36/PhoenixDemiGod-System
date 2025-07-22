"""
Event Routing System for PHOENIXxHYDRA

This module implements the core components of the Event Routing System,
providing a flexible, scalable mechanism for routing events from publishers
to subscribers based on event types and patterns.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Pattern, Callable


class DeliveryMode(Enum):
    """
    Event delivery modes for controlling how events are delivered to subscribers.
    
    Modes:
        SYNC: Synchronous delivery - The publisher waits for all subscribers to process the event
              before continuing. Errors in subscribers will be propagated to the publisher.
              
        ASYNC: Asynchronous delivery - The publisher does not wait for subscribers to process the event.
               Subscribers process the event in the background. Errors in subscribers will not affect
               the publisher.
               
        QUEUED: Queued delivery - The event is placed in a queue for later processing. Subscribers
                will process the event when they are ready. This mode is useful for high-throughput
                scenarios or when subscribers might be temporarily unavailable.
    """
    SYNC = "sync"
    ASYNC = "async"
    QUEUED = "queued"
    
    @classmethod
    def from_string(cls, mode_str: str) -> 'DeliveryMode':
        """
        Convert a string to a DeliveryMode.
        
        Args:
            mode_str: String representation of the delivery mode
            
        Returns:
            The corresponding DeliveryMode
            
        Raises:
            ValueError: If the string does not match any DeliveryMode
        """
        try:
            return cls(mode_str.lower())
        except ValueError:
            valid_modes = ", ".join([mode.value for mode in cls])
            raise ValueError(f"Invalid delivery mode: {mode_str}. Valid modes are: {valid_modes}")
    
    def is_synchronous(self) -> bool:
        """
        Check if this is a synchronous delivery mode.
        
        Returns:
            True if this is a synchronous delivery mode, False otherwise
        """
        return self == DeliveryMode.SYNC
    
    def is_asynchronous(self) -> bool:
        """
        Check if this is an asynchronous delivery mode.
        
        Returns:
            True if this is an asynchronous delivery mode, False otherwise
        """
        return self in [DeliveryMode.ASYNC, DeliveryMode.QUEUED]


@dataclass
class Event:
    """
    Core event data structure for the Event Routing System.
    
    Attributes:
        id: Unique identifier for the event
        type: Event type (used for routing)
        source: Component that generated the event
        timestamp: When the event was created
        correlation_id: ID linking related events
        causation_id: ID of the event that caused this event
        payload: Event data
        metadata: Additional context information
        is_replay: Whether this is a replayed event
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_replay: bool = False
    
    def __post_init__(self):
        """Validate and initialize the event after creation"""
        if not self.type:
            raise ValueError("Event type cannot be empty")
        if not self.source:
            raise ValueError("Event source cannot be empty")
    
    @classmethod
    def create(cls, 
              event_type: str, 
              source: str, 
              payload: Dict[str, Any] = None, 
              metadata: Dict[str, Any] = None,
              correlation_id: Optional[str] = None,
              causation_id: Optional[str] = None) -> 'Event':
        """
        Factory method to create a new event with default values.
        
        Args:
            event_type: Type of the event
            source: Component that generated the event
            payload: Event data
            metadata: Additional context information
            correlation_id: ID linking related events
            causation_id: ID of the event that caused this event
            
        Returns:
            A new Event instance
        """
        return cls(
            type=event_type,
            source=source,
            payload=payload or {},
            metadata=metadata or {},
            correlation_id=correlation_id,
            causation_id=causation_id
        )
    
    def derive(self, 
              event_type: str, 
              source: Optional[str] = None, 
              payload: Optional[Dict[str, Any]] = None) -> 'Event':
        """
        Create a derived event that maintains the correlation chain.
        
        Args:
            event_type: Type of the derived event
            source: Source of the derived event (defaults to original source)
            payload: Payload for the derived event
            
        Returns:
            A new Event instance with correlation to this event
        """
        return Event(
            type=event_type,
            source=source or self.source,
            correlation_id=self.correlation_id or self.id,
            causation_id=self.id,
            payload=payload or {},
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "payload": self.payload,
            "metadata": self.metadata,
            "is_replay": self.is_replay
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """
        Create an event from a dictionary representation.
        
        Args:
            data: Dictionary representation of the event
            
        Returns:
            An Event instance
        """
        event_data = data.copy()
        if isinstance(event_data.get("timestamp"), str):
            event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
        
        return cls(**event_data)


@dataclass
class EventPattern:
    """
    Pattern for matching events in subscriptions.
    
    Attributes:
        event_type: Event type pattern (can include wildcards)
        attributes: Attribute filters for matching events
    """
    event_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the pattern"""
        if self.attributes:
            attrs = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
            return f"{self.event_type}[{attrs}]"
        return self.event_type
    
    def __eq__(self, other):
        """Check if two patterns are equal"""
        if not isinstance(other, EventPattern):
            return False
        return (self.event_type == other.event_type and 
                self.attributes == other.attributes)
    
    def matches_event_type(self, event_type: str) -> bool:
        """
        Check if the pattern matches an event type.
        
        Args:
            event_type: The event type to match against
            
        Returns:
            True if the pattern matches the event type, False otherwise
        """
        # Direct match
        if self.event_type == event_type:
            return True
        
        # Wildcard match
        if self.event_type == "*":
            return True
        
        # Hierarchical wildcard match (e.g., "system.*" matches "system.alert")
        if self.event_type.endswith(".*"):
            prefix = self.event_type[:-1]  # Remove the "*"
            return event_type.startswith(prefix)
        
        # Double wildcard match (e.g., "system.**" matches "system.alert.critical")
        if self.event_type.endswith(".**"):
            prefix = self.event_type[:-2]  # Remove the "**"
            return event_type.startswith(prefix)
        
        return False
    
    def matches_attributes(self, event_attributes: Dict[str, Any]) -> bool:
        """
        Check if the pattern matches event attributes.
        
        Args:
            event_attributes: The event attributes to match against
            
        Returns:
            True if the pattern matches the attributes, False otherwise
        """
        if not self.attributes:
            return True
        
        for key, pattern_value in self.attributes.items():
            # Handle nested attributes using dot notation (e.g., "user.id")
            if "." in key:
                parts = key.split(".")
                current = event_attributes
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        return False
                    current = current[part]
                
                last_part = parts[-1]
                if last_part not in current:
                    return False
                
                actual_value = current[last_part]
            else:
                if key not in event_attributes:
                    return False
                actual_value = event_attributes[key]
            
            # Handle different types of pattern values
            if isinstance(pattern_value, dict) and any(k.startswith("$") for k in pattern_value.keys()):
                # Operator-based comparison
                for op, op_value in pattern_value.items():
                    if op == "$eq":
                        if actual_value != op_value:
                            return False
                    elif op == "$ne":
                        if actual_value == op_value:
                            return False
                    elif op == "$gt":
                        if not (isinstance(actual_value, (int, float)) and actual_value > op_value):
                            return False
                    elif op == "$gte":
                        if not (isinstance(actual_value, (int, float)) and actual_value >= op_value):
                            return False
                    elif op == "$lt":
                        if not (isinstance(actual_value, (int, float)) and actual_value < op_value):
                            return False
                    elif op == "$lte":
                        if not (isinstance(actual_value, (int, float)) and actual_value <= op_value):
                            return False
                    elif op == "$in":
                        if actual_value not in op_value:
                            return False
                    elif op == "$nin":
                        if actual_value in op_value:
                            return False
                    elif op == "$exists":
                        # This is handled by the key check above
                        pass
            else:
                # Direct value comparison
                if actual_value != pattern_value:
                    return False
        
        return True
    
    def matches(self, event: 'Event') -> bool:
        """
        Check if the pattern matches an event.
        
        Args:
            event: The event to match against
            
        Returns:
            True if the pattern matches the event, False otherwise
        """
        # Check event type match
        if not self.matches_event_type(event.type):
            return False
        
        # Check payload attributes match
        if not self.matches_attributes(event.payload):
            return False
        
        return True


@dataclass
class Subscription:
    """
    Represents a subscription to events.
    
    Attributes:
        id: Unique identifier for the subscription
        pattern: Pattern for matching events
        handler: Function to handle matching events
        active: Whether the subscription is active
        max_events: Maximum number of events to process before expiring
        expiration: Time in seconds after which the subscription expires
        priority: Priority of the subscription (higher values = higher priority)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern: EventPattern = field(default_factory=lambda: EventPattern("*"))
    handler: Callable[['Event'], None] = None
    active: bool = True
    max_events: Optional[int] = None
    expiration: Optional[float] = None
    priority: int = 0
    
    # Runtime state (not part of initialization)
    events_processed: int = field(default=0, init=False)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp(), init=False)
    last_event_time: Optional[float] = field(default=None, init=False)
    
    def __post_init__(self):
        """Validate the subscription after creation"""
        if self.handler is None:
            raise ValueError("Subscription handler cannot be None")
    
    def activate(self) -> None:
        """Activate the subscription"""
        self.active = True
    
    def deactivate(self) -> None:
        """Deactivate the subscription"""
        self.active = False
    
    def is_expired(self) -> bool:
        """
        Check if the subscription has expired.
        
        Returns:
            True if the subscription has expired, False otherwise
        """
        # Check max events
        if self.max_events is not None and self.events_processed >= self.max_events:
            return True
        
        # Check expiration time
        if self.expiration is not None:
            current_time = datetime.now().timestamp()
            if current_time - self.created_at >= self.expiration:
                return True
        
        return False
    
    def matches(self, event: 'Event') -> bool:
        """
        Check if the subscription matches an event.
        
        Args:
            event: The event to check
            
        Returns:
            True if the subscription matches the event, False otherwise
        """
        return self.active and self.pattern.matches(event)
    
    def process_event(self, event: 'Event') -> None:
        """
        Process an event through this subscription.
        
        Args:
            event: The event to process
        """
        if not self.active:
            return
        
        self.handler(event)
        self.events_processed += 1
        self.last_event_time = datetime.now().timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the subscription to a dictionary representation.
        
        Returns:
            Dictionary representation of the subscription
        """
        return {
            "id": self.id,
            "pattern": str(self.pattern),
            "active": self.active,
            "max_events": self.max_events,
            "expiration": self.expiration,
            "priority": self.priority,
            "events_processed": self.events_processed,
            "created_at": self.created_at,
            "last_event_time": self.last_event_time
        }