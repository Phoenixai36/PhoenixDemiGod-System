"""
Data models for Phoenix Hydra System Review Tool
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class ComponentCategory(Enum):
    """Categories for Phoenix Hydra components"""
    INFRASTRUCTURE = "infrastructure"
    MONETIZATION = "monetization"
    AUTOMATION = "automation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"


class Priority(Enum):
    """Priority levels for tasks and issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Status indicators for tasks and components"""
    COMPLETE = "complete"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"


class ComponentStatus(Enum):
    """Status indicators for system components"""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ImpactLevel(Enum):
    """Impact levels for gaps and issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Component:
    """Represents a Phoenix Hydra system component"""
    name: str
    category: ComponentCategory
    path: str
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    status: ComponentStatus = ComponentStatus.UNKNOWN
    description: Optional[str] = None
    version: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass
class Issue:
    """Represents an issue found during component evaluation"""
    severity: Priority
    description: str
    component: str
    recommendation: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class EvaluationResult:
    """Results from evaluating a component against criteria"""
    component: Component
    criteria_met: List[str] = field(default_factory=list)
    criteria_missing: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0
    quality_score: float = 0.0
    issues: List[Issue] = field(default_factory=list)
    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_complete(self) -> bool:
        """Check if component meets all criteria"""
        return len(self.criteria_missing) == 0
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if component has critical issues"""
        return any(issue.severity == Priority.CRITICAL for issue in self.issues)


@dataclass
class Gap:
    """Represents a gap between current state and completion target"""
    component: str
    description: str
    impact: ImpactLevel
    effort_estimate: int  # hours
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    category: ComponentCategory = ComponentCategory.INFRASTRUCTURE
    priority: Priority = Priority.MEDIUM
    
    @property
    def effort_days(self) -> float:
        """Convert effort estimate to days (8 hours per day)"""
        return self.effort_estimate / 8.0


@dataclass
class TODOTask:
    """Represents a task in the TODO checklist"""
    id: str
    title: str
    description: str
    category: str
    priority: Priority
    status: TaskStatus
    effort_hours: int
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    created_date: datetime = field(default_factory=datetime.now)
    
    @property
    def effort_days(self) -> float:
        """Convert effort estimate to days"""
        return self.effort_hours / 8.0
    
    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies"""
        return len(self.dependencies) > 0 and self.status == TaskStatus.NOT_STARTED


@dataclass
class CompletionScore:
    """Represents completion scoring for a component or system"""
    component_name: str
    completion_percentage: float
    weighted_score: float
    criteria_total: int
    criteria_met: int
    quality_score: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ProjectInventory:
    """Inventory of all discovered project components"""
    components: List[Component] = field(default_factory=list)
    total_files: int = 0
    total_directories: int = 0
    configuration_files: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)
    scan_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceRegistry:
    """Registry of discovered services and their status"""
    services: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    health_checks: Dict[str, bool] = field(default_factory=dict)
    endpoints: Dict[str, str] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class DependencyGraph:
    """Represents component dependencies"""
    nodes: List[str] = field(default_factory=list)
    edges: List[tuple] = field(default_factory=list)  # (from, to) tuples
    circular_dependencies: List[List[str]] = field(default_factory=list)


@dataclass
class AssessmentResults:
    """Complete assessment results for the Phoenix Hydra system"""
    overall_completion: float
    component_scores: Dict[str, CompletionScore] = field(default_factory=dict)
    identified_gaps: List[Gap] = field(default_factory=list)
    prioritized_tasks: List[TODOTask] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessment_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def critical_gaps(self) -> List[Gap]:
        """Get gaps with critical impact"""
        return [gap for gap in self.identified_gaps if gap.impact == ImpactLevel.CRITICAL]
    
    @property
    def high_priority_tasks(self) -> List[TODOTask]:
        """Get high priority tasks"""
        return [task for task in self.prioritized_tasks if task.priority in [Priority.CRITICAL, Priority.HIGH]]