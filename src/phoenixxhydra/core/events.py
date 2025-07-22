"""
Event bus and messaging system for PHOENIXxHYDRA system
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Set, Callable, Optional, Any, Tuple, Union
import json
import time

from .models import SystemEvent, EventType, CommunicationMessage


class EventSubscription:
    """Event subscription details"""
    
    def __init__(self, 
                 subscription_id: str, 
                 event_types: List[EventType], 
                 callback: Callable[[SystemEvent], None],
                 max_events: Optional[int] = None,
                 expiration: Optional[float] = None):
        self.subscription_id = subscription_id
        self.event_types = event_types
        self.callback = callback
        self.max_events = max_events
        self.events_processed = 0
        self.expiration = expiration
        self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if subscription is expired"""
        if self.max_events and self.events_processed >= self.max_events:
            return True
        
        if self.expiration and (time.time() - self.created_at) >= self.expiration:
            return True
        
        return False
    
    def matches_event(self, event: SystemEvent) -> bool:
        """Check if subscription matches event type"""
        return event.event_type in self.event_types
    
    def process_event(self, event: SystemEvent) -> None:
        """Process an event through this subscription"""
        self.callback(event)
        self.events_processed += 1


class EventBus:
    """Central event bus for system-wide events"""
    
    def __init__(self, max_history: int = 1000):
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_history: List[SystemEvent] = []
        self.max_history = max_history
        self.logger = logging.getLogger("EventBus")
        self._lock = asyncio.Lock()
    
    async def publish(self, event: SystemEvent) -> bool:
        """Publish an event to the bus"""
        async with self._lock:
            # Add to history
            self.event_history.append(event)
            
            # Trim history if needed
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
            
            # Process subscriptions
            matched_subscriptions = []
            expired_subscriptions = []
            
            for sub_id, subscription in self.subscriptions.items():
                if subscription.matches_event(event):
                    matched_subscriptions.append(subscription)
                    # Check if subscription will expire after processing this event
                    if subscription.max_events and subscription.events_processed + 1 >= subscription.max_events:
                        expired_subscriptions.append(sub_id)
                elif subscription.is_expired():
                    expired_subscriptions.append(sub_id)
            
            # Process event through matching subscriptions
            for subscription in matched_subscriptions:
                try:
                    subscription.process_event(event)
                except Exception as e:
                    self.logger.error(f"Error processing event {event.event_id} in subscription {subscription.subscription_id}: {e}")
            
            # Remove expired subscriptions
            for sub_id in expired_subscriptions:
                del self.subscriptions[sub_id]
            
            # Process event through matching subscriptions
            for subscription in matched_subscriptions:
                try:
                    subscription.process_event(event)
                except Exception as e:
                    self.logger.error(f"Error processing event {event.event_id} in subscription {subscription.subscription_id}: {e}")
            
            return True
    
    async def subscribe(self, 
                       event_types: List[Union[EventType, str]], 
                       callback: Callable[[SystemEvent], None],
                       max_events: Optional[int] = None,
                       expiration: Optional[float] = None) -> str:
        """Subscribe to specific event types"""
        # Convert string event types to EventType enum
        typed_event_types = []
        for event_type in event_types:
            if isinstance(event_type, str):
                try:
                    typed_event_types.append(EventType(event_type))
                except ValueError:
                    self.logger.warning(f"Invalid event type: {event_type}")
            else:
                typed_event_types.append(event_type)
        
        subscription_id = str(uuid.uuid4())
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_types=typed_event_types,
            callback=callback,
            max_events=max_events,
            expiration=expiration
        )
        
        async with self._lock:
            self.subscriptions[subscription_id] = subscription
        
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        async with self._lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                return True
            return False
    
    async def get_event_history(self, 
                              limit: int = 100, 
                              event_types: Optional[List[EventType]] = None,
                              source_component: Optional[str] = None) -> List[SystemEvent]:
        """Get recent event history with optional filtering"""
        async with self._lock:
            filtered_events = self.event_history
            
            # Filter by event type if specified
            if event_types:
                filtered_events = [e for e in filtered_events if e.event_type in event_types]
            
            # Filter by source component if specified
            if source_component:
                filtered_events = [e for e in filtered_events if e.source_component == source_component]
            
            # Return limited number of events
            return filtered_events[-limit:]
    
    async def clear_history(self) -> None:
        """Clear event history"""
        async with self._lock:
            self.event_history = []


