"""
Event Store implementation for Phoenix Hydra Event Routing System.

This module provides event persistence and retrieval capabilities,
supporting chronological ordering, filtering, and retention policies.
"""

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from .event_routing import Event


@dataclass
class RetentionPolicy:
    """
    Defines retention policies for event storage.
    
    Attributes:
        max_age_seconds: Maximum age of events in seconds (None = no age limit)
        max_count: Maximum number of events to retain (None = no count limit)
        event_type_policies: Specific policies for event types
        priority_based: Whether to prioritize certain events during cleanup
        preserve_correlations: Whether to preserve complete correlation chains
    """
    max_age_seconds: Optional[float] = None
    max_count: Optional[int] = None
    event_type_policies: Dict[str, 'RetentionPolicy'] = field(default_factory=dict)
    priority_based: bool = False
    preserve_correlations: bool = False
    
    def is_expired(self, event: Event, current_time: Optional[float] = None) -> bool:
        """
        Check if an event should be expired based on this policy.
        
        Args:
            event: The event to check
            current_time: Current timestamp (defaults to now)
            
        Returns:
            True if the event should be expired, False otherwise
        """
        if current_time is None:
            current_time = time.time()
        
        # Check event-type-specific policy first
        if event.type in self.event_type_policies:
            return self.event_type_policies[event.type].is_expired(event, current_time)
        
        # Check age-based expiration
        if self.max_age_seconds is not None:
            event_age = current_time - event.timestamp.timestamp()
            if event_age > self.max_age_seconds:
                return True
        
        return False


