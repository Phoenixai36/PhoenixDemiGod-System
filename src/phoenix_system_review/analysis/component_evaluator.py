"""
Component Evaluator for Phoenix Hydra System Review Tool
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from ..models.data_models import Component, ComponentCategory, Priority, EvaluationResult
from ..criteria.infrastructure_criteria import InfrastructureCriteria, InfrastructureComponent
from ..criteria.monetization_criteria import MonetizationCriteria, MonetizationComponent
from ..criteria.automation_criteria import AutomationCriteria, AutomationComponent
from ..criteria.infrastructure_criteria import CriterionDefinition, ComponentCriteria


class EvaluationStatus(Enum):
    """Status of component evaluation"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_EVALUATED = "not_evaluated"


@dataclass
class CriterionEvaluation:
    """Result of evaluating a single criterion"""
    criterion_id: str
    criterion_name: str
    status: EvaluationStatus
    score: float  # 0.0 to 1.0
    weight: float
    required: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentEvaluation:
    """Result of evaluating a component"""
    component: Component
    criteria_type: str
    overall_score: float  # 0.0 to 1.0
    completion_percentage: float  # 0.0 to 100.0
    status: EvaluationStatus
    criterion_evaluations: List[CriterionEvaluation] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    meets_minimum_score: bool = False
    critical_criteria_passed: bool = False


