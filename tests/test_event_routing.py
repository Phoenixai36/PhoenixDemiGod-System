"""
Tests for the Event Routing System
"""

import unittest
from datetime import datetime, timedelta
import uuid
from src.phoenixxhydra.core.event_routing import Event, EventPattern, Subscription, DeliveryMode


class TestEvent(unittest.TestCase):
    """Test cases for the Event class"""
    
    def test_event_creation(self):
        """Test creating an event with default values"""
        event = Event(type="test.event", source="test_component")
        
        self.assertIsNotNone(event.id)
        self.assertEqual(event.type, "test.event")
        self.assertEqual(event.source, "test_component")
        self.assertIsInstance(event.timestamp, datetime)
        self.assertIsNone(event.correlation_id)
        self.assertIsNone(event.causation_id)
        self.assertEqual(event.payload, {})
        self.assertEqual(event.metadata, {})
        self.assertFalse(event.is_replay)
    
    def test_event_validation(self):
        """Test event validation during creation"""
        with self.assertRaises(ValueError):
            Event(type="", source="test_component")
        
        with self.assertRaises(ValueError):
            Event(type="test.event", source="")
    
    def test_event_factory_method(self):
        """Test the create factory method"""
        payload = {"key": "value"}
        metadata = {"meta": "data"}
        correlation_id = str(uuid.uuid4())
        causation_id = str(uuid.uuid4())
        
        event = Event.create(
            event_type="test.created",
            source="test_factory",
            payload=payload,
            metadata=metadata,
            correlation_id=correlation_id,
            causation_id=causation_id
        )
        
        self.assertEqual(event.type, "test.created")
        self.assertEqual(event.source, "test_factory")
        self.assertEqual(event.payload, payload)
        self.assertEqual(event.metadata, metadata)
        self.assertEqual(event.correlation_id, correlation_id)
        self.assertEqual(event.causation_id, causation_id)
    
    def test_event_derive(self):
        """Test creating a derived event"""
        original = Event(
            type="test.original",
            source="test_source",
            payload={"original": True},
            metadata={"meta": "original"}
        )
        
        derived = original.derive(
            event_type="test.derived",
            payload={"derived": True}
        )
        
        self.assertEqual(derived.type, "test.derived")
        self.assertEqual(derived.source, original.source)
        self.assertEqual(derived.correlation_id, original.id)
        self.assertEqual(derived.causation_id, original.id)
        self.assertEqual(derived.payload, {"derived": True})
        self.assertEqual(derived.metadata, original.metadata)
    
    def test_event_to_dict(self):
        """Test converting an event to a dictionary"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        correlation_id = str(uuid.uuid4())
        causation_id = str(uuid.uuid4())
        
        event = Event(
            id=event_id,
            type="test.event",
            source="test_component",
            timestamp=timestamp,
            correlation_id=correlation_id,
            causation_id=causation_id,
            payload={"key": "value"},
            metadata={"meta": "data"},
            is_replay=True
        )
        
        event_dict = event.to_dict()
        
        self.assertEqual(event_dict["id"], event_id)
        self.assertEqual(event_dict["type"], "test.event")
        self.assertEqual(event_dict["source"], "test_component")
        self.assertEqual(event_dict["timestamp"], timestamp.isoformat())
        self.assertEqual(event_dict["correlation_id"], correlation_id)
        self.assertEqual(event_dict["causation_id"], causation_id)
        self.assertEqual(event_dict["payload"], {"key": "value"})
        self.assertEqual(event_dict["metadata"], {"meta": "data"})
        self.assertTrue(event_dict["is_replay"])
    
    def test_event_from_dict(self):
        """Test creating an event from a dictionary"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        correlation_id = str(uuid.uuid4())
        causation_id = str(uuid.uuid4())
        
        event_dict = {
            "id": event_id,
            "type": "test.event",
            "source": "test_component",
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "payload": {"key": "value"},
            "metadata": {"meta": "data"},
            "is_replay": True
        }
        
        event = Event.from_dict(event_dict)
        
        self.assertEqual(event.id, event_id)
        self.assertEqual(event.type, "test.event")
        self.assertEqual(event.source, "test_component")
        self.assertEqual(event.timestamp.isoformat(), timestamp.isoformat())
        self.assertEqual(event.correlation_id, correlation_id)
        self.assertEqual(event.causation_id, causation_id)
        self.assertEqual(event.payload, {"key": "value"})
        self.assertEqual(event.metadata, {"meta": "data"})
        self.assertTrue(event.is_replay)


