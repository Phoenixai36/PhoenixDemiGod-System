"""
Unit tests for Component Evaluator module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.phoenix_system_review.analysis.component_evaluator import (
    ComponentEvaluator,
    ComponentEvaluation,
    CriterionEvaluation,
    EvaluationStatus
)
from src.phoenix_system_review.models.data_models import (
    Component,
    ComponentCategory,
    ComponentStatus,
    EvaluationCriterion,
    CriterionType
)


class TestComponentEvaluator:
    """Test component evaluator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.project_root = "/test/project"
        self.evaluator = ComponentEvaluator(self.project_root)
    
    def test_initialization(self):
        """Test evaluator initialization"""
        assert self.evaluator.project_root == Path(self.project_root)
        assert self.evaluator.infrastructure_criteria is not None
        assert self.evaluator.monetization_criteria is not None
        assert self.evaluator.automation_criteria is not None
    
    def test_evaluate_component_with_automation_component(self):
        """Test evaluating an automation component"""
        # Create test component
        component = Component(
            name="VS Code Tasks",
            category=ComponentCategory.AUTOMATION,
            path=".vscode/",
            status=ComponentStatus.OPERATIONAL,
            description="VS Code task automation"
        )
        
        # Mock the automation criteria
        mock_criteria = [
            EvaluationCriterion(
                id="test_criterion",
                name="Test Criterion",
                description="Test criterion description",
                criterion_type=CriterionType.EXISTENCE,
                weight=1.0,
                is_critical=True,
                evaluation_method="file_exists",
                parameters={"file_path": ".vscode/tasks.json"}
            )
        ]
        
        with patch.object(self.evaluator.automation_criteria, 'get_automation_criteria', return_value=mock_criteria):
            with patch.object(Path, 'exists', return_value=True):
                evaluation = self.evaluator.evaluate_component(component)
        
        assert isinstance(evaluation, ComponentEvaluation)
        assert evaluation.component == component
        assert evaluation.status in [EvaluationStatus.PASSED, EvaluationStatus.WARNING, EvaluationStatus.FAILED]
        assert 0 <= evaluation.completion_percentage <= 100
        assert len(evaluation.criterion_evaluations) > 0
    
    def test_evaluate_component_unknown_type(self):
        """Test evaluating component with unknown type"""
        component = Component(
            name="Unknown Component",
            category=ComponentCategory.DOCUMENTATION,  # Not handled by current mappings
            path="./",
            status=ComponentStatus.UNKNOWN
        )
        
        evaluation = self.evaluator.evaluate_component(component)
        
        assert evaluation.status == EvaluationStatus.NOT_EVALUATED
        assert evaluation.completion_percentage == 0.0
        assert "Unknown component type" in evaluation.issues[0]
    
    def test_validate_existence_file_exists(self):
        """Test existence validation when file exists"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.AUTOMATION,
            path="./",
            status=ComponentStatus.OPERATIONAL
        )
        
        criterion = EvaluationCriterion(
            id="test_file_exists",
            name="Test File Exists",
            description="Test file existence",
            criterion_type=CriterionType.EXISTENCE,
            parameters={"file_path": "test.txt"}
        )
        
        with patch.object(Path, 'exists', return_value=True):
            score, status, message = self.evaluator._validate_existence(component, criterion)
        
        assert score == 1.0
        assert status == EvaluationStatus.PASSED
        assert "exists" in message
    
    def test_validate_existence_file_missing(self):
        """Test existence validation when file is missing"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.AUTOMATION,
            path="./",
            status=ComponentStatus.OPERATIONAL
        )
        
        criterion = EvaluationCriterion(
            id="test_file_missing",
            name="Test File Missing",
            description="Test file missing",
            criterion_type=CriterionType.EXISTENCE,
            parameters={"file_path": "missing.txt"}
        )
        
        with patch.object(Path, 'exists', return_value=False):
            score, status, message = self.evaluator._validate_existence(component, criterion)
        
        assert score == 0.0
        assert status == EvaluationStatus.FAILED
        assert "not found" in message
    
    def test_validate_configuration_json_file(self):
        """Test configuration validation for JSON file"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.AUTOMATION,
            path="./",
            status=ComponentStatus.OPERATIONAL
        )
        
        criterion = EvaluationCriterion(
            id="test_json_config",
            name="Test JSON Config",
            description="Test JSON configuration",
            criterion_type=CriterionType.CONFIGURATION,
            parameters={"file_path": "config.json"}
        )
        
        mock_json_content = {"test_key": "test_value"}
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open_json(mock_json_content)):
                score, status, message = self.evaluator._validate_configuration(component, criterion)
        
        assert score >= 0.8
        assert status == EvaluationStatus.PASSED
        assert "valid" in message
    
    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        criterion_evaluations = [
            CriterionEvaluation(
                criterion_id="test1",
                criterion_name="Test 1",
                status=EvaluationStatus.PASSED,
                score=1.0,
                weight=1.0,
                required=True,
                message="Test passed"
            ),
            CriterionEvaluation(
                criterion_id="test2",
                criterion_name="Test 2",
                status=EvaluationStatus.FAILED,
                score=0.0,
                weight=0.5,
                required=False,
                message="Test failed"
            )
        ]
        
        overall_score = self.evaluator._calculate_overall_score(criterion_evaluations)
        
        # Expected: (1.0 * 1.0 + 0.0 * 0.5) / (1.0 + 0.5) = 1.0 / 1.5 = 0.667
        expected_score = 1.0 / 1.5
        assert abs(overall_score - expected_score) < 0.01
    
    def test_check_critical_criteria_all_passed(self):
        """Test critical criteria check when all pass"""
        criterion_evaluations = [
            CriterionEvaluation(
                criterion_id="critical1",
                criterion_name="Critical 1",
                status=EvaluationStatus.PASSED,
                score=1.0,
                weight=1.0,
                required=True,
                message="Critical passed"
            ),
            CriterionEvaluation(
                criterion_id="non_critical",
                criterion_name="Non Critical",
                status=EvaluationStatus.FAILED,
                score=0.0,
                weight=1.0,
                required=False,
                message="Non-critical failed"
            )
        ]
        
        critical_criteria = ["critical1"]
        result = self.evaluator._check_critical_criteria(criterion_evaluations, critical_criteria)
        
        assert result is True
    
    def test_check_critical_criteria_some_failed(self):
        """Test critical criteria check when some fail"""
        criterion_evaluations = [
            CriterionEvaluation(
                criterion_id="critical1",
                criterion_name="Critical 1",
                status=EvaluationStatus.FAILED,
                score=0.0,
                weight=1.0,
                required=True,
                message="Critical failed"
            )
        ]
        
        critical_criteria = ["critical1"]
        result = self.evaluator._check_critical_criteria(criterion_evaluations, critical_criteria)
        
        assert result is False
    
    def test_evaluate_components_multiple(self):
        """Test evaluating multiple components"""
        components = [
            Component(
                name="Component 1",
                category=ComponentCategory.AUTOMATION,
                path="./",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Component 2", 
                category=ComponentCategory.AUTOMATION,
                path="./",
                status=ComponentStatus.DEGRADED
            )
        ]
        
        # Mock criteria for automation components
        mock_criteria = [
            EvaluationCriterion(
                id="test_criterion",
                name="Test Criterion",
                description="Test criterion",
                criterion_type=CriterionType.EXISTENCE,
                weight=1.0,
                is_critical=False,
                parameters={"file_path": "test.txt"}
            )
        ]
        
        with patch.object(self.evaluator.automation_criteria, 'get_automation_criteria', return_value=mock_criteria):
            with patch.object(Path, 'exists', return_value=True):
                evaluations = self.evaluator.evaluate_components(components)
        
        assert len(evaluations) == 2
        assert all(isinstance(e, ComponentEvaluation) for e in evaluations)
    
    def test_calculate_system_completion(self):
        """Test system completion calculation"""
        evaluations = [
            ComponentEvaluation(
                component=Component(
                    name="Component 1",
                    category=ComponentCategory.AUTOMATION,
                    path="./"
                ),
                criteria_type="automation",
                overall_score=0.8,
                completion_percentage=80.0,
                status=EvaluationStatus.PASSED,
                critical_criteria_passed=True
            ),
            ComponentEvaluation(
                component=Component(
                    name="Component 2",
                    category=ComponentCategory.INFRASTRUCTURE,
                    path="./"
                ),
                criteria_type="infrastructure",
                overall_score=0.6,
                completion_percentage=60.0,
                status=EvaluationStatus.WARNING,
                critical_criteria_passed=True
            )
        ]
        
        system_metrics = self.evaluator.calculate_system_completion(evaluations)
        
        assert system_metrics["overall_completion"] == 70.0  # (80 + 60) / 2
        assert system_metrics["total_components"] == 2
        assert system_metrics["evaluated_components"] == 2
        assert system_metrics["passed_components"] == 1
        assert system_metrics["failed_components"] == 0
        assert "automation" in system_metrics["category_completion"]
        assert "infrastructure" in system_metrics["category_completion"]


    def test_detect_component_issues(self):
        """Test component issue detection and categorization"""
        # Create evaluation with various types of issues
        component = Component(
            name="Test Component",
            category=ComponentCategory.AUTOMATION,
            path="./"
        )
        
        criterion_evaluations = [
            CriterionEvaluation(
                criterion_id="missing_file",
                criterion_name="Configuration File",
                status=EvaluationStatus.FAILED,
                score=0.0,
                weight=1.0,
                required=True,
                message="File not found",
                details={
                    "evaluation_method": "file_exists",
                    "parameters": {"file_path": "config.json"}
                }
            ),
            CriterionEvaluation(
                criterion_id="quality_issue",
                criterion_name="Code Quality Check",
                status=EvaluationStatus.WARNING,
                score=0.6,
                weight=1.0,
                required=False,
                message="Quality standards not met",
                details={"parameters": {}}
            )
        ]
        
        evaluation = ComponentEvaluation(
            component=component,
            criteria_type="automation",
            overall_score=0.3,
            completion_percentage=30.0,
            status=EvaluationStatus.FAILED,
            criterion_evaluations=criterion_evaluations
        )
        
        issues = self.evaluator.detect_component_issues(evaluation)
        
        assert "missing_files" in issues
        assert "quality_issues" in issues
        assert "Missing file: config.json" in issues["missing_files"]
        assert "Quality standards not met" in issues["quality_issues"]
    
    def test_calculate_completion_trend(self):
        """Test completion trend calculation"""
        evaluations = [
            ComponentEvaluation(
                component=Component(
                    name="Component 1",
                    category=ComponentCategory.AUTOMATION,
                    path="./"
                ),
                criteria_type="automation",
                overall_score=0.9,
                completion_percentage=90.0,
                status=EvaluationStatus.PASSED
            ),
            ComponentEvaluation(
                component=Component(
                    name="Component 2",
                    category=ComponentCategory.INFRASTRUCTURE,
                    path="./"
                ),
                criteria_type="infrastructure",
                overall_score=0.3,
                completion_percentage=30.0,
                status=EvaluationStatus.FAILED
            )
        ]
        
        trend_data = self.evaluator.calculate_completion_trend(evaluations)
        
        assert trend_data["trend"] == "good"  # 60% average
        assert trend_data["overall_average"] == 60.0
        assert "automation" in trend_data["category_averages"]
        assert "infrastructure" in trend_data["category_averages"]
        assert trend_data["total_components"] == 2
    
    def test_generate_specific_recommendation(self):
        """Test specific recommendation generation"""
        criterion_eval = CriterionEvaluation(
            criterion_id="test_file",
            criterion_name="Test File Check",
            status=EvaluationStatus.FAILED,
            score=0.0,
            weight=1.0,
            required=True,
            message="File missing",
            details={
                "parameters": {"file_path": "test.txt"}
            }
        )
        
        recommendation = self.evaluator._generate_specific_recommendation(criterion_eval, "CRITICAL")
        
        assert "CRITICAL" in recommendation
        assert "test.txt" in recommendation
        assert "Test File Check" in recommendation
    
    def test_improved_scoring_with_penalties(self):
        """Test improved scoring algorithm with penalties for critical failures"""
        # Test with critical failure
        criterion_evaluations_with_critical_failure = [
            CriterionEvaluation(
                criterion_id="critical_test",
                criterion_name="Critical Test",
                status=EvaluationStatus.FAILED,
                score=0.0,
                weight=1.0,
                required=True,  # Critical
                message="Critical failure"
            ),
            CriterionEvaluation(
                criterion_id="normal_test",
                criterion_name="Normal Test",
                status=EvaluationStatus.PASSED,
                score=1.0,
                weight=1.0,
                required=False,
                message="Normal passed"
            )
        ]
        
        score_with_penalty = self.evaluator._calculate_overall_score(criterion_evaluations_with_critical_failure)
        
        # Should be less than 0.5 due to critical failure penalty
        assert score_with_penalty < 0.5
        
        # Test with high performers bonus
        criterion_evaluations_high_performance = [
            CriterionEvaluation(
                criterion_id="high1",
                criterion_name="High 1",
                status=EvaluationStatus.PASSED,
                score=0.95,
                weight=1.0,
                required=False,
                message="High performance"
            ),
            CriterionEvaluation(
                criterion_id="high2",
                criterion_name="High 2",
                status=EvaluationStatus.PASSED,
                score=0.92,
                weight=1.0,
                required=False,
                message="High performance"
            )
        ]
        
        score_with_bonus = self.evaluator._calculate_overall_score(criterion_evaluations_high_performance)
        
        # Should be close to or above the base average due to bonus
        base_average = (0.95 + 0.92) / 2
        assert score_with_bonus >= base_average


def mock_open_json(json_content):
    """Mock open function for JSON content"""
    import json
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(json_content))


if __name__ == "__main__":
    pytest.main([__file__])