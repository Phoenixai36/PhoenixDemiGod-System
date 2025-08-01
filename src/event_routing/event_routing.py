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
from abc import ABC, abstractmethod


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
              payload: Optional[Dict[str, Any]] = None, 
              metadata: Optional[Dict[str, Any]] = None,
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
        matcher = WildcardPatternMatcher()
        return matcher.matches_event_type(event_type, self.event_type)
    
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
    handler: Optional[Callable[['Event'], None]] = None
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
        
        if self.handler:
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

class PatternMatcher(ABC):
    """
    Abstract base class for pattern matching implementations.
    
    This interface defines the contract for pattern matching components
    that evaluate events against subscription patterns.
    """
    
    @abstractmethod
    def matches(self, event: Event, pattern: EventPattern) -> bool:
        """
        Check if an event matches a pattern.
        
        Args:
            event: The event to match
            pattern: The pattern to match against
            
        Returns:
            True if the event matches the pattern, False otherwise
        """
        pass
    
    @abstractmethod
    def find_matching_subscriptions(self, event: Event, subscriptions: List[Subscription]) -> List[Subscription]:
        """
        Find all subscriptions that match an event.
        
        Args:
            event: The event to match
            subscriptions: List of subscriptions to check
            
        Returns:
            List of matching subscriptions
        """
        pass


class DefaultPatternMatcher(PatternMatcher):
    """
    Default implementation of the PatternMatcher interface.
    
    This implementation uses the built-in pattern matching logic
    from EventPattern and Subscription classes.
    """
    
    def matches(self, event: Event, pattern: EventPattern) -> bool:
        """
        Check if an event matches a pattern using the pattern's built-in matching logic.
        
        Args:
            event: The event to match
            pattern: The pattern to match against
            
        Returns:
            True if the event matches the pattern, False otherwise
        """
        return pattern.matches(event)
    
    def find_matching_subscriptions(self, event: Event, subscriptions: List[Subscription]) -> List[Subscription]:
        """
        Find all subscriptions that match an event.
        
        Args:
            event: The event to match
            subscriptions: List of subscriptions to check
            
        Returns:
            List of matching subscriptions sorted by priority (highest first)
        """
        matching_subscriptions = []
        
        for subscription in subscriptions:
            if subscription.matches(event) and not subscription.is_expired():
                matching_subscriptions.append(subscription)
        
        # Sort by priority (highest first), then by creation time (oldest first)
        matching_subscriptions.sort(
            key=lambda s: (-s.priority, s.created_at)
        )
        
        return matching_subscriptions


class CachedPatternMatcher(PatternMatcher):
    """
    Pattern matcher with caching for improved performance.
    
    This implementation caches pattern matching results to avoid
    repeated computation for the same event-pattern combinations.
    """
    
    def __init__(self, cache_size: int = 1000):
        """
        Initialize the cached pattern matcher.
        
        Args:
            cache_size: Maximum number of cache entries to maintain
        """
        self.cache_size = cache_size
        self._cache: Dict[str, bool] = {}
        self._cache_order: List[str] = []
    
    def _get_cache_key(self, event: Event, pattern: EventPattern) -> str:
        """
        Generate a cache key for an event-pattern combination.
        
        Args:
            event: The event
            pattern: The pattern
            
        Returns:
            A string cache key
        """
        return f"{event.type}:{event.source}:{hash(str(pattern))}:{hash(str(event.payload))}"
    
    def _update_cache(self, key: str, result: bool) -> None:
        """
        Update the cache with a new result.
        
        Args:
            key: The cache key
            result: The matching result
        """
        # Remove oldest entries if cache is full
        if len(self._cache) >= self.cache_size:
            oldest_key = self._cache_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = result
        self._cache_order.append(key)
    
    def matches(self, event: Event, pattern: EventPattern) -> bool:
        """
        Check if an event matches a pattern with caching.
        
        Args:
            event: The event to match
            pattern: The pattern to match against
            
        Returns:
            True if the event matches the pattern, False otherwise
        """
        cache_key = self._get_cache_key(event, pattern)
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Compute result and cache it
        result = pattern.matches(event)
        self._update_cache(cache_key, result)
        
        return result
    
    def find_matching_subscriptions(self, event: Event, subscriptions: List[Subscription]) -> List[Subscription]:
        """
        Find all subscriptions that match an event with caching.
        
        Args:
            event: The event to match
            subscriptions: List of subscriptions to check
            
        Returns:
            List of matching subscriptions sorted by priority (highest first)
        """
        matching_subscriptions = []
        
        for subscription in subscriptions:
            if not subscription.active or subscription.is_expired():
                continue
                
            if self.matches(event, subscription.pattern):
                matching_subscriptions.append(subscription)
        
        # Sort by priority (highest first), then by creation time (oldest first)
        matching_subscriptions.sort(
            key=lambda s: (-s.priority, s.created_at)
        )
        
        return matching_subscriptions
    
    def clear_cache(self) -> None:
        """Clear the pattern matching cache."""
        self._cache.clear()
        self._cache_order.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            "cache_utilization": len(self._cache) / self.cache_size if self.cache_size > 0 else 0
        }
