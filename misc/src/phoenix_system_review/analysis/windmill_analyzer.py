"""
Windmill GitOps Analysis for Phoenix Hydra System Review

Provides specialized analysis capabilities for Windmill script configurations,
GitOps workflow evaluation, and TypeScript/Python script quality assessment.
"""

import json
import os
import ast
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..models.data_models import Component, ComponentStatus, Issue, Priority, EvaluationResult


class ScriptLanguage(Enum):
    """Supported script languages in Windmill"""
    TYPESCRIPT = "typescript"
    PYTHON3 = "python3"
    BASH = "bash"
    DENO = "deno"
    GO = "go"
    UNKNOWN = "unknown"


class WorkflowType(Enum):
    """Types of Windmill workflows"""
    SCRIPT = "script"
    FLOW = "flow"
    APP = "app"
    RESOURCE = "resource"


@dataclass
class WindmillScript:
    """Information about a Windmill script"""
    path: str
    language: ScriptLanguage
    content: str
    summary: Optional[str] = None
    parameters: Dict[str, Any] = None
    resource_type: Optional[str] = None
    lock: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None


@dataclass
class WindmillFlow:
    """Information about a Windmill flow"""
    path: str
    summary: str
    value: Dict[str, Any]
    modules: List[Dict[str, Any]] = None
    failure_module: Optional[Dict[str, Any]] = None
    retry: Optional[Dict[str, Any]] = None


@dataclass
class WindmillWorkspace:
    """Information about a Windmill workspace"""
    name: str
    version: str
    scripts: List[WindmillScript]
    flows: List[WindmillFlow]
    resources: List[Dict[str, Any]]
    variables: List[Dict[str, Any]]


@dataclass
class ScriptQualityMetrics:
    """Quality metrics for a script"""
    lines_of_code: int
    complexity_score: float
    has_error_handling: bool
    has_documentation: bool
    has_type_annotations: bool
    security_issues: List[str]
    performance_issues: List[str]
    maintainability_score: float


@dataclass
class WindmillAnalysis:
    """Analysis results for Windmill GitOps"""
    workspaces: List[WindmillWorkspace]
    total_scripts: int
    total_flows: int
    script_quality_scores: Dict[str, ScriptQualityMetrics]
    gitops_readiness: float
    issues: List[Issue]
    health_score: float


