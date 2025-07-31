"""
Unit tests for Data Models
"""

import pytest
from datetime import datetime, timedelta

from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, EvaluationResult,
    Issue, Priority, Gap, ImpactLevel, TODOTask, TaskStatus,
    CompletionScore, ProjectInventory, ServiceRegistry, DependencyGraph,
    AssessmentResults, EvaluationCriterion, CriterionType
)


class TestComponent:
    """Test cases for Component data model"""
    
    def test_component_creation(self):
        """Test creating a component with required fields"""
        component = Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test"
        )
        
        assert component.name == "test-component"
        assert component.category == ComponentCategory.INFRASTRUCTURE
        assert component.path == "/src/test"
        assert component.dependencies == []
        assert component.configuration == {}
        assert component.status == ComponentStatus.UNKNOWN
    
    def test_component_with_optional_fields(self):
        """Test creating a component with optional fields"""
        now = datetime.now()
        component = Component(
            name="full-component",
            category=ComponentCategory.MONETIZATION,
            path="/src/monetization",
            dependencies=["database", "storage"],
            configuration={"port": 8080, "debug": True},
            status=ComponentStatus.OPERATIONAL,
            description="A test component",
            version="1.0.0",
            last_updated=now
        )
        
        assert component.dependencies == ["database", "storage"]
        assert component.configuration["port"] == 8080
        assert component.status == ComponentStatus.OPERATIONAL
        assert component.description == "A test component"
        assert component.version == "1.0.0"
        assert component.last_updated == now


class TestEvaluationResult:
    """Test cases for EvaluationResult data model"""
    
    @pytest.fixture
    def sample_component(self):
        """Create a sample component for testing"""
        return Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test"
        )
    
    def test_evaluation_result_creation(self, sample_component):
        """Test creating an evaluation result"""
        result = EvaluationResult(
            component=sample_component,
            criteria_met=["criterion1", "criterion2"],
            criteria_missing=["criterion3"],
            completion_percentage=66.7,
            quality_score=80.0
        )
        
        assert result.component == sample_component
        assert len(result.criteria_met) == 2
        assert len(result.criteria_missing) == 1
        assert result.completion_percentage == 66.7
        assert result.quality_score == 80.0
        assert isinstance(result.evaluation_timestamp, datetime)
    
    def test_is_complete_property(self, sample_component):
        """Test the is_complete property"""
        complete_result = EvaluationResult(
            component=sample_component,
            criteria_met=["criterion1", "criterion2"],
            criteria_missing=[],
            completion_percentage=100.0
        )
        
        incomplete_result = EvaluationResult(
            component=sample_component,
            criteria_met=["criterion1"],
            criteria_missing=["criterion2"],
            completion_percentage=50.0
        )
        
        assert complete_result.is_complete is True
        assert incomplete_result.is_complete is False
    
    def test_has_critical_issues_property(self, sample_component):
        """Test the has_critical_issues property"""
        critical_issue = Issue(
            severity=Priority.CRITICAL,
            description="Critical security vulnerability",
            component="test-component"
        )
        
        minor_issue = Issue(
            severity=Priority.LOW,
            description="Minor documentation issue",
            component="test-component"
        )
        
        result_with_critical = EvaluationResult(
            component=sample_component,
            issues=[critical_issue, minor_issue]
        )
        
        result_without_critical = EvaluationResult(
            component=sample_component,
            issues=[minor_issue]
        )
        
        assert result_with_critical.has_critical_issues is True
        assert result_without_critical.has_critical_issues is False


class TestGap:
    """Test cases for Gap data model"""
    
    def test_gap_creation(self):
        """Test creating a gap with required fields"""
        gap = Gap(
            component="test-component",
            description="Missing feature X",
            impact=ImpactLevel.HIGH,
            effort_estimate=16
        )
        
        assert gap.component == "test-component"
        assert gap.description == "Missing feature X"
        assert gap.impact == ImpactLevel.HIGH
        assert gap.effort_estimate == 16
        assert gap.category == ComponentCategory.INFRASTRUCTURE  # default
        assert gap.priority == Priority.MEDIUM  # default
    
    def test_effort_days_property(self):
        """Test the effort_days property"""
        gap = Gap(
            component="test",
            description="Test gap",
            impact=ImpactLevel.MEDIUM,
            effort_estimate=24  # 3 days
        )
        
        assert gap.effort_days == 3.0
        
        gap_with_partial_day = Gap(
            component="test",
            description="Test gap",
            impact=ImpactLevel.MEDIUM,
            effort_estimate=12  # 1.5 days
        )
        
        assert gap_with_partial_day.effort_days == 1.5


