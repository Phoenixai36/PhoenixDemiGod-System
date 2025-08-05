#!/usr/bin/env python3
"""
Test script for Event Store functionality.

This script tests the Event Store implementation to ensure it works correctly
with storage, retrieval, filtering, and retention policies.
"""

import sys
import time
import traceback
from datetime import datetime, timedelta


def test_event_store():
    """Test the Event Store implementation."""
    
    print("🔄 Testing Event Store Implementation...")
    
    try:
        # Test imports
        print("  ✓ Testing imports...")
        from src.event_routing import Event, InMemoryEventStore, RetentionPolicy
        print("    ✅ Event Store imports successful")
        
        # Create event store
        print("  ✓ Testing Event Store creation...")
        store = InMemoryEventStore()
        print("    ✅ Event Store created")
        
        # Create test events
        print("  ✓ Testing event storage...")
        event1 = Event.create(
            event_type="test.event1",
            source="test_source",
            payload={"message": "First event", "priority": 1}
        )
        
        event2 = Event.create(
            event_type="test.event2", 
            source="test_source",
            payload={"message": "Second event", "priority": 2}
        )
        
        event3 = Event.create(
            event_type="other.event",
            source="other_source", 
            payload={"message": "Third event", "priority": 3}
        )
        
        # Store events
        store.store(event1)
        store.store(event2)
        store.store(event3)
        
        assert store.get_event_count() == 3
        print("    ✅ Event storage works")
        
        # Test retrieval by ID
        print("  ✓ Testing event retrieval by ID...")
        retrieved_event = store.get_event_by_id(event1.id)
        assert retrieved_event is not None
        assert retrieved_event.id == event1.id
        assert retrieved_event.type == "test.event1"
        print("    ✅ Event retrieval by ID works")
        
        # Test get all events
        print("  ✓ Testing get all events...")
        all_events = store.get_events()
        assert len(all_events) == 3
        # Events should be in chronological order
        assert all_events[0].timestamp <= all_events[1].timestamp <= all_events[2].timestamp
        print("    ✅ Get all events works")
        
        # Test filtering by type
        print("  ✓ Testing event filtering...")
        test_events = store.get_events(filter_criteria={"type": "test.event1"})
        assert len(test_events) == 1
        assert test_events[0].type == "test.event1"
        
        # Test filtering by source
        test_source_events = store.get_events(filter_criteria={"source": "test_source"})
        assert len(test_source_events) == 2
        
        # Test payload filtering
        priority_events = store.get_events(filter_criteria={"payload.priority": 2})
        assert len(priority_events) == 1
        assert priority_events[0].payload["priority"] == 2
        print("    ✅ Event filtering works")
        
        # Test time-based filtering
        print("  ✓ Testing time-based filtering...")
        now = datetime.now()
        past = now - timedelta(minutes=1)
        future = now + timedelta(minutes=1)
        
        # All events should be between past and future
        time_filtered = store.get_events(start_time=past, end_time=future)
        assert len(time_filtered) == 3
        
        # No events should be in the far future
        future_events = store.get_events(start_time=future)
        assert len(future_events) == 0
        print("    ✅ Time-based filtering works")
        
        # Test limit and offset
        print("  ✓ Testing limit and offset...")
        limited_events = store.get_events(limit=2)
        assert len(limited_events) == 2
        
        offset_events = store.get_events(offset=1, limit=1)
        assert len(offset_events) == 1
        assert offset_events[0].id != all_events[0].id  # Should be different from first
        print("    ✅ Limit and offset work")
        
        # Test retention policy
        print("  ✓ Testing retention policy...")
        
        # Create a retention policy that keeps only 2 events
        retention_policy = RetentionPolicy.create_count_based_policy(2)
        removed_count = store.cleanup_expired_events(retention_policy)
        
        assert removed_count == 1  # Should remove 1 event (oldest)
        assert store.get_event_count() == 2
        
        remaining_events = store.get_events()
        assert len(remaining_events) == 2
        print("    ✅ Retention policy works")
        
        # Test age-based retention
        print("  ✓ Testing age-based retention...")
        
        # Create events with different timestamps
        old_event = Event.create(
            event_type="old.event",
            source="test_source",
            payload={"message": "Old event"}
        )
        # Manually set an old timestamp
        old_event.timestamp = datetime.now() - timedelta(hours=2)
        store.store(old_event)
        
        # Create retention policy that expires events older than 1 hour
        age_retention = RetentionPolicy.create_age_based_policy(1.0)  # 1 hour
        removed_count = store.cleanup_expired_events(age_retention)
        
        assert removed_count == 1  # Should remove the old event
        print("    ✅ Age-based retention works")
        
        # Test advanced querying
        print("  ✓ Testing advanced querying...")
        
        # Add some test events for advanced queries
        test_event_a = Event.create("test.advanced.a", "test_source", {"category": "important"})
        test_event_b = Event.create("test.advanced.b", "test_source", {"category": "normal"})
        store.store(test_event_a)
        store.store(test_event_b)
        
        # Test pattern matching
        pattern_events = store.get_events_by_type_pattern("test.advanced.*")
        assert len(pattern_events) == 2
        
        # Test search
        search_results = store.search_events("important")
        assert len(search_results) >= 1
        
        # Test aggregation
        aggregated = store.aggregate_events("type")
        assert len(aggregated) > 0
        
        print("    ✅ Advanced querying works")
        
        # Test retention statistics
        print("  ✓ Testing retention statistics...")
        retention_policy = RetentionPolicy.create_count_based_policy(5)
        retention_stats = store.get_retention_stats(retention_policy)
        assert "total_events" in retention_stats
        assert "events_to_expire" in retention_stats
        print("    ✅ Retention statistics work")
        
        # Test statistics
        print("  ✓ Testing statistics...")
        stats = store.get_stats()
        assert "total_events" in stats
        assert "event_types" in stats
        assert "sources" in stats
        assert stats["total_events"] > 0
        print("    ✅ Statistics work")
        
        # Test clear
        print("  ✓ Testing clear...")
        cleared_count = store.clear()
        assert cleared_count > 0
        assert store.get_event_count() == 0
        assert len(store.get_events()) == 0
        print("    ✅ Clear works")
        
        print("\n🎉 Event Store Test: ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Event Store Test FAILED: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_event_store()
    sys.exit(0 if success else 1)