class WildcardPatternMatcher(PatternMatcher):
    """
    Pattern matcher specialized in wildcard pattern matching.
    
    This implementation provides optimized matching for wildcard patterns
    and caches compiled regular expressions for improved performance.
    """
    
    def __init__(self):
        """Initialize the wildcard pattern matcher."""
        self._regex_cache: Dict[str, Pattern] = {}
    
    def _compile_pattern(self, pattern_str: str) -> Pattern:
        """
        Compile a wildcard pattern into a regular expression.
        
        Args:
            pattern_str: The wildcard pattern string
            
        Returns:
            A compiled regular expression pattern
        """
        if pattern_str in self._regex_cache:
            return self._regex_cache[pattern_str]

        if pattern_str.startswith("regex:"):
            regex_str = pattern_str[6:]
        elif pattern_str == "*":
            regex_str = ".*"
        else:
            regex_str = re.escape(pattern_str).replace('\\*\\*', '.*').replace('\\*', '[^.]*')
            regex_str = f"^{regex_str}$"

        try:
            regex_pattern = re.compile(regex_str)
            self._regex_cache[pattern_str] = regex_pattern
            return regex_pattern
        except re.error:
            return re.compile(r"^$")
    
    def matches_event_type(self, event_type: str, pattern_str: str) -> bool:
        """
        Check if an event type matches a pattern string.
        
        Args:
            event_type: The event type to match
            pattern_str: The pattern string to match against
            
        Returns:
            True if the event type matches the pattern, False otherwise
        """
        if pattern_str.startswith("!"):
            return not self.matches_event_type(event_type, pattern_str[1:])

        regex_pattern = self._compile_pattern(pattern_str)
        return bool(regex_pattern.match(event_type))
    
    def matches(self, event: Event, pattern: EventPattern) -> bool:
        """
        Check if an event matches a pattern.
        
        Args:
            event: The event to match
            pattern: The pattern to match against
            
        Returns:
            True if the event matches the pattern, False otherwise
        """
        # Check event type match
        if not self.matches_event_type(event.type, pattern.event_type):
            return False
        
        # Check payload attributes match
        if not pattern.matches_attributes(event.payload):
            return False
        
        return True
    
    def find_matching_subscriptions(self, event: Event, subscriptions: List[Subscription]) -> List[Subscription]:
        """
        Find all subscriptions that match an event.
        
        Args:
            event: The event to match
            subscriptions: List of subscriptions to check
            
        Returns:
            List of matching subscriptions sorted by priority (highest first)
        """
        matching_subscriptions = []
        
        for subscription in subscriptions:
            if not subscription.active or subscription.is_expired():
                continue
                
            if self.matches(event, subscription.pattern):
                matching_subscriptions.append(subscription)
        
        # Sort by priority (highest first), then by creation time (oldest first)
        matching_subscriptions.sort(
            key=lambda s: (-s.priority, s.created_at)
        )
        
        return matching_subscriptions
    
    def clear_cache(self) -> None:
        """Clear the regex pattern cache."""
        self._regex_cache.clear()


