"""
Unit tests for Reporting Engine components
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from phoenix_system_review.reporting.todo_generator import TODOGenerator
from phoenix_system_review.reporting.status_reporter import StatusReporter
from phoenix_system_review.reporting.recommendation_engine import RecommendationEngine
from phoenix_system_review.models.data_models import (
    TODOTask, Priority, TaskStatus, Gap, ImpactLevel, ComponentCategory,
    AssessmentResults, CompletionScore, Component, EvaluationResult
)


class TestTODOGenerator:
    """Test cases for TODOGenerator"""
    
    @pytest.fixture
    def generator(self):
        """Create TODOGenerator instance"""
        return TODOGenerator()
    
    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for testing"""
        return [
            TODOTask(
                id="task-1",
                title="Fix critical security vulnerability",
                description="Implement proper authentication and authorization",
                category="security",
                priority=Priority.CRITICAL,
                status=TaskStatus.NOT_STARTED,
                effort_hours=16,
                dependencies=[],
                acceptance_criteria=["Authentication implemented", "Authorization working"]
            ),
            TODOTask(
                id="task-2",
                title="Add health check endpoints",
                description="Implement health check endpoints for all services",
                category="infrastructure",
                priority=Priority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                effort_hours=8,
                dependencies=["task-1"],
                acceptance_criteria=["Health endpoints respond", "Monitoring configured"]
            ),
            TODOTask(
                id="task-3",
                title="Update API documentation",
                description="Update OpenAPI specifications for all endpoints",
                category="documentation",
                priority=Priority.MEDIUM,
                status=TaskStatus.NOT_STARTED,
                effort_hours=12,
                dependencies=["task-2"],
                acceptance_criteria=["OpenAPI spec updated", "Examples provided"]
            ),
            TODOTask(
                id="task-4",
                title="Add unit tests",
                description="Increase test coverage to 90%",
                category="testing",
                priority=Priority.LOW,
                status=TaskStatus.NOT_STARTED,
                effort_hours=24,
                dependencies=["task-3"],
                acceptance_criteria=["90% test coverage", "All tests passing"]
            )
        ]
    
    def test_generate_todo_checklist(self, generator, sample_tasks):
        """Test generating TODO checklist from tasks"""
        checklist = generator.generate_todo_checklist(sample_tasks)
        
        assert isinstance(checklist, str)
        assert len(checklist) > 0
        
        # Should contain task titles
        assert "Fix critical security vulnerability" in checklist
        assert "Add health check endpoints" in checklist
        assert "Update API documentation" in checklist
        assert "Add unit tests" in checklist
        
        # Should contain priority indicators
        assert "CRITICAL" in checklist or "Critical" in checklist
        assert "HIGH" in checklist or "High" in checklist
        
        # Should contain effort estimates
        assert "16h" in checklist or "16 hours" in checklist
        assert "8h" in checklist or "8 hours" in checklist
    
    def test_generate_hierarchical_checklist(self, generator, sample_tasks):
        """Test generating hierarchical checklist with categories"""
        checklist = generator.generate_hierarchical_checklist(sample_tasks)
        
        assert isinstance(checklist, str)
        assert len(checklist) > 0
        
        # Should have category headers
        assert "Security" in checklist or "SECURITY" in checklist
        assert "Infrastructure" in checklist or "INFRASTRUCTURE" in checklist
        assert "Documentation" in checklist or "DOCUMENTATION" in checklist
        assert "Testing" in checklist or "TESTING" in checklist
        
        # Should have checkbox format
        assert "- [ ]" in checklist or "- [x]" in checklist or "☐" in checklist
    
    def test_generate_markdown_checklist(self, generator, sample_tasks):
        """Test generating markdown formatted checklist"""
        checklist = generator.generate_markdown_checklist(sample_tasks)
        
        assert isinstance(checklist, str)
        assert len(checklist) > 0
        
        # Should have markdown formatting
        assert "# " in checklist or "## " in checklist  # Headers
        assert "- [ ]" in checklist  # Checkboxes
        assert "**" in checklist or "*" in checklist  # Bold/italic text
        
        # Should include task details
        assert "Dependencies:" in checklist or "Depends on:" in checklist
        assert "Acceptance Criteria:" in checklist or "Criteria:" in checklist
    
    def test_filter_tasks_by_priority(self, generator, sample_tasks):
        """Test filtering tasks by priority"""
        critical_tasks = generator.filter_tasks_by_priority(sample_tasks, Priority.CRITICAL)
        
        assert isinstance(critical_tasks, list)
        assert len(critical_tasks) == 1
        assert critical_tasks[0].priority == Priority.CRITICAL
        assert critical_tasks[0].title == "Fix critical security vulnerability"
        
        high_priority_tasks = generator.filter_tasks_by_priority(sample_tasks, [Priority.CRITICAL, Priority.HIGH])
        assert len(high_priority_tasks) == 2
    
    def test_filter_tasks_by_status(self, generator, sample_tasks):
        """Test filtering tasks by status"""
        not_started_tasks = generator.filter_tasks_by_status(sample_tasks, TaskStatus.NOT_STARTED)
        
        assert isinstance(not_started_tasks, list)
        assert len(not_started_tasks) == 3
        assert all(task.status == TaskStatus.NOT_STARTED for task in not_started_tasks)
        
        in_progress_tasks = generator.filter_tasks_by_status(sample_tasks, TaskStatus.IN_PROGRESS)
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0].title == "Add health check endpoints"
    
    def test_calculate_total_effort(self, generator, sample_tasks):
        """Test calculating total effort for tasks"""
        total_effort = generator.calculate_total_effort(sample_tasks)
        
        assert isinstance(total_effort, int)
        assert total_effort == 60  # 16 + 8 + 12 + 24
        
        # Test with filtered tasks
        critical_tasks = generator.filter_tasks_by_priority(sample_tasks, Priority.CRITICAL)
        critical_effort = generator.calculate_total_effort(critical_tasks)
        assert critical_effort == 16
    
    def test_generate_summary_statistics(self, generator, sample_tasks):
        """Test generating summary statistics"""
        stats = generator.generate_summary_statistics(sample_tasks)
        
        assert isinstance(stats, dict)
        assert "total_tasks" in stats
        assert "by_priority" in stats
        assert "by_status" in stats
        assert "by_category" in stats
        assert "total_effort_hours" in stats
        assert "estimated_days" in stats
        
        assert stats["total_tasks"] == 4
        assert stats["total_effort_hours"] == 60
        assert stats["estimated_days"] == 7.5  # 60 hours / 8 hours per day