class TestEventPattern(unittest.TestCase):
    """Test cases for the EventPattern class"""
    
    def test_event_pattern_creation(self):
        """Test creating an event pattern"""
        pattern = EventPattern(event_type="test.*")
        
        self.assertEqual(pattern.event_type, "test.*")
        self.assertEqual(pattern.attributes, {})
    
    def test_event_pattern_with_attributes(self):
        """Test creating an event pattern with attributes"""
        attributes = {"priority": 1, "source": "test_component"}
        pattern = EventPattern(event_type="test.event", attributes=attributes)
        
        self.assertEqual(pattern.event_type, "test.event")
        self.assertEqual(pattern.attributes, attributes)
    
    def test_event_pattern_string_representation(self):
        """Test string representation of an event pattern"""
        pattern1 = EventPattern(event_type="test.*")
        self.assertEqual(str(pattern1), "test.*")
        
        pattern2 = EventPattern(event_type="test.event", attributes={"priority": 1})
        self.assertEqual(str(pattern2), "test.event[priority=1]")
    
    def test_event_pattern_equality(self):
        """Test pattern equality"""
        pattern1 = EventPattern(event_type="test.*", attributes={"priority": 1})
        pattern2 = EventPattern(event_type="test.*", attributes={"priority": 1})
        pattern3 = EventPattern(event_type="test.**", attributes={"priority": 1})
        pattern4 = EventPattern(event_type="test.*", attributes={"priority": 2})
        
        self.assertEqual(pattern1, pattern2)
        self.assertNotEqual(pattern1, pattern3)
        self.assertNotEqual(pattern1, pattern4)
        self.assertNotEqual(pattern1, "not_a_pattern")
    
    def test_event_type_matching(self):
        """Test event type pattern matching"""
        # Direct match
        pattern1 = EventPattern(event_type="test.event")
        self.assertTrue(pattern1.matches_event_type("test.event"))
        self.assertFalse(pattern1.matches_event_type("test.other"))
        
        # Wildcard match
        pattern2 = EventPattern(event_type="*")
        self.assertTrue(pattern2.matches_event_type("test.event"))
        self.assertTrue(pattern2.matches_event_type("system.alert"))
        
        # Hierarchical wildcard match
        pattern3 = EventPattern(event_type="test.*")
        self.assertTrue(pattern3.matches_event_type("test.event"))
        self.assertTrue(pattern3.matches_event_type("test.other"))
        self.assertFalse(pattern3.matches_event_type("system.event"))
        
        # Double wildcard match
        pattern4 = EventPattern(event_type="test.**")
        self.assertTrue(pattern4.matches_event_type("test.event"))
        self.assertTrue(pattern4.matches_event_type("test.event.detail"))
        self.assertFalse(pattern4.matches_event_type("system.event"))
    
    def test_attribute_matching(self):
        """Test attribute pattern matching"""
        # Direct value match
        pattern1 = EventPattern(event_type="test.*", attributes={"priority": 1})
        self.assertTrue(pattern1.matches_attributes({"priority": 1}))
        self.assertFalse(pattern1.matches_attributes({"priority": 2}))
        self.assertFalse(pattern1.matches_attributes({"other": 1}))
        
        # Nested attribute match
        pattern2 = EventPattern(event_type="test.*", attributes={"user.id": 123})
        self.assertTrue(pattern2.matches_attributes({"user": {"id": 123}}))
        self.assertFalse(pattern2.matches_attributes({"user": {"id": 456}}))
        self.assertFalse(pattern2.matches_attributes({"user": "not_a_dict"}))
        
        # Operator-based comparison
        pattern3 = EventPattern(event_type="test.*", attributes={
            "priority": {"$gt": 1}
        })
        self.assertTrue(pattern3.matches_attributes({"priority": 2}))
        self.assertFalse(pattern3.matches_attributes({"priority": 1}))
        self.assertFalse(pattern3.matches_attributes({"priority": 0}))
        
        pattern4 = EventPattern(event_type="test.*", attributes={
            "status": {"$in": ["active", "pending"]}
        })
        self.assertTrue(pattern4.matches_attributes({"status": "active"}))
        self.assertTrue(pattern4.matches_attributes({"status": "pending"}))
        self.assertFalse(pattern4.matches_attributes({"status": "inactive"}))
    
    def test_event_matching(self):
        """Test complete event matching"""
        pattern = EventPattern(event_type="test.*", attributes={"priority": 1})
        
        # Matching event
        event1 = Event(
            type="test.event",
            source="test_source",
            payload={"priority": 1}
        )
        self.assertTrue(pattern.matches(event1))
        
        # Non-matching event type
        event2 = Event(
            type="system.event",
            source="test_source",
            payload={"priority": 1}
        )
        self.assertFalse(pattern.matches(event2))
        
        # Non-matching attributes
        event3 = Event(
            type="test.event",
            source="test_source",
            payload={"priority": 2}
        )
        self.assertFalse(pattern.matches(event3))


