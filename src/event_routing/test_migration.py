#!/usr/bin/env python3
"""
Test script to verify the migrated event routing system works correctly.

This script tests the basic functionality of the migrated event routing
components to ensure the migration was successful.
"""

import sys
import traceback
from datetime import datetime


def test_event_routing_migration():
    """Test the migrated event routing system."""
    
    print("🔄 Testing Event Routing Migration...")
    
    try:
        # Test imports
        print("  ✓ Testing imports...")
        from src.event_routing import (
            DefaultPatternMatcher,
            DeliveryMode,
            Event,
            EventPattern,
            EventRouter,
            InMemoryEventQueue,
            Subscription,
            WildcardPatternMatcher,
        )
        print("    ✅ All imports successful")
        
        # Test Event creation
        print("  ✓ Testing Event creation...")
        event = Event.create(
            event_type="test.migration",
            source="migration_test",
            payload={"message": "Hello Phoenix Hydra!"}
        )
        assert event.type == "test.migration"
        assert event.source == "migration_test"
        assert event.payload["message"] == "Hello Phoenix Hydra!"
        print("    ✅ Event creation works")
        
        # Test EventPattern
        print("  ✓ Testing EventPattern...")
        pattern = EventPattern("test.*")
        assert pattern.matches(event) == True
        print("    ✅ EventPattern matching works")
        
        # Test EventRouter
        print("  ✓ Testing EventRouter...")
        router = EventRouter()
        
        # Create a test handler
        received_events = []
        def test_handler(event):
            received_events.append(event)
        
        # Subscribe to events
        subscription = router.subscribe(
            pattern=EventPattern("test.*"),
            handler=test_handler
        )
        
        # Publish an event
        router.publish(event)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].type == "test.migration"
        print("    ✅ EventRouter pub/sub works")
        
        # Test pattern matching
        print("  ✓ Testing pattern matching...")
        matcher = WildcardPatternMatcher()
        assert matcher.matches_event_type("test.migration", "test.*") == True
        assert matcher.matches_event_type("other.event", "test.*") == False
        print("    ✅ Pattern matching works")
        
        # Test event queue
        print("  ✓ Testing event queue...")
        queue = InMemoryEventQueue()
        queue.enqueue(event)
        assert queue.size() == 1
        dequeued_event = queue.dequeue()
        assert dequeued_event.type == "test.migration"
        assert queue.is_empty() == True
        print("    ✅ Event queue works")
        
        # Test event store
        print("  ✓ Testing event store...")
        from src.event_routing import InMemoryEventStore, RetentionPolicy
        
        store = InMemoryEventStore()
        store.store(event)
        
        # Test retrieval
        retrieved = store.get_event_by_id(event.id)
        assert retrieved is not None
        assert retrieved.type == "test.migration"
        
        # Test filtering
        filtered = store.get_events(filter_criteria={"type": "test.migration"})
        assert len(filtered) == 1
        
        # Test retention
        policy = RetentionPolicy(max_count=1)
        store.cleanup_expired_events(policy)
        assert store.get_event_count() == 1
        
        print("    ✅ Event store works")
        
        # Test event correlator
        print("  ✓ Testing event correlator...")
        from src.event_routing import EventCorrelator
        
        correlator = EventCorrelator(router, store, auto_correlate=False)
        
        # Test manual correlation
        correlation_id = correlator.correlate(event)
        assert correlation_id is not None
        
        # Test correlation chain retrieval
        chain = correlator.get_correlation_chain(correlation_id)
        assert len(chain) == 1
        assert chain[0].id == event.id
        
        correlator.stop()
        print("    ✅ Event correlator works")
        
        print("\n🎉 Event Routing Migration Test: ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Event Routing Migration Test FAILED: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_event_routing_migration()
    sys.exit(0 if success else 1)