"""
Data models for the Phoenix Hydra System Review tool.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class ComponentCategory(Enum):
    """Categories for system components"""

    INFRASTRUCTURE = "infrastructure"
    MONETIZATION = "monetization"
    AUTOMATION = "automation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"


class ComponentStatus(Enum):
    """Status of system components"""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Priority levels for tasks and issues"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Status of TODO tasks"""

    COMPLETE = "complete"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"


class ImpactLevel(Enum):
    """Impact levels for gaps and issues"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Issue:
    """Represents an issue found during evaluation"""

    severity: Priority
    description: str
    component: str


@dataclass
class Component:
    """Represents a system component."""

    name: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    component_type: str = "generic"
    details: Dict[str, Any] = field(default_factory=dict)
    category: ComponentCategory = ComponentCategory.INFRASTRUCTURE
    path: str = ""
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class ServiceRegistry:
    """Represents a registry of discovered services."""

    services: List[Component]

    def get_components(self) -> List[Component]:
        """Return the list of discovered components."""
        return self.services

    @property
    def service_count(self) -> int:
        """Return the number of discovered services."""
        return len(self.services)


@dataclass
class DependencyGraph:
    """Represents the dependency graph of components."""

    dependencies: Dict[str, List[str]] = field(default_factory=dict)

    def add_dependency(self, source: str, target: str):
        """Adds a dependency to the graph."""
        self.dependencies.setdefault(source, []).append(target)

    def get_dependencies(self, component_name: str) -> List[str]:
        """Gets the dependencies for a given component."""
        return self.dependencies.get(component_name, [])


@dataclass
class EvaluationResult:
    """Represents the result of a component evaluation."""

    component_name: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)
    component: Component = None
    criteria_met: List[str] = field(default_factory=list)
    criteria_missing: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0
    quality_score: float = 0.0
    issues: List[Issue] = field(default_factory=list)

    @property
    def has_critical_issues(self) -> bool:
        """Check if component has critical issues"""
        return any(issue.severity == Priority.CRITICAL for issue in self.issues)


@dataclass
class Gap:
    """Represents an identified gap in the system."""

    description: str
    component_name: str
    severity: str
    component: str = ""
    impact: ImpactLevel = ImpactLevel.MEDIUM
    effort_estimate: int = 8
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    category: ComponentCategory = ComponentCategory.INFRASTRUCTURE
    priority: Priority = Priority.MEDIUM


@dataclass
class CompletionScore:
    """Represents a completion score."""

    score: float
    breakdown: Dict[str, float]


@dataclass
class TODOTask:
    """Represents a task in the TODO checklist."""

    description: str
    priority: Priority = Priority.MEDIUM
    effort: int = 8
    id: str = ""
    title: str = ""
    category: str = ""
    status: TaskStatus = TaskStatus.NOT_STARTED
    effort_hours: int = 8
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class ProjectInventory:
    """Represents the inventory of a project."""

    files: List[str]
    directories: List[str]


@dataclass
class AssessmentResults:
    """Represents the final assessment results."""

    summary: str
    results: List[EvaluationResult]
    dependency_graph: DependencyGraph
    overall_completion: float = 0.0
    identified_gaps: List[Gap] = field(default_factory=list)
    prioritized_tasks: List[TODOTask] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