class TestSubscription(unittest.TestCase):
    """Test cases for the Subscription class"""
    
    def test_subscription_creation(self):
        """Test creating a subscription"""
        pattern = EventPattern(event_type="test.*")
        handler = lambda event: None
        
        subscription = Subscription(pattern=pattern, handler=handler)
        
        self.assertIsNotNone(subscription.id)
        self.assertEqual(subscription.pattern, pattern)
        self.assertEqual(subscription.handler, handler)
        self.assertTrue(subscription.active)
        self.assertEqual(subscription.events_processed, 0)
        self.assertIsNotNone(subscription.created_at)
        self.assertIsNone(subscription.last_event_time)
    
    def test_subscription_validation(self):
        """Test subscription validation"""
        pattern = EventPattern(event_type="test.*")
        
        with self.assertRaises(ValueError):
            Subscription(pattern=pattern, handler=None)
    
    def test_subscription_activation(self):
        """Test activating and deactivating a subscription"""
        subscription = Subscription(handler=lambda event: None)
        
        subscription.deactivate()
        self.assertFalse(subscription.active)
        
        subscription.activate()
        self.assertTrue(subscription.active)
    
    def test_subscription_expiration(self):
        """Test subscription expiration"""
        # Max events expiration
        subscription1 = Subscription(
            handler=lambda event: None,
            max_events=3
        )
        
        self.assertFalse(subscription1.is_expired())
        
        subscription1.events_processed = 2
        self.assertFalse(subscription1.is_expired())
        
        subscription1.events_processed = 3
        self.assertTrue(subscription1.is_expired())
        
        # Time-based expiration
        subscription2 = Subscription(
            handler=lambda event: None,
            expiration=3600  # 1 hour
        )
        
        self.assertFalse(subscription2.is_expired())
        
        # Simulate time passing
        subscription2.created_at = datetime.now().timestamp() - 7200  # 2 hours ago
        self.assertTrue(subscription2.is_expired())
    
    def test_subscription_matching(self):
        """Test subscription matching"""
        subscription = Subscription(
            pattern=EventPattern(event_type="test.*", attributes={"priority": 1}),
            handler=lambda event: None
        )
        
        # Matching event
        event1 = Event(
            type="test.event",
            source="test_source",
            payload={"priority": 1}
        )
        self.assertTrue(subscription.matches(event1))
        
        # Non-matching event
        event2 = Event(
            type="system.event",
            source="test_source",
            payload={"priority": 1}
        )
        self.assertFalse(subscription.matches(event2))
        
        # Inactive subscription
        subscription.deactivate()
        self.assertFalse(subscription.matches(event1))
    
    def test_subscription_process_event(self):
        """Test processing an event through a subscription"""
        processed_events = []
        
        def handler(event):
            processed_events.append(event)
        
        subscription = Subscription(
            pattern=EventPattern(event_type="test.*"),
            handler=handler
        )
        
        event = Event(
            type="test.event",
            source="test_source"
        )
        
        # Process event
        subscription.process_event(event)
        
        self.assertEqual(len(processed_events), 1)
        self.assertEqual(processed_events[0], event)
        self.assertEqual(subscription.events_processed, 1)
        self.assertIsNotNone(subscription.last_event_time)
        
        # Inactive subscription
        subscription.deactivate()
        subscription.process_event(event)
        
        self.assertEqual(len(processed_events), 1)  # No change
        self.assertEqual(subscription.events_processed, 1)  # No change
    
    def test_subscription_to_dict(self):
        """Test converting a subscription to a dictionary"""
        subscription = Subscription(
            pattern=EventPattern(event_type="test.*"),
            handler=lambda event: None,
            max_events=10,
            expiration=3600,
            priority=5
        )
        
        subscription.events_processed = 3
        
        subscription_dict = subscription.to_dict()
        
        self.assertEqual(subscription_dict["id"], subscription.id)
        self.assertEqual(subscription_dict["pattern"], "test.*")
        self.assertTrue(subscription_dict["active"])
        self.assertEqual(subscription_dict["max_events"], 10)
        self.assertEqual(subscription_dict["expiration"], 3600)
        self.assertEqual(subscription_dict["priority"], 5)
        self.assertEqual(subscription_dict["events_processed"], 3)
        self.assertIsNotNone(subscription_dict["created_at"])
        self.assertIsNone(subscription_dict["last_event_time"])


class TestDeliveryMode(unittest.TestCase):
    """Test cases for the DeliveryMode enum"""
    
    def test_delivery_mode_values(self):
        """Test delivery mode values"""
        self.assertEqual(DeliveryMode.SYNC.value, "sync")
        self.assertEqual(DeliveryMode.ASYNC.value, "async")
        self.assertEqual(DeliveryMode.QUEUED.value, "queued")
    
    def test_from_string(self):
        """Test converting strings to delivery modes"""
        self.assertEqual(DeliveryMode.from_string("sync"), DeliveryMode.SYNC)
        self.assertEqual(DeliveryMode.from_string("ASYNC"), DeliveryMode.ASYNC)
        self.assertEqual(DeliveryMode.from_string("Queued"), DeliveryMode.QUEUED)
        
        with self.assertRaises(ValueError):
            DeliveryMode.from_string("invalid")
    
    def test_is_synchronous(self):
        """Test checking if a delivery mode is synchronous"""
        self.assertTrue(DeliveryMode.SYNC.is_synchronous())
        self.assertFalse(DeliveryMode.ASYNC.is_synchronous())
        self.assertFalse(DeliveryMode.QUEUED.is_synchronous())
    
    def test_is_asynchronous(self):
        """Test checking if a delivery mode is asynchronous"""
        self.assertFalse(DeliveryMode.SYNC.is_asynchronous())
        self.assertTrue(DeliveryMode.ASYNC.is_asynchronous())
        self.assertTrue(DeliveryMode.QUEUED.is_asynchronous())


if __name__ == "__main__":
    unittest.main()