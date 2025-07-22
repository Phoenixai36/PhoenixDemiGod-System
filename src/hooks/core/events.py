"""
Core event system for Agent Hooks automation.

This module provides the event bus and event handling infrastructure
for the Phoenix DemiGod Agent Hooks system.
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from pathlib import Path


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """
    Represents a system event that can trigger agent hooks.
    
    Events are the core communication mechanism between event sources
    and hook executors in the Phoenix DemiGod system.
    """
    
    # Core event properties
    event_type: str
    source: str
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Event management
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: EventPriority = EventPriority.NORMAL
    tags: Set[str] = field(default_factory=set)
    
    # Processing state
    processed: bool = False
    processing_started_at: Optional[float] = None
    processing_completed_at: Optional[float] = None
    processing_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        event_dict = asdict(self)
        event_dict['tags'] = list(self.tags)  # Convert set to list
        event_dict['priority'] = self.priority.value
        return event_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        # Handle special fields
        if 'tags' in data:
            data['tags'] = set(data['tags'])
        if 'priority' in data:
            data['priority'] = EventPriority(data['priority'])
        
        return cls(**data)
    
    def add_tag(self, tag: str):
        """Add a tag to the event."""
        self.tags.add(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if event has a specific tag."""
        return tag in self.tags
    
    def mark_processing_started(self):
        """Mark event as processing started."""
        self.processing_started_at = time.time()
    
    def mark_processing_completed(self):
        """Mark event as processing completed."""
        self.processing_completed_at = time.time()
        self.processed = True
    
    def add_processing_error(self, error: str):
        """Add a processing error to the event."""
        self.processing_errors.append(error)
    
    def get_processing_duration(self) -> Optional[float]:
        """Get the processing duration in seconds."""
        if self.processing_started_at and self.processing_completed_at:
            return self.processing_completed_at - self.processing_started_at
        return None