class TestTODOTask:
    """Test cases for TODOTask data model"""
    
    def test_todo_task_creation(self):
        """Test creating a TODO task"""
        task = TODOTask(
            id="task-1",
            title="Implement feature X",
            description="Add feature X to the system",
            category="infrastructure",
            priority=Priority.HIGH,
            status=TaskStatus.NOT_STARTED,
            effort_hours=16
        )
        
        assert task.id == "task-1"
        assert task.title == "Implement feature X"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.NOT_STARTED
        assert task.effort_hours == 16
        assert isinstance(task.created_date, datetime)
    
    def test_effort_days_property(self):
        """Test the effort_days property"""
        task = TODOTask(
            id="task-1",
            title="Test task",
            description="Test description",
            category="test",
            priority=Priority.MEDIUM,
            status=TaskStatus.NOT_STARTED,
            effort_hours=32  # 4 days
        )
        
        assert task.effort_days == 4.0
    
    def test_is_blocked_property(self):
        """Test the is_blocked property"""
        blocked_task = TODOTask(
            id="task-1",
            title="Blocked task",
            description="This task is blocked",
            category="test",
            priority=Priority.MEDIUM,
            status=TaskStatus.NOT_STARTED,
            effort_hours=8,
            dependencies=["task-0"]
        )
        
        unblocked_task = TODOTask(
            id="task-2",
            title="Unblocked task",
            description="This task is not blocked",
            category="test",
            priority=Priority.MEDIUM,
            status=TaskStatus.NOT_STARTED,
            effort_hours=8,
            dependencies=[]
        )
        
        in_progress_task = TODOTask(
            id="task-3",
            title="In progress task",
            description="This task is in progress",
            category="test",
            priority=Priority.MEDIUM,
            status=TaskStatus.IN_PROGRESS,
            effort_hours=8,
            dependencies=["task-0"]
        )
        
        assert blocked_task.is_blocked is True
        assert unblocked_task.is_blocked is False
        assert in_progress_task.is_blocked is False  # In progress tasks are not blocked


class TestCompletionScore:
    """Test cases for CompletionScore data model"""
    
    def test_completion_score_creation(self):
        """Test creating a completion score"""
        score = CompletionScore(
            component_name="test-component",
            completion_percentage=85.5,
            weighted_score=82.0,
            criteria_total=10,
            criteria_met=8,
            quality_score=90.0
        )
        
        assert score.component_name == "test-component"
        assert score.completion_percentage == 85.5
        assert score.weighted_score == 82.0
        assert score.criteria_total == 10
        assert score.criteria_met == 8
        assert score.quality_score == 90.0
        assert isinstance(score.last_updated, datetime)


class TestProjectInventory:
    """Test cases for ProjectInventory data model"""
    
    def test_project_inventory_creation(self):
        """Test creating a project inventory"""
        component = Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test"
        )
        
        inventory = ProjectInventory(
            components=[component],
            total_files=100,
            total_directories=20,
            configuration_files=["config.yaml", "settings.json"],
            source_files=["main.py", "utils.py"],
            documentation_files=["README.md", "API.md"]
        )
        
        assert len(inventory.components) == 1
        assert inventory.total_files == 100
        assert inventory.total_directories == 20
        assert len(inventory.configuration_files) == 2
        assert len(inventory.source_files) == 2
        assert len(inventory.documentation_files) == 2
        assert isinstance(inventory.scan_timestamp, datetime)


class TestServiceRegistry:
    """Test cases for ServiceRegistry data model"""
    
    def test_service_registry_creation(self):
        """Test creating a service registry"""
        registry = ServiceRegistry(
            services={
                "n8n": {"port": 5678, "status": "running"},
                "windmill": {"port": 8000, "status": "stopped"}
            },
            health_checks={
                "n8n": True,
                "windmill": False
            },
            endpoints={
                "n8n": "http://localhost:5678",
                "windmill": "http://localhost:8000"
            }
        )
        
        assert len(registry.services) == 2
        assert registry.services["n8n"]["port"] == 5678
        assert registry.health_checks["n8n"] is True
        assert registry.health_checks["windmill"] is False
        assert registry.endpoints["n8n"] == "http://localhost:5678"
        assert isinstance(registry.last_check, datetime)


