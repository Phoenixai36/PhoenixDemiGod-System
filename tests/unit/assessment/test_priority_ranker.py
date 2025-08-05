"""
Unit tests for Priority Ranker module.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.phoenix_system_review.assessment.priority_ranker import (
    PriorityRanker,
    PriorityRankingResult,
    PriorityScore,
    PriorityLevel,
    EffortLevel
)
from src.phoenix_system_review.assessment.completion_calculator import (
    ComponentCompletionScore,
    CompletionTier
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
    QualityLevel
)
from src.phoenix_system_review.analysis.dependency_analyzer import (
    DependencyAnalysisResult,
    DependencyGraph
)


class TestPriorityRanker:
    """Test priority ranker"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.ranker = PriorityRanker()
    
    def test_initialization(self):
        """Test ranker initialization"""
        assert len(self.ranker.business_impact_weights) > 0
        assert len(self.ranker.complexity_factors) > 0
        assert len(self.ranker.effort_mappings) > 0
        assert len(self.ranker.roi_parameters) > 0
    
    def test_rank_priorities_basic(self):
        """Test basic priority ranking"""
        # Create test data
        component = Component(
            name="Test Component",
            category=ComponentCategory.MONETIZATION,
            path="src/test.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        component_score = ComponentCompletionScore(
            component=component,
            completion_percentage=60.0,
            weighted_score=120.0,
            tier=CompletionTier.CRITICAL,
            quality_factor=0.8,
            dependency_factor=1.0,
            business_impact_weight=2.0,
            technical_complexity_weight=1.0,
            adjusted_completion=65.0,
            confidence_level=0.8
        )
        
        evaluation = ComponentEvaluation(
            component=component,
            criteria_type="monetization",
            overall_score=0.7,
            completion_percentage=60.0,
            status=EvaluationStatus.WARNING,
            critical_criteria_passed=True
        )
        
        quality_assessment = QualityAssessmentResult(
            component=component,
            overall_quality_score=0.7,
            quality_level=QualityLevel.GOOD
        )
        
        dependency_analysis = DependencyAnalysisResult(
            dependency_graph=DependencyGraph(),
            missing_dependencies=[],
            circular_dependencies=[],
            overall_dependency_health=1.0
        )
        
        # Rank priorities
        result = self.ranker.rank_priorities(
            [component_score], [evaluation], [quality_assessment], dependency_analysis
        )
        
        assert isinstance(result, PriorityRankingResult)
        assert len(result.priority_scores) == 1
        assert len(result.priority_matrix) > 0
        assert result.total_estimated_effort > 0
    
    def test_calculate_business_impact_score(self):
        """Test business impact score calculation"""
        # Create monetization component (high impact)
        monetization_component = Component(
            name="Revenue Tracker",
            category=ComponentCategory.MONETIZATION,
            path="src/revenue.py"
        )
        
        monetization_score = ComponentCompletionScore(
            component=monetization_component,
            completion_percentage=50.0,
            weighted_score=100.0,
            tier=CompletionTier.CRITICAL,
            quality_factor=0.8,
            dependency_factor=1.0,
            business_impact_weight=2.0,
            technical_complexity_weight=1.0,
            adjusted_completion=55.0,
            confidence_level=0.8
        )
        
        impact_score = self.ranker._calculate_business_impact_score(monetization_score, None)
        
        # Should be high due to monetization category and critical tier
        assert impact_score > 80.0
        
        # Create documentation component (lower impact)
        doc_component = Component(
            name="Documentation",
            category=ComponentCategory.DOCUMENTATION,
            path="docs/"
        )
        
        doc_score = ComponentCompletionScore(
            component=doc_component,
            completion_percentage=80.0,
            weighted_score=40.0,
            tier=CompletionTier.OPTIONAL,
            quality_factor=0.8,
            dependency_factor=1.0,
            business_impact_weight=0.5,
            technical_complexity_weight=1.0,
            adjusted_completion=85.0,
            confidence_level=0.8
        )
        
        doc_impact_score = self.ranker._calculate_business_impact_score(doc_score, None)
        
        # Should be lower than monetization component
        assert doc_impact_score < impact_score
    
    def test_calculate_technical_complexity_score(self):
        """Test technical complexity score calculation"""
        # Create database component (high complexity)
        db_component = Component(
            name="Database Integration",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/database.py"
        )
        
        # Test with poor quality (increases complexity)
        poor_quality = QualityAssessmentResult(
            component=db_component,
            overall_quality_score=0.3,
            quality_level=QualityLevel.POOR
        )
        
        complexity_score = self.ranker._calculate_technical_complexity_score(
            db_component, None, poor_quality
        )
        
        # Should be high due to database complexity and poor quality
        assert complexity_score > 60.0
        
        # Test with good quality (reduces complexity)
        good_quality = QualityAssessmentResult(
            component=db_component,
            overall_quality_score=0.9,
            quality_level=QualityLevel.EXCELLENT
        )
        
        good_complexity_score = self.ranker._calculate_technical_complexity_score(
            db_component, None, good_quality
        )
        
        # Should be lower than poor quality version
        assert good_complexity_score < complexity_score
    
    def test_determine_priority_level(self):
        """Test priority level determination"""
        # Test critical tier with high score
        priority_level = self.ranker._determine_priority_level(85.0, CompletionTier.CRITICAL)
        assert priority_level == PriorityLevel.CRITICAL
        
        # Test critical tier with medium score
        priority_level = self.ranker._determine_priority_level(55.0, CompletionTier.CRITICAL)
        assert priority_level == PriorityLevel.HIGH
        
        # Test non-critical tier with high score
        priority_level = self.ranker._determine_priority_level(85.0, CompletionTier.IMPORTANT)
        assert priority_level == PriorityLevel.CRITICAL
        
        # Test low score
        priority_level = self.ranker._determine_priority_level(30.0, CompletionTier.OPTIONAL)
        assert priority_level == PriorityLevel.LOW
    
    def test_estimate_effort(self):
        """Test effort estimation"""
        # Create API component (higher effort)
        api_component = Component(
            name="Core API",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/api.py"
        )
        
        # Test with poor quality (increases effort)
        poor_quality = QualityAssessmentResult(
            component=api_component,
            overall_quality_score=0.3,
            quality_level=QualityLevel.POOR
        )
        
        effort_level, effort_hours = self.ranker._estimate_effort(
            api_component, None, poor_quality, 40.0  # 60% remaining work
        )
        
        assert isinstance(effort_level, EffortLevel)
        assert effort_hours > 0
        
        # Test with good quality (reduces effort)
        good_quality = QualityAssessmentResult(
            component=api_component,
            overall_quality_score=0.9,
            quality_level=QualityLevel.EXCELLENT
        )
        
        good_effort_level, good_effort_hours = self.ranker._estimate_effort(
            api_component, None, good_quality, 40.0
        )
        
        # Should require less effort with good quality
        assert good_effort_hours < effort_hours
    
    def test_calculate_roi_score(self):
        """Test ROI score calculation"""
        # High impact, low effort = high ROI
        high_roi = self.ranker._calculate_roi_score(90.0, 20)  # High impact, low effort
        
        # Low impact, high effort = low ROI
        low_roi = self.ranker._calculate_roi_score(30.0, 160)  # Low impact, high effort
        
        assert high_roi > low_roi
        assert 0 <= high_roi <= 100
        assert 0 <= low_roi <= 100
    
    def test_identify_quick_wins(self):
        """Test quick wins identification"""
        # Create priority scores with different ROI and effort combinations
        priority_scores = [
            PriorityScore(
                component_name="Quick Win 1",
                priority_level=PriorityLevel.HIGH,
                priority_score=75.0,
                business_impact_score=80.0,
                technical_complexity_score=30.0,
                dependency_urgency_score=40.0,
                effort_estimate=EffortLevel.MINIMAL,
                effort_hours=16,
                roi_score=85.0,  # High ROI
                risk_factor=0.3,
                completion_tier=CompletionTier.IMPORTANT,
                justification="High ROI, low effort"
            ),
            PriorityScore(
                component_name="High Effort Item",
                priority_level=PriorityLevel.HIGH,
                priority_score=80.0,
                business_impact_score=85.0,
                technical_complexity_score=70.0,
                dependency_urgency_score=60.0,
                effort_estimate=EffortLevel.EXTENSIVE,
                effort_hours=200,
                roi_score=45.0,  # Lower ROI due to high effort
                risk_factor=0.6,
                completion_tier=CompletionTier.CRITICAL,
                justification="High impact but high effort"
            )
        ]
        
        quick_wins = self.ranker._identify_quick_wins(priority_scores)
        
        assert len(quick_wins) == 1
        assert quick_wins[0].component_name == "Quick Win 1"
        assert quick_wins[0].roi_score >= 60
        assert quick_wins[0].effort_estimate in [EffortLevel.MINIMAL, EffortLevel.LOW]
    
    def test_identify_high_impact_items(self):
        """Test high impact items identification"""
        priority_scores = [
            PriorityScore(
                component_name="High Impact 1",
                priority_level=PriorityLevel.CRITICAL,
                priority_score=90.0,
                business_impact_score=95.0,  # High impact
                technical_complexity_score=60.0,
                dependency_urgency_score=70.0,
                effort_estimate=EffortLevel.HIGH,
                effort_hours=120,
                roi_score=60.0,
                risk_factor=0.8,
                completion_tier=CompletionTier.CRITICAL,
                justification="Critical business impact"
            ),
            PriorityScore(
                component_name="Low Impact Item",
                priority_level=PriorityLevel.LOW,
                priority_score=40.0,
                business_impact_score=35.0,  # Low impact
                technical_complexity_score=40.0,
                dependency_urgency_score=20.0,
                effort_estimate=EffortLevel.LOW,
                effort_hours=30,
                roi_score=40.0,
                risk_factor=0.2,
                completion_tier=CompletionTier.OPTIONAL,
                justification="Low business impact"
            )
        ]
        
        high_impact_items = self.ranker._identify_high_impact_items(priority_scores)
        
        assert len(high_impact_items) == 1
        assert high_impact_items[0].component_name == "High Impact 1"
        assert high_impact_items[0].business_impact_score >= 70
    
    def test_create_priority_matrix(self):
        """Test priority matrix creation"""
        priority_scores = [
            PriorityScore(
                component_name="Critical Item",
                priority_level=PriorityLevel.CRITICAL,
                priority_score=90.0,
                business_impact_score=85.0,
                technical_complexity_score=50.0,
                dependency_urgency_score=70.0,
                effort_estimate=EffortLevel.MEDIUM,
                effort_hours=60,
                roi_score=70.0,
                risk_factor=0.8,
                completion_tier=CompletionTier.CRITICAL,
                justification="Critical priority"
            ),
            PriorityScore(
                component_name="High Item",
                priority_level=PriorityLevel.HIGH,
                priority_score=75.0,
                business_impact_score=70.0,
                technical_complexity_score=40.0,
                dependency_urgency_score=50.0,
                effort_estimate=EffortLevel.LOW,
                effort_hours=30,
                roi_score=80.0,
                risk_factor=0.5,
                completion_tier=CompletionTier.ESSENTIAL,
                justification="High priority"
            )
        ]
        
        matrix = self.ranker._create_priority_matrix(priority_scores)
        
        assert "critical" in matrix
        assert "high" in matrix
        assert "medium" in matrix
        assert "low" in matrix
        
        assert len(matrix["critical"]) == 1
        assert len(matrix["high"]) == 1
        assert matrix["critical"][0].component_name == "Critical Item"
        assert matrix["high"][0].component_name == "High Item"
    
    def test_get_priority_summary(self):
        """Test priority summary generation"""
        # Create test ranking result
        priority_scores = [
            PriorityScore(
                component_name="Test Component",
                priority_level=PriorityLevel.HIGH,
                priority_score=75.0,
                business_impact_score=80.0,
                technical_complexity_score=40.0,
                dependency_urgency_score=50.0,
                effort_estimate=EffortLevel.MEDIUM,
                effort_hours=60,
                roi_score=70.0,
                risk_factor=0.5,
                completion_tier=CompletionTier.IMPORTANT,
                justification="Test justification"
            )
        ]
        
        ranking_result = PriorityRankingResult(
            priority_scores=priority_scores,
            priority_matrix={"high": priority_scores, "critical": [], "medium": [], "low": []},
            effort_distribution={"medium": 1, "minimal": 0, "low": 0, "high": 0, "extensive": 0},
            total_estimated_effort=60,
            quick_wins=[],
            high_impact_items=[],
            recommendations=["Test recommendation"]
        )
        
        summary = self.ranker.get_priority_summary(ranking_result)
        
        assert summary["total_components"] == 1
        assert summary["high_priority_count"] == 1
        assert summary["critical_priority_count"] == 0
        assert summary["total_estimated_effort_hours"] == 60
        assert summary["total_estimated_effort_weeks"] == 1.5  # 60/40
        assert len(summary["top_priorities"]) == 1
        assert summary["top_priorities"][0]["component"] == "Test Component"
        assert "recommendations" in summary
        assert "analysis_timestamp" in summary


if __name__ == "__main__":
    pytest.main([__file__])