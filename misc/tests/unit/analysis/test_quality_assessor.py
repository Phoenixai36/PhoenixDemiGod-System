"""
Unit tests for Quality Assessor module.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import ast

from src.phoenix_system_review.analysis.quality_assessor import (
    QualityAssessor,
    QualityAssessmentResult,
    QualityLevel,
    QualityMetric,
    QualityIssue,
    CodeQualityResult,
    DocumentationResult,
    TestCoverageResult
)
from src.phoenix_system_review.models.data_models import (
    Component,
    ComponentCategory,
    ComponentStatus
)


class TestQualityAssessor:
    """Test quality assessor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.project_root = "/test/project"
        self.assessor = QualityAssessor(self.project_root)
    
    def test_initialization(self):
        """Test assessor initialization"""
        assert self.assessor.project_root == Path(self.project_root)
        assert len(self.assessor.quality_thresholds) == 4
        assert self.assessor.quality_thresholds[QualityLevel.EXCELLENT] == 0.9
        assert self.assessor.quality_thresholds[QualityLevel.GOOD] == 0.7
    
    def test_assess_component_quality_basic(self):
        """Test basic component quality assessment"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/test_component.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        # Mock file operations
        with patch.object(self.assessor, '_get_component_python_files', return_value=[]):
            result = self.assessor.assess_component_quality(component)
        
        assert isinstance(result, QualityAssessmentResult)
        assert result.component == component
        assert isinstance(result.code_quality, CodeQualityResult)
        assert isinstance(result.documentation, DocumentationResult)
        assert isinstance(result.test_coverage, TestCoverageResult)
        assert result.quality_level in QualityLevel
    
    def test_analyze_code_quality_no_files(self):
        """Test code quality analysis with no Python files"""
        component = Component(
            name="Empty Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="empty/",
            status=ComponentStatus.OPERATIONAL
        )
        
        with patch.object(self.assessor, '_get_component_python_files', return_value=[]):
            result = self.assessor._analyze_code_quality(component)
        
        assert result.total_files == 0
        assert result.analyzed_files == 0
        assert len(result.issues) == 0
        assert result.quality_score == 0.0
    
    def test_analyze_code_quality_with_files(self):
        """Test code quality analysis with Python files"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/test_component.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        mock_files = [Path("/test/project/src/test_component.py")]
        
        with patch.object(self.assessor, '_get_component_python_files', return_value=mock_files):
            with patch.object(self.assessor, '_run_linting_checks', return_value=[]):
                with patch.object(self.assessor, '_calculate_complexity_score', return_value=0.8):
                    with patch.object(self.assessor, '_calculate_maintainability_score', return_value=0.7):
                        result = self.assessor._analyze_code_quality(component)
        
        assert result.total_files == 1
        assert result.analyzed_files == 1
        assert result.complexity_score == 0.8
        assert result.maintainability_score == 0.7
    
    def test_analyze_documentation_no_files(self):
        """Test documentation analysis with no files"""
        component = Component(
            name="Empty Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="empty/",
            status=ComponentStatus.OPERATIONAL
        )
        
        with patch.object(self.assessor, '_get_component_python_files', return_value=[]):
            result = self.assessor._analyze_documentation(component)
        
        assert result.total_functions == 0
        assert result.total_classes == 0
        assert result.total_modules == 0
        assert result.documentation_score == 0.0
    
    def test_analyze_documentation_with_files(self):
        """Test documentation analysis with Python files"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/test_component.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        # Mock Python file with docstrings
        python_code = '''
"""Module docstring"""

class TestClass:
    """Class docstring"""
    
    def documented_method(self):
        """Method docstring"""
        pass
    
    def undocumented_method(self):
        pass

def documented_function():
    """Function docstring"""
    pass

def undocumented_function():
    pass
'''
        
        mock_files = [Path("/test/project/src/test_component.py")]
        
        with patch.object(self.assessor, '_get_component_python_files', return_value=mock_files):
            with patch('builtins.open', mock_open(read_data=python_code)):
                result = self.assessor._analyze_documentation(component)
        
        assert result.total_functions == 2
        assert result.documented_functions == 1
        assert result.total_classes == 1
        assert result.documented_classes == 1
        assert result.total_modules == 1
        assert result.documented_modules == 1
        assert result.documentation_score > 0.5  # Should be decent score
    
    def test_analyze_test_coverage_no_tests(self):
        """Test test coverage analysis with no test files"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/test_component.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        with patch.object(self.assessor, '_count_test_files', return_value=0):
            with patch.object(self.assessor, '_get_component_python_files', return_value=[Path("test.py")]):
                result = self.assessor._analyze_test_coverage(component)
        
        assert result.test_files_count == 0
        assert result.coverage_percentage == 0.0
    
    def test_analyze_test_coverage_with_tests(self):
        """Test test coverage analysis with test files"""
        component = Component(
            name="Test Component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/test_component.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        with patch.object(self.assessor, '_count_test_files', return_value=2):
            with patch.object(self.assessor, '_get_component_python_files', return_value=[Path("test.py")]):
                result = self.assessor._analyze_test_coverage(component)
        
        assert result.test_files_count == 2
        assert result.coverage_percentage == 50.0  # Basic estimate
    
    def test_run_linting_checks_valid_syntax(self):
        """Test linting checks on valid Python code"""
        file_path = Path("/test/project/valid.py")
        valid_code = "def hello():\n    return 'world'"
        
        with patch('builtins.open', mock_open(read_data=valid_code)):
            issues = self.assessor._run_linting_checks(file_path)
        
        assert len(issues) == 0
    
    def test_run_linting_checks_syntax_error(self):
        """Test linting checks on invalid Python code"""
        file_path = Path("/test/project/invalid.py")
        invalid_code = "def hello(\n    return 'world'"  # Missing closing parenthesis
        
        with patch('builtins.open', mock_open(read_data=invalid_code)):
            issues = self.assessor._run_linting_checks(file_path)
        
        assert len(issues) > 0
        assert issues[0].issue_type == 'syntax'
        assert issues[0].severity == 'error'
    
    def test_analyze_file_documentation_complete(self):
        """Test file documentation analysis with complete docstrings"""
        python_code = '''
"""Module docstring"""

class TestClass:
    """Class docstring"""
    
    def test_method(self):
        """Method docstring"""
        pass

def test_function():
    """Function docstring"""
    pass
'''
        
        tree = ast.parse(python_code)
        stats = self.assessor._analyze_file_documentation(tree, "test.py")
        
        assert stats['has_module_docstring'] is True
        assert stats['total_functions'] == 2  # Method + function
        assert stats['documented_functions'] == 2
        assert stats['total_classes'] == 1
        assert stats['documented_classes'] == 1
        assert len(stats['missing_docs']) == 0
    
    def test_analyze_file_documentation_incomplete(self):
        """Test file documentation analysis with missing docstrings"""
        python_code = '''
class TestClass:
    def test_method(self):
        pass

def test_function():
    pass
'''
        
        tree = ast.parse(python_code)
        stats = self.assessor._analyze_file_documentation(tree, "test.py")
        
        assert stats['has_module_docstring'] is False
        assert stats['total_functions'] == 1
        assert stats['documented_functions'] == 0
        assert stats['total_classes'] == 1
        assert stats['documented_classes'] == 0
        assert len(stats['missing_docs']) == 2  # Missing class and function docstrings
    
    def test_calculate_code_quality_score_no_issues(self):
        """Test code quality score calculation with no issues"""
        issues = []
        file_count = 3
        
        score = self.assessor._calculate_code_quality_score(issues, file_count)
        
        assert score == 1.0  # Perfect score with no issues
    
    def test_calculate_code_quality_score_with_issues(self):
        """Test code quality score calculation with issues"""
        issues = [
            QualityIssue("test.py", 1, "error", "error", "Test error"),
            QualityIssue("test.py", 2, "warning", "warning", "Test warning"),
            QualityIssue("test.py", 3, "info", "info", "Test info")
        ]
        file_count = 1
        
        score = self.assessor._calculate_code_quality_score(issues, file_count)
        
        assert 0.0 <= score < 1.0  # Should be less than perfect due to issues
    
    def test_calculate_complexity_score_simple_code(self):
        """Test complexity score calculation for simple code"""
        simple_code = '''
def simple_function():
    return "hello"

def another_simple_function():
    x = 1
    return x + 1
'''
        
        mock_files = [Path("/test/project/simple.py")]
        
        with patch('builtins.open', mock_open(read_data=simple_code)):
            score = self.assessor._calculate_complexity_score(mock_files)
        
        assert score > 0.8  # Simple code should have high complexity score
    
    def test_calculate_file_complexity_simple(self):
        """Test file complexity calculation for simple functions"""
        simple_code = '''
def simple_function():
    return "hello"

def function_with_if(x):
    if x > 0:
        return x
    return 0
'''
        
        tree = ast.parse(simple_code)
        complexity, function_count = self.assessor._calculate_file_complexity(tree)
        
        assert function_count == 2
        assert complexity == 3  # 1 + 1 (base) + 1 (if statement)
    
    def test_determine_quality_level(self):
        """Test quality level determination"""
        assert self.assessor._determine_quality_level(0.95) == QualityLevel.EXCELLENT
        assert self.assessor._determine_quality_level(0.8) == QualityLevel.GOOD
        assert self.assessor._determine_quality_level(0.6) == QualityLevel.FAIR
        assert self.assessor._determine_quality_level(0.3) == QualityLevel.POOR
    
    def test_generate_quality_recommendations_poor_quality(self):
        """Test quality recommendations generation for poor quality component"""
        code_quality = CodeQualityResult(
            quality_score=0.5,
            issues=[
                QualityIssue("test.py", 1, "error", "error", "Test error"),
                QualityIssue("test.py", 2, "warning", "warning", "Test warning")
            ]
        )
        
        documentation = DocumentationResult(
            total_functions=5,
            documented_functions=2,
            documentation_score=0.4
        )
        
        test_coverage = TestCoverageResult(
            coverage_percentage=30.0,
            test_files_count=1
        )
        
        recommendations = self.assessor._generate_quality_recommendations(
            code_quality, documentation, test_coverage
        )
        
        assert len(recommendations) > 0
        assert any("error" in rec.lower() for rec in recommendations)
        assert any("docstring" in rec.lower() for rec in recommendations)
        assert any("coverage" in rec.lower() for rec in recommendations)
    
    def test_assess_multiple_components(self):
        """Test assessing multiple components"""
        components = [
            Component(
                name="Component 1",
                category=ComponentCategory.INFRASTRUCTURE,
                path="src/comp1.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Component 2",
                category=ComponentCategory.AUTOMATION,
                path="src/comp2.py",
                status=ComponentStatus.OPERATIONAL
            )
        ]
        
        with patch.object(self.assessor, 'assess_component_quality') as mock_assess:
            mock_assess.return_value = QualityAssessmentResult(
                component=components[0],
                overall_quality_score=0.8,
                quality_level=QualityLevel.GOOD
            )
            
            results = self.assessor.assess_multiple_components(components)
        
        assert len(results) == 2
        assert mock_assess.call_count == 2
    
    def test_generate_quality_report(self):
        """Test quality report generation"""
        results = [
            QualityAssessmentResult(
                component=Component("Comp1", ComponentCategory.INFRASTRUCTURE, "src/"),
                overall_quality_score=0.8,
                quality_level=QualityLevel.GOOD,
                code_quality=CodeQualityResult(quality_score=0.8),
                documentation=DocumentationResult(documentation_score=0.7),
                test_coverage=TestCoverageResult(coverage_percentage=75.0)
            ),
            QualityAssessmentResult(
                component=Component("Comp2", ComponentCategory.AUTOMATION, "src/"),
                overall_quality_score=0.6,
                quality_level=QualityLevel.FAIR,
                code_quality=CodeQualityResult(quality_score=0.6),
                documentation=DocumentationResult(documentation_score=0.5),
                test_coverage=TestCoverageResult(coverage_percentage=50.0)
            )
        ]
        
        report = self.assessor.generate_quality_report(results)
        
        assert "summary" in report
        assert "quality_distribution" in report
        assert "issues" in report
        assert "detailed_results" in report
        
        assert report["summary"]["total_components"] == 2
        assert report["summary"]["average_quality_score"] == 0.7  # (0.8 + 0.6) / 2
        assert len(report["detailed_results"]) == 2
    
    def test_is_test_file(self):
        """Test test file identification"""
        assert self.assessor._is_test_file(Path("test_component.py")) is True
        assert self.assessor._is_test_file(Path("component_test.py")) is True
        assert self.assessor._is_test_file(Path("tests/component.py")) is True
        assert self.assessor._is_test_file(Path("src/component.py")) is False
    
    def test_is_related_test_file(self):
        """Test related test file identification"""
        component = Component(
            name="User Authentication",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/auth.py"
        )
        
        assert self.assessor._is_related_test_file(Path("test_user_authentication.py"), component) is True
        assert self.assessor._is_related_test_file(Path("test_auth.py"), component) is True
        assert self.assessor._is_related_test_file(Path("test_database.py"), component) is False


if __name__ == "__main__":
    pytest.main([__file__])