"""
Infrastructure evaluation criteria for Phoenix Hydra System Review Tool

Defines evaluation criteria for infrastructure components including NCA Toolkit,
Podman stack, database configuration, and Minio S3 storage.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..models.data_models import Component, ComponentCategory, Priority


class InfrastructureComponent(Enum):
    """Types of infrastructure components"""
    NCA_TOOLKIT = "nca_toolkit"
    PODMAN_STACK = "podman_stack"
    DATABASE = "database"
    MINIO_STORAGE = "minio_storage"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    NETWORKING = "networking"


@dataclass
class CriterionDefinition:
    """Definition of a single evaluation criterion"""
    id: str
    name: str
    description: str
    category: str
    weight: float
    required: bool = True
    validation_method: Optional[str] = None
    expected_values: Optional[List[Any]] = None
    error_message: Optional[str] = None


@dataclass
class ComponentCriteria:
    """Complete criteria set for a component"""
    component_type: InfrastructureComponent
    criteria: List[CriterionDefinition]
    minimum_score: float = 0.7
    critical_criteria: List[str] = None
    
    def __post_init__(self):
        if self.critical_criteria is None:
            self.critical_criteria = []


class InfrastructureCriteria:
    """
    Infrastructure evaluation criteria for Phoenix Hydra components.
    
    Provides comprehensive criteria definitions for evaluating infrastructure
    components including API endpoints, container configurations, database
    schemas, and storage policies.
    """
    
    def __init__(self):
        """Initialize infrastructure criteria definitions"""
        self._criteria_definitions = self._build_criteria_definitions()
    
    def _build_criteria_definitions(self) -> Dict[InfrastructureComponent, ComponentCriteria]:
        """Build complete criteria definitions for all infrastructure components"""
        return {
            InfrastructureComponent.NCA_TOOLKIT: self._build_nca_toolkit_criteria(),
            InfrastructureComponent.PODMAN_STACK: self._build_podman_stack_criteria(),
            InfrastructureComponent.DATABASE: self._build_database_criteria(),
            InfrastructureComponent.MINIO_STORAGE: self._build_minio_storage_criteria(),
            InfrastructureComponent.PROMETHEUS: self._build_prometheus_criteria(),
            InfrastructureComponent.GRAFANA: self._build_grafana_criteria(),
            InfrastructureComponent.NETWORKING: self._build_networking_criteria()
        }
    
    def _build_nca_toolkit_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for NCA Toolkit"""
        criteria = [
            CriterionDefinition(
                id="nca_api_endpoints",
                name="API Endpoints Available",
                description="NCA Toolkit exposes required API endpoints",
                category="functionality",
                weight=0.25,
                required=True,
                validation_method="check_api_endpoints",
                expected_values=[
                    "/health", "/api/v1/process", "/api/v1/status", 
                    "/api/v1/formats", "/api/v1/upload"
                ],
                error_message="Missing required NCA Toolkit API endpoints"
            ),
            CriterionDefinition(
                id="nca_health_check",
                name="Health Check Functional",
                description="NCA Toolkit health endpoint returns healthy status",
                category="health",
                weight=0.20,
                required=True,
                validation_method="check_health_endpoint",
                expected_values=[200, "healthy"],
                error_message="NCA Toolkit health check failing"
            ),
            CriterionDefinition(
                id="nca_multimedia_support",
                name="Multimedia Processing Support",
                description="NCA Toolkit supports required multimedia formats",
                category="functionality",
                weight=0.20,
                required=True,
                validation_method="check_multimedia_formats",
                expected_values=[
                    "image/jpeg", "image/png", "video/mp4", "audio/wav",
                    "application/pdf", "text/plain"
                ],
                error_message="Missing multimedia format support"
            ),
            CriterionDefinition(
                id="nca_performance",
                name="Performance Benchmarks",
                description="NCA Toolkit meets performance requirements",
                category="performance",
                weight=0.15,
                required=False,
                validation_method="check_performance_metrics",
                expected_values={"response_time_ms": 1000, "throughput_rps": 10},
                error_message="Performance below acceptable thresholds"
            ),
            CriterionDefinition(
                id="nca_documentation",
                name="API Documentation",
                description="NCA Toolkit has complete API documentation",
                category="documentation",
                weight=0.10,
                required=False,
                validation_method="check_api_documentation",
                expected_values=["/docs", "/swagger", "/openapi.json"],
                error_message="Missing or incomplete API documentation"
            ),
            CriterionDefinition(
                id="nca_error_handling",
                name="Error Handling",
                description="NCA Toolkit properly handles and reports errors",
                category="reliability",
                weight=0.10,
                required=True,
                validation_method="check_error_handling",
                expected_values=["400", "404", "500", "error_details"],
                error_message="Inadequate error handling implementation"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.NCA_TOOLKIT,
            criteria=criteria,
            minimum_score=0.8,
            critical_criteria=["nca_api_endpoints", "nca_health_check"]
        )
    
    def _build_podman_stack_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for Podman stack"""
        criteria = [
            CriterionDefinition(
                id="podman_compose_file",
                name="Compose File Present",
                description="Valid docker-compose.yml or podman-compose.yml exists",
                category="configuration",
                weight=0.20,
                required=True,
                validation_method="check_compose_file",
                expected_values=["docker-compose.yml", "compose.yml"],
                error_message="Missing or invalid compose file"
            ),
            CriterionDefinition(
                id="podman_service_definitions",
                name="Service Definitions Complete",
                description="All required Phoenix Hydra services defined in compose",
                category="configuration",
                weight=0.25,
                required=True,
                validation_method="check_service_definitions",
                expected_values=[
                    "phoenix-core", "nca-toolkit", "n8n-phoenix", 
                    "windmill", "postgres", "minio"
                ],
                error_message="Missing required service definitions"
            ),
            CriterionDefinition(
                id="podman_health_checks",
                name="Health Checks Configured",
                description="Health checks configured for all critical services",
                category="monitoring",
                weight=0.20,
                required=True,
                validation_method="check_health_checks",
                expected_values=["healthcheck", "test", "interval"],
                error_message="Missing health check configurations"
            ),
            CriterionDefinition(
                id="podman_networking",
                name="Network Configuration",
                description="Proper network configuration for service communication",
                category="networking",
                weight=0.15,
                required=True,
                validation_method="check_networking",
                expected_values=["networks", "ports", "expose"],
                error_message="Inadequate network configuration"
            ),
            CriterionDefinition(
                id="podman_volumes",
                name="Volume Management",
                description="Persistent volumes configured for data storage",
                category="storage",
                weight=0.10,
                required=False,
                validation_method="check_volumes",
                expected_values=["volumes", "bind", "persistent"],
                error_message="Missing volume configurations"
            ),
            CriterionDefinition(
                id="podman_security",
                name="Security Configuration",
                description="Security best practices implemented",
                category="security",
                weight=0.10,
                required=False,
                validation_method="check_security",
                expected_values=["user", "read_only", "no_new_privileges"],
                error_message="Security configurations missing"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.PODMAN_STACK,
            criteria=criteria,
            minimum_score=0.75,
            critical_criteria=["podman_compose_file", "podman_service_definitions", "podman_health_checks"]
        )
    
    def _build_database_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for database configuration"""
        criteria = [
            CriterionDefinition(
                id="db_schema_present",
                name="Database Schema Defined",
                description="Database schema files present and valid",
                category="schema",
                weight=0.25,
                required=True,
                validation_method="check_database_schema",
                expected_values=["schema.sql", "migrations/", "models/"],
                error_message="Missing database schema definition"
            ),
            CriterionDefinition(
                id="db_migrations",
                name="Migration System",
                description="Database migration system configured",
                category="schema",
                weight=0.20,
                required=True,
                validation_method="check_migrations",
                expected_values=["migrations/", "alembic", "flyway"],
                error_message="Database migration system not configured"
            ),
            CriterionDefinition(
                id="db_connection_config",
                name="Connection Configuration",
                description="Database connection properly configured",
                category="configuration",
                weight=0.20,
                required=True,
                validation_method="check_db_connection",
                expected_values=["DATABASE_URL", "connection_pool", "timeout"],
                error_message="Database connection configuration missing"
            ),
            CriterionDefinition(
                id="db_backup_strategy",
                name="Backup Strategy",
                description="Database backup and recovery strategy implemented",
                category="reliability",
                weight=0.15,
                required=False,
                validation_method="check_backup_strategy",
                expected_values=["backup_script", "pg_dump", "schedule"],
                error_message="Database backup strategy not implemented"
            ),
            CriterionDefinition(
                id="db_performance_tuning",
                name="Performance Configuration",
                description="Database performance tuning applied",
                category="performance",
                weight=0.10,
                required=False,
                validation_method="check_db_performance",
                expected_values=["indexes", "query_optimization", "connection_pooling"],
                error_message="Database performance not optimized"
            ),
            CriterionDefinition(
                id="db_security",
                name="Security Configuration",
                description="Database security measures implemented",
                category="security",
                weight=0.10,
                required=True,
                validation_method="check_db_security",
                expected_values=["authentication", "ssl", "user_permissions"],
                error_message="Database security configuration inadequate"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.DATABASE,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["db_schema_present", "db_connection_config", "db_security"]
        )
    
    def _build_minio_storage_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for Minio S3 storage"""
        criteria = [
            CriterionDefinition(
                id="minio_configuration",
                name="Minio Configuration",
                description="Minio server properly configured",
                category="configuration",
                weight=0.25,
                required=True,
                validation_method="check_minio_config",
                expected_values=["MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "data_dir"],
                error_message="Minio configuration incomplete"
            ),
            CriterionDefinition(
                id="minio_buckets",
                name="Bucket Configuration",
                description="Required S3 buckets created and configured",
                category="storage",
                weight=0.20,
                required=True,
                validation_method="check_minio_buckets",
                expected_values=["phoenix-media", "phoenix-backups", "phoenix-logs"],
                error_message="Required S3 buckets not configured"
            ),
            CriterionDefinition(
                id="minio_access_policies",
                name="Access Policies",
                description="Proper access policies and permissions configured",
                category="security",
                weight=0.20,
                required=True,
                validation_method="check_access_policies",
                expected_values=["bucket_policy", "user_permissions", "read_write_access"],
                error_message="Access policies not properly configured"
            ),
            CriterionDefinition(
                id="minio_health_monitoring",
                name="Health Monitoring",
                description="Minio health and performance monitoring configured",
                category="monitoring",
                weight=0.15,
                required=False,
                validation_method="check_minio_monitoring",
                expected_values=["/minio/health/live", "/minio/health/ready", "metrics"],
                error_message="Minio health monitoring not configured"
            ),
            CriterionDefinition(
                id="minio_backup_replication",
                name="Backup and Replication",
                description="Backup and replication strategy implemented",
                category="reliability",
                weight=0.10,
                required=False,
                validation_method="check_minio_backup",
                expected_values=["replication", "versioning", "lifecycle_policy"],
                error_message="Backup and replication not configured"
            ),
            CriterionDefinition(
                id="minio_ssl_tls",
                name="SSL/TLS Configuration",
                description="SSL/TLS encryption configured for secure access",
                category="security",
                weight=0.10,
                required=False,
                validation_method="check_minio_ssl",
                expected_values=["https", "certificates", "tls_config"],
                error_message="SSL/TLS not configured for Minio"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.MINIO_STORAGE,
            criteria=criteria,
            minimum_score=0.7,
            critical_criteria=["minio_configuration", "minio_buckets", "minio_access_policies"]
        )
    
    def _build_prometheus_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for Prometheus monitoring"""
        criteria = [
            CriterionDefinition(
                id="prometheus_config",
                name="Prometheus Configuration",
                description="Prometheus server properly configured",
                category="configuration",
                weight=0.30,
                required=True,
                validation_method="check_prometheus_config",
                expected_values=["prometheus.yml", "scrape_configs", "targets"],
                error_message="Prometheus configuration missing or invalid"
            ),
            CriterionDefinition(
                id="prometheus_targets",
                name="Monitoring Targets",
                description="All Phoenix Hydra services configured as monitoring targets",
                category="monitoring",
                weight=0.25,
                required=True,
                validation_method="check_prometheus_targets",
                expected_values=["phoenix-core", "nca-toolkit", "postgres", "minio"],
                error_message="Missing monitoring targets"
            ),
            CriterionDefinition(
                id="prometheus_retention",
                name="Data Retention Policy",
                description="Appropriate data retention policy configured",
                category="storage",
                weight=0.15,
                required=False,
                validation_method="check_prometheus_retention",
                expected_values=["retention.time", "retention.size"],
                error_message="Data retention policy not configured"
            ),
            CriterionDefinition(
                id="prometheus_alerting",
                name="Alerting Rules",
                description="Alerting rules configured for critical metrics",
                category="alerting",
                weight=0.20,
                required=False,
                validation_method="check_prometheus_alerting",
                expected_values=["alert.rules", "alertmanager", "notifications"],
                error_message="Alerting rules not configured"
            ),
            CriterionDefinition(
                id="prometheus_storage",
                name="Storage Configuration",
                description="Persistent storage configured for metrics data",
                category="storage",
                weight=0.10,
                required=False,
                validation_method="check_prometheus_storage",
                expected_values=["storage.tsdb", "volume_mount", "persistence"],
                error_message="Persistent storage not configured"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.PROMETHEUS,
            criteria=criteria,
            minimum_score=0.6,
            critical_criteria=["prometheus_config", "prometheus_targets"]
        )
    
    def _build_grafana_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for Grafana dashboards"""
        criteria = [
            CriterionDefinition(
                id="grafana_config",
                name="Grafana Configuration",
                description="Grafana properly configured with data sources",
                category="configuration",
                weight=0.25,
                required=True,
                validation_method="check_grafana_config",
                expected_values=["grafana.ini", "datasources", "prometheus"],
                error_message="Grafana configuration incomplete"
            ),
            CriterionDefinition(
                id="grafana_dashboards",
                name="Phoenix Dashboards",
                description="Phoenix Hydra specific dashboards configured",
                category="visualization",
                weight=0.30,
                required=True,
                validation_method="check_grafana_dashboards",
                expected_values=["system_overview", "service_health", "performance_metrics"],
                error_message="Phoenix Hydra dashboards not configured"
            ),
            CriterionDefinition(
                id="grafana_alerts",
                name="Alert Configuration",
                description="Alert notifications configured in Grafana",
                category="alerting",
                weight=0.20,
                required=False,
                validation_method="check_grafana_alerts",
                expected_values=["notification_channels", "alert_rules", "thresholds"],
                error_message="Grafana alerts not configured"
            ),
            CriterionDefinition(
                id="grafana_users",
                name="User Management",
                description="User access and permissions configured",
                category="security",
                weight=0.15,
                required=False,
                validation_method="check_grafana_users",
                expected_values=["admin_user", "viewer_role", "authentication"],
                error_message="User management not configured"
            ),
            CriterionDefinition(
                id="grafana_plugins",
                name="Required Plugins",
                description="Necessary Grafana plugins installed",
                category="functionality",
                weight=0.10,
                required=False,
                validation_method="check_grafana_plugins",
                expected_values=["prometheus", "postgres", "json"],
                error_message="Required Grafana plugins missing"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.GRAFANA,
            criteria=criteria,
            minimum_score=0.6,
            critical_criteria=["grafana_config", "grafana_dashboards"]
        )
    
    def _build_networking_criteria(self) -> ComponentCriteria:
        """Build evaluation criteria for networking configuration"""
        criteria = [
            CriterionDefinition(
                id="network_topology",
                name="Network Topology",
                description="Proper network topology configured for service communication",
                category="networking",
                weight=0.25,
                required=True,
                validation_method="check_network_topology",
                expected_values=["bridge_network", "service_discovery", "internal_communication"],
                error_message="Network topology not properly configured"
            ),
            CriterionDefinition(
                id="port_management",
                name="Port Management",
                description="Port assignments and management properly configured",
                category="networking",
                weight=0.20,
                required=True,
                validation_method="check_port_management",
                expected_values=["port_mapping", "no_conflicts", "standard_ports"],
                error_message="Port management issues detected"
            ),
            CriterionDefinition(
                id="load_balancing",
                name="Load Balancing",
                description="Load balancing configured for high availability",
                category="scalability",
                weight=0.15,
                required=False,
                validation_method="check_load_balancing",
                expected_values=["nginx", "haproxy", "round_robin"],
                error_message="Load balancing not configured"
            ),
            CriterionDefinition(
                id="ssl_termination",
                name="SSL Termination",
                description="SSL/TLS termination properly configured",
                category="security",
                weight=0.20,
                required=False,
                validation_method="check_ssl_termination",
                expected_values=["ssl_certificates", "https_redirect", "tls_config"],
                error_message="SSL termination not configured"
            ),
            CriterionDefinition(
                id="firewall_rules",
                name="Firewall Configuration",
                description="Firewall rules configured for security",
                category="security",
                weight=0.20,
                required=False,
                validation_method="check_firewall_rules",
                expected_values=["iptables", "ufw", "port_restrictions"],
                error_message="Firewall rules not configured"
            )
        ]
        
        return ComponentCriteria(
            component_type=InfrastructureComponent.NETWORKING,
            criteria=criteria,
            minimum_score=0.6,
            critical_criteria=["network_topology", "port_management"]
        )
    
    def get_criteria_for_component(self, component_type: InfrastructureComponent) -> ComponentCriteria:
        """
        Get evaluation criteria for a specific infrastructure component.
        
        Args:
            component_type: Type of infrastructure component
            
        Returns:
            ComponentCriteria object with all criteria definitions
        """
        return self._criteria_definitions.get(component_type)
    
    def get_all_criteria(self) -> Dict[InfrastructureComponent, ComponentCriteria]:
        """
        Get all infrastructure evaluation criteria.
        
        Returns:
            Dictionary mapping component types to their criteria
        """
        return self._criteria_definitions.copy()
    
    def get_criterion_by_id(self, component_type: InfrastructureComponent, criterion_id: str) -> Optional[CriterionDefinition]:
        """
        Get a specific criterion by ID.
        
        Args:
            component_type: Type of infrastructure component
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
    
    def get_critical_criteria(self, component_type: InfrastructureComponent) -> List[CriterionDefinition]:
        """
        Get critical criteria for a component type.
        
        Args:
            component_type: Type of infrastructure component
            
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
    
    def calculate_component_score(self, component_type: InfrastructureComponent, 
                                 evaluation_results: Dict[str, bool]) -> float:
        """
        Calculate weighted score for a component based on evaluation results.
        
        Args:
            component_type: Type of infrastructure component
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