"""
Unit tests for Component Evaluator
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from src.phoenix_system_review.analysis.component_evaluator import (
    ComponentEvaluator,
    ComponentEvaluation,
    CriterionEvaluation,
    EvaluationStatus
)
from src.phoenix_system_review.models.data_models import Component, ComponentCategory, Priority
from src.phoenix_system_review.criteria.infrastructure_criteria import InfrastructureComponent
from src.phoenix_system_review.criteria.monetization_criteria import MonetizationComponent
from src.phoenix_system_review.criteria.automation_criteria import AutomationComponent


class TestComponentEvaluator:
    """Test cases for ComponentEvaluator class"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_files = [
                ".vscode/tasks.json",
                "pyproject.toml",
                "infra/podman/compose.yaml",
                "configs/phoenix-monetization.json"
            ]
            
            for file_path in test_files:
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("{}")
            
            yield temp_dir
    
    @pytest.fixture
    def component_evaluator(self, temp_project_dir):
        """Create ComponentEvaluator instance for testing"""
        return ComponentEvaluator(temp_project_dir)
    
    @pytest.fixture
    def sample_infrastructure_component(self):
        """Create sample infrastructure component"""
        return Component(
            name="NCA Toolkit",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/api/nca_toolkit.py",
            description="Multimedia processing API toolkit",
            configuration={"endpoints": ["transcribe", "caption", "compose"]}
        )
    
    def test_evaluator_initialization(self, component_evaluator):
        """Test component evaluator initialization"""
        assert component_evaluator is not None
        assert component_evaluator.infrastructure_criteria is not None
        assert component_evaluator.monetization_criteria is not None
        assert component_evaluator.automation_criteria is not None
        assert len(component_evaluator.component_type_mappings) == 3
    
    def test_determine_infrastructure_component_type(self, component_evaluator):
        """Test infrastructure component type determination"""
        # Test NCA Toolkit
        nca_component = Component(
            name="NCA Toolkit API",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/api/nca_toolkit.py",
            description="API endpoints"
        )
        component_type = component_evaluator._get_infrastructure_component_type(nca_component)
        assert component_type == InfrastructureComponent.NCA_TOOLKIT
        
        # Test unknown component
        unknown_component = Component(
            name="Unknown Service",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/unknown/service.py",
            description="Unknown service"
        )
        component_type = component_evaluator._get_infrastructure_component_type(unknown_component)
        assert component_type is None
    
    def test_evaluate_infrastructure_component(self, component_evaluator, sample_infrastructure_component):
        """Test evaluation of infrastructure component"""
        evaluation = component_evaluator.evaluate_component(sample_infrastructure_component)
        
        assert isinstance(evaluation, ComponentEvaluation)
        assert evaluation.component == sample_infrastructure_component
        assert evaluation.criteria_type == str(InfrastructureComponent.NCA_TOOLKIT)
        assert 0.0 <= evaluation.overall_score <= 1.0
        assert 0.0 <= evaluation.completion_percentage <= 100.0
        assert evaluation.status in [EvaluationStatus.PASSED, EvaluationStatus.WARNING, EvaluationStatus.FAILED]
        assert len(evaluation.criterion_evaluations) > 0
        assert isinstance(evaluation.meets_minimum_score, bool)
        assert isinstance(evaluation.critical_criteria_passed, bool)
    
    def test_evaluate_unknown_component(self, component_evaluator):
        """Test evaluation of unknown component type"""
        unknown_component = Component(
            name="Unknown Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/unknown/component.py",
            description="Unknown component type"
        )
        
        evaluation = component_evaluator.evaluate_component(unknown_component)
        
        assert evaluation.status == EvaluationStatus.NOT_EVALUATED
        assert evaluation.overall_score == 0.0
        assert evaluation.completion_percentage == 0.0
        assert len(evaluation.issues) > 0
        assert "not evaluated" in evaluation.issues[0].lower()
    
    def test_calculate_system_completion_empty(self, component_evaluator):
        """Test system completion calculation with empty evaluations"""
        completion = component_evaluator.calculate_system_completion([])
        
        assert completion["overall_completion"] == 0.0
        assert completion["total_components"] == 0
        assert completion["evaluated_components"] == 0
        assert completion["passed_components"] == 0
        assert completion["failed_components"] == 0
        assert completion["critical_issues"] == 0
    
    def test_generate_evaluation_report(self, component_evaluator, sample_infrastructure_component):
        """Test evaluation report generation"""
        components = [sample_infrastructure_component]
        evaluations = component_evaluator.evaluate_components(components)
        
        report = component_evaluator.generate_evaluation_report(evaluations)
        
        assert "system_metrics" in report
        assert "component_evaluations" in report
        assert "top_issues" in report
        assert "top_recommendations" in report
        assert "evaluation_timestamp" in report
    
    def test_criterion_evaluation_creation(self):
        """Test creation of criterion evaluation"""
        criterion_eval = CriterionEvaluation(
            criterion_id="test_criterion",
            criterion_name="Test Criterion",
            status=EvaluationStatus.PASSED,
            score=0.8,
            weight=0.25,
            required=True,
            message="Test passed"
        )
        
        assert criterion_eval.criterion_id == "test_criterion"
        assert criterion_eval.criterion_name == "Test Criterion"
        assert criterion_eval.status == EvaluationStatus.PASSED
        assert criterion_eval.score == 0.8
        assert criterion_eval.weight == 0.25
        assert criterion_eval.required is True
        assert criterion_eval.message == "Test passed"
        assert isinstance(criterion_eval.details, dict)
    
    def test_check_expected_value_file_exists(self, component_evaluator, temp_project_dir):
        """Test checking expected value for existing file"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.AUTOMATION,
            path="/test/component.py",
            description="Test"
        )
        
        # Test existing file
        result = component_evaluator._check_expected_value(component, ".vscode/tasks.json")
        assert result is True
        
        # Test non-existing file
        result = component_evaluator._check_expected_value(component, "non_existent_file.txt")
        assert result is False
    
    def test_calculate_overall_score(self, component_evaluator):
        """Test overall score calculation"""
        criterion_evaluations = [
            CriterionEvaluation(
                criterion_id="crit1",
                criterion_name="Criterion 1",
                status=EvaluationStatus.PASSED,
                score=0.8,
                weight=0.5,
                required=True,
                message="Passed"
            ),
            CriterionEvaluation(
                criterion_id="crit2",
                criterion_name="Criterion 2",
                status=EvaluationStatus.WARNING,
                score=0.6,
                weight=0.3,
                required=False,
                message="Warning"
            ),
            CriterionEvaluation(
                criterion_id="crit3",
                criterion_name="Criterion 3",
                status=EvaluationStatus.FAILED,
                score=0.2,
                weight=0.2,
                required=False,
                message="Failed"
            )
        ]
        
        overall_score = component_evaluator._calculate_overall_score(criterion_evaluations)
        
        # Expected: (0.8 * 0.5) + (0.6 * 0.3) + (0.2 * 0.2) = 0.4 + 0.18 + 0.04 = 0.62
        expected_score = 0.62
        assert abs(overall_score - expected_score) < 0.01
    
    def test_calculate_overall_score_empty(self, component_evaluator):
        """Test overall score calculation with empty evaluations"""
        overall_score = component_evaluator._calculate_overall_score([])
        assert overall_score == 0.0
    
    def test_timestamp_generation(self, component_evaluator):
        """Test timestamp generation for reports"""
        timestamp = component_evaluator._get_timestamp()
        
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Should be in ISO format
        assert "T" in timestamp


if __name__ == "__main__":
    pytest.main([__file__])