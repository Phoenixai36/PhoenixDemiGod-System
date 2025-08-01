"""
Quality Assessor for Phoenix Hydra System Review Tool
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import subprocess
import ast
import re
import json

from ..models.data_models import Component, ComponentCategory, ComponentStatus


class QualityMetric(Enum):
    """Types of quality metrics"""
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    TEST_COVERAGE = "test_coverage"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"


class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 70-89%
    FAIR = "fair"           # 50-69%
    POOR = "poor"           # 0-49%


@dataclass
class QualityIssue:
    """Represents a quality issue found during assessment"""
    file_path: str
    line_number: Optional[int]
    issue_type: str
    severity: str
    message: str
    rule_id: Optional[str] = None


@dataclass
class CodeQualityResult:
    """Results from code quality analysis"""
    total_files: int = 0
    analyzed_files: int = 0
    issues: List[QualityIssue] = field(default_factory=list)
    quality_score: float = 0.0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0


@dataclass
class DocumentationResult:
    """Results from documentation analysis"""
    total_functions: int = 0
    documented_functions: int = 0
    total_classes: int = 0
    documented_classes: int = 0
    total_modules: int = 0
    documented_modules: int = 0
    documentation_score: float = 0.0
    missing_docs: List[str] = field(default_factory=list)


@dataclass
class TestCoverageResult:
    """Results from test coverage analysis"""
    total_lines: int = 0
    covered_lines: int = 0
    coverage_percentage: float = 0.0
    uncovered_files: List[str] = field(default_factory=list)
    test_files_count: int = 0


@dataclass
class QualityAssessmentResult:
    """Complete quality assessment results"""
    component: Component
    code_quality: CodeQualityResult = field(default_factory=CodeQualityResult)
    documentation: DocumentationResult = field(default_factory=DocumentationResult)
    test_coverage: TestCoverageResult = field(default_factory=TestCoverageResult)
    overall_quality_score: float = 0.0
    quality_level: QualityLevel = QualityLevel.POOR
    recommendations: List[str] = field(default_factory=list)


class QualityAssessor:
    """Assesses code quality, documentation, and test coverage for Phoenix Hydra components."""
    
    def __init__(self, project_root: str = "."):
        """Initialize quality assessor"""
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Quality thresholds
        self.quality_thresholds = {
            QualityLevel.EXCELLENT: 0.9,
            QualityLevel.GOOD: 0.7,
            QualityLevel.FAIR: 0.5,
            QualityLevel.POOR: 0.0
        }
    
    def assess_component_quality(self, component: Component) -> QualityAssessmentResult:
        """Assess the quality of a single component."""
        try:
            # Analyze code quality
            code_quality = self._analyze_code_quality(component)
            
            # Analyze documentation
            documentation = self._analyze_documentation(component)
            
            # Analyze test coverage
            test_coverage = self._analyze_test_coverage(component)
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_quality_score(
                code_quality, documentation, test_coverage
            )
            
            # Determine quality level
            quality_level = self._determine_quality_level(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(
                code_quality, documentation, test_coverage
            )
            
            return QualityAssessmentResult(
                component=component,
                code_quality=code_quality,
                documentation=documentation,
                test_coverage=test_coverage,
                overall_quality_score=overall_score,
                quality_level=quality_level,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error assessing quality for {component.name}: {e}")
            return QualityAssessmentResult(
                component=component,
                recommendations=[f"Quality assessment failed: {e}"]
            )
    
    def assess_multiple_components(self, components: List[Component]) -> List[QualityAssessmentResult]:
        """Assess quality for multiple components"""
        results = []
        for component in components:
            result = self.assess_component_quality(component)
            results.append(result)
        return results
    
    def _analyze_code_quality(self, component: Component) -> CodeQualityResult:
        """Analyze code quality using linting and formatting checks"""
        result = CodeQualityResult()
        
        # Get Python files for the component
        python_files = self._get_component_python_files(component)
        result.total_files = len(python_files)
        
        if not python_files:
            return result
        
        # Run linting checks
        issues = []
        for file_path in python_files:
            file_issues = self._run_linting_checks(file_path)
            issues.extend(file_issues)
        
        result.issues = issues
        result.analyzed_files = len(python_files)
        
        # Calculate quality scores
        result.quality_score = self._calculate_code_quality_score(issues, len(python_files))
        result.complexity_score = self._calculate_complexity_score(python_files)
        result.maintainability_score = self._calculate_maintainability_score(python_files)
        
        return result
    
    def _analyze_documentation(self, component: Component) -> DocumentationResult:
        """Analyze documentation completeness"""
        result = DocumentationResult()
        
        # Get Python files for the component
        python_files = self._get_component_python_files(component)
        
        if not python_files:
            return result
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to analyze documentation
                tree = ast.parse(content)
                file_stats = self._analyze_file_documentation(tree, str(file_path))
                
                result.total_functions += file_stats['total_functions']
                result.documented_functions += file_stats['documented_functions']
                result.total_classes += file_stats['total_classes']
                result.documented_classes += file_stats['documented_classes']
                result.total_modules += 1
                
                if file_stats['has_module_docstring']:
                    result.documented_modules += 1
                else:
                    result.missing_docs.append(f"Module docstring missing: {file_path}")
                
                result.missing_docs.extend(file_stats['missing_docs'])
                
            except Exception as e:
                self.logger.warning(f"Could not analyze documentation for {file_path}: {e}")
        
        # Calculate documentation score
        total_items = result.total_functions + result.total_classes + result.total_modules
        documented_items = result.documented_functions + result.documented_classes + result.documented_modules
        
        if total_items > 0:
            result.documentation_score = documented_items / total_items
        
        return result
    
    def _analyze_test_coverage(self, component: Component) -> TestCoverageResult:
        """Analyze test coverage for the component"""
        result = TestCoverageResult()
        
        try:
            # Count test files
            result.test_files_count = self._count_test_files(component)
            
            # Get Python files for the component
            python_files = self._get_component_python_files(component)
            
            if not python_files:
                return result
            
            # Try to get actual coverage data using coverage.py
            coverage_data = self._get_coverage_data(component, python_files)
            
            if coverage_data:
                result.total_lines = coverage_data['total_lines']
                result.covered_lines = coverage_data['covered_lines']
                result.coverage_percentage = coverage_data['coverage_percentage']
                result.uncovered_files = coverage_data['uncovered_files']
            else:
                # Fallback to estimation based on test files and code analysis
                result = self._estimate_test_coverage(component, python_files, result.test_files_count)
            
        except Exception as e:
            self.logger.warning(f"Could not analyze test coverage for {component.name}: {e}")
        
        return result    

    def _get_component_python_files(self, component: Component) -> List[Path]:
        """Get Python files associated with a component"""
        files = []
        
        # Start with the component's main file if it's a Python file
        if component.path and component.path.endswith('.py'):
            main_file = self.project_root / component.path.lstrip('/')
            if main_file.exists():
                files.append(main_file)
        
        # Look for related Python files in the component's directory
        if component.path:
            component_dir = self.project_root / Path(component.path).parent
            if component_dir.exists() and component_dir.is_dir():
                # Find all Python files in the component directory
                for py_file in component_dir.rglob('*.py'):
                    if py_file not in files and not self._is_test_file(py_file):
                        files.append(py_file)
        
        return files
    
    def _run_linting_checks(self, file_path: Path) -> List[QualityIssue]:
        """Run linting checks on a Python file"""
        issues = []
        
        try:
            # Try basic AST parsing for syntax errors
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            issues.append(QualityIssue(
                file_path=str(file_path),
                line_number=e.lineno,
                issue_type='syntax',
                severity='error',
                message=f"Syntax error: {e.msg}",
                rule_id='E999'
            ))
        except Exception as e:
            self.logger.warning(f"Could not analyze {file_path}: {e}")
        
        return issues
    
    def _analyze_file_documentation(self, tree: ast.AST, file_path: str) -> Dict[str, Any]:
        """Analyze documentation in a Python file AST"""
        stats = {
            'total_functions': 0,
            'documented_functions': 0,
            'total_classes': 0,
            'documented_classes': 0,
            'has_module_docstring': False,
            'missing_docs': []
        }
        
        # Check for module docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            stats['has_module_docstring'] = True
        
        # Walk the AST to find functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats['total_functions'] += 1
                if ast.get_docstring(node):
                    stats['documented_functions'] += 1
                else:
                    stats['missing_docs'].append(f"Function '{node.name}' missing docstring in {file_path}")
            
            elif isinstance(node, ast.ClassDef):
                stats['total_classes'] += 1
                if ast.get_docstring(node):
                    stats['documented_classes'] += 1
                else:
                    stats['missing_docs'].append(f"Class '{node.name}' missing docstring in {file_path}")
        
        return stats
    
    def _map_ruff_severity(self, code: str) -> str:
        """Map ruff error codes to severity levels"""
        if not code:
            return 'info'
        
        # Error codes starting with E or F are usually errors
        if code.startswith(('E9', 'F')):
            return 'error'
        elif code.startswith(('E', 'W')):
            return 'warning'
        else:
            return 'info'
    
    def _count_test_files(self, component: Component) -> int:
        """Count test files related to a component"""
        count = 0
        
        if component.path:
            component_dir = self.project_root / Path(component.path).parent
            
            # Look for test files in the component directory and tests directory
            search_dirs = [component_dir]
            
            # Also check common test directories
            test_dirs = [
                self.project_root / 'tests',
                self.project_root / 'test',
                component_dir / 'tests',
                component_dir / 'test'
            ]
            
            for test_dir in test_dirs:
                if test_dir.exists():
                    search_dirs.append(test_dir)
            
            for search_dir in search_dirs:
                if search_dir.exists():
                    for test_file in search_dir.rglob('test_*.py'):
                        if self._is_related_test_file(test_file, component):
                            count += 1
                    for test_file in search_dir.rglob('*_test.py'):
                        if self._is_related_test_file(test_file, component):
                            count += 1
        
        return count
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file"""
        name = file_path.name
        return (name.startswith('test_') or name.endswith('_test.py') or 
                'test' in str(file_path.parent).lower())
    
    def _is_related_test_file(self, test_file: Path, component: Component) -> bool:
        """Check if a test file is related to a component"""
        test_name = test_file.stem.lower()
        component_name = component.name.lower().replace(' ', '_')
        
        # More specific heuristic: test file name contains significant component name parts
        # Exclude common words like "test", "component", etc.
        excluded_words = {'test', 'component', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        component_words = [word for word in component_name.split('_') if len(word) > 3 and word not in excluded_words]
        
        if not component_words:
            # Fallback to exact component name match
            return component_name in test_name
        
        return component_name in test_name or any(
            word in test_name for word in component_words
        )
    
    def _calculate_code_quality_score(self, issues: List[QualityIssue], file_count: int) -> float:
        """Calculate code quality score based on linting issues"""
        if file_count == 0:
            return 0.0
        
        # Weight issues by severity
        severity_weights = {
            'error': 1.0,
            'warning': 0.5,
            'info': 0.1
        }
        
        total_penalty = sum(
            severity_weights.get(issue.severity, 0.5) for issue in issues
        )
        
        # Calculate score (fewer issues = higher score)
        max_penalty = file_count * 10  # Assume max 10 major issues per file
        score = max(0.0, 1.0 - (total_penalty / max_penalty))
        
        return score
    
    def _calculate_complexity_score(self, python_files: List[Path]) -> float:
        """Calculate complexity score based on cyclomatic complexity"""
        if not python_files:
            return 0.0
        
        total_complexity = 0
        total_functions = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_complexity, file_functions = self._calculate_file_complexity(tree)
                total_complexity += file_complexity
                total_functions += file_functions
                
            except Exception as e:
                self.logger.warning(f"Could not analyze complexity for {file_path}: {e}")
        
        if total_functions == 0:
            return 1.0
        
        # Average complexity per function
        avg_complexity = total_complexity / total_functions
        
        # Convert to score (lower complexity = higher score)
        # Complexity > 10 is considered high
        score = max(0.0, 1.0 - (avg_complexity - 1) / 9)
        return min(1.0, score)
    
    def _calculate_file_complexity(self, tree: ast.AST) -> Tuple[int, int]:
        """Calculate cyclomatic complexity for a file"""
        complexity = 0
        function_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_count += 1
                # Base complexity is 1 for each function
                func_complexity = 1
                
                # Add complexity for control flow statements
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                        func_complexity += 1
                    elif isinstance(child, ast.ExceptHandler):
                        func_complexity += 1
                    elif isinstance(child, (ast.And, ast.Or)):
                        func_complexity += 1
                
                complexity += func_complexity
        
        return complexity, function_count
    
    def _calculate_maintainability_score(self, python_files: List[Path]) -> float:
        """Calculate maintainability score based on various factors"""
        if not python_files:
            return 0.0
        
        total_score = 0.0
        file_count = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Calculate various maintainability factors
                lines = content.split('\n')
                
                # Factor 1: File length (shorter is better)
                length_score = max(0.0, 1.0 - len(lines) / 1000)  # Penalty after 1000 lines
                
                # Factor 2: Average line length
                non_empty_lines = [line for line in lines if line.strip()]
                if non_empty_lines:
                    avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
                    line_length_score = max(0.0, 1.0 - (avg_line_length - 80) / 40)  # Penalty after 80 chars
                else:
                    line_length_score = 1.0
                
                # Factor 3: Comment ratio
                comment_lines = len([line for line in lines if line.strip().startswith('#')])
                comment_ratio = comment_lines / len(lines) if lines else 0
                comment_score = min(1.0, comment_ratio * 5)  # Good if 20% comments
                
                # Combine factors
                file_score = (length_score + line_length_score + comment_score) / 3
                total_score += min(1.0, file_score)  # Cap at 1.0
                file_count += 1
                
            except Exception as e:
                self.logger.warning(f"Could not analyze maintainability for {file_path}: {e}")
        
        return total_score / file_count if file_count > 0 else 0.0
    
    def _calculate_overall_quality_score(self, code_quality: CodeQualityResult, 
                                       documentation: DocumentationResult,
                                       test_coverage: TestCoverageResult) -> float:
        """Calculate overall quality score from individual metrics"""
        # Weights for different quality aspects
        weights = {
            'code_quality': 0.4,
            'documentation': 0.3,
            'test_coverage': 0.3
        }
        
        # Normalize test coverage percentage to 0-1 scale
        coverage_score = test_coverage.coverage_percentage / 100.0
        
        # Calculate weighted average
        overall_score = (
            code_quality.quality_score * weights['code_quality'] +
            documentation.documentation_score * weights['documentation'] +
            coverage_score * weights['test_coverage']
        )
        
        return overall_score
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level based on score"""
        if score >= self.quality_thresholds[QualityLevel.EXCELLENT]:
            return QualityLevel.EXCELLENT
        elif score >= self.quality_thresholds[QualityLevel.GOOD]:
            return QualityLevel.GOOD
        elif score >= self.quality_thresholds[QualityLevel.FAIR]:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR
    
    def _get_coverage_data(self, component: Component, python_files: List[Path]) -> Optional[Dict[str, Any]]:
        """Get actual test coverage data using coverage.py"""
        try:
            import coverage
            
            # Create coverage instance
            cov = coverage.Coverage()
            
            # Look for existing coverage data file
            coverage_file = self.project_root / '.coverage'
            if not coverage_file.exists():
                # Try to find coverage data in common locations
                alt_locations = [
                    self.project_root / 'coverage.xml',
                    self.project_root / 'htmlcov' / 'index.html',
                    self.project_root / '.pytest_cache' / '.coverage'
                ]
                
                for alt_file in alt_locations:
                    if alt_file.exists():
                        coverage_file = alt_file
                        break
                else:
                    # No coverage data found
                    return None
            
            # Load coverage data
            cov.load()
            
            # Get coverage for component files
            total_lines = 0
            covered_lines = 0
            uncovered_files = []
            
            for py_file in python_files:
                try:
                    # Get relative path for coverage lookup
                    rel_path = py_file.relative_to(self.project_root)
                    
                    # Get coverage analysis for this file
                    analysis = cov.analysis2(str(rel_path))
                    if analysis:
                        _, statements, _, missing, _ = analysis
                        file_total = len(statements)
                        file_covered = file_total - len(missing)
                        
                        total_lines += file_total
                        covered_lines += file_covered
                        
                        if len(missing) > 0:
                            uncovered_files.append(str(rel_path))
                            
                except Exception as e:
                    self.logger.debug(f"Could not get coverage for {py_file}: {e}")
                    continue
            
            if total_lines > 0:
                coverage_percentage = (covered_lines / total_lines) * 100
                return {
                    'total_lines': total_lines,
                    'covered_lines': covered_lines,
                    'coverage_percentage': coverage_percentage,
                    'uncovered_files': uncovered_files
                }
            
        except ImportError:
            self.logger.debug("Coverage module not available")
        except Exception as e:
            self.logger.debug(f"Could not load coverage data: {e}")
        
        return None
    
    def _estimate_test_coverage(self, component: Component, python_files: List[Path], test_count: int) -> TestCoverageResult:
        """Estimate test coverage based on heuristics"""
        result = TestCoverageResult()
        result.test_files_count = test_count
        
        # Count total lines of code
        total_lines = 0
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Count non-empty, non-comment lines
                    code_lines = [
                        line for line in lines 
                        if line.strip() and not line.strip().startswith('#')
                    ]
                    total_lines += len(code_lines)
            except Exception as e:
                self.logger.debug(f"Could not count lines in {py_file}: {e}")
        
        result.total_lines = total_lines
        
        if test_count == 0:
            result.coverage_percentage = 0.0
            result.covered_lines = 0
            result.uncovered_files = [str(f.relative_to(self.project_root)) for f in python_files]
        else:
            # Estimate coverage based on test file count and code complexity
            # More test files generally mean better coverage
            base_coverage = min(80.0, test_count * 25.0)  # Up to 80% with 4+ test files
            
            # Adjust based on code complexity
            complexity_factor = self._estimate_complexity_factor(python_files)
            estimated_coverage = base_coverage * complexity_factor
            
            result.coverage_percentage = max(10.0, min(90.0, estimated_coverage))
            result.covered_lines = int((result.coverage_percentage / 100.0) * total_lines)
            
            # Assume some files might not be fully covered
            if result.coverage_percentage < 100.0:
                uncovered_count = max(1, len(python_files) // 3)
                result.uncovered_files = [
                    str(f.relative_to(self.project_root)) 
                    for f in python_files[:uncovered_count]
                ]
        
        return result
    
    def _estimate_complexity_factor(self, python_files: List[Path]) -> float:
        """Estimate complexity factor for coverage estimation"""
        if not python_files:
            return 1.0
        
        total_complexity = 0
        total_functions = 0
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                complexity, functions = self._calculate_file_complexity(tree)
                total_complexity += complexity
                total_functions += functions
            except Exception:
                continue
        
        if total_functions == 0:
            return 1.0
        
        avg_complexity = total_complexity / total_functions
        
        # Higher complexity means lower coverage factor
        # Complexity 1-3: factor 1.0, Complexity 4-6: factor 0.8, etc.
        factor = max(0.3, 1.0 - (avg_complexity - 1) * 0.1)
        return factor

    def _generate_quality_recommendations(self, code_quality: CodeQualityResult,
                                        documentation: DocumentationResult,
                                        test_coverage: TestCoverageResult) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        # Code quality recommendations
        if code_quality.quality_score < 0.8:
            error_count = len([i for i in code_quality.issues if i.severity == 'error'])
            warning_count = len([i for i in code_quality.issues if i.severity == 'warning'])
            
            if error_count > 0:
                recommendations.append(f"Fix {error_count} code errors to improve quality")
            if warning_count > 0:
                recommendations.append(f"Address {warning_count} code warnings")
        
        if code_quality.complexity_score < 0.7:
            recommendations.append("Reduce code complexity by breaking down large functions")
        
        # Documentation recommendations
        if documentation.documentation_score < 0.8:
            missing_funcs = documentation.total_functions - documentation.documented_functions
            missing_classes = documentation.total_classes - documentation.documented_classes
            
            if missing_funcs > 0:
                recommendations.append(f"Add docstrings to {missing_funcs} functions")
            if missing_classes > 0:
                recommendations.append(f"Add docstrings to {missing_classes} classes")
        
        # Test coverage recommendations
        if test_coverage.coverage_percentage < 80:
            recommendations.append(f"Increase test coverage from {test_coverage.coverage_percentage:.1f}% to at least 80%")
        
        if test_coverage.test_files_count == 0:
            recommendations.append("Create unit tests for this component")
        elif test_coverage.test_files_count < 3:
            recommendations.append(f"Add more test files (currently {test_coverage.test_files_count}, recommended: 3+)")
        
        if test_coverage.uncovered_files:
            uncovered_count = len(test_coverage.uncovered_files)
            if uncovered_count <= 3:
                file_list = ", ".join(test_coverage.uncovered_files)
                recommendations.append(f"Add tests for uncovered files: {file_list}")
            else:
                recommendations.append(f"Add tests for {uncovered_count} uncovered files")
        
        # Integration test recommendations
        if test_coverage.coverage_percentage > 0 and test_coverage.coverage_percentage < 60:
            recommendations.append("Consider adding integration tests to complement unit tests")
        
        return recommendations
    
    def run_coverage_analysis(self, component: Component) -> Optional[Dict[str, Any]]:
        """Run coverage analysis for a component using pytest-cov"""
        try:
            python_files = self._get_component_python_files(component)
            if not python_files:
                return None
            
            # Get the component's module path for coverage
            if component.path:
                component_dir = Path(component.path).parent
                module_path = str(component_dir).replace('/', '.').replace('\\', '.')
                
                # Run pytest with coverage for this specific module
                cmd = [
                    'python', '-m', 'pytest', 
                    '--cov=' + module_path,
                    '--cov-report=json',
                    '--cov-report=term-missing',
                    '-v'
                ]
                
                # Look for related test files
                test_files = []
                for test_dir in ['tests', 'test']:
                    test_path = self.project_root / test_dir
                    if test_path.exists():
                        for test_file in test_path.rglob('test_*.py'):
                            if self._is_related_test_file(test_file, component):
                                test_files.append(str(test_file))
                
                if test_files:
                    cmd.extend(test_files)
                else:
                    # Run all tests if no specific tests found
                    cmd.append('tests/')
                
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    # Try to read coverage.json if it was generated
                    coverage_json = self.project_root / 'coverage.json'
                    if coverage_json.exists():
                        with open(coverage_json, 'r') as f:
                            coverage_data = json.load(f)
                        
                        # Extract relevant data
                        files_data = coverage_data.get('files', {})
                        total_lines = 0
                        covered_lines = 0
                        uncovered_files = []
                        
                        for file_path, file_data in files_data.items():
                            if any(str(pf).endswith(file_path) for pf in python_files):
                                summary = file_data.get('summary', {})
                                file_total = summary.get('num_statements', 0)
                                file_covered = summary.get('covered_lines', 0)
                                
                                total_lines += file_total
                                covered_lines += file_covered
                                
                                if file_covered < file_total:
                                    uncovered_files.append(file_path)
                        
                        if total_lines > 0:
                            return {
                                'total_lines': total_lines,
                                'covered_lines': covered_lines,
                                'coverage_percentage': (covered_lines / total_lines) * 100,
                                'uncovered_files': uncovered_files,
                                'raw_data': coverage_data
                            }
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Coverage analysis timed out for {component.name}")
        except Exception as e:
            self.logger.debug(f"Could not run coverage analysis for {component.name}: {e}")
        
        return None

    def generate_quality_report(self, results: List[QualityAssessmentResult]) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        if not results:
            return {"error": "No quality assessment results provided"}
        
        # Calculate aggregate metrics
        total_components = len(results)
        quality_levels = {level: 0 for level in QualityLevel}
        
        total_quality_score = 0.0
        total_code_quality = 0.0
        total_documentation = 0.0
        total_coverage = 0.0
        
        all_issues = []
        all_recommendations = []
        
        for result in results:
            quality_levels[result.quality_level] += 1
            total_quality_score += result.overall_quality_score
            total_code_quality += result.code_quality.quality_score
            total_documentation += result.documentation.documentation_score
            total_coverage += result.test_coverage.coverage_percentage
            
            all_issues.extend(result.code_quality.issues)
            all_recommendations.extend(result.recommendations)
        
        # Calculate averages
        avg_quality_score = total_quality_score / total_components
        avg_code_quality = total_code_quality / total_components
        avg_documentation = total_documentation / total_components
        avg_coverage = total_coverage / total_components
        
        return {
            "summary": {
                "total_components": total_components,
                "average_quality_score": avg_quality_score,
                "average_code_quality": avg_code_quality,
                "average_documentation_score": avg_documentation,
                "average_test_coverage": avg_coverage
            },
            "quality_distribution": {
                level.value: count for level, count in quality_levels.items()
            },
            "issues": {
                "total_issues": len(all_issues),
                "errors": len([i for i in all_issues if i.severity == 'error']),
                "warnings": len([i for i in all_issues if i.severity == 'warning']),
                "info": len([i for i in all_issues if i.severity == 'info'])
            },
            "recommendations": list(set(all_recommendations)),  # Remove duplicates
            "detailed_results": [
                {
                    "component_name": result.component.name,
                    "quality_level": result.quality_level.value,
                    "overall_score": result.overall_quality_score,
                    "code_quality_score": result.code_quality.quality_score,
                    "documentation_score": result.documentation.documentation_score,
                    "test_coverage": result.test_coverage.coverage_percentage,
                    "issues_count": len(result.code_quality.issues),
                    "recommendations_count": len(result.recommendations)
                }
                for result in results
            ]
        }