class EventQueue(ABC):
    """
    Abstract base class for event queue implementations.
    
    This interface defines the contract for event queues that store and
    manage events for asynchronous processing.
    """
    
    @abstractmethod
    def enqueue(self, event: Event) -> None:
        """
        Add an event to the queue.
        
        Args:
            event: The event to add to the queue
        """
        pass
    
    @abstractmethod
    def dequeue(self) -> Optional[Event]:
        """
        Remove and return the next event from the queue.
        
        Returns:
            The next event in the queue, or None if the queue is empty
        """
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if the queue is empty, False otherwise
        """
        pass
    
    @abstractmethod
    def size(self) -> int:
        """
        Get the number of events in the queue.
        
        Returns:
            The number of events in the queue
        """
        pass


class InMemoryEventQueue(EventQueue):
    """
    In-memory implementation of the EventQueue interface.
    
    This implementation uses a simple list to store events in memory.
    """
    
    def __init__(self):
        """Initialize the in-memory event queue."""
        self._queue: List[Event] = []
    
    def enqueue(self, event: Event) -> None:
        """
        Add an event to the queue.
        
        Args:
            event: The event to add to the queue
        """
        self._queue.append(event)
    
    def dequeue(self) -> Optional[Event]:
        """
        Remove and return the next event from the queue.
        
        Returns:
            The next event in the queue, or None if the queue is empty
        """
        if not self.is_empty():
            return self._queue.pop(0)
        return None
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if the queue is empty, False otherwise
        """
        return len(self._queue) == 0
    
    def size(self) -> int:
        """
        Get the number of events in the queue.
        
        Returns:
            The number of events in the queue
        """
        return len(self._queue)


class EventRouter:
    """
    Central event router for the Event Routing System.
    
    This class manages subscriptions and routes events to the appropriate
    subscribers based on event patterns and delivery modes.
    """
    
    def __init__(self, 
                 pattern_matcher: PatternMatcher, 
                 event_queue: Optional[EventQueue] = None):
        """
        Initialize the event router.
        
        Args:
            pattern_matcher: The pattern matcher to use for matching events
            event_queue: The event queue to use for queued delivery
        """
        self.subscriptions: List[Subscription] = []
        self.pattern_matcher = pattern_matcher
        self.event_queue = event_queue
    
    def subscribe(self, 
                  pattern: EventPattern, 
                  handler: Callable[[Event], None], 
                  delivery_mode: DeliveryMode = DeliveryMode.SYNC,
                  priority: int = 0) -> Subscription:
        """
        Create a new subscription.
        
        Args:
            pattern: The event pattern to subscribe to
            handler: The event handler to call for matching events
            delivery_mode: The delivery mode for the subscription
            priority: The priority of the subscription
            
        Returns:
            The new subscription
        """
        subscription = Subscription(
            pattern=pattern,
            handler=handler,
            priority=priority
        )
        self.subscriptions.append(subscription)
        return subscription
    
    def unsubscribe(self, subscription: Subscription) -> None:
        """
        Remove a subscription.
        
        Args:
            subscription: The subscription to remove
        """
        self.subscriptions.remove(subscription)
    
    def publish(self, event: Event, delivery_mode: DeliveryMode = DeliveryMode.SYNC) -> None:
        """
        Publish an event to all matching subscribers.
        
        Args:
            event: The event to publish
            delivery_mode: The delivery mode for the event
        """
        matching_subscriptions = self.pattern_matcher.find_matching_subscriptions(
            event, self.subscriptions
        )
        
        for subscription in matching_subscriptions:
            if delivery_mode == DeliveryMode.SYNC:
                subscription.process_event(event)
            elif delivery_mode == DeliveryMode.ASYNC:
                # In a real implementation, this would use a thread pool or async framework
                subscription.process_event(event)
            elif delivery_mode == DeliveryMode.QUEUED:
                if self.event_queue:
                    self.event_queue.enqueue(event)


class EventPublisher:
    """
    Event publisher for the Event Routing System.
    
    This class provides a simple interface for publishing events to an
    event router.
    """
    
    def __init__(self, router: EventRouter):
        """
        Initialize the event publisher.
        
        Args:
            router: The event router to use for publishing events
        """
        self.router = router
    
    def publish(self, event: Event, delivery_mode: DeliveryMode = DeliveryMode.SYNC) -> None:
        """
        Publish an event.
        
        Args:
            event: The event to publish
            delivery_mode: The delivery mode for the event
        """
        self.router.publish(event, delivery_mode)