class TestDependencyGraph:
    """Test cases for DependencyGraph data model"""
    
    def test_dependency_graph_creation(self):
        """Test creating a dependency graph"""
        graph = DependencyGraph(
            nodes=["component_a", "component_b", "component_c"],
            edges=[("component_a", "component_b"), ("component_b", "component_c")],
            circular_dependencies=[["component_x", "component_y", "component_x"]]
        )
        
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2
        assert ("component_a", "component_b") in graph.edges
        assert len(graph.circular_dependencies) == 1
        assert len(graph.circular_dependencies[0]) == 3


class TestAssessmentResults:
    """Test cases for AssessmentResults data model"""
    
    def test_assessment_results_creation(self):
        """Test creating assessment results"""
        score = CompletionScore(
            component_name="test-component",
            completion_percentage=85.0,
            weighted_score=82.0,
            criteria_total=10,
            criteria_met=8,
            quality_score=90.0
        )
        
        gap = Gap(
            component="test-component",
            description="Missing feature",
            impact=ImpactLevel.HIGH,
            effort_estimate=16
        )
        
        task = TODOTask(
            id="task-1",
            title="Fix gap",
            description="Fix the missing feature",
            category="infrastructure",
            priority=Priority.HIGH,
            status=TaskStatus.NOT_STARTED,
            effort_hours=16
        )
        
        results = AssessmentResults(
            overall_completion=85.0,
            component_scores={"test-component": score},
            identified_gaps=[gap],
            prioritized_tasks=[task],
            recommendations=["Fix the gap", "Improve quality"]
        )
        
        assert results.overall_completion == 85.0
        assert len(results.component_scores) == 1
        assert len(results.identified_gaps) == 1
        assert len(results.prioritized_tasks) == 1
        assert len(results.recommendations) == 2
        assert isinstance(results.assessment_timestamp, datetime)
    
    def test_critical_gaps_property(self):
        """Test the critical_gaps property"""
        critical_gap = Gap(
            component="critical-component",
            description="Critical issue",
            impact=ImpactLevel.CRITICAL,
            effort_estimate=8
        )
        
        medium_gap = Gap(
            component="medium-component",
            description="Medium issue",
            impact=ImpactLevel.MEDIUM,
            effort_estimate=4
        )
        
        results = AssessmentResults(
            overall_completion=80.0,
            identified_gaps=[critical_gap, medium_gap]
        )
        
        critical_gaps = results.critical_gaps
        assert len(critical_gaps) == 1
        assert critical_gaps[0].impact == ImpactLevel.CRITICAL
    
    def test_high_priority_tasks_property(self):
        """Test the high_priority_tasks property"""
        critical_task = TODOTask(
            id="task-1",
            title="Critical task",
            description="Critical task description",
            category="security",
            priority=Priority.CRITICAL,
            status=TaskStatus.NOT_STARTED,
            effort_hours=8
        )
        
        high_task = TODOTask(
            id="task-2",
            title="High priority task",
            description="High priority task description",
            category="infrastructure",
            priority=Priority.HIGH,
            status=TaskStatus.NOT_STARTED,
            effort_hours=16
        )
        
        low_task = TODOTask(
            id="task-3",
            title="Low priority task",
            description="Low priority task description",
            category="documentation",
            priority=Priority.LOW,
            status=TaskStatus.NOT_STARTED,
            effort_hours=4
        )
        
        results = AssessmentResults(
            overall_completion=80.0,
            prioritized_tasks=[critical_task, high_task, low_task]
        )
        
        high_priority_tasks = results.high_priority_tasks
        assert len(high_priority_tasks) == 2
        assert all(task.priority in [Priority.CRITICAL, Priority.HIGH] for task in high_priority_tasks)


class TestEvaluationCriterion:
    """Test cases for EvaluationCriterion data model"""
    
    def test_evaluation_criterion_creation(self):
        """Test creating an evaluation criterion"""
        criterion = EvaluationCriterion(
            id="api_endpoints",
            name="API Endpoints",
            description="Component has properly defined API endpoints",
            criterion_type=CriterionType.FUNCTIONALITY,
            weight=1.0,
            is_critical=True,
            evaluation_method="automated",
            parameters={"endpoint_count": 5, "response_time_ms": 200}
        )
        
        assert criterion.id == "api_endpoints"
        assert criterion.name == "API Endpoints"
        assert criterion.criterion_type == CriterionType.FUNCTIONALITY
        assert criterion.weight == 1.0
        assert criterion.is_critical is True
        assert criterion.evaluation_method == "automated"
        assert criterion.parameters["endpoint_count"] == 5


if __name__ == '__main__':
    pytest.main([__file__])