class ComponentEvaluator:
    """Evaluates Phoenix Hydra components against defined criteria."""
    
    def __init__(self, project_root: str = "."):
        """Initialize component evaluator with criteria"""
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Initialize criteria systems
        self.infrastructure_criteria = InfrastructureCriteria()
        self.monetization_criteria = MonetizationCriteria()
        self.automation_criteria = AutomationCriteria()
        
        # Component type mappings
        self.component_type_mappings = {
            ComponentCategory.INFRASTRUCTURE: self._get_infrastructure_component_type,
            ComponentCategory.MONETIZATION: self._get_monetization_component_type,
            ComponentCategory.AUTOMATION: self._get_automation_component_type
        }
    
    def evaluate_component(self, component: Component) -> ComponentEvaluation:
        """Evaluate a single component against its criteria."""
        try:
            # Determine component type and get criteria
            component_type = self._determine_component_type(component)
            if not component_type:
                return self._create_not_evaluated_result(component, "Unknown component type")
            
            criteria = self._get_criteria_for_component(component, component_type)
            if not criteria:
                return self._create_not_evaluated_result(component, "No criteria found")
            
            # Evaluate each criterion
            criterion_evaluations = []
            for criterion in criteria.criteria:
                evaluation = self._evaluate_criterion(component, criterion)
                criterion_evaluations.append(evaluation)
            
            # Calculate overall score and status
            overall_score = self._calculate_overall_score(criterion_evaluations)
            completion_percentage = overall_score * 100.0
            
            # Check minimum score and critical criteria
            meets_minimum = overall_score >= criteria.minimum_score
            critical_passed = self._check_critical_criteria(criterion_evaluations, criteria.critical_criteria)
            
            # Determine overall status
            status = self._determine_overall_status(overall_score, meets_minimum, critical_passed)
            
            # Generate issues and recommendations
            issues = self._generate_issues(criterion_evaluations, meets_minimum, critical_passed)
            recommendations = self._generate_recommendations(criterion_evaluations, criteria)
            
            return ComponentEvaluation(
                component=component,
                criteria_type=str(component_type),
                overall_score=overall_score,
                completion_percentage=completion_percentage,
                status=status,
                criterion_evaluations=criterion_evaluations,
                issues=issues,
                recommendations=recommendations,
                meets_minimum_score=meets_minimum,
                critical_criteria_passed=critical_passed
            )
            
        except Exception as e:
            self.logger.error(f"Error evaluating component {component.name}: {e}")
            return self._create_not_evaluated_result(component, f"Evaluation error: {e}")
    
    def evaluate_components(self, components: List[Component]) -> List[ComponentEvaluation]:
        """Evaluate multiple components."""
        evaluations = []
        for component in components:
            evaluation = self.evaluate_component(component)
            evaluations.append(evaluation)
        return evaluations
    
    def calculate_system_completion(self, evaluations: List[ComponentEvaluation]) -> Dict[str, Any]:
        """Calculate overall system completion based on component evaluations."""
        if not evaluations:
            return {
                "overall_completion": 0.0,
                "category_completion": {},
                "total_components": 0,
                "evaluated_components": 0,
                "passed_components": 0,
                "failed_components": 0,
                "critical_issues": 0
            }
        
        # Filter out not evaluated components
        valid_evaluations = [e for e in evaluations if e.status != EvaluationStatus.NOT_EVALUATED]
        
        # Calculate overall completion
        if valid_evaluations:
            overall_completion = sum(e.completion_percentage for e in valid_evaluations) / len(valid_evaluations)
        else:
            overall_completion = 0.0
        
        # Calculate category-wise completion
        category_completion = {}
        category_groups = {}
        
        for evaluation in valid_evaluations:
            category = evaluation.component.category.value
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(evaluation)
        
        for category, cat_evaluations in category_groups.items():
            category_completion[category] = {
                "completion": sum(e.completion_percentage for e in cat_evaluations) / len(cat_evaluations),
                "components": len(cat_evaluations),
                "passed": len([e for e in cat_evaluations if e.status == EvaluationStatus.PASSED]),
                "failed": len([e for e in cat_evaluations if e.status == EvaluationStatus.FAILED])
            }
        
        # Count components by status
        passed_components = len([e for e in valid_evaluations if e.status == EvaluationStatus.PASSED])
        failed_components = len([e for e in valid_evaluations if e.status == EvaluationStatus.FAILED])
        
        # Count critical issues
        critical_issues = len([e for e in valid_evaluations if not e.critical_criteria_passed])
        
        return {
            "overall_completion": overall_completion,
            "category_completion": category_completion,
            "total_components": len(evaluations),
            "evaluated_components": len(valid_evaluations),
            "passed_components": passed_components,
            "failed_components": failed_components,
            "critical_issues": critical_issues
        }
    
    def generate_evaluation_report(self, evaluations: List[ComponentEvaluation]) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        system_metrics = self.calculate_system_completion(evaluations)
        
        # Group evaluations by status
        passed_evaluations = [e for e in evaluations if e.status == EvaluationStatus.PASSED]
        failed_evaluations = [e for e in evaluations if e.status == EvaluationStatus.FAILED]
        warning_evaluations = [e for e in evaluations if e.status == EvaluationStatus.WARNING]
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        
        for evaluation in evaluations:
            all_issues.extend(evaluation.issues)
            all_recommendations.extend(evaluation.recommendations)
        
        # Find top issues and recommendations
        top_issues = list(set(all_issues))[:10]  # Remove duplicates and limit
        top_recommendations = list(set(all_recommendations))[:10]
        
        return {
            "system_metrics": system_metrics,
            "component_evaluations": {
                "passed": [self._evaluation_summary(e) for e in passed_evaluations],
                "failed": [self._evaluation_summary(e) for e in failed_evaluations],
                "warnings": [self._evaluation_summary(e) for e in warning_evaluations]
            },
            "top_issues": top_issues,
            "top_recommendations": top_recommendations,
            "evaluation_timestamp": self._get_timestamp()
        }
    
    def _determine_component_type(self, component: Component) -> Optional[Any]:
        """Determine the specific component type for evaluation"""
        if component.category in self.component_type_mappings:
            return self.component_type_mappings[component.category](component)
        return None
    
    def _get_infrastructure_component_type(self, component: Component) -> Optional[InfrastructureComponent]:
        """Map component to infrastructure component type"""
        name_lower = component.name.lower()
        
        if "nca" in name_lower or "toolkit" in name_lower:
            return InfrastructureComponent.NCA_TOOLKIT
        elif "podman" in name_lower or "container" in name_lower:
            return InfrastructureComponent.PODMAN_STACK
        elif "database" in name_lower or "postgres" in name_lower:
            return InfrastructureComponent.DATABASE
        elif "minio" in name_lower or "s3" in name_lower:
            return InfrastructureComponent.MINIO_STORAGE
        elif "prometheus" in name_lower:
            return InfrastructureComponent.PROMETHEUS
        elif "grafana" in name_lower:
            return InfrastructureComponent.GRAFANA
        elif "network" in name_lower or "proxy" in name_lower:
            return InfrastructureComponent.NETWORKING
        
        return None
    
    def _get_monetization_component_type(self, component: Component) -> Optional[MonetizationComponent]:
        """Map component to monetization component type"""
        name_lower = component.name.lower()
        
        if "affiliate" in name_lower:
            return MonetizationComponent.AFFILIATE_MARKETING
        elif "grant" in name_lower:
            return MonetizationComponent.GRANT_TRACKING
        elif "revenue" in name_lower:
            return MonetizationComponent.REVENUE_STREAMS
        elif "strategy" in name_lower:
            return MonetizationComponent.MONETIZATION_STRATEGY
        elif "payment" in name_lower:
            return MonetizationComponent.PAYMENT_PROCESSING
        elif "analytics" in name_lower:
            return MonetizationComponent.ANALYTICS_TRACKING
        elif "compliance" in name_lower:
            return MonetizationComponent.COMPLIANCE_MONITORING
        
        return None
    
    def _get_automation_component_type(self, component: Component) -> Optional[AutomationComponent]:
        """Map component to automation component type"""
        name_lower = component.name.lower()
        
        if "vscode" in name_lower or "ide" in name_lower:
            return AutomationComponent.VSCODE_INTEGRATION
        elif "deployment" in name_lower and "script" in name_lower:
            return AutomationComponent.DEPLOYMENT_SCRIPTS
        elif "hook" in name_lower or "kiro" in name_lower:
            return AutomationComponent.KIRO_AGENT_HOOKS
        elif "cicd" in name_lower or "pipeline" in name_lower:
            return AutomationComponent.CICD_PIPELINE
        elif "build" in name_lower:
            return AutomationComponent.BUILD_AUTOMATION
        elif "test" in name_lower:
            return AutomationComponent.TESTING_AUTOMATION
        elif "monitor" in name_lower:
            return AutomationComponent.MONITORING_AUTOMATION
        
        return None
    
    def _get_criteria_for_component(self, component: Component, component_type: Any) -> Optional[ComponentCriteria]:
        """Get criteria for a specific component type"""
        if isinstance(component_type, InfrastructureComponent):
            return self.infrastructure_criteria.get_criteria_for_component(component_type)
        elif isinstance(component_type, MonetizationComponent):
            return self.monetization_criteria.get_criteria_for_component(component_type)
        elif isinstance(component_type, AutomationComponent):
            return self.automation_criteria.get_criteria_for_component(component_type)
        
        return None
    
    def _evaluate_criterion(self, component: Component, criterion: CriterionDefinition) -> CriterionEvaluation:
        """Evaluate a single criterion against a component"""
        try:
            score, status, message = self._perform_criterion_validation(component, criterion)
            
            return CriterionEvaluation(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                status=status,
                score=score,
                weight=criterion.weight,
                required=criterion.required,
                message=message,
                details={
                    "validation_method": criterion.validation_method,
                    "expected_values": criterion.expected_values
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error evaluating criterion {criterion.id}: {e}")
            return CriterionEvaluation(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                status=EvaluationStatus.FAILED,
                score=0.0,
                weight=criterion.weight,
                required=criterion.required,
                message=f"Evaluation error: {e}"
            )
    
    def _perform_criterion_validation(self, component: Component, criterion: CriterionDefinition) -> Tuple[float, EvaluationStatus, str]:
        """Perform actual validation of a criterion"""
        # Simplified validation logic
        if criterion.expected_values:
            found_values = 0
            total_values = len(criterion.expected_values)
            
            for expected_value in criterion.expected_values:
                if self._check_expected_value(component, expected_value):
                    found_values += 1
            
            score = found_values / total_values if total_values > 0 else 0.0
            
            if score >= 0.8:
                status = EvaluationStatus.PASSED
                message = f"Criterion met ({found_values}/{total_values} requirements satisfied)"
            elif score >= 0.5:
                status = EvaluationStatus.WARNING
                message = f"Criterion partially met ({found_values}/{total_values} requirements satisfied)"
            else:
                status = EvaluationStatus.FAILED
                message = f"Criterion not met ({found_values}/{total_values} requirements satisfied)"
        else:
            # Default evaluation based on component status
            from ..models.data_models import ComponentStatus
            if component.status == ComponentStatus.OPERATIONAL:
                score = 0.8
                status = EvaluationStatus.PASSED
                message = "Component is operational"
            elif component.status == ComponentStatus.DEGRADED:
                score = 0.5
                status = EvaluationStatus.WARNING
                message = "Component is degraded"
            else:
                score = 0.2
                status = EvaluationStatus.FAILED
                message = "Component is not operational"
        
        return score, status, message
    
    def _check_expected_value(self, component: Component, expected_value: str) -> bool:
        """Check if an expected value exists for the component"""
        # Check if it's a file path
        if "/" in expected_value or "\\" in expected_value or "." in expected_value:
            file_path = self.project_root / expected_value
            return file_path.exists()
        
        # Check if it's mentioned in component configuration
        if hasattr(component, 'configuration') and component.configuration:
            config_str = str(component.configuration).lower()
            return expected_value.lower() in config_str
        
        # Check if it's in the component name or description
        component_text = f"{component.name} {component.description or ''}".lower()
        return expected_value.lower() in component_text
    
    def _calculate_overall_score(self, criterion_evaluations: List[CriterionEvaluation]) -> float:
        """Calculate weighted overall score from criterion evaluations"""
        if not criterion_evaluations:
            return 0.0
        
        total_weight = sum(ce.weight for ce in criterion_evaluations)
        if total_weight == 0:
            return 0.0
        
        weighted_score = sum(ce.score * ce.weight for ce in criterion_evaluations)
        return weighted_score / total_weight
    
    def _check_critical_criteria(self, criterion_evaluations: List[CriterionEvaluation], critical_criteria: List[str]) -> bool:
        """Check if all critical criteria are passed"""
        if not critical_criteria:
            return True
        
        critical_evaluations = [ce for ce in criterion_evaluations if ce.criterion_id in critical_criteria]
        return all(ce.status == EvaluationStatus.PASSED for ce in critical_evaluations)
    
    def _determine_overall_status(self, overall_score: float, meets_minimum: bool, critical_passed: bool) -> EvaluationStatus:
        """Determine overall evaluation status"""
        if not critical_passed:
            return EvaluationStatus.FAILED
        
        if meets_minimum and overall_score >= 0.8:
            return EvaluationStatus.PASSED
        elif overall_score >= 0.5:
            return EvaluationStatus.WARNING
        else:
            return EvaluationStatus.FAILED
    
    def _generate_issues(self, criterion_evaluations: List[CriterionEvaluation], meets_minimum: bool, critical_passed: bool) -> List[str]:
        """Generate list of issues from evaluation results"""
        issues = []
        
        if not critical_passed:
            failed_critical = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED and ce.required]
            for ce in failed_critical:
                issues.append(f"Critical criterion failed: {ce.criterion_name}")
        
        if not meets_minimum:
            issues.append("Component does not meet minimum score threshold")
        
        # Add specific criterion failures
        failed_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED]
        for ce in failed_criteria:
            issues.append(f"{ce.criterion_name}: {ce.message}")
        
        return issues
    
    def _generate_recommendations(self, criterion_evaluations: List[CriterionEvaluation], criteria: ComponentCriteria) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        # Recommendations for failed criteria
        failed_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED]
        for ce in failed_criteria:
            if ce.details.get("expected_values"):
                expected = ce.details["expected_values"]
                if isinstance(expected, list):
                    expected_str = ', '.join(str(x) for x in expected[:3])
                else:
                    expected_str = str(expected)
                recommendations.append(f"Implement {ce.criterion_name}: ensure {expected_str} are configured")
        
        # Recommendations for warning criteria
        warning_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.WARNING]
        for ce in warning_criteria:
            recommendations.append(f"Improve {ce.criterion_name}: {ce.message}")
        
        return recommendations
    
    def _create_not_evaluated_result(self, component: Component, reason: str) -> ComponentEvaluation:
        """Create evaluation result for components that couldn't be evaluated"""
        return ComponentEvaluation(
            component=component,
            criteria_type="unknown",
            overall_score=0.0,
            completion_percentage=0.0,
            status=EvaluationStatus.NOT_EVALUATED,
            issues=[f"Component not evaluated: {reason}"],
            recommendations=["Define appropriate evaluation criteria for this component"]
        )
    
    def _evaluation_summary(self, evaluation: ComponentEvaluation) -> Dict[str, Any]:
        """Create summary of evaluation for reporting"""
        return {
            "component_name": evaluation.component.name,
            "category": evaluation.component.category.value,
            "completion_percentage": evaluation.completion_percentage,
            "status": evaluation.status.value,
            "issues_count": len(evaluation.issues),
            "recommendations_count": len(evaluation.recommendations),
            "critical_criteria_passed": evaluation.critical_criteria_passed
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reporting"""
        from datetime import datetime
        return datetime.now().isoformat()