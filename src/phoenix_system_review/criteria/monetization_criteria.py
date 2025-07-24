"""
Monetization evaluation criteria for Phoenix Hydra System Review Tool

Defines evaluation criteria for monetization components including affiliate programs,
grant applications, marketplace readiness, and revenue tracking systems.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models.data_models import Component, ComponentCategory, Priority
from .infrastructure_criteria import CriterionDefinition, ComponentCriteria


class MonetizationComponent(Enum):
    """Types of monetization components"""
    AFFILIATE_PROGRAMS = "affiliate_programs"
    GRANT_APPLICATIONS = "grant_applications"
    MARKETPLACE_READINESS = "marketplace_readiness"
    REVENUE_TRACKING = "revenue_tracking"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    COMPLIANCE = "compliance"


class MonetizationCriteria:
    """
    Monetization evaluation criteria for Phoenix Hydra components.
    
    Provides comprehensive criteria definitions for evaluating monetization
    infrastructure including affiliate programs, grant applications, marketplace
    readiness, and revenue tracking systems.
    """
    
    def __init__(self):
        """Initialize monetization criteria definitions"""
        self._criteria_definitions = self._build_criteria_definitions()
    
    def _build_criteria_definitions(self) -> Dict[MonetizationComponent, ComponentCriteria]:
        """Build complete criteria definitions for all monetization components"""
        return {
            MonetizationComponent.AFFILIATE_PROGRAMS: self._build_affiliate_programs_criteria(),
            MonetizationComponent.GRANT_APPLICATIONS: self._build_grant_applications_criteria(),
            MonetizationComponent.MARKETPLACE_READINESS: self._build_marketplace_readiness_criteria(),
            MonetizationComponent.REVENUE_TRACKING: self._build_revenue_tracking_criteria(),
            MonetizationComponent.BUSINESS_INTELLIGENCE: self._build_business_intelligence_criteria(),
            MonetizationComponent.COMPLIANCE: self._build_compliance_criteria()
        }
    
    def _build_affiliate_programs_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for affiliate programs"""
        criteria = [
            CriterionDefinition(
                id="affiliate_digitalocean_setup",
                name="DigitalOcean Affiliate Setup",
                description="DigitalOcean affiliate program properly configured",
                category="affiliate_setup",
                weight=0.20,
                required=True,
                validation_method="check_digitalocean_affiliate",
                expected_values=["affiliate_id", "tracking_links", "badge_deployment"],
                error_message="DigitalOcean affiliate program not properly configured"
            ),
            CriterionDefinition(
                id="affiliate_customgpt_setup",
                name="CustomGPT Affiliate Setup",
                description="CustomGPT affiliate program properly configured",
                category="affiliate_setup",
                weight=0.15,
                required=True,
                validation_method="check_customgpt_affiliate",
                expected_values=["partner_id", "referral_links", "integration"],
                error_message="CustomGPT affiliate program not configured"
            ),
            CriterionDefinition(
                id="affiliate_cloudflare_setup",
                name="Cloudflare Partner Setup",
                description="Cloudflare partner program properly configured",
                category="affiliate_setup",
                weight=0.15,
                required=True,
                validation_method="check_cloudflare_partner",
                expected_values=["partner_account", "referral_system", "commission_tracking"],
                error_message="Cloudflare partner program not configured"
            ),
            CriterionDefinition(
                id="affiliate_badge_deployment",
                name="Badge Deployment System",
                description="Automated badge deployment system functional",
                category="automation",
                weight=0.20,
                required=True,
                validation_method="check_badge_deployment",
                expected_values=["deploy_script", "badge_templates", "automation"],
                error_message="Badge deployment system not functional"
            ),
            CriterionDefinition(
                id="affiliate_tracking_scripts",
                name="Tracking Scripts Implementation",
                description="Affiliate tracking scripts properly implemented",
                category="tracking",
                weight=0.15,
                required=True,
                validation_method="check_tracking_scripts",
                expected_values=["tracking_pixels", "conversion_tracking", "analytics"],
                error_message="Affiliate tracking scripts not implemented"
            ),
            CriterionDefinition(
                id="affiliate_revenue_reporting",
                name="Revenue Reporting System",
                description="Affiliate revenue reporting and analytics system",
                category="reporting",
                weight=0.15,
                required=False,
                validation_method="check_affiliate_reporting",
                expected_values=["revenue_dashboard", "commission_reports", "performance_metrics"],
                error_message="Affiliate revenue reporting system missing"
            )
        ]
        
        return ComponentCriteria(
            component_type=MonetizationComponent.AFFILIATE_PROGRAMS,
            criteria=criteria,
            minimum_score=0.75,
            critical_criteria=["affiliate_digitalocean_setup", "affiliate_badge_deployment", "affiliate_tracking_scripts"]
        )
    
    def _build_grant_applications_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for grant applications"""
        criteria = [
            CriterionDefinition(
                id="grant_neotec_generator",
                name="NEOTEC Application Generator",
                description="NEOTEC grant application generator functional",
                category="grant_automation",
                weight=0.25,
                required=True,
                validation_method="check_neotec_generator",
                expected_values=["generator_script", "template_system", "data_integration"],
                error_message="NEOTEC application generator not functional"
            ),
            CriterionDefinition(
                id="grant_enisa_documentation",
                name="ENISA Documentation Readiness",
                description="ENISA grant documentation prepared and current",
                category="documentation",
                weight=0.20,
                required=True,
                validation_method="check_enisa_documentation",
                expected_values=["technical_documentation", "security_assessment", "compliance_docs"],
                error_message="ENISA documentation not ready"
            ),
            CriterionDefinition(
                id="grant_eic_accelerator_prep",
                name="EIC Accelerator Preparation",
                description="EIC Accelerator application preparation complete",
                category="grant_preparation",
                weight=0.20,
                required=True,
                validation_method="check_eic_preparation",
                expected_values=["business_plan", "technical_feasibility", "market_analysis"],
                error_message="EIC Accelerator preparation incomplete"
            ),
            CriterionDefinition(
                id="grant_submission_tracking",
                name="Submission Tracking System",
                description="Grant submission tracking and management system",
                category="tracking",
                weight=0.15,
                required=False,
                validation_method="check_submission_tracking",
                expected_values=["submission_log", "deadline_tracking", "status_monitoring"],
                error_message="Grant submission tracking system missing"
            ),
            CriterionDefinition(
                id="grant_compliance_monitoring",
                name="Compliance Monitoring",
                description="Grant compliance and reporting requirements monitoring",
                category="compliance",
                weight=0.10,
                required=False,
                validation_method="check_grant_compliance",
                expected_values=["compliance_checklist", "reporting_schedule", "milestone_tracking"],
                error_message="Grant compliance monitoring not implemented"
            ),
            CriterionDefinition(
                id="grant_financial_projections",
                name="Financial Projections System",
                description="Financial projections and budget management for grants",
                category="financial_planning",
                weight=0.10,
                required=False,
                validation_method="check_financial_projections",
                expected_values=["budget_templates", "roi_calculations", "financial_models"],
                error_message="Financial projections system not implemented"
            )
        ]
        
        return ComponentCriteria(
            component_type=MonetizationComponent.GRANT_APPLICATIONS,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["grant_neotec_generator", "grant_enisa_documentation", "grant_eic_accelerator_prep"]
        )
    
    def _build_marketplace_readiness_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for marketplace readiness"""
        criteria = [
            CriterionDefinition(
                id="marketplace_aws_deployment",
                name="AWS Marketplace Deployment",
                description="AWS Marketplace deployment scripts and configuration ready",
                category="marketplace_deployment",
                weight=0.25,
                required=True,
                validation_method="check_aws_marketplace",
                expected_values=["cloudformation_templates", "ami_creation", "marketplace_listing"],
                error_message="AWS Marketplace deployment not ready"
            ),
            CriterionDefinition(
                id="marketplace_cloudflare_workers",
                name="Cloudflare Workers Configuration",
                description="Cloudflare Workers deployment and configuration ready",
                category="marketplace_deployment",
                weight=0.20,
                required=True,
                validation_method="check_cloudflare_workers",
                expected_values=["worker_scripts", "deployment_config", "edge_optimization"],
                error_message="Cloudflare Workers configuration not ready"
            ),
            CriterionDefinition(
                id="marketplace_huggingface_integration",
                name="Hugging Face Integration",
                description="Hugging Face model hub integration and deployment ready",
                category="ai_marketplace",
                weight=0.20,
                required=True,
                validation_method="check_huggingface_integration",
                expected_values=["model_cards", "api_integration", "deployment_pipeline"],
                error_message="Hugging Face integration not ready"
            ),
            CriterionDefinition(
                id="marketplace_enterprise_api",
                name="Enterprise API Documentation",
                description="Enterprise API documentation and examples complete",
                category="enterprise_features",
                weight=0.15,
                required=True,
                validation_method="check_enterprise_api",
                expected_values=["api_documentation", "sdk_examples", "integration_guides"],
                error_message="Enterprise API documentation incomplete"
            ),
            CriterionDefinition(
                id="marketplace_pricing_models",
                name="Pricing Models Configuration",
                description="Marketplace pricing models and billing integration",
                category="pricing",
                weight=0.10,
                required=False,
                validation_method="check_pricing_models",
                expected_values=["pricing_tiers", "billing_integration", "usage_metering"],
                error_message="Pricing models not configured"
            ),
            CriterionDefinition(
                id="marketplace_support_system",
                name="Customer Support System",
                description="Customer support and onboarding system for marketplace users",
                category="customer_support",
                weight=0.10,
                required=False,
                validation_method="check_support_system",
                expected_values=["support_documentation", "onboarding_flow", "help_desk"],
                error_message="Customer support system not implemented"
            )
        ]
        
        return ComponentCriteria(
            component_type=MonetizationComponent.MARKETPLACE_READINESS,
            criteria=criteria,
            minimum_score=0.75,
            critical_criteria=["marketplace_aws_deployment", "marketplace_cloudflare_workers", "marketplace_huggingface_integration"]
        )
    
    def _build_revenue_tracking_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for revenue tracking"""
        criteria = [
            CriterionDefinition(
                id="revenue_tracking_automation",
                name="Revenue Tracking Automation",
                description="Automated revenue tracking across all channels",
                category="automation",
                weight=0.25,
                required=True,
                validation_method="check_revenue_automation",
                expected_values=["tracking_scripts", "api_integrations", "data_collection"],
                error_message="Revenue tracking automation not implemented"
            ),
            CriterionDefinition(
                id="revenue_metrics_collection",
                name="Metrics Collection System",
                description="Comprehensive metrics collection for all revenue streams",
                category="data_collection",
                weight=0.20,
                required=True,
                validation_method="check_metrics_collection",
                expected_values=["kpi_tracking", "conversion_metrics", "revenue_attribution"],
                error_message="Revenue metrics collection system missing"
            ),
            CriterionDefinition(
                id="revenue_dashboard",
                name="Revenue Dashboard",
                description="Real-time revenue dashboard and reporting system",
                category="visualization",
                weight=0.20,
                required=True,
                validation_method="check_revenue_dashboard",
                expected_values=["dashboard_interface", "real_time_data", "revenue_charts"],
                error_message="Revenue dashboard not implemented"
            ),
            CriterionDefinition(
                id="revenue_forecasting",
                name="Revenue Forecasting",
                description="Revenue forecasting and projection system",
                category="analytics",
                weight=0.15,
                required=False,
                validation_method="check_revenue_forecasting",
                expected_values=["forecasting_models", "trend_analysis", "projection_reports"],
                error_message="Revenue forecasting system not implemented"
            ),
            CriterionDefinition(
                id="revenue_alerting",
                name="Revenue Alerting System",
                description="Automated alerts for revenue milestones and issues",
                category="monitoring",
                weight=0.10,
                required=False,
                validation_method="check_revenue_alerting",
                expected_values=["milestone_alerts", "anomaly_detection", "notification_system"],
                error_message="Revenue alerting system not configured"
            ),
            CriterionDefinition(
                id="revenue_data_export",
                name="Data Export and Integration",
                description="Revenue data export and third-party integration capabilities",
                category="integration",
                weight=0.10,
                required=False,
                validation_method="check_revenue_export",
                expected_values=["data_export", "api_endpoints", "integration_hooks"],
                error_message="Revenue data export capabilities missing"
            )
        ]
        
        return ComponentCriteria(
            component_type=MonetizationComponent.REVENUE_TRACKING,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["revenue_tracking_automation", "revenue_metrics_collection", "revenue_dashboard"]
        )
    
    def _build_business_intelligence_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for business intelligence"""
        criteria = [
            CriterionDefinition(
                id="bi_kpi_definition",
                name="KPI Definition and Tracking",
                description="Key Performance Indicators properly defined and tracked",
                category="kpi_management",
                weight=0.25,
                required=True,
                validation_method="check_kpi_definition",
                expected_values=["kpi_definitions", "success_metrics", "performance_targets"],
                error_message="KPIs not properly defined or tracked"
            ),
            CriterionDefinition(
                id="bi_success_metrics",
                name="Success Metrics Framework",
                description="Comprehensive success metrics framework implemented",
                category="metrics_framework",
                weight=0.20,
                required=True,
                validation_method="check_success_metrics",
                expected_values=["metrics_framework", "measurement_system", "benchmark_data"],
                error_message="Success metrics framework not implemented"
            ),
            CriterionDefinition(
                id="bi_performance_monitoring",
                name="Performance Monitoring System",
                description="Business performance monitoring and analysis system",
                category="monitoring",
                weight=0.20,
                required=True,
                validation_method="check_performance_monitoring",
                expected_values=["monitoring_dashboard", "performance_analysis", "trend_tracking"],
                error_message="Performance monitoring system not implemented"
            ),
            CriterionDefinition(
                id="bi_competitive_analysis",
                name="Competitive Analysis Framework",
                description="Competitive analysis and market positioning framework",
                category="market_analysis",
                weight=0.15,
                required=False,
                validation_method="check_competitive_analysis",
                expected_values=["competitor_tracking", "market_analysis", "positioning_strategy"],
                error_message="Competitive analysis framework missing"
            ),
            CriterionDefinition(
                id="bi_roi_calculation",
                name="ROI Calculation System",
                description="Return on Investment calculation and tracking system",
                category="financial_analysis",
                weight=0.10,
                required=False,
                validation_method="check_roi_calculation",
                expected_values=["roi_models", "investment_tracking", "return_analysis"],
                error_message="ROI calculation system not implemented"
            ),
            CriterionDefinition(
                id="bi_reporting_automation",
                name="Automated Reporting System",
                description="Automated business intelligence reporting system",
                category="reporting",
                weight=0.10,
                required=False,
                validation_method="check_bi_reporting",
                expected_values=["automated_reports", "scheduled_delivery", "stakeholder_dashboards"],
                error_message="Automated BI reporting system missing"
            )
        ]
        
        return ComponentCriteria(
            component_type=MonetizationComponent.BUSINESS_INTELLIGENCE,
            criteria=criteria,
            minimum_score=0.65,
            critical_criteria=["bi_kpi_definition", "bi_success_metrics", "bi_performance_monitoring"]
        )
    
    def _build_compliance_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for compliance and legal requirements"""
        criteria = [
            CriterionDefinition(
                id="compliance_gdpr",
                name="GDPR Compliance",
                description="General Data Protection Regulation compliance implemented",
                category="data_protection",
                weight=0.25,
                required=True,
                validation_method="check_gdpr_compliance",
                expected_values=["privacy_policy", "data_processing", "consent_management"],
                error_message="GDPR compliance not implemented"
            ),
            CriterionDefinition(
                id="compliance_financial_reporting",
                name="Financial Reporting Compliance",
                description="Financial reporting and tax compliance requirements met",
                category="financial_compliance",
                weight=0.20,
                required=True,
                validation_method="check_financial_compliance",
                expected_values=["tax_reporting", "financial_records", "audit_trail"],
                error_message="Financial reporting compliance not met"
            ),
            CriterionDefinition(
                id="compliance_terms_conditions",
                name="Terms and Conditions",
                description="Comprehensive terms and conditions for all services",
                category="legal_framework",
                weight=0.15,
                required=True,
                validation_method="check_terms_conditions",
                expected_values=["service_terms", "usage_policies", "liability_clauses"],
                error_message="Terms and conditions not comprehensive"
            ),
            CriterionDefinition(
                id="compliance_intellectual_property",
                name="Intellectual Property Protection",
                description="Intellectual property rights and protection measures",
                category="ip_protection",
                weight=0.15,
                required=False,
                validation_method="check_ip_protection",
                expected_values=["copyright_notices", "trademark_protection", "license_agreements"],
                error_message="IP protection measures insufficient"
            ),
            CriterionDefinition(
                id="compliance_export_control",
                name="Export Control Compliance",
                description="Export control and international trade compliance",
                category="trade_compliance",
                weight=0.15,
                required=False,
                validation_method="check_export_control",
                expected_values=["export_classification", "trade_restrictions", "compliance_screening"],
                error_message="Export control compliance not addressed"
            ),
            CriterionDefinition(
                id="compliance_audit_readiness",
                name="Audit Readiness",
                description="Audit readiness and compliance documentation",
                category="audit_preparation",
                weight=0.10,
                required=False,
                validation_method="check_audit_readiness",
                expected_values=["audit_documentation", "compliance_records", "process_documentation"],
                error_message="Audit readiness not established"
            )
        ]
        
        return ComponentCriteria(
            component_type=MonetizationComponent.COMPLIANCE,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["compliance_gdpr", "compliance_financial_reporting", "compliance_terms_conditions"]
        )
    
    def get_criteria_for_component(self, component_type: MonetizationComponent) -> ComponentCriteria:
        """
        Get evaluation criteria for a specific monetization component.
        
        Args:
            component_type: Type of monetization component
            
        Returns:
            ComponentCriteria object with all criteria definitions
        """
        return self._criteria_definitions.get(component_type)
    
    def get_all_criteria(self) -> Dict[MonetizationComponent, ComponentCriteria]:
        """
        Get all monetization evaluation criteria.
        
        Returns:
            Dictionary mapping component types to their criteria
        """
        return self._criteria_definitions.copy()
    
    def get_criterion_by_id(self, component_type: MonetizationComponent, criterion_id: str) -> Optional[CriterionDefinition]:
        """
        Get a specific criterion by ID.
        
        Args:
            component_type: Type of monetization component
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
    
    def get_critical_criteria(self, component_type: MonetizationComponent) -> List[CriterionDefinition]:
        """
        Get critical criteria for a component type.
        
        Args:
            component_type: Type of monetization component
            
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
    
    def calculate_component_score(self, component_type: MonetizationComponent, 
                                 evaluation_results: Dict[str, bool]) -> float:
        """
        Calculate weighted score for a component based on evaluation results.
        
        Args:
            component_type: Type of monetization component
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
    
    def get_revenue_target_criteria(self, target_amount: float = 400000.0) -> Dict[str, Any]:
        """
        Get criteria specific to Phoenix Hydra's €400k+ revenue target.
        
        Args:
            target_amount: Revenue target amount (default: €400k)
            
        Returns:
            Dictionary with revenue target specific criteria
        """
        return {
            "target_amount": target_amount,
            "currency": "EUR",
            "timeframe": "2025",
            "revenue_streams": {
                "affiliate_programs": {"weight": 0.3, "target": target_amount * 0.3},
                "marketplace_sales": {"weight": 0.4, "target": target_amount * 0.4},
                "grant_funding": {"weight": 0.2, "target": target_amount * 0.2},
                "enterprise_services": {"weight": 0.1, "target": target_amount * 0.1}
            },
            "milestones": {
                "q1_2025": target_amount * 0.15,
                "q2_2025": target_amount * 0.35,
                "q3_2025": target_amount * 0.65,
                "q4_2025": target_amount * 1.0
            },
            "success_metrics": [
                "monthly_recurring_revenue",
                "customer_acquisition_cost",
                "lifetime_value",
                "conversion_rates",
                "market_penetration"
            ]
        }
    
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