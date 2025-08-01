"""
TODO Generator for Phoenix Hydra System Review Tool

Implements hierarchical task list generation from identified gaps,
creates task prioritization and effort estimation, and adds dependency tracking
and prerequisite identification.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import uuid

from ..models.data_models import (
    Gap, TODOTask, Priority, TaskStatus, ComponentCategory, ImpactLevel
)
from ..assessment.gap_analyzer import IdentifiedGap, GapAnalysisResult, GapType, GapSeverity
from ..assessment.priority_ranker import PriorityScore, PriorityRankingResult, PriorityLevel, EffortLevel


class TaskCategory(Enum):
    """Categories for TODO tasks"""
    INFRASTRUCTURE = "Infrastructure"
    MONETIZATION = "Monetization"
    AUTOMATION = "Automation"
    DOCUMENTATION = "Documentation"
    TESTING = "Testing"
    SECURITY = "Security"
    INTEGRATION = "Integration"
    CONFIGURATION = "Configuration"


class TaskType(Enum):
    """Types of TODO tasks"""
    IMPLEMENTATION = "implementation"
    CONFIGURATION = "configuration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


@dataclass
class TaskDependency:
    """Represents a dependency between tasks"""
    task_id: str
    dependency_id: str
    dependency_type: str  # "blocks", "requires", "follows"
    description: str


@dataclass
class TaskHierarchy:
    """Represents hierarchical task structure"""
    parent_task: Optional[TODOTask]
    child_tasks: List[TODOTask] = field(default_factory=list)
    level: int = 0
    category: TaskCategory = TaskCategory.INFRASTRUCTURE


@dataclass
class TODOChecklist:
    """Complete TODO checklist with hierarchical structure"""
    tasks: List[TODOTask] = field(default_factory=list)
    task_hierarchy: Dict[str, TaskHierarchy] = field(default_factory=dict)
    task_dependencies: List[TaskDependency] = field(default_factory=list)
    category_summary: Dict[str, int] = field(default_factory=dict)
    priority_summary: Dict[str, int] = field(default_factory=dict)
    effort_summary: Dict[str, int] = field(default_factory=dict)
    total_tasks: int = 0
    total_effort_hours: int = 0
    estimated_completion_date: Optional[datetime] = None
    critical_path: List[str] = field(default_factory=list)
    quick_wins: List[str] = field(default_factory=list)
    generated_timestamp: datetime = field(default_factory=datetime.now)


class TODOGenerator:
    """
    Generates hierarchical TODO checklists from identified gaps and priority rankings.
    
    Creates actionable tasks with effort estimates, dependencies, and acceptance criteria
    to guide Phoenix Hydra system completion.
    """
    
    def __init__(self):
        """Initialize TODO generator"""
        self.logger = logging.getLogger(__name__)
        
        # Task templates for different gap types
        self.task_templates = self._define_task_templates()
        
        # Category mappings
        self.category_mappings = self._define_category_mappings()
        
        # Effort estimation rules
        self.effort_rules = self._define_effort_rules()
        
        # Dependency rules
        self.dependency_rules = self._define_dependency_rules()
    
    def generate_todo_checklist(self, 
                               gap_analysis: GapAnalysisResult,
                               priority_ranking: PriorityRankingResult) -> TODOChecklist:
        """
        Generate comprehensive TODO checklist from gaps and priorities.
        
        Args:
            gap_analysis: Results from gap analysis
            priority_ranking: Results from priority ranking
            
        Returns:
            TODOChecklist with hierarchical tasks and dependencies
        """
        try:
            # Generate tasks from gaps
            gap_tasks = self._generate_tasks_from_gaps(gap_analysis.identified_gaps)
            
            # Generate tasks from priority scores
            priority_tasks = self._generate_tasks_from_priorities(priority_ranking.priority_scores)
            
            # Merge and deduplicate tasks
            all_tasks = self._merge_and_deduplicate_tasks(gap_tasks, priority_tasks)
            
            # Create task hierarchy
            task_hierarchy = self._create_task_hierarchy(all_tasks)
            
            # Generate task dependencies
            task_dependencies = self._generate_task_dependencies(all_tasks, priority_ranking)
            
            # Calculate summaries
            category_summary = self._calculate_category_summary(all_tasks)
            priority_summary = self._calculate_priority_summary(all_tasks)
            effort_summary = self._calculate_effort_summary(all_tasks)
            
            # Calculate totals
            total_tasks = len(all_tasks)
            total_effort_hours = sum(task.effort_hours for task in all_tasks)
            
            # Estimate completion date
            estimated_completion = self._estimate_completion_date(all_tasks, task_dependencies)
            
            # Identify critical path and quick wins
            critical_path = self._identify_critical_path_tasks(all_tasks, task_dependencies)
            quick_wins = self._identify_quick_win_tasks(all_tasks)
            
            return TODOChecklist(
                tasks=all_tasks,
                task_hierarchy=task_hierarchy,
                task_dependencies=task_dependencies,
                category_summary=category_summary,
                priority_summary=priority_summary,
                effort_summary=effort_summary,
                total_tasks=total_tasks,
                total_effort_hours=total_effort_hours,
                estimated_completion_date=estimated_completion,
                critical_path=critical_path,
                quick_wins=quick_wins
            )
            
        except Exception as e:
            self.logger.error(f"Error generating TODO checklist: {e}")
            return TODOChecklist()
    
    def format_checklist_markdown(self, checklist: TODOChecklist) -> str:
        """
        Format TODO checklist as hierarchical markdown.
        
        Args:
            checklist: TODOChecklist to format
            
        Returns:
            Formatted markdown string
        """
        try:
            lines = []
            
            # Header
            lines.append("# Phoenix Hydra System Completion TODO Checklist")
            lines.append("")
            lines.append(f"Generated: {checklist.generated_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Total Tasks: {checklist.total_tasks}")
            lines.append(f"Total Effort: {checklist.total_effort_hours} hours ({checklist.total_effort_hours / 8:.1f} days)")
            
            if checklist.estimated_completion_date:
                lines.append(f"Estimated Completion: {checklist.estimated_completion_date.strftime('%Y-%m-%d')}")
            
            lines.append("")
            
            # Summary section
            lines.append("## Summary")
            lines.append("")
            
            # Priority summary
            lines.append("### By Priority")
            for priority, count in checklist.priority_summary.items():
                lines.append(f"- {priority.title()}: {count} tasks")
            lines.append("")
            
            # Category summary
            lines.append("### By Category")
            for category, count in checklist.category_summary.items():
                lines.append(f"- {category}: {count} tasks")
            lines.append("")
            
            # Quick wins
            if checklist.quick_wins:
                lines.append("### Quick Wins (High Impact, Low Effort)")
                for task_id in checklist.quick_wins[:5]:
                    task = next((t for t in checklist.tasks if t.id == task_id), None)
                    if task:
                        lines.append(f"- {task.title} ({task.effort_hours}h)")
                lines.append("")
            
            # Critical path
            if checklist.critical_path:
                lines.append("### Critical Path")
                for task_id in checklist.critical_path[:5]:
                    task = next((t for t in checklist.tasks if t.id == task_id), None)
                    if task:
                        lines.append(f"- {task.title}")
                lines.append("")
            
            # Tasks by category
            lines.append("## Tasks")
            lines.append("")
            
            # Group tasks by category
            tasks_by_category = {}
            for task in checklist.tasks:
                category = task.category
                if category not in tasks_by_category:
                    tasks_by_category[category] = []
                tasks_by_category[category].append(task)
            
            # Sort categories by importance
            category_order = [
                TaskCategory.INFRASTRUCTURE.value,
                TaskCategory.MONETIZATION.value,
                TaskCategory.SECURITY.value,
                TaskCategory.AUTOMATION.value,
                TaskCategory.TESTING.value,
                TaskCategory.DOCUMENTATION.value,
                TaskCategory.INTEGRATION.value,
                TaskCategory.CONFIGURATION.value
            ]
            
            for category in category_order:
                if category in tasks_by_category:
                    lines.append(f"### {category}")
                    lines.append("")
                    
                    # Sort tasks by priority within category
                    category_tasks = sorted(
                        tasks_by_category[category],
                        key=lambda t: self._priority_sort_key(t.priority)
                    )
                    
                    for task in category_tasks:
                        # Task checkbox with priority indicator
                        priority_icon = self._get_priority_icon(task.priority)
                        status_icon = self._get_status_icon(task.status)
                        
                        lines.append(f"- [{status_icon}] {priority_icon} **{task.title}** ({task.effort_hours}h)")
                        
                        # Task description
                        if task.description:
                            lines.append(f"  - {task.description}")
                        
                        # Dependencies
                        if task.dependencies:
                            lines.append(f"  - **Dependencies:** {', '.join(task.dependencies)}")
                        
                        # Acceptance criteria
                        if task.acceptance_criteria:
                            lines.append("  - **Acceptance Criteria:**")
                            for criterion in task.acceptance_criteria:
                                lines.append(f"    - {criterion}")
                        
                        lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Error formatting checklist markdown: {e}")
            return "# Error generating TODO checklist"
    
    def _generate_tasks_from_gaps(self, gaps: List[IdentifiedGap]) -> List[TODOTask]:
        """Generate TODO tasks from identified gaps"""
        tasks = []
        
        for gap in gaps:
            # Get task template for gap type
            template = self.task_templates.get(gap.gap_type, self.task_templates[GapType.INCOMPLETE_IMPLEMENTATION])
            
            # Create main task
            task_id = f"gap_{gap.gap_id}"
            
            # Map gap severity to priority
            priority_mapping = {
                GapSeverity.CRITICAL: Priority.CRITICAL,
                GapSeverity.HIGH: Priority.HIGH,
                GapSeverity.MEDIUM: Priority.MEDIUM,
                GapSeverity.LOW: Priority.LOW
            }
            
            # Map component category to task category
            task_category = self.category_mappings.get(gap.category, TaskCategory.INFRASTRUCTURE.value)
            
            main_task = TODOTask(
                id=task_id,
                title=template["title_format"].format(component=gap.component_name),
                description=gap.description,
                category=task_category,
                priority=priority_mapping[gap.severity],
                status=TaskStatus.NOT_STARTED,
                effort_hours=gap.effort_estimate_hours,
                dependencies=gap.dependencies.copy(),
                acceptance_criteria=gap.acceptance_criteria.copy()
            )
            
            tasks.append(main_task)
            
            # Generate subtasks if template defines them
            if "subtasks" in template:
                for i, subtask_template in enumerate(template["subtasks"]):
                    subtask_id = f"{task_id}_sub_{i+1}"
                    
                    subtask = TODOTask(
                        id=subtask_id,
                        title=subtask_template["title"].format(component=gap.component_name),
                        description=subtask_template.get("description", ""),
                        category=task_category,
                        priority=main_task.priority,
                        status=TaskStatus.NOT_STARTED,
                        effort_hours=subtask_template.get("effort_hours", 8),
                        dependencies=[task_id] if subtask_template.get("depends_on_parent", True) else [],
                        acceptance_criteria=subtask_template.get("acceptance_criteria", [])
                    )
                    
                    tasks.append(subtask)
        
        return tasks
    
    def _generate_tasks_from_priorities(self, priority_scores: List[PriorityScore]) -> List[TODOTask]:
        """Generate TODO tasks from priority scores"""
        tasks = []
        
        for score in priority_scores:
            # Skip if already at high completion
            if score.completion_tier.value in ["complete", "excellent"]:
                continue
            
            task_id = f"priority_{score.component_name}"
            
            # Map priority level to Priority enum
            priority_mapping = {
                PriorityLevel.CRITICAL: Priority.CRITICAL,
                PriorityLevel.HIGH: Priority.HIGH,
                PriorityLevel.MEDIUM: Priority.MEDIUM,
                PriorityLevel.LOW: Priority.LOW
            }
            
            # Determine task category from component name
            task_category = self._determine_task_category_from_component(score.component_name)
            
            task = TODOTask(
                id=task_id,
                title=f"Complete {score.component_name} implementation",
                description=f"Bring {score.component_name} to production readiness. {score.justification}",
                category=task_category,
                priority=priority_mapping[score.priority_level],
                status=TaskStatus.NOT_STARTED,
                effort_hours=score.effort_hours,
                dependencies=score.dependencies.copy(),
                acceptance_criteria=[
                    f"{score.component_name} passes all evaluation criteria",
                    f"Component reaches {score.completion_tier.value} completion tier",
                    "All critical issues resolved"
                ]
            )
            
            tasks.append(task)
        
        return tasks
    
    def _merge_and_deduplicate_tasks(self, gap_tasks: List[TODOTask], priority_tasks: List[TODOTask]) -> List[TODOTask]:
        """Merge and deduplicate tasks from different sources"""
        all_tasks = []
        seen_components = set()
        
        # Add gap tasks first (more specific)
        for task in gap_tasks:
            all_tasks.append(task)
            # Extract component name from task
            component_name = self._extract_component_name_from_task(task)
            if component_name:
                seen_components.add(component_name)
        
        # Add priority tasks that don't duplicate gap tasks
        for task in priority_tasks:
            component_name = self._extract_component_name_from_task(task)
            if component_name not in seen_components:
                all_tasks.append(task)
                seen_components.add(component_name)
        
        return all_tasks
    
    def _create_task_hierarchy(self, tasks: List[TODOTask]) -> Dict[str, TaskHierarchy]:
        """Create hierarchical task structure"""
        hierarchy = {}
        
        # Group tasks by category
        tasks_by_category = {}
        for task in tasks:
            category = task.category
            if category not in tasks_by_category:
                tasks_by_category[category] = []
            tasks_by_category[category].append(task)
        
        # Create hierarchy for each category
        for category, category_tasks in tasks_by_category.items():
            # Sort tasks by priority and dependencies
            sorted_tasks = sorted(
                category_tasks,
                key=lambda t: (self._priority_sort_key(t.priority), len(t.dependencies))
            )
            
            # Create parent-child relationships based on dependencies
            for task in sorted_tasks:
                task_hierarchy = TaskHierarchy(
                    parent_task=None,
                    child_tasks=[],
                    level=0,
                    category=TaskCategory(category) if isinstance(category, str) else category
                )
                
                # Find parent tasks (tasks this one depends on)
                for dep_id in task.dependencies:
                    parent_task = next((t for t in tasks if t.id == dep_id), None)
                    if parent_task:
                        task_hierarchy.parent_task = parent_task
                        task_hierarchy.level = 1
                        break
                
                # Find child tasks (tasks that depend on this one)
                for other_task in tasks:
                    if task.id in other_task.dependencies:
                        task_hierarchy.child_tasks.append(other_task)
                
                hierarchy[task.id] = task_hierarchy
        
        return hierarchy
    
    def _generate_task_dependencies(self, tasks: List[TODOTask], priority_ranking: PriorityRankingResult) -> List[TaskDependency]:
        """Generate task dependencies based on component relationships"""
        dependencies = []
        
        # Create lookup for priority scores
        priority_lookup = {score.component_name: score for score in priority_ranking.priority_scores}
        
        for task in tasks:
            component_name = self._extract_component_name_from_task(task)
            if not component_name:
                continue
            
            priority_score = priority_lookup.get(component_name)
            if not priority_score:
                continue
            
            # Add dependencies from priority score
            for dep_component in priority_score.dependencies:
                dep_task = next((t for t in tasks if self._extract_component_name_from_task(t) == dep_component), None)
                if dep_task and dep_task.id != task.id:
                    dependency = TaskDependency(
                        task_id=task.id,
                        dependency_id=dep_task.id,
                        dependency_type="requires",
                        description=f"{task.title} requires {dep_task.title} to be completed first"
                    )
                    dependencies.append(dependency)
            
            # Add blockers as critical dependencies
            for blocker_component in priority_score.blockers:
                blocker_task = next((t for t in tasks if self._extract_component_name_from_task(t) == blocker_component), None)
                if blocker_task and blocker_task.id != task.id:
                    dependency = TaskDependency(
                        task_id=task.id,
                        dependency_id=blocker_task.id,
                        dependency_type="blocks",
                        description=f"{blocker_task.title} blocks {task.title} and must be resolved first"
                    )
                    dependencies.append(dependency)
        
        return dependencies
    
    def _calculate_category_summary(self, tasks: List[TODOTask]) -> Dict[str, int]:
        """Calculate task count by category"""
        summary = {}
        for task in tasks:
            category = task.category
            summary[category] = summary.get(category, 0) + 1
        return summary
    
    def _calculate_priority_summary(self, tasks: List[TODOTask]) -> Dict[str, int]:
        """Calculate task count by priority"""
        summary = {}
        for task in tasks:
            priority = task.priority.value
            summary[priority] = summary.get(priority, 0) + 1
        return summary
    
    def _calculate_effort_summary(self, tasks: List[TODOTask]) -> Dict[str, int]:
        """Calculate effort distribution"""
        summary = {
            "total_hours": sum(task.effort_hours for task in tasks),
            "total_days": sum(task.effort_hours for task in tasks) / 8,
            "by_priority": {}
        }
        
        for task in tasks:
            priority = task.priority.value
            if priority not in summary["by_priority"]:
                summary["by_priority"][priority] = 0
            summary["by_priority"][priority] += task.effort_hours
        
        return summary
    
    def _estimate_completion_date(self, tasks: List[TODOTask], dependencies: List[TaskDependency]) -> Optional[datetime]:
        """Estimate completion date based on tasks and dependencies"""
        try:
            # Simple estimation: assume 8 hours per day, 5 days per week
            total_hours = sum(task.effort_hours for task in tasks)
            working_days = total_hours / 8
            calendar_days = working_days * 1.4  # Account for weekends and overhead
            
            completion_date = datetime.now() + timedelta(days=calendar_days)
            return completion_date
            
        except Exception as e:
            self.logger.error(f"Error estimating completion date: {e}")
            return None
    
    def _identify_critical_path_tasks(self, tasks: List[TODOTask], dependencies: List[TaskDependency]) -> List[str]:
        """Identify tasks on the critical path"""
        critical_tasks = []
        
        # Find tasks with critical priority
        critical_priority_tasks = [task.id for task in tasks if task.priority == Priority.CRITICAL]
        critical_tasks.extend(critical_priority_tasks)
        
        # Find tasks that block many others
        blocking_count = {}
        for dep in dependencies:
            if dep.dependency_type == "blocks":
                blocking_count[dep.dependency_id] = blocking_count.get(dep.dependency_id, 0) + 1
        
        # Add tasks that block 2 or more other tasks
        high_blocking_tasks = [task_id for task_id, count in blocking_count.items() if count >= 2]
        critical_tasks.extend(high_blocking_tasks)
        
        # Remove duplicates and limit to top 10
        return list(set(critical_tasks))[:10]
    
    def _identify_quick_win_tasks(self, tasks: List[TODOTask]) -> List[str]:
        """Identify quick win tasks (low effort, high impact)"""
        quick_wins = []
        
        for task in tasks:
            # Quick wins: <= 16 hours effort and high/critical priority
            if (task.effort_hours <= 16 and 
                task.priority in [Priority.HIGH, Priority.CRITICAL]):
                quick_wins.append(task.id)
        
        # Sort by effort (lowest first)
        quick_wins.sort(key=lambda task_id: next(
            task.effort_hours for task in tasks if task.id == task_id
        ))
        
        return quick_wins[:10]  # Top 10 quick wins
    
    # Helper methods
    def _extract_component_name_from_task(self, task: TODOTask) -> Optional[str]:
        """Extract component name from task ID or title"""
        if task.id.startswith("gap_"):
            # Extract from gap ID format: gap_gap_id where gap_id contains component name
            # Remove "gap_" prefix and return the rest
            gap_id = task.id.replace("gap_", "")
            # For gap IDs like "missing_api" or "incomplete_auth", extract the component part
            if gap_id.startswith("missing_"):
                return gap_id.replace("missing_", "")
            elif gap_id.startswith("incomplete_"):
                return gap_id.replace("incomplete_", "")
            else:
                # For other gap types, try to extract component name from the end
                parts = gap_id.split("_")
                if len(parts) >= 2:
                    return "_".join(parts[1:])  # Skip the gap type part
                return gap_id
        elif task.id.startswith("priority_"):
            # Extract from priority ID format: priority_component_name
            return task.id.replace("priority_", "")
        
        return None
    
    def _determine_task_category_from_component(self, component_name: str) -> str:
        """Determine task category from component name"""
        component_lower = component_name.lower()
        
        # Category keywords
        category_keywords = {
            TaskCategory.INFRASTRUCTURE.value: ["api", "database", "storage", "container", "podman", "service"],
            TaskCategory.MONETIZATION.value: ["revenue", "affiliate", "grant", "payment", "marketplace"],
            TaskCategory.AUTOMATION.value: ["workflow", "script", "deployment", "ci", "cd", "automation"],
            TaskCategory.SECURITY.value: ["auth", "security", "ssl", "certificate", "encryption"],
            TaskCategory.TESTING.value: ["test", "coverage", "quality", "validation"],
            TaskCategory.DOCUMENTATION.value: ["doc", "readme", "guide", "manual"],
            TaskCategory.INTEGRATION.value: ["integration", "webhook", "api", "connector"],
            TaskCategory.CONFIGURATION.value: ["config", "settings", "environment", "setup"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in component_lower for keyword in keywords):
                return category
        
        return TaskCategory.INFRASTRUCTURE.value  # Default category
    
    def _priority_sort_key(self, priority: Priority) -> int:
        """Get sort key for priority (lower number = higher priority)"""
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        return priority_order.get(priority, 4)
    
    def _get_priority_icon(self, priority: Priority) -> str:
        """Get icon for priority level"""
        icons = {
            Priority.CRITICAL: "🔴",
            Priority.HIGH: "🟠",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢"
        }
        return icons.get(priority, "⚪")
    
    def _get_status_icon(self, status: TaskStatus) -> str:
        """Get icon for task status"""
        icons = {
            TaskStatus.COMPLETE: "x",
            TaskStatus.IN_PROGRESS: "-",
            TaskStatus.NOT_STARTED: " "
        }
        return icons.get(status, " ")
    
    def _define_task_templates(self) -> Dict[GapType, Dict[str, Any]]:
        """Define task templates for different gap types"""
        return {
            GapType.MISSING_COMPONENT: {
                "title_format": "Implement missing {component} component",
                "subtasks": [
                    {
                        "title": "Design {component} architecture",
                        "description": "Create architectural design and specifications",
                        "effort_hours": 16,
                        "acceptance_criteria": ["Architecture documented", "Design reviewed"]
                    },
                    {
                        "title": "Implement {component} core functionality",
                        "description": "Develop core component functionality",
                        "effort_hours": 32,
                        "acceptance_criteria": ["Core functionality implemented", "Unit tests passing"]
                    },
                    {
                        "title": "Integrate {component} with system",
                        "description": "Integrate component with existing system",
                        "effort_hours": 16,
                        "acceptance_criteria": ["Integration complete", "Integration tests passing"]
                    }
                ]
            },
            GapType.INCOMPLETE_IMPLEMENTATION: {
                "title_format": "Complete {component} implementation",
                "subtasks": [
                    {
                        "title": "Identify {component} completion gaps",
                        "description": "Analyze what needs to be completed",
                        "effort_hours": 8,
                        "acceptance_criteria": ["Gaps identified", "Completion plan created"]
                    },
                    {
                        "title": "Implement missing {component} features",
                        "description": "Develop missing functionality",
                        "effort_hours": 24,
                        "acceptance_criteria": ["Missing features implemented", "Tests updated"]
                    }
                ]
            },
            GapType.CONFIGURATION_GAP: {
                "title_format": "Fix {component} configuration",
                "subtasks": [
                    {
                        "title": "Review {component} configuration requirements",
                        "description": "Analyze configuration needs",
                        "effort_hours": 4,
                        "acceptance_criteria": ["Requirements documented"]
                    },
                    {
                        "title": "Update {component} configuration",
                        "description": "Apply correct configuration",
                        "effort_hours": 8,
                        "acceptance_criteria": ["Configuration updated", "Validation passing"]
                    }
                ]
            },
            GapType.QUALITY_GAP: {
                "title_format": "Improve {component} code quality",
                "subtasks": [
                    {
                        "title": "Refactor {component} code",
                        "description": "Improve code quality and maintainability",
                        "effort_hours": 16,
                        "acceptance_criteria": ["Code quality improved", "Linting passing"]
                    },
                    {
                        "title": "Add {component} tests",
                        "description": "Increase test coverage",
                        "effort_hours": 12,
                        "acceptance_criteria": ["Test coverage > 80%", "All tests passing"]
                    }
                ]
            },
            GapType.SECURITY_GAP: {
                "title_format": "Secure {component} component",
                "subtasks": [
                    {
                        "title": "Implement {component} security measures",
                        "description": "Add authentication, authorization, and security controls",
                        "effort_hours": 20,
                        "acceptance_criteria": ["Security measures implemented", "Security audit passed"]
                    }
                ]
            },
            GapType.DOCUMENTATION_GAP: {
                "title_format": "Document {component} component",
                "subtasks": [
                    {
                        "title": "Create {component} documentation",
                        "description": "Write comprehensive documentation",
                        "effort_hours": 8,
                        "acceptance_criteria": ["Documentation complete", "Examples provided"]
                    }
                ]
            },
            GapType.TESTING_GAP: {
                "title_format": "Add {component} testing",
                "subtasks": [
                    {
                        "title": "Write {component} unit tests",
                        "description": "Create comprehensive unit tests",
                        "effort_hours": 12,
                        "acceptance_criteria": ["Unit tests written", "Coverage > 80%"]
                    },
                    {
                        "title": "Add {component} integration tests",
                        "description": "Create integration tests",
                        "effort_hours": 8,
                        "acceptance_criteria": ["Integration tests written", "All tests passing"]
                    }
                ]
            }
        }
    
    def _define_category_mappings(self) -> Dict[ComponentCategory, str]:
        """Define mappings from component categories to task categories"""
        return {
            ComponentCategory.INFRASTRUCTURE: TaskCategory.INFRASTRUCTURE.value,
            ComponentCategory.MONETIZATION: TaskCategory.MONETIZATION.value,
            ComponentCategory.AUTOMATION: TaskCategory.AUTOMATION.value,
            ComponentCategory.DOCUMENTATION: TaskCategory.DOCUMENTATION.value,
            ComponentCategory.TESTING: TaskCategory.TESTING.value,
            ComponentCategory.SECURITY: TaskCategory.SECURITY.value
        }
    
    def _define_effort_rules(self) -> Dict[str, int]:
        """Define effort estimation rules"""
        return {
            "missing_component": 64,      # 8 days for new component
            "incomplete_implementation": 32,  # 4 days to complete
            "configuration_gap": 8,       # 1 day for configuration
            "quality_gap": 16,           # 2 days for quality improvement
            "security_gap": 24,          # 3 days for security
            "documentation_gap": 8,      # 1 day for documentation
            "testing_gap": 16,           # 2 days for testing
            "integration_gap": 20        # 2.5 days for integration
        }
    
    def _define_dependency_rules(self) -> Dict[str, List[str]]:
        """Define dependency rules between components"""
        return {
            "database": [],  # No dependencies
            "storage": [],   # No dependencies
            "api": ["database", "storage"],  # APIs depend on data layers
            "authentication": ["database"],  # Auth depends on database
            "monitoring": ["api"],  # Monitoring depends on APIs
            "documentation": ["api"],  # Docs depend on APIs being complete
            "testing": ["api", "database"]  # Tests depend on core components
        }