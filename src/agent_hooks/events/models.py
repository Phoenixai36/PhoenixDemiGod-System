"""
Event data models and schemas for the Agent Hooks Enhancement system.

This module defines the data models for various event types that can trigger hooks,
including file system events, system performance events, and development lifecycle events.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from uuid import uuid4

from pydantic import BaseModel, Field, validator, root_validator


class EventType(str, Enum):
    """Types of events that can trigger hooks."""
    # File system events
    FILE_SAVE = "file_save"
    FILE_CREATE = "file_create"
    FILE_DELETE = "file_delete"
    FILE_RENAME = "file_rename"
    FILE_MODIFY = "file_modify"
    DIRECTORY_CREATE = "directory_create"
    DIRECTORY_DELETE = "directory_delete"
    
    # System performance events
    METRIC_THRESHOLD = "metric_threshold"
    CONTAINER_START = "container_start"
    CONTAINER_STOP = "container_stop"
    CONTAINER_RESTART = "container_restart"
    SERVICE_HEALTH = "service_health"
    RESOURCE_USAGE = "resource_usage"
    
    # Development lifecycle events
    BUILD_START = "build_start"
    BUILD_SUCCESS = "build_success"
    BUILD_FAILURE = "build_failure"
    TEST_START = "test_start"
    TEST_SUCCESS = "test_success"
    TEST_FAILURE = "test_failure"
    DEPLOYMENT_START = "deployment_start"
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILURE = "deployment_failure"
    
    # Git events
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"
    GIT_BRANCH = "git_branch"
    GIT_MERGE = "git_merge"
    
    # Dependency events
    DEPENDENCY_ADD = "dependency_add"
    DEPENDENCY_REMOVE = "dependency_remove"
    DEPENDENCY_UPDATE = "dependency_update"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"
    
    # Manual and time-based events
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    
    # Custom events
    CUSTOM = "custom"


class EventSeverity(str, Enum):
    """Severity levels for events."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BaseEvent(BaseModel):
    """
    Base model for all events in the system.
    
    Contains common fields that all events should have, such as ID, timestamp,
    source, type, and context information.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(..., description="Event source component")
    type: EventType = Field(..., description="Event type")
    data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = Field(None, description="For event chaining")
    severity: EventSeverity = Field(default=EventSeverity.INFO)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: list,
            Path: str
        }
    
    def to_json(self) -> str:
        """Convert the event to a JSON string."""
        return json.dumps(self.dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "BaseEvent":
        """Create an event from a JSON string."""
        data = json.loads(json_str)
        return cls(**data)
    
    def with_correlation(self, correlation_id: str) -> "BaseEvent":
        """Create a new event with the specified correlation ID."""
        return self.copy(update={"correlation_id": correlation_id})
    
    def with_context(self, context: Dict[str, Any]) -> "BaseEvent":
        """Create a new event with additional context."""
        new_context = {**self.context, **context}
        return self.copy(update={"context": new_context})


class FileEvent(BaseEvent):
    """
    Event related to file system changes.
    
    Contains information about file operations such as save, create, delete, etc.
    """
    file_path: Path
    file_type: str
    operation: str  # save, create, delete, modify, rename
    content_hash: Optional[str] = None
    size_bytes: Optional[int] = None
    old_path: Optional[Path] = None  # For rename operations
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate that the operation is a valid file operation."""
        valid_operations = {"save", "create", "delete", "modify", "rename"}
        if v not in valid_operations:
            raise ValueError(f"Invalid file operation: {v}")
        return v
    
    @validator("file_type")
    def validate_file_type(cls, v, values):
        """Derive file type from file path if not provided."""
        if not v and "file_path" in values:
            file_path = values["file_path"]
            return file_path.suffix.lstrip(".") if file_path.suffix else "unknown"
        return v
    
    @root_validator
    def validate_rename_operation(cls, values):
        """Validate that old_path is provided for rename operations."""
        operation = values.get("operation")
        old_path = values.get("old_path")
        
        if operation == "rename" and old_path is None:
            raise ValueError("old_path must be provided for rename operations")
        
        return values
    
    @classmethod
    def create_save_event(cls, file_path: Union[str, Path], content_hash: Optional[str] = None, **kwargs) -> "FileEvent":
        """Create a file save event."""
        return cls(
            source="file_system",
            type=EventType.FILE_SAVE,
            file_path=Path(file_path),
            file_type=Path(file_path).suffix.lstrip(".") or "unknown",
            operation="save",
            content_hash=content_hash,
            **kwargs
        )
    
    @classmethod
    def create_create_event(cls, file_path: Union[str, Path], **kwargs) -> "FileEvent":
        """Create a file creation event."""
        return cls(
            source="file_system",
            type=EventType.FILE_CREATE,
            file_path=Path(file_path),
            file_type=Path(file_path).suffix.lstrip(".") or "unknown",
            operation="create",
            **kwargs
        )
    
    @classmethod
    def create_delete_event(cls, file_path: Union[str, Path], **kwargs) -> "FileEvent":
        """Create a file deletion event."""
        return cls(
            source="file_system",
            type=EventType.FILE_DELETE,
            file_path=Path(file_path),
            file_type=Path(file_path).suffix.lstrip(".") or "unknown",
            operation="delete",
            **kwargs
        )
    
    @classmethod
    def create_modify_event(cls, file_path: Union[str, Path], content_hash: Optional[str] = None, **kwargs) -> "FileEvent":
        """Create a file modification event."""
        return cls(
            source="file_system",
            type=EventType.FILE_MODIFY,
            file_path=Path(file_path),
            file_type=Path(file_path).suffix.lstrip(".") or "unknown",
            operation="modify",
            content_hash=content_hash,
            **kwargs
        )
    
    @classmethod
    def create_rename_event(cls, old_path: Union[str, Path], new_path: Union[str, Path], **kwargs) -> "FileEvent":
        """Create a file rename event."""
        return cls(
            source="file_system",
            type=EventType.FILE_RENAME,
            file_path=Path(new_path),
            file_type=Path(new_path).suffix.lstrip(".") or "unknown",
            operation="rename",
            old_path=Path(old_path),
            **kwargs
        )


