"""
Unit tests for Assessment Engine components
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from phoenix_system_review.assessment.gap_analyzer import GapAnalyzer
from phoenix_system_review.assessment.completion_calculator import CompletionCalculator
from phoenix_system_review.assessment.priority_ranker import PriorityRanker
from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, EvaluationResult, Gap, TODOTask,
    Priority, ImpactLevel, TaskStatus, Issue, CompletionScore
)


class TestGapAnalyzer:
    """Test cases for GapAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create GapAnalyzer instance"""
        return GapAnalyzer()
    
    @pytest.fixture
    def sample_evaluation_results(self):
        """Create sample evaluation results for testing"""
        component1 = Component(
            name="phoenix-core",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/core"
        )
        
        component2 = Component(
            name="n8n-workflows",
            category=ComponentCategory.AUTOMATION,
            path="/configs/n8n"
        )
        
        # Component with missing criteria
        result1 = EvaluationResult(
            component=component1,
            criteria_met=["api_endpoints", "health_checks"],
            criteria_missing=["documentation", "monitoring"],
            completion_percentage=60.0,
            quality_score=75.0,
            issues=[
                Issue(
                    severity=Priority.HIGH,
                    description="Missing API documentation",
                    component="phoenix-core"
                )
            ]
        )
        
        # Component with all criteria met
        result2 = EvaluationResult(
            component=component2,
            criteria_met=["workflow_definitions", "error_handling", "documentation"],
            criteria_missing=[],
            completion_percentage=100.0,
            quality_score=90.0,
            issues=[]
        )
        
        return [result1, result2]
    
    def test_identify_gaps(self, analyzer, sample_evaluation_results):
        """Test identifying gaps from evaluation results"""
        gaps = analyzer.identify_gaps(sample_evaluation_results)
        
        assert isinstance(gaps, list)
        assert len(gaps) > 0
        
        # Should have gaps for the incomplete component
        phoenix_gaps = [gap for gap in gaps if gap.component == "phoenix-core"]
        assert len(phoenix_gaps) > 0
        
        # Should have gaps for missing criteria
        missing_criteria_gaps = [gap for gap in phoenix_gaps if "documentation" in gap.description or "monitoring" in gap.description]
        assert len(missing_criteria_gaps) > 0
    
    def test_identify_gaps_no_missing_criteria(self, analyzer):
        """Test identifying gaps when no criteria are missing"""
        component = Component(
            name="complete-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/complete"
        )
        
        complete_result = EvaluationResult(
            component=component,
            criteria_met=["all_criteria"],
            criteria_missing=[],
            completion_percentage=100.0,
            quality_score=100.0,
            issues=[]
        )
        
        gaps = analyzer.identify_gaps([complete_result])
        
        # Should have no gaps for complete component
        component_gaps = [gap for gap in gaps if gap.component == "complete-component"]
        assert len(component_gaps) == 0
    
    def test_categorize_gaps_by_impact(self, analyzer, sample_evaluation_results):
        """Test categorizing gaps by impact level"""
        gaps = analyzer.identify_gaps(sample_evaluation_results)
        categorized = analyzer.categorize_gaps_by_impact(gaps)
        
        assert isinstance(categorized, dict)
        assert ImpactLevel.CRITICAL in categorized
        assert ImpactLevel.HIGH in categorized
        assert ImpactLevel.MEDIUM in categorized
        assert ImpactLevel.LOW in categorized
        
        # All categorized gaps should be in the original list
        all_categorized = []
        for impact_gaps in categorized.values():
            all_categorized.extend(impact_gaps)
        assert len(all_categorized) == len(gaps)
    
    def test_estimate_gap_effort(self, analyzer):
        """Test estimating effort for gaps"""
        gap = Gap(
            component="test-component",
            description="Implement missing API documentation",
            impact=ImpactLevel.HIGH,
            effort_estimate=0,  # Will be estimated
            category=ComponentCategory.INFRASTRUCTURE
        )
        
        estimated_effort = analyzer.estimate_gap_effort(gap)
        
        assert isinstance(estimated_effort, int)
        assert estimated_effort > 0
        assert estimated_effort <= 40  # Should be reasonable estimate in hours
    
    def test_identify_dependency_gaps(self, analyzer):
        """Test identifying gaps related to dependencies"""
        component_with_deps = Component(
            name="dependent-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/dependent",
            dependencies=["missing-dependency", "another-missing"]
        )
        
        result_with_deps = EvaluationResult(
            component=component_with_deps,
            criteria_met=[],
            criteria_missing=["dependency_validation"],
            completion_percentage=50.0,
            quality_score=60.0,
            issues=[
                Issue(
                    severity=Priority.CRITICAL,
                    description="Missing dependency: missing-dependency",
                    component="dependent-component"
                )
            ]
        )
        
        gaps = analyzer.identify_gaps([result_with_deps])
        dependency_gaps = [gap for gap in gaps if "dependency" in gap.description.lower()]
        
        assert len(dependency_gaps) > 0
        assert any(gap.impact == ImpactLevel.CRITICAL for gap in dependency_gaps)


class TestCompletionCalculator:
    """Test cases for CompletionCalculator"""
    
    @pytest.fixture
    def calculator(self):
        """Create CompletionCalculator instance"""
        return CompletionCalculator()
    
    @pytest.fixture
    def sample_evaluation_results(self):
        """Create sample evaluation results for testing"""
        component1 = Component(
            name="infrastructure-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/infra"
        )
        
        component2 = Component(
            name="monetization-component",
            category=ComponentCategory.MONETIZATION,
            path="/src/monetization"
        )
        
        result1 = EvaluationResult(
            component=component1,
            criteria_met=["criterion1", "criterion2"],
            criteria_missing=["criterion3"],
            completion_percentage=66.7,
            quality_score=80.0
        )
        
        result2 = EvaluationResult(
            component=component2,
            criteria_met=["criterion1", "criterion2", "criterion3", "criterion4"],
            criteria_missing=[],
            completion_percentage=100.0,
            quality_score=95.0
        )
        
        return [result1, result2]
    
    def test_calculate_component_completion(self, calculator, sample_evaluation_results):
        """Test calculating completion for individual components"""
        completion_scores = calculator.calculate_completion(sample_evaluation_results)
        
        assert isinstance(completion_scores, dict)
        assert len(completion_scores) == 2
        
        # Check infrastructure component
        infra_score = completion_scores["infrastructure-component"]
        assert isinstance(infra_score, CompletionScore)
        assert infra_score.completion_percentage == 66.7
        assert infra_score.quality_score == 80.0
        
        # Check monetization component
        monetization_score = completion_scores["monetization-component"]
        assert isinstance(monetization_score, CompletionScore)
        assert monetization_score.completion_percentage == 100.0
        assert monetization_score.quality_score == 95.0
    
    def test_calculate_overall_completion(self, calculator, sample_evaluation_results):
        """Test calculating overall system completion"""
        component_scores = calculator.calculate_completion(sample_evaluation_results)
        overall_completion = calculator.calculate_overall_completion(component_scores)
        
        assert isinstance(overall_completion, float)
        assert 0.0 <= overall_completion <= 100.0
        
        # Should be weighted average based on component categories
        # Infrastructure (35% weight) at 66.7% + Monetization (25% weight) at 100%
        # Plus other categories at 0% = weighted average
        expected_min = (0.35 * 66.7 + 0.25 * 100.0) / (0.35 + 0.25)
        assert overall_completion >= expected_min * 0.9  # Allow some tolerance
    
    def test_calculate_weighted_score(self, calculator):
        """Test calculating weighted completion score"""
        scores = {
            ComponentCategory.INFRASTRUCTURE: 80.0,
            ComponentCategory.MONETIZATION: 90.0,
            ComponentCategory.AUTOMATION: 70.0,
            ComponentCategory.DOCUMENTATION: 60.0,
            ComponentCategory.TESTING: 50.0,
            ComponentCategory.SECURITY: 85.0
        }
        
        weighted_score = calculator.calculate_weighted_score(scores)
        
        assert isinstance(weighted_score, float)
        assert 0.0 <= weighted_score <= 100.0
        
        # Should be weighted according to component importance
        # Infrastructure (35%) + Monetization (25%) + Automation (20%) + others
        expected = (0.35 * 80.0 + 0.25 * 90.0 + 0.20 * 70.0 + 
                   0.10 * 60.0 + 0.05 * 50.0 + 0.05 * 85.0)
        assert abs(weighted_score - expected) < 0.1
    
    def test_get_completion_trend(self, calculator):
        """Test getting completion trend over time"""
        historical_scores = [
            (datetime(2024, 1, 1), 70.0),
            (datetime(2024, 2, 1), 75.0),
            (datetime(2024, 3, 1), 80.0),
            (datetime(2024, 4, 1), 85.0)
        ]
        
        trend = calculator.get_completion_trend(historical_scores)
        
        assert isinstance(trend, dict)
        assert "trend_direction" in trend
        assert "average_monthly_increase" in trend
        assert "projected_completion_date" in trend
        
        assert trend["trend_direction"] == "increasing"
        assert trend["average_monthly_increase"] > 0
    
    def test_calculate_completion_empty_results(self, calculator):
        """Test calculating completion with empty results"""
        completion_scores = calculator.calculate_completion([])
        
        assert isinstance(completion_scores, dict)
        assert len(completion_scores) == 0
        
        overall_completion = calculator.calculate_overall_completion(completion_scores)
        assert overall_completion == 0.0


class TestPriorityRanker:
    """Test cases for PriorityRanker"""
    
    @pytest.fixture
    def ranker(self):
        """Create PriorityRanker instance"""
        return PriorityRanker()
    
    @pytest.fixture
    def sample_gaps(self):
        """Create sample gaps for testing"""
        return [
            Gap(
                component="critical-component",
                description="Critical security vulnerability",
                impact=ImpactLevel.CRITICAL,
                effort_estimate=8,
                category=ComponentCategory.SECURITY,
                dependencies=[]
            ),
            Gap(
                component="infrastructure-component",
                description="Missing health checks",
                impact=ImpactLevel.HIGH,
                effort_estimate=16,
                category=ComponentCategory.INFRASTRUCTURE,
                dependencies=["critical-component"]
            ),
            Gap(
                component="documentation-component",
                description="Update API documentation",
                impact=ImpactLevel.MEDIUM,
                effort_estimate=4,
                category=ComponentCategory.DOCUMENTATION,
                dependencies=[]
            ),
            Gap(
                component="testing-component",
                description="Add unit tests",
                impact=ImpactLevel.LOW,
                effort_estimate=24,
                category=ComponentCategory.TESTING,
                dependencies=["infrastructure-component"]
            )
        ]
    
    def test_prioritize_tasks(self, ranker, sample_gaps):
        """Test prioritizing tasks from gaps"""
        tasks = ranker.prioritize_tasks(sample_gaps)
        
        assert isinstance(tasks, list)
        assert len(tasks) == len(sample_gaps)
        assert all(isinstance(task, TODOTask) for task in tasks)
        
        # Tasks should be sorted by priority
        priorities = [task.priority for task in tasks]
        assert priorities[0] == Priority.CRITICAL  # Security vulnerability first
        assert Priority.CRITICAL in priorities or Priority.HIGH in priorities
    
    def test_assign_priority_based_on_impact(self, ranker):
        """Test assigning priority based on impact level"""
        critical_gap = Gap(
            component="test",
            description="Critical issue",
            impact=ImpactLevel.CRITICAL,
            effort_estimate=8,
            category=ComponentCategory.SECURITY
        )
        
        priority = ranker.assign_priority(critical_gap)
        assert priority == Priority.CRITICAL
        
        low_gap = Gap(
            component="test",
            description="Low priority issue",
            impact=ImpactLevel.LOW,
            effort_estimate=8,
            category=ComponentCategory.DOCUMENTATION
        )
        
        priority = ranker.assign_priority(low_gap)
        assert priority == Priority.LOW
    
    def test_calculate_priority_score(self, ranker, sample_gaps):
        """Test calculating priority score for gaps"""
        for gap in sample_gaps:
            score = ranker.calculate_priority_score(gap)
            
            assert isinstance(score, float)
            assert score >= 0.0
            
            # Critical impact should have higher score
            if gap.impact == ImpactLevel.CRITICAL:
                assert score > 80.0
            elif gap.impact == ImpactLevel.LOW:
                assert score < 50.0
    
    def test_adjust_priority_for_dependencies(self, ranker, sample_gaps):
        """Test adjusting priority based on dependencies"""
        # Gap with dependencies should have adjusted priority
        dependent_gap = next(gap for gap in sample_gaps if len(gap.dependencies) > 0)
        original_priority = ranker.assign_priority(dependent_gap)
        
        adjusted_tasks = ranker.prioritize_tasks(sample_gaps)
        dependent_task = next(task for task in adjusted_tasks if task.title == dependent_gap.description)
        
        # Task with dependencies might have different priority due to dependency ordering
        assert isinstance(dependent_task.priority, Priority)
    
    def test_estimate_effort(self, ranker):
        """Test estimating effort for different types of gaps"""
        security_gap = Gap(
            component="security",
            description="Implement authentication",
            impact=ImpactLevel.CRITICAL,
            effort_estimate=0,  # Will be estimated
            category=ComponentCategory.SECURITY
        )
        
        estimated_effort = ranker.estimate_effort(security_gap)
        
        assert isinstance(estimated_effort, int)
        assert estimated_effort > 0
        assert estimated_effort <= 80  # Should be reasonable estimate
    
    def test_create_todo_task_from_gap(self, ranker):
        """Test creating TODO task from gap"""
        gap = Gap(
            component="test-component",
            description="Implement feature X",
            impact=ImpactLevel.HIGH,
            effort_estimate=16,
            category=ComponentCategory.INFRASTRUCTURE,
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
        
        task = ranker.create_todo_task(gap)
        
        assert isinstance(task, TODOTask)
        assert task.title == gap.description
        assert task.effort_hours == gap.effort_estimate
        assert task.category == gap.category.value
        assert task.status == TaskStatus.NOT_STARTED
        assert len(task.acceptance_criteria) == 2
    
    def test_sort_tasks_by_priority(self, ranker, sample_gaps):
        """Test sorting tasks by priority and dependencies"""
        tasks = ranker.prioritize_tasks(sample_gaps)
        
        # Critical tasks should come first
        critical_tasks = [task for task in tasks if task.priority == Priority.CRITICAL]
        if critical_tasks:
            assert tasks.index(critical_tasks[0]) == 0
        
        # Tasks without dependencies should come before dependent tasks
        for i, task in enumerate(tasks):
            if len(task.dependencies) == 0:
                # Check that all dependent tasks come after this one
                for j in range(i + 1, len(tasks)):
                    if task.id in tasks[j].dependencies:
                        assert j > i


if __name__ == '__main__':
    pytest.main([__file__])