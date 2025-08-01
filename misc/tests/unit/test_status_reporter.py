"""
Unit tests for Status Reporter
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from src.phoenix_system_review.reporting.status_reporter import (
    StatusReporter, StatusReport, ReportType, ReportFormat, CompletionVisualization
)
from src.phoenix_system_review.models.data_models import (
    AssessmentResults, CompletionScore, Component, ComponentCategory, Priority
)
from src.phoenix_system_review.assessment.gap_analyzer import (
    GapAnalysisResult, IdentifiedGap, GapType, GapSeverity
)
from src.phoenix_system_review.assessment.priority_ranker import (
    PriorityRankingResult, PriorityScore, PriorityLevel, EffortLevel
)
from src.phoenix_system_review.assessment.completion_calculator import CompletionTier


class TestStatusReporter:
    """Test cases for StatusReporter"""
    
    @pytest.fixture
    def status_reporter(self):
        """Create status reporter instance"""
        return StatusReporter()
    
    @pytest.fixture
    def sample_component(self):
        """Create sample component"""
        return Component(
            name="test_component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/test/path",
            dependencies=[],
            configuration={}
        )
    
    @pytest.fixture
    def sample_completion_scores(self, sample_component):
        """Create sample completion scores"""
        return {
            "infrastructure_api": CompletionScore(
                component_name="infrastructure_api",
                completion_percentage=85.0,
                weighted_score=85.0,
                criteria_total=10,
                criteria_met=8,
                quality_score=80.0
            ),
            "monetization_system": CompletionScore(
                component_name="monetization_system", 
                completion_percentage=60.0,
                weighted_score=60.0,
                criteria_total=8,
                criteria_met=5,
                quality_score=65.0
            ),
            "security_auth": CompletionScore(
                component_name="security_auth",
                completion_percentage=40.0,
                weighted_score=40.0,
                criteria_total=12,
                criteria_met=5,
                quality_score=45.0
            )
        }
    
    @pytest.fixture
    def sample_assessment_results(self, sample_completion_scores):
        """Create sample assessment results"""
        return AssessmentResults(
            overall_completion=75.0,
            component_scores=sample_completion_scores,
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=["Complete security implementation", "Improve monetization system"]
        )
    
    @pytest.fixture
    def sample_gaps(self):
        """Create sample identified gaps"""
        return [
            IdentifiedGap(
                gap_id="critical_security",
                component_name="security_auth",
                gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                severity=GapSeverity.CRITICAL,
                title="Critical security gap",
                description="Authentication system incomplete",
                current_state="Partially implemented",
                expected_state="Fully functional",
                impact_description="Security vulnerability",
                effort_estimate_hours=32,
                category=ComponentCategory.SECURITY,
                dependencies=["database"],
                acceptance_criteria=["Authentication working", "Security audit passed"]
            ),
            IdentifiedGap(
                gap_id="missing_monitoring",
                component_name="monitoring_system",
                gap_type=GapType.MISSING_COMPONENT,
                severity=GapSeverity.HIGH,
                title="Missing monitoring system",
                description="No monitoring system implemented",
                current_state="Not implemented",
                expected_state="Monitoring active",
                impact_description="No visibility into system health",
                effort_estimate_hours=48,
                category=ComponentCategory.INFRASTRUCTURE,
                dependencies=[],
                acceptance_criteria=["Monitoring deployed", "Alerts configured"]
            )
        ]
    
    @pytest.fixture
    def sample_gap_analysis(self, sample_gaps):
        """Create sample gap analysis result"""
        return GapAnalysisResult(
            identified_gaps=sample_gaps,
            gap_summary={"incomplete_implementation": 1, "missing_component": 1},
            critical_gaps=[sample_gaps[0]],
            missing_components=["monitoring_system"],
            incomplete_implementations=["security_auth"],
            configuration_gaps=[],
            total_effort_estimate=80,
            completion_blockers=[sample_gaps[0]],
            recommendations=["Fix critical security gap", "Implement monitoring"]
        )
    
    @pytest.fixture
    def sample_priority_scores(self):
        """Create sample priority scores"""
        return [
            PriorityScore(
                component_name="security_auth",
                priority_level=PriorityLevel.CRITICAL,
                priority_score=90.0,
                business_impact_score=85.0,
                technical_complexity_score=70.0,
                dependency_urgency_score=80.0,
                effort_estimate=EffortLevel.MEDIUM,
                effort_hours=32,
                roi_score=75.0,
                risk_factor=0.9,
                completion_tier=CompletionTier.CRITICAL,
                justification="Critical security component",
                dependencies=["database"],
                blockers=[]
            ),
            PriorityScore(
                component_name="documentation",
                priority_level=PriorityLevel.LOW,
                priority_score=25.0,
                business_impact_score=20.0,
                technical_complexity_score=15.0,
                dependency_urgency_score=10.0,
                effort_estimate=EffortLevel.LOW,
                effort_hours=16,
                roi_score=30.0,
                risk_factor=0.1,
                completion_tier=CompletionTier.OPTIONAL,
                justification="Nice to have documentation",
                dependencies=[],
                blockers=[]
            )
        ]
    
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
            critical_path=["security_auth"],
            quick_wins=["documentation"],
            high_impact_items=[sample_priority_scores[0]],
            recommendations=["Focus on security", "Quick win with docs"],
            total_estimated_effort=48
        )
    
    def test_create_status_report(self, status_reporter, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test status report creation"""
        report = status_reporter.create_status_report(
            sample_assessment_results,
            sample_gap_analysis,
            sample_priority_ranking,
            ReportType.EXECUTIVE_SUMMARY,
            ReportFormat.MARKDOWN
        )
        
        assert isinstance(report, StatusReport)
        assert report.report_type == ReportType.EXECUTIVE_SUMMARY
        assert report.title is not None
        assert len(report.executive_summary) > 0
        assert len(report.detailed_sections) > 0
        assert len(report.metrics) > 0
        assert len(report.recommendations) > 0
        assert isinstance(report.generated_timestamp, datetime)
    
    def test_generate_executive_summary(self, status_reporter, sample_assessment_results):
        """Test executive summary generation"""
        summary = status_reporter.generate_executive_summary(sample_assessment_results)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Executive Summary" in summary
        assert "Overall System Completion" in summary
        assert "75.0%" in summary  # Overall completion from sample data
        assert "Key Metrics" in summary
        assert "Completion by Category" in summary
    
    def test_create_completion_dashboard(self, status_reporter, sample_assessment_results):
        """Test completion dashboard creation"""
        dashboard = status_reporter.create_completion_dashboard(
            sample_assessment_results,
            ReportFormat.MARKDOWN
        )
        
        assert isinstance(dashboard, str)
        assert len(dashboard) > 0
        assert "Completion Dashboard" in dashboard
        assert "Overall System Completion" in dashboard
        assert "75.0%" in dashboard
        assert "Completion by Category" in dashboard
    
    def test_format_report_markdown(self, status_reporter, sample_assessment_results):
        """Test markdown report formatting"""
        report = status_reporter.create_status_report(
            sample_assessment_results,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format_type=ReportFormat.MARKDOWN
        )
        
        formatted = status_reporter.format_report(report, ReportFormat.MARKDOWN)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert formatted.startswith("# ")  # Markdown header
        assert "## Executive Summary" in formatted
        assert "Generated:" in formatted
    
    def test_format_report_json(self, status_reporter, sample_assessment_results):
        """Test JSON report formatting"""
        report = status_reporter.create_status_report(
            sample_assessment_results,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format_type=ReportFormat.JSON
        )
        
        formatted = status_reporter.format_report(report, ReportFormat.JSON)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert "report_type" in parsed
        assert "title" in parsed
        assert "executive_summary" in parsed
        assert "metrics" in parsed
    
    def test_format_report_html(self, status_reporter, sample_assessment_results):
        """Test HTML report formatting"""
        report = status_reporter.create_status_report(
            sample_assessment_results,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format_type=ReportFormat.HTML
        )
        
        formatted = status_reporter.format_report(report, ReportFormat.HTML)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "<!DOCTYPE html>" in formatted
        assert "<html>" in formatted
        assert "<body>" in formatted
    
    def test_format_report_text(self, status_reporter, sample_assessment_results):
        """Test text report formatting"""
        report = status_reporter.create_status_report(
            sample_assessment_results,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format_type=ReportFormat.TEXT
        )
        
        formatted = status_reporter.format_report(report, ReportFormat.TEXT)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        # Should not contain markdown formatting
        assert "# " not in formatted
        assert "## " not in formatted
        assert "**" not in formatted
    
    def test_generate_component_breakdown(self, status_reporter, sample_assessment_results):
        """Test component breakdown generation"""
        breakdown = status_reporter._generate_component_breakdown(sample_assessment_results)
        
        assert isinstance(breakdown, str)
        assert len(breakdown) > 0
        assert "Component Breakdown" in breakdown
        assert "infrastructure_api" in breakdown
        assert "monetization_system" in breakdown
        assert "security_auth" in breakdown
        assert "85.0%" in breakdown  # Infrastructure API completion
        assert "60.0%" in breakdown  # Monetization system completion
        assert "40.0%" in breakdown  # Security auth completion
    
    def test_generate_gap_analysis_section(self, status_reporter, sample_gap_analysis):
        """Test gap analysis section generation"""
        section = status_reporter._generate_gap_analysis_section(sample_gap_analysis)
        
        assert isinstance(section, str)
        assert len(section) > 0
        assert "Gap Analysis" in section
        assert "**Total Gaps:** 2" in section
        assert "**Critical Gaps:** 1" in section
        assert "**Total Effort Estimate:** 80 hours" in section
        assert "Critical security gap" in section
        # The section only shows critical gaps in detail, so check for the critical gap
        assert "Critical security gap" in section
    
    def test_generate_priority_matrix_section(self, status_reporter, sample_priority_ranking):
        """Test priority matrix section generation"""
        section = status_reporter._generate_priority_matrix_section(sample_priority_ranking)
        
        assert isinstance(section, str)
        assert len(section) > 0
        assert "Priority Matrix" in section
        assert "Priority Distribution" in section
        assert "Critical Priority Items" in section
        assert "Quick Wins" in section
        assert "security_auth" in section
        assert "documentation" in section
    
    def test_calculate_category_completion(self, status_reporter, sample_assessment_results):
        """Test category completion calculation"""
        category_completion = status_reporter._calculate_category_completion(sample_assessment_results)
        
        assert isinstance(category_completion, dict)
        assert len(category_completion) > 0
        
        # Should have completion percentages for each category
        for category, completion in category_completion.items():
            assert isinstance(completion, float)
            assert 0 <= completion <= 100
    
    def test_create_completion_visualization(self, status_reporter, sample_assessment_results):
        """Test completion visualization creation"""
        viz = status_reporter._create_completion_visualization(sample_assessment_results)
        
        assert isinstance(viz, CompletionVisualization)
        assert viz.overall_completion == 75.0
        assert isinstance(viz.category_completion, dict)
        assert isinstance(viz.component_completion, dict)
        assert len(viz.component_completion) == 3  # Three sample components
    
    def test_progress_bar_creation(self, status_reporter):
        """Test progress bar creation"""
        # Test normal progress bar
        bar = status_reporter._create_progress_bar(75.0, 20)
        assert isinstance(bar, str)
        assert "75.0%" in bar
        assert "[" in bar and "]" in bar
        
        # Test large progress bar
        large_bar = status_reporter._create_large_progress_bar(50.0, 40)
        assert isinstance(large_bar, str)
        assert "50.0%" in large_bar
        assert "[" in large_bar and "]" in large_bar
    
    def test_status_emoji_generation(self, status_reporter):
        """Test status emoji generation"""
        assert status_reporter._get_status_emoji(98.0) == "✅"  # Complete
        assert status_reporter._get_status_emoji(88.0) == "🟡"  # Near complete
        assert status_reporter._get_status_emoji(75.0) == "🟠"  # In progress
        assert status_reporter._get_status_emoji(50.0) == "🔴"  # Early stage
    
    def test_completion_icon_generation(self, status_reporter):
        """Test completion icon generation"""
        assert status_reporter._get_completion_icon(95.0) == "✅"  # Complete
        assert status_reporter._get_completion_icon(80.0) == "🟡"  # Good
        assert status_reporter._get_completion_icon(60.0) == "🟠"  # Moderate
        assert status_reporter._get_completion_icon(30.0) == "🔴"  # Poor
    
    def test_report_title_generation(self, status_reporter):
        """Test report title generation"""
        title = status_reporter._generate_report_title(ReportType.EXECUTIVE_SUMMARY)
        assert "Executive Summary" in title
        assert "Phoenix Hydra" in title
        
        title = status_reporter._generate_report_title(ReportType.DETAILED_BREAKDOWN)
        assert "Detailed Breakdown" in title
        
        title = status_reporter._generate_report_title(ReportType.COMPLETION_DASHBOARD)
        assert "Completion Dashboard" in title
    
    def test_calculate_report_metrics(self, status_reporter, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test report metrics calculation"""
        metrics = status_reporter._calculate_report_metrics(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        assert isinstance(metrics, dict)
        assert "overall_completion" in metrics
        assert "total_components" in metrics
        assert "completed_components" in metrics
        assert "category_completion" in metrics
        assert "total_gaps" in metrics
        assert "critical_gaps" in metrics
        assert "quick_wins" in metrics
        
        assert metrics["overall_completion"] == 75.0
        assert metrics["total_components"] == 3
        assert metrics["total_gaps"] == 2
        assert metrics["critical_gaps"] == 1
    
    def test_generate_report_recommendations(self, status_reporter, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test report recommendations generation"""
        recommendations = status_reporter._generate_report_recommendations(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should have recommendations based on completion level (75%)
        assert any("critical gaps" in rec.lower() for rec in recommendations)
        assert any("quick wins" in rec.lower() for rec in recommendations)
    
    def test_error_handling(self, status_reporter):
        """Test error handling in status reporter"""
        # Test with invalid assessment results
        invalid_results = AssessmentResults(
            overall_completion=0.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        report = status_reporter.create_status_report(invalid_results)
        
        assert isinstance(report, StatusReport)
        # Should handle empty data gracefully
    
    def test_different_report_types(self, status_reporter, sample_assessment_results):
        """Test different report types"""
        # Executive summary
        exec_report = status_reporter.create_status_report(
            sample_assessment_results, 
            report_type=ReportType.EXECUTIVE_SUMMARY
        )
        assert exec_report.report_type == ReportType.EXECUTIVE_SUMMARY
        
        # Detailed breakdown
        detailed_report = status_reporter.create_status_report(
            sample_assessment_results,
            report_type=ReportType.DETAILED_BREAKDOWN
        )
        assert detailed_report.report_type == ReportType.DETAILED_BREAKDOWN
        
        # Completion dashboard
        dashboard_report = status_reporter.create_status_report(
            sample_assessment_results,
            report_type=ReportType.COMPLETION_DASHBOARD
        )
        assert dashboard_report.report_type == ReportType.COMPLETION_DASHBOARD
    
    def test_visualization_generation(self, status_reporter, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test visualization generation"""
        visualizations = status_reporter._generate_visualizations(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking, ReportFormat.MARKDOWN
        )
        
        assert isinstance(visualizations, dict)
        assert "completion" in visualizations
        assert "gaps" in visualizations
        assert "priorities" in visualizations
        
        # Check visualization content
        completion_viz = visualizations["completion"]
        assert isinstance(completion_viz, str)
        assert "75.0%" in completion_viz  # Overall completion
    
    def test_create_report_metadata(self, status_reporter, sample_assessment_results):
        """Test report metadata creation"""
        metadata = status_reporter._create_report_metadata(
            sample_assessment_results, None, None, ReportType.EXECUTIVE_SUMMARY
        )
        
        assert isinstance(metadata, dict)
        assert "report_type" in metadata
        assert "assessment_timestamp" in metadata
        assert "overall_completion" in metadata
        assert "total_components" in metadata
        assert "generator" in metadata
        assert "version" in metadata
        
        assert metadata["report_type"] == "executive_summary"
        assert metadata["overall_completion"] == 75.0
        assert metadata["total_components"] == 3
    
    def test_report_templates_defined(self, status_reporter):
        """Test that report templates are properly defined"""
        templates = status_reporter.report_templates
        
        assert isinstance(templates, dict)
        assert ReportType.EXECUTIVE_SUMMARY in templates
        assert ReportType.DETAILED_BREAKDOWN in templates
        assert ReportType.COMPLETION_DASHBOARD in templates
        
        # Check template structure
        for report_type, template in templates.items():
            assert "sections" in template
            assert "stakeholder" in template
            assert "detail_level" in template
    
    def test_visualization_settings_defined(self, status_reporter):
        """Test that visualization settings are properly defined"""
        settings = status_reporter.visualization_settings
        
        assert isinstance(settings, dict)
        assert "progress_bar_width" in settings
        assert "large_progress_bar_width" in settings
        assert "color_scheme" in settings
        
        # Check color scheme
        colors = settings["color_scheme"]
        assert "critical" in colors
        assert "high" in colors
        assert "medium" in colors
        assert "low" in colors


if __name__ == "__main__":
    pytest.main([__file__])