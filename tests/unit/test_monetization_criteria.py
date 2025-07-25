"""
Unit tests for Monetization Criteria
"""

import pytest
from src.phoenix_system_review.criteria.monetization_criteria import (
    MonetizationCriteria, MonetizationComponent
)
from src.phoenix_system_review.criteria.infrastructure_criteria import CriterionDefinition, ComponentCriteria


class TestMonetizationCriteria:
    """Test cases for MonetizationCriteria class"""
    
    @pytest.fixture
    def monetization_criteria(self):
        """Create MonetizationCriteria instance for testing"""
        return MonetizationCriteria()
    
    def test_initialization(self, monetization_criteria):
        """Test monetization criteria initialization"""
        assert monetization_criteria is not None
        all_criteria = monetization_criteria.get_all_criteria()
        assert len(all_criteria) > 0
        
        # Check that all expected component types are present
        expected_components = [
            MonetizationComponent.AFFILIATE_PROGRAMS,
            MonetizationComponent.GRANT_APPLICATIONS,
            MonetizationComponent.MARKETPLACE_READINESS,
            MonetizationComponent.REVENUE_TRACKING,
            MonetizationComponent.BUSINESS_INTELLIGENCE,
            MonetizationComponent.COMPLIANCE
        ]
        
        for component in expected_components:
            assert component in all_criteria
    
    def test_affiliate_programs_criteria(self, monetization_criteria):
        """Test affiliate programs criteria definition"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.AFFILIATE_PROGRAMS)
        
        assert criteria is not None
        assert criteria.component_type == MonetizationComponent.AFFILIATE_PROGRAMS
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.75
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "affiliate_digitalocean_setup" in criterion_ids
        assert "affiliate_badge_deployment" in criterion_ids
        assert "affiliate_tracking_scripts" in criterion_ids
        
        # Check critical criteria
        assert "affiliate_digitalocean_setup" in criteria.critical_criteria
        assert "affiliate_badge_deployment" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_grant_applications_criteria(self, monetization_criteria):
        """Test grant applications criteria definition"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.GRANT_APPLICATIONS)
        
        assert criteria is not None
        assert criteria.component_type == MonetizationComponent.GRANT_APPLICATIONS
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "grant_neotec_generator" in criterion_ids
        assert "grant_enisa_documentation" in criterion_ids
        assert "grant_eic_accelerator_prep" in criterion_ids
        
        # Check critical criteria
        assert "grant_neotec_generator" in criteria.critical_criteria
        assert "grant_enisa_documentation" in criteria.critical_criteria
        assert "grant_eic_accelerator_prep" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_marketplace_readiness_criteria(self, monetization_criteria):
        """Test marketplace readiness criteria definition"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.MARKETPLACE_READINESS)
        
        assert criteria is not None
        assert criteria.component_type == MonetizationComponent.MARKETPLACE_READINESS
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.75
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "marketplace_aws_deployment" in criterion_ids
        assert "marketplace_cloudflare_workers" in criterion_ids
        assert "marketplace_huggingface_integration" in criterion_ids
        
        # Check critical criteria
        assert "marketplace_aws_deployment" in criteria.critical_criteria
        assert "marketplace_cloudflare_workers" in criteria.critical_criteria
        assert "marketplace_huggingface_integration" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_revenue_tracking_criteria(self, monetization_criteria):
        """Test revenue tracking criteria definition"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.REVENUE_TRACKING)
        
        assert criteria is not None
        assert criteria.component_type == MonetizationComponent.REVENUE_TRACKING
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "revenue_tracking_automation" in criterion_ids
        assert "revenue_metrics_collection" in criterion_ids
        assert "revenue_dashboard" in criterion_ids
        
        # Check critical criteria
        assert "revenue_tracking_automation" in criteria.critical_criteria
        assert "revenue_metrics_collection" in criteria.critical_criteria
        assert "revenue_dashboard" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_business_intelligence_criteria(self, monetization_criteria):
        """Test business intelligence criteria definition"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.BUSINESS_INTELLIGENCE)
        
        assert criteria is not None
        assert criteria.component_type == MonetizationComponent.BUSINESS_INTELLIGENCE
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.65
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "bi_kpi_definition" in criterion_ids
        assert "bi_success_metrics" in criterion_ids
        assert "bi_performance_monitoring" in criterion_ids
        
        # Check critical criteria
        assert "bi_kpi_definition" in criteria.critical_criteria
        assert "bi_success_metrics" in criteria.critical_criteria
        assert "bi_performance_monitoring" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_compliance_criteria(self, monetization_criteria):
        """Test compliance criteria definition"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.COMPLIANCE)
        
        assert criteria is not None
        assert criteria.component_type == MonetizationComponent.COMPLIANCE
        assert len(criteria.criteria) > 0
        assert criteria.minimum_score == 0.7
        
        # Check for required criteria
        criterion_ids = [c.id for c in criteria.criteria]
        assert "compliance_gdpr" in criterion_ids
        assert "compliance_financial_reporting" in criterion_ids
        assert "compliance_terms_conditions" in criterion_ids
        
        # Check critical criteria
        assert "compliance_gdpr" in criteria.critical_criteria
        assert "compliance_financial_reporting" in criteria.critical_criteria
        assert "compliance_terms_conditions" in criteria.critical_criteria
        
        # Verify weights sum to 1.0
        total_weight = sum(c.weight for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_get_criterion_by_id(self, monetization_criteria):
        """Test getting specific criterion by ID"""
        # Test existing criterion
        criterion = monetization_criteria.get_criterion_by_id(
            MonetizationComponent.AFFILIATE_PROGRAMS, 
            "affiliate_digitalocean_setup"
        )
        
        assert criterion is not None
        assert criterion.id == "affiliate_digitalocean_setup"
        assert criterion.name == "DigitalOcean Affiliate Setup"
        assert criterion.required is True
        
        # Test non-existent criterion
        criterion = monetization_criteria.get_criterion_by_id(
            MonetizationComponent.AFFILIATE_PROGRAMS,
            "non_existent_criterion"
        )
        assert criterion is None
        
        # Test non-existent component
        criterion = monetization_criteria.get_criterion_by_id(
            None,
            "affiliate_digitalocean_setup"
        )
        assert criterion is None
    
    def test_get_critical_criteria(self, monetization_criteria):
        """Test getting critical criteria for components"""
        # Test affiliate programs critical criteria
        critical = monetization_criteria.get_critical_criteria(MonetizationComponent.AFFILIATE_PROGRAMS)
        
        assert len(critical) > 0
        critical_ids = [c.id for c in critical]
        assert "affiliate_digitalocean_setup" in critical_ids
        assert "affiliate_badge_deployment" in critical_ids
        
        # Test component with no critical criteria
        critical = monetization_criteria.get_critical_criteria(None)
        assert len(critical) == 0
    
    def test_calculate_component_score(self, monetization_criteria):
        """Test component score calculation"""
        # Test perfect score for affiliate programs
        evaluation_results = {
            "affiliate_digitalocean_setup": True,
            "affiliate_customgpt_setup": True,
            "affiliate_cloudflare_setup": True,
            "affiliate_badge_deployment": True,
            "affiliate_tracking_scripts": True,
            "affiliate_revenue_reporting": True
        }
        
        score = monetization_criteria.calculate_component_score(
            MonetizationComponent.AFFILIATE_PROGRAMS,
            evaluation_results
        )
        assert score == 1.0
        
        # Test partial score
        evaluation_results = {
            "affiliate_digitalocean_setup": True,
            "affiliate_customgpt_setup": False,
            "affiliate_cloudflare_setup": False,
            "affiliate_badge_deployment": True,
            "affiliate_tracking_scripts": True,
            "affiliate_revenue_reporting": False
        }
        
        score = monetization_criteria.calculate_component_score(
            MonetizationComponent.AFFILIATE_PROGRAMS,
            evaluation_results
        )
        assert 0.0 < score < 1.0
        
        # Test zero score
        evaluation_results = {
            "affiliate_digitalocean_setup": False,
            "affiliate_customgpt_setup": False,
            "affiliate_cloudflare_setup": False,
            "affiliate_badge_deployment": False,
            "affiliate_tracking_scripts": False,
            "affiliate_revenue_reporting": False
        }
        
        score = monetization_criteria.calculate_component_score(
            MonetizationComponent.AFFILIATE_PROGRAMS,
            evaluation_results
        )
        assert score == 0.0
        
        # Test non-existent component
        score = monetization_criteria.calculate_component_score(
            None,
            evaluation_results
        )
        assert score == 0.0
    
    def test_get_revenue_target_criteria(self, monetization_criteria):
        """Test revenue target criteria"""
        revenue_criteria = monetization_criteria.get_revenue_target_criteria()
        
        assert isinstance(revenue_criteria, dict)
        assert revenue_criteria["target_amount"] == 400000.0
        assert revenue_criteria["currency"] == "EUR"
        assert revenue_criteria["timeframe"] == "2025"
        
        # Check revenue streams
        assert "revenue_streams" in revenue_criteria
        streams = revenue_criteria["revenue_streams"]
        assert "affiliate_programs" in streams
        assert "marketplace_sales" in streams
        assert "grant_funding" in streams
        assert "enterprise_services" in streams
        
        # Check milestones
        assert "milestones" in revenue_criteria
        milestones = revenue_criteria["milestones"]
        assert "q1_2025" in milestones
        assert "q2_2025" in milestones
        assert "q3_2025" in milestones
        assert "q4_2025" in milestones
        
        # Test custom target amount
        custom_criteria = monetization_criteria.get_revenue_target_criteria(500000.0)
        assert custom_criteria["target_amount"] == 500000.0
    
    def test_criterion_definition_properties(self, monetization_criteria):
        """Test CriterionDefinition properties"""
        criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.AFFILIATE_PROGRAMS)
        
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
    
    def test_component_criteria_properties(self, monetization_criteria):
        """Test ComponentCriteria properties"""
        all_criteria = monetization_criteria.get_all_criteria()
        
        for component_type, criteria in all_criteria.items():
            assert isinstance(criteria.component_type, MonetizationComponent)
            assert isinstance(criteria.criteria, list)
            assert len(criteria.criteria) > 0
            assert isinstance(criteria.minimum_score, float)
            assert 0.0 <= criteria.minimum_score <= 1.0
            assert isinstance(criteria.critical_criteria, list)
            
            # Check that critical criteria exist in the criteria list
            criterion_ids = [c.id for c in criteria.criteria]
            for critical_id in criteria.critical_criteria:
                assert critical_id in criterion_ids
    
    def test_all_components_have_criteria(self, monetization_criteria):
        """Test that all monetization components have criteria defined"""
        all_criteria = monetization_criteria.get_all_criteria()
        
        # Check that we have criteria for all expected components
        expected_components = [
            MonetizationComponent.AFFILIATE_PROGRAMS,
            MonetizationComponent.GRANT_APPLICATIONS,
            MonetizationComponent.MARKETPLACE_READINESS,
            MonetizationComponent.REVENUE_TRACKING,
            MonetizationComponent.BUSINESS_INTELLIGENCE,
            MonetizationComponent.COMPLIANCE
        ]
        
        for component in expected_components:
            assert component in all_criteria
            criteria = all_criteria[component]
            assert len(criteria.criteria) > 0
    
    def test_criteria_categories(self, monetization_criteria):
        """Test that criteria have appropriate categories"""
        all_criteria = monetization_criteria.get_all_criteria()
        
        expected_categories = {
            "affiliate_setup", "automation", "tracking", "reporting",
            "grant_automation", "documentation", "grant_preparation", 
            "compliance", "financial_planning", "marketplace_deployment",
            "ai_marketplace", "enterprise_features", "pricing", 
            "customer_support", "data_collection", "visualization",
            "analytics", "monitoring", "integration", "kpi_management",
            "metrics_framework", "market_analysis", "financial_analysis",
            "data_protection", "financial_compliance", "legal_framework",
            "ip_protection", "trade_compliance", "audit_preparation"
        }
        
        found_categories = set()
        for criteria in all_criteria.values():
            for criterion in criteria.criteria:
                found_categories.add(criterion.category)
        
        # All found categories should be in expected categories
        assert found_categories.issubset(expected_categories)
        
        # Should have at least some core categories
        core_categories = {"automation", "tracking", "documentation", "compliance"}
        assert core_categories.issubset(found_categories)
    
    def test_phoenix_specific_criteria(self, monetization_criteria):
        """Test Phoenix Hydra specific monetization criteria"""
        # Test that Phoenix-specific services are covered
        affiliate_criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.AFFILIATE_PROGRAMS)
        affiliate_ids = [c.id for c in affiliate_criteria.criteria]
        
        # Should have DigitalOcean, CustomGPT, and Cloudflare
        assert "affiliate_digitalocean_setup" in affiliate_ids
        assert "affiliate_customgpt_setup" in affiliate_ids
        assert "affiliate_cloudflare_setup" in affiliate_ids
        
        # Test grant applications for EU programs
        grant_criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.GRANT_APPLICATIONS)
        grant_ids = [c.id for c in grant_criteria.criteria]
        
        # Should have NEOTEC, ENISA, and EIC
        assert "grant_neotec_generator" in grant_ids
        assert "grant_enisa_documentation" in grant_ids
        assert "grant_eic_accelerator_prep" in grant_ids
        
        # Test marketplace readiness for target platforms
        marketplace_criteria = monetization_criteria.get_criteria_for_component(MonetizationComponent.MARKETPLACE_READINESS)
        marketplace_ids = [c.id for c in marketplace_criteria.criteria]
        
        # Should have AWS, Cloudflare, and Hugging Face
        assert "marketplace_aws_deployment" in marketplace_ids
        assert "marketplace_cloudflare_workers" in marketplace_ids
        assert "marketplace_huggingface_integration" in marketplace_ids
    
    def test_revenue_target_alignment(self, monetization_criteria):
        """Test that criteria align with €400k+ revenue target"""
        revenue_criteria = monetization_criteria.get_revenue_target_criteria()
        
        # Should target €400k
        assert revenue_criteria["target_amount"] == 400000.0
        assert revenue_criteria["currency"] == "EUR"
        
        # Revenue streams should add up to 100%
        streams = revenue_criteria["revenue_streams"]
        total_weight = sum(stream["weight"] for stream in streams.values())
        assert abs(total_weight - 1.0) < 0.01
        
        # Milestones should be progressive
        milestones = revenue_criteria["milestones"]
        q1_target = milestones["q1_2025"]
        q2_target = milestones["q2_2025"]
        q3_target = milestones["q3_2025"]
        q4_target = milestones["q4_2025"]
        
        assert q1_target < q2_target < q3_target < q4_target
        assert q4_target == revenue_criteria["target_amount"]


if __name__ == "__main__":
    pytest.main([__file__])