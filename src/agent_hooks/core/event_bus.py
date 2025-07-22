"""
Event bus for the Agent Hooks Automation system.

This module implements a central event bus for distributing events to registered
subscribers, with support for filtering, prioritization, and asynchronous processing.
"""

import asyncio
import time
from typing import Dict, Any, List, Set, Callable, Awaitable, Optional, Union
import uuid
from datetime import datetime

from src.agent_hooks.events.models import BaseEvent, EventType, EventSeverity, EventSerializer
from src.agent_hooks.events.router import EventFilter, EventFilterGroup
from src.agent_hooks.utils.logging import get_logger, ExecutionError


# Type alias for event handlers
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class EventSubscription:
    """
    Subscription to events on the event bus.
    
    Represents a registration of an event handler for specific event types
    or matching specific filters.
    """
    
    def __init__(
        self,
        handler: EventHandler,
        event_types: Optional[List[EventType]] = None,
        filter_group: Optional[EventFilterGroup] = None,
        priority: int = 0,
        subscription_id: Optional[str] = None
    ):
        """
        Initialize an event subscription.
        
        Args:
            handler: Async function to call when an event is received
            event_types: List of event types to subscribe to, or None for all
            filter_group: Filter group to apply, or None for no filtering
            priority: Priority of this subscription (higher numbers = higher priority)
            subscription_id: Unique ID for this subscription, or None to generate one
        """
        self.handler = handler
        self.event_types = set(event_types) if event_types else None
        self.filter_group = filter_group
        self.priority = priority
        self.subscription_id = subscription_id or str(uuid.uuid4())
        self.created_at = datetime.now()
    
    def matches_event(self, event: BaseEvent) -> bool:
        """
        Check if this subscription matches an event.
        
        Args:
            event: Event to check
            
        Returns:
            True if the subscription matches the event, False otherwise
        """
        # Check event type
        if self.event_types is not None and event.type not in self.event_types:
            return False
        
        # Check filter group
        if self.filter_group is not None and not self.filter_group.matches(event):
            return False
        
        return True


class EventBus:
    """
    Central event bus for distributing events to subscribers.
    
    The event bus allows components to publish events and subscribe to events
    of interest, with support for filtering, prioritization, and asynchronous
    processing.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize the event bus.
        
        Args:
            max_queue_size: Maximum number of events to queue
        """
        self.logger = get_logger("core.event_bus")
        self.subscriptions: List[EventSubscription] = []
        self.queue: asyncio.Queue[BaseEvent] = asyncio.Queue(maxsize=max_queue_size)
        self.running = False
        self.processing_task: Optional[asyncio.Task] = None
        self.event_counts: Dict[EventType, int] = {event_type: 0 for event_type in EventType}
        self.start_time = datetime.now()
    
    async def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: Event to publish
            
        Raises:
            asyncio.QueueFull: If the event queue is full
        """
        await self.queue.put(event)
        self.event_counts[event.type] = self.event_counts.get(event.type, 0) + 1
        self.logger.debug(
            f"Event published: {event.type.value}",
            {"event_id": event.id, "event_type": event.type.value}
        )
    
    def subscribe(
        self,
        handler: EventHandler,
        event_types: Optional[List[EventType]] = None,
        filter_group: Optional[EventFilterGroup] = None,
        priority: int = 0
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            handler: Async function to call when an event is received
            event_types: List of event types to subscribe to, or None for all
            filter_group: Filter group to apply, or None for no filtering
            priority: Priority of this subscription (higher numbers = higher priority)
            
        Returns:
            Subscription ID
        """
        subscription = EventSubscription(
            handler=handler,
            event_types=event_types,
            filter_group=filter_group,
            priority=priority
        )
        
        self.subscriptions.append(subscription)
        self.subscriptions.sort(key=lambda s: s.priority, reverse=True)
        
        self.logger.info(
            f"Subscription added: {subscription.subscription_id}",
            {
                "subscription_id": subscription.subscription_id,
                "event_types": [et.value for et in event_types] if event_types else "all",
                "priority": priority
            }
        )
        
        return subscription.subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: ID of the subscription to remove
            
        Returns:
            True if the subscription was found and removed, False otherwise
        """
        for i, subscription in enumerate(self.subscriptions):
            if subscription.subscription_id == subscription_id:
                self.subscriptions.pop(i)
                self.logger.info(
                    f"Subscription removed: {subscription_id}",
                    {"subscription_id": subscription_id}
                )
                return True
        
        return False
    
    async def start(self) -> None:
        """
        Start processing events.
        
        This method starts a background task that processes events from the queue
        and distributes them to subscribers.
        """
        if self.running:
            return
        
        self.running = True
        self.processing_task = asyncio.create_task(self._process_events())
        self.logger.info("Event bus started")
    
    async def stop(self) -> None:
        """
        Stop processing events.
        
        This method stops the background task that processes events.
        """
        if not self.running:
            return
        
        self.running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
        
        self.logger.info("Event bus stopped")
    
    async def _process_events(self) -> None:
        """
        Process events from the queue.
        
        This method runs in a background task and processes events from the queue,
        distributing them to subscribers.
        """
        while self.running:
            try:
                event = await self.queue.get()
                
                # Find matching subscriptions
                matching_subscriptions = [
                    subscription for subscription in self.subscriptions
                    if subscription.matches_event(event)
                ]
                
                # Process event with each matching subscription
                if matching_subscriptions:
                    await asyncio.gather(
                        *[self._process_subscription(subscription, event) for subscription in matching_subscriptions]
                    )
                
                self.queue.task_done()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Error processing event: {e}",
                    {"error": str(e)},
                    e
                )
    
    async def _process_subscription(self, subscription: EventSubscription, event: BaseEvent) -> None:
        """
        Process an event with a subscription.
        
        Args:
            subscription: Subscription to process
            event: Event to process
        """
        start_time = time.time()
        
        try:
            await subscription.handler(event)
            
            processing_time = time.time() - start_time
            self.logger.debug(
                f"Event processed: {event.type.value}",
                {
                    "event_id": event.id,
                    "subscription_id": subscription.subscription_id,
                    "processing_time_ms": round(processing_time * 1000, 2)
                }
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"Error in event handler: {e}",
                {
                    "event_id": event.id,
                    "subscription_id": subscription.subscription_id,
                    "processing_time_ms": round(processing_time * 1000, 2)
                },
                e
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the event bus.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "queue_size": self.queue.qsize(),
            "subscription_count": len(self.subscriptions),
            "event_counts": {et.value: count for et, count in self.event_counts.items()},
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "is_running": self.running
        }