class TestStatusReporter:
    """Test cases for StatusReporter"""
    
    @pytest.fixture
    def reporter(self):
        """Create StatusReporter instance"""
        return StatusReporter()
    
    @pytest.fixture
    def sample_assessment_results(self):
        """Create sample assessment results for testing"""
        component_scores = {
            "phoenix-core": CompletionScore(
                component_name="phoenix-core",
                completion_percentage=85.0,
                weighted_score=82.0,
                criteria_total=10,
                criteria_met=8,
                quality_score=88.0
            ),
            "n8n-workflows": CompletionScore(
                component_name="n8n-workflows",
                completion_percentage=92.0,
                weighted_score=90.0,
                criteria_total=8,
                criteria_met=7,
                quality_score=95.0
            )
        }
        
        gaps = [
            Gap(
                component="phoenix-core",
                description="Missing monitoring integration",
                impact=ImpactLevel.HIGH,
                effort_estimate=16,
                category=ComponentCategory.INFRASTRUCTURE
            ),
            Gap(
                component="phoenix-core",
                description="Incomplete API documentation",
                impact=ImpactLevel.MEDIUM,
                effort_estimate=8,
                category=ComponentCategory.DOCUMENTATION
            )
        ]
        
        return AssessmentResults(
            overall_completion=88.5,
            component_scores=component_scores,
            identified_gaps=gaps,
            prioritized_tasks=[],
            recommendations=["Implement monitoring", "Complete documentation"]
        )
    
    def test_create_status_report(self, reporter, sample_assessment_results):
        """Test creating comprehensive status report"""
        report = reporter.create_status_report(sample_assessment_results)
        
        assert isinstance(report, str)
        assert len(report) > 0
        
        # Should contain overall completion
        assert "88.5" in report or "88%" in report
        
        # Should contain component information
        assert "phoenix-core" in report
        assert "n8n-workflows" in report
        
        # Should contain completion percentages
        assert "85" in report  # phoenix-core completion
        assert "92" in report  # n8n-workflows completion
        
        # Should contain gap information
        assert "monitoring" in report.lower()
        assert "documentation" in report.lower()
    
    def test_generate_executive_summary(self, reporter, sample_assessment_results):
        """Test generating executive summary"""
        summary = reporter.generate_executive_summary(sample_assessment_results)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Should be concise (less than full report)
        full_report = reporter.create_status_report(sample_assessment_results)
        assert len(summary) < len(full_report)
        
        # Should contain key metrics
        assert "88.5" in summary or "88%" in summary
        assert "completion" in summary.lower()
        
        # Should mention critical information
        assert "gap" in summary.lower() or "issue" in summary.lower()
    
    def test_create_component_breakdown(self, reporter, sample_assessment_results):
        """Test creating component breakdown report"""
        breakdown = reporter.create_component_breakdown(sample_assessment_results)
        
        assert isinstance(breakdown, str)
        assert len(breakdown) > 0
        
        # Should have sections for each component
        assert "phoenix-core" in breakdown
        assert "n8n-workflows" in breakdown
        
        # Should include detailed metrics
        assert "85.0%" in breakdown or "85%" in breakdown
        assert "92.0%" in breakdown or "92%" in breakdown
        assert "8/10" in breakdown or "8 of 10" in breakdown  # criteria met
    
    def test_generate_progress_visualization(self, reporter, sample_assessment_results):
        """Test generating progress visualization"""
        visualization = reporter.generate_progress_visualization(sample_assessment_results)
        
        assert isinstance(visualization, str)
        assert len(visualization) > 0
        
        # Should contain visual elements (ASCII art or progress bars)
        assert "█" in visualization or "▓" in visualization or "=" in visualization or "|" in visualization
        
        # Should show completion percentages
        assert "85" in visualization
        assert "92" in visualization
    
    def test_create_gap_analysis_report(self, reporter, sample_assessment_results):
        """Test creating gap analysis report"""
        gap_report = reporter.create_gap_analysis_report(sample_assessment_results)
        
        assert isinstance(gap_report, str)
        assert len(gap_report) > 0
        
        # Should contain gap information
        assert "monitoring" in gap_report.lower()
        assert "documentation" in gap_report.lower()
        
        # Should include impact levels
        assert "HIGH" in gap_report or "high" in gap_report
        assert "MEDIUM" in gap_report or "medium" in gap_report
        
        # Should include effort estimates
        assert "16" in gap_report  # monitoring gap effort
        assert "8" in gap_report   # documentation gap effort
    
    def test_format_completion_percentage(self, reporter):
        """Test formatting completion percentage"""
        formatted = reporter.format_completion_percentage(85.67)
        assert formatted == "85.7%"
        
        formatted = reporter.format_completion_percentage(100.0)
        assert formatted == "100.0%"
        
        formatted = reporter.format_completion_percentage(0.0)
        assert formatted == "0.0%"


