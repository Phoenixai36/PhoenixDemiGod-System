"""
Event Correlator for Phoenix Hydra Event Routing System

This module implements the EventCorrelator component that tracks relationships
between events and maintains correlation chains for workflow processing.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set

from .event_routing import Event


@dataclass
class CorrelationChain:
    """
    Represents a chain of correlated events.
    
    Attributes:
        correlation_id: Unique identifier for the correlation chain
        root_event_id: ID of the first event in the chain
        events: List of event IDs in chronological order
        created_at: When the correlation chain was created
        last_updated: When the chain was last updated
        metadata: Additional metadata about the correlation
    """
    correlation_id: str
    root_event_id: str
    events: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def add_event(self, event_id: str) -> None:
        """
        Add an event to the correlation chain.
        
        Args:
            event_id: ID of the event to add
        """
        if event_id not in self.events:
            self.events.append(event_id)
            self.last_updated = datetime.now()
    
    def get_event_count(self) -> int:
        """
        Get the number of events in the correlation chain.
        
        Returns:
            Number of events in the chain
        """
        return len(self.events)
    
    def contains_event(self, event_id: str) -> bool:
        """
        Check if an event is part of this correlation chain.
        
        Args:
            event_id: ID of the event to check
            
        Returns:
            True if the event is in the chain, False otherwise
        """
        return event_id in self.events


class EventCorrelator:
    """
    Manages event correlation and maintains correlation chains.
    
    This component tracks relationships between events and provides
    functionality to correlate events and retrieve correlation chains.
    """
    
    def __init__(self):
        """Initialize the event correlator."""
        self._correlation_chains: Dict[str, CorrelationChain] = {}
        self._event_to_correlation: Dict[str, str] = {}
        self._stored_events: Dict[str, Event] = {}
    
    def correlate(self, event: Event, parent_event: Optional[Event] = None) -> Event:
        """
        Correlate an event with a parent event or start a new correlation.
        
        This method either:
        1. Creates a new correlation chain if no parent event is provided
        2. Adds the event to an existing correlation chain if parent event is provided
        3. Uses existing correlation_id from the event if already set
        
        Args:
            event: The event to correlate
            parent_event: Optional parent event to correlate with
            
        Returns:
            The event with correlation information updated
        """
        # If event already has a correlation_id, use it
        if event.correlation_id:
            correlation_id = event.correlation_id
            
            # Ensure the correlation chain exists
            if correlation_id not in self._correlation_chains:
                self._correlation_chains[correlation_id] = CorrelationChain(
                    correlation_id=correlation_id,
                    root_event_id=event.id
                )
        
        # If parent event is provided, use its correlation
        elif parent_event:
            if parent_event.correlation_id:
                correlation_id = parent_event.correlation_id
            else:
                # Parent event doesn't have correlation, create one
                correlation_id = self._generate_correlation_id()
                parent_event.correlation_id = correlation_id
                
                # Create correlation chain for parent if it doesn't exist
                if correlation_id not in self._correlation_chains:
                    self._correlation_chains[correlation_id] = CorrelationChain(
                        correlation_id=correlation_id,
                        root_event_id=parent_event.id
                    )
                    self._correlation_chains[correlation_id].add_event(parent_event.id)
                    self._event_to_correlation[parent_event.id] = correlation_id
                    self._stored_events[parent_event.id] = parent_event
            
            # Set correlation and causation for the new event
            event.correlation_id = correlation_id
            event.causation_id = parent_event.id
        
        # No parent event and no existing correlation, create new correlation
        else:
            correlation_id = self._generate_correlation_id()
            event.correlation_id = correlation_id
            
            # Create new correlation chain
            self._correlation_chains[correlation_id] = CorrelationChain(
                correlation_id=correlation_id,
                root_event_id=event.id
            )
        
        # Add event to the correlation chain
        chain = self._correlation_chains[correlation_id]
        chain.add_event(event.id)
        
        # Update mappings
        self._event_to_correlation[event.id] = correlation_id
        self._stored_events[event.id] = event
        
        return event
    
    def get_correlation_chain(self, correlation_id: str) -> List[Event]:
        """
        Get all events in a correlation chain.
        
        Args:
            correlation_id: The correlation ID to retrieve events for
            
        Returns:
            List of events in chronological order (by timestamp)
            
        Raises:
            ValueError: If the correlation ID is not found
        """
        if correlation_id not in self._correlation_chains:
            raise ValueError(f"Correlation ID {correlation_id} not found")
        
        chain = self._correlation_chains[correlation_id]
        events = []
        
        for event_id in chain.events:
            if event_id in self._stored_events:
                events.append(self._stored_events[event_id])
        
        # Sort events by timestamp to ensure chronological order
        events.sort(key=lambda e: e.timestamp)
        
        return events
    
    def get_correlation_id_for_event(self, event_id: str) -> Optional[str]:
        """
        Get the correlation ID for a specific event.
        
        Args:
            event_id: The event ID to look up
            
        Returns:
            The correlation ID if found, None otherwise
        """
        return self._event_to_correlation.get(event_id)
    
    def get_related_events(self, event_id: str) -> List[Event]:
        """
        Get all events related to a specific event through correlation.
        
        Args:
            event_id: The event ID to find related events for
            
        Returns:
            List of related events (including the original event)
        """
        correlation_id = self.get_correlation_id_for_event(event_id)
        if not correlation_id:
            # Return just the event itself if no correlation exists
            if event_id in self._stored_events:
                return [self._stored_events[event_id]]
            return []
        
        return self.get_correlation_chain(correlation_id)
    
    def get_causation_chain(self, event_id: str) -> List[Event]:
        """
        Get the causation chain for an event (events that led to this event).
        
        Args:
            event_id: The event ID to trace causation for
            
        Returns:
            List of events in causation order (root cause first)
        """
        if event_id not in self._stored_events:
            return []
        
        causation_chain = []
        current_event = self._stored_events[event_id]
        visited = set()  # Prevent infinite loops
        
        while current_event and current_event.id not in visited:
            causation_chain.append(current_event)
            visited.add(current_event.id)
            
            # Find the parent event (causation)
            if current_event.causation_id and current_event.causation_id in self._stored_events:
                current_event = self._stored_events[current_event.causation_id]
            else:
                break
        
        # Reverse to get root cause first
        causation_chain.reverse()
        return causation_chain
    
    def associate_events(self, event_ids: List[str], correlation_id: Optional[str] = None) -> str:
        """
        Associate multiple events with the same correlation.
        
        Args:
            event_ids: List of event IDs to associate
            correlation_id: Optional correlation ID to use (generates new one if not provided)
            
        Returns:
            The correlation ID used for association
            
        Raises:
            ValueError: If any event ID is not found
        """
        # Validate all event IDs exist
        for event_id in event_ids:
            if event_id not in self._stored_events:
                raise ValueError(f"Event ID {event_id} not found")
        
        # Use provided correlation ID or generate new one
        if not correlation_id:
            correlation_id = self._generate_correlation_id()
        
        # Create or get correlation chain
        if correlation_id not in self._correlation_chains:
            # Use first event as root
            root_event_id = event_ids[0] if event_ids else str(uuid.uuid4())
            self._correlation_chains[correlation_id] = CorrelationChain(
                correlation_id=correlation_id,
                root_event_id=root_event_id
            )
        
        chain = self._correlation_chains[correlation_id]
        
        # Associate all events with this correlation
        for event_id in event_ids:
            event = self._stored_events[event_id]
            event.correlation_id = correlation_id
            
            chain.add_event(event_id)
            self._event_to_correlation[event_id] = correlation_id
        
        return correlation_id
    
    def get_correlation_statistics(self) -> Dict[str, any]:
        """
        Get statistics about correlations.
        
        Returns:
            Dictionary with correlation statistics
        """
        total_chains = len(self._correlation_chains)
        total_events = len(self._stored_events)
        
        if total_chains == 0:
            return {
                "total_correlation_chains": 0,
                "total_correlated_events": 0,
                "average_events_per_chain": 0,
                "largest_chain_size": 0,
                "uncorrelated_events": total_events
            }
        
        chain_sizes = [chain.get_event_count() for chain in self._correlation_chains.values()]
        correlated_events = sum(chain_sizes)
        
        return {
            "total_correlation_chains": total_chains,
            "total_correlated_events": correlated_events,
            "average_events_per_chain": correlated_events / total_chains,
            "largest_chain_size": max(chain_sizes) if chain_sizes else 0,
            "uncorrelated_events": total_events - correlated_events
        }
    
    def cleanup_expired_correlations(self, max_age_hours: int = 24) -> int:
        """
        Clean up old correlation chains.
        
        Args:
            max_age_hours: Maximum age in hours for correlation chains
            
        Returns:
            Number of correlation chains removed
        """
        current_time = datetime.now()
        expired_correlations = []
        
        for correlation_id, chain in self._correlation_chains.items():
            age_hours = (current_time - chain.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                expired_correlations.append(correlation_id)
        
        # Remove expired correlations
        for correlation_id in expired_correlations:
            chain = self._correlation_chains[correlation_id]
            
            # Remove event mappings
            for event_id in chain.events:
                if event_id in self._event_to_correlation:
                    del self._event_to_correlation[event_id]
                if event_id in self._stored_events:
                    del self._stored_events[event_id]
            
            # Remove correlation chain
            del self._correlation_chains[correlation_id]
        
        return len(expired_correlations)
    
    def _generate_correlation_id(self) -> str:
        """
        Generate a unique correlation ID.
        
        Returns:
            A unique correlation ID string
        """
        return f"corr_{uuid.uuid4().hex[:12]}"
    
    def get_all_correlation_chains(self) -> Dict[str, CorrelationChain]:
        """
        Get all correlation chains.
        
        Returns:
            Dictionary mapping correlation IDs to CorrelationChain objects
        """
        return self._correlation_chains.copy()
    
    def clear_all_correlations(self) -> None:
        """Clear all correlation data (useful for testing)."""
        self._correlation_chains.clear()
        self._event_to_correlation.clear()
        self._stored_events.clear()