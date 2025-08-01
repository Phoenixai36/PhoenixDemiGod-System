import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class DeliveryMode(Enum):
    SYNC = "sync"  # Synchronous delivery
    ASYNC = "async"  # Asynchronous delivery


@dataclass
class Event:
    id: str
    type: str
    source: str
    timestamp: float
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_replay: bool = False


@dataclass
class EventPattern:
    event_type: str  # Can include wildcards
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    id: str
    pattern: EventPattern
    handler: Callable[[Event], None]
    active: bool = True


class EventRouter:
    def __init__(self):
        self.subscriptions: List[Subscription] = []

    async def publish(
            self,
            event: Event,
            mode: DeliveryMode = DeliveryMode.ASYNC) -> None:
        """Publish an event to all matching subscribers."""
        matching_subscriptions = [
            sub for sub in self.subscriptions if self._matches_pattern(
                event, sub.pattern)]

        if mode == DeliveryMode.ASYNC:
            await self._publish_async(
                event, matching_subscriptions)
        elif mode == DeliveryMode.SYNC:
            await self._publish_sync(event, matching_subscriptions)
        else:
            raise ValueError(f"Unsupported delivery mode: {mode}")

    async def _publish_async(
            self,
            event: Event,
            subscriptions: List[Subscription]):
        """Asynchronously publish an event to multiple subscribers."""
        tasks = [
            self._safe_handler_call(
                event,
                sub.handler) for sub in subscriptions]
        await asyncio.gather(*tasks)

    async def _publish_sync(
        self, event: Event, subscriptions: List[Subscription]
    ):
        """Synchronously publish an event to multiple subscribers."""
        logger = logging.getLogger(__name__)
        for subscription in subscriptions:
            try:
                await self._safe_handler_call(event, subscription.handler)
            except (ValueError, TypeError, AttributeError) as e:
                logger.exception(
                    "Handler failed for subscription %s: %s",
                    subscription.id,
                    e,
                )

    def subscribe(self,
                  pattern: EventPattern,
                  handler: Callable[[Event],
                                    None]) -> Subscription:
        """Subscribe to events matching the given pattern."""
        subscription_id = str(uuid.uuid4())
        subscription = Subscription(
            id=subscription_id,
            pattern=pattern,
            handler=handler)
        self.subscriptions.append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """Remove a subscription."""
        self.subscriptions = [
            sub for sub in self.subscriptions if sub.id == subscription.id]

    def matches_pattern(self, event: Event, pattern: EventPattern) -> bool:
        return EventRouter._matches_pattern(event, pattern)

    @staticmethod
    def _matches_pattern(event: Event, pattern: EventPattern) -> bool:
        """Check if an event matches a pattern."""
        # Implement wildcard and attribute matching
        if pattern.event_type == "*":
            event_type_match = True
        elif "*" in pattern.event_type:
            pattern_regex = pattern.event_type.replace("*", ".*")
            event_type_match = re.match(pattern_regex, event.type) is not None
        else:
            event_type_match = event.type == pattern.event_type

        if not event_type_match:
            return False

        for key, value in pattern.attributes.items():
            if key not in event.payload or event.payload[key] != value:
                return False

        return True

    async def _safe_handler_call(
            self, event: Event, handler: Callable[[Event], None]):
        """Call an event handler and catch any exceptions."""
        logger = logging.getLogger(__name__)
        try:
            handler(event)
        except (ValueError, TypeError, AttributeError) as e:
            logger.exception("Handler failed: %s", e)
