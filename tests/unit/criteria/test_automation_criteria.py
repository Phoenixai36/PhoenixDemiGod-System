"""
Unit tests for Automation Criteria module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.phoenix_system_review.criteria.automation_criteria import (
    AutomationCriteriaEvaluator,
    AutomationComponentType,
    VSCodeTaskCriteria,
    DeploymentScriptCriteria,
    KiroAgentHooksCriteria,
    CICDPipelineCriteria
)
from src.phoenix_system_review.models.data_models import ComponentCategory, CriterionType


class TestAutomationCriteriaEvaluator:
    """Test automation criteria evaluator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.project_root = "/test/project"
        self.evaluator = AutomationCriteriaEvaluator(self.project_root)
    
    def test_initialization(self):
        """Test evaluator initialization"""
        assert self.evaluator.project_root == Path(self.project_root)
        assert isinstance(self.evaluator.vscode_criteria, VSCodeTaskCriteria)
        assert isinstance(self.evaluator.deployment_criteria, DeploymentScriptCriteria)
        assert isinstance(self.evaluator.hooks_criteria, KiroAgentHooksCriteria)
        assert isinstance(self.evaluator.cicd_criteria, CICDPipelineCriteria)
    
    def test_get_vscode_task_criteria(self):
        """Test VS Code task criteria generation"""
        criteria = self.evaluator.get_automation_criteria(AutomationComponentType.VSCODE_TASKS)
        
        assert len(criteria) > 0
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria]
        assert "vscode_tasks_config_exists" in criterion_ids
        assert "vscode_tasks_configuration_quality" in criterion_ids
        assert "vscode_kiro_integration" in criterion_ids
        
        # Check for required tasks
        required_task_criteria = [c for c in criteria if "vscode_task_" in c.id and c.id != "vscode_tasks_config_exists"]
        assert len(required_task_criteria) >= 8  # Should have criteria for all required tasks
        
        # Check critical criteria
        critical_criteria = [c for c in criteria if c.is_critical]
        assert len(critical_criteria) >= 1  # At least config existence should be critical
    
    def test_get_deployment_script_criteria(self):
        """Test deployment script criteria generation"""
        criteria = self.evaluator.get_automation_criteria(AutomationComponentType.DEPLOYMENT_SCRIPTS)
        
        assert len(criteria) > 0
        
        # Check for platform-specific scripts
        criterion_ids = [c.id for c in criteria]
        assert any("windows" in cid for cid in criterion_ids)
        assert any("linux" in cid for cid in criterion_ids)
        
        # Check for quality requirements
        quality_criteria = [c for c in criteria if c.criterion_type == CriterionType.QUALITY]
        assert len(quality_criteria) >= 5  # Should have all quality requirements
        
        # Check for critical scripts
        critical_criteria = [c for c in criteria if c.is_critical]
        assert len(critical_criteria) >= 2  # Complete deployment scripts should be critical
    
    def test_get_kiro_hooks_criteria(self):
        """Test Kiro agent hooks criteria generation"""
        criteria = self.evaluator.get_automation_criteria(AutomationComponentType.KIRO_AGENT_HOOKS)
        
        assert len(criteria) > 0
        
        # Check for required hook types
        criterion_ids = [c.id for c in criteria]
        assert "kiro_hooks_config_exists" in criterion_ids
        assert "kiro_hook_code_quality" in criterion_ids
        assert "kiro_hook_infrastructure" in criterion_ids
        assert "kiro_hook_revenue_tracking" in criterion_ids
        
        # Check for event system integration
        assert "kiro_hooks_event_system" in criterion_ids
        
        # Check critical hooks
        critical_criteria = [c for c in criteria if c.is_critical]
        assert len(critical_criteria) >= 3  # Config, code quality, infrastructure, revenue should be critical
    
    def test_get_cicd_pipeline_criteria(self):
        """Test CI/CD pipeline criteria generation"""
        criteria = self.evaluator.get_automation_criteria(AutomationComponentType.CICD_PIPELINE)
        
        assert len(criteria) > 0
        
        # Check for pipeline configuration
        criterion_ids = [c.id for c in criteria]
        assert "cicd_pipeline_config_exists" in criterion_ids
        
        # Check for pipeline stages
        stage_criteria = [c for c in criteria if "cicd_stage_" in c.id]
        assert len(stage_criteria) >= 7  # Should have all required stages
        
        # Check for deployment environments
        env_criteria = [c for c in criteria if "cicd_deployment_" in c.id]
        assert len(env_criteria) >= 3  # Should have all environments
        
        # Check critical criteria
        critical_criteria = [c for c in criteria if c.is_critical]
        assert len(critical_criteria) >= 4  # Config, key stages, and production deployment
    
    def test_get_build_automation_criteria(self):
        """Test build automation criteria generation"""
        criteria = self.evaluator.get_automation_criteria(AutomationComponentType.BUILD_AUTOMATION)
        
        assert len(criteria) > 0
        
        # Check for build configuration files
        criterion_ids = [c.id for c in criteria]
        assert "build_config_pyproject_toml" in criterion_ids
        assert "build_config_dockerfile" in criterion_ids
        
        # Check for build features
        feature_criteria = [c for c in criteria if "build_automation_" in c.id]
        assert len(feature_criteria) >= 4  # Should have all build features
        
        # Check critical criteria
        critical_criteria = [c for c in criteria if c.is_critical]
        assert len(critical_criteria) >= 2  # Python config and Docker should be critical
    
    def test_get_monitoring_automation_criteria(self):
        """Test monitoring automation criteria generation"""
        criteria = self.evaluator.get_automation_criteria(AutomationComponentType.MONITORING_AUTOMATION)
        
        assert len(criteria) > 0
        
        # Check for monitoring configurations
        criterion_ids = [c.id for c in criteria]
        assert any("prometheus" in cid for cid in criterion_ids)
        assert any("grafana" in cid for cid in criterion_ids)
        
        # Check for monitoring features
        feature_criteria = [c for c in criteria if "monitoring_automation_" in c.id]
        assert len(feature_criteria) >= 4  # Should have all monitoring features
        
        # Check critical criteria
        critical_criteria = [c for c in criteria if c.is_critical]
        assert len(critical_criteria) >= 2  # Prometheus and health checks should be critical
    
    def test_get_all_automation_criteria(self):
        """Test getting all automation criteria"""
        all_criteria = self.evaluator.get_all_automation_criteria()
        
        assert len(all_criteria) == len(AutomationComponentType)
        
        for component_type in AutomationComponentType:
            assert component_type.value in all_criteria
            assert len(all_criteria[component_type.value]) > 0
    
    def test_create_automation_components(self):
        """Test creating automation components"""
        components = self.evaluator.create_automation_components()
        
        assert len(components) == len(AutomationComponentType)
        
        for component in components:
            assert component.category == ComponentCategory.AUTOMATION
            assert len(component.criteria) > 0
            assert component.name
            assert component.description
            assert component.path


