"""
Unit tests for Gap Analyzer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.phoenix_system_review.assessment.gap_analyzer import (
    GapAnalyzer, GapAnalysisResult, IdentifiedGap, GapType, GapSeverity
)
from src.phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, Gap, ImpactLevel, Priority
)
from src.phoenix_system_review.analysis.component_evaluator import (
    ComponentEvaluation, EvaluationStatus, CriterionEvaluation
)
from src.phoenix_system_review.analysis.quality_assessor import (
    QualityAssessmentResult, QualityLevel
)
from src.phoenix_system_review.analysis.dependency_analyzer import (
    DependencyAnalysisResult, DependencyGraph, Dependency, DependencyType, DependencyStatus
)


class TestGapAnalyzer:
    """Test cases for GapAnalyzer class"""
    
    @pytest.fixture
    def gap_analyzer(self, tmp_path):
        """Create GapAnalyzer instance for testing"""
        return GapAnalyzer(project_root=str(tmp_path))
    
    @pytest.fixture
    def sample_components(self):
        """Create sample components for testing"""
        return [
            Component(
                name="nca_toolkit",
                category=ComponentCategory.INFRASTRUCTURE,
                path="src/nca_toolkit",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="revenue_tracking",
                category=ComponentCategory.MONETIZATION,
                path="src/revenue",
                status=ComponentStatus.DEGRADED
            ),
            Component(
                name="deployment_scripts",
                category=ComponentCategory.AUTOMATION,
                path="scripts/deployment",
                status=ComponentStatus.OPERATIONAL
            )
        ]
    
    @pytest.fixture
    def sample_component_evaluations(self, sample_components):
        """Create sample component evaluations"""
        evaluations = []
        
        # Complete component
        evaluations.append(ComponentEvaluation(
            component=sample_components[0],
            criteria_type="infrastructure",
            overall_score=0.95,
            completion_percentage=95.0,
            status=EvaluationStatus.PASSED,
            meets_minimum_score=True,
            critical_criteria_passed=True
        ))
        
        # Incomplete component
        evaluations.append(ComponentEvaluation(
            component=sample_components[1],
            criteria_type="monetization",
            overall_score=0.45,
            completion_percentage=45.0,
            status=EvaluationStatus.WARNING,
            meets_minimum_score=False,
            critical_criteria_passed=False,
            criterion_evaluations=[
                CriterionEvaluation(
                    criterion_id="critical_1",
                    criterion_name="Critical Feature",
                    status=EvaluationStatus.FAILED,
                    score=0.0,
                    weight=1.0,
                    required=True,
                    message="Critical feature not implemented"
                )
            ]
        ))
        
        # Moderately complete component
        evaluations.append(ComponentEvaluation(
            component=sample_components[2],
            criteria_type="automation",
            overall_score=0.75,
            completion_percentage=75.0,
            status=EvaluationStatus.PASSED,
            meets_minimum_score=True,
            critical_criteria_passed=True
        ))
        
        return evaluations
    
    @pytest.fixture
    def sample_quality_assessments(self, sample_components):
        """Create sample quality assessments"""
        return [
            QualityAssessmentResult(
                component=sample_components[0],
                quality_level=QualityLevel.GOOD,
                test_coverage=85.0
            ),
            QualityAssessmentResult(
                component=sample_components[1],
                quality_level=QualityLevel.POOR,
                test_coverage=25.0
            ),
            QualityAssessmentResult(
                component=sample_components[2],
                quality_level=QualityLevel.FAIR,
                test_coverage=60.0
            )
        ]
    
    @pytest.fixture
    def sample_dependency_analysis(self, sample_components):
        """Create sample dependency analysis"""
        dependency_graph = DependencyGraph(
            components={comp.name: comp for comp in sample_components},
            dependencies=[
                Dependency(
                    source="revenue_tracking",
                    target="nca_toolkit",
                    dependency_type=DependencyType.REQUIRED,
                    status=DependencyStatus.SATISFIED,
                    description="Revenue tracking depends on NCA toolkit"
                )
            ]
        )
        
        return DependencyAnalysisResult(
            dependency_graph=dependency_graph,
            circular_dependencies=[["revenue_tracking", "deployment_scripts", "revenue_tracking"]],
            missing_dependencies=[
                Dependency(
                    source="revenue_tracking",
                    target="missing_database",
                    dependency_type=DependencyType.REQUIRED,
                    status=DependencyStatus.MISSING,
                    description="Missing database dependency"
                )
            ],
            component_dependency_scores={
                "nca_toolkit": 0.9,
                "revenue_tracking": 0.5,
                "deployment_scripts": 0.8
            },
            overall_dependency_health=0.73
        )
    
    def test_gap_analyzer_initialization(self, tmp_path):
        """Test GapAnalyzer initialization"""
        analyzer = GapAnalyzer(project_root=str(tmp_path))
        
        assert analyzer.project_root == Path(tmp_path)
        assert analyzer.expected_components is not None
        assert analyzer.completion_criteria is not None
        assert analyzer.critical_thresholds is not None
        
        # Check that expected components are defined for all categories
        assert ComponentCategory.INFRASTRUCTURE in analyzer.expected_components
        assert ComponentCategory.MONETIZATION in analyzer.expected_components
        assert ComponentCategory.AUTOMATION in analyzer.expected_components
    
    def test_identify_gaps_complete_analysis(self, gap_analyzer, sample_components, 
                                           sample_component_evaluations, sample_quality_assessments,
                                           sample_dependency_analysis):
        """Test complete gap identification analysis"""
        result = gap_analyzer.identify_gaps(
            component_evaluations=sample_component_evaluations,
            quality_assessments=sample_quality_assessments,
            dependency_analysis=sample_dependency_analysis,
            discovered_components=sample_components
        )
        
        assert isinstance(result, GapAnalysisResult)
        assert len(result.identified_gaps) > 0
        assert result.total_effort_estimate > 0
        assert len(result.recommendations) > 0
        
        # Check that different gap types are identified
        gap_types = {gap.gap_type for gap in result.identified_gaps}
        assert GapType.MISSING_COMPONENT in gap_types
        assert GapType.INCOMPLETE_IMPLEMENTATION in gap_types
    
    def test_identify_missing_components(self, gap_analyzer, sample_components):
        """Test identification of missing components"""
        # Remove one expected component from discovered components
        incomplete_components = [comp for comp in sample_components if comp.name != "database"]
        
        gaps = gap_analyzer._identify_missing_components(incomplete_components)
        
        # Should identify missing database component
        missing_names = [gap.component_name for gap in gaps]
        assert "database" in missing_names
        
        # Check gap properties
        database_gap = next(gap for gap in gaps if gap.component_name == "database")
        assert database_gap.gap_type == GapType.MISSING_COMPONENT
        assert database_gap.severity == GapSeverity.CRITICAL
        assert database_gap.effort_estimate_hours > 0
        assert len(database_gap.acceptance_criteria) > 0
    
    def test_identify_incomplete_implementations(self, gap_analyzer, sample_component_evaluations):
        """Test identification of incomplete implementations"""
        gaps = gap_analyzer._identify_incomplete_implementations(sample_component_evaluations)
        
        # Should identify revenue_tracking as incomplete (45% completion)
        incomplete_names = [gap.component_name for gap in gaps]
        assert "revenue_tracking" in incomplete_names
        
        # Check gap properties
        revenue_gap = next(gap for gap in gaps if gap.component_name == "revenue_tracking")
        assert revenue_gap.gap_type == GapType.INCOMPLETE_IMPLEMENTATION
        assert revenue_gap.severity in [GapSeverity.HIGH, GapSeverity.CRITICAL]
        assert "45.0%" in revenue_gap.description
        
        # Should also identify critical criteria failure
        critical_gaps = [gap for gap in gaps if "critical_criteria" in gap.gap_id]
        assert len(critical_gaps) > 0
    
    def test_identify_dependency_gaps(self, gap_analyzer, sample_dependency_analysis):
        """Test identification of dependency gaps"""
        gaps = gap_analyzer._identify_dependency_gaps(sample_dependency_analysis)
        
        # Should identify missing dependency
        missing_dep_gaps = [gap for gap in gaps if gap.gap_type == GapType.DEPENDENCY_GAP and "missing_dep" in gap.gap_id]
        assert len(missing_dep_gaps) > 0
        
        # Should identify circular dependency
        circular_dep_gaps = [gap for gap in gaps if gap.gap_type == GapType.DEPENDENCY_GAP and "circular_dep" in gap.gap_id]
        assert len(circular_dep_gaps) > 0
        
        # Check missing dependency gap
        missing_gap = missing_dep_gaps[0]
        assert missing_gap.component_name == "revenue_tracking"
        assert "missing_database" in missing_gap.description
        assert missing_gap.severity == GapSeverity.HIGH
    
    def test_identify_quality_gaps(self, gap_analyzer, sample_quality_assessments):
        """Test identification of quality gaps"""
        gaps = gap_analyzer._identify_quality_gaps(sample_quality_assessments)
        
        # Should identify poor quality component
        quality_gap_names = [gap.component_name for gap in gaps]
        assert "revenue_tracking" in quality_gap_names  # Has POOR quality
        
        # Check quality gap properties
        poor_quality_gap = next(gap for gap in gaps if gap.component_name == "revenue_tracking")
        assert poor_quality_gap.gap_type == GapType.QUALITY_GAP
        assert poor_quality_gap.severity == GapSeverity.HIGH
        assert "poor" in poor_quality_gap.description.lower()
    
    def test_identify_integration_gaps(self, gap_analyzer, sample_component_evaluations, sample_dependency_analysis):
        """Test identification of integration gaps"""
        gaps = gap_analyzer._identify_integration_gaps(sample_component_evaluations, sample_dependency_analysis)
        
        # Should identify components with low dependency health scores
        integration_gap_names = [gap.component_name for gap in gaps]
        assert "revenue_tracking" in integration_gap_names  # Has 0.5 dependency score
        
        # Check integration gap properties
        integration_gap = next(gap for gap in gaps if gap.component_name == "revenue_tracking")
        assert integration_gap.gap_type == GapType.INTEGRATION_GAP
        assert integration_gap.severity == GapSeverity.MEDIUM
        assert "integration health" in integration_gap.description.lower()
    
    def test_identify_documentation_gaps(self, gap_analyzer, sample_components, tmp_path):
        """Test identification of documentation gaps"""
        # Set up temporary directory structure without README files
        gap_analyzer.project_root = tmp_path
        
        gaps = gap_analyzer._identify_documentation_gaps(sample_components)
        
        # Should identify missing README files for all components
        doc_gap_names = [gap.component_name for gap in gaps]
        assert len(doc_gap_names) == len(sample_components)
        
        # Check documentation gap properties
        doc_gap = gaps[0]
        assert doc_gap.gap_type == GapType.DOCUMENTATION_GAP
        assert doc_gap.severity == GapSeverity.LOW
        assert "README" in doc_gap.description
    
    def test_identify_testing_gaps(self, gap_analyzer, sample_components, sample_quality_assessments):
        """Test identification of testing gaps"""
        gaps = gap_analyzer._identify_testing_gaps(sample_components, sample_quality_assessments)
        
        # Should identify components with low test coverage
        testing_gap_names = [gap.component_name for gap in gaps]
        assert "revenue_tracking" in testing_gap_names  # Has 25% coverage
        assert "deployment_scripts" in testing_gap_names  # Has 60% coverage
        
        # Check testing gap properties
        testing_gap = next(gap for gap in gaps if gap.component_name == "revenue_tracking")
        assert testing_gap.gap_type == GapType.TESTING_GAP
        assert testing_gap.severity == GapSeverity.MEDIUM
        assert "25.0%" in testing_gap.description
    
    def test_identify_security_gaps(self, gap_analyzer, sample_components, sample_component_evaluations):
        """Test identification of security gaps"""
        # Add security-critical components
        security_components = sample_components + [
            Component(
                name="auth_service",
                category=ComponentCategory.SECURITY,
                path="src/auth",
                status=ComponentStatus.OPERATIONAL
            )
        ]
        
        gaps = gap_analyzer._identify_security_gaps(security_components, sample_component_evaluations)
        
        # Should identify security configuration gaps
        security_gap_names = [gap.component_name for gap in gaps]
        assert "auth_service" in security_gap_names
        
        # Check security gap properties
        security_gap = next(gap for gap in gaps if gap.component_name == "auth_service")
        assert security_gap.gap_type == GapType.SECURITY_GAP
        assert security_gap.severity == GapSeverity.HIGH
        assert "security configuration" in security_gap.description.lower()
    
    def test_gap_severity_determination(self, gap_analyzer):
        """Test gap severity determination based on completion percentage"""
        assert gap_analyzer._determine_severity_from_completion(20.0) == GapSeverity.CRITICAL
        assert gap_analyzer._determine_severity_from_completion(40.0) == GapSeverity.HIGH
        assert gap_analyzer._determine_severity_from_completion(60.0) == GapSeverity.MEDIUM
        assert gap_analyzer._determine_severity_from_completion(80.0) == GapSeverity.LOW
    
    def test_effort_estimation(self, gap_analyzer, sample_component_evaluations):
        """Test effort estimation for different types of gaps"""
        incomplete_evaluation = sample_component_evaluations[1]  # 45% complete
        
        # Test completion effort estimation
        effort = gap_analyzer._estimate_completion_effort(incomplete_evaluation)
        assert effort > 0
        assert effort >= 8  # Minimum effort
        
        # Test critical criteria effort estimation
        critical_effort = gap_analyzer._estimate_critical_criteria_effort(incomplete_evaluation)
        assert critical_effort >= 16  # Minimum for critical criteria
    
    def test_identified_gap_to_gap_model_conversion(self):
        """Test conversion of IdentifiedGap to Gap model"""
        identified_gap = IdentifiedGap(
            gap_id="test_gap",
            component_name="test_component",
            gap_type=GapType.MISSING_COMPONENT,
            severity=GapSeverity.HIGH,
            title="Test Gap",
            description="Test gap description",
            current_state="Current state",
            expected_state="Expected state",
            impact_description="Impact description",
            effort_estimate_hours=24,
            category=ComponentCategory.INFRASTRUCTURE,
            dependencies=["dep1", "dep2"],
            acceptance_criteria=["criteria1", "criteria2"]
        )
        
        gap_model = identified_gap.to_gap_model()
        
        assert isinstance(gap_model, Gap)
        assert gap_model.component == "test_component"
        assert gap_model.description == "Test gap description"
        assert gap_model.impact == ImpactLevel.HIGH
        assert gap_model.effort_estimate == 24
        assert gap_model.dependencies == ["dep1", "dep2"]
        assert gap_model.acceptance_criteria == ["criteria1", "criteria2"]
        assert gap_model.category == ComponentCategory.INFRASTRUCTURE
        assert gap_model.priority == Priority.HIGH
    
    def test_gap_analysis_result_generation(self, gap_analyzer):
        """Test generation of comprehensive gap analysis result"""
        # Create sample identified gaps
        identified_gaps = [
            IdentifiedGap(
                gap_id="critical_gap",
                component_name="critical_component",
                gap_type=GapType.MISSING_COMPONENT,
                severity=GapSeverity.CRITICAL,
                title="Critical Gap",
                description="Critical gap description",
                current_state="Missing",
                expected_state="Present",
                impact_description="Critical impact",
                effort_estimate_hours=40,
                category=ComponentCategory.INFRASTRUCTURE
            ),
            IdentifiedGap(
                gap_id="config_gap",
                component_name="config_component",
                gap_type=GapType.CONFIGURATION_GAP,
                severity=GapSeverity.MEDIUM,
                title="Config Gap",
                description="Configuration gap description",
                current_state="Incomplete config",
                expected_state="Complete config",
                impact_description="Medium impact",
                effort_estimate_hours=16,
                category=ComponentCategory.AUTOMATION
            )
        ]
        
        result = gap_analyzer._generate_gap_analysis_result(identified_gaps)
        
        assert isinstance(result, GapAnalysisResult)
        assert len(result.identified_gaps) == 2
        assert len(result.critical_gaps) == 1
        assert result.total_effort_estimate == 56  # 40 + 16
        assert len(result.completion_blockers) == 1  # Critical gap
        assert len(result.recommendations) > 0
        
        # Check gap summary
        assert result.gap_summary[GapType.MISSING_COMPONENT.value] == 1
        assert result.gap_summary[GapType.CONFIGURATION_GAP.value] == 1
    
    def test_expected_components_definition(self, gap_analyzer):
        """Test that expected components are properly defined"""
        expected = gap_analyzer.expected_components
        
        # Check that all categories have expected components
        assert ComponentCategory.INFRASTRUCTURE in expected
        assert ComponentCategory.MONETIZATION in expected
        assert ComponentCategory.AUTOMATION in expected
        
        # Check that critical infrastructure components are defined
        infra_components = expected[ComponentCategory.INFRASTRUCTURE]
        assert "nca_toolkit" in infra_components
        assert "podman_stack" in infra_components
        assert "database" in infra_components
        
        # Check component definitions have required fields
        nca_toolkit = infra_components["nca_toolkit"]
        assert "description" in nca_toolkit
        assert "severity" in nca_toolkit
        assert "effort_hours" in nca_toolkit
        assert "acceptance_criteria" in nca_toolkit
    
    def test_completion_criteria_definition(self, gap_analyzer):
        """Test that completion criteria are properly defined"""
        criteria = gap_analyzer.completion_criteria
        
        # Check that all categories have completion criteria
        assert ComponentCategory.INFRASTRUCTURE in criteria
        assert ComponentCategory.MONETIZATION in criteria
        assert ComponentCategory.AUTOMATION in criteria
        
        # Check that criteria have required fields
        infra_criteria = criteria[ComponentCategory.INFRASTRUCTURE]
        assert "minimum_completion" in infra_criteria
        assert "required_features" in infra_criteria
        assert "critical_thresholds" in infra_criteria
    
    def test_error_handling(self, gap_analyzer):
        """Test error handling in gap identification"""
        # Test with invalid inputs
        result = gap_analyzer.identify_gaps(
            component_evaluations=[],
            quality_assessments=[],
            dependency_analysis=DependencyAnalysisResult(dependency_graph=DependencyGraph()),
            discovered_components=[]
        )
        
        # Should return empty result without crashing
        assert isinstance(result, GapAnalysisResult)
        assert len(result.identified_gaps) >= 0  # May have missing component gaps
    
    @patch('src.phoenix_system_review.assessment.gap_analyzer.Path.exists')
    def test_configuration_gap_detection(self, mock_exists, gap_analyzer, sample_components):
        """Test configuration gap detection"""
        # Mock that configuration files don't exist
        mock_exists.return_value = False
        
        # Test with infrastructure component that should have compose.yaml
        podman_component = Component(
            name="podman_stack",
            category=ComponentCategory.INFRASTRUCTURE,
            path="infra/podman",
            status=ComponentStatus.OPERATIONAL
        )
        
        gaps = gap_analyzer._check_configuration_completeness(podman_component)
        
        # Should identify missing compose.yaml
        assert len(gaps) > 0
        config_gap = gaps[0]
        assert config_gap.gap_type == GapType.CONFIGURATION_GAP
        assert "compose.yaml" in config_gap.title
        assert config_gap.severity == GapSeverity.CRITICAL
    
    def test_recommendation_generation(self, gap_analyzer):
        """Test recommendation generation based on gaps"""
        # Create gaps with different severities
        critical_gap = IdentifiedGap(
            gap_id="critical",
            component_name="critical_comp",
            gap_type=GapType.MISSING_COMPONENT,
            severity=GapSeverity.CRITICAL,
            title="Critical Gap",
            description="Critical",
            current_state="Missing",
            expected_state="Present",
            impact_description="Critical impact",
            effort_estimate_hours=40,
            category=ComponentCategory.INFRASTRUCTURE
        )
        
        high_gap = IdentifiedGap(
            gap_id="high",
            component_name="high_comp",
            gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
            severity=GapSeverity.HIGH,
            title="High Gap",
            description="High priority",
            current_state="Incomplete",
            expected_state="Complete",
            impact_description="High impact",
            effort_estimate_hours=24,
            category=ComponentCategory.MONETIZATION
        )
        
        identified_gaps = [critical_gap, high_gap]
        critical_gaps = [critical_gap]
        completion_blockers = [critical_gap, high_gap]
        
        recommendations = gap_analyzer._generate_gap_recommendations(
            identified_gaps, critical_gaps, completion_blockers
        )
        
        assert len(recommendations) > 0
        
        # Should mention critical gaps
        critical_mentioned = any("critical" in rec.lower() for rec in recommendations)
        assert critical_mentioned
        
        # Should mention completion blockers
        blocker_mentioned = any("blocker" in rec.lower() for rec in recommendations)
        assert blocker_mentioned


class TestIdentifiedGap:
    """Test cases for IdentifiedGap class"""
    
    def test_identified_gap_creation(self):
        """Test IdentifiedGap creation and properties"""
        gap = IdentifiedGap(
            gap_id="test_gap",
            component_name="test_component",
            gap_type=GapType.MISSING_COMPONENT,
            severity=GapSeverity.HIGH,
            title="Test Gap",
            description="Test description",
            current_state="Current",
            expected_state="Expected",
            impact_description="Impact",
            effort_estimate_hours=16,
            category=ComponentCategory.INFRASTRUCTURE
        )
        
        assert gap.gap_id == "test_gap"
        assert gap.component_name == "test_component"
        assert gap.gap_type == GapType.MISSING_COMPONENT
        assert gap.severity == GapSeverity.HIGH
        assert gap.effort_estimate_hours == 16
        assert isinstance(gap.identified_date, datetime)
    
    def test_gap_model_conversion_mappings(self):
        """Test that severity and priority mappings work correctly"""
        # Test all severity levels
        severities = [
            (GapSeverity.CRITICAL, ImpactLevel.CRITICAL, Priority.CRITICAL),
            (GapSeverity.HIGH, ImpactLevel.HIGH, Priority.HIGH),
            (GapSeverity.MEDIUM, ImpactLevel.MEDIUM, Priority.MEDIUM),
            (GapSeverity.LOW, ImpactLevel.LOW, Priority.LOW)
        ]
        
        for severity, expected_impact, expected_priority in severities:
            gap = IdentifiedGap(
                gap_id="test",
                component_name="test",
                gap_type=GapType.MISSING_COMPONENT,
                severity=severity,
                title="Test",
                description="Test",
                current_state="Current",
                expected_state="Expected",
                impact_description="Impact",
                effort_estimate_hours=8,
                category=ComponentCategory.INFRASTRUCTURE
            )
            
            gap_model = gap.to_gap_model()
            assert gap_model.impact == expected_impact
            assert gap_model.priority == expected_priority


class TestGapAnalysisResult:
    """Test cases for GapAnalysisResult class"""
    
    def test_gap_analysis_result_creation(self):
        """Test GapAnalysisResult creation and properties"""
        result = GapAnalysisResult(
            total_effort_estimate=100,
            analysis_timestamp=datetime.now()
        )
        
        assert result.total_effort_estimate == 100
        assert isinstance(result.analysis_timestamp, datetime)
        assert len(result.identified_gaps) == 0
        assert len(result.recommendations) == 0
    
    def test_gap_analysis_result_with_gaps(self):
        """Test GapAnalysisResult with actual gaps"""
        gaps = [
            IdentifiedGap(
                gap_id="gap1",
                component_name="comp1",
                gap_type=GapType.MISSING_COMPONENT,
                severity=GapSeverity.CRITICAL,
                title="Gap 1",
                description="Description 1",
                current_state="Current",
                expected_state="Expected",
                impact_description="Impact",
                effort_estimate_hours=20,
                category=ComponentCategory.INFRASTRUCTURE
            ),
            IdentifiedGap(
                gap_id="gap2",
                component_name="comp2",
                gap_type=GapType.CONFIGURATION_GAP,
                severity=GapSeverity.MEDIUM,
                title="Gap 2",
                description="Description 2",
                current_state="Current",
                expected_state="Expected",
                impact_description="Impact",
                effort_estimate_hours=10,
                category=ComponentCategory.AUTOMATION
            )
        ]
        
        result = GapAnalysisResult(
            identified_gaps=gaps,
            critical_gaps=[gaps[0]],
            missing_components=["comp1"],
            total_effort_estimate=30
        )
        
        assert len(result.identified_gaps) == 2
        assert len(result.critical_gaps) == 1
        assert result.missing_components == ["comp1"]
        assert result.total_effort_estimate == 30


if __name__ == "__main__":
    pytest.main([__file__])