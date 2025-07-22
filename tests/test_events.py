"""
Unit tests for event bus and messaging system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.phoenixxhydra.core.models import (
    SystemEvent, EventType, CommunicationMessage, TaskResult
)
from src.phoenixxhydra.core.events import (
    EventBus, MessageBroker, EventSubscription, EventReplay
)


class TestEventSubscription:
    """Test EventSubscription class"""
    
    def test_event_subscription_creation(self):
        """Test basic EventSubscription creation"""
        callback = MagicMock()
        subscription = EventSubscription(
            subscription_id="test_sub_1",
            event_types=[EventType.CELL_SPAWN, EventType.CELL_DEATH],
            callback=callback,
            max_events=10,
            expiration=60.0
        )
        
        assert subscription.subscription_id == "test_sub_1"
        assert EventType.CELL_SPAWN in subscription.event_types
        assert EventType.CELL_DEATH in subscription.event_types
        assert subscription.callback == callback
        assert subscription.max_events == 10
        assert subscription.expiration == 60.0
        assert subscription.events_processed == 0
    
    def test_is_expired_by_max_events(self):
        """Test subscription expiration by max events"""
        subscription = EventSubscription(
            subscription_id="test_sub_2",
            event_types=[EventType.SYSTEM_ALERT],
            callback=MagicMock(),
            max_events=5
        )
        
        # Process 4 events
        for _ in range(4):
            subscription.process_event(SystemEvent(event_type=EventType.SYSTEM_ALERT))
        
        # Should not be expired yet
        assert not subscription.is_expired()
        assert subscription.events_processed == 4
        
        # Process one more event to reach max
        subscription.process_event(SystemEvent(event_type=EventType.SYSTEM_ALERT))
        
        # Should be expired now
        assert subscription.is_expired()
        assert subscription.events_processed == 5
    
    def test_is_expired_by_time(self):
        """Test subscription expiration by time"""
        subscription = EventSubscription(
            subscription_id="test_sub_3",
            event_types=[EventType.SYSTEM_ALERT],
            callback=MagicMock(),
            expiration=0.1  # 100ms
        )
        
        # Should not be expired immediately
        assert not subscription.is_expired()
        
        # Wait for expiration
        import time
        time.sleep(0.2)  # 200ms
        
        # Should be expired now
        assert subscription.is_expired()
    
    def test_matches_event(self):
        """Test event type matching"""
        subscription = EventSubscription(
            subscription_id="test_sub_4",
            event_types=[EventType.CELL_SPAWN, EventType.CELL_DEATH],
            callback=MagicMock()
        )
        
        # Should match
        assert subscription.matches_event(SystemEvent(event_type=EventType.CELL_SPAWN))
        assert subscription.matches_event(SystemEvent(event_type=EventType.CELL_DEATH))
        
        # Should not match
        assert not subscription.matches_event(SystemEvent(event_type=EventType.SYSTEM_ALERT))
        assert not subscription.matches_event(SystemEvent(event_type=EventType.NETWORK_PARTITION))
    
    def test_process_event(self):
        """Test event processing"""
        callback = MagicMock()
        subscription = EventSubscription(
            subscription_id="test_sub_5",
            event_types=[EventType.CELL_SPAWN],
            callback=callback
        )
        
        event = SystemEvent(event_type=EventType.CELL_SPAWN)
        subscription.process_event(event)
        
        # Callback should be called with the event
        callback.assert_called_once_with(event)
        
        # Events processed should be incremented
        assert subscription.events_processed == 1


class TestEventBus:
    """Test EventBus class"""
    
    @pytest.fixture
    def event_bus(self):
        """Create an event bus for testing"""
        return EventBus(max_history=5)
    
    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        """Test publishing an event"""
        event = SystemEvent(
            event_type=EventType.CELL_SPAWN,
            source_component="test_component",
            data={"cell_id": "test_cell_1"}
        )
        
        result = await event_bus.publish(event)
        assert result is True
        
        # Event should be in history
        assert len(event_bus.event_history) == 1
        assert event_bus.event_history[0] == event
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus):
        """Test subscribing to events and publishing"""
        callback = AsyncMock()
        
        # Subscribe to CELL_SPAWN events
        subscription_id = await event_bus.subscribe(
            event_types=[EventType.CELL_SPAWN],
            callback=callback
        )
        
        assert subscription_id in event_bus.subscriptions
        
        # Publish a matching event
        event = SystemEvent(event_type=EventType.CELL_SPAWN)
        await event_bus.publish(event)
        
        # Callback should be called
        callback.assert_called_once_with(event)
        
        # Publish a non-matching event
        await event_bus.publish(SystemEvent(event_type=EventType.SYSTEM_ALERT))
        
        # Callback should still be called only once
        assert callback.call_count == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events"""
        callback = AsyncMock()
        
        # Subscribe to events
        subscription_id = await event_bus.subscribe(
            event_types=[EventType.CELL_SPAWN],
            callback=callback
        )
        
        # Unsubscribe
        result = await event_bus.unsubscribe(subscription_id)
        assert result is True
        
        # Subscription should be removed
        assert subscription_id not in event_bus.subscriptions
        
        # Publish an event
        await event_bus.publish(SystemEvent(event_type=EventType.CELL_SPAWN))
        
        # Callback should not be called
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_event_history_limit(self, event_bus):
        """Test event history size limit"""
        # Publish 10 events (max_history is 5)
        for i in range(10):
            await event_bus.publish(
                SystemEvent(
                    event_type=EventType.SYSTEM_ALERT,
                    data={"index": i}
                )
            )
        
        # History should be limited to 5 events
        assert len(event_bus.event_history) == 5
        
        # Only the last 5 events should be in history
        for i in range(5, 10):
            assert any(e.data.get("index") == i for e in event_bus.event_history)
    
    @pytest.mark.asyncio
    async def test_get_event_history(self, event_bus):
        """Test getting event history"""
        # Publish some events
        for i in range(3):
            await event_bus.publish(
                SystemEvent(
                    event_type=EventType.SYSTEM_ALERT if i % 2 == 0 else EventType.CELL_SPAWN,
                    source_component=f"component_{i}",
                    data={"index": i}
                )
            )
        
        # Get all history
        history = await event_bus.get_event_history()
        assert len(history) == 3
        
        # Get limited history
        history = await event_bus.get_event_history(limit=2)
        assert len(history) == 2
        
        # Get filtered history by event type
        history = await event_bus.get_event_history(
            event_types=[EventType.SYSTEM_ALERT]
        )
        assert len(history) == 2
        assert all(e.event_type == EventType.SYSTEM_ALERT for e in history)
        
        # Get filtered history by source component
        history = await event_bus.get_event_history(
            source_component="component_1"
        )
        assert len(history) == 1
        assert history[0].source_component == "component_1"
    
    @pytest.mark.asyncio
    async def test_clear_history(self, event_bus):
        """Test clearing event history"""
        # Publish some events
        for i in range(3):
            await event_bus.publish(SystemEvent(event_type=EventType.SYSTEM_ALERT))
        
        # Clear history
        await event_bus.clear_history()
        
        # History should be empty
        assert len(event_bus.event_history) == 0
    
    @pytest.mark.asyncio
    async def test_expired_subscription_removal(self, event_bus):
        """Test automatic removal of expired subscriptions"""
        # Create a subscription that expires after 1 event
        subscription_id = await event_bus.subscribe(
            event_types=[EventType.CELL_SPAWN],
            callback=AsyncMock(),
            max_events=1
        )
        
        assert subscription_id in event_bus.subscriptions
        
        # Publish a matching event to trigger expiration
        await event_bus.publish(SystemEvent(event_type=EventType.CELL_SPAWN))
        
        # Subscription should be removed
        assert subscription_id not in event_bus.subscriptions


