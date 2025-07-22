"""
Event subscription implementation for the Agent Hooks Enhancement system.

This module implements event subscriptions, which represent handlers that are
called when matching events are received.
"""

import asyncio
import uuid
from typing import Callable, Awaitable, Optional, Union

from src.agent_hooks.events.models import BaseEvent
from src.agent_hooks.events.components.filters import EventFilter, EventFilterGroup


class EventSubscription:
    """
    Subscription to events with filtering and handling.
    
    This class represents a subscription to events that match specific filters,
    with a handler function to be called when matching events are received.
    """
    
    def __init__(
        self,
        handler: Callable[[BaseEvent], Awaitable[None]],
        filters: Optional[Union[EventFilter, EventFilterGroup]] = None,
        id: Optional[str] = None,
        priority: int = 0,
        max_concurrent: int = 1
    ):
        """
        Initialize an event subscription.
        
        Args:
            handler: Async function to call when matching events are received
            filters: Filters to apply to events
            id: Unique identifier for this subscription
            priority: Priority of this subscription (higher values = higher priority)
            max_concurrent: Maximum number of concurrent handler executions
        """
        self.handler = handler
        self.filters = filters
        self.id = id or str(uuid.uuid4())
        self.priority = priority
        self.max_concurrent = max_concurrent
        self.active_count = 0
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    def matches(self, event: BaseEvent) -> bool:
        """
        Check if an event matches this subscription's filters.
        
        Args:
            event: Event to check
            
        Returns:
            True if the event matches, False otherwise
        """
        if self.filters is None:
            return True
        
        return self.filters.matches(event)
    
    async def handle(self, event: BaseEvent) -> None:
        """
        Handle an event by calling the handler function.
        
        Args:
            event: Event to handle
        """
        async with self.semaphore:
            self.active_count += 1
            try:
                await self.handler(event)
            finally:
                self.active_count -= 1