class EventStoreBase(ABC):
    """
    Abstract base class for event store implementations.
    
    This interface defines the contract for event stores that persist
    and retrieve events for the Event Routing System.
    """
    
    @abstractmethod
    def store(self, event: Event) -> None:
        """
        Store a single event.
        
        Args:
            event: The event to store
        """
        pass
    
    @abstractmethod
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Retrieve an event by its ID.
        
        Args:
            event_id: The ID of the event to retrieve
            
        Returns:
            The event if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_events(self, 
                   filter_criteria: Optional[Dict[str, Any]] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: Optional[int] = None,
                   offset: int = 0) -> List[Event]:
        """
        Retrieve events based on filter criteria.
        
        Args:
            filter_criteria: Dictionary of filter criteria
            start_time: Start time for time-based filtering
            end_time: End time for time-based filtering
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of events matching the criteria, ordered chronologically
        """
        pass
    
    @abstractmethod
    def cleanup_expired_events(self, retention_policy: RetentionPolicy) -> int:
        """
        Remove expired events based on retention policy.
        
        Args:
            retention_policy: The retention policy to apply
            
        Returns:
            Number of events removed
        """
        pass
    
    @abstractmethod
    def get_event_count(self, filter_criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Get the count of events matching filter criteria.
        
        Args:
            filter_criteria: Dictionary of filter criteria
            
        Returns:
            Number of events matching the criteria
        """
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """
        Clear all events from the store.
        
        Returns:
            Number of events removed
        """
        pass


class InMemoryEventStore(EventStoreBase):
    """
    In-memory implementation of the EventStore interface.
    
    This implementation stores events in memory using a list for chronological
    ordering and a dictionary for fast ID-based lookups. It's suitable for
    development, testing, and scenarios where persistence is not required.
    """
    
    def __init__(self):
        """Initialize the in-memory event store."""
        self._events: List[Event] = []
        self._events_by_id: Dict[str, Event] = {}
        self._lock = threading.RLock()
    
    def store(self, event: Event) -> None:
        """
        Store a single event.
        
        Args:
            event: The event to store
        """
        with self._lock:
            # Check if event already exists
            if event.id in self._events_by_id:
                # Update existing event
                existing_event = self._events_by_id[event.id]
                index = self._events.index(existing_event)
                self._events[index] = event
            else:
                # Add new event in chronological order
                self._events.append(event)
                # Sort to maintain chronological order
                self._events.sort(key=lambda e: e.timestamp)
            
            # Update ID lookup
            self._events_by_id[event.id] = event
    
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Retrieve an event by its ID.
        
        Args:
            event_id: The ID of the event to retrieve
            
        Returns:
            The event if found, None otherwise
        """
        with self._lock:
            return self._events_by_id.get(event_id)
    
    def get_events(self, 
                   filter_criteria: Optional[Dict[str, Any]] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: Optional[int] = None,
                   offset: int = 0) -> List[Event]:
        """
        Retrieve events based on filter criteria.
        
        Args:
            filter_criteria: Dictionary of filter criteria
            start_time: Start time for time-based filtering
            end_time: End time for time-based filtering
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of events matching the criteria, ordered chronologically
        """
        with self._lock:
            # Start with all events (already chronologically ordered)
            filtered_events = self._events.copy()
            
            # Apply time-based filtering
            if start_time is not None:
                filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
            
            if end_time is not None:
                filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
            
            # Apply filter criteria
            if filter_criteria:
                filtered_events = self._apply_filter_criteria(filtered_events, filter_criteria)
            
            # Apply offset and limit
            if offset > 0:
                filtered_events = filtered_events[offset:]
            
            if limit is not None:
                filtered_events = filtered_events[:limit]
            
            return filtered_events
    
    def _apply_filter_criteria(self, events: List[Event], criteria: Dict[str, Any]) -> List[Event]:
        """
        Apply filter criteria to a list of events.
        
        Args:
            events: List of events to filter
            criteria: Filter criteria dictionary
            
        Returns:
            Filtered list of events
        """
        filtered_events = []
        
        for event in events:
            if self._event_matches_criteria(event, criteria):
                filtered_events.append(event)
        
        return filtered_events
    
    def _event_matches_criteria(self, event: Event, criteria: Dict[str, Any]) -> bool:
        """
        Check if an event matches the given criteria.
        
        Args:
            event: The event to check
            criteria: The criteria to match against
            
        Returns:
            True if the event matches all criteria, False otherwise
        """
        for key, value in criteria.items():
            if key == "type":
                if event.type != value:
                    return False
            elif key == "source":
                if event.source != value:
                    return False
            elif key == "correlation_id":
                if event.correlation_id != value:
                    return False
            elif key == "causation_id":
                if event.causation_id != value:
                    return False
            elif key == "is_replay":
                if event.is_replay != value:
                    return False
            elif key.startswith("payload."):
                # Handle nested payload filtering
                payload_key = key[8:]  # Remove "payload." prefix
                if not self._check_nested_value(event.payload, payload_key, value):
                    return False
            elif key.startswith("metadata."):
                # Handle nested metadata filtering
                metadata_key = key[9:]  # Remove "metadata." prefix
                if not self._check_nested_value(event.metadata, metadata_key, value):
                    return False
            else:
                # Direct attribute check
                if not hasattr(event, key) or getattr(event, key) != value:
                    return False
        
        return True
    
    def _check_nested_value(self, data: Dict[str, Any], key_path: str, expected_value: Any) -> bool:
        """
        Check a nested value using dot notation.
        
        Args:
            data: The data dictionary to check
            key_path: The key path (e.g., "user.id")
            expected_value: The expected value
            
        Returns:
            True if the nested value matches, False otherwise
        """
        keys = key_path.split(".")
        current = data
        
        for key in keys[:-1]:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        
        final_key = keys[-1]
        if not isinstance(current, dict) or final_key not in current:
            return False
        
        return current[final_key] == expected_value
    
    def cleanup_expired_events(self, retention_policy: RetentionPolicy) -> int:
        """
        Remove expired events based on retention policy.
        
        Args:
            retention_policy: The retention policy to apply
            
        Returns:
            Number of events removed
        """
        with self._lock:
            initial_count = len(self._events)
            current_time = time.time()
            
            # If preserve_correlations is enabled, we need special handling
            if retention_policy.preserve_correlations:
                return self._cleanup_with_correlation_preservation(retention_policy, current_time)
            
            # Standard cleanup without correlation preservation
            non_expired_events = []
            removed_events = []
            
            for event in self._events:
                effective_policy = retention_policy.get_effective_policy(event)
                if not effective_policy.is_expired(event, current_time):
                    non_expired_events.append(event)
                else:
                    removed_events.append(event)
                    # Remove from ID lookup
                    if event.id in self._events_by_id:
                        del self._events_by_id[event.id]
            
            # Apply count-based retention if specified
            if retention_policy.max_count is not None and len(non_expired_events) > retention_policy.max_count:
                # Keep the most recent events
                events_to_remove = len(non_expired_events) - retention_policy.max_count
                
                if retention_policy.priority_based:
                    # Sort by priority (keep high priority events)
                    non_expired_events.sort(key=lambda e: (
                        e.metadata.get('priority', 0),  # Higher priority first
                        e.timestamp  # Then by timestamp
                    ), reverse=True)
                
                # Remove oldest/lowest priority events
                for event in non_expired_events[:events_to_remove]:
                    removed_events.append(event)
                    if event.id in self._events_by_id:
                        del self._events_by_id[event.id]
                
                non_expired_events = non_expired_events[events_to_remove:]
                
                # Re-sort by timestamp for chronological order
                non_expired_events.sort(key=lambda e: e.timestamp)
            
            self._events = non_expired_events
            return len(removed_events)
    
    def _cleanup_with_correlation_preservation(self, 
                                             retention_policy: RetentionPolicy, 
                                             current_time: float) -> int:
        """
        Cleanup events while preserving complete correlation chains.
        
        Args:
            retention_policy: The retention policy to apply
            current_time: Current timestamp
            
        Returns:
            Number of events removed
        """
        initial_count = len(self._events)
        
        # Group events by correlation ID
        correlation_groups = {}
        standalone_events = []
        
        for event in self._events:
            if event.correlation_id:
                if event.correlation_id not in correlation_groups:
                    correlation_groups[event.correlation_id] = []
                correlation_groups[event.correlation_id].append(event)
            else:
                standalone_events.append(event)
        
        # Process standalone events normally
        kept_events = []
        for event in standalone_events:
            effective_policy = retention_policy.get_effective_policy(event)
            if not effective_policy.is_expired(event, current_time):
                kept_events.append(event)
            else:
                if event.id in self._events_by_id:
                    del self._events_by_id[event.id]
        
        # Process correlation groups
        for correlation_id, events in correlation_groups.items():
            # Check if any event in the group should be preserved
            should_preserve_group = False
            
            for event in events:
                effective_policy = retention_policy.get_effective_policy(event)
                if not effective_policy.is_expired(event, current_time):
                    should_preserve_group = True
                    break
            
            if should_preserve_group:
                # Keep the entire correlation chain
                kept_events.extend(events)
            else:
                # Remove the entire correlation chain
                for event in events:
                    if event.id in self._events_by_id:
                        del self._events_by_id[event.id]
        
        # Apply count-based retention if needed
        if retention_policy.max_count is not None and len(kept_events) > retention_policy.max_count:
            # Sort by timestamp and keep most recent
            kept_events.sort(key=lambda e: e.timestamp)
            events_to_remove = len(kept_events) - retention_policy.max_count
            
            for event in kept_events[:events_to_remove]:
                if event.id in self._events_by_id:
                    del self._events_by_id[event.id]
            
            kept_events = kept_events[events_to_remove:]
        
        # Sort final events by timestamp
        kept_events.sort(key=lambda e: e.timestamp)
        self._events = kept_events
        
        return initial_count - len(self._events)
    
    def get_event_count(self, filter_criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Get the count of events matching filter criteria.
        
        Args:
            filter_criteria: Dictionary of filter criteria
            
        Returns:
            Number of events matching the criteria
        """
        with self._lock:
            if filter_criteria is None:
                return len(self._events)
            
            filtered_events = self._apply_filter_criteria(self._events, filter_criteria)
            return len(filtered_events)
    
    def clear(self) -> int:
        """
        Clear all events from the store.
        
        Returns:
            Number of events removed
        """
        with self._lock:
            count = len(self._events)
            self._events.clear()
            self._events_by_id.clear()
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the event store.
        
        Returns:
            Dictionary with store statistics
        """
        with self._lock:
            if not self._events:
                return {
                    "total_events": 0,
                    "oldest_event": None,
                    "newest_event": None,
                    "event_types": {},
                    "sources": {}
                }
            
            # Count events by type and source
            event_types = {}
            sources = {}
            
            for event in self._events:
                event_types[event.type] = event_types.get(event.type, 0) + 1
                sources[event.source] = sources.get(event.source, 0) + 1
            
            return {
                "total_events": len(self._events),
                "oldest_event": self._events[0].timestamp.isoformat(),
                "newest_event": self._events[-1].timestamp.isoformat(),
                "event_types": event_types,
                "sources": sources
            } 
   def get_events_by_correlation_id(self, correlation_id: str) -> List[Event]:
        """
        Get all events with the same correlation ID.
        
        Args:
            correlation_id: The correlation ID to search for
            
        Returns:
            List of events with the same correlation ID, ordered chronologically
        """
        return self.get_events(filter_criteria={"correlation_id": correlation_id})
    
    def get_events_by_type_pattern(self, type_pattern: str) -> List[Event]:
        """
        Get events matching a type pattern (supports wildcards).
        
        Args:
            type_pattern: Event type pattern (e.g., "user.*", "system.error.*")
            
        Returns:
            List of matching events
        """
        with self._lock:
            from .event_routing import WildcardPatternMatcher
            matcher = WildcardPatternMatcher()
            
            matching_events = []
            for event in self._events:
                if matcher.matches_event_type(event.type, type_pattern):
                    matching_events.append(event)
            
            return matching_events
    
    def get_events_by_source_pattern(self, source_pattern: str) -> List[Event]:
        """
        Get events matching a source pattern (supports wildcards).
        
        Args:
            source_pattern: Source pattern (e.g., "service.*", "agent.*.processor")
            
        Returns:
            List of matching events
        """
        with self._lock:
            from .event_routing import WildcardPatternMatcher
            matcher = WildcardPatternMatcher()
            
            matching_events = []
            for event in self._events:
                if matcher.matches_event_type(event.source, source_pattern):
                    matching_events.append(event)
            
            return matching_events
    
    def search_events(self, 
                     query: str, 
                     search_fields: List[str] = None) -> List[Event]:
        """
        Search events using text search across specified fields.
        
        Args:
            query: Search query string
            search_fields: Fields to search in (defaults to payload and metadata)
            
        Returns:
            List of events containing the query string
        """
        if search_fields is None:
            search_fields = ["payload", "metadata"]
        
        with self._lock:
            matching_events = []
            query_lower = query.lower()
            
            for event in self._events:
                found = False
                
                for field in search_fields:
                    if field == "payload":
                        if self._search_in_dict(event.payload, query_lower):
                            found = True
                            break
                    elif field == "metadata":
                        if self._search_in_dict(event.metadata, query_lower):
                            found = True
                            break
                    elif hasattr(event, field):
                        field_value = str(getattr(event, field)).lower()
                        if query_lower in field_value:
                            found = True
                            break
                
                if found:
                    matching_events.append(event)
            
            return matching_events
    
    def _search_in_dict(self, data: Dict[str, Any], query: str) -> bool:
        """
        Search for a query string within a dictionary recursively.
        
        Args:
            data: Dictionary to search in
            query: Query string (already lowercased)
            
        Returns:
            True if query found, False otherwise
        """
        for key, value in data.items():
            if isinstance(value, dict):
                if self._search_in_dict(value, query):
                    return True
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, dict):
                        if self._search_in_dict(item, query):
                            return True
                    elif query in str(item).lower():
                        return True
            elif query in str(value).lower():
                return True
        
        return False
    
    def get_event_timeline(self, 
                          correlation_id: str, 
                          include_causation: bool = True) -> List[Event]:
        """
        Get a timeline of related events based on correlation and causation.
        
        Args:
            correlation_id: The correlation ID to build timeline for
            include_causation: Whether to include causation relationships
            
        Returns:
            List of events in chronological order showing the event timeline
        """
        with self._lock:
            timeline_events = []
            
            # Get all events with the same correlation ID
            correlated_events = self.get_events_by_correlation_id(correlation_id)
            timeline_events.extend(correlated_events)
            
            if include_causation:
                # Find events that caused or were caused by these events
                event_ids = {event.id for event in correlated_events}
                
                for event in self._events:
                    # Include events that caused any of our correlated events
                    if event.id in {e.causation_id for e in correlated_events if e.causation_id}:
                        if event not in timeline_events:
                            timeline_events.append(event)
                    
                    # Include events that were caused by any of our correlated events
                    if event.causation_id in event_ids:
                        if event not in timeline_events:
                            timeline_events.append(event)
            
            # Sort by timestamp
            timeline_events.sort(key=lambda e: e.timestamp)
            return timeline_events
    
    def aggregate_events(self, 
                        group_by: str, 
                        filter_criteria: Optional[Dict[str, Any]] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, List[Event]]:
        """
        Aggregate events by a specified field.
        
        Args:
            group_by: Field to group by (e.g., "type", "source", "correlation_id")
            filter_criteria: Optional filter criteria
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary mapping group values to lists of events
        """
        events = self.get_events(
            filter_criteria=filter_criteria,
            start_time=start_time,
            end_time=end_time
        )
        
        aggregated = {}
        
        for event in events:
            if group_by == "type":
                key = event.type
            elif group_by == "source":
                key = event.source
            elif group_by == "correlation_id":
                key = event.correlation_id or "no_correlation"
            elif group_by.startswith("payload."):
                payload_key = group_by[8:]
                key = str(self._get_nested_value(event.payload, payload_key, "unknown"))
            elif group_by.startswith("metadata."):
                metadata_key = group_by[9:]
                key = str(self._get_nested_value(event.metadata, metadata_key, "unknown"))
            else:
                key = str(getattr(event, group_by, "unknown"))
            
            if key not in aggregated:
                aggregated[key] = []
            aggregated[key].append(event)
        
        return aggregated
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        Get a nested value using dot notation.
        
        Args:
            data: The data dictionary
            key_path: The key path (e.g., "user.id")
            default: Default value if not found
            
        Returns:
            The nested value or default
        """
        keys = key_path.split(".")
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default    
   
 @classmethod
    def create_age_based_policy(cls, max_age_hours: float) -> 'RetentionPolicy':
        """
        Create an age-based retention policy.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            RetentionPolicy configured for age-based retention
        """
        return cls(max_age_seconds=max_age_hours * 3600)
    
    @classmethod
    def create_count_based_policy(cls, max_count: int) -> 'RetentionPolicy':
        """
        Create a count-based retention policy.
        
        Args:
            max_count: Maximum number of events to retain
            
        Returns:
            RetentionPolicy configured for count-based retention
        """
        return cls(max_count=max_count)
    
    @classmethod
    def create_combined_policy(cls, 
                              max_age_hours: float, 
                              max_count: int,
                              preserve_correlations: bool = True) -> 'RetentionPolicy':
        """
        Create a combined age and count-based retention policy.
        
        Args:
            max_age_hours: Maximum age in hours
            max_count: Maximum number of events to retain
            preserve_correlations: Whether to preserve correlation chains
            
        Returns:
            RetentionPolicy configured for combined retention
        """
        return cls(
            max_age_seconds=max_age_hours * 3600,
            max_count=max_count,
            preserve_correlations=preserve_correlations
        )
    
    def add_event_type_policy(self, event_type: str, policy: 'RetentionPolicy') -> None:
        """
        Add a specific retention policy for an event type.
        
        Args:
            event_type: The event type to apply the policy to
            policy: The retention policy for this event type
        """
        self.event_type_policies[event_type] = policy
    
    def get_effective_policy(self, event: Event) -> 'RetentionPolicy':
        """
        Get the effective retention policy for a specific event.
        
        Args:
            event: The event to get the policy for
            
        Returns:
            The effective retention policy
        """
        if event.type in self.event_type_policies:
            return self.event_type_policies[event.type]
        return self    

    def get_retention_stats(self, retention_policy: RetentionPolicy) -> Dict[str, Any]:
        """
        Get statistics about what would be affected by a retention policy.
        
        Args:
            retention_policy: The retention policy to analyze
            
        Returns:
            Dictionary with retention statistics
        """
        with self._lock:
            if not self._events:
                return {
                    "total_events": 0,
                    "events_to_expire": 0,
                    "events_to_keep": 0,
                    "oldest_event_age_hours": 0,
                    "newest_event_age_hours": 0
                }
            
            current_time = time.time()
            events_to_expire = 0
            events_to_keep = 0
            
            for event in self._events:
                effective_policy = retention_policy.get_effective_policy(event)
                if effective_policy.is_expired(event, current_time):
                    events_to_expire += 1
                else:
                    events_to_keep += 1
            
            # Calculate age statistics
            oldest_event = min(self._events, key=lambda e: e.timestamp)
            newest_event = max(self._events, key=lambda e: e.timestamp)
            
            oldest_age_hours = (current_time - oldest_event.timestamp.timestamp()) / 3600
            newest_age_hours = (current_time - newest_event.timestamp.timestamp()) / 3600
            
            # Count-based expiration
            count_based_expiration = 0
            if retention_policy.max_count is not None:
                if len(self._events) > retention_policy.max_count:
                    count_based_expiration = len(self._events) - retention_policy.max_count
            
            return {
                "total_events": len(self._events),
                "events_to_expire": events_to_expire,
                "events_to_keep": events_to_keep,
                "count_based_expiration": count_based_expiration,
                "oldest_event_age_hours": oldest_age_hours,
                "newest_event_age_hours": newest_age_hours,
                "policy_max_age_hours": retention_policy.max_age_seconds / 3600 if retention_policy.max_age_seconds else None,
                "policy_max_count": retention_policy.max_count
            }