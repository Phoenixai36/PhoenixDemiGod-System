"""
Unit tests for Automation Criteria

Tests the automation evaluation criteria for Phoenix Hydra components
including VS Code integration, deployment scripts, and Kiro agent hooks.
"""

import pytest
from src.phoenix_system_review.criteria.automation_criteria import (
    AutomationCriteria, AutomationComponent, CriterionDefinition, ComponentCriteria
)


class TestAutomationCriteria:
    """Test cases for AutomationCriteria class"""
    
    @pytest.fixture
    def automation_criteria(self):
        """Create AutomationCriteria instance for testing"""
        return AutomationCriteria()
    
    def test_initialization(self, automation_criteria):
        """Test automation criteria initialization"""
        assert automation_criteria is not None
        all_criteria = automation_criteria.get_all_criteria()
        assert len(all_criteria) > 0
        
        # Check that all expected component types are present
        expected_components = [
            AutomationComponent.VSCODE_INTEGRATION,
            AutomationComponent.DEPLOYMENT_SCRIPTS,
            AutomationComponent.KIRO_AGENT_HOOKS,
            AutomationComponent.CICD_PIPELINE,
            AutomationComponent.BUILD_AUTOMATION,
            AutomationComponent.TESTING_AUTOMATION,
            AutomationComponent.MONITORING_AUTOMATION
        ]
        
        for component in expected_components:
            assert component in all_criteria
    
    def test_vscode_integration_criteria(self, automation_criteria):
        """Test VS Code integration criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.VSCODE_INTEGRATION)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.VSCODE_INTEGRATION
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "vscode_tasks_configuration" in criterion_ids
        assert "vscode_settings_validation" in criterion_ids
        
        # Check critical criteria
        assert "vscode_tasks_configuration" in criteria.critical_criteria
        assert "vscode_settings_validation" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_deployment_scripts_criteria(self, automation_criteria):
        """Test deployment scripts criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.DEPLOYMENT_SCRIPTS)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.DEPLOYMENT_SCRIPTS
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.75
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "deployment_powershell_scripts" in criterion_ids
        assert "deployment_bash_scripts" in criterion_ids
        assert "deployment_automation_scripts" in criterion_ids
        
        # Check critical criteria
        assert "deployment_powershell_scripts" in criteria.critical_criteria
        assert "deployment_bash_scripts" in criteria.critical_criteria
        assert "deployment_automation_scripts" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_kiro_agent_hooks_criteria(self, automation_criteria):
        """Test Kiro agent hooks criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.KIRO_AGENT_HOOKS)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.KIRO_AGENT_HOOKS
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "kiro_hooks_file_watchers" in criterion_ids
        assert "kiro_hooks_container_events" in criterion_ids
        assert "kiro_hooks_automation_triggers" in criterion_ids
        
        # Check critical criteria
        assert "kiro_hooks_file_watchers" in criteria.critical_criteria
        assert "kiro_hooks_container_events" in criteria.critical_criteria
        assert "kiro_hooks_automation_triggers" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_cicd_pipeline_criteria(self, automation_criteria):
        """Test CI/CD pipeline criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.CICD_PIPELINE)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.CICD_PIPELINE
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.5
        
        # Check for criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "cicd_pipeline_configuration" in criterion_ids
        assert "cicd_automated_testing" in criterion_ids
        assert "cicd_build_automation" in criterion_ids
        
        # CI/CD is optional, so no critical criteria
        assert len(criteria.critical_criteria) == 0
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_build_automation_criteria(self, automation_criteria):
        """Test build automation criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.BUILD_AUTOMATION)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.BUILD_AUTOMATION
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.6
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "build_python_packaging" in criterion_ids
        assert "build_container_images" in criterion_ids
        
        # Check critical criteria
        assert "build_python_packaging" in criteria.critical_criteria
        assert "build_container_images" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_testing_automation_criteria(self, automation_criteria):
        """Test testing automation criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.TESTING_AUTOMATION)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.TESTING_AUTOMATION
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.75
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "testing_unit_automation" in criterion_ids
        assert "testing_integration_automation" in criterion_ids
        assert "testing_code_quality_automation" in criterion_ids
        
        # Check critical criteria
        assert "testing_unit_automation" in criteria.critical_criteria
        assert "testing_integration_automation" in criteria.critical_criteria
        assert "testing_code_quality_automation" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_monitoring_automation_criteria(self, automation_criteria):
        """Test monitoring automation criteria definition"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.MONITORING_AUTOMATION)
        
        assert criteria is not None
        assert criteria.component_type == AutomationComponent.MONITORING_AUTOMATION
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.6
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "monitoring_health_checks" in criterion_ids
        
        # Check critical criteria
        assert "monitoring_health_checks" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_get_criterion_by_id(self, automation_criteria):
        """Test getting specific criterion by ID"""
        # Test existing criterion
        criterion = automation_criteria.get_criterion_by_id(
            AutomationComponent.VSCODE_INTEGRATION, 
            "vscode_tasks_configuration"
        )
        
        assert criterion is not None
        assert criterion.id == "vscode_tasks_configuration"
        assert criterion.name == "VS Code Tasks Configuration"
        assert criterion.required is True
        
        # Test non-existent criterion
        criterion = automation_criteria.get_criterion_by_id(
            AutomationComponent.VSCODE_INTEGRATION,
            "non_existent_criterion"
        )
        assert criterion is None
        
        # Test non-existent component
        criterion = automation_criteria.get_criterion_by_id(
            None,
            "vscode_tasks_configuration"
        )
        assert criterion is None
    
    def test_get_critical_criteria(self, automation_criteria):
        """Test getting critical criteria for components"""
        # Test VS Code integration critical criteria
        critical = automation_criteria.get_critical_criteria(AutomationComponent.VSCODE_INTEGRATION)
        
        assert len(critical) > 0
        critical_ids = [c.id for c in critical]
        assert "vscode_tasks_configuration" in critical_ids
        assert "vscode_settings_validation" in critical_ids
        
        # Test component with no critical criteria
        critical = automation_criteria.get_critical_criteria(AutomationComponent.CICD_PIPELINE)
        assert len(critical) == 0
        
        # Test non-existent component
        critical = automation_criteria.get_critical_criteria(None)
        assert len(critical) == 0
    
    def test_calculate_component_score(self, automation_criteria):
        """Test component score calculation"""
        # Test perfect score
        evaluation_results = {
            "vscode_tasks_configuration": True,
            "vscode_settings_validation": True,
            "vscode_launch_configuration": True,
            "vscode_extensions_recommendations": True,
            "vscode_snippets": True,
            "vscode_workspace_configuration": True
        }
        
        score = automation_criteria.calculate_component_score(
            AutomationComponent.VSCODE_INTEGRATION,
            evaluation_results
        )
        assert score == 1.0
        
        # Test partial score
        evaluation_results = {
            "vscode_tasks_configuration": True,
            "vscode_settings_validation": True,
            "vscode_launch_configuration": False,
            "vscode_extensions_recommendations": False,
            "vscode_snippets": False,
            "vscode_workspace_configuration": False
        }
        
        score = automation_criteria.calculate_component_score(
            AutomationComponent.VSCODE_INTEGRATION,
            evaluation_results
        )
        assert 0.0 < score < 1.0
        
        # Test zero score
        evaluation_results = {
            "vscode_tasks_configuration": False,
            "vscode_settings_validation": False,
            "vscode_launch_configuration": False,
            "vscode_extensions_recommendations": False,
            "vscode_snippets": False,
            "vscode_workspace_configuration": False
        }
        
        score = automation_criteria.calculate_component_score(
            AutomationComponent.VSCODE_INTEGRATION,
            evaluation_results
        )
        assert score == 0.0
        
        # Test non-existent component
        score = automation_criteria.calculate_component_score(
            None,
            evaluation_results
        )
        assert score == 0.0
    
    def test_validate_criteria_completeness(self, automation_criteria):
        """Test criteria validation"""
        issues = automation_criteria.validate_criteria_completeness()
        
        # Should have no issues with properly defined criteria
        assert isinstance(issues, dict)
        
        # If there are issues, they should be properly formatted
        for component_type, component_issues in issues.items():
            assert isinstance(component_type, str)
            assert isinstance(component_issues, list)
            for issue in component_issues:
                assert isinstance(issue, str)
    
    def test_criterion_definition_properties(self, automation_criteria):
        """Test CriterionDefinition properties"""
        criteria = automation_criteria.get_criteria_for_component(AutomationComponent.VSCODE_INTEGRATION)
        
        for criterion in criteria.criteria:
            # Check required properties
            assert isinstance(criterion.id, str)
            assert len(criterion.id) > 0
            assert isinstance(criterion.name, str)
            assert len(criterion.name) > 0
            assert isinstance(criterion.description, str)
            assert len(criterion.description) > 0
            assert isinstance(criterion.category, str)
            assert isinstance(criterion.weight, float)
            assert 0.0 < criterion.weight <= 1.0
            assert isinstance(criterion.required, bool)
            
            # Check optional properties
            if criterion.validation_method:
                assert isinstance(criterion.validation_method, str)
            if criterion.expected_values:
                assert isinstance(criterion.expected_values, (list, dict))
            if criterion.error_message:
                assert isinstance(criterion.error_message, str)
    
    def test_component_criteria_properties(self, automation_criteria):
        """Test ComponentCriteria properties"""
        all_criteria = automation_criteria.get_all_criteria()
        
        for component_type, criteria in all_criteria.items():
            assert isinstance(criteria.component_type, AutomationComponent)
            assert isinstance(criteria.criteria, list)
            assert len(criteria.criteria) > 0
            assert isinstance(criteria.minimum_score, float)
            assert 0.0 <= criteria.minimum_score <= 1.0
            assert isinstance(criteria.critical_criteria, list)
            
            # Check that critical criteria exist in the criteria list
            criterion_ids = [c.id for c in criteria.criteria]
            for critical_id in criteria.critical_criteria:
                assert critical_id in criterion_ids
    
    def test_all_components_have_criteria(self, automation_criteria):
        """Test that all automation components have criteria defined"""
        all_criteria = automation_criteria.get_all_criteria()
        
        # Check that we have criteria for all expected components
        expected_components = [
            AutomationComponent.VSCODE_INTEGRATION,
            AutomationComponent.DEPLOYMENT_SCRIPTS,
            AutomationComponent.KIRO_AGENT_HOOKS,
            AutomationComponent.CICD_PIPELINE,
            AutomationComponent.BUILD_AUTOMATION,
            AutomationComponent.TESTING_AUTOMATION,
            AutomationComponent.MONITORING_AUTOMATION
        ]
        
        for component in expected_components:
            assert component in all_criteria
            criteria = all_criteria[component]
            assert len(criteria.criteria) > 0
    
    def test_criteria_categories(self, automation_criteria):
        """Test that criteria have appropriate categories"""
        all_criteria = automation_criteria.get_all_criteria()
        
        expected_categories = {
            "ide_integration", "ide_configuration", "debugging", "development_environment",
            "productivity", "workspace_management", "windows_deployment", "unix_deployment",
            "automation", "reliability", "configuration", "disaster_recovery",
            "file_monitoring", "container_monitoring", "automation_triggers",
            "event_coordination", "performance", "pipeline_setup", "testing_integration",
            "build_processes", "deployment_automation", "security", "monitoring",
            "python_build", "containerization", "dependency_management",
            "artifact_management", "quality_assurance", "unit_testing",
            "integration_testing", "code_quality", "performance_testing",
            "security_testing", "health_monitoring", "log_management",
            "metrics_monitoring", "alerting", "visualization"
        }
        
        found_categories = set()
        for criteria in all_criteria.values():
            for criterion in criteria.criteria:
                found_categories.add(criterion.category)
        
        # All found categories should be in expected categories
        assert found_categories.issubset(expected_categories)
        
        # Should have at least some core categories
        core_categories = {"automation", "reliability", "configuration", "monitoring"}
        assert core_categories.issubset(found_categories)
    
    def test_automation_specific_criteria(self, automation_criteria):
        """Test automation-specific criteria features"""
        # Test VS Code integration has tasks configuration
        vscode_criteria = automation_criteria.get_criteria_for_component(AutomationComponent.VSCODE_INTEGRATION)
        criterion_ids = [c.id for c in vscode_criteria.criteria]
        assert "vscode_tasks_configuration" in criterion_ids
        
        # Test deployment scripts have both PowerShell and Bash
        deployment_criteria = automation_criteria.get_criteria_for_component(AutomationComponent.DEPLOYMENT_SCRIPTS)
        criterion_ids = [c.id for c in deployment_criteria.criteria]
        assert "deployment_powershell_scripts" in criterion_ids
        assert "deployment_bash_scripts" in criterion_ids
        
        # Test Kiro agent hooks have file watchers
        hooks_criteria = automation_criteria.get_criteria_for_component(AutomationComponent.KIRO_AGENT_HOOKS)
        criterion_ids = [c.id for c in hooks_criteria.criteria]
        assert "kiro_hooks_file_watchers" in criterion_ids
        
        # Test testing automation has unit tests
        testing_criteria = automation_criteria.get_criteria_for_component(AutomationComponent.TESTING_AUTOMATION)
        criterion_ids = [c.id for c in testing_criteria.criteria]
        assert "testing_unit_automation" in criterion_ids
    
    def test_minimum_scores_appropriate(self, automation_criteria):
        """Test that minimum scores are appropriate for each component"""
        all_criteria = automation_criteria.get_all_criteria()
        
        # Critical components should have higher minimum scores
        critical_components = [
            AutomationComponent.DEPLOYMENT_SCRIPTS,
            AutomationComponent.TESTING_AUTOMATION
        ]
        
        for component in critical_components:
            criteria = all_criteria[component]
            assert criteria.minimum_score >= 0.75
        
        # Optional components can have lower minimum scores
        optional_components = [
            AutomationComponent.CICD_PIPELINE
        ]
        
        for component in optional_components:
            criteria = all_criteria[component]
            assert criteria.minimum_score <= 0.6
    
    def test_required_vs_optional_criteria(self, automation_criteria):
        """Test that required and optional criteria are properly balanced"""
        all_criteria = automation_criteria.get_all_criteria()
        
        for component_type, criteria in all_criteria.items():
            required_count = sum(1 for c in criteria.criteria if c.required)
            optional_count = sum(1 for c in criteria.criteria if not c.required)
            
            # Should have at least some required criteria for most components
            if component_type != AutomationComponent.CICD_PIPELINE:  # CI/CD is fully optional
                assert required_count > 0
            
            # Should have a reasonable balance
            total_count = len(criteria.criteria)
            assert total_count > 0
            
            # At least 30% should be required for critical components
            if component_type in [AutomationComponent.DEPLOYMENT_SCRIPTS, AutomationComponent.TESTING_AUTOMATION]:
                assert required_count / total_count >= 0.3


if __name__ == "__main__":
    pytest.main([__file__])