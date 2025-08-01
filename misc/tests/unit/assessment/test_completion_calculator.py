"""
Unit tests for Completion Calculator module.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.phoenix_system_review.assessment.completion_calculator import (
    CompletionCalculator,
    CompletionAnalysisResult,
    ComponentCompletionScore,
    SystemCompletionScore,
    CompletionTrend,
    CompletionTier,
    TrendDirection
)
from src.phoenix_system_review.models.data_models import (
    Component,
    ComponentCategory,
    ComponentStatus
)
from src.phoenix_system_review.analysis.component_evaluator import (
    ComponentEvaluation,
    EvaluationStatus
)
from src.phoenix_system_review.analysis.quality_assessor import (
    QualityAssessmentResult,
    QualityLevel,
    CodeQualityResult,
    DocumentationResult,
    TestCoverageResult
)
from src.phoenix_system_review.analysis.dependency_analyzer import (
    DependencyAnalysisResult
)


class TestCompletionCalculator:
    """Test completion calculator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = CompletionCalculator()
    
    def test_initialization(self):
        """Test calculator initialization"""
        assert len(self.calculator.category_weights) >= 3
        assert len(self.calculator.component_tiers) > 0
        assert len(self.calculator.completion_thresholds) == 4
        assert isinstance(self.calculator.historical_data, dict)
    
    def test_calculate_functionality_score(self):
        """Test functionality score calculation"""
        # Test different evaluation statuses
        passed_eval = Mock(status=EvaluationStatus.PASSED)
        warning_eval = Mock(status=EvaluationStatus.WARNING)
        failed_eval = Mock(status=EvaluationStatus.FAILED)
        not_eval = Mock(status=EvaluationStatus.NOT_EVALUATED)
        
        assert self.calculator._calculate_functionality_score(passed_eval) == 1.0
        assert self.calculator._calculate_functionality_score(warning_eval) == 0.7
        assert self.calculator._calculate_functionality_score(failed_eval) == 0.3
        assert self.calculator._calculate_functionality_score(not_eval) == 0.0
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        # Test with quality assessment
        quality_assessment = Mock()
        quality_assessment.overall_quality_score = 0.8
        
        assert self.calculator._calculate_quality_score(quality_assessment) == 0.8
        
        # Test without quality assessment
        assert self.calculator._calculate_quality_score(None) == 0.0
    
    def test_calculate_documentation_score(self):
        """Test documentation score calculation"""
        # Test with quality assessment
        quality_assessment = Mock()
        quality_assessment.documentation.documentation_score = 0.75
        
        assert self.calculator._calculate_documentation_score(quality_assessment) == 0.75
        
        # Test without quality assessment
        assert self.calculator._calculate_documentation_score(None) == 0.0
    
    def test_calculate_testing_score(self):
        """Test testing score calculation"""
        # Test with quality assessment
        quality_assessment = Mock()
        quality_assessment.test_coverage.coverage_percentage = 80.0
        
        assert self.calculator._calculate_testing_score(quality_assessment) == 0.8
        
        # Test without quality assessment
        assert self.calculator._calculate_testing_score(None) == 0.0
    
    def test_calculate_integration_score(self):
        """Test integration score calculation"""
        # Create mock evaluation
        component = Component("Test Component", ComponentCategory.INFRASTRUCTURE, "./")
        evaluation = Mock()
        evaluation.component = component
        
        # Create mock dependency analysis with no issues
        dependency_analysis = Mock()
        dependency_analysis.missing_dependencies = []
        dependency_analysis.circular_dependencies = []
        dependency_analysis.overall_dependency_health = 0.9
        
        score = self.calculator._calculate_integration_score(evaluation, dependency_analysis)
        assert score == 0.9
        
        # Test with dependency issues
        dependency_analysis.missing_dependencies = [Mock(source="Test Component")]
        score = self.calculator._calculate_integration_score(evaluation, dependency_analysis)
        assert score == 0.5
    
    def test_calculate_deployment_score(self):
        """Test deployment score calculation"""
        # Test different component statuses
        operational_component = Component("Test", ComponentCategory.INFRASTRUCTURE, "./", status=ComponentStatus.OPERATIONAL)
        degraded_component = Component("Test", ComponentCategory.INFRASTRUCTURE, "./", status=ComponentStatus.DEGRADED)
        failed_component = Component("Test", ComponentCategory.INFRASTRUCTURE, "./", status=ComponentStatus.FAILED)
        unknown_component = Component("Test", ComponentCategory.INFRASTRUCTURE, "./", status=ComponentStatus.UNKNOWN)
        
        operational_eval = Mock(component=operational_component)
        degraded_eval = Mock(component=degraded_component)
        failed_eval = Mock(component=failed_component)
        unknown_eval = Mock(component=unknown_component)
        
        assert self.calculator._calculate_deployment_score(operational_eval) == 1.0
        assert self.calculator._calculate_deployment_score(degraded_eval) == 0.6
        assert self.calculator._calculate_deployment_score(failed_eval) == 0.2
        assert self.calculator._calculate_deployment_score(unknown_eval) == 0.0
    
    def test_calculate_weighted_component_score(self):
        """Test weighted component score calculation"""
        # Test with perfect scores
        score = self.calculator._calculate_weighted_component_score(1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        assert score == 1.0
        
        # Test with zero scores
        score = self.calculator._calculate_weighted_component_score(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        assert score == 0.0
        
        # Test with mixed scores
        score = self.calculator._calculate_weighted_component_score(1.0, 0.8, 0.6, 0.4, 0.2, 0.0)
        assert 0.0 < score < 1.0
    
    def test_identify_critical_components(self):
        """Test critical component identification"""
        # Create test components
        monetization_component = Component("Revenue Tracker", ComponentCategory.MONETIZATION, "./")
        infrastructure_component = Component("NCA Toolkit", ComponentCategory.INFRASTRUCTURE, "./")
        automation_component = Component("Deployment Scripts", ComponentCategory.AUTOMATION, "./")
        
        scores = [
            ComponentCompletionScore(component=monetization_component),
            ComponentCompletionScore(component=infrastructure_component),
            ComponentCompletionScore(component=automation_component)
        ]
        
        critical_components = self.calculator._identify_critical_components(scores)
        
        # Should identify monetization and infrastructure components as critical
        critical_names = [score.component.name for score in critical_components]
        assert "Revenue Tracker" in critical_names
        assert "NCA Toolkit" in critical_names
        assert "Deployment Scripts" in critical_names  # Contains "deployment"
    
    def test_calculate_component_scores(self):
        """Test component score calculation"""
        # Create test data
        component = Component("Test Component", ComponentCategory.INFRASTRUCTURE, "./", status=ComponentStatus.OPERATIONAL)
        
        evaluation = ComponentEvaluation(
            component=component,
            criteria_type="test",
            overall_score=0.8,
            completion_percentage=80.0,
            status=EvaluationStatus.PASSED,
            critical_criteria_passed=True
        )
        
        quality_assessment = QualityAssessmentResult(
            component=component,
            overall_quality_score=0.7,
            quality_level=QualityLevel.GOOD,
            documentation=DocumentationResult(documentation_score=0.6),
            test_coverage=TestCoverageResult(coverage_percentage=75.0)
        )
        
        dependency_analysis = DependencyAnalysisResult(
            missing_dependencies=[],
            circular_dependencies=[],
            overall_dependency_health=0.9
        )
        
        scores = self.calculator._calculate_component_scores(
            [evaluation], [quality_assessment], dependency_analysis
        )
        
        assert len(scores) == 1
        score = scores[0]
        assert score.component == component
        assert 0 <= score.completion_percentage <= 100
        assert 0 <= score.weighted_score <= 1.0
    
    def test_calculate_category_scores(self):
        """Test category score calculation"""
        # Create test component scores
        infrastructure_component = Component("DB", ComponentCategory.INFRASTRUCTURE, "./")
        monetization_component = Component("Revenue", ComponentCategory.MONETIZATION, "./")
        
        scores = [
            ComponentCompletionScore(
                component=infrastructure_component,
                completion_percentage=80.0
            ),
            ComponentCompletionScore(
                component=monetization_component,
                completion_percentage=60.0
            )
        ]
        
        category_scores = self.calculator._calculate_category_scores(scores)
        
        assert ComponentCategory.INFRASTRUCTURE in category_scores
        assert ComponentCategory.MONETIZATION in category_scores
        
        infra_score = category_scores[ComponentCategory.INFRASTRUCTURE]
        assert infra_score.component_count == 1
        assert infra_score.average_completion == 80.0
        
        monetization_score = category_scores[ComponentCategory.MONETIZATION]
        assert monetization_score.component_count == 1
        assert monetization_score.average_completion == 60.0
    
    def test_calculate_system_score(self):
        """Test system score calculation"""
        # Create test category scores
        from src.phoenix_system_review.assessment.completion_calculator import CategoryCompletionScore
        
        infrastructure_score = CategoryCompletionScore(
            category=ComponentCategory.INFRASTRUCTURE,
            weighted_completion=80.0,
            component_count=2,
            completed_components=1,
            total_critical_components=1,
            critical_components_completed=1
        )
        
        monetization_score = CategoryCompletionScore(
            category=ComponentCategory.MONETIZATION,
            weighted_completion=60.0,
            component_count=1,
            completed_components=0,
            total_critical_components=1,
            critical_components_completed=0
        )
        
        category_scores = {
            ComponentCategory.INFRASTRUCTURE: infrastructure_score,
            ComponentCategory.MONETIZATION: monetization_score
        }
        
        system_score = self.calculator._calculate_system_score(category_scores)
        
        assert system_score.total_components == 3
        assert system_score.completed_components == 1
        assert 0 <= system_score.overall_completion <= 100
        assert 0 <= system_score.business_readiness <= 100
    
    def test_analyze_completion_trends_no_history(self):
        """Test trend analysis with no historical data"""
        current_scores = [
            ComponentCompletionScore(
                component=Component("Test", ComponentCategory.INFRASTRUCTURE, "./"),
                completion_percentage=75.0
            )
        ]
        
        trends = self.calculator._analyze_completion_trends(current_scores, None)
        
        assert len(trends) == 1
        trend = trends[0]
        assert trend.current_score == 75.0
        assert trend.previous_score == 0.0
        assert trend.trend_direction == TrendDirection.UNKNOWN
    
    def test_analyze_completion_trends_with_history(self):
        """Test trend analysis with historical data"""
        # Create historical scores
        historical_scores = [
            ComponentCompletionScore(
                component=Component("Test", ComponentCategory.INFRASTRUCTURE, "./"),
                completion_percentage=60.0,
                last_updated=datetime.now() - timedelta(days=7)
            )
        ]
        
        # Create current scores
        current_scores = [
            ComponentCompletionScore(
                component=Component("Test", ComponentCategory.INFRASTRUCTURE, "./"),
                completion_percentage=75.0,
                last_updated=datetime.now()
            )
        ]
        
        trends = self.calculator._analyze_completion_trends(current_scores, historical_scores)
        
        assert len(trends) == 1
        trend = trends[0]
        assert trend.current_score == 75.0
        assert trend.previous_score == 60.0
        assert trend.score_change == 15.0
        assert trend.trend_direction == TrendDirection.IMPROVING
        assert trend.improvement_rate > 0
    
    def test_calculate_completion_full_workflow(self):
        """Test complete completion calculation workflow"""
        # Create test data
        component = Component("Test Component", ComponentCategory.INFRASTRUCTURE, "./", status=ComponentStatus.OPERATIONAL)
        
        evaluation = ComponentEvaluation(
            component=component,
            criteria_type="test",
            overall_score=0.8,
            completion_percentage=80.0,
            status=EvaluationStatus.PASSED,
            critical_criteria_passed=True
        )
        
        quality_assessment = QualityAssessmentResult(
            component=component,
            overall_quality_score=0.7,
            quality_level=QualityLevel.GOOD,
            documentation=DocumentationResult(documentation_score=0.6),
            test_coverage=TestCoverageResult(coverage_percentage=75.0)
        )
        
        dependency_analysis = DependencyAnalysisResult(
            missing_dependencies=[],
            circular_dependencies=[],
            overall_dependency_health=0.9
        )
        
        result = self.calculator.calculate_completion(
            [evaluation], [quality_assessment], dependency_analysis
        )
        
        assert isinstance(result, CompletionAnalysisResult)
        assert len(result.component_scores) == 1
        assert len(result.trends) == 1
        assert len(result.recommendations) > 0
        assert result.system_score.total_components == 1
    
    def test_generate_completion_report(self):
        """Test completion report generation"""
        # Create minimal test result
        component = Component("Test", ComponentCategory.INFRASTRUCTURE, "./")
        
        result = CompletionAnalysisResult(
            system_score=SystemCompletionScore(
                overall_completion=75.0,
                business_readiness=70.0,
                total_components=1,
                completed_components=0
            ),
            component_scores=[
                ComponentCompletionScore(
                    component=component,
                    completion_percentage=75.0,
                    functionality_score=0.8,
                    quality_score=0.7
                )
            ],
            trends=[
                CompletionTrend(
                    component_name="Test",
                    current_score=75.0,
                    previous_score=60.0,
                    score_change=15.0,
                    trend_direction=TrendDirection.IMPROVING,
                    days_since_last_update=7,
                    improvement_rate=2.14
                )
            ],
            recommendations=["Test recommendation"]
        )
        
        report = self.calculator.generate_completion_report(result)
        
        assert "system_overview" in report
        assert "category_breakdown" in report
        assert "component_details" in report
        assert "trend_summary" in report
        assert "recommendations" in report
        assert "thresholds" in report
        
        assert report["system_overview"]["overall_completion"] == 75.0
        assert len(report["component_details"]) == 1
        assert len(report["recommendations"]) == 1
    
    def test_calculate_completion_velocity(self):
        """Test completion velocity calculation"""
        trends = [
            CompletionTrend(
                component_name="Test1",
                current_score=80.0,
                previous_score=70.0,
                score_change=10.0,
                trend_direction=TrendDirection.IMPROVING,
                days_since_last_update=5,
                improvement_rate=2.0
            ),
            CompletionTrend(
                component_name="Test2",
                current_score=60.0,
                previous_score=65.0,
                score_change=-5.0,
                trend_direction=TrendDirection.DECLINING,
                days_since_last_update=5,
                improvement_rate=-1.0
            )
        ]
        
        velocity = self.calculator.calculate_completion_velocity(trends)
        
        assert "average_velocity" in velocity
        assert "median_velocity" in velocity
        assert "max_velocity" in velocity
        assert "improving_components" in velocity
        
        # Should only consider positive improvement rates
        assert velocity["improving_components"] == 1
        assert velocity["average_velocity"] == 2.0
    
    def test_identify_completion_blockers(self):
        """Test completion blocker identification"""
        # Create test result with low-completion components
        low_completion_component = Component("Blocker", ComponentCategory.MONETIZATION, "./")
        
        result = CompletionAnalysisResult(
            system_score=SystemCompletionScore(),
            component_scores=[
                ComponentCompletionScore(
                    component=low_completion_component,
                    completion_percentage=30.0,
                    functionality_score=0.3,
                    integration_score=0.2,
                    deployment_score=0.1
                )
            ]
        )
        
        blockers = self.calculator.identify_completion_blockers(result)
        
        assert len(blockers) == 1
        blocker = blockers[0]
        assert blocker["component"] == "Blocker"
        assert blocker["completion"] == 30.0
        assert len(blocker["blocking_reasons"]) > 0
        assert "Critical for revenue generation" in blocker["blocking_reasons"]
    
    def test_estimate_completion_timeline(self):
        """Test completion timeline estimation"""
        # Test with positive velocity
        trends = [
            CompletionTrend(
                component_name="Test",
                current_score=70.0,
                previous_score=60.0,
                score_change=10.0,
                trend_direction=TrendDirection.IMPROVING,
                days_since_last_update=5,
                improvement_rate=2.0
            )
        ]
        
        result = CompletionAnalysisResult(
            system_score=SystemCompletionScore(overall_completion=70.0),
            trends=trends
        )
        
        timeline = self.calculator.estimate_completion_timeline(result, 90.0)
        
        assert timeline["target_reached"] is False
        assert timeline["current_completion"] == 70.0
        assert timeline["target_completion"] == 90.0
        assert timeline["estimated_days"] is not None
        assert timeline["estimated_days"] > 0
        
        # Test when target is already reached
        result.system_score.overall_completion = 95.0
        timeline = self.calculator.estimate_completion_timeline(result, 90.0)
        assert timeline["target_reached"] is True


if __name__ == "__main__":
    pytest.main([__file__])