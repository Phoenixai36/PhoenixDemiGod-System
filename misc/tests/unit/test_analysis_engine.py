"""
Unit tests for Analysis Engine components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer
from phoenix_system_review.analysis.quality_assessor import QualityAssessor
from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, EvaluationResult,
    Issue, Priority, EvaluationCriterion, CriterionType, DependencyGraph
)


class TestComponentEvaluator:
    """Test cases for ComponentEvaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create ComponentEvaluator instance"""
        return ComponentEvaluator()
    
    @pytest.fixture
    def sample_component(self):
        """Create a sample component for testing"""
        return Component(
            name="phoenix-core",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/core",
            dependencies=["database", "storage"],
            configuration={"port": 8080, "debug": False},
            status=ComponentStatus.OPERATIONAL
        )
    
    @pytest.fixture
    def sample_criteria(self):
        """Create sample evaluation criteria"""
        return {
            "api_endpoints": EvaluationCriterion(
                id="api_endpoints",
                name="API Endpoints",
                description="Component has properly defined API endpoints",
                criterion_type=CriterionType.FUNCTIONALITY,
                weight=1.0,
                is_critical=True
            ),
            "health_checks": EvaluationCriterion(
                id="health_checks",
                name="Health Checks",
                description="Component has health check endpoints",
                criterion_type=CriterionType.FUNCTIONALITY,
                weight=0.8,
                is_critical=False
            ),
            "documentation": EvaluationCriterion(
                id="documentation",
                name="Documentation",
                description="Component has complete documentation",
                criterion_type=CriterionType.QUALITY,
                weight=0.6,
                is_critical=False
            )
        }
    
    def test_evaluate_component_all_criteria_met(self, evaluator, sample_component, sample_criteria):
        """Test component evaluation when all criteria are met"""
        # Mock the evaluation methods to return positive results
        with patch.object(evaluator, '_check_criterion', return_value=True):
            result = evaluator.evaluate_component(sample_component, sample_criteria)
            
            assert isinstance(result, EvaluationResult)
            assert result.component == sample_component
            assert len(result.criteria_met) == 3
            assert len(result.criteria_missing) == 0
            assert result.completion_percentage == 100.0
            assert result.is_complete is True
    
    def test_evaluate_component_partial_criteria_met(self, evaluator, sample_component, sample_criteria):
        """Test component evaluation when some criteria are met"""
        # Mock the evaluation methods to return mixed results
        def mock_check_criterion(component, criterion):
            return criterion.id in ["api_endpoints", "health_checks"]
        
        with patch.object(evaluator, '_check_criterion', side_effect=mock_check_criterion):
            result = evaluator.evaluate_component(sample_component, sample_criteria)
            
            assert isinstance(result, EvaluationResult)
            assert len(result.criteria_met) == 2
            assert len(result.criteria_missing) == 1
            assert "documentation" in result.criteria_missing
            assert result.completion_percentage < 100.0
            assert result.is_complete is False
    
    def test_evaluate_component_no_criteria_met(self, evaluator, sample_component, sample_criteria):
        """Test component evaluation when no criteria are met"""
        with patch.object(evaluator, '_check_criterion', return_value=False):
            result = evaluator.evaluate_component(sample_component, sample_criteria)
            
            assert isinstance(result, EvaluationResult)
            assert len(result.criteria_met) == 0
            assert len(result.criteria_missing) == 3
            assert result.completion_percentage == 0.0
            assert result.is_complete is False
    
    def test_evaluate_component_with_critical_issues(self, evaluator, sample_component, sample_criteria):
        """Test component evaluation with critical issues"""
        def mock_check_criterion(component, criterion):
            if criterion.is_critical:
                return False
            return True
        
        with patch.object(evaluator, '_check_criterion', side_effect=mock_check_criterion):
            result = evaluator.evaluate_component(sample_component, sample_criteria)
            
            assert result.has_critical_issues is True
            assert any(issue.severity == Priority.CRITICAL for issue in result.issues)
    
    def test_get_evaluation_criteria_infrastructure(self, evaluator):
        """Test getting evaluation criteria for infrastructure components"""
        criteria = evaluator.get_evaluation_criteria("infrastructure")
        
        assert isinstance(criteria, dict)
        assert len(criteria) > 0
        assert all(isinstance(criterion, EvaluationCriterion) for criterion in criteria.values())
    
    def test_get_evaluation_criteria_monetization(self, evaluator):
        """Test getting evaluation criteria for monetization components"""
        criteria = evaluator.get_evaluation_criteria("monetization")
        
        assert isinstance(criteria, dict)
        assert len(criteria) > 0
        assert all(isinstance(criterion, EvaluationCriterion) for criterion in criteria.values())
    
    def test_get_evaluation_criteria_unknown_type(self, evaluator):
        """Test getting evaluation criteria for unknown component type"""
        criteria = evaluator.get_evaluation_criteria("unknown")
        
        assert isinstance(criteria, dict)
        assert len(criteria) == 0  # Should return empty dict for unknown types


class TestDependencyAnalyzer:
    """Test cases for DependencyAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create DependencyAnalyzer instance"""
        return DependencyAnalyzer()
    
    @pytest.fixture
    def sample_components(self):
        """Create sample components with dependencies"""
        return [
            Component(
                name="database",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/database",
                dependencies=[]
            ),
            Component(
                name="storage",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/storage",
                dependencies=["database"]
            ),
            Component(
                name="api",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/api",
                dependencies=["database", "storage"]
            ),
            Component(
                name="frontend",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/frontend",
                dependencies=["api"]
            )
        ]
    
    def test_map_dependencies(self, analyzer, sample_components):
        """Test mapping component dependencies"""
        dependency_graph = analyzer.map_dependencies(sample_components)
        
        assert isinstance(dependency_graph, DependencyGraph)
        assert len(dependency_graph.nodes) == 4
        assert len(dependency_graph.edges) == 4  # storage->database, api->database, api->storage, frontend->api
        
        # Check specific edges
        assert ("storage", "database") in dependency_graph.edges
        assert ("api", "database") in dependency_graph.edges
        assert ("api", "storage") in dependency_graph.edges
        assert ("frontend", "api") in dependency_graph.edges
    
    def test_detect_circular_dependencies(self, analyzer):
        """Test detection of circular dependencies"""
        circular_components = [
            Component(
                name="component_a",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/a",
                dependencies=["component_b"]
            ),
            Component(
                name="component_b",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/b",
                dependencies=["component_c"]
            ),
            Component(
                name="component_c",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/c",
                dependencies=["component_a"]  # Creates circular dependency
            )
        ]
        
        dependency_graph = analyzer.map_dependencies(circular_components)
        
        assert len(dependency_graph.circular_dependencies) > 0
        circular_cycle = dependency_graph.circular_dependencies[0]
        assert "component_a" in circular_cycle
        assert "component_b" in circular_cycle
        assert "component_c" in circular_cycle
    
    def test_analyze_component_dependencies(self, analyzer, sample_components):
        """Test analyzing dependencies for a specific component"""
        dependency_graph = analyzer.map_dependencies(sample_components)
        api_component = next(c for c in sample_components if c.name == "api")
        
        analysis = analyzer.analyze_dependencies(api_component, dependency_graph)
        
        assert isinstance(analysis, dict)
        assert "direct_dependencies" in analysis
        assert "transitive_dependencies" in analysis
        assert "dependents" in analysis
        
        assert len(analysis["direct_dependencies"]) == 2  # database, storage
        assert "database" in analysis["direct_dependencies"]
        assert "storage" in analysis["direct_dependencies"]
    
    def test_validate_dependencies(self, analyzer, sample_components):
        """Test validating component dependencies"""
        # Add a component with invalid dependency
        invalid_component = Component(
            name="invalid",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/invalid",
            dependencies=["nonexistent"]
        )
        components_with_invalid = sample_components + [invalid_component]
        
        issues = analyzer.validate_dependencies(components_with_invalid)
        
        assert len(issues) > 0
        assert any("nonexistent" in issue for issue in issues)
    
    def test_get_dependency_order(self, analyzer, sample_components):
        """Test getting topological order of dependencies"""
        dependency_graph = analyzer.map_dependencies(sample_components)
        order = analyzer.get_dependency_order(dependency_graph)
        
        assert isinstance(order, list)
        assert len(order) == 4
        
        # Database should come first (no dependencies)
        assert order.index("database") < order.index("storage")
        assert order.index("storage") < order.index("api")
        assert order.index("api") < order.index("frontend")


class TestQualityAssessor:
    """Test cases for QualityAssessor"""
    
    @pytest.fixture
    def assessor(self):
        """Create QualityAssessor instance"""
        return QualityAssessor()
    
    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
"""
Sample Python module for testing
"""

def hello_world():
    """Return a greeting message"""
    return "Hello, World!"

class SampleClass:
    """A sample class for testing"""
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        """Return a personalized greeting"""
        return f"Hello, {self.name}!"

if __name__ == "__main__":
    print(hello_world())
''')
            return f.name
    
    def test_analyze_code_quality(self, assessor, sample_python_file):
        """Test analyzing code quality metrics"""
        try:
            metrics = assessor.analyze_code_quality(sample_python_file)
            
            assert isinstance(metrics, dict)
            assert "complexity" in metrics
            assert "maintainability" in metrics
            assert "documentation_ratio" in metrics
            
            # Check that metrics are reasonable values
            assert 0 <= metrics["complexity"] <= 100
            assert 0 <= metrics["maintainability"] <= 100
            assert 0 <= metrics["documentation_ratio"] <= 1.0
        finally:
            import os
            os.unlink(sample_python_file)
    
    def test_analyze_code_quality_nonexistent_file(self, assessor):
        """Test analyzing code quality for nonexistent file"""
        metrics = assessor.analyze_code_quality("/nonexistent/file.py")
        
        assert metrics is None or all(v == 0 for v in metrics.values())
    
    def test_check_documentation_completeness(self, assessor):
        """Test checking documentation completeness"""
        component = Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test",
            description="A test component"
        )
        
        with patch.object(assessor, '_count_documented_functions', return_value=(8, 10)):
            completeness = assessor.check_documentation_completeness(component)
            
            assert isinstance(completeness, float)
            assert 0.0 <= completeness <= 1.0
            assert completeness == 0.8  # 8 out of 10 functions documented
    
    def test_assess_test_coverage(self, assessor):
        """Test assessing test coverage"""
        component = Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test"
        )
        
        with patch.object(assessor, '_calculate_test_coverage', return_value=85.5):
            coverage = assessor.assess_test_coverage(component)
            
            assert isinstance(coverage, float)
            assert coverage == 85.5
    
    def test_validate_configuration_files(self, assessor):
        """Test validating configuration files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('''
app:
  name: test-app
  port: 8080
  debug: true
database:
  host: localhost
  port: 5432
''')
            yaml_file = f.name
        
        try:
            issues = assessor.validate_configuration_files([yaml_file])
            
            assert isinstance(issues, list)
            # Should have no issues for valid YAML
            assert len(issues) == 0
        finally:
            import os
            os.unlink(yaml_file)
    
    def test_validate_invalid_configuration_files(self, assessor):
        """Test validating invalid configuration files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            invalid_file = f.name
        
        try:
            issues = assessor.validate_configuration_files([invalid_file])
            
            assert isinstance(issues, list)
            assert len(issues) > 0
            assert any("syntax" in issue.lower() or "invalid" in issue.lower() for issue in issues)
        finally:
            import os
            os.unlink(invalid_file)
    
    def test_calculate_overall_quality_score(self, assessor):
        """Test calculating overall quality score"""
        component = Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test"
        )
        
        with patch.object(assessor, 'analyze_code_quality', return_value={
            "complexity": 75.0,
            "maintainability": 80.0,
            "documentation_ratio": 0.9
        }):
            with patch.object(assessor, 'check_documentation_completeness', return_value=0.85):
                with patch.object(assessor, 'assess_test_coverage', return_value=90.0):
                    score = assessor.calculate_overall_quality_score(component)
                    
                    assert isinstance(score, float)
                    assert 0.0 <= score <= 100.0


if __name__ == '__main__':
    pytest.main([__file__])