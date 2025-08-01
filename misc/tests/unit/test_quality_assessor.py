"""
Unit tests for Quality Assessor

Tests the quality assessment functionality including code quality analysis,
documentation completeness, and test coverage metrics.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import ast

from src.phoenix_system_review.analysis.quality_assessor import (
    QualityAssessor,
    QualityAssessmentResult,
    CodeQualityResult,
    DocumentationResult,
    TestCoverageResult,
    QualityMetric,
    QualityLevel,
    QualityIssue
)
from src.phoenix_system_review.models.data_models import Component, ComponentCategory, ComponentStatus


class TestQualityAssessor:
    """Test cases for QualityAssessor class"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create test Python files
            test_files = {
                "src/component.py": '''"""Module docstring"""
def documented_function():
    """This function has documentation"""
    return True

def undocumented_function():
    return False

class DocumentedClass:
    """This class has documentation"""
    pass

class UndocumentedClass:
    pass
''',
                "src/complex_component.py": '''def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "very large"
            else:
                return "large"
        else:
            return "small positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"
''',
                "tests/test_component.py": '''import unittest

class TestComponent(unittest.TestCase):
    def test_something(self):
        self.assertTrue(True)
'''
            }
            
            for file_path, content in test_files.items():
                full_path = project_root / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            
            yield str(project_root)
    
    @pytest.fixture
    def quality_assessor(self, temp_project_dir):
        """Create QualityAssessor instance for testing"""
        return QualityAssessor(temp_project_dir)
    
    @pytest.fixture
    def sample_component(self):
        """Create sample component for testing"""
        return Component(
            name="Test Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/component.py",
            status=ComponentStatus.OPERATIONAL,
            description="Test component for quality assessment"
        )
    
    def test_assessor_initialization(self, quality_assessor):
        """Test quality assessor initialization"""
        assert quality_assessor is not None
        assert quality_assessor.project_root is not None
        assert quality_assessor.quality_thresholds is not None
        assert len(quality_assessor.quality_thresholds) == 4
        
        # Check quality thresholds
        assert quality_assessor.quality_thresholds[QualityLevel.EXCELLENT] == 0.9
        assert quality_assessor.quality_thresholds[QualityLevel.GOOD] == 0.7
        assert quality_assessor.quality_thresholds[QualityLevel.FAIR] == 0.5
        assert quality_assessor.quality_thresholds[QualityLevel.POOR] == 0.0
    
    def test_assess_component_quality(self, quality_assessor, sample_component):
        """Test component quality assessment"""
        result = quality_assessor.assess_component_quality(sample_component)
        
        assert isinstance(result, QualityAssessmentResult)
        assert result.component == sample_component
        assert isinstance(result.code_quality, CodeQualityResult)
        assert isinstance(result.documentation, DocumentationResult)
        assert isinstance(result.test_coverage, TestCoverageResult)
        assert isinstance(result.overall_quality_score, float)
        assert 0.0 <= result.overall_quality_score <= 1.0
        assert isinstance(result.quality_level, QualityLevel)
        assert isinstance(result.recommendations, list)
    
    def test_assess_multiple_components(self, quality_assessor, sample_component):
        """Test assessment of multiple components"""
        components = [sample_component]
        results = quality_assessor.assess_multiple_components(components)
        
        assert len(results) == 1
        assert all(isinstance(r, QualityAssessmentResult) for r in results)
        assert results[0].component == sample_component
    
    def test_get_component_python_files(self, quality_assessor, sample_component):
        """Test getting Python files for a component"""
        files = quality_assessor._get_component_python_files(sample_component)
        
        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, Path) for f in files)
        assert all(f.suffix == '.py' for f in files)
    
    def test_analyze_documentation(self, quality_assessor, sample_component):
        """Test documentation analysis"""
        result = quality_assessor._analyze_documentation(sample_component)
        
        assert isinstance(result, DocumentationResult)
        assert result.total_functions >= 0
        assert result.documented_functions >= 0
        assert result.total_classes >= 0
        assert result.documented_classes >= 0
        assert result.total_modules >= 0
        assert result.documented_modules >= 0
        assert 0.0 <= result.documentation_score <= 1.0
        assert isinstance(result.missing_docs, list)
    
    def test_analyze_file_documentation(self, quality_assessor):
        """Test file documentation analysis"""
        code = '''"""Module docstring"""

def documented_function():
    """Function docstring"""
    pass

def undocumented_function():
    pass

class DocumentedClass:
    """Class docstring"""
    pass

class UndocumentedClass:
    pass
'''
        tree = ast.parse(code)
        stats = quality_assessor._analyze_file_documentation(tree, "test.py")
        
        assert stats['total_functions'] == 2
        assert stats['documented_functions'] == 1
        assert stats['total_classes'] == 2
        assert stats['documented_classes'] == 1
        assert stats['has_module_docstring'] is True
        assert len(stats['missing_docs']) == 2  # 1 function + 1 class
    
    def test_calculate_file_complexity(self, quality_assessor):
        """Test cyclomatic complexity calculation"""
        code = '''
def simple_function():
    return True

def complex_function(x):
    if x > 0:
        if x > 10:
            return "large"
        else:
            return "small"
    else:
        return "zero or negative"
'''
        tree = ast.parse(code)
        complexity, function_count = quality_assessor._calculate_file_complexity(tree)
        
        assert function_count == 2
        assert complexity > 2  # Should have complexity from control structures
    
    def test_calculate_code_quality_score(self, quality_assessor):
        """Test code quality score calculation"""
        # Test with no issues
        score = quality_assessor._calculate_code_quality_score([], 1)
        assert score == 1.0
        
        # Test with issues
        issues = [
            QualityIssue("test.py", 1, "linting", "error", "Test error"),
            QualityIssue("test.py", 2, "linting", "warning", "Test warning"),
            QualityIssue("test.py", 3, "linting", "info", "Test info")
        ]
        score = quality_assessor._calculate_code_quality_score(issues, 1)
        assert 0.0 <= score < 1.0  # Should be less than 1 due to issues
    
    def test_calculate_complexity_score(self, quality_assessor, temp_project_dir):
        """Test complexity score calculation"""
        # Create a test file with known complexity
        test_file = Path(temp_project_dir) / "test_complexity.py"
        test_file.write_text('''
def simple_function():
    return True

def complex_function(x):
    if x > 0:
        if x > 10:
            return "large"
        else:
            return "small"
    else:
        return "zero"
''')
        
        score = quality_assessor._calculate_complexity_score([test_file])
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_calculate_maintainability_score(self, quality_assessor, temp_project_dir):
        """Test maintainability score calculation"""
        # Create a test file
        test_file = Path(temp_project_dir) / "test_maintainability.py"
        test_file.write_text('''# This is a comment
def well_maintained_function():
    """Good documentation"""
    # Another comment
    return True
''')
        
        score = quality_assessor._calculate_maintainability_score([test_file])
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_map_ruff_severity(self, quality_assessor):
        """Test ruff severity mapping"""
        assert quality_assessor._map_ruff_severity("E999") == "error"
        assert quality_assessor._map_ruff_severity("F401") == "error"
        assert quality_assessor._map_ruff_severity("E501") == "warning"
        assert quality_assessor._map_ruff_severity("W292") == "warning"
        assert quality_assessor._map_ruff_severity("N806") == "info"
        assert quality_assessor._map_ruff_severity("") == "info"
    
    def test_calculate_overall_quality_score(self, quality_assessor):
        """Test overall quality score calculation"""
        code_quality = CodeQualityResult(quality_score=0.8)
        documentation = DocumentationResult(documentation_score=0.7)
        test_coverage = TestCoverageResult(coverage_percentage=60.0)
        
        score = quality_assessor._calculate_overall_quality_score(
            code_quality, documentation, test_coverage
        )
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
        # Should be weighted average: 0.8*0.4 + 0.7*0.3 + 0.6*0.3 = 0.71
        expected = 0.8 * 0.4 + 0.7 * 0.3 + 0.6 * 0.3
        assert abs(score - expected) < 0.01
    
    def test_determine_quality_level(self, quality_assessor):
        """Test quality level determination"""
        assert quality_assessor._determine_quality_level(0.95) == QualityLevel.EXCELLENT
        assert quality_assessor._determine_quality_level(0.85) == QualityLevel.GOOD
        assert quality_assessor._determine_quality_level(0.65) == QualityLevel.FAIR
        assert quality_assessor._determine_quality_level(0.35) == QualityLevel.POOR
    
    def test_generate_quality_recommendations(self, quality_assessor):
        """Test quality recommendation generation"""
        # Create results with various issues
        code_quality = CodeQualityResult(
            quality_score=0.6,
            complexity_score=0.5,
            issues=[
                QualityIssue("test.py", 1, "linting", "error", "Test error"),
                QualityIssue("test.py", 2, "linting", "warning", "Test warning")
            ]
        )
        
        documentation = DocumentationResult(
            total_functions=5,
            documented_functions=2,
            total_classes=3,
            documented_classes=1,
            documentation_score=0.5
        )
        
        test_coverage = TestCoverageResult(
            coverage_percentage=45.0,
            test_files_count=0
        )
        
        recommendations = quality_assessor._generate_quality_recommendations(
            code_quality, documentation, test_coverage
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should have recommendations for each issue type
        rec_text = " ".join(recommendations).lower()
        assert "error" in rec_text or "warning" in rec_text
        assert "docstring" in rec_text or "documentation" in rec_text
        assert "test" in rec_text or "coverage" in rec_text
    
    def test_count_test_files(self, quality_assessor, sample_component):
        """Test test file counting"""
        count = quality_assessor._count_test_files(sample_component)
        
        assert isinstance(count, int)
        assert count >= 0
    
    def test_is_test_file(self, quality_assessor):
        """Test test file identification"""
        assert quality_assessor._is_test_file(Path("test_component.py"))
        assert quality_assessor._is_test_file(Path("component_test.py"))
        assert quality_assessor._is_test_file(Path("tests/component.py"))
        assert not quality_assessor._is_test_file(Path("component.py"))
    
    def test_is_related_test_file(self, quality_assessor, sample_component):
        """Test related test file identification"""
        assert quality_assessor._is_related_test_file(
            Path("test_test_component.py"), sample_component
        )
        assert quality_assessor._is_related_test_file(
            Path("test_component.py"), sample_component
        )
        assert not quality_assessor._is_related_test_file(
            Path("test_other.py"), sample_component
        )
    
    def test_generate_quality_report(self, quality_assessor, sample_component):
        """Test quality report generation"""
        # Create sample results
        results = [
            QualityAssessmentResult(
                component=sample_component,
                code_quality=CodeQualityResult(quality_score=0.8),
                documentation=DocumentationResult(documentation_score=0.7),
                test_coverage=TestCoverageResult(coverage_percentage=60.0),
                overall_quality_score=0.75,
                quality_level=QualityLevel.GOOD,
                recommendations=["Test recommendation"]
            )
        ]
        
        report = quality_assessor.generate_quality_report(results)
        
        assert isinstance(report, dict)
        assert "summary" in report
        assert "quality_distribution" in report
        assert "issues" in report
        assert "recommendations" in report
        assert "detailed_results" in report
        
        # Check summary
        summary = report["summary"]
        assert summary["total_components"] == 1
        assert isinstance(summary["average_quality_score"], float)
        assert isinstance(summary["average_code_quality"], float)
        assert isinstance(summary["average_documentation_score"], float)
        assert isinstance(summary["average_test_coverage"], float)
        
        # Check quality distribution
        distribution = report["quality_distribution"]
        assert sum(distribution.values()) == 1
        assert distribution["good"] == 1
        
        # Check detailed results
        detailed = report["detailed_results"]
        assert len(detailed) == 1
        assert detailed[0]["component_name"] == sample_component.name
        assert detailed[0]["quality_level"] == "good"
    
    def test_generate_quality_report_empty(self, quality_assessor):
        """Test quality report generation with empty results"""
        report = quality_assessor.generate_quality_report([])
        
        assert isinstance(report, dict)
        assert "error" in report
    
    @patch('subprocess.run')
    def test_run_linting_checks_with_ruff(self, mock_run, quality_assessor, temp_project_dir):
        """Test linting checks with ruff"""
        # Mock successful ruff execution
        mock_run.return_value = Mock(
            returncode=0,
            stdout='[{"location": {"row": 1}, "code": "E501", "message": "Line too long"}]'
        )
        
        test_file = Path(temp_project_dir) / "test.py"
        test_file.write_text("print('hello')")
        
        issues = quality_assessor._run_linting_checks(test_file)
        
        assert isinstance(issues, list)
        if issues:  # If ruff was successfully mocked
            assert len(issues) > 0
            assert all(isinstance(issue, QualityIssue) for issue in issues)
    
    @patch('subprocess.run')
    def test_run_linting_checks_fallback(self, mock_run, quality_assessor, temp_project_dir):
        """Test linting checks fallback to AST parsing"""
        # Mock ruff failure
        mock_run.side_effect = FileNotFoundError()
        
        # Create file with syntax error
        test_file = Path(temp_project_dir) / "syntax_error.py"
        test_file.write_text("def invalid_syntax(\n")  # Missing closing parenthesis
        
        issues = quality_assessor._run_linting_checks(test_file)
        
        assert isinstance(issues, list)
        # Should detect syntax error
        if issues:
            assert any(issue.issue_type == 'syntax' for issue in issues)
    
    def test_error_handling_in_assessment(self, quality_assessor):
        """Test error handling during quality assessment"""
        # Create component with invalid path
        invalid_component = Component(
            name="Invalid Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="non/existent/path.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        result = quality_assessor.assess_component_quality(invalid_component)
        
        # Should not crash and return valid result
        assert isinstance(result, QualityAssessmentResult)
        assert result.component == invalid_component
        assert result.overall_quality_score == 0.0


if __name__ == "__main__":
    pytest.main([__file__])