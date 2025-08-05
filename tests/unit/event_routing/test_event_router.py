import asyncio
import unittest
from unittest.mock import MagicMock

from src.event_routing.event_router import (
    DeliveryMode,
    Event,
    EventPattern,
    EventRouter,
)


class TestEventRouter(unittest.TestCase):
    def setUp(self):
        self.router = EventRouter()
        # self.logger = logging.getLogger(__name__)

    async def test_subscribe_and_publish_sync(self):
        event_payload = {"key": "value"}
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()

        subscription = self.router.subscribe(pattern, handler_mock)
        self.assertIn(subscription, self.router.subscriptions)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload=event_payload)
        await self.router.publish(event, mode=DeliveryMode.SYNC)

        handler_mock.assert_called_once_with(event)

    async def test_subscribe_and_publish_async(self):
        event_payload = {"key": "value"}
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()

        subscription = self.router.subscribe(pattern, handler_mock)
        self.assertIn(subscription, self.router.subscriptions)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload=event_payload)
        await self.router.publish(event, mode=DeliveryMode.ASYNC)
        handler_mock.assert_called_once_with(event)

    async def test_subscribe_and_publish_sync_handler_failure(self):
        event_payload = {"key": "value"}
        pattern = EventPattern(event_type="test.event")
        handler_mock1 = MagicMock()
        handler_mock2 = MagicMock()

        def side_effect():
            raise RuntimeError("Simulated failure")

        handler_mock1.side_effect = side_effect

        self.router.subscribe(pattern, handler_mock1)
        self.router.subscribe(pattern, handler_mock2)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload=event_payload)
        await self.router.publish(event, mode=DeliveryMode.SYNC)

        handler_mock2.assert_called_once_with(event)

    async def test_unsubscribe(self):
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()

        subscription = self.router.subscribe(pattern, handler_mock)
        self.assertIn(subscription, self.router.subscriptions)

        self.router.unsubscribe(subscription)
        await asyncio.sleep(0.01)  # Allow time for unsubscription to propagate
        self.assertNotIn(subscription, self.router.subscriptions)

    def test_matches_pattern(self):
        event_payload = {"key": "value"}
        pattern = EventPattern(
            event_type="test.event",
            attributes=event_payload)
        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload=event_payload)
        self.assertTrue(self.router.matches_pattern(event, pattern))

        pattern = EventPattern(
            event_type="test.event",
            attributes={"key": "wrong_value"})
        self.assertFalse(self.router.matches_pattern(event, pattern))

        pattern = EventPattern(
            event_type="wrong.event",
            attributes=event_payload,
        )
        self.assertFalse(self.router.matches_pattern(event, pattern))

    def test_matches_pattern_wildcard(self):
        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})

        pattern = EventPattern(event_type="*")
        self.assertTrue(self.router.matches_pattern(event, pattern))

        pattern = EventPattern(event_type="test.*")
        self.assertTrue(self.router.matches_pattern(event, pattern))

        pattern = EventPattern(event_type="another.*")
        self.assertFalse(self.router.matches_pattern(event, pattern))

    def test_matches_pattern_attributes(self):
        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value", "another_key": "another_value"})

        pattern = EventPattern(
            event_type="test.event",
            attributes={"key": "value"},
        )
        self.assertTrue(self.router.matches_pattern(event, pattern))

        pattern = EventPattern(
            event_type="test.event",
            attributes={"key": "value",
                        "another_key": "another_value"})
        self.assertTrue(self.router.matches_pattern(event, pattern))

        pattern = EventPattern(
            event_type="test.event",
            attributes={"key": "wrong_value"},
        )
        self.assertFalse(self.router.matches_pattern(event, pattern))

    async def test_handler_raises_exception(self):
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()
        handler_mock.side_effect = ValueError("Intentional exception")

        self.router.subscribe(pattern, handler_mock)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})

        with self.assertLogs(level='ERROR') as cm:
            await self.router.publish(event, mode=DeliveryMode.SYNC)
            self.assertEqual(len(cm.output), 1)
            self.assertIn("Intentional exception", cm.output[0])

        # Check that the exception didn't prevent other handlers from running
        handler_mock.assert_called_once_with(event)

    async def test_no_matching_handlers(self):
        event = Event(
            id="123",
            type="unregistered.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})

        # Publish an event with no matching handlers
        await self.router.publish(event, mode=DeliveryMode.SYNC)

        # Assert that no handlers were called (no exceptions raised)
        self.assertEqual(len(self.router.subscriptions), 0)

    async def test_event_filtering_attributes(self):
        pattern = EventPattern(
            event_type="test.event",
            attributes={"key": "expected_value"})
        handler_mock = MagicMock()

        self.router.subscribe(pattern, handler_mock)

        # Publish an event that matches the attribute filter
        event1 = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "expected_value"})
        await self.router.publish(event1, mode=DeliveryMode.SYNC)
        handler_mock.assert_called_once_with(event1)

        # Reset the mock
        handler_mock.reset_mock()

        # Publish an event that does not match the attribute filter
        event2 = Event(
            id="456",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "wrong_value"})
        await self.router.publish(event2, mode=DeliveryMode.SYNC)
        handler_mock.assert_not_called()

    async def test_multiple_handlers_for_event(self):
        pattern = EventPattern(event_type="test.event")
        handler_mock1 = MagicMock()
        handler_mock2 = MagicMock()

        self.router.subscribe(pattern, handler_mock1)
        self.router.subscribe(pattern, handler_mock2)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})
        await self.router.publish(event, mode=DeliveryMode.SYNC)

        handler_mock1.assert_called_once_with(event)
        handler_mock2.assert_called_once_with(event)

    async def test_unsubscribe_handler(self):
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()

        subscription = self.router.subscribe(pattern, handler_mock)
        self.assertIn(subscription, self.router.subscriptions)

        self.router.unsubscribe(subscription)
        await asyncio.sleep(0.01)
        self.assertNotIn(subscription, self.router.subscriptions)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})
        await self.router.publish(event, mode=DeliveryMode.SYNC)

        handler_mock.assert_not_called()

    async def test_wildcard_event_type(self):
        handler_mock = MagicMock()
        self.router.subscribe(
            EventPattern(event_type="org.example.*"), handler_mock)

        event1 = Event(
            id="1", type="org.example.event1", source="test", timestamp=1.0)
        event2 = Event(
            id="2", type="org.example.event2", source="test", timestamp=1.0)
        event3 = Event(
            id="3", type="com.example.event3", source="test", timestamp=1.0)

        await self.router.publish(event1, mode=DeliveryMode.SYNC)
        await self.router.publish(event2, mode=DeliveryMode.SYNC)
        await self.router.publish(event3, mode=DeliveryMode.SYNC)

        self.assertEqual(handler_mock.call_count, 2)
        handler_mock.assert_called_with(event2)

    async def test_delivery_mode_sync(self):
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()

        self.router.subscribe(pattern, handler_mock)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})
        await self.router.publish(event, mode=DeliveryMode.SYNC)

        handler_mock.assert_called_once_with(event)

    async def test_delivery_mode_async(self):
        pattern = EventPattern(event_type="test.event")
        handler_mock = MagicMock()

        self.router.subscribe(pattern, handler_mock)

        event = Event(
            id="123",
            type="test.event",
            source="test",
            timestamp=1.0,
            payload={"key": "value"})
        await self.router.publish(event, mode=DeliveryMode.ASYNC)

        handler_mock.assert_called_once_with(event)


if __name__ == "__main__":
    unittest.main()