class TestAutomationCriteriaDataClasses:
    """Test automation criteria data classes"""
    
    def test_vscode_task_criteria(self):
        """Test VS Code task criteria data class"""
        criteria = VSCodeTaskCriteria()
        
        assert len(criteria.required_tasks) >= 8
        assert "Deploy Phoenix Badges" in criteria.required_tasks
        assert "Start Phoenix Hydra (Podman)" in criteria.required_tasks
        assert "Phoenix Health Check" in criteria.required_tasks
        
        assert "version" in criteria.task_configuration_requirements
        assert "tasks" in criteria.task_configuration_requirements
        
        assert len(criteria.integration_requirements) >= 4
    
    def test_deployment_script_criteria(self):
        """Test deployment script criteria data class"""
        criteria = DeploymentScriptCriteria()
        
        assert "windows" in criteria.required_scripts
        assert "linux" in criteria.required_scripts
        assert len(criteria.required_scripts["windows"]) >= 4
        assert len(criteria.required_scripts["linux"]) >= 4
        
        assert criteria.script_requirements["error_handling"] is True
        assert criteria.script_requirements["logging"] is True
        assert criteria.script_requirements["rollback_capability"] is True
        
        assert len(criteria.deployment_stages) >= 5
    
    def test_kiro_agent_hooks_criteria(self):
        """Test Kiro agent hooks criteria data class"""
        criteria = KiroAgentHooksCriteria()
        
        assert len(criteria.required_hooks) >= 5
        assert any("Code quality" in hook for hook in criteria.required_hooks)
        assert any("Revenue tracking" in hook for hook in criteria.required_hooks)
        
        assert "event_sources" in criteria.hook_configuration
        assert "file_watcher" in criteria.hook_configuration["event_sources"]
        assert criteria.hook_configuration["error_handling"] is True
        
        assert len(criteria.integration_points) >= 4
    
    def test_cicd_pipeline_criteria(self):
        """Test CI/CD pipeline criteria data class"""
        criteria = CICDPipelineCriteria()
        
        assert len(criteria.pipeline_stages) >= 7
        assert "Unit testing" in criteria.pipeline_stages
        assert "Deployment automation" in criteria.pipeline_stages
        
        assert len(criteria.required_integrations) >= 5
        assert "Git repository integration" in criteria.required_integrations
        
        assert len(criteria.deployment_environments) >= 3
        assert "Production" in criteria.deployment_environments


if __name__ == "__main__":
    pytest.main([__file__])