class MessageBroker:
    """Message broker for P2P communication"""
    
    def __init__(self, node_id: str, max_queue_size: int = 1000):
        self.node_id = node_id
        self.max_queue_size = max_queue_size
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.message_history: Dict[str, List[CommunicationMessage]] = {}
        self.logger = logging.getLogger("MessageBroker")
        self._lock = asyncio.Lock()
    
    async def send_message(self, message: CommunicationMessage) -> bool:
        """Send a message to a receiver"""
        if not message.sender_id:
            message.sender_id = self.node_id
        
        if not message.message_id:
            message.message_id = str(uuid.uuid4())
        
        if not message.timestamp:
            message.timestamp = datetime.now()
        
        receiver_id = message.receiver_id
        
        async with self._lock:
            # Create queue for receiver if it doesn't exist
            if receiver_id not in self.message_queues:
                self.message_queues[receiver_id] = asyncio.Queue(maxsize=self.max_queue_size)
                self.message_history[receiver_id] = []
            
            # Add to history
            self.message_history[receiver_id].append(message)
            
            # Trim history if needed
            if len(self.message_history[receiver_id]) > self.max_queue_size:
                self.message_history[receiver_id] = self.message_history[receiver_id][-self.max_queue_size:]
                # Ensure we keep the most recent messages (with highest indices)
                self.message_history[receiver_id].sort(key=lambda msg: msg.timestamp)
            
            # Add to queue
            try:
                self.message_queues[receiver_id].put_nowait(message)
                return True
            except asyncio.QueueFull:
                self.logger.warning(f"Message queue full for receiver {receiver_id}")
                return False
    
    async def receive_message(self, receiver_id: str, timeout: Optional[float] = None) -> Optional[CommunicationMessage]:
        """Receive a message for a specific receiver"""
        if receiver_id not in self.message_queues:
            async with self._lock:
                self.message_queues[receiver_id] = asyncio.Queue(maxsize=self.max_queue_size)
                self.message_history[receiver_id] = []
        
        try:
            if timeout is not None:
                return await asyncio.wait_for(self.message_queues[receiver_id].get(), timeout)
            else:
                return await self.message_queues[receiver_id].get()
        except asyncio.TimeoutError:
            return None
    
    async def get_message_history(self, receiver_id: str, limit: int = 100) -> List[CommunicationMessage]:
        """Get message history for a specific receiver"""
        async with self._lock:
            if receiver_id not in self.message_history:
                return []
            
            return self.message_history[receiver_id][-limit:]
    
    async def clear_messages(self, receiver_id: Optional[str] = None) -> None:
        """Clear message history and queues"""
        async with self._lock:
            if receiver_id:
                if receiver_id in self.message_history:
                    self.message_history[receiver_id] = []
                
                if receiver_id in self.message_queues:
                    # Clear the queue
                    while not self.message_queues[receiver_id].empty():
                        try:
                            self.message_queues[receiver_id].get_nowait()
                        except asyncio.QueueEmpty:
                            break
            else:
                # Clear all message history and queues
                self.message_history = {}
                
                for queue_id, queue in self.message_queues.items():
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
    
    async def has_pending_messages(self, receiver_id: str) -> bool:
        """Check if there are pending messages for a receiver"""
        if receiver_id not in self.message_queues:
            return False
        
        return not self.message_queues[receiver_id].empty()


class EventReplay:
    """Event replay system for recovery and testing"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("EventReplay")
    
    async def save_events_to_file(self, file_path: str, events: List[SystemEvent]) -> bool:
        """Save events to a file for later replay"""
        try:
            # Convert events to serializable format
            serialized_events = []
            for event in events:
                event_dict = {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "source_component": event.source_component,
                    "target_component": event.target_component,
                    "data": event.data,
                    "priority": event.priority,
                    "complexity_score": event.complexity_score
                }
                serialized_events.append(event_dict)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(serialized_events, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving events to file {file_path}: {e}")
            return False
    
    async def load_events_from_file(self, file_path: str) -> List[SystemEvent]:
        """Load events from a file"""
        try:
            with open(file_path, 'r') as f:
                serialized_events = json.load(f)
            
            # Convert serialized events back to SystemEvent objects
            events = []
            for event_dict in serialized_events:
                event = SystemEvent(
                    event_id=event_dict["event_id"],
                    event_type=EventType(event_dict["event_type"]),
                    timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                    source_component=event_dict["source_component"],
                    target_component=event_dict["target_component"],
                    data=event_dict["data"],
                    priority=event_dict["priority"],
                    complexity_score=event_dict["complexity_score"]
                )
                events.append(event)
            
            return events
        except Exception as e:
            self.logger.error(f"Error loading events from file {file_path}: {e}")
            return []
    
    async def replay_events(self, 
                          events: List[SystemEvent], 
                          delay: Optional[float] = None,
                          preserve_timing: bool = False) -> Tuple[int, int]:
        """Replay events through the event bus"""
        success_count = 0
        failure_count = 0
        
        if preserve_timing and len(events) >= 2:
            # Calculate time differences between events
            base_time = events[0].timestamp.timestamp()
            time_diffs = []
            
            for i in range(1, len(events)):
                time_diffs.append(events[i].timestamp.timestamp() - events[i-1].timestamp.timestamp())
        
        for i, event in enumerate(events):
            try:
                success = await self.event_bus.publish(event)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Apply delay between events
                if i < len(events) - 1:
                    if preserve_timing and len(events) >= 2:
                        await asyncio.sleep(time_diffs[i])
                    elif delay:
                        await asyncio.sleep(delay)
            
            except Exception as e:
                self.logger.error(f"Error replaying event {event.event_id}: {e}")
                failure_count += 1
        
        return success_count, failure_count