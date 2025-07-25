"""
Automation evaluation criteria for Phoenix Hydra System Review Tool

Defines evaluation criteria for automation components including VS Code tasks,
deployment scripts, Kiro agent hooks, and CI/CD pipeline readiness.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models.data_models import Component, ComponentCategory, Priority
from .infrastructure_criteria import CriterionDefinition, ComponentCriteria


class AutomationComponent(Enum):
    """Types of automation components"""
    VSCODE_INTEGRATION = "vscode_integration"
    DEPLOYMENT_SCRIPTS = "deployment_scripts"
    KIRO_AGENT_HOOKS = "kiro_agent_hooks"
    CICD_PIPELINE = "cicd_pipeline"
    BUILD_AUTOMATION = "build_automation"
    TESTING_AUTOMATION = "testing_automation"
    MONITORING_AUTOMATION = "monitoring_automation"


class AutomationCriteria:
    """
    Automation evaluation criteria for Phoenix Hydra components.
    
    Provides comprehensive criteria definitions for evaluating automation
    systems including VS Code integration, deployment scripts, agent hooks,
    and CI/CD pipeline readiness.
    """
    
    def __init__(self):
        """Initialize automation criteria definitions"""
        self._criteria_definitions = self._build_criteria_definitions()
    
    def _build_criteria_definitions(self) -> Dict[AutomationComponent, ComponentCriteria]:
        """Build complete criteria definitions for all automation components"""
        return {
            AutomationComponent.VSCODE_INTEGRATION: self._build_vscode_integration_criteria(),
            AutomationComponent.DEPLOYMENT_SCRIPTS: self._build_deployment_scripts_criteria(),
            AutomationComponent.KIRO_AGENT_HOOKS: self._build_kiro_agent_hooks_criteria(),
            AutomationComponent.CICD_PIPELINE: self._build_cicd_pipeline_criteria(),
            AutomationComponent.BUILD_AUTOMATION: self._build_build_automation_criteria(),
            AutomationComponent.TESTING_AUTOMATION: self._build_testing_automation_criteria(),
            AutomationComponent.MONITORING_AUTOMATION: self._build_monitoring_automation_criteria()
        }
    
    def _build_vscode_integration_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for VS Code integration"""
        criteria = [
            CriterionDefinition(
                id="vscode_tasks_configuration",
                name="VS Code Tasks Configuration",
                description="VS Code tasks properly configured for Phoenix Hydra development",
                category="ide_integration",
                weight=0.25,
                required=True,
                validation_method="check_vscode_tasks",
                expected_values=[".vscode/tasks.json", "deploy_phoenix_badges", "generate_neotec", "start_phoenix_hydra"],
                error_message="VS Code tasks not properly configured"
            ),
            CriterionDefinition(
                id="vscode_settings_validation",
                name="VS Code Settings Validation",
                description="VS Code workspace settings properly configured",
                category="ide_configuration",
                weight=0.20,
                required=True,
                validation_method="check_vscode_settings",
                expected_values=[".vscode/settings.json", "python.defaultInterpreter", "extensions.recommendations"],
                error_message="VS Code settings not properly configured"
            ),
            CriterionDefinition(
                id="vscode_launch_configuration",
                name="Launch Configuration",
                description="VS Code launch configurations for debugging and development",
                category="debugging",
                weight=0.15,
                required=False,
                validation_method="check_launch_config",
                expected_values=[".vscode/launch.json", "debug_configurations", "python_debugging"],
                error_message="VS Code launch configurations missing"
            ),
            CriterionDefinition(
                id="vscode_extensions_recommendations",
                name="Extension Recommendations",
                description="Recommended VS Code extensions for Phoenix Hydra development",
                category="development_environment",
                weight=0.15,
                required=False,
                validation_method="check_extension_recommendations",
                expected_values=[".vscode/extensions.json", "python", "docker", "yaml"],
                error_message="VS Code extension recommendations not configured"
            ),
            CriterionDefinition(
                id="vscode_snippets",
                name="Code Snippets",
                description="Custom code snippets for Phoenix Hydra development",
                category="productivity",
                weight=0.10,
                required=False,
                validation_method="check_code_snippets",
                expected_values=[".vscode/snippets/", "python.json", "yaml.json"],
                error_message="Custom code snippets not configured"
            ),
            CriterionDefinition(
                id="vscode_workspace_configuration",
                name="Workspace Configuration",
                description="VS Code workspace file properly configured",
                category="workspace_management",
                weight=0.15,
                required=False,
                validation_method="check_workspace_config",
                expected_values=["phoenix-hydra.code-workspace", "folders", "settings"],
                error_message="VS Code workspace configuration missing"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.VSCODE_INTEGRATION,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["vscode_tasks_configuration", "vscode_settings_validation"]
        )
    
    def _build_deployment_scripts_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for deployment scripts"""
        criteria = [
            CriterionDefinition(
                id="deployment_powershell_scripts",
                name="PowerShell Deployment Scripts",
                description="PowerShell deployment scripts for Windows environments",
                category="windows_deployment",
                weight=0.25,
                required=True,
                validation_method="check_powershell_scripts",
                expected_values=["complete-phoenix-deployment.ps1", "error_handling", "logging"],
                error_message="PowerShell deployment scripts not functional"
            ),
            CriterionDefinition(
                id="deployment_bash_scripts",
                name="Bash Deployment Scripts",
                description="Bash deployment scripts for Linux/macOS environments",
                category="unix_deployment",
                weight=0.25,
                required=True,
                validation_method="check_bash_scripts",
                expected_values=["complete-phoenix-deployment.sh", "error_handling", "logging"],
                error_message="Bash deployment scripts not functional"
            ),
            CriterionDefinition(
                id="deployment_automation_scripts",
                name="Automation Scripts",
                description="Node.js automation scripts for various deployment tasks",
                category="automation",
                weight=0.20,
                required=True,
                validation_method="check_automation_scripts",
                expected_values=["deploy-badges.js", "revenue-tracking.js", "neotec-generator.py"],
                error_message="Automation scripts not functional"
            ),
            CriterionDefinition(
                id="deployment_error_handling",
                name="Error Handling and Logging",
                description="Comprehensive error handling and logging in deployment scripts",
                category="reliability",
                weight=0.15,
                required=True,
                validation_method="check_error_handling",
                expected_values=["try_catch_blocks", "logging_system", "rollback_procedures"],
                error_message="Error handling and logging insufficient"
            ),
            CriterionDefinition(
                id="deployment_configuration_management",
                name="Configuration Management",
                description="Configuration management and environment-specific deployments",
                category="configuration",
                weight=0.10,
                required=False,
                validation_method="check_config_management",
                expected_values=["environment_configs", "parameter_validation", "config_templates"],
                error_message="Configuration management not implemented"
            ),
            CriterionDefinition(
                id="deployment_rollback_procedures",
                name="Rollback Procedures",
                description="Automated rollback procedures for failed deployments",
                category="disaster_recovery",
                weight=0.05,
                required=False,
                validation_method="check_rollback_procedures",
                expected_values=["rollback_scripts", "backup_procedures", "recovery_automation"],
                error_message="Rollback procedures not implemented"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.DEPLOYMENT_SCRIPTS,
            criteria=criteria,
            minimum_score=0.75,
            critical_criteria=["deployment_powershell_scripts", "deployment_bash_scripts", "deployment_automation_scripts"]
        )
    
    def _build_kiro_agent_hooks_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for Kiro agent hooks"""
        criteria = [
            CriterionDefinition(
                id="kiro_hooks_file_watchers",
                name="File System Watchers",
                description="File system watchers for automated responses to code changes",
                category="file_monitoring",
                weight=0.25,
                required=True,
                validation_method="check_file_watchers",
                expected_values=["src/hooks/event_sources/file_watcher.py", "debouncing", "pattern_matching"],
                error_message="File system watchers not properly configured"
            ),
            CriterionDefinition(
                id="kiro_hooks_container_events",
                name="Container Event Listeners",
                description="Container event listeners for automated container management",
                category="container_monitoring",
                weight=0.20,
                required=True,
                validation_method="check_container_events",
                expected_values=["src/containers/event_listener.py", "health_monitoring", "restart_automation"],
                error_message="Container event listeners not configured"
            ),
            CriterionDefinition(
                id="kiro_hooks_automation_triggers",
                name="Automation Triggers",
                description="Automated triggers for common development and deployment tasks",
                category="automation_triggers",
                weight=0.20,
                required=True,
                validation_method="check_automation_triggers",
                expected_values=["test_automation", "deployment_triggers", "code_quality_checks"],
                error_message="Automation triggers not properly configured"
            ),
            CriterionDefinition(
                id="kiro_hooks_event_bus",
                name="Event Bus System",
                description="Event bus system for coordinating hook executions",
                category="event_coordination",
                weight=0.15,
                required=False,
                validation_method="check_event_bus",
                expected_values=["src/hooks/core/events.py", "event_filtering", "subscription_management"],
                error_message="Event bus system not implemented"
            ),
            CriterionDefinition(
                id="kiro_hooks_error_handling",
                name="Hook Error Handling",
                description="Error handling and recovery mechanisms for failed hooks",
                category="reliability",
                weight=0.10,
                required=False,
                validation_method="check_hook_error_handling",
                expected_values=["error_recovery", "retry_mechanisms", "failure_notifications"],
                error_message="Hook error handling not implemented"
            ),
            CriterionDefinition(
                id="kiro_hooks_performance_monitoring",
                name="Performance Monitoring",
                description="Performance monitoring and optimization for hook executions",
                category="performance",
                weight=0.10,
                required=False,
                validation_method="check_hook_performance",
                expected_values=["execution_metrics", "performance_optimization", "resource_monitoring"],
                error_message="Hook performance monitoring not implemented"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.KIRO_AGENT_HOOKS,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["kiro_hooks_file_watchers", "kiro_hooks_container_events", "kiro_hooks_automation_triggers"]
        )
    
    def _build_cicd_pipeline_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for CI/CD pipeline"""
        criteria = [
            CriterionDefinition(
                id="cicd_pipeline_configuration",
                name="Pipeline Configuration",
                description="CI/CD pipeline configuration files and setup",
                category="pipeline_setup",
                weight=0.25,
                required=False,
                validation_method="check_pipeline_config",
                expected_values=[".github/workflows/", "ci.yml", "cd.yml"],
                error_message="CI/CD pipeline configuration not found"
            ),
            CriterionDefinition(
                id="cicd_automated_testing",
                name="Automated Testing Integration",
                description="Automated testing integration in CI/CD pipeline",
                category="testing_integration",
                weight=0.20,
                required=False,
                validation_method="check_automated_testing",
                expected_values=["pytest_integration", "coverage_reporting", "test_automation"],
                error_message="Automated testing not integrated in pipeline"
            ),
            CriterionDefinition(
                id="cicd_build_automation",
                name="Build Automation",
                description="Automated build processes in CI/CD pipeline",
                category="build_processes",
                weight=0.20,
                required=False,
                validation_method="check_build_automation",
                expected_values=["build_scripts", "artifact_generation", "dependency_management"],
                error_message="Build automation not configured"
            ),
            CriterionDefinition(
                id="cicd_deployment_automation",
                name="Deployment Automation",
                description="Automated deployment processes in CI/CD pipeline",
                category="deployment_automation",
                weight=0.15,
                required=False,
                validation_method="check_deployment_automation",
                expected_values=["deployment_stages", "environment_promotion", "rollback_capabilities"],
                error_message="Deployment automation not configured"
            ),
            CriterionDefinition(
                id="cicd_security_scanning",
                name="Security Scanning",
                description="Security scanning and vulnerability assessment in pipeline",
                category="security",
                weight=0.10,
                required=False,
                validation_method="check_security_scanning",
                expected_values=["vulnerability_scanning", "dependency_checking", "security_gates"],
                error_message="Security scanning not integrated"
            ),
            CriterionDefinition(
                id="cicd_monitoring_integration",
                name="Monitoring Integration",
                description="Monitoring and alerting integration in CI/CD pipeline",
                category="monitoring",
                weight=0.10,
                required=False,
                validation_method="check_monitoring_integration",
                expected_values=["pipeline_monitoring", "failure_alerts", "performance_tracking"],
                error_message="Monitoring integration not configured"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.CICD_PIPELINE,
            criteria=criteria,
            minimum_score=0.5,
            critical_criteria=[]  # CI/CD is optional for Phoenix Hydra
        )
    
    def _build_build_automation_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for build automation"""
        criteria = [
            CriterionDefinition(
                id="build_python_packaging",
                name="Python Packaging Automation",
                description="Automated Python package building and distribution",
                category="python_build",
                weight=0.30,
                required=True,
                validation_method="check_python_packaging",
                expected_values=["pyproject.toml", "build_scripts", "wheel_generation"],
                error_message="Python packaging automation not configured"
            ),
            CriterionDefinition(
                id="build_container_images",
                name="Container Image Building",
                description="Automated container image building and tagging",
                category="containerization",
                weight=0.25,
                required=True,
                validation_method="check_container_building",
                expected_values=["Dockerfile", "build_automation", "image_tagging"],
                error_message="Container image building not automated"
            ),
            CriterionDefinition(
                id="build_dependency_management",
                name="Dependency Management",
                description="Automated dependency management and updates",
                category="dependency_management",
                weight=0.20,
                required=False,
                validation_method="check_dependency_management",
                expected_values=["requirements.txt", "dependency_updates", "vulnerability_scanning"],
                error_message="Dependency management not automated"
            ),
            CriterionDefinition(
                id="build_artifact_generation",
                name="Artifact Generation",
                description="Automated generation of build artifacts and distributions",
                category="artifact_management",
                weight=0.15,
                required=False,
                validation_method="check_artifact_generation",
                expected_values=["build_artifacts", "distribution_packages", "versioning"],
                error_message="Artifact generation not automated"
            ),
            CriterionDefinition(
                id="build_quality_gates",
                name="Quality Gates",
                description="Quality gates and checks in build process",
                category="quality_assurance",
                weight=0.10,
                required=False,
                validation_method="check_quality_gates",
                expected_values=["code_quality_checks", "test_coverage", "build_validation"],
                error_message="Quality gates not implemented in build process"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.BUILD_AUTOMATION,
            criteria=criteria,
            minimum_score=0.6,
            critical_criteria=["build_python_packaging", "build_container_images"]
        )
    
    def _build_testing_automation_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for testing automation"""
        criteria = [
            CriterionDefinition(
                id="testing_unit_automation",
                name="Unit Test Automation",
                description="Automated unit testing with pytest and coverage reporting",
                category="unit_testing",
                weight=0.30,
                required=True,
                validation_method="check_unit_testing",
                expected_values=["pytest.ini", "test_discovery", "coverage_reporting"],
                error_message="Unit test automation not properly configured"
            ),
            CriterionDefinition(
                id="testing_integration_automation",
                name="Integration Test Automation",
                description="Automated integration testing for system components",
                category="integration_testing",
                weight=0.25,
                required=True,
                validation_method="check_integration_testing",
                expected_values=["integration_tests/", "test_fixtures", "database_testing"],
                error_message="Integration test automation not configured"
            ),
            CriterionDefinition(
                id="testing_code_quality_automation",
                name="Code Quality Automation",
                description="Automated code quality checks with linting and formatting",
                category="code_quality",
                weight=0.20,
                required=True,
                validation_method="check_code_quality",
                expected_values=["black", "ruff", "mypy", "pre_commit_hooks"],
                error_message="Code quality automation not configured"
            ),
            CriterionDefinition(
                id="testing_performance_automation",
                name="Performance Test Automation",
                description="Automated performance testing and benchmarking",
                category="performance_testing",
                weight=0.15,
                required=False,
                validation_method="check_performance_testing",
                expected_values=["performance_tests/", "benchmarking", "load_testing"],
                error_message="Performance test automation not implemented"
            ),
            CriterionDefinition(
                id="testing_security_automation",
                name="Security Test Automation",
                description="Automated security testing and vulnerability scanning",
                category="security_testing",
                weight=0.10,
                required=False,
                validation_method="check_security_testing",
                expected_values=["security_tests/", "vulnerability_scanning", "penetration_testing"],
                error_message="Security test automation not implemented"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.TESTING_AUTOMATION,
            criteria=criteria,
            minimum_score=0.75,
            critical_criteria=["testing_unit_automation", "testing_integration_automation", "testing_code_quality_automation"]
        )
    
    def _build_monitoring_automation_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for monitoring automation"""
        criteria = [
            CriterionDefinition(
                id="monitoring_health_checks",
                name="Automated Health Checks",
                description="Automated health checking for all Phoenix Hydra services",
                category="health_monitoring",
                weight=0.25,
                required=True,
                validation_method="check_health_monitoring",
                expected_values=["health_endpoints", "automated_checks", "status_reporting"],
                error_message="Automated health checks not configured"
            ),
            CriterionDefinition(
                id="monitoring_log_aggregation",
                name="Log Aggregation Automation",
                description="Automated log collection and aggregation system",
                category="log_management",
                weight=0.20,
                required=False,
                validation_method="check_log_aggregation",
                expected_values=["log_collection", "centralized_logging", "log_analysis"],
                error_message="Log aggregation automation not implemented"
            ),
            CriterionDefinition(
                id="monitoring_metrics_collection",
                name="Metrics Collection Automation",
                description="Automated metrics collection and monitoring",
                category="metrics_monitoring",
                weight=0.20,
                required=False,
                validation_method="check_metrics_collection",
                expected_values=["prometheus_integration", "metrics_endpoints", "data_collection"],
                error_message="Metrics collection automation not configured"
            ),
            CriterionDefinition(
                id="monitoring_alerting_automation",
                name="Alerting Automation",
                description="Automated alerting system for system issues and anomalies",
                category="alerting",
                weight=0.20,
                required=False,
                validation_method="check_alerting_automation",
                expected_values=["alert_rules", "notification_system", "escalation_procedures"],
                error_message="Alerting automation not configured"
            ),
            CriterionDefinition(
                id="monitoring_dashboard_automation",
                name="Dashboard Automation",
                description="Automated dashboard generation and updates",
                category="visualization",
                weight=0.15,
                required=False,
                validation_method="check_dashboard_automation",
                expected_values=["grafana_dashboards", "automated_updates", "visualization"],
                error_message="Dashboard automation not implemented"
            )
        ]
        
        return ComponentCriteria(
            component_type=AutomationComponent.MONITORING_AUTOMATION,
            criteria=criteria,
            minimum_score=0.6,
            critical_criteria=["monitoring_health_checks"]
        )
    
    def get_criteria_for_component(self, component_type: AutomationComponent) -> ComponentCriteria:
        """
        Get evaluation criteria for a specific automation component.
        
        Args:
            component_type: Type of automation component
            
        Returns:
            ComponentCriteria object with all criteria definitions
        """
        return self._criteria_definitions.get(component_type)
    
    def get_all_criteria(self) -> Dict[AutomationComponent, ComponentCriteria]:
        """
        Get all automation evaluation criteria.
        
        Returns:
            Dictionary mapping component types to their criteria
        """
        return self._criteria_definitions.copy()
    
    def get_criterion_by_id(self, component_type: AutomationComponent, criterion_id: str) -> Optional[CriterionDefinition]:
        """
        Get a specific criterion by ID.
        
        Args:
            component_type: Type of automation component
            criterion_id: ID of the criterion
            
        Returns:
            CriterionDefinition object or None if not found
        """
        criteria = self._criteria_definitions.get(component_type)
        if criteria:
            for criterion in criteria.criteria:
                if criterion.id == criterion_id:
                    return criterion
        return None
    
    def get_critical_criteria(self, component_type: AutomationComponent) -> List[CriterionDefinition]:
        """
        Get critical criteria for a component type.
        
        Args:
            component_type: Type of automation component
            
        Returns:
            List of critical CriterionDefinition objects
        """
        criteria = self._criteria_definitions.get(component_type)
        if criteria:
            critical_ids = criteria.critical_criteria
            return [
                criterion for criterion in criteria.criteria 
                if criterion.id in critical_ids
            ]
        return []
    
    def calculate_component_score(self, component_type: AutomationComponent, 
                                 evaluation_results: Dict[str, bool]) -> float:
        """
        Calculate weighted score for a component based on evaluation results.
        
        Args:
            component_type: Type of automation component
            evaluation_results: Dictionary mapping criterion IDs to pass/fail results
            
        Returns:
            Weighted score between 0.0 and 1.0
        """
        criteria = self._criteria_definitions.get(component_type)
        if not criteria:
            return 0.0
        
        total_weight = 0.0
        achieved_weight = 0.0
        
        for criterion in criteria.criteria:
            total_weight += criterion.weight
            if evaluation_results.get(criterion.id, False):
                achieved_weight += criterion.weight
        
        return achieved_weight / total_weight if total_weight > 0 else 0.0
    
    def validate_criteria_completeness(self) -> Dict[str, List[str]]:
        """
        Validate that all criteria definitions are complete and consistent.
        
        Returns:
            Dictionary of validation issues by component type
        """
        issues = {}
        
        for component_type, criteria in self._criteria_definitions.items():
            component_issues = []
            
            # Check total weight
            total_weight = sum(criterion.weight for criterion in criteria.criteria)
            if abs(total_weight - 1.0) > 0.01:
                component_issues.append(f"Total weight {total_weight:.2f} != 1.0")
            
            # Check for duplicate IDs
            criterion_ids = [criterion.id for criterion in criteria.criteria]
            if len(criterion_ids) != len(set(criterion_ids)):
                component_issues.append("Duplicate criterion IDs found")
            
            # Check critical criteria exist
            for critical_id in criteria.critical_criteria:
                if critical_id not in criterion_ids:
                    component_issues.append(f"Critical criterion '{critical_id}' not found")
            
            if component_issues:
                issues[component_type.value] = component_issues
        
        return issues
    
    def get_phoenix_automation_requirements(self) -> Dict[str, Any]:
        """
        Get Phoenix Hydra specific automation requirements and recommendations.
        
        Returns:
            Dictionary with Phoenix-specific automation requirements
        """
        return {
            "required_vscode_tasks": [
                "Deploy Phoenix Badges",
                "Generate NEOTEC Application", 
                "Update Revenue Metrics",
                "Start Phoenix Hydra (Podman)",
                "Phoenix Health Check"
            ],
            "required_deployment_scripts": [
                "complete-phoenix-deployment.ps1",
                "complete-phoenix-deployment.sh",
                "deploy-badges.js",
                "revenue-tracking.js",
                "neotec-generator.py"
            ],
            "required_agent_hooks": [
                "file_system_watchers",
                "container_event_listeners",
                "code_quality_automation",
                "deployment_triggers"
            ],
            "automation_priorities": {
                "high": ["VS Code integration", "deployment scripts", "agent hooks"],
                "medium": ["build automation", "testing automation"],
                "low": ["CI/CD pipeline", "monitoring automation"]
            },
            "phoenix_specific_automations": {
                "monetization": ["badge_deployment", "revenue_tracking", "grant_applications"],
                "infrastructure": ["container_management", "service_health", "backup_automation"],
                "development": ["code_quality", "testing", "documentation_generation"]
            }
        }