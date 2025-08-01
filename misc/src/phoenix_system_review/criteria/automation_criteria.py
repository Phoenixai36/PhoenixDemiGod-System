"""
Automation System Criteria for Phoenix Hydra System Review Tool

Defines evaluation criteria for automation components including VS Code tasks,
deployment scripts, Kiro agent hooks, and CI/CD pipeline readiness.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path

from ..models.data_models import Component, ComponentCategory, EvaluationCriterion, CriterionType


class AutomationComponentType(Enum):
    """Types of automation components"""
    VSCODE_TASKS = "vscode_tasks"
    DEPLOYMENT_SCRIPTS = "deployment_scripts"
    KIRO_AGENT_HOOKS = "kiro_agent_hooks"
    CICD_PIPELINE = "cicd_pipeline"
    BUILD_AUTOMATION = "build_automation"
    MONITORING_AUTOMATION = "monitoring_automation"


@dataclass
class VSCodeTaskCriteria:
    """Criteria for VS Code task evaluation"""
    required_tasks: List[str] = field(default_factory=lambda: [
        "Deploy Phoenix Badges",
        "Generate NEOTEC Application", 
        "Update Revenue Metrics",
        "Start Phoenix Hydra (Podman)",
        "Phoenix Health Check",
        "Run Tests",
        "Format Code",
        "Build Project"
    ])
    task_configuration_requirements: Dict[str, Any] = field(default_factory=lambda: {
        "version": "2.0.0",
        "tasks": {
            "required_properties": ["label", "type", "command"],
            "optional_properties": ["group", "presentation", "options", "dependsOn"]
        }
    })
    integration_requirements: List[str] = field(default_factory=lambda: [
        "Kiro agent hooks integration",
        "Terminal integration",
        "Problem matcher configuration",
        "Task dependencies"
    ])


@dataclass
class DeploymentScriptCriteria:
    """Criteria for deployment script evaluation"""
    required_scripts: Dict[str, List[str]] = field(default_factory=lambda: {
        "windows": [
            "complete-phoenix-deployment.ps1",
            "setup-environment.ps1",
            "deploy-containers.ps1",
            "health-check.ps1"
        ],
        "linux": [
            "complete-phoenix-deployment.sh",
            "setup-environment.sh", 
            "deploy-containers.sh",
            "health-check.sh"
        ]
    })
    script_requirements: Dict[str, Any] = field(default_factory=lambda: {
        "error_handling": True,
        "logging": True,
        "parameter_validation": True,
        "rollback_capability": True,
        "idempotent_operations": True
    })
    deployment_stages: List[str] = field(default_factory=lambda: [
        "Environment validation",
        "Dependency installation",
        "Service deployment",
        "Health verification",
        "Rollback procedures"
    ])


@dataclass
class KiroAgentHooksCriteria:
    """Criteria for Kiro agent hooks evaluation"""
    required_hooks: List[str] = field(default_factory=lambda: [
        "Code quality hooks (Python file changes)",
        "Infrastructure automation hooks (Terraform changes)",
        "Workflow synchronization hooks (Windmill/n8n)",
        "Revenue tracking hooks (monetization config)",
        "Container health monitoring hooks"
    ])
    hook_configuration: Dict[str, Any] = field(default_factory=lambda: {
        "event_sources": ["file_watcher", "container_monitor", "api_monitor"],
        "event_filtering": True,
        "debouncing": True,
        "error_handling": True,
        "parallel_execution": True
    })
    integration_points: List[str] = field(default_factory=lambda: [
        "VS Code tasks integration",
        "Container event system",
        "File system monitoring",
        "API health checks"
    ])


@dataclass
class CICDPipelineCriteria:
    """Criteria for CI/CD pipeline evaluation"""
    pipeline_stages: List[str] = field(default_factory=lambda: [
        "Code quality checks",
        "Unit testing",
        "Integration testing",
        "Security scanning",
        "Build artifacts",
        "Deployment automation",
        "Health verification"
    ])
    required_integrations: List[str] = field(default_factory=lambda: [
        "Git repository integration",
        "Container registry",
        "Testing frameworks",
        "Monitoring systems",
        "Notification systems"
    ])
    deployment_environments: List[str] = field(default_factory=lambda: [
        "Development",
        "Staging", 
        "Production"
    ])


class AutomationCriteriaEvaluator:
    """
    Evaluates automation system components against Phoenix Hydra requirements.
    
    Provides criteria for VS Code tasks, deployment scripts, Kiro agent hooks,
    and CI/CD pipeline readiness assessment.
    """
    
    def __init__(self, project_root: str):
        """Initialize automation criteria evaluator"""
        self.project_root = Path(project_root)
        self.vscode_criteria = VSCodeTaskCriteria()
        self.deployment_criteria = DeploymentScriptCriteria()
        self.hooks_criteria = KiroAgentHooksCriteria()
        self.cicd_criteria = CICDPipelineCriteria()
    
    def get_automation_criteria(self, component_type: AutomationComponentType) -> List[EvaluationCriterion]:
        """
        Get evaluation criteria for specific automation component type.
        
        Args:
            component_type: Type of automation component to evaluate
            
        Returns:
            List of evaluation criteria for the component type
        """
        criteria_map = {
            AutomationComponentType.VSCODE_TASKS: self._get_vscode_task_criteria,
            AutomationComponentType.DEPLOYMENT_SCRIPTS: self._get_deployment_script_criteria,
            AutomationComponentType.KIRO_AGENT_HOOKS: self._get_kiro_hooks_criteria,
            AutomationComponentType.CICD_PIPELINE: self._get_cicd_pipeline_criteria,
            AutomationComponentType.BUILD_AUTOMATION: self._get_build_automation_criteria,
            AutomationComponentType.MONITORING_AUTOMATION: self._get_monitoring_automation_criteria
        }
        
        return criteria_map.get(component_type, lambda: [])()
    
    def _get_vscode_task_criteria(self) -> List[EvaluationCriterion]:
        """Get VS Code task evaluation criteria"""
        criteria = []
        
        # Task configuration file existence
        criteria.append(EvaluationCriterion(
            id="vscode_tasks_config_exists",
            name="VS Code Tasks Configuration Exists",
            description="VS Code tasks.json configuration file exists",
            criterion_type=CriterionType.EXISTENCE,
            weight=0.2,
            is_critical=True,
            evaluation_method="file_exists",
            parameters={"file_path": ".vscode/tasks.json"}
        ))
        
        # Required tasks presence
        for task_name in self.vscode_criteria.required_tasks:
            criteria.append(EvaluationCriterion(
                id=f"vscode_task_{task_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}",
                name=f"VS Code Task: {task_name}",
                description=f"Required VS Code task '{task_name}' is configured",
                criterion_type=CriterionType.CONFIGURATION,
                weight=0.1,
                is_critical=task_name in ["Start Phoenix Hydra (Podman)", "Phoenix Health Check"],
                evaluation_method="json_contains",
                parameters={
                    "file_path": ".vscode/tasks.json",
                    "json_path": "tasks",
                    "search_key": "label",
                    "search_value": task_name
                }
            ))
        
        # Task configuration quality
        criteria.append(EvaluationCriterion(
            id="vscode_tasks_configuration_quality",
            name="VS Code Tasks Configuration Quality",
            description="Tasks have proper configuration with required properties",
            criterion_type=CriterionType.QUALITY,
            weight=0.15,
            is_critical=False,
            evaluation_method="json_schema_validation",
            parameters={
                "file_path": ".vscode/tasks.json",
                "schema": self.vscode_criteria.task_configuration_requirements
            }
        ))
        
        # Integration with Kiro hooks
        criteria.append(EvaluationCriterion(
            id="vscode_kiro_integration",
            name="VS Code Kiro Integration",
            description="VS Code tasks integrate with Kiro agent hooks",
            criterion_type=CriterionType.INTEGRATION,
            weight=0.1,
            is_critical=False,
            evaluation_method="integration_check",
            parameters={
                "integration_type": "kiro_hooks",
                "check_files": [".vscode/tasks.json", ".kiro/hooks/"]
            }
        ))
        
        return criteria
    
    def _get_deployment_script_criteria(self) -> List[EvaluationCriterion]:
        """Get deployment script evaluation criteria"""
        criteria = []
        
        # Platform-specific deployment scripts
        for platform, scripts in self.deployment_criteria.required_scripts.items():
            for script_name in scripts:
                criteria.append(EvaluationCriterion(
                    id=f"deployment_script_{platform}_{script_name.replace('.', '_').replace('-', '_')}",
                    name=f"Deployment Script: {script_name} ({platform})",
                    description=f"Required {platform} deployment script '{script_name}' exists",
                    criterion_type=CriterionType.EXISTENCE,
                    weight=0.15 if "complete-phoenix-deployment" in script_name else 0.1,
                    is_critical="complete-phoenix-deployment" in script_name,
                    evaluation_method="file_exists",
                    parameters={"file_path": f"scripts/{script_name}"}
                ))
        
        # Script quality requirements
        script_quality_criteria = [
            ("error_handling", "Error Handling", "Scripts include proper error handling", 0.15, True),
            ("logging", "Logging", "Scripts include structured logging", 0.1, False),
            ("parameter_validation", "Parameter Validation", "Scripts validate input parameters", 0.1, False),
            ("rollback_capability", "Rollback Capability", "Scripts support rollback operations", 0.15, True),
            ("idempotent_operations", "Idempotent Operations", "Scripts can be run multiple times safely", 0.1, False)
        ]
        
        for req_id, name, desc, weight, critical in script_quality_criteria:
            criteria.append(EvaluationCriterion(
                id=f"deployment_script_{req_id}",
                name=f"Deployment Script {name}",
                description=desc,
                criterion_type=CriterionType.QUALITY,
                weight=weight,
                is_critical=critical,
                evaluation_method="script_analysis",
                parameters={"requirement": req_id, "script_paths": ["scripts/"]}
            ))
        
        return criteria
    
    def _get_kiro_hooks_criteria(self) -> List[EvaluationCriterion]:
        """Get Kiro agent hooks evaluation criteria"""
        criteria = []
        
        # Hooks configuration existence
        criteria.append(EvaluationCriterion(
            id="kiro_hooks_config_exists",
            name="Kiro Hooks Configuration Exists",
            description="Kiro agent hooks configuration exists",
            criterion_type=CriterionType.EXISTENCE,
            weight=0.2,
            is_critical=True,
            evaluation_method="directory_exists",
            parameters={"directory_path": ".kiro/hooks/"}
        ))
        
        # Required hook types
        hook_types = [
            ("code_quality", "Code Quality Hooks", "Hooks for Python file changes and code quality", 0.15, True),
            ("infrastructure", "Infrastructure Automation Hooks", "Hooks for Terraform and infrastructure changes", 0.15, True),
            ("workflow_sync", "Workflow Synchronization Hooks", "Hooks for Windmill/n8n workflow sync", 0.1, False),
            ("revenue_tracking", "Revenue Tracking Hooks", "Hooks for monetization configuration changes", 0.15, True),
            ("container_health", "Container Health Monitoring", "Hooks for container health monitoring", 0.1, False)
        ]
        
        for hook_id, name, desc, weight, critical in hook_types:
            criteria.append(EvaluationCriterion(
                id=f"kiro_hook_{hook_id}",
                name=name,
                description=desc,
                criterion_type=CriterionType.FUNCTIONALITY,
                weight=weight,
                is_critical=critical,
                evaluation_method="hook_implementation_check",
                parameters={"hook_type": hook_id, "hooks_path": ".kiro/hooks/"}
            ))
        
        # Event system integration
        criteria.append(EvaluationCriterion(
            id="kiro_hooks_event_system",
            name="Kiro Hooks Event System Integration",
            description="Hooks integrate with event bus and filtering system",
            criterion_type=CriterionType.INTEGRATION,
            weight=0.1,
            is_critical=False,
            evaluation_method="event_system_check",
            parameters={"hooks_path": ".kiro/hooks/", "event_sources": self.hooks_criteria.hook_configuration["event_sources"]}
        ))
        
        return criteria
    
    def _get_cicd_pipeline_criteria(self) -> List[EvaluationCriterion]:
        """Get CI/CD pipeline evaluation criteria"""
        criteria = []
        
        # Pipeline configuration existence
        pipeline_configs = [
            (".github/workflows/", "GitHub Actions"),
            (".gitlab-ci.yml", "GitLab CI"),
            ("Jenkinsfile", "Jenkins"),
            (".azure-pipelines.yml", "Azure Pipelines")
        ]
        
        criteria.append(EvaluationCriterion(
            id="cicd_pipeline_config_exists",
            name="CI/CD Pipeline Configuration Exists",
            description="At least one CI/CD pipeline configuration exists",
            criterion_type=CriterionType.EXISTENCE,
            weight=0.2,
            is_critical=True,
            evaluation_method="any_file_exists",
            parameters={"file_paths": [config[0] for config in pipeline_configs]}
        ))
        
        # Pipeline stages
        for stage in self.cicd_criteria.pipeline_stages:
            criteria.append(EvaluationCriterion(
                id=f"cicd_stage_{stage.lower().replace(' ', '_')}",
                name=f"CI/CD Stage: {stage}",
                description=f"Pipeline includes {stage.lower()} stage",
                criterion_type=CriterionType.FUNCTIONALITY,
                weight=0.1,
                is_critical=stage in ["Unit testing", "Build artifacts", "Deployment automation"],
                evaluation_method="pipeline_stage_check",
                parameters={"stage": stage, "pipeline_configs": pipeline_configs}
            ))
        
        # Environment deployments
        for env in self.cicd_criteria.deployment_environments:
            criteria.append(EvaluationCriterion(
                id=f"cicd_deployment_{env.lower()}",
                name=f"CI/CD {env} Deployment",
                description=f"Pipeline supports deployment to {env.lower()} environment",
                criterion_type=CriterionType.DEPLOYMENT,
                weight=0.15 if env == "Production" else 0.1,
                is_critical=env in ["Development", "Production"],
                evaluation_method="deployment_environment_check",
                parameters={"environment": env, "pipeline_configs": pipeline_configs}
            ))
        
        return criteria
    
    def _get_build_automation_criteria(self) -> List[EvaluationCriterion]:
        """Get build automation evaluation criteria"""
        criteria = []
        
        # Build configuration files
        build_configs = [
            ("pyproject.toml", "Python Build Configuration", 0.2, True),
            ("package.json", "Node.js Build Configuration", 0.15, False),
            ("Dockerfile", "Container Build Configuration", 0.15, True),
            ("docker-compose.yml", "Multi-container Build Configuration", 0.1, False)
        ]
        
        for config_file, name, weight, critical in build_configs:
            criteria.append(EvaluationCriterion(
                id=f"build_config_{config_file.replace('.', '_').replace('-', '_')}",
                name=name,
                description=f"Build configuration file '{config_file}' exists and is properly configured",
                criterion_type=CriterionType.CONFIGURATION,
                weight=weight,
                is_critical=critical,
                evaluation_method="build_config_check",
                parameters={"config_file": config_file}
            ))
        
        # Build automation features
        build_features = [
            ("dependency_management", "Dependency Management", "Automated dependency installation and management", 0.15, True),
            ("test_automation", "Test Automation", "Automated test execution during build", 0.1, False),
            ("artifact_generation", "Artifact Generation", "Automated build artifact generation", 0.1, False),
            ("version_management", "Version Management", "Automated version management and tagging", 0.05, False)
        ]
        
        for feature_id, name, desc, weight, critical in build_features:
            criteria.append(EvaluationCriterion(
                id=f"build_automation_{feature_id}",
                name=f"Build Automation: {name}",
                description=desc,
                criterion_type=CriterionType.AUTOMATION,
                weight=weight,
                is_critical=critical,
                evaluation_method="build_feature_check",
                parameters={"feature": feature_id}
            ))
        
        return criteria
    
    def _get_monitoring_automation_criteria(self) -> List[EvaluationCriterion]:
        """Get monitoring automation evaluation criteria"""
        criteria = []
        
        # Monitoring configuration
        monitoring_configs = [
            ("monitoring/prometheus.yml", "Prometheus Configuration", 0.2, True),
            ("monitoring/grafana/", "Grafana Dashboards", 0.15, False),
            ("monitoring/alerts/", "Alert Rules", 0.15, True),
            (".kiro/hooks/monitoring/", "Monitoring Hooks", 0.1, False)
        ]
        
        for config_path, name, weight, critical in monitoring_configs:
            criteria.append(EvaluationCriterion(
                id=f"monitoring_config_{config_path.replace('/', '_').replace('.', '_')}",
                name=name,
                description=f"Monitoring configuration '{config_path}' exists",
                criterion_type=CriterionType.CONFIGURATION,
                weight=weight,
                is_critical=critical,
                evaluation_method="monitoring_config_check",
                parameters={"config_path": config_path}
            ))
        
        # Automated monitoring features
        monitoring_features = [
            ("health_checks", "Automated Health Checks", "Automated service health monitoring", 0.15, True),
            ("performance_monitoring", "Performance Monitoring", "Automated performance metrics collection", 0.1, False),
            ("log_aggregation", "Log Aggregation", "Automated log collection and analysis", 0.1, False),
            ("alerting", "Automated Alerting", "Automated alert generation and notification", 0.15, True)
        ]
        
        for feature_id, name, desc, weight, critical in monitoring_features:
            criteria.append(EvaluationCriterion(
                id=f"monitoring_automation_{feature_id}",
                name=f"Monitoring Automation: {name}",
                description=desc,
                criterion_type=CriterionType.AUTOMATION,
                weight=weight,
                is_critical=critical,
                evaluation_method="monitoring_feature_check",
                parameters={"feature": feature_id}
            ))
        
        return criteria
    
    def get_all_automation_criteria(self) -> Dict[str, List[EvaluationCriterion]]:
        """
        Get all automation criteria organized by component type.
        
        Returns:
            Dictionary mapping component types to their evaluation criteria
        """
        return {
            component_type.value: self.get_automation_criteria(component_type)
            for component_type in AutomationComponentType
        }
    
    def create_automation_components(self) -> List[Component]:
        """
        Create Component objects for all automation system components.
        
        Returns:
            List of Component objects for automation evaluation
        """
        components = []
        
        for component_type in AutomationComponentType:
            component = Component(
                name=component_type.value.replace('_', ' ').title(),
                category=ComponentCategory.AUTOMATION,
                description=self._get_component_description(component_type),
                path=self._get_component_path(component_type),
                criteria=self.get_automation_criteria(component_type)
            )
            components.append(component)
        
        return components
    
    def _get_component_description(self, component_type: AutomationComponentType) -> str:
        """Get description for automation component type"""
        descriptions = {
            AutomationComponentType.VSCODE_TASKS: "VS Code task automation for development workflow",
            AutomationComponentType.DEPLOYMENT_SCRIPTS: "Automated deployment and infrastructure scripts",
            AutomationComponentType.KIRO_AGENT_HOOKS: "Kiro agent hooks for event-driven automation",
            AutomationComponentType.CICD_PIPELINE: "Continuous integration and deployment pipeline",
            AutomationComponentType.BUILD_AUTOMATION: "Automated build and artifact generation",
            AutomationComponentType.MONITORING_AUTOMATION: "Automated monitoring and alerting system"
        }
        return descriptions.get(component_type, "Automation system component")
    
    def _get_component_path(self, component_type: AutomationComponentType) -> str:
        """Get primary path for automation component type"""
        paths = {
            AutomationComponentType.VSCODE_TASKS: ".vscode/",
            AutomationComponentType.DEPLOYMENT_SCRIPTS: "scripts/",
            AutomationComponentType.KIRO_AGENT_HOOKS: ".kiro/hooks/",
            AutomationComponentType.CICD_PIPELINE: ".github/workflows/",
            AutomationComponentType.BUILD_AUTOMATION: ".",
            AutomationComponentType.MONITORING_AUTOMATION: "monitoring/"
        }
        return paths.get(component_type, ".")