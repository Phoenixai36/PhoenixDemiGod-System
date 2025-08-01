"""
Unit tests for TODO Generator
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.phoenix_system_review.reporting.todo_generator import (
    TODOGenerator, TODOChecklist, TaskCategory, TaskType, TaskDependency
)
from src.phoenix_system_review.models.data_models import (
    Priority, TaskStatus, ComponentCategory, ImpactLevel
)
from src.phoenix_system_review.assessment.gap_analyzer import (
    IdentifiedGap, GapAnalysisResult, GapType, GapSeverity
)
from src.phoenix_system_review.assessment.priority_ranker import (
    PriorityScore, PriorityRankingResult, PriorityLevel, EffortLevel
)
from src.phoenix_system_review.assessment.completion_calculator import CompletionTier


class TestTODOGenerator:
    """Test cases for TODOGenerator"""
    
    @pytest.fixture
    def todo_generator(self):
        """Create TODO generator instance"""
        return TODOGenerator()
    
    @pytest.fixture
    def sample_gaps(self):
        """Create sample identified gaps"""
        return [
            IdentifiedGap(
                gap_id="missing_api",
                component_name="nca_toolkit_api",
                gap_type=GapType.MISSING_COMPONENT,
                severity=GapSeverity.CRITICAL,
                title="Missing NCA Toolkit API",
                description="NCA Toolkit API component is missing",
                current_state="Component not found",
                expected_state="API should be implemented",
                impact_description="Missing API affects core functionality",
                effort_estimate_hours=64,
                category=ComponentCategory.INFRASTRUCTURE,
                dependencies=[],
                acceptance_criteria=["API endpoints implemented", "Health checks working"]
            ),
            IdentifiedGap(
                gap_id="incomplete_auth",
                component_name="authentication",
                gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                severity=GapSeverity.HIGH,
                title="Incomplete authentication",
                description="Authentication system is incomplete",
                current_state="Partially implemented",
                expected_state="Fully functional authentication",
                impact_description="Security vulnerability",
                effort_estimate_hours=32,
                category=ComponentCategory.SECURITY,
                dependencies=["database"],
                acceptance_criteria=["Authentication working", "Security audit passed"]
            )
        ]
    
    @pytest.fixture
    def sample_priority_scores(self):
        """Create sample priority scores"""
        return [
            PriorityScore(
                component_name="revenue_tracking",
                priority_level=PriorityLevel.CRITICAL,
                priority_score=85.0,
                business_impact_score=90.0,
                technical_complexity_score=60.0,
                dependency_urgency_score=70.0,
                effort_estimate=EffortLevel.MEDIUM,
                effort_hours=48,
                roi_score=75.0,
                risk_factor=0.8,
                completion_tier=CompletionTier.CRITICAL,
                justification="High business impact; Critical for revenue",
                dependencies=["database"],
                blockers=[]
            ),
            PriorityScore(
                component_name="documentation",
                priority_level=PriorityLevel.LOW,
                priority_score=30.0,
                business_impact_score=25.0,
                technical_complexity_score=20.0,
                dependency_urgency_score=15.0,
                effort_estimate=EffortLevel.LOW,
                effort_hours=16,
                roi_score=40.0,
                risk_factor=0.2,
                completion_tier=CompletionTier.OPTIONAL,
                justification="Low business impact; Nice to have",
                dependencies=[],
                blockers=[]
            )
        ]
    
    @pytest.fixture
    def sample_gap_analysis(self, sample_gaps):
        """Create sample gap analysis result"""
        return GapAnalysisResult(
            identified_gaps=sample_gaps,
            gap_summary={"missing_component": 1, "incomplete_implementation": 1},
            critical_gaps=[sample_gaps[0]],
            missing_components=["nca_toolkit_api"],
            incomplete_implementations=["authentication"],
            configuration_gaps=[],
            total_effort_estimate=96,
            completion_blockers=[sample_gaps[0]],
            recommendations=["Implement missing API", "Complete authentication"]
        )
    
    @pytest.fixture
    def sample_priority_ranking(self, sample_priority_scores):
        """Create sample priority ranking result"""
        return PriorityRankingResult(
            priority_scores=sample_priority_scores,
            priority_matrix={
                "critical": [sample_priority_scores[0]],
                "low": [sample_priority_scores[1]]
            },
            effort_distribution={"medium": 1, "low": 1},
            critical_path=["revenue_tracking"],
            quick_wins=["documentation"],
            high_impact_items=[sample_priority_scores[0]],
            recommendations=["Focus on revenue tracking", "Quick win with documentation"],
            total_estimated_effort=64
        )
    
    def test_generate_todo_checklist(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test TODO checklist generation"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        
        assert isinstance(checklist, TODOChecklist)
        assert len(checklist.tasks) > 0
        assert checklist.total_tasks > 0
        assert checklist.total_effort_hours > 0
        assert len(checklist.category_summary) > 0
        assert len(checklist.priority_summary) > 0
    
    def test_generate_tasks_from_gaps(self, todo_generator, sample_gaps):
        """Test task generation from gaps"""
        tasks = todo_generator._generate_tasks_from_gaps(sample_gaps)
        
        assert len(tasks) >= len(sample_gaps)  # May include subtasks
        
        # Check main tasks (tasks that don't have "_sub_" in their ID)
        main_tasks = [task for task in tasks if "_sub_" not in task.id]
        assert len(main_tasks) == len(sample_gaps)
        
        # Check task properties
        for task in main_tasks:
            assert task.id.startswith("gap_")
            assert task.title is not None
            assert task.description is not None
            assert task.priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
            assert task.status == TaskStatus.NOT_STARTED
            assert task.effort_hours > 0
    
    def test_generate_tasks_from_priorities(self, todo_generator, sample_priority_scores):
        """Test task generation from priority scores"""
        tasks = todo_generator._generate_tasks_from_priorities(sample_priority_scores)
        
        assert len(tasks) <= len(sample_priority_scores)  # May skip complete components
        
        for task in tasks:
            assert task.id.startswith("priority_")
            assert task.title is not None
            assert task.description is not None
            assert task.priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
            assert task.effort_hours > 0
    
    def test_merge_and_deduplicate_tasks(self, todo_generator, sample_gaps, sample_priority_scores):
        """Test task merging and deduplication"""
        gap_tasks = todo_generator._generate_tasks_from_gaps(sample_gaps)
        priority_tasks = todo_generator._generate_tasks_from_priorities(sample_priority_scores)
        
        merged_tasks = todo_generator._merge_and_deduplicate_tasks(gap_tasks, priority_tasks)
        
        # Should have gap tasks plus non-duplicate priority tasks
        assert len(merged_tasks) >= len(gap_tasks)
        
        # Check for duplicates by component name
        component_names = []
        for task in merged_tasks:
            component_name = todo_generator._extract_component_name_from_task(task)
            if component_name:
                component_names.append(component_name)
        
        # Should not have duplicate component names
        assert len(component_names) == len(set(component_names))
    
    def test_create_task_hierarchy(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test task hierarchy creation"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        hierarchy = checklist.task_hierarchy
        
        assert isinstance(hierarchy, dict)
        assert len(hierarchy) == len(checklist.tasks)
        
        # Check hierarchy structure
        for task_id, task_hierarchy in hierarchy.items():
            assert hasattr(task_hierarchy, 'parent_task')
            assert hasattr(task_hierarchy, 'child_tasks')
            assert hasattr(task_hierarchy, 'level')
            assert hasattr(task_hierarchy, 'category')
    
    def test_generate_task_dependencies(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test task dependency generation"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        dependencies = checklist.task_dependencies
        
        assert isinstance(dependencies, list)
        
        for dep in dependencies:
            assert isinstance(dep, TaskDependency)
            assert dep.task_id is not None
            assert dep.dependency_id is not None
            assert dep.dependency_type in ["blocks", "requires", "follows"]
            assert dep.description is not None
    
    def test_format_checklist_markdown(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test markdown formatting"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        markdown = todo_generator.format_checklist_markdown(checklist)
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "# Phoenix Hydra System Completion TODO Checklist" in markdown
        assert "## Summary" in markdown
        assert "## Tasks" in markdown
        
        # Check for task formatting
        assert "- [ ]" in markdown or "- [x]" in markdown or "- [-]" in markdown
        
        # Check for priority icons
        priority_icons = ["🔴", "🟠", "🟡", "🟢"]
        assert any(icon in markdown for icon in priority_icons)
    
    def test_calculate_summaries(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test summary calculations"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        
        # Category summary
        assert isinstance(checklist.category_summary, dict)
        assert sum(checklist.category_summary.values()) == checklist.total_tasks
        
        # Priority summary
        assert isinstance(checklist.priority_summary, dict)
        assert sum(checklist.priority_summary.values()) == checklist.total_tasks
        
        # Effort summary
        assert isinstance(checklist.effort_summary, dict)
        assert checklist.effort_summary["total_hours"] == checklist.total_effort_hours
    
    def test_identify_critical_path_tasks(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test critical path identification"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        critical_path = checklist.critical_path
        
        assert isinstance(critical_path, list)
        assert len(critical_path) <= 10  # Should be limited to top 10
        
        # Critical path should contain task IDs
        for task_id in critical_path:
            assert any(task.id == task_id for task in checklist.tasks)
    
    def test_identify_quick_win_tasks(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test quick win identification"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        quick_wins = checklist.quick_wins
        
        assert isinstance(quick_wins, list)
        assert len(quick_wins) <= 10  # Should be limited to top 10
        
        # Quick wins should be low effort, high priority tasks
        for task_id in quick_wins:
            task = next((t for t in checklist.tasks if t.id == task_id), None)
            assert task is not None
            assert task.effort_hours <= 16  # Low effort
            assert task.priority in [Priority.HIGH, Priority.CRITICAL]  # High priority
    
    def test_extract_component_name_from_task(self, todo_generator):
        """Test component name extraction from task"""
        from src.phoenix_system_review.models.data_models import TODOTask
        
        # Test gap task
        gap_task = TODOTask(
            id="gap_missing_nca_toolkit",
            title="Test task",
            description="Test",
            category="Infrastructure",
            priority=Priority.HIGH,
            status=TaskStatus.NOT_STARTED,
            effort_hours=8
        )
        
        component_name = todo_generator._extract_component_name_from_task(gap_task)
        assert component_name == "nca_toolkit"
        
        # Test priority task
        priority_task = TODOTask(
            id="priority_revenue_tracking",
            title="Test task",
            description="Test",
            category="Monetization",
            priority=Priority.CRITICAL,
            status=TaskStatus.NOT_STARTED,
            effort_hours=16
        )
        
        component_name = todo_generator._extract_component_name_from_task(priority_task)
        assert component_name == "revenue_tracking"
    
    def test_determine_task_category_from_component(self, todo_generator):
        """Test task category determination"""
        # Test infrastructure components
        assert todo_generator._determine_task_category_from_component("api_service") == TaskCategory.INFRASTRUCTURE.value
        assert todo_generator._determine_task_category_from_component("database_config") == TaskCategory.INFRASTRUCTURE.value
        
        # Test monetization components
        assert todo_generator._determine_task_category_from_component("revenue_tracking") == TaskCategory.MONETIZATION.value
        assert todo_generator._determine_task_category_from_component("affiliate_system") == TaskCategory.MONETIZATION.value
        
        # Test security components
        assert todo_generator._determine_task_category_from_component("authentication") == TaskCategory.SECURITY.value
        assert todo_generator._determine_task_category_from_component("security_config") == TaskCategory.SECURITY.value
        
        # Test default category
        assert todo_generator._determine_task_category_from_component("unknown_component") == TaskCategory.INFRASTRUCTURE.value
    
    def test_priority_sort_key(self, todo_generator):
        """Test priority sorting"""
        assert todo_generator._priority_sort_key(Priority.CRITICAL) == 0
        assert todo_generator._priority_sort_key(Priority.HIGH) == 1
        assert todo_generator._priority_sort_key(Priority.MEDIUM) == 2
        assert todo_generator._priority_sort_key(Priority.LOW) == 3
    
    def test_get_priority_icon(self, todo_generator):
        """Test priority icon generation"""
        assert todo_generator._get_priority_icon(Priority.CRITICAL) == "🔴"
        assert todo_generator._get_priority_icon(Priority.HIGH) == "🟠"
        assert todo_generator._get_priority_icon(Priority.MEDIUM) == "🟡"
        assert todo_generator._get_priority_icon(Priority.LOW) == "🟢"
    
    def test_get_status_icon(self, todo_generator):
        """Test status icon generation"""
        assert todo_generator._get_status_icon(TaskStatus.COMPLETE) == "x"
        assert todo_generator._get_status_icon(TaskStatus.IN_PROGRESS) == "-"
        assert todo_generator._get_status_icon(TaskStatus.NOT_STARTED) == " "
    
    def test_estimate_completion_date(self, todo_generator, sample_gap_analysis, sample_priority_ranking):
        """Test completion date estimation"""
        checklist = todo_generator.generate_todo_checklist(sample_gap_analysis, sample_priority_ranking)
        
        if checklist.estimated_completion_date:
            assert isinstance(checklist.estimated_completion_date, datetime)
            assert checklist.estimated_completion_date > datetime.now()
    
    def test_error_handling(self, todo_generator):
        """Test error handling in TODO generation"""
        # Test with empty inputs
        empty_gap_analysis = GapAnalysisResult()
        empty_priority_ranking = PriorityRankingResult()
        
        checklist = todo_generator.generate_todo_checklist(empty_gap_analysis, empty_priority_ranking)
        
        assert isinstance(checklist, TODOChecklist)
        assert checklist.total_tasks == 0
        assert checklist.total_effort_hours == 0
    
    def test_task_templates(self, todo_generator):
        """Test task templates are properly defined"""
        templates = todo_generator.task_templates
        
        assert isinstance(templates, dict)
        assert GapType.MISSING_COMPONENT in templates
        assert GapType.INCOMPLETE_IMPLEMENTATION in templates
        assert GapType.CONFIGURATION_GAP in templates
        
        # Check template structure
        for gap_type, template in templates.items():
            assert "title_format" in template
            if "subtasks" in template:
                for subtask in template["subtasks"]:
                    assert "title" in subtask
                    assert "effort_hours" in subtask
    
    def test_category_mappings(self, todo_generator):
        """Test category mappings are properly defined"""
        mappings = todo_generator.category_mappings
        
        assert isinstance(mappings, dict)
        assert ComponentCategory.INFRASTRUCTURE in mappings
        assert ComponentCategory.MONETIZATION in mappings
        assert ComponentCategory.SECURITY in mappings
        
        # Check all mappings are valid task categories
        for component_category, task_category in mappings.items():
            assert task_category in [tc.value for tc in TaskCategory]


if __name__ == "__main__":
    pytest.main([__file__])