class TestMessageBroker:
    """Test MessageBroker class"""
    
    @pytest.fixture
    def message_broker(self):
        """Create a message broker for testing"""
        return MessageBroker(node_id="test_node", max_queue_size=5)
    
    @pytest.mark.asyncio
    async def test_send_message(self, message_broker):
        """Test sending a message"""
        message = CommunicationMessage(
            sender_id="",  # Should be filled automatically
            receiver_id="receiver_node",
            message_type="test_message",
            payload={"data": "test_data"}
        )
        
        result = await message_broker.send_message(message)
        assert result is True
        
        # Message should have sender_id set
        assert message.sender_id == "test_node"
        
        # Message should be in history
        assert "receiver_node" in message_broker.message_history
        assert len(message_broker.message_history["receiver_node"]) == 1
        assert message_broker.message_history["receiver_node"][0] == message
        
        # Message should be in queue
        assert "receiver_node" in message_broker.message_queues
        assert message_broker.message_queues["receiver_node"].qsize() == 1
    
    @pytest.mark.asyncio
    async def test_receive_message(self, message_broker):
        """Test receiving a message"""
        # Send a message
        message = CommunicationMessage(
            receiver_id="receiver_node",
            payload={"data": "test_data"}
        )
        await message_broker.send_message(message)
        
        # Receive the message
        received_message = await message_broker.receive_message("receiver_node")
        
        assert received_message == message
        
        # Queue should be empty now
        assert message_broker.message_queues["receiver_node"].empty()
    
    @pytest.mark.asyncio
    async def test_receive_message_timeout(self, message_broker):
        """Test receiving a message with timeout"""
        # Try to receive a message with timeout
        received_message = await message_broker.receive_message("nonexistent_node", timeout=0.1)
        
        # Should return None after timeout
        assert received_message is None
    
    @pytest.mark.asyncio
    async def test_get_message_history(self, message_broker):
        """Test getting message history"""
        # Send some messages
        for i in range(3):
            await message_broker.send_message(
                CommunicationMessage(
                    receiver_id="receiver_node",
                    payload={"index": i}
                )
            )
        
        # Get history
        history = await message_broker.get_message_history("receiver_node")
        assert len(history) == 3
        
        # Get limited history
        history = await message_broker.get_message_history("receiver_node", limit=2)
        assert len(history) == 2
        
        # Get history for nonexistent node
        history = await message_broker.get_message_history("nonexistent_node")
        assert len(history) == 0
    
    @pytest.mark.asyncio
    async def test_clear_messages(self, message_broker):
        """Test clearing messages"""
        # Send messages to multiple receivers
        await message_broker.send_message(
            CommunicationMessage(receiver_id="receiver1")
        )
        await message_broker.send_message(
            CommunicationMessage(receiver_id="receiver2")
        )
        
        # Clear messages for one receiver
        await message_broker.clear_messages("receiver1")
        
        # History for receiver1 should be empty
        assert len(message_broker.message_history["receiver1"]) == 0
        assert message_broker.message_queues["receiver1"].empty()
        
        # History for receiver2 should still exist
        assert len(message_broker.message_history["receiver2"]) == 1
        assert not message_broker.message_queues["receiver2"].empty()
        
        # Clear all messages
        await message_broker.clear_messages()
        
        # All histories should be empty
        assert len(message_broker.message_history) == 0
        assert message_broker.message_queues["receiver2"].empty()
    
    @pytest.mark.asyncio
    async def test_has_pending_messages(self, message_broker):
        """Test checking for pending messages"""
        # No messages initially
        assert not await message_broker.has_pending_messages("receiver")
        
        # Send a message
        await message_broker.send_message(
            CommunicationMessage(receiver_id="receiver")
        )
        
        # Should have pending messages now
        assert await message_broker.has_pending_messages("receiver")
        
        # Receive the message
        await message_broker.receive_message("receiver")
        
        # Should not have pending messages anymore
        assert not await message_broker.has_pending_messages("receiver")
    
    @pytest.mark.asyncio
    async def test_message_queue_full(self, message_broker):
        """Test behavior when message queue is full"""
        # Send max_queue_size + 1 messages
        for i in range(6):  # max_queue_size is 5
            result = await message_broker.send_message(
                CommunicationMessage(
                    receiver_id="receiver",
                    payload={"index": i}
                )
            )
            
            # First 5 should succeed, 6th should fail
            if i < 5:
                assert result is True
            else:
                assert result is False
        
        # Queue should have max_queue_size messages
        assert message_broker.message_queues["receiver"].qsize() == 5
        
        # History should have all messages
        assert len(message_broker.message_history["receiver"]) == 5
        
        # History should have the last 5 messages (indices 1-5)
        indices = [msg.payload.get("index") for msg in message_broker.message_history["receiver"]]
        assert set(indices) == set(range(1, 6))