class WindmillAnalyzer:
    """
    Analyzer for Windmill GitOps infrastructure in Phoenix Hydra.
    
    Provides comprehensive analysis of:
    - Windmill script configurations and quality
    - GitOps workflow evaluation
    - TypeScript/Python script assessment
    - Integration with Phoenix Hydra services
    """
    
    def __init__(self, project_root: str, windmill_url: str = "http://localhost:8000"):
        """
        Initialize Windmill analyzer.
        
        Args:
            project_root: Root directory of the Phoenix Hydra project
            windmill_url: URL of the Windmill instance
        """
        self.project_root = Path(project_root)
        self.windmill_url = windmill_url
        self.windmill_dir = self.project_root / "windmill-scripts"
        
        # Expected Phoenix Hydra Windmill scripts
        self.expected_scripts = {
            "monetization/affiliate_badges": {
                "language": ScriptLanguage.TYPESCRIPT,
                "required_functions": ["main"],
                "required_integrations": ["digitalocean", "customgpt", "huggingface"],
                "description": "Affiliate program badge management"
            },
            "monetization/marketplace_enterprise": {
                "language": ScriptLanguage.PYTHON3,
                "required_functions": ["main"],
                "required_integrations": ["aws", "cloudflare", "nca_toolkit"],
                "description": "Enterprise marketplace configuration"
            },
            "grants/neotec_generator": {
                "language": ScriptLanguage.TYPESCRIPT,
                "required_functions": ["main"],
                "required_data": ["deadline", "amount", "trl_level"],
                "description": "NEOTEC grant application generator"
            },
            "grants/eic_accelerator": {
                "language": ScriptLanguage.PYTHON3,
                "required_functions": ["main"],
                "required_data": ["program", "max_amount", "deadline"],
                "description": "EIC Accelerator application configuration"
            }
        }
        
        # Phoenix Hydra specific validation rules
        self.validation_rules = {
            "api_endpoints": [
                "sea-turtle-app-nlak2.ondigitalocean.app",
                "localhost:8080",
                "localhost:8081"
            ],
            "monetization_sources": [
                "digitalocean_affiliate",
                "customgpt_affiliate",
                "aws_marketplace",
                "huggingface_marketplace",
                "cloudflare_workers"
            ],
            "grant_programs": [
                "neotec",
                "eic_accelerator",
                "enisa",
                "horizon_europe"
            ],
            "required_env_vars": [
                "WINDMILL_TOKEN",
                "WINDMILL_BASE_URL",
                "PHOENIX_API_KEY"
            ]
        }
    
    def analyze_windmill_configurations(self) -> List[WindmillWorkspace]:
        """
        Analyze Windmill configuration files in the project.
        
        Returns:
            List of WindmillWorkspace objects for each configuration
        """
        workspaces = []
        
        if not self.windmill_dir.exists():
            return workspaces
        
        # Find all Windmill configuration files
        config_files = list(self.windmill_dir.glob("*.json"))
        config_files.extend(self.windmill_dir.glob("windmill-*.json"))
        
        for config_file in config_files:
            try:
                workspace = self._parse_windmill_config(config_file)
                workspaces.append(workspace)
            except Exception as e:
                # Create workspace with error
                workspace = WindmillWorkspace(
                    name=config_file.stem,
                    version="unknown",
                    scripts=[],
                    flows=[],
                    resources=[],
                    variables=[]
                )
                workspaces.append(workspace)
        
        return workspaces
    
    def _parse_windmill_config(self, config_file: Path) -> WindmillWorkspace:
        """
        Parse a single Windmill configuration file.
        
        Args:
            config_file: Path to the configuration JSON file
            
        Returns:
            WindmillWorkspace object with parsed configuration
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Parse scripts
        scripts = []
        if 'scripts' in config_data:
            for script_data in config_data['scripts']:
                script = WindmillScript(
                    path=script_data.get('path', ''),
                    language=self._detect_script_language(script_data.get('language', '')),
                    content=script_data.get('content', ''),
                    summary=script_data.get('summary'),
                    parameters=script_data.get('parameters'),
                    resource_type=script_data.get('resource_type'),
                    lock=script_data.get('lock'),
                    schema=script_data.get('schema')
                )
                scripts.append(script)
        
        # Parse flows
        flows = []
        if 'flows' in config_data:
            for flow_data in config_data['flows']:
                flow = WindmillFlow(
                    path=flow_data.get('path', ''),
                    summary=flow_data.get('summary', ''),
                    value=flow_data.get('value', {}),
                    modules=flow_data.get('value', {}).get('modules', []),
                    failure_module=flow_data.get('value', {}).get('failure_module'),
                    retry=flow_data.get('value', {}).get('retry')
                )
                flows.append(flow)
        
        return WindmillWorkspace(
            name=config_data.get('name', config_file.stem),
            version=config_data.get('version', '1.0.0'),
            scripts=scripts,
            flows=flows,
            resources=config_data.get('resources', []),
            variables=config_data.get('variables', [])
        )
    
    def _detect_script_language(self, language_str: str) -> ScriptLanguage:
        """
        Detect script language from string.
        
        Args:
            language_str: Language string from configuration
            
        Returns:
            ScriptLanguage enum value
        """
        language_map = {
            'typescript': ScriptLanguage.TYPESCRIPT,
            'python3': ScriptLanguage.PYTHON3,
            'python': ScriptLanguage.PYTHON3,
            'bash': ScriptLanguage.BASH,
            'deno': ScriptLanguage.DENO,
            'go': ScriptLanguage.GO
        }
        
        return language_map.get(language_str.lower(), ScriptLanguage.UNKNOWN)
    
    def analyze_script_quality(self, script: WindmillScript) -> ScriptQualityMetrics:
        """
        Analyze the quality of a Windmill script.
        
        Args:
            script: WindmillScript object to analyze
            
        Returns:
            ScriptQualityMetrics with quality assessment
        """
        if script.language == ScriptLanguage.TYPESCRIPT:
            return self._analyze_typescript_quality(script)
        elif script.language == ScriptLanguage.PYTHON3:
            return self._analyze_python_quality(script)
        else:
            # Basic analysis for other languages
            return ScriptQualityMetrics(
                lines_of_code=len(script.content.split('\n')),
                complexity_score=0.5,
                has_error_handling=False,
                has_documentation=False,
                has_type_annotations=False,
                security_issues=[],
                performance_issues=[],
                maintainability_score=0.5
            )
    
    def _analyze_typescript_quality(self, script: WindmillScript) -> ScriptQualityMetrics:
        """
        Analyze TypeScript script quality.
        
        Args:
            script: WindmillScript with TypeScript content
            
        Returns:
            ScriptQualityMetrics for TypeScript script
        """
        content = script.content
        lines = content.split('\n')
        
        # Basic metrics
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        # Check for error handling
        has_error_handling = any(keyword in content for keyword in ['try', 'catch', 'throw', 'Error'])
        
        # Check for documentation
        has_documentation = any(marker in content for marker in ['/**', '///', '@param', '@returns'])
        
        # Check for type annotations
        has_type_annotations = any(pattern in content for pattern in [': string', ': number', ': boolean', ': any', 'interface', 'type '])
        
        # Security issues
        security_issues = []
        if 'eval(' in content:
            security_issues.append("Use of eval() function")
        if 'innerHTML' in content:
            security_issues.append("Direct innerHTML manipulation")
        if 'document.write' in content:
            security_issues.append("Use of document.write")
        
        # Performance issues
        performance_issues = []
        if content.count('for (') > 3:
            performance_issues.append("Multiple nested loops detected")
        if 'JSON.parse(JSON.stringify(' in content:
            performance_issues.append("Inefficient deep cloning")
        
        # Calculate complexity score (simplified)
        complexity_indicators = content.count('if ') + content.count('for ') + content.count('while ') + content.count('switch ')
        complexity_score = min(1.0, complexity_indicators / max(1, lines_of_code / 10))
        
        # Calculate maintainability score
        maintainability_factors = [
            has_error_handling,
            has_documentation,
            has_type_annotations,
            len(security_issues) == 0,
            len(performance_issues) == 0,
            lines_of_code < 100  # Reasonable size
        ]
        maintainability_score = sum(maintainability_factors) / len(maintainability_factors)
        
        return ScriptQualityMetrics(
            lines_of_code=lines_of_code,
            complexity_score=complexity_score,
            has_error_handling=has_error_handling,
            has_documentation=has_documentation,
            has_type_annotations=has_type_annotations,
            security_issues=security_issues,
            performance_issues=performance_issues,
            maintainability_score=maintainability_score
        )
    
    def _analyze_python_quality(self, script: WindmillScript) -> ScriptQualityMetrics:
        """
        Analyze Python script quality.
        
        Args:
            script: WindmillScript with Python content
            
        Returns:
            ScriptQualityMetrics for Python script
        """
        content = script.content
        lines = content.split('\n')
        
        # Basic metrics
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Check for error handling
        has_error_handling = any(keyword in content for keyword in ['try:', 'except:', 'raise', 'Exception'])
        
        # Check for documentation
        has_documentation = any(marker in content for marker in ['"""', "'''", 'def ', 'class ']) and ('"""' in content or "'''" in content)
        
        # Check for type annotations
        has_type_annotations = any(pattern in content for pattern in [': str', ': int', ': bool', ': List', ': Dict', '-> '])
        
        # Security issues
        security_issues = []
        if 'eval(' in content:
            security_issues.append("Use of eval() function")
        if 'exec(' in content:
            security_issues.append("Use of exec() function")
        if 'os.system(' in content:
            security_issues.append("Direct system command execution")
        if 'subprocess.call(' in content and 'shell=True' in content:
            security_issues.append("Shell injection vulnerability")
        
        # Performance issues
        performance_issues = []
        if content.count('for ') > 3 and content.count('    for ') > 1:
            performance_issues.append("Multiple nested loops detected")
        if 'import *' in content:
            performance_issues.append("Wildcard imports affect performance")
        
        # Try to parse AST for more detailed analysis
        try:
            tree = ast.parse(content)
            
            # Count complexity indicators
            complexity_indicators = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    complexity_indicators += 1
            
            complexity_score = min(1.0, complexity_indicators / max(1, lines_of_code / 10))
            
        except SyntaxError:
            complexity_score = 0.8  # Assume high complexity if can't parse
            security_issues.append("Syntax errors in Python code")
        
        # Calculate maintainability score
        maintainability_factors = [
            has_error_handling,
            has_documentation,
            has_type_annotations,
            len(security_issues) == 0,
            len(performance_issues) == 0,
            lines_of_code < 150  # Reasonable size for Python
        ]
        maintainability_score = sum(maintainability_factors) / len(maintainability_factors)
        
        return ScriptQualityMetrics(
            lines_of_code=lines_of_code,
            complexity_score=complexity_score,
            has_error_handling=has_error_handling,
            has_documentation=has_documentation,
            has_type_annotations=has_type_annotations,
            security_issues=security_issues,
            performance_issues=performance_issues,
            maintainability_score=maintainability_score
        )
    
    def validate_gitops_workflow(self, workspace: WindmillWorkspace) -> List[Issue]:
        """
        Validate GitOps workflow patterns in Windmill workspace.
        
        Args:
            workspace: WindmillWorkspace to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for required Phoenix Hydra scripts
        script_paths = [script.path for script in workspace.scripts]
        for expected_path, expected_spec in self.expected_scripts.items():
            if not any(expected_path in path for path in script_paths):
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Expected script '{expected_path}' not found",
                    component="windmill_gitops",
                    recommendation=f"Create {expected_spec['description']} script"
                ))
        
        # Validate individual scripts
        for script in workspace.scripts:
            script_issues = self._validate_script_configuration(script)
            issues.extend(script_issues)
        
        # Validate flows
        for flow in workspace.flows:
            flow_issues = self._validate_flow_configuration(flow)
            issues.extend(flow_issues)
        
        # Check GitOps readiness
        gitops_issues = self._validate_gitops_readiness(workspace)
        issues.extend(gitops_issues)
        
        return issues
    
    def _validate_script_configuration(self, script: WindmillScript) -> List[Issue]:
        """Validate individual script configuration"""
        issues = []
        
        # Check for main function
        if 'function main(' not in script.content and 'def main(' not in script.content:
            issues.append(Issue(
                severity=Priority.HIGH,
                description=f"Script '{script.path}' lacks main function",
                component="windmill_script",
                recommendation="Add main function as entry point"
            ))
        
        # Check for Phoenix Hydra integrations
        if 'phoenix' in script.path.lower():
            has_phoenix_integration = any(
                endpoint in script.content 
                for endpoint in self.validation_rules['api_endpoints']
            )
            
            if not has_phoenix_integration:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Phoenix script '{script.path}' lacks Phoenix API integration",
                    component="windmill_script",
                    recommendation="Add integration with Phoenix Hydra services"
                ))
        
        # Check monetization scripts
        if 'monetization' in script.path:
            monetization_sources = sum(
                1 for source in self.validation_rules['monetization_sources']
                if source in script.content
            )
            
            if monetization_sources < 2:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Monetization script '{script.path}' covers few revenue sources",
                    component="windmill_script",
                    recommendation="Add more monetization source integrations"
                ))
        
        # Check grant scripts
        if 'grant' in script.path:
            grant_programs = sum(
                1 for program in self.validation_rules['grant_programs']
                if program in script.content.lower()
            )
            
            if grant_programs == 0:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description=f"Grant script '{script.path}' doesn't reference grant programs",
                    component="windmill_script",
                    recommendation="Add specific grant program configurations"
                ))
        
        return issues
    
    def _validate_flow_configuration(self, flow: WindmillFlow) -> List[Issue]:
        """Validate flow configuration"""
        issues = []
        
        # Check for modules
        if not flow.modules:
            issues.append(Issue(
                severity=Priority.HIGH,
                description=f"Flow '{flow.path}' has no modules",
                component="windmill_flow",
                recommendation="Add workflow modules to implement functionality"
            ))
            return issues
        
        # Check for error handling
        if not flow.failure_module:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Flow '{flow.path}' lacks failure handling",
                component="windmill_flow",
                recommendation="Add failure module for error handling"
            ))
        
        # Check module connections
        module_ids = [module.get('id', '') for module in flow.modules]
        for module in flow.modules:
            if 'input_transforms' in module:
                for transform_key, transform_value in module['input_transforms'].items():
                    if isinstance(transform_value, str) and 'results.' in transform_value:
                        referenced_module = transform_value.split('.')[1] if '.' in transform_value else ''
                        if referenced_module and referenced_module not in module_ids:
                            issues.append(Issue(
                                severity=Priority.HIGH,
                                description=f"Flow '{flow.path}' references non-existent module '{referenced_module}'",
                                component="windmill_flow",
                                recommendation="Fix module references or add missing modules"
                            ))
        
        return issues
    
    def _validate_gitops_readiness(self, workspace: WindmillWorkspace) -> List[Issue]:
        """Validate GitOps readiness of workspace"""
        issues = []
        
        # Check for version control integration
        if not workspace.version or workspace.version == "1.0.0":
            issues.append(Issue(
                severity=Priority.LOW,
                description=f"Workspace '{workspace.name}' uses default version",
                component="windmill_gitops",
                recommendation="Implement proper versioning for GitOps workflow"
            ))
        
        # Check for environment variables
        has_env_config = any(
            'env' in str(script.content).lower() or 'process.env' in script.content
            for script in workspace.scripts
        )
        
        if not has_env_config:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Workspace '{workspace.name}' lacks environment configuration",
                component="windmill_gitops",
                recommendation="Add environment variable management for different deployment stages"
            ))
        
        # Check for resource definitions
        if not workspace.resources:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Workspace '{workspace.name}' has no resource definitions",
                component="windmill_gitops",
                recommendation="Define resources for external service connections"
            ))
        
        # Check for automation flows
        automation_flows = [flow for flow in workspace.flows if 'automation' in flow.path.lower()]
        if not automation_flows:
            issues.append(Issue(
                severity=Priority.LOW,
                description=f"Workspace '{workspace.name}' lacks automation flows",
                component="windmill_gitops",
                recommendation="Create automation flows for GitOps deployment"
            ))
        
        return issues
    
    def check_windmill_health(self) -> Tuple[bool, Optional[str], List[Issue]]:
        """
        Check the health status of the Windmill instance.
        
        Returns:
            Tuple of (is_healthy, version, list_of_issues)
        """
        issues = []
        
        try:
            import requests
            
            # Check Windmill health endpoint
            response = requests.get(f"{self.windmill_url}/api/version", timeout=10)
            
            if response.status_code == 200:
                version_data = response.json()
                version = version_data.get('windmill_version', 'unknown')
                return True, version, issues
            else:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description=f"Windmill health check failed with status {response.status_code}",
                    component="windmill_instance",
                    recommendation="Check Windmill service status and configuration"
                ))
                return False, None, issues
                
        except ImportError:
            issues.append(Issue(
                severity=Priority.LOW,
                description="requests library not available for Windmill health check",
                component="windmill_instance",
                recommendation="Install requests library for health checking"
            ))
            return False, None, issues
        except Exception as e:
            # Check if it's a connection-related error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['connection', 'refused', 'timeout', 'unreachable']):
                issues.append(Issue(
                    severity=Priority.CRITICAL,
                    description=f"Cannot connect to Windmill instance: {str(e)}",
                    component="windmill_instance",
                    recommendation="Start Windmill service or check connection URL"
                ))
            else:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Windmill health check failed: {str(e)}",
                    component="windmill_instance",
                    recommendation="Verify Windmill service configuration and network connectivity"
                ))
            return False, None, issues
    
    def calculate_gitops_readiness_score(self, workspace: WindmillWorkspace, issues: List[Issue]) -> float:
        """
        Calculate GitOps readiness score for a workspace.
        
        Args:
            workspace: WindmillWorkspace object
            issues: List of issues found
            
        Returns:
            GitOps readiness score between 0.0 and 1.0
        """
        # Base score from workspace completeness
        base_factors = [
            len(workspace.scripts) > 0,
            len(workspace.flows) > 0,
            len(workspace.resources) > 0,
            workspace.version != "1.0.0",
            any('automation' in flow.path.lower() for flow in workspace.flows)
        ]
        base_score = sum(base_factors) / len(base_factors)
        
        # Deduct points for issues
        issue_penalty = 0.0
        for issue in issues:
            if issue.severity == Priority.CRITICAL:
                issue_penalty += 0.3
            elif issue.severity == Priority.HIGH:
                issue_penalty += 0.2
            elif issue.severity == Priority.MEDIUM:
                issue_penalty += 0.1
            elif issue.severity == Priority.LOW:
                issue_penalty += 0.05
        
        return max(0.0, base_score - issue_penalty)
    
    def generate_evaluation_result(self) -> EvaluationResult:
        """
        Generate comprehensive evaluation result for Windmill GitOps.
        
        Returns:
            EvaluationResult with complete analysis
        """
        # Create component
        component = Component(
            name="windmill_gitops",
            category="automation",
            path=str(self.windmill_dir),
            status=ComponentStatus.UNKNOWN
        )
        
        all_issues = []
        criteria_met = []
        criteria_missing = []
        
        # Analyze Windmill configurations
        workspaces = self.analyze_windmill_configurations()
        if workspaces:
            criteria_met.append("windmill_configs_present")
            
            total_gitops_score = 0.0
            for workspace in workspaces:
                workspace_issues = self.validate_gitops_workflow(workspace)
                all_issues.extend(workspace_issues)
                
                gitops_score = self.calculate_gitops_readiness_score(workspace, workspace_issues)
                total_gitops_score += gitops_score
                
                if gitops_score >= 0.7:
                    criteria_met.append(f"workspace_gitops_ready_{workspace.name}")
                else:
                    criteria_missing.append(f"workspace_gitops_ready_{workspace.name}")
            
            # Check for expected scripts
            all_script_paths = []
            for workspace in workspaces:
                all_script_paths.extend([script.path for script in workspace.scripts])
            
            for expected_path in self.expected_scripts.keys():
                if any(expected_path in path for path in all_script_paths):
                    criteria_met.append(f"expected_script_{expected_path.replace('/', '_')}")
                else:
                    criteria_missing.append(f"expected_script_{expected_path.replace('/', '_')}")
        else:
            criteria_missing.append("windmill_configs_present")
            all_issues.append(Issue(
                severity=Priority.HIGH,
                description="No Windmill configuration files found",
                component="windmill_gitops",
                recommendation="Create Windmill workspace configuration files"
            ))
        
        # Check Windmill health
        windmill_healthy, windmill_version, windmill_issues = self.check_windmill_health()
        all_issues.extend(windmill_issues)
        if windmill_healthy:
            criteria_met.append("windmill_instance_healthy")
        else:
            criteria_missing.append("windmill_instance_healthy")
        
        # Calculate completion percentage
        total_criteria = len(criteria_met) + len(criteria_missing)
        completion_percentage = len(criteria_met) / total_criteria if total_criteria > 0 else 0.0
        
        # Calculate quality score based on issues
        critical_high_issues = len([i for i in all_issues if i.severity in [Priority.CRITICAL, Priority.HIGH]])
        quality_score = max(0.0, 1.0 - (critical_high_issues * 0.2))
        
        return EvaluationResult(
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion_percentage,
            quality_score=quality_score,
            issues=all_issues
        )
    
    def generate_analysis_report(self) -> WindmillAnalysis:
        """
        Generate comprehensive Windmill analysis report.
        
        Returns:
            WindmillAnalysis object with complete analysis
        """
        workspaces = self.analyze_windmill_configurations()
        windmill_healthy, windmill_version, windmill_issues = self.check_windmill_health()
        
        all_issues = list(windmill_issues)
        script_quality_scores = {}
        total_scripts = 0
        total_flows = 0
        total_gitops_score = 0.0
        
        for workspace in workspaces:
            total_scripts += len(workspace.scripts)
            total_flows += len(workspace.flows)
            
            # Analyze script quality
            for script in workspace.scripts:
                quality_metrics = self.analyze_script_quality(script)
                script_quality_scores[script.path] = quality_metrics
            
            # Validate workspace
            workspace_issues = self.validate_gitops_workflow(workspace)
            all_issues.extend(workspace_issues)
            
            gitops_score = self.calculate_gitops_readiness_score(workspace, workspace_issues)
            total_gitops_score += gitops_score
        
        overall_gitops_readiness = total_gitops_score / len(workspaces) if workspaces else 0.0
        
        # Calculate overall health score
        health_factors = [
            windmill_healthy,
            len(workspaces) > 0,
            total_scripts > 0,
            overall_gitops_readiness >= 0.7
        ]
        health_score = sum(health_factors) / len(health_factors)
        
        return WindmillAnalysis(
            workspaces=workspaces,
            total_scripts=total_scripts,
            total_flows=total_flows,
            script_quality_scores=script_quality_scores,
            gitops_readiness=overall_gitops_readiness,
            issues=all_issues,
            health_score=health_score
        )