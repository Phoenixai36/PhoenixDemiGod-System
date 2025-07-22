"""
Core models for the Agent Hooks Enhancement system.

This module defines the fundamental data structures and interfaces used throughout
the hook system, including enums, data classes, and abstract base classes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Set
from uuid import uuid4
from ..events.models import EventType, EventFilterGroup


class HookPriority(Enum):
    """Priority levels for hook execution."""
    CRITICAL = 1    # Security, system failures
    HIGH = 2        # Performance issues, build failures
    MEDIUM = 3      # Code quality, documentation
    LOW = 4         # Optimization suggestions, cleanup


@dataclass
class HookTrigger:
    """Defines the conditions under which a hook is triggered."""
    event_types: Set[EventType]
    filter_group: Optional[EventFilterGroup] = None


@dataclass
class HookContext:
    """
    Context information provided to hooks during execution.
    
    Contains all relevant information about the triggering event,
    project state, system metrics, and user preferences.
    """
    trigger_event: Dict[str, Any]
    project_state: Dict[str, Any]
    system_metrics: Dict[str, Any]
    user_preferences: Dict[str, Any]
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    def with_updated_metrics(self, metrics: Dict[str, Any]) -> "HookContext":
        """Create a new context with updated system metrics."""
        return HookContext(
            trigger_event=self.trigger_event,
            project_state=self.project_state,
            system_metrics={**self.system_metrics, **metrics},
            user_preferences=self.user_preferences,
            execution_history=self.execution_history,
            execution_id=self.execution_id,
            timestamp=datetime.now()
        )
    
    def with_execution_record(self, record: Dict[str, Any]) -> "HookContext":
        """Create a new context with an additional execution history record."""
        return HookContext(
            trigger_event=self.trigger_event,
            project_state=self.project_state,
            system_metrics=self.system_metrics,
            user_preferences=self.user_preferences,
            execution_history=self.execution_history + [record],
            execution_id=self.execution_id,
            timestamp=datetime.now()
        )


@dataclass
class HookResult:
    """
    Result of a hook execution.
    
    Contains information about the success or failure of the hook,
    actions taken, suggestions for the user, and performance metrics.
    """
    success: bool
    message: str
    actions_taken: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    execution_time_ms: Optional[float] = None
    error: Optional[Exception] = None
    
    @classmethod
    def success_result(cls, message: str, **kwargs) -> "HookResult":
        """Create a successful result with the given message."""
        return cls(success=True, message=message, **kwargs)
    
    @classmethod
    def error_result(cls, message: str, error: Optional[Exception] = None, **kwargs) -> "HookResult":
        """Create an error result with the given message and exception."""
        return cls(success=False, message=message, error=error, **kwargs)
    
    def with_execution_time(self, execution_time_ms: float) -> "HookResult":
        """Add execution time to the result."""
        return HookResult(
            success=self.success,
            message=self.message,
            actions_taken=self.actions_taken,
            suggestions=self.suggestions,
            metrics=self.metrics,
            artifacts=self.artifacts,
            execution_time_ms=execution_time_ms,
            error=self.error
        )


class AgentHook(ABC):
    """
    Abstract base class for all agent hooks.
    
    Defines the interface that all hooks must implement, including
    methods for determining if the hook should execute, executing
    the hook, and getting resource requirements.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the hook with the given configuration.
        
        Args:
            config: Hook configuration dictionary
        """
        self.config = config
        self.id = config.get("id", str(uuid4()))
        self.name = config.get("name", self.__class__.__name__)
        self.description = config.get("description", "")
        self.priority = HookPriority(config.get("priority", HookPriority.MEDIUM.value))
        trigger_config = config.get("trigger", {})
        self.trigger = HookTrigger(
            event_types={EventType(et) for et in trigger_config.get("event_types", [])},
            filter_group=EventFilterGroup.from_dict(trigger_config.get("filter_group")) if trigger_config.get("filter_group") else None
        )
        self.enabled = config.get("enabled", True)
        self.timeout_seconds = config.get("timeout_seconds", 30)
        self.max_retries = config.get("max_retries", 3)
    
    @abstractmethod
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute given the current context.
        
        Args:
            context: Current execution context
            
        Returns:
            True if the hook should execute, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook and return results.
        
        Args:
            context: Current execution context
            
        Returns:
            Result of the hook execution
        """
        pass
    
    @abstractmethod
    def get_resource_requirements(self) -> Dict[str, Any]:
        """
        Return resource requirements for execution.
        
        Returns:
            Dictionary of resource requirements (CPU, memory, etc.)
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the hook."""
        return f"{self.name} ({self.id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the hook."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, enabled={self.enabled}, priority={self.priority})"
