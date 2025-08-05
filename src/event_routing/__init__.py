"""
Event Routing System for Phoenix Hydra

This module provides a comprehensive event routing system with pattern matching,
subscription management, and delivery modes for the Phoenix Hydra ecosystem.
"""

from .event_correlator import (
    CorrelationChain,
    # Event correlator
    EventCorrelator,
)
from .event_routing import (
    CachedPatternMatcher,
    DefaultPatternMatcher,
    DeliveryMode,
    # Core data models
    Event,
    EventPattern,
    # Event queue
    EventQueue,
    # Main router
    EventRouter,
    InMemoryEventQueue,
    # Pattern matching
    PatternMatcher,
    Subscription,
    WildcardPatternMatcher,
)
from .event_store import (
    # Event store
    EventStoreBase,
    InMemoryEventStore,
    RetentionPolicy,
)

__all__ = [
    # Core data models
    'Event',
    'EventPattern',
    'Subscription',
    'DeliveryMode',
    
    # Pattern matching
    'PatternMatcher',
    'DefaultPatternMatcher',
    'WildcardPatternMatcher',
    'CachedPatternMatcher',
    
    # Event queue
    'EventQueue',
    'InMemoryEventQueue',
    
    # Main router
    'EventRouter',
    
    # Event store
    'EventStoreBase',
    'InMemoryEventStore',
    'RetentionPolicy',
    
    # Event correlator
    'EventCorrelator',
    'CorrelationChain',
]