class TestRecommendationEngine:
    """Test cases for RecommendationEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create RecommendationEngine instance"""
        return RecommendationEngine()
    
    @pytest.fixture
    def sample_gaps(self):
        """Create sample gaps for testing"""
        return [
            Gap(
                component="security",
                description="Critical security vulnerability",
                impact=ImpactLevel.CRITICAL,
                effort_estimate=16,
                category=ComponentCategory.SECURITY
            ),
            Gap(
                component="infrastructure",
                description="Missing monitoring",
                impact=ImpactLevel.HIGH,
                effort_estimate=24,
                category=ComponentCategory.INFRASTRUCTURE
            ),
            Gap(
                component="documentation",
                description="Incomplete API docs",
                impact=ImpactLevel.MEDIUM,
                effort_estimate=8,
                category=ComponentCategory.DOCUMENTATION
            )
        ]
    
    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for testing"""
        return [
            TODOTask(
                id="task-1",
                title="Fix security issue",
                description="Address critical security vulnerability",
                category="security",
                priority=Priority.CRITICAL,
                status=TaskStatus.NOT_STARTED,
                effort_hours=16
            ),
            TODOTask(
                id="task-2",
                title="Implement monitoring",
                description="Add comprehensive monitoring",
                category="infrastructure",
                priority=Priority.HIGH,
                status=TaskStatus.NOT_STARTED,
                effort_hours=24
            )
        ]
    
    def test_provide_recommendations(self, engine, sample_gaps, sample_tasks):
        """Test providing strategic recommendations"""
        recommendations = engine.provide_recommendations(sample_gaps, sample_tasks)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
        
        # Should prioritize critical issues
        security_recommendations = [rec for rec in recommendations if "security" in rec.lower()]
        assert len(security_recommendations) > 0
        
        # Should mention high-impact items
        monitoring_recommendations = [rec for rec in recommendations if "monitoring" in rec.lower()]
        assert len(monitoring_recommendations) > 0
    
    def test_generate_strategic_recommendations(self, engine, sample_gaps):
        """Test generating strategic recommendations"""
        strategic_recs = engine.generate_strategic_recommendations(sample_gaps)
        
        assert isinstance(strategic_recs, list)
        assert len(strategic_recs) > 0
        
        # Should focus on high-impact items first
        first_rec = strategic_recs[0]
        assert "critical" in first_rec.lower() or "security" in first_rec.lower()
    
    def test_generate_resource_allocation_suggestions(self, engine, sample_tasks):
        """Test generating resource allocation suggestions"""
        suggestions = engine.generate_resource_allocation_suggestions(sample_tasks)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should mention effort estimates
        effort_suggestions = [s for s in suggestions if "hour" in s.lower() or "day" in s.lower()]
        assert len(effort_suggestions) > 0
        
        # Should prioritize critical tasks
        priority_suggestions = [s for s in suggestions if "critical" in s.lower() or "priority" in s.lower()]
        assert len(priority_suggestions) > 0
    
    def test_assess_production_readiness(self, engine, sample_gaps):
        """Test assessing production readiness"""
        readiness_assessment = engine.assess_production_readiness(sample_gaps)
        
        assert isinstance(readiness_assessment, dict)
        assert "readiness_score" in readiness_assessment
        assert "blocking_issues" in readiness_assessment
        assert "recommendations" in readiness_assessment
        
        # Should have reasonable readiness score
        score = readiness_assessment["readiness_score"]
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        
        # Should identify blocking issues
        blocking_issues = readiness_assessment["blocking_issues"]
        assert isinstance(blocking_issues, list)
        
        # Critical gaps should be blocking issues
        critical_gaps = [gap for gap in sample_gaps if gap.impact == ImpactLevel.CRITICAL]
        if critical_gaps:
            assert len(blocking_issues) > 0
    
    def test_generate_risk_assessment(self, engine, sample_gaps):
        """Test generating risk assessment"""
        risk_assessment = engine.generate_risk_assessment(sample_gaps)
        
        assert isinstance(risk_assessment, dict)
        assert "high_risk_areas" in risk_assessment
        assert "mitigation_strategies" in risk_assessment
        assert "risk_score" in risk_assessment
        
        # Should identify high-risk areas
        high_risk_areas = risk_assessment["high_risk_areas"]
        assert isinstance(high_risk_areas, list)
        
        # Security gaps should be high risk
        security_gaps = [gap for gap in sample_gaps if gap.category == ComponentCategory.SECURITY]
        if security_gaps:
            security_risks = [area for area in high_risk_areas if "security" in area.lower()]
            assert len(security_risks) > 0
    
    def test_recommend_next_steps(self, engine, sample_gaps, sample_tasks):
        """Test recommending next steps"""
        next_steps = engine.recommend_next_steps(sample_gaps, sample_tasks)
        
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        assert all(isinstance(step, str) for step in next_steps)
        
        # Should be actionable steps
        actionable_steps = [step for step in next_steps if any(verb in step.lower() for verb in ["implement", "fix", "add", "update", "create"])]
        assert len(actionable_steps) > 0
        
        # Should prioritize critical items
        if any(gap.impact == ImpactLevel.CRITICAL for gap in sample_gaps):
            first_step = next_steps[0]
            assert "critical" in first_step.lower() or "security" in first_step.lower()
    
    def test_calculate_completion_timeline(self, engine, sample_tasks):
        """Test calculating completion timeline"""
        timeline = engine.calculate_completion_timeline(sample_tasks)
        
        assert isinstance(timeline, dict)
        assert "total_effort_hours" in timeline
        assert "estimated_completion_days" in timeline
        assert "milestone_dates" in timeline
        
        # Should calculate reasonable timeline
        total_effort = timeline["total_effort_hours"]
        assert total_effort == sum(task.effort_hours for task in sample_tasks)
        
        completion_days = timeline["estimated_completion_days"]
        assert isinstance(completion_days, (int, float))
        assert completion_days > 0


if __name__ == '__main__':
    pytest.main([__file__])