class TestEventReplay:
    """Test EventReplay class"""
    
    @pytest.fixture
    def event_bus(self):
        """Create an event bus for testing"""
        return EventBus()
    
    @pytest.fixture
    def event_replay(self, event_bus):
        """Create an event replay system for testing"""
        return EventReplay(event_bus)
    
    @pytest.mark.asyncio
    async def test_save_and_load_events(self, event_replay, tmp_path):
        """Test saving and loading events to/from file"""
        # Create some events
        events = [
            SystemEvent(
                event_type=EventType.CELL_SPAWN,
                source_component="test_component",
                data={"cell_id": f"cell_{i}"}
            )
            for i in range(3)
        ]
        
        # Save events to file
        file_path = tmp_path / "events.json"
        result = await event_replay.save_events_to_file(str(file_path), events)
        assert result is True
        
        # Load events from file
        loaded_events = await event_replay.load_events_from_file(str(file_path))
        
        # Should have the same number of events
        assert len(loaded_events) == len(events)
        
        # Events should have the same properties
        for i, event in enumerate(loaded_events):
            assert event.event_type == events[i].event_type
            assert event.source_component == events[i].source_component
            assert event.data == events[i].data
    
    @pytest.mark.asyncio
    async def test_replay_events(self, event_replay, event_bus):
        """Test replaying events"""
        # Create a subscription to track replayed events
        callback = AsyncMock()
        await event_bus.subscribe(
            event_types=[EventType.CELL_SPAWN, EventType.CELL_DEATH],
            callback=callback
        )
        
        # Create some events
        events = [
            SystemEvent(event_type=EventType.CELL_SPAWN),
            SystemEvent(event_type=EventType.CELL_DEATH),
            SystemEvent(event_type=EventType.SYSTEM_ALERT)  # Not subscribed
        ]
        
        # Replay events
        success_count, failure_count = await event_replay.replay_events(events)
        
        # All events should be successful
        assert success_count == 3
        assert failure_count == 0
        
        # Callback should be called twice (for CELL_SPAWN and CELL_DEATH)
        assert callback.call_count == 2
        
        # Events should be in history
        assert len(event_bus.event_history) == 3
    
    @pytest.mark.asyncio
    async def test_replay_events_with_delay(self, event_replay, event_bus):
        """Test replaying events with delay"""
        # Create some events
        events = [
            SystemEvent(event_type=EventType.CELL_SPAWN),
            SystemEvent(event_type=EventType.CELL_DEATH)
        ]
        
        # Replay events with delay
        start_time = datetime.now()
        success_count, failure_count = await event_replay.replay_events(
            events, delay=0.1  # 100ms delay
        )
        end_time = datetime.now()
        
        # Should take at least 100ms
        assert (end_time - start_time).total_seconds() >= 0.1
        
        # All events should be successful
        assert success_count == 2
        assert failure_count == 0
    
    @pytest.mark.asyncio
    async def test_replay_events_with_preserve_timing(self, event_replay, event_bus):
        """Test replaying events with preserved timing"""
        # Create some events with different timestamps
        now = datetime.now()
        events = [
            SystemEvent(
                event_type=EventType.CELL_SPAWN,
                timestamp=now
            ),
            SystemEvent(
                event_type=EventType.CELL_DEATH,
                timestamp=now + timedelta(seconds=0.2)  # 200ms later
            )
        ]
        
        # Replay events with preserved timing
        start_time = datetime.now()
        success_count, failure_count = await event_replay.replay_events(
            events, preserve_timing=True
        )
        end_time = datetime.now()
        
        # Should take at least 200ms
        assert (end_time - start_time).total_seconds() >= 0.2
        
        # All events should be successful
        assert success_count == 2
        assert failure_count == 0


if __name__ == "__main__":
    pytest.main([__file__])