class MetricThreshold(BaseModel):
    """Threshold configuration for a metric."""
    value: float
    comparison: str = Field(..., description="gt, lt, gte, lte, eq, neq")
    duration_seconds: Optional[int] = None
    
    @validator("comparison")
    def validate_comparison(cls, v):
        """Validate that the comparison is valid."""
        valid_comparisons = {"gt", "lt", "gte", "lte", "eq", "neq"}
        if v not in valid_comparisons:
            raise ValueError(f"Invalid comparison: {v}")
        return v
    
    def is_exceeded(self, value: float, duration: Optional[int] = None) -> bool:
        """Check if the threshold is exceeded."""
        if self.comparison == "gt":
            result = value > self.value
        elif self.comparison == "lt":
            result = value < self.value
        elif self.comparison == "gte":
            result = value >= self.value
        elif self.comparison == "lte":
            result = value <= self.value
        elif self.comparison == "eq":
            result = value == self.value
        elif self.comparison == "neq":
            result = value != self.value
        else:
            result = False
        
        # If duration is specified, both the threshold value and duration must be exceeded
        if self.duration_seconds is not None and duration is not None:
            return result and duration >= self.duration_seconds
        
        return result


class MetricEvent(BaseEvent):
    """
    Event related to system metrics.
    
    Contains information about metric values, thresholds, and related context.
    """
    metric_name: str
    value: float
    threshold: Optional[MetricThreshold] = None
    duration_seconds: Optional[int] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    
    @classmethod
    def create_threshold_event(
        cls,
        metric_name: str,
        value: float,
        threshold_value: float,
        comparison: str = "gt",
        duration_seconds: Optional[int] = None,
        **kwargs
    ) -> "MetricEvent":
        """Create a metric threshold event."""
        threshold = MetricThreshold(
            value=threshold_value,
            comparison=comparison,
            duration_seconds=duration_seconds
        )
        
        severity = EventSeverity.INFO
        if comparison in ("gt", "gte") and value >= threshold_value * 1.5:
            severity = EventSeverity.CRITICAL
        elif comparison in ("gt", "gte") and value >= threshold_value * 1.2:
            severity = EventSeverity.HIGH
        elif comparison in ("gt", "gte") and value >= threshold_value:
            severity = EventSeverity.MEDIUM
        
        return cls(
            source="metrics",
            type=EventType.METRIC_THRESHOLD,
            metric_name=metric_name,
            value=value,
            threshold=threshold,
            duration_seconds=duration_seconds,
            severity=severity,
            **kwargs
        )


