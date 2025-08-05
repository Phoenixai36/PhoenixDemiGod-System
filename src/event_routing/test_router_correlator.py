#!/usr/bin/env python3
"""
Test script for EventRouter and EventCorrelator integration.

This script tests the enhanced EventRouter with delivery modes,
error handling, and the EventCorrelator for correlation tracking.
"""

import sys
import threading
import time
import traceback
from datetime import datetime


def test_router_and_correlator():
    """Test the EventRouter and EventCorrelator integration."""
    
    print("🔄 Testing EventRouter and EventCorrelator Integration...")
    
    try:
        # Test imports
        print("  ✓ Testing imports...")
        from src.event_routing import (
            DeliveryMode,
            Event,
            EventCorrelator,
            EventPattern,
            EventRouter,
            InMemoryEventStore,
            WildcardPatternMatcher,
        )
        print("    ✅ All imports successful")
        
        # Create components
        print("  ✓ Testing component creation...")
        store = InMemoryEventStore()
        router = EventRouter(
            pattern_matcher=WildcardPatternMatcher(),
            enable_delivery_confirmation=True
        )
        correlator = EventCorrelator(router, store, auto_correlate=True)
        print("    ✅ Components created")
        
        # Test basic pub/sub
        print("  ✓ Testing basic publish/subscribe...")
        received_events = []
        
        def test_handler(event):
            received_events.append(event)
        
        subscription = router.subscribe(
            pattern=EventPattern("test.*"),
            handler=test_handler
        )
        
        test_event = Event.create(
            event_type="test.basic",
            source="test_source",
            payload={"message": "Hello World"}
        )
        
        router.publish(test_event)
        
        assert len(received_events) == 1
        assert received_events[0].type == "test.basic"
        print("    ✅ Basic pub/sub works")
        
        # Test correlation
        print("  ✓ Testing event correlation...")
        
        # The correlator should have automatically assigned a correlation ID
        time.sleep(0.1)  # Give correlator time to process
        
        stored_events = store.get_events()
        correlated_events = [e for e in stored_events if e.correlation_id is not None]
        assert len(correlated_events) > 0
        
        # Test correlation chain
        correlation_id = correlated_events[0].correlation_id
        chain = correlator.get_correlation_chain(correlation_id)
        assert len(chain) > 0
        print("    ✅ Event correlation works")
        
        # Test async delivery
        print("  ✓ Testing async delivery...")
        async_received = []
        
        def async_handler(event):
            async_received.append(event)
        
        router.subscribe(
            pattern=EventPattern("async.*"),
            handler=async_handler
        )
        
        async_event = Event.create(
            event_type="async.test",
            source="test_source",
            payload={"mode": "async"}
        )
        
        router.publish(async_event, DeliveryMode.ASYNC)
        
        # Wait for async delivery
        time.sleep(0.2)
        assert len(async_received) == 1
        print("    ✅ Async delivery works")
        
        # Test error handling
        print("  ✓ Testing error handling...")
        error_events = []
        
        def error_handler(event, subscription, exception):
            error_events.append((event, subscription, exception))
        
        def failing_handler(event):
            raise ValueError("Test error")
        
        router.add_error_handler(error_handler)
        router.subscribe(
            pattern=EventPattern("error.*"),
            handler=failing_handler
        )
        
        error_event = Event.create(
            event_type="error.test",
            source="test_source",
            payload={"should": "fail"}
        )
        
        router.publish(error_event)
        
        assert len(error_events) == 1
        assert isinstance(error_events[0][2], ValueError)
        print("    ✅ Error handling works")
        
        # Test queued delivery
        print("  ✓ Testing queued delivery...")
        
        queued_event = Event.create(
            event_type="queued.test",
            source="test_source",
            payload={"mode": "queued"}
        )
        
        initial_queue_size = router.event_queue.size()
        router.publish(queued_event, DeliveryMode.QUEUED)
        
        # Should have events in queue now
        assert router.event_queue.size() > initial_queue_size
        print("    ✅ Queued delivery works")
        
        # Test correlation chain building
        print("  ✓ Testing correlation chain building...")
        
        # Create a series of related events
        parent_event = Event.create(
            event_type="chain.parent",
            source="test_source",
            payload={"step": 1}
        )
        
        router.publish(parent_event)
        time.sleep(0.1)  # Let correlator process
        
        # Create child event
        child_event = parent_event.derive(
            event_type="chain.child",
            payload={"step": 2}
        )
        
        router.publish(child_event)
        time.sleep(0.1)
        
        # Check correlation chain
        if parent_event.correlation_id:
            chain = correlator.get_correlation_chain(parent_event.correlation_id)
            assert len(chain) >= 2
            
            # Check causation
            related_events = correlator.find_related_events(parent_event.id)
            assert len(related_events) > 0
        
        print("    ✅ Correlation chain building works")
        
        # Test statistics
        print("  ✓ Testing statistics...")
        router_stats = router.get_stats()
        assert "events_published" in router_stats
        assert "successful_deliveries" in router_stats
        assert router_stats["events_published"] > 0
        
        correlator_stats = correlator.get_correlation_statistics()
        assert "events_processed" in correlator_stats
        assert "active_correlation_chains" in correlator_stats
        print("    ✅ Statistics work")
        
        # Test subscription management
        print("  ✓ Testing subscription management...")
        
        # Pause and resume subscription
        success = router.pause_subscription(subscription.id)
        assert success == True
        
        success = router.resume_subscription(subscription.id)
        assert success == True
        
        # Test subscription cleanup
        expired_count = router.cleanup_expired_subscriptions()
        assert expired_count >= 0
        print("    ✅ Subscription management works")
        
        # Test retry mechanism
        print("  ✓ Testing retry mechanism...")
        retry_attempts = []
        
        def retry_handler(event):
            retry_attempts.append(event)
            if len(retry_attempts) < 2:
                raise RuntimeError("Retry test")
        
        router.subscribe(
            pattern=EventPattern("retry.*"),
            handler=retry_handler
        )
        
        retry_event = Event.create(
            event_type="retry.test",
            source="test_source",
            payload={"attempt": 1}
        )
        
        success = router.publish_with_retry(retry_event, max_retries=2, retry_delay=0.1)
        assert success == True
        assert len(retry_attempts) >= 2
        print("    ✅ Retry mechanism works")
        
        # Cleanup
        correlator.stop()
        
        print("\n🎉 EventRouter and EventCorrelator Test: ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ EventRouter and EventCorrelator Test FAILED: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_router_and_correlator()
    sys.exit(0 if success else 1)