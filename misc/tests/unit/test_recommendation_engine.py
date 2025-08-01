"""
Unit tests for Recommendation Engine
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.phoenix_system_review.reporting.recommendation_engine import (
    RecommendationEngine, RecommendationReport, Recommendation, RecommendationType,
    RecommendationPriority, RiskLevel, RiskAssessment, ResourceAllocation
)
from src.phoenix_system_review.models.data_models import (
    AssessmentResults, CompletionScore, ComponentCategory, Priority
)
from src.phoenix_system_review.assessment.gap_analyzer import (
    GapAnalysisResult, IdentifiedGap, GapType, GapSeverity
)
from src.phoenix_system_review.assessment.priority_ranker import (
    PriorityRankingResult, PriorityScore, PriorityLevel, EffortLevel
)
from src.phoenix_system_review.assessment.completion_calculator import CompletionTier


class TestRecommendationEngine:
    """Test cases for RecommendationEngine"""
    
    @pytest.fixture
    def recommendation_engine(self):
        """Create recommendation engine instance"""
        return RecommendationEngine()
    
    @pytest.fixture
    def sample_assessment_results(self):
        """Create sample assessment results"""
        return AssessmentResults(
            overall_completion=75.0,
            component_scores={
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
                )
            },
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
    
    @pytest.fixture
    def sample_gap_analysis(self):
        """Create sample gap analysis result"""
        gaps = [
            IdentifiedGap(
                gap_id="critical_security",
                component_name="security_auth",
                gap_type=GapType.SECURITY_GAP,
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
            ),
            IdentifiedGap(
                gap_id="monetization_tracking",
                component_name="revenue_tracking",
                gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                severity=GapSeverity.HIGH,
                title="Incomplete revenue tracking",
                description="Revenue tracking system incomplete",
                current_state="Basic implementation",
                expected_state="Full tracking operational",
                impact_description="Cannot track revenue accurately",
                effort_estimate_hours=40,
                category=ComponentCategory.MONETIZATION,
                dependencies=[],
                acceptance_criteria=["Revenue tracking operational", "Reports generated"]
            )
        ]
        
        return GapAnalysisResult(
            identified_gaps=gaps,
            gap_summary={"security_gap": 1, "missing_component": 1, "incomplete_implementation": 1},
            critical_gaps=[gaps[0]],
            missing_components=["monitoring_system"],
            incomplete_implementations=["security_auth", "revenue_tracking"],
            configuration_gaps=[],
            total_effort_estimate=120,
            completion_blockers=[gaps[0]],
            recommendations=["Fix critical security gap", "Implement monitoring", "Complete revenue tracking"]
        )
    
    @pytest.fixture
    def sample_priority_ranking(self):
        """Create sample priority ranking result"""
        priority_scores = [
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
                component_name="revenue_tracking",
                priority_level=PriorityLevel.HIGH,
                priority_score=80.0,
                business_impact_score=90.0,
                technical_complexity_score=60.0,
                dependency_urgency_score=70.0,
                effort_estimate=EffortLevel.MEDIUM,
                effort_hours=40,
                roi_score=85.0,
                risk_factor=0.7,
                completion_tier=CompletionTier.ESSENTIAL,
                justification="High business impact for revenue",
                dependencies=[],
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
                roi_score=40.0,
                risk_factor=0.1,
                completion_tier=CompletionTier.OPTIONAL,
                justification="Nice to have documentation",
                dependencies=[],
                blockers=[]
            )
        ]
        
        return PriorityRankingResult(
            priority_scores=priority_scores,
            priority_matrix={
                "critical": [priority_scores[0]],
                "high": [priority_scores[1]],
                "low": [priority_scores[2]]
            },
            effort_distribution={"medium": 2, "low": 1},
            critical_path=["security_auth", "revenue_tracking"],
            quick_wins=["documentation"],
            high_impact_items=[priority_scores[0], priority_scores[1]],
            recommendations=["Focus on security", "Complete revenue tracking", "Quick win with docs"],
            total_estimated_effort=88
        )
    
    def test_generate_recommendations(self, recommendation_engine, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test recommendation generation"""
        report = recommendation_engine.generate_recommendations(
            sample_assessment_results,
            sample_gap_analysis,
            sample_priority_ranking
        )
        
        assert isinstance(report, RecommendationReport)
        assert len(report.strategic_recommendations) > 0
        assert len(report.tactical_recommendations) > 0
        assert len(report.quick_wins) > 0
        assert len(report.critical_path_recommendations) > 0
        assert report.risk_assessment is not None
        assert len(report.executive_summary) > 0
        assert len(report.implementation_roadmap) > 0
        assert len(report.success_metrics) > 0
        assert isinstance(report.generated_timestamp, datetime)
    
    def test_generate_strategic_recommendations(self, recommendation_engine, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test strategic recommendation generation"""
        strategic_recs = recommendation_engine._generate_strategic_recommendations(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        assert isinstance(strategic_recs, list)
        assert len(strategic_recs) > 0
        
        for rec in strategic_recs:
            assert isinstance(rec, Recommendation)
            assert rec.recommendation_type == RecommendationType.STRATEGIC
            assert rec.priority in [RecommendationPriority.IMMEDIATE, RecommendationPriority.HIGH]
            assert rec.effort_estimate_hours > 0
            assert len(rec.success_criteria) > 0
    
    def test_generate_tactical_recommendations(self, recommendation_engine, sample_gap_analysis, sample_priority_ranking):
        """Test tactical recommendation generation"""
        tactical_recs = recommendation_engine._generate_tactical_recommendations(
            sample_gap_analysis, sample_priority_ranking
        )
        
        assert isinstance(tactical_recs, list)
        assert len(tactical_recs) > 0
        
        for rec in tactical_recs:
            assert isinstance(rec, Recommendation)
            assert rec.recommendation_type == RecommendationType.TACTICAL
            assert rec.effort_estimate_hours > 0
            assert len(rec.affected_components) > 0
    
    def test_generate_operational_recommendations(self, recommendation_engine, sample_assessment_results, sample_gap_analysis):
        """Test operational recommendation generation"""
        operational_recs = recommendation_engine._generate_operational_recommendations(
            sample_assessment_results, sample_gap_analysis
        )
        
        assert isinstance(operational_recs, list)
        # May be empty if no testing gaps in sample data
        
        for rec in operational_recs:
            assert isinstance(rec, Recommendation)
            assert rec.recommendation_type == RecommendationType.OPERATIONAL
    
    def test_identify_quick_wins(self, recommendation_engine, sample_priority_ranking, sample_gap_analysis):
        """Test quick win identification"""
        quick_wins = recommendation_engine._identify_quick_wins(
            sample_priority_ranking, sample_gap_analysis
        )
        
        assert isinstance(quick_wins, list)
        assert len(quick_wins) > 0
        
        for rec in quick_wins:
            assert isinstance(rec, Recommendation)
            assert rec.recommendation_type == RecommendationType.QUICK_WIN
            assert rec.effort_estimate_hours <= 40  # Should be relatively low effort
    
    def test_generate_critical_path_recommendations(self, recommendation_engine, sample_priority_ranking, sample_gap_analysis):
        """Test critical path recommendation generation"""
        critical_path_recs = recommendation_engine._generate_critical_path_recommendations(
            sample_priority_ranking, sample_gap_analysis
        )
        
        assert isinstance(critical_path_recs, list)
        assert len(critical_path_recs) > 0
        
        for rec in critical_path_recs:
            assert isinstance(rec, Recommendation)
            assert rec.recommendation_type == RecommendationType.CRITICAL_PATH
            assert rec.priority == RecommendationPriority.IMMEDIATE
            assert len(rec.risks_if_ignored) > 0
    
    def test_generate_resource_allocation(self, recommendation_engine, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test resource allocation generation"""
        allocations = recommendation_engine._generate_resource_allocation(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        assert isinstance(allocations, list)
        
        for allocation in allocations:
            assert isinstance(allocation, ResourceAllocation)
            assert allocation.allocation_percentage > 0
            assert allocation.allocation_percentage <= 100
            assert len(allocation.justification) > 0
            assert len(allocation.skills_required) > 0
    
    def test_perform_risk_assessment(self, recommendation_engine, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test risk assessment"""
        risk_assessment = recommendation_engine._perform_risk_assessment(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        assert isinstance(risk_assessment, RiskAssessment)
        assert isinstance(risk_assessment.overall_risk_level, RiskLevel)
        assert 0 <= risk_assessment.deployment_readiness_score <= 100
        assert len(risk_assessment.risk_factors) > 0
        assert len(risk_assessment.mitigation_strategies) > 0
        assert len(risk_assessment.critical_blockers) > 0
        assert isinstance(risk_assessment.recommended_deployment_timeline, datetime)
        assert len(risk_assessment.rollback_plan) > 0
        assert len(risk_assessment.monitoring_requirements) > 0
    
    def test_risk_level_calculation(self, recommendation_engine):
        """Test risk level calculation based on different scenarios"""
        # Low completion scenario
        low_completion_results = AssessmentResults(
            overall_completion=60.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        gap_analysis_with_critical = GapAnalysisResult(
            identified_gaps=[],
            critical_gaps=[Mock() for _ in range(5)],  # 5 critical gaps
            missing_components=[],
            incomplete_implementations=[],
            configuration_gaps=[],
            total_effort_estimate=100,
            completion_blockers=[],
            recommendations=[]
        )
        
        risk_assessment = recommendation_engine._perform_risk_assessment(
            low_completion_results, gap_analysis_with_critical, Mock()
        )
        
        assert risk_assessment.overall_risk_level == RiskLevel.CRITICAL
        
        # High completion scenario
        high_completion_results = AssessmentResults(
            overall_completion=96.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        gap_analysis_minimal = GapAnalysisResult(
            identified_gaps=[],
            critical_gaps=[],
            missing_components=[],
            incomplete_implementations=[],
            configuration_gaps=[],
            total_effort_estimate=10,
            completion_blockers=[],
            recommendations=[]
        )
        
        risk_assessment = recommendation_engine._perform_risk_assessment(
            high_completion_results, gap_analysis_minimal, Mock()
        )
        
        assert risk_assessment.overall_risk_level == RiskLevel.LOW
    
    def test_format_recommendations_markdown(self, recommendation_engine, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test markdown formatting"""
        report = recommendation_engine.generate_recommendations(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        markdown = recommendation_engine.format_recommendations_markdown(report)
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "# Phoenix Hydra System Recommendations" in markdown
        assert "## Executive Summary" in markdown
        assert "## Risk Assessment" in markdown
        assert "## Strategic Recommendations" in markdown
        assert "## Quick Wins" in markdown
        assert "## Critical Path" in markdown
        
        # Check for emojis and formatting
        assert "🔴" in markdown or "🟠" in markdown or "🟡" in markdown  # Priority emojis
        assert "**" in markdown  # Bold formatting
    
    def test_generate_executive_summary(self, recommendation_engine):
        """Test executive summary generation"""
        strategic_recs = [
            Recommendation(
                id="test_strategic",
                title="Test Strategic Recommendation",
                description="Test description",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.IMMEDIATE,
                rationale="Test rationale",
                impact_description="Test impact",
                effort_estimate_hours=40
            )
        ]
        
        tactical_recs = []
        quick_wins = [Mock()]
        
        risk_assessment = RiskAssessment(
            overall_risk_level=RiskLevel.MEDIUM,
            deployment_readiness_score=75.0,
            critical_blockers=["Test blocker"],
            recommended_deployment_timeline=datetime.now() + timedelta(weeks=2)
        )
        
        summary = recommendation_engine._generate_executive_summary(
            strategic_recs, tactical_recs, quick_wins, risk_assessment
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Risk Level:" in summary
        assert "Deployment Readiness:" in summary
        assert "75.0%" in summary
        assert "Strategic Priority:" in summary
        assert "Quick Wins:" in summary
        assert "Critical Blockers:" in summary
    
    def test_create_implementation_roadmap(self, recommendation_engine):
        """Test implementation roadmap creation"""
        strategic_recs = [
            Recommendation(
                id="strategic_immediate",
                title="Immediate Strategic Task",
                description="Test",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.IMMEDIATE,
                rationale="Test",
                impact_description="Test",
                effort_estimate_hours=40
            ),
            Recommendation(
                id="strategic_high",
                title="High Priority Strategic Task",
                description="Test",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.HIGH,
                rationale="Test",
                impact_description="Test",
                effort_estimate_hours=40
            )
        ]
        
        tactical_recs = [
            Recommendation(
                id="tactical_immediate",
                title="Immediate Tactical Task",
                description="Test",
                recommendation_type=RecommendationType.TACTICAL,
                priority=RecommendationPriority.IMMEDIATE,
                rationale="Test",
                impact_description="Test",
                effort_estimate_hours=40
            )
        ]
        
        operational_recs = []
        priority_ranking = Mock()
        
        roadmap = recommendation_engine._create_implementation_roadmap(
            strategic_recs, tactical_recs, operational_recs, priority_ranking
        )
        
        assert isinstance(roadmap, list)
        assert len(roadmap) > 0
        assert any("Phase 1" in phase for phase in roadmap)
        assert any("Phase 2" in phase for phase in roadmap)
    
    def test_define_success_metrics(self, recommendation_engine, sample_assessment_results, sample_gap_analysis):
        """Test success metrics definition"""
        metrics = recommendation_engine._define_success_metrics(
            sample_assessment_results, sample_gap_analysis
        )
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        # Check for key metrics
        assert any("completion" in metric.lower() for metric in metrics)
        assert any("critical gaps" in metric.lower() for metric in metrics)
        assert any("security" in metric.lower() for metric in metrics)
        assert any("test coverage" in metric.lower() for metric in metrics)
    
    def test_format_recommendation_markdown(self, recommendation_engine):
        """Test individual recommendation markdown formatting"""
        rec = Recommendation(
            id="test_rec",
            title="Test Recommendation",
            description="Test description",
            recommendation_type=RecommendationType.STRATEGIC,
            priority=RecommendationPriority.HIGH,
            rationale="Test rationale",
            impact_description="Test impact",
            effort_estimate_hours=40,
            affected_components=["component1", "component2"],
            success_criteria=["Criterion 1", "Criterion 2"],
            risks_if_ignored=["Risk 1", "Risk 2"],
            business_value="High business value",
            technical_complexity="Medium complexity"
        )
        
        formatted = recommendation_engine._format_recommendation_markdown(rec)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "### 🟠 Test Recommendation" in formatted
        assert "**Description:** Test description" in formatted
        assert "**Rationale:** Test rationale" in formatted
        assert "**Impact:** Test impact" in formatted
        assert "**Effort:** 40 hours" in formatted
        assert "**Business Value:** High business value" in formatted
        assert "**Affected Components:** component1, component2" in formatted
        assert "**Success Criteria:**" in formatted
        assert "- Criterion 1" in formatted
        assert "**Risks if Ignored:**" in formatted
        assert "- ⚠️ Risk 1" in formatted
    
    def test_priority_emoji_mapping(self, recommendation_engine):
        """Test priority emoji mapping"""
        assert recommendation_engine._get_priority_emoji(RecommendationPriority.IMMEDIATE) == "🔴"
        assert recommendation_engine._get_priority_emoji(RecommendationPriority.HIGH) == "🟠"
        assert recommendation_engine._get_priority_emoji(RecommendationPriority.MEDIUM) == "🟡"
        assert recommendation_engine._get_priority_emoji(RecommendationPriority.LOW) == "🟢"
    
    def test_risk_emoji_mapping(self, recommendation_engine):
        """Test risk emoji mapping"""
        assert recommendation_engine._get_risk_emoji(RiskLevel.CRITICAL) == "🔴"
        assert recommendation_engine._get_risk_emoji(RiskLevel.HIGH) == "🟠"
        assert recommendation_engine._get_risk_emoji(RiskLevel.MEDIUM) == "🟡"
        assert recommendation_engine._get_risk_emoji(RiskLevel.LOW) == "🟢"
        assert recommendation_engine._get_risk_emoji(RiskLevel.MINIMAL) == "✅"
    
    def test_configuration_methods(self, recommendation_engine):
        """Test configuration definition methods"""
        # Test recommendation templates
        templates = recommendation_engine._define_recommendation_templates()
        assert isinstance(templates, dict)
        assert "foundation" in templates
        assert "integration" in templates
        
        # Test risk criteria
        risk_criteria = recommendation_engine._define_risk_criteria()
        assert isinstance(risk_criteria, dict)
        assert "completion_thresholds" in risk_criteria
        assert "gap_thresholds" in risk_criteria
        
        # Test resource models
        resource_models = recommendation_engine._define_resource_models()
        assert isinstance(resource_models, dict)
        assert "development" in resource_models
        
        # Test business weights
        business_weights = recommendation_engine._define_business_weights()
        assert isinstance(business_weights, dict)
        assert ComponentCategory.MONETIZATION in business_weights
        assert ComponentCategory.INFRASTRUCTURE in business_weights
    
    def test_error_handling(self, recommendation_engine):
        """Test error handling in recommendation generation"""
        # Test with invalid inputs
        invalid_assessment = AssessmentResults(
            overall_completion=0.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        invalid_gap_analysis = GapAnalysisResult()
        invalid_priority_ranking = PriorityRankingResult()
        
        report = recommendation_engine.generate_recommendations(
            invalid_assessment, invalid_gap_analysis, invalid_priority_ranking
        )
        
        assert isinstance(report, RecommendationReport)
        # Should handle gracefully without crashing
    
    def test_monetization_focus(self, recommendation_engine, sample_assessment_results, sample_gap_analysis, sample_priority_ranking):
        """Test that monetization gaps get appropriate strategic focus"""
        report = recommendation_engine.generate_recommendations(
            sample_assessment_results, sample_gap_analysis, sample_priority_ranking
        )
        
        # Should have strategic recommendation for monetization
        monetization_recs = [rec for rec in report.strategic_recommendations 
                           if "monetization" in rec.title.lower() or "revenue" in rec.title.lower()]
        
        assert len(monetization_recs) > 0
        
        # Should be high priority
        for rec in monetization_recs:
            assert rec.priority in [RecommendationPriority.IMMEDIATE, RecommendationPriority.HIGH]
    
    def test_completion_level_recommendations(self, recommendation_engine):
        """Test recommendations based on different completion levels"""
        gap_analysis = GapAnalysisResult()
        priority_ranking = PriorityRankingResult()
        
        # Test low completion (< 70%)
        low_completion = AssessmentResults(
            overall_completion=65.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        strategic_recs = recommendation_engine._generate_strategic_recommendations(
            low_completion, gap_analysis, priority_ranking
        )
        
        foundation_recs = [rec for rec in strategic_recs if "foundation" in rec.title.lower()]
        assert len(foundation_recs) > 0
        
        # Test medium completion (70-85%)
        medium_completion = AssessmentResults(
            overall_completion=80.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        strategic_recs = recommendation_engine._generate_strategic_recommendations(
            medium_completion, gap_analysis, priority_ranking
        )
        
        integration_recs = [rec for rec in strategic_recs if "integration" in rec.title.lower()]
        assert len(integration_recs) > 0
        
        # Test high completion (85-95%)
        high_completion = AssessmentResults(
            overall_completion=90.0,
            component_scores={},
            identified_gaps=[],
            prioritized_tasks=[],
            recommendations=[]
        )
        
        strategic_recs = recommendation_engine._generate_strategic_recommendations(
            high_completion, gap_analysis, priority_ranking
        )
        
        production_recs = [rec for rec in strategic_recs if "production" in rec.title.lower()]
        assert len(production_recs) > 0


if __name__ == "__main__":
    pytest.main([__file__])