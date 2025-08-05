"""
Priority queue implementation for the Agent Hooks Enhancement system.

This module implements a priority queue for events, where events with higher
priority are processed first.
"""

import heapq
from typing import List, Tuple, Optional

from src.event_routing.event_routing import Event


class PriorityQueue:
    """
    Priority queue for events.
    
    This class implements a priority queue for events, where events with higher
    priority are processed first.
    """
    
    def __init__(self):
        """Initialize an empty priority queue."""
        self.queue: List[Tuple[int, int, Event]] = []
        self.counter = 0
    
    def push(self, event: Event, priority: int) -> None:
        """
        Push an event onto the queue with the given priority.
        
        Args:
            event: Event to push
            priority: Priority of the event (higher values = higher priority)
        """
        # Use negative priority because heapq is a min-heap
        heapq.heappush(self.queue, (-priority, self.counter, event))
        self.counter += 1
    
    def pop(self) -> Optional[Event]:
        """
        Pop the highest-priority event from the queue.
        
        Returns:
            Highest-priority event, or None if the queue is empty
        """
        if not self.queue:
            return None
        
        _, _, event = heapq.heappop(self.queue)
        return event
    
    def peek(self) -> Optional[Event]:
        """
        Peek at the highest-priority event without removing it.
        
        Returns:
            Highest-priority event, or None if the queue is empty
        """
        if not self.queue:
            return None
        
        _, _, event = self.queue[0]
        return event
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if the queue is empty, False otherwise
        """
        return len(self.queue) == 0
    
    def size(self) -> int:
        """
        Get the number of events in the queue.
        
        Returns:
            Number of events in the queue
        """
        return len(self.queue)
    
    def clear(self) -> None:
        """Clear the queue."""
        self.queue = []