class SystemEvent(BaseEvent):
    """
    Event related to system components and services.
    
    Contains information about system state changes, service health, etc.
    """
    component: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)
    affected_services: List[str] = Field(default_factory=list)
    
    @classmethod
    def create_service_health_event(
        cls,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        affected_services: Optional[List[str]] = None,
        **kwargs
    ) -> "SystemEvent":
        """Create a service health event."""
        severity = EventSeverity.INFO
        if status.lower() in ("down", "failed", "error", "critical"):
            severity = EventSeverity.CRITICAL
        elif status.lower() in ("degraded", "warning", "unstable"):
            severity = EventSeverity.HIGH
        
        return cls(
            source="system",
            type=EventType.SERVICE_HEALTH,
            component=component,
            status=status,
            details=details or {},
            affected_services=affected_services or [],
            severity=severity,
            **kwargs
        )


class GitEvent(BaseEvent):
    """
    Event related to Git operations.
    
    Contains information about Git commits, branches, merges, etc.
    """
    repository: str
    branch: str
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    message: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    
    @classmethod
    def create_commit_event(
        cls,
        repository: str,
        branch: str,
        commit_hash: str,
        author: str,
        message: str,
        files_changed: List[str],
        **kwargs
    ) -> "GitEvent":
        """Create a Git commit event."""
        return cls(
            source="git",
            type=EventType.GIT_COMMIT,
            repository=repository,
            branch=branch,
            commit_hash=commit_hash,
            author=author,
            message=message,
            files_changed=files_changed,
            **kwargs
        )


class BuildEvent(BaseEvent):
    """
    Event related to build processes.
    
    Contains information about build starts, successes, failures, etc.
    """
    project: str
    build_id: str
    build_type: str
    duration_seconds: Optional[float] = None
    artifacts: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    @classmethod
    def create_build_success_event(
        cls,
        project: str,
        build_id: str,
        build_type: str,
        duration_seconds: float,
        artifacts: List[str],
        **kwargs
    ) -> "BuildEvent":
        """Create a build success event."""
        return cls(
            source="build",
            type=EventType.BUILD_SUCCESS,
            project=project,
            build_id=build_id,
            build_type=build_type,
            duration_seconds=duration_seconds,
            artifacts=artifacts,
            **kwargs
        )
    
    @classmethod
    def create_build_failure_event(
        cls,
        project: str,
        build_id: str,
        build_type: str,
        duration_seconds: float,
        errors: List[str],
        **kwargs
    ) -> "BuildEvent":
        """Create a build failure event."""
        return cls(
            source="build",
            type=EventType.BUILD_FAILURE,
            project=project,
            build_id=build_id,
            build_type=build_type,
            duration_seconds=duration_seconds,
            errors=errors,
            severity=EventSeverity.HIGH,
            **kwargs
        )


