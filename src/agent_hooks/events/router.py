"""
Event router and processing pipeline for the Agent Hooks Enhancement system.

This module implements the central event routing and processing functionality,
including event filtering, priority-based processing, and hook matching.
"""

import asyncio
import heapq
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Callable, Tuple, Awaitable, TypeVar, Generic, Union, cast
import logging
import re

from src.agent_hooks.core.models import AgentHook, HookContext, HookResult, HookPriority, HookTrigger
from src.agent_hooks.events.models import (
    BaseEvent, FileEvent, MetricEvent, SystemEvent, GitEvent, BuildEvent, DependencyEvent,
    EventType, EventSeverity, EventSerializer, EventValidator
)
from src.agent_hooks.utils.logging import get_logger, ExecutionError


# Type variable for event handlers
T = TypeVar("T", bound=BaseEvent)


class EventFilterType(Enum):
    """Types of event filters."""
    SOURCE = "source"
    TYPE = "type"
    SEVERITY = "severity"
    ATTRIBUTE = "attribute"
    CUSTOM = "custom"


class EventFilter:
    """
    Filter for events based on various criteria.
    
    This class provides a flexible way to filter events based on their
    source, type, severity, attributes, or custom conditions.
    """
    
    def __init__(
        self,
        filter_type: EventFilterType,
        value: Any = None,
        attribute_name: Optional[str] = None,
        custom_filter: Optional[Callable[[BaseEvent], bool]] = None,
        invert: bool = False
    ):
        """
        Initialize an event filter.
        
        Args:
            filter_type: Type of filter to apply
            value: Value to compare against
            attribute_name: Name of the attribute to check (for ATTRIBUTE filter type)
            custom_filter: Custom filter function (for CUSTOM filter type)
            invert: Whether to invert the filter result
        """
        self.filter_type = filter_type
        self.value = value
        self.attribute_name = attribute_name
        self.custom_filter = custom_filter
        self.invert = invert
    
    def matches(self, event: BaseEvent) -> bool:
        """
        Check if an event matches this filter.
        
        Args:
            event: Event to check
            
        Returns:
            True if the event matches the filter, False otherwise
        """
        result = False
        
        if self.filter_type == EventFilterType.SOURCE:
            result = event.source == self.value
        
        elif self.filter_type == EventFilterType.TYPE:
            if isinstance(self.value, list):
                result = event.type in self.value
            else:
                result = event.type == self.value
        
        elif self.filter_type == EventFilterType.SEVERITY:
            if isinstance(self.value, list):
                result = event.severity in self.value
            else:
                result = event.severity == self.value
        
        elif self.filter_type == EventFilterType.ATTRIBUTE:
            if self.attribute_name is None:
                return False
            
            # Handle nested attributes using dot notation
            if "." in self.attribute_name:
                parts = self.attribute_name.split(".")
                obj = event
                for part in parts:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    elif isinstance(obj, dict) and part in obj:
                        obj = obj[part]
                    else:
                        return False
                
                result = obj == self.value
            else:
                # Check if the attribute exists
                if hasattr(event, self.attribute_name):
                    result = getattr(event, self.attribute_name) == self.value
                elif isinstance(event.data, dict) and self.attribute_name in event.data:
                    result = event.data[self.attribute_name] == self.value
                elif isinstance(event.context, dict) and self.attribute_name in event.context:
                    result = event.context[self.attribute_name] == self.value
        
        elif self.filter_type == EventFilterType.CUSTOM:
            if self.custom_filter is None:
                return False
            
            result = self.custom_filter(event)
        
        return not result if self.invert else result


class EventFilterGroup:
    """
    Group of event filters with logical operations.
    
    This class allows combining multiple filters with AND or OR operations.
    """
    
    def __init__(self, filters: List[Union[EventFilter, "EventFilterGroup"]], operator: str = "AND"):
        """
        Initialize an event filter group.
        
        Args:
            filters: List of filters or filter groups to combine
            operator: Logical operator to use ("AND" or "OR")
        """
        self.filters = filters
        self.operator = operator.upper()
        
        if self.operator not in ("AND", "OR"):
            raise ValueError(f"Invalid operator: {operator}")
    
    def matches(self, event: BaseEvent) -> bool:
        """
        Check if an event matches this filter group.
        
        Args:
            event: Event to check
            
        Returns:
            True if the event matches the filter group, False otherwise
        """
        if not self.filters:
            return True
        
        if self.operator == "AND":
            return all(f.matches(event) for f in self.filters)
        else:  # OR
            return any(f.matches(event) for f in self.filters)
