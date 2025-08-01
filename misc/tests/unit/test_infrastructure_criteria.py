"""
Unit tests for Infrastructure Criteria
"""

import pytest
from src.phoenix_system_review.criteria.infrastructure_criteria import (
    InfrastructureCriteria, InfrastructureComponent, CriterionDefinition, ComponentCriteria
)


class TestInfrastructureCriteria:
    """Test cases for InfrastructureCriteria class"""
    
    @pytest.fixture
    def infrastructure_criteria(self):
        """Create InfrastructureCriteria instance for testing"""
        return InfrastructureCriteria()
    
    def test_initialization(self, infrastructure_criteria):
        """Test infrastructure criteria initialization"""
        assert infrastructure_criteria is not None
        all_criteria = infrastructure_criteria.get_all_criteria()
        assert len(all_criteria) > 0
        
        # Check that all expected component types are present
        expected_components = [
            InfrastructureComponent.NCA_TOOLKIT,
            InfrastructureComponent.PODMAN_STACK,
            InfrastructureComponent.DATABASE,
            InfrastructureComponent.MINIO_STORAGE,
            InfrastructureComponent.PROMETHEUS,
            InfrastructureComponent.GRAFANA,
            InfrastructureComponent.NETWORKING
        ]
        
        for component in expected_components:
            assert component in all_criteria
    
    def test_nca_toolkit_criteria(self, infrastructure_criteria):
        """Test NCA Toolkit criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.NCA_TOOLKIT)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.NCA_TOOLKIT
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.8
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "nca_api_endpoints" in criterion_ids
        assert "nca_health_check" in criterion_ids
        assert "nca_multimedia_support" in criterion_ids
        
        # Check critical criteria
        assert "nca_api_endpoints" in criteria.critical_criteria
        assert "nca_health_check" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_podman_stack_criteria(self, infrastructure_criteria):
        """Test Podman stack criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.PODMAN_STACK)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.PODMAN_STACK
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.75
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "podman_compose_file" in criterion_ids
        assert "podman_service_definitions" in criterion_ids
        assert "podman_health_checks" in criterion_ids
        assert "podman_networking" in criterion_ids
        
        # Check critical criteria
        assert "podman_compose_file" in criteria.critical_criteria
        assert "podman_service_definitions" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_database_criteria(self, infrastructure_criteria):
        """Test database criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.DATABASE)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.DATABASE
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "db_schema_present" in criterion_ids
        assert "db_connection_config" in criterion_ids
        assert "db_security" in criterion_ids
        
        # Check critical criteria
        assert "db_schema_present" in criteria.critical_criteria
        assert "db_connection_config" in criteria.critical_criteria
        assert "db_security" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_minio_storage_criteria(self, infrastructure_criteria):
        """Test Minio storage criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.MINIO_STORAGE)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.MINIO_STORAGE
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "minio_configuration" in criterion_ids
        assert "minio_buckets" in criterion_ids
        assert "minio_access_policies" in criterion_ids
        
        # Check critical criteria
        assert "minio_configuration" in criteria.critical_criteria
        assert "minio_buckets" in criteria.critical_criteria
        assert "minio_access_policies" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_prometheus_criteria(self, infrastructure_criteria):
        """Test Prometheus criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.PROMETHEUS)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.PROMETHEUS
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.6
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "prometheus_config" in criterion_ids
        assert "prometheus_targets" in criterion_ids
        
        # Check critical criteria
        assert "prometheus_config" in criteria.critical_criteria
        assert "prometheus_targets" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_grafana_criteria(self, infrastructure_criteria):
        """Test Grafana criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.GRAFANA)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.GRAFANA
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.6
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "grafana_config" in criterion_ids
        assert "grafana_dashboards" in criterion_ids
        
        # Check critical criteria
        assert "grafana_config" in criteria.critical_criteria
        assert "grafana_dashboards" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_networking_criteria(self, infrastructure_criteria):
        """Test networking criteria definition"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.NETWORKING)
        
        assert criteria is not None
        assert criteria.component_type == InfrastructureComponent.NETWORKING
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.6
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "network_topology" in criterion_ids
        assert "port_management" in criterion_ids
        
        # Check critical criteria
        assert "network_topology" in criteria.critical_criteria
        assert "port_management" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_get_criterion_by_id(self, infrastructure_criteria):
        """Test getting specific criterion by ID"""
        # Test existing criterion
        criterion = infrastructure_criteria.get_criterion_by_id(
            InfrastructureComponent.NCA_TOOLKIT, 
            "nca_api_endpoints"
        )
        
        assert criterion is not None
        assert criterion.id == "nca_api_endpoints"
        assert criterion.name == "API Endpoints Available"
        assert criterion.required is True
        
        # Test non-existent criterion
        criterion = infrastructure_criteria.get_criterion_by_id(
            InfrastructureComponent.NCA_TOOLKIT,
            "non_existent_criterion"
        )
        assert criterion is None
        
        # Test non-existent component
        criterion = infrastructure_criteria.get_criterion_by_id(
            None,
            "nca_api_endpoints"
        )
        assert criterion is None
    
    def test_get_critical_criteria(self, infrastructure_criteria):
        """Test getting critical criteria for components"""
        # Test NCA Toolkit critical criteria
        critical = infrastructure_criteria.get_critical_criteria(InfrastructureComponent.NCA_TOOLKIT)
        
        assert len(critical) > 0
        critical_ids = [c.id for c in critical]
        assert "nca_api_endpoints" in critical_ids
        assert "nca_health_check" in critical_ids
        
        # Test component with no critical criteria
        critical = infrastructure_criteria.get_critical_criteria(None)
        assert len(critical) == 0
    
    def test_calculate_component_score(self, infrastructure_criteria):
        """Test component score calculation"""
        # Test perfect score
        evaluation_results = {
            "nca_api_endpoints": True,
            "nca_health_check": True,
            "nca_multimedia_support": True,
            "nca_performance": True,
            "nca_documentation": True,
            "nca_error_handling": True
        }
        
        score = infrastructure_criteria.calculate_component_score(
            InfrastructureComponent.NCA_TOOLKIT,
            evaluation_results
        )
        assert score == 1.0
        
        # Test partial score
        evaluation_results = {
            "nca_api_endpoints": True,
            "nca_health_check": True,
            "nca_multimedia_support": False,
            "nca_performance": False,
            "nca_documentation": False,
            "nca_error_handling": True
        }
        
        score = infrastructure_criteria.calculate_component_score(
            InfrastructureComponent.NCA_TOOLKIT,
            evaluation_results
        )
        assert 0.0 < score < 1.0
        
        # Test zero score
        evaluation_results = {
            "nca_api_endpoints": False,
            "nca_health_check": False,
            "nca_multimedia_support": False,
            "nca_performance": False,
            "nca_documentation": False,
            "nca_error_handling": False
        }
        
        score = infrastructure_criteria.calculate_component_score(
            InfrastructureComponent.NCA_TOOLKIT,
            evaluation_results
        )
        assert score == 0.0
        
        # Test non-existent component
        score = infrastructure_criteria.calculate_component_score(
            None,
            evaluation_results
        )
        assert score == 0.0
    
    def test_validate_criteria_completeness(self, infrastructure_criteria):
        """Test criteria validation"""
        issues = infrastructure_criteria.validate_criteria_completeness()
        
        # Should have no issues with properly defined criteria
        assert isinstance(issues, dict)
        
        # If there are issues, they should be properly formatted
        for component_type, component_issues in issues.items():
            assert isinstance(component_type, str)
            assert isinstance(component_issues, list)
            for issue in component_issues:
                assert isinstance(issue, str)
    
    def test_criterion_definition_properties(self, infrastructure_criteria):
        """Test CriterionDefinition properties"""
        criteria = infrastructure_criteria.get_criteria_for_component(InfrastructureComponent.NCA_TOOLKIT)
        
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
    
    def test_component_criteria_properties(self, infrastructure_criteria):
        """Test ComponentCriteria properties"""
        all_criteria = infrastructure_criteria.get_all_criteria()
        
        for component_type, criteria in all_criteria.items():
            assert isinstance(criteria.component_type, InfrastructureComponent)
            assert isinstance(criteria.criteria, list)
            assert len(criteria.criteria) > 0
            assert isinstance(criteria.minimum_score, float)
            assert 0.0 <= criteria.minimum_score <= 1.0
            assert isinstance(criteria.critical_criteria, list)
            
            # Check that critical criteria exist in the criteria list
            criterion_ids = [c.id for c in criteria.criteria]
            for critical_id in criteria.critical_criteria:
                assert critical_id in criterion_ids
    
    def test_all_components_have_criteria(self, infrastructure_criteria):
        """Test that all infrastructure components have criteria defined"""
        all_criteria = infrastructure_criteria.get_all_criteria()
        
        # Check that we have criteria for all expected components
        expected_components = [
            InfrastructureComponent.NCA_TOOLKIT,
            InfrastructureComponent.PODMAN_STACK,
            InfrastructureComponent.DATABASE,
            InfrastructureComponent.MINIO_STORAGE,
            InfrastructureComponent.PROMETHEUS,
            InfrastructureComponent.GRAFANA,
            InfrastructureComponent.NETWORKING
        ]
        
        for component in expected_components:
            assert component in all_criteria
            criteria = all_criteria[component]
            assert len(criteria.criteria) > 0
    
    def test_criteria_categories(self, infrastructure_criteria):
        """Test that criteria have appropriate categories"""
        all_criteria = infrastructure_criteria.get_all_criteria()
        
        expected_categories = {
            "functionality", "health", "performance", "documentation", 
            "reliability", "configuration", "monitoring", "networking",
            "storage", "security", "schema", "alerting", "visualization",
            "scalability"
        }
        
        found_categories = set()
        for criteria in all_criteria.values():
            for criterion in criteria.criteria:
                found_categories.add(criterion.category)
        
        # All found categories should be in expected categories
        assert found_categories.issubset(expected_categories)
        
        # Should have at least some core categories
        core_categories = {"functionality", "configuration", "security", "monitoring"}
        assert core_categories.issubset(found_categories)


if __name__ == "__main__":
    pytest.main([__file__])