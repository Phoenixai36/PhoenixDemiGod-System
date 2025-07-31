"""
Phoenix Hydra Integration Coordinator

Coordinates all Phoenix Hydra specific integrations (Podman, n8n, Windmill)
and provides a unified interface for the system review framework.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from ..models.data_models import Component, ComponentStatus, Issue, Priority, EvaluationResult
from .podman_analyzer import PodmanAnalyzer, ComposeAnalysis, SystemdServiceInfo
from .n8n_analyzer import N8nAnalyzer, N8nAnalysis, WorkflowInfo
from .windmill_analyzer import WindmillAnalyzer, WindmillAnalysis, WindmillWorkspace


@dataclass
class PhoenixHydraIntegrationResult:
    """Comprehensive result of Phoenix Hydra integration analysis"""
    podman_analysis: Optional[EvaluationResult] = None
    n8n_analysis: Optional[EvaluationResult] = None
    windmill_analysis: Optional[EvaluationResult] = None
    integration_health_score: float = 0.0
    cross_integration_issues: List[Issue] = None
    integration_recommendations: List[str] = None
    
    def __post_init__(self):
        if self.cross_integration_issues is None:
            self.cross_integration_issues = []
        if self.integration_recommendations is None:
            self.integration_recommendations = []


class PhoenixHydraIntegrator:
    """
    Coordinates all Phoenix Hydra specific integrations and provides
    unified analysis results for the system review framework.
    """
    
    def __init__(self, project_root: str):
        """
        Initialize Phoenix Hydra integrator.
        
        Args:
            project_root: Root directory of the Phoenix Hydra project
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Initialize individual analyzers
        self.podman_analyzer = PodmanAnalyzer(str(project_root))
        self.n8n_analyzer = N8nAnalyzer(str(project_root))
        self.windmill_analyzer = WindmillAnalyzer(str(project_root))
        
        # Integration validation rules
        self.integration_rules = {
            "service_connectivity": {
                "podman_to_n8n": {"port": 5678, "health_endpoint": "/healthz"},
                "podman_to_windmill": {"port": 8000, "health_endpoint": "/api/version"},
                "n8n_to_phoenix_core": {"port": 8080, "health_endpoint": "/health"},
                "windmill_to_nca_toolkit": {"port": 8081, "health_endpoint": "/health"}
            },
            "configuration_consistency": {
                "environment_variables": ["PHOENIX_API_KEY", "WINDMILL_TOKEN"],
                "service_names": ["phoenix-core", "nca-toolkit", "n8n-phoenix", "windmill-phoenix"],
                "network_names": ["phoenix-network", "phoenix-internal"]
            },
            "workflow_integration": {
                "n8n_windmill_sync": ["monetization", "grant-application", "nca-toolkit"],
                "shared_resources": ["revenue-db", "phoenix-storage"],
                "api_endpoints": ["localhost:8080", "localhost:8081"]
            }
        }
    
    def analyze_all_integrations(self) -> PhoenixHydraIntegrationResult:
        """
        Perform comprehensive analysis of all Phoenix Hydra integrations.
        
        Returns:
            PhoenixHydraIntegrationResult with complete integration analysis
        """
        self.logger.info("Starting comprehensive Phoenix Hydra integration analysis")
        
        result = PhoenixHydraIntegrationResult()
        
        try:
            # Analyze individual components
            result.podman_analysis = self._analyze_podman_integration()
            result.n8n_analysis = self._analyze_n8n_integration()
            result.windmill_analysis = self._analyze_windmill_integration()
            
            # Analyze cross-integration dependencies
            result.cross_integration_issues = self._analyze_cross_integrations(
                result.podman_analysis,
                result.n8n_analysis,
                result.windmill_analysis
            )
            
            # Calculate overall integration health
            result.integration_health_score = self._calculate_integration_health_score(
                result.podman_analysis,
                result.n8n_analysis,
                result.windmill_analysis,
                result.cross_integration_issues
            )
            
            # Generate integration recommendations
            result.integration_recommendations = self._generate_integration_recommendations(
                result.podman_analysis,
                result.n8n_analysis,
                result.windmill_analysis,
                result.cross_integration_issues
            )
            
            self.logger.info(f"Integration analysis completed with health score: {result.integration_health_score:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error during integration analysis: {e}")
            result.cross_integration_issues.append(Issue(
                severity=Priority.CRITICAL,
                description=f"Integration analysis failed: {str(e)}",
                component="phoenix_hydra_integrator",
                recommendation="Check system configuration and analyzer implementations"
            ))
        
        return result
    
    def _analyze_podman_integration(self) -> EvaluationResult:
        """Analyze Podman container integration"""
        self.logger.info("Analyzing Podman container integration")
        
        try:
            return self.podman_analyzer.generate_evaluation_result()
        except Exception as e:
            self.logger.error(f"Podman analysis failed: {e}")
            
            # Create fallback evaluation result
            component = Component(
                name="podman_infrastructure",
                category="infrastructure",
                path=str(self.podman_analyzer.podman_dir),
                status=ComponentStatus.UNKNOWN
            )
            
            return EvaluationResult(
                component=component,
                criteria_met=[],
                criteria_missing=["podman_analysis_failed"],
                completion_percentage=0.0,
                quality_score=0.0,
                issues=[Issue(
                    severity=Priority.CRITICAL,
                    description=f"Podman analysis failed: {str(e)}",
                    component="podman_infrastructure",
                    recommendation="Check Podman installation and configuration"
                )]
            )
    
    def _analyze_n8n_integration(self) -> EvaluationResult:
        """Analyze n8n workflow integration"""
        self.logger.info("Analyzing n8n workflow integration")
        
        try:
            # Get n8n analysis data
            workflows = self.n8n_analyzer.analyze_workflow_files()
            n8n_healthy, n8n_version, health_issues = self.n8n_analyzer.check_n8n_health()
            
            # Create component
            component = Component(
                name="n8n_workflows",
                category="automation",
                path=str(self.n8n_analyzer.workflows_dir),
                status=ComponentStatus.OPERATIONAL if n8n_healthy else ComponentStatus.DEGRADED
            )
            
            all_issues = health_issues.copy()
            criteria_met = []
            criteria_missing = []
            
            # Evaluate workflows
            if workflows:
                criteria_met.append("workflows_present")
                
                # Validate each workflow
                for workflow in workflows:
                    workflow_issues = self.n8n_analyzer.validate_workflow(workflow)
                    all_issues.extend(workflow_issues)
                    
                    if len(workflow_issues) == 0:
                        criteria_met.append(f"workflow_valid_{workflow.name}")
                    else:
                        criteria_missing.append(f"workflow_valid_{workflow.name}")
            else:
                criteria_missing.append("workflows_present")
                all_issues.append(Issue(
                    severity=Priority.HIGH,
                    description="No n8n workflows found",
                    component="n8n_workflows",
                    recommendation="Create n8n workflows for Phoenix Hydra automation"
                ))
            
            # Check n8n health
            if n8n_healthy:
                criteria_met.append("n8n_service_healthy")
            else:
                criteria_missing.append("n8n_service_healthy")
            
            # Calculate completion and quality scores
            total_criteria = len(criteria_met) + len(criteria_missing)
            completion_percentage = len(criteria_met) / total_criteria if total_criteria > 0 else 0.0
            
            critical_issues = len([i for i in all_issues if i.severity == Priority.CRITICAL])
            quality_score = max(0.0, 1.0 - (critical_issues * 0.3))
            
            return EvaluationResult(
                component=component,
                criteria_met=criteria_met,
                criteria_missing=criteria_missing,
                completion_percentage=completion_percentage,
                quality_score=quality_score,
                issues=all_issues
            )
            
        except Exception as e:
            self.logger.error(f"n8n analysis failed: {e}")
            
            # Create fallback evaluation result
            component = Component(
                name="n8n_workflows",
                category="automation",
                path=str(self.n8n_analyzer.workflows_dir),
                status=ComponentStatus.UNKNOWN
            )
            
            return EvaluationResult(
                component=component,
                criteria_met=[],
                criteria_missing=["n8n_analysis_failed"],
                completion_percentage=0.0,
                quality_score=0.0,
                issues=[Issue(
                    severity=Priority.CRITICAL,
                    description=f"n8n analysis failed: {str(e)}",
                    component="n8n_workflows",
                    recommendation="Check n8n installation and workflow configurations"
                )]
            )
    
    def _analyze_windmill_integration(self) -> EvaluationResult:
        """Analyze Windmill GitOps integration"""
        self.logger.info("Analyzing Windmill GitOps integration")
        
        try:
            return self.windmill_analyzer.generate_evaluation_result()
        except Exception as e:
            self.logger.error(f"Windmill analysis failed: {e}")
            
            # Create fallback evaluation result
            component = Component(
                name="windmill_gitops",
                category="automation",
                path=str(self.windmill_analyzer.windmill_dir),
                status=ComponentStatus.UNKNOWN
            )
            
            return EvaluationResult(
                component=component,
                criteria_met=[],
                criteria_missing=["windmill_analysis_failed"],
                completion_percentage=0.0,
                quality_score=0.0,
                issues=[Issue(
                    severity=Priority.CRITICAL,
                    description=f"Windmill analysis failed: {str(e)}",
                    component="windmill_gitops",
                    recommendation="Check Windmill installation and script configurations"
                )]
            )
    
    def _analyze_cross_integrations(self, podman_result: Optional[EvaluationResult],
                                  n8n_result: Optional[EvaluationResult],
                                  windmill_result: Optional[EvaluationResult]) -> List[Issue]:
        """Analyze cross-integration dependencies and consistency"""
        issues = []
        
        # Check service connectivity
        issues.extend(self._validate_service_connectivity(podman_result, n8n_result, windmill_result))
        
        # Check configuration consistency
        issues.extend(self._validate_configuration_consistency(podman_result, n8n_result, windmill_result))
        
        # Check workflow integration
        issues.extend(self._validate_workflow_integration(n8n_result, windmill_result))
        
        return issues
    
    def _validate_service_connectivity(self, podman_result: Optional[EvaluationResult],
                                     n8n_result: Optional[EvaluationResult],
                                     windmill_result: Optional[EvaluationResult]) -> List[Issue]:
        """Validate service connectivity between components"""
        issues = []
        
        # Check if Podman services are exposing expected ports for n8n and Windmill
        if podman_result and "compose_files_present" in podman_result.criteria_met:
            # Check if n8n port is exposed
            if n8n_result and "n8n_service_healthy" not in n8n_result.criteria_met:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description="n8n service not accessible despite Podman configuration",
                    component="cross_integration",
                    recommendation="Verify n8n service port mapping in Podman compose file"
                ))
            
            # Check if Windmill port is exposed
            if windmill_result and "windmill_service_healthy" not in windmill_result.criteria_met:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description="Windmill service not accessible despite Podman configuration",
                    component="cross_integration",
                    recommendation="Verify Windmill service port mapping in Podman compose file"
                ))
        
        # Check if services can communicate with Phoenix Core
        if podman_result and "containers_running" in podman_result.criteria_met:
            phoenix_core_running = any("phoenix-core" in str(issue.description).lower() 
                                     for issue in podman_result.issues if "running" in str(issue.description).lower())
            
            if not phoenix_core_running:
                issues.append(Issue(
                    severity=Priority.CRITICAL,
                    description="Phoenix Core service not running - affects all integrations",
                    component="cross_integration",
                    recommendation="Start Phoenix Core service for proper integration functionality"
                ))
        
        return issues
    
    def _validate_configuration_consistency(self, podman_result: Optional[EvaluationResult],
                                          n8n_result: Optional[EvaluationResult],
                                          windmill_result: Optional[EvaluationResult]) -> List[Issue]:
        """Validate configuration consistency across components"""
        issues = []
        
        # Check for consistent service naming
        expected_services = self.integration_rules["configuration_consistency"]["service_names"]
        
        if podman_result:
            # Check if expected services are defined in Podman
            missing_services = []
            for service in expected_services:
                if not any(service in str(issue.description).lower() for issue in podman_result.issues):
                    # Service might be present, check criteria_met
                    if not any(service in criterion for criterion in podman_result.criteria_met):
                        missing_services.append(service)
            
            if missing_services:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Missing expected services in Podman configuration: {', '.join(missing_services)}",
                    component="cross_integration",
                    recommendation="Add missing services to Podman compose file"
                ))
        
        # Check for consistent environment variables
        expected_env_vars = self.integration_rules["configuration_consistency"]["environment_variables"]
        
        env_var_issues = []
        if n8n_result and any("environment" in str(issue.description).lower() for issue in n8n_result.issues):
            env_var_issues.append("n8n missing environment configuration")
        
        if windmill_result and any("environment" in str(issue.description).lower() for issue in windmill_result.issues):
            env_var_issues.append("Windmill missing environment configuration")
        
        if env_var_issues:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Environment variable configuration issues: {', '.join(env_var_issues)}",
                component="cross_integration",
                recommendation="Ensure consistent environment variable configuration across all services"
            ))
        
        return issues
    
    def _validate_workflow_integration(self, n8n_result: Optional[EvaluationResult],
                                     windmill_result: Optional[EvaluationResult]) -> List[Issue]:
        """Validate workflow integration between n8n and Windmill"""
        issues = []
        
        # Check for complementary workflows
        expected_workflows = self.integration_rules["workflow_integration"]["n8n_windmill_sync"]
        
        if n8n_result and windmill_result:
            # Check if both systems have complementary workflows
            n8n_has_monetization = any("monetization" in criterion for criterion in n8n_result.criteria_met)
            windmill_has_monetization = any("monetization" in criterion for criterion in windmill_result.criteria_met)
            
            if n8n_has_monetization and not windmill_has_monetization:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description="n8n has monetization workflows but Windmill lacks corresponding scripts",
                    component="cross_integration",
                    recommendation="Create Windmill scripts to complement n8n monetization workflows"
                ))
            elif windmill_has_monetization and not n8n_has_monetization:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description="Windmill has monetization scripts but n8n lacks corresponding workflows",
                    component="cross_integration",
                    recommendation="Create n8n workflows to complement Windmill monetization scripts"
                ))
        
        # Check for shared API endpoints
        expected_endpoints = self.integration_rules["workflow_integration"]["api_endpoints"]
        
        if n8n_result and windmill_result:
            # Both should be using Phoenix API endpoints
            n8n_uses_phoenix_api = any("phoenix" in str(issue.description).lower() for issue in n8n_result.issues)
            windmill_uses_phoenix_api = any("phoenix" in str(issue.description).lower() for issue in windmill_result.issues)
            
            if not n8n_uses_phoenix_api and not windmill_uses_phoenix_api:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description="Neither n8n nor Windmill are integrated with Phoenix API endpoints",
                    component="cross_integration",
                    recommendation="Configure both n8n and Windmill to use Phoenix Hydra API endpoints"
                ))
        
        return issues
    
    def _calculate_integration_health_score(self, podman_result: Optional[EvaluationResult],
                                          n8n_result: Optional[EvaluationResult],
                                          windmill_result: Optional[EvaluationResult],
                                          cross_issues: List[Issue]) -> float:
        """Calculate overall integration health score"""
        
        # Base scores from individual components
        scores = []
        weights = []
        
        if podman_result:
            scores.append(podman_result.completion_percentage / 100.0)
            weights.append(0.4)  # Podman is critical for infrastructure
        
        if n8n_result:
            scores.append(n8n_result.completion_percentage / 100.0)
            weights.append(0.3)  # n8n is important for automation
        
        if windmill_result:
            scores.append(windmill_result.completion_percentage / 100.0)
            weights.append(0.3)  # Windmill is important for GitOps
        
        if not scores:
            return 0.0
        
        # Calculate weighted average
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        base_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Apply penalties for cross-integration issues
        issue_penalty = 0.0
        for issue in cross_issues:
            if issue.severity == Priority.CRITICAL:
                issue_penalty += 0.2
            elif issue.severity == Priority.HIGH:
                issue_penalty += 0.1
            elif issue.severity == Priority.MEDIUM:
                issue_penalty += 0.05
            elif issue.severity == Priority.LOW:
                issue_penalty += 0.02
        
        final_score = max(0.0, base_score - issue_penalty)
        
        return final_score
    
    def _generate_integration_recommendations(self, podman_result: Optional[EvaluationResult],
                                            n8n_result: Optional[EvaluationResult],
                                            windmill_result: Optional[EvaluationResult],
                                            cross_issues: List[Issue]) -> List[str]:
        """Generate recommendations for improving integrations"""
        recommendations = []
        
        # Priority recommendations from cross-integration issues
        critical_cross_issues = [issue for issue in cross_issues if issue.severity == Priority.CRITICAL]
        for issue in critical_cross_issues:
            recommendations.append(f"CRITICAL: {issue.recommendation}")
        
        # Component-specific recommendations
        if podman_result and podman_result.completion_percentage < 80:
            recommendations.append("Improve Podman container configuration to ensure reliable service orchestration")
        
        if n8n_result and n8n_result.completion_percentage < 70:
            recommendations.append("Enhance n8n workflow configurations for better automation coverage")
        
        if windmill_result and windmill_result.completion_percentage < 70:
            recommendations.append("Improve Windmill GitOps scripts for better deployment automation")
        
        # Integration-specific recommendations
        high_cross_issues = [issue for issue in cross_issues if issue.severity == Priority.HIGH]
        for issue in high_cross_issues:
            recommendations.append(f"HIGH: {issue.recommendation}")
        
        # General integration improvements
        if len(cross_issues) > 5:
            recommendations.append("Consider redesigning integration architecture to reduce complexity")
        
        # Performance recommendations
        all_results = [r for r in [podman_result, n8n_result, windmill_result] if r]
        if all_results:
            avg_quality = sum(r.quality_score for r in all_results) / len(all_results)
            if avg_quality < 0.7:
                recommendations.append("Focus on improving code quality and error handling across all integrations")
        
        return recommendations
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get a summary of integration status for reporting"""
        result = self.analyze_all_integrations()
        
        return {
            "integration_health_score": result.integration_health_score,
            "components_analyzed": {
                "podman": result.podman_analysis is not None,
                "n8n": result.n8n_analysis is not None,
                "windmill": result.windmill_analysis is not None
            },
            "component_scores": {
                "podman": result.podman_analysis.completion_percentage if result.podman_analysis else 0.0,
                "n8n": result.n8n_analysis.completion_percentage if result.n8n_analysis else 0.0,
                "windmill": result.windmill_analysis.completion_percentage if result.windmill_analysis else 0.0
            },
            "total_issues": len(result.cross_integration_issues),
            "critical_issues": len([i for i in result.cross_integration_issues if i.severity == Priority.CRITICAL]),
            "top_recommendations": result.integration_recommendations[:5],
            "integration_status": "healthy" if result.integration_health_score >= 0.8 else 
                                "degraded" if result.integration_health_score >= 0.5 else "critical"
        }