class DependencyEvent(BaseEvent):
    """
    Event related to project dependencies.
    
    Contains information about dependency additions, removals, updates, etc.
    """
    package_name: str
    package_version: Optional[str] = None
    previous_version: Optional[str] = None
    package_type: str  # npm, pip, etc.
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    
    @classmethod
    def create_vulnerability_event(
        cls,
        package_name: str,
        package_version: str,
        package_type: str,
        vulnerabilities: List[Dict[str, Any]],
        **kwargs
    ) -> "DependencyEvent":
        """Create a dependency vulnerability event."""
        # Determine severity based on vulnerability severity
        max_severity = max(
            (v.get("severity", "low") for v in vulnerabilities),
            key=lambda s: {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(s.lower(), 0),
            default="low"
        )
        
        event_severity = EventSeverity.INFO
        if max_severity.lower() == "critical":
            event_severity = EventSeverity.CRITICAL
        elif max_severity.lower() == "high":
            event_severity = EventSeverity.HIGH
        elif max_severity.lower() == "medium":
            event_severity = EventSeverity.MEDIUM
        elif max_severity.lower() == "low":
            event_severity = EventSeverity.LOW
        
        return cls(
            source="dependencies",
            type=EventType.DEPENDENCY_VULNERABILITY,
            package_name=package_name,
            package_version=package_version,
            package_type=package_type,
            vulnerabilities=vulnerabilities,
            severity=event_severity,
            **kwargs
        )


class EventSerializer:
    """
    Utility class for serializing and deserializing events.
    
    Provides methods for converting events to and from various formats,
    such as JSON, dictionaries, and database records.
    """
    
    @staticmethod
    def serialize(event: BaseEvent) -> Dict[str, Any]:
        """
        Serialize an event to a dictionary.
        
        Args:
            event: Event to serialize
            
        Returns:
            Dictionary representation of the event
        """
        return event.dict()
    
    @staticmethod
    def deserialize(data: Dict[str, Any]) -> BaseEvent:
        """
        Deserialize a dictionary to an event.
        
        Args:
            data: Dictionary representation of the event
            
        Returns:
            Deserialized event
            
        Raises:
            ValueError: If the event type is unknown
        """
        event_type = data.get("type")
        
        if not event_type:
            raise ValueError("Event data must include a 'type' field")
        
        # Convert string event type to enum if needed
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
                data["type"] = event_type
            except ValueError:
                pass
        
        # Determine the appropriate event class based on the event type
        if event_type in {
            EventType.FILE_SAVE, EventType.FILE_CREATE, EventType.FILE_DELETE,
            EventType.FILE_RENAME, EventType.FILE_MODIFY, EventType.DIRECTORY_CREATE,
            EventType.DIRECTORY_DELETE
        }:
            # Convert string paths to Path objects
            if "file_path" in data and isinstance(data["file_path"], str):
                data["file_path"] = Path(data["file_path"])
            if "old_path" in data and isinstance(data["old_path"], str):
                data["old_path"] = Path(data["old_path"])
            
            return FileEvent(**data)
        
        elif event_type in {
            EventType.METRIC_THRESHOLD, EventType.RESOURCE_USAGE
        }:
            return MetricEvent(**data)
        
        elif event_type in {
            EventType.SERVICE_HEALTH, EventType.CONTAINER_START,
            EventType.CONTAINER_STOP, EventType.CONTAINER_RESTART
        }:
            return SystemEvent(**data)
        
        elif event_type in {
            EventType.GIT_COMMIT, EventType.GIT_PUSH, EventType.GIT_PULL,
            EventType.GIT_BRANCH, EventType.GIT_MERGE
        }:
            return GitEvent(**data)
        
        elif event_type in {
            EventType.BUILD_START, EventType.BUILD_SUCCESS, EventType.BUILD_FAILURE,
            EventType.TEST_START, EventType.TEST_SUCCESS, EventType.TEST_FAILURE,
            EventType.DEPLOYMENT_START, EventType.DEPLOYMENT_SUCCESS, EventType.DEPLOYMENT_FAILURE
        }:
            return BuildEvent(**data)
        
        elif event_type in {
            EventType.DEPENDENCY_ADD, EventType.DEPENDENCY_REMOVE,
            EventType.DEPENDENCY_UPDATE, EventType.DEPENDENCY_VULNERABILITY
        }:
            return DependencyEvent(**data)
        
        else:
            # Default to BaseEvent for unknown event types
            return BaseEvent(**data)
    
    @staticmethod
    def to_json(event: BaseEvent) -> str:
        """
        Serialize an event to a JSON string.
        
        Args:
            event: Event to serialize
            
        Returns:
            JSON string representation of the event
        """
        return event.json()
    
    @staticmethod
    def from_json(json_str: str) -> BaseEvent:
        """
        Deserialize a JSON string to an event.
        
        Args:
            json_str: JSON string representation of the event
            
        Returns:
            Deserialized event
            
        Raises:
            ValueError: If the JSON string is invalid or the event type is unknown
        """
        try:
            data = json.loads(json_str)
            return EventSerializer.deserialize(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")


class EventValidator:
    """
    Utility class for validating events.
    
    Provides methods for checking if events are valid according to various rules,
    such as required fields, field types, and business logic constraints.
    """
    
    @staticmethod
    def validate(event: BaseEvent) -> List[str]:
        """
        Validate an event.
        
        Args:
            event: Event to validate
            
        Returns:
            List of validation error messages, empty if the event is valid
        """
        errors = []
        
        # Check required fields
        if not event.source:
            errors.append("Event source is required")
        
        if not event.type:
            errors.append("Event type is required")
        
        # Validate specific event types
        if isinstance(event, FileEvent):
            errors.extend(EventValidator._validate_file_event(event))
        elif isinstance(event, MetricEvent):
            errors.extend(EventValidator._validate_metric_event(event))
        elif isinstance(event, SystemEvent):
            errors.extend(EventValidator._validate_system_event(event))
        elif isinstance(event, GitEvent):
            errors.extend(EventValidator._validate_git_event(event))
        elif isinstance(event, BuildEvent):
            errors.extend(EventValidator._validate_build_event(event))
        elif isinstance(event, DependencyEvent):
            errors.extend(EventValidator._validate_dependency_event(event))
        
        return errors
    
    @staticmethod
    def _validate_file_event(event: FileEvent) -> List[str]:
        """Validate a file event."""
        errors = []
        
        if not event.file_path:
            errors.append("File path is required")
        
        if not event.operation:
            errors.append("File operation is required")
        
        if event.operation == "rename" and not event.old_path:
            errors.append("Old path is required for rename operations")
        
        return errors
    
    @staticmethod
    def _validate_metric_event(event: MetricEvent) -> List[str]:
        """Validate a metric event."""
        errors = []
        
        if not event.metric_name:
            errors.append("Metric name is required")
        
        return errors
    
    @staticmethod
    def _validate_system_event(event: SystemEvent) -> List[str]:
        """Validate a system event."""
        errors = []
        
        if not event.component:
            errors.append("Component is required")
        
        if not event.status:
            errors.append("Status is required")
        
        return errors
    
    @staticmethod
    def _validate_git_event(event: GitEvent) -> List[str]:
        """Validate a git event."""
        errors = []
        
        if not event.repository:
            errors.append("Repository is required")
        
        if not event.branch:
            errors.append("Branch is required")
        
        return errors
    
    @staticmethod
    def _validate_build_event(event: BuildEvent) -> List[str]:
        """Validate a build event."""
        errors = []
        
        if not event.project:
            errors.append("Project is required")
        
        if not event.build_id:
            errors.append("Build ID is required")
        
        if not event.build_type:
            errors.append("Build type is required")
        
        return errors
    
    @staticmethod
    def _validate_dependency_event(event: DependencyEvent) -> List[str]:
        """Validate a dependency event."""
        errors = []
        
        if not event.package_name:
            errors.append("Package name is required")
        
        if not event.package_type:
            errors.append("Package type is required")
        
        return errors