class EventFilter:
    """Filter for matching events based on criteria."""
    
    def __init__(self, 
                 event_types: Optional[List[str]] = None,
                 sources: Optional[List[str]] = None,
                 tags: Optional[List[str]] = None,
                 priority_min: Optional[EventPriority] = None,
                 custom_filter: Optional[Callable[[Event], bool]] = None):
        self.event_types = set(event_types) if event_types else None
        self.sources = set(sources) if sources else None
        self.tags = set(tags) if tags else None
        self.priority_min = priority_min
        self.custom_filter = custom_filter
    
    def matches(self, event: Event) -> bool:
        """Check if event matches the filter criteria."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check source
        if self.sources and event.source not in self.sources:
            return False
        
        # Check tags
        if self.tags and not self.tags.intersection(event.tags):
            return False
        
        # Check priority
        if self.priority_min and event.priority.value < self.priority_min.value:
            return False
        
        # Check custom filter
        if self.custom_filter and not self.custom_filter(event):
            return False
        
        return True


class EventSubscription:
    """Represents a subscription to events."""
    
    def __init__(self, 
                 callback: Callable[[Event], Any],
                 event_filter: Optional[EventFilter] = None,
                 subscription_id: Optional[str] = None):
        self.callback = callback
        self.event_filter = event_filter or EventFilter()
        self.subscription_id = subscription_id or str(uuid.uuid4())
        self.created_at = time.time()
        self.event_count = 0
        self.last_event_at: Optional[float] = None


class EventBus:
    """
    Asynchronous event bus for the Agent Hooks system.
    
    The event bus handles event distribution, filtering, and persistence
    for the Phoenix DemiGod system. It supports:
    - Asynchronous event processing
    - Event filtering and routing
    - Event persistence and replay
    - Subscription management
    - Backpressure handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self.event_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.get('max_queue_size', 10000)
        )
        self.event_history: List[Event] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        # Subscriptions
        self.subscriptions: Dict[str, EventSubscription] = {}
        
        # Processing state
        self.is_running = False
        self.processor_task: Optional[asyncio.Task] = None
        self.stats = {
            'events_emitted': 0,
            'events_processed': 0,
            'events_failed': 0,
            'subscriptions_active': 0,
        }
        
        # Persistence
        self.enable_persistence = self.config.get('enable_persistence', False)
        self.persistence_path = Path(self.config.get('persistence_path', 'data/events/'))
        
        if self.enable_persistence:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """Start the event bus."""
        if self.is_running:
            return
        
        self.is_running = True
        self.processor_task = asyncio.create_task(self._process_events())
        
        # Load persisted events if enabled
        if self.enable_persistence:
            await self._load_persisted_events()
        
        self.logger.info("Event bus started")
    
    async def stop(self):
        """Stop the event bus."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel processor task
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        # Persist remaining events if enabled
        if self.enable_persistence:
            await self._persist_events()
        
        self.logger.info("Event bus stopped")
    
    async def emit(self, event: Event):
        """Emit an event to the bus."""
        try:
            # Add to queue
            await self.event_queue.put(event)
            self.stats['events_emitted'] += 1
            
            self.logger.debug(f"Event emitted: {event.event_type} from {event.source}")
            
        except asyncio.QueueFull:
            self.logger.error("Event queue is full, dropping event")
            raise
    
    def subscribe(self, 
                  callback: Callable[[Event], Any],
                  event_filter: Optional[EventFilter] = None) -> str:
        """Subscribe to events with optional filtering."""
        subscription = EventSubscription(callback, event_filter)
        self.subscriptions[subscription.subscription_id] = subscription
        self.stats['subscriptions_active'] = len(self.subscriptions)
        
        self.logger.info(f"New subscription created: {subscription.subscription_id}")
        return subscription.subscription_id
    
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            self.stats['subscriptions_active'] = len(self.subscriptions)
            self.logger.info(f"Subscription removed: {subscription_id}")
    
    async def _process_events(self):
        """Main event processing loop."""
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event):
        """Handle a single event by notifying subscribers."""
        event.mark_processing_started()
        
        try:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)
            
            # Notify matching subscribers
            matching_subscriptions = [
                sub for sub in self.subscriptions.values()
                if sub.event_filter.matches(event)
            ]
            
            # Process subscriptions concurrently
            if matching_subscriptions:
                tasks = []
                for subscription in matching_subscriptions:
                    task = asyncio.create_task(
                        self._notify_subscriber(subscription, event)
                    )
                    tasks.append(task)
                
                # Wait for all notifications to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        subscription = matching_subscriptions[i]
                        error_msg = f"Subscription {subscription.subscription_id} failed: {result}"
                        event.add_processing_error(error_msg)
                        self.logger.error(error_msg)
            
            event.mark_processing_completed()
            self.stats['events_processed'] += 1
            
        except Exception as e:
            event.add_processing_error(str(e))
            self.stats['events_failed'] += 1
            self.logger.error(f"Failed to handle event {event.event_id}: {e}")
    
    async def _notify_subscriber(self, subscription: EventSubscription, event: Event):
        """Notify a single subscriber about an event."""
        try:
            # Update subscription stats
            subscription.event_count += 1
            subscription.last_event_at = time.time()
            
            # Call the callback
            if asyncio.iscoroutinefunction(subscription.callback):
                await subscription.callback(event)
            else:
                subscription.callback(event)
                
        except Exception as e:
            self.logger.error(
                f"Subscription {subscription.subscription_id} callback failed: {e}"
            )
            raise
    
    async def _persist_events(self):
        """Persist events to disk."""
        if not self.enable_persistence:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.persistence_path / f"events_{timestamp}.json"
            
            events_data = [event.to_dict() for event in self.event_history]
            
            with open(filename, 'w') as f:
                json.dump(events_data, f, indent=2)
            
            self.logger.info(f"Persisted {len(events_data)} events to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to persist events: {e}")
    
    async def _load_persisted_events(self):
        """Load persisted events from disk."""
        if not self.enable_persistence:
            return
        
        try:
            # Find the most recent events file
            event_files = list(self.persistence_path.glob("events_*.json"))
            if not event_files:
                return
            
            latest_file = max(event_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                events_data = json.load(f)
            
            # Load events into history
            for event_data in events_data:
                event = Event.from_dict(event_data)
                self.event_history.append(event)
            
            self.logger.info(f"Loaded {len(events_data)} events from {latest_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load persisted events: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self.stats,
            'queue_size': self.event_queue.qsize(),
            'history_size': len(self.event_history),
            'is_running': self.is_running,
        }
    
    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get recent events from history."""
        return self.event_history[-limit:]
    
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Event]:
        """Get events of a specific type."""
        matching_events = [
            event for event in self.event_history
            if event.event_type == event_type
        ]
        return matching_events[-limit:]