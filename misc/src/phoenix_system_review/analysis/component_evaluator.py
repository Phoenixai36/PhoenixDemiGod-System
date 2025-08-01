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
from ..criteria.automation_criteria import AutomationCriteriaEvaluator, AutomationComponentType
from ..models.data_models import EvaluationCriterion, CriterionType


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
        self.automation_criteria = AutomationCriteriaEvaluator(str(self.project_root))
        
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
            for criterion in criteria:
                evaluation = self._evaluate_criterion(component, criterion)
                criterion_evaluations.append(evaluation)
            
            # Calculate overall score and status
            overall_score = self._calculate_overall_score(criterion_evaluations)
            completion_percentage = overall_score * 100.0
            
            # Check minimum score and critical criteria
            minimum_score = 0.7  # Default minimum score
            meets_minimum = overall_score >= minimum_score
            critical_criteria = [c.id for c in criteria if c.is_critical]
            critical_passed = self._check_critical_criteria(criterion_evaluations, critical_criteria)
            
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
    
    def _get_automation_component_type(self, component: Component) -> Optional[AutomationComponentType]:
        """Map component to automation component type"""
        name_lower = component.name.lower()
        path_lower = component.path.lower()
        
        # Check by path first for more accurate mapping
        if ".vscode" in path_lower or "vscode" in name_lower or "vs code" in name_lower or "ide" in name_lower:
            return AutomationComponentType.VSCODE_TASKS
        elif ("deployment" in name_lower and "script" in name_lower) or "scripts" in path_lower:
            return AutomationComponentType.DEPLOYMENT_SCRIPTS
        elif "hook" in name_lower or "kiro" in name_lower or ".kiro" in path_lower:
            return AutomationComponentType.KIRO_AGENT_HOOKS
        elif "cicd" in name_lower or "pipeline" in name_lower or ".github" in path_lower:
            return AutomationComponentType.CICD_PIPELINE
        elif "build" in name_lower or "build" in path_lower:
            return AutomationComponentType.BUILD_AUTOMATION
        elif "monitor" in name_lower or "monitoring" in path_lower:
            return AutomationComponentType.MONITORING_AUTOMATION
        
        # Default to VS Code tasks for automation category components
        if component.category == ComponentCategory.AUTOMATION:
            return AutomationComponentType.VSCODE_TASKS
        
        return None
    
    def _get_criteria_for_component(self, component: Component, component_type: Any) -> Optional[List[EvaluationCriterion]]:
        """Get criteria for a specific component type"""
        if isinstance(component_type, InfrastructureComponent):
            return self.infrastructure_criteria.get_criteria_for_component(component_type)
        elif isinstance(component_type, MonetizationComponent):
            return self.monetization_criteria.get_criteria_for_component(component_type)
        elif isinstance(component_type, AutomationComponentType):
            return self.automation_criteria.get_automation_criteria(component_type)
        
        return None
    
    def _evaluate_criterion(self, component: Component, criterion: EvaluationCriterion) -> CriterionEvaluation:
        """Evaluate a single criterion against a component"""
        try:
            score, status, message = self._perform_criterion_validation(component, criterion)
            
            return CriterionEvaluation(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                status=status,
                score=score,
                weight=criterion.weight,
                required=criterion.is_critical,
                message=message,
                details={
                    "evaluation_method": criterion.evaluation_method,
                    "parameters": criterion.parameters
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
                required=criterion.is_critical,
                message=f"Evaluation error: {e}"
            )
    
    def _perform_criterion_validation(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Perform actual validation of a criterion"""
        try:
            # Route to appropriate validation method based on criterion type
            if criterion.criterion_type == CriterionType.EXISTENCE:
                return self._validate_existence(component, criterion)
            elif criterion.criterion_type == CriterionType.CONFIGURATION:
                return self._validate_configuration(component, criterion)
            elif criterion.criterion_type == CriterionType.FUNCTIONALITY:
                return self._validate_functionality(component, criterion)
            elif criterion.criterion_type == CriterionType.QUALITY:
                return self._validate_quality(component, criterion)
            elif criterion.criterion_type == CriterionType.INTEGRATION:
                return self._validate_integration(component, criterion)
            elif criterion.criterion_type == CriterionType.DEPLOYMENT:
                return self._validate_deployment(component, criterion)
            elif criterion.criterion_type == CriterionType.AUTOMATION:
                return self._validate_automation(component, criterion)
            else:
                # Default evaluation based on component status
                from ..models.data_models import ComponentStatus
                if component.status == ComponentStatus.OPERATIONAL:
                    return 0.8, EvaluationStatus.PASSED, "Component is operational"
                elif component.status == ComponentStatus.DEGRADED:
                    return 0.5, EvaluationStatus.WARNING, "Component is degraded"
                else:
                    return 0.2, EvaluationStatus.FAILED, "Component is not operational"
        
        except Exception as e:
            self.logger.error(f"Error validating criterion {criterion.id}: {e}")
            return 0.0, EvaluationStatus.FAILED, f"Validation error: {e}"
    
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
            # If no weights, use simple average
            return sum(ce.score for ce in criterion_evaluations) / len(criterion_evaluations)
        
        # Calculate weighted score
        weighted_score = sum(ce.score * ce.weight for ce in criterion_evaluations)
        base_score = weighted_score / total_weight
        
        # Apply penalties for critical failures
        critical_failures = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED and ce.required]
        if critical_failures:
            # Reduce score by 20% for each critical failure
            penalty = min(0.8, len(critical_failures) * 0.2)
            base_score *= (1.0 - penalty)
        
        # Apply bonus for high-performing criteria
        high_performers = [ce for ce in criterion_evaluations if ce.score >= 0.9]
        if len(high_performers) > len(criterion_evaluations) * 0.8:
            # Small bonus for consistently high performance
            base_score = min(1.0, base_score * 1.05)
        
        return max(0.0, min(1.0, base_score))
    
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
        
        # Critical issues first
        if not critical_passed:
            failed_critical = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED and ce.required]
            for ce in failed_critical:
                issues.append(f"CRITICAL: {ce.criterion_name} - {ce.message}")
        
        # Overall score issues
        if not meets_minimum:
            overall_score = self._calculate_overall_score(criterion_evaluations)
            issues.append(f"Component score ({overall_score:.1%}) below minimum threshold (70%)")
        
        # Specific criterion failures
        failed_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED and not ce.required]
        for ce in failed_criteria:
            issues.append(f"FAILED: {ce.criterion_name} - {ce.message}")
        
        # Warning criteria
        warning_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.WARNING]
        for ce in warning_criteria:
            issues.append(f"WARNING: {ce.criterion_name} - {ce.message}")
        
        # Performance issues
        low_score_criteria = [ce for ce in criterion_evaluations if ce.score < 0.5 and ce.status != EvaluationStatus.FAILED]
        for ce in low_score_criteria:
            issues.append(f"LOW SCORE: {ce.criterion_name} scored {ce.score:.1%}")
        
        return issues
    
    def _generate_recommendations(self, criterion_evaluations: List[CriterionEvaluation], criteria: List[EvaluationCriterion]) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        # Priority-based recommendations
        critical_failed = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED and ce.required]
        failed_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.FAILED and not ce.required]
        warning_criteria = [ce for ce in criterion_evaluations if ce.status == EvaluationStatus.WARNING]
        
        # Critical recommendations first
        for ce in critical_failed:
            recommendations.append(self._generate_specific_recommendation(ce, "CRITICAL"))
        
        # High-impact recommendations
        for ce in failed_criteria:
            if ce.weight >= 1.0:  # High-weight criteria
                recommendations.append(self._generate_specific_recommendation(ce, "HIGH"))
        
        # Medium-impact recommendations
        for ce in failed_criteria:
            if ce.weight < 1.0:
                recommendations.append(self._generate_specific_recommendation(ce, "MEDIUM"))
        
        # Improvement recommendations
        for ce in warning_criteria:
            recommendations.append(self._generate_specific_recommendation(ce, "IMPROVE"))
        
        # General recommendations based on overall score
        overall_score = self._calculate_overall_score(criterion_evaluations)
        if overall_score < 0.5:
            recommendations.append("Consider redesigning component architecture to meet basic requirements")
        elif overall_score < 0.8:
            recommendations.append("Focus on addressing failed criteria to improve component reliability")
        
        return recommendations
    
    def _generate_specific_recommendation(self, criterion_eval: CriterionEvaluation, priority: str) -> str:
        """Generate specific recommendation based on criterion evaluation"""
        parameters = criterion_eval.details.get("parameters", {})
        
        if "file_path" in parameters:
            file_path = parameters["file_path"]
            return f"[{priority}] Create missing file: {file_path} for {criterion_eval.criterion_name}"
        elif "directory_path" in parameters:
            dir_path = parameters["directory_path"]
            return f"[{priority}] Create missing directory: {dir_path} for {criterion_eval.criterion_name}"
        elif "hook_type" in parameters:
            hook_type = parameters["hook_type"]
            return f"[{priority}] Implement {hook_type} hook for {criterion_eval.criterion_name}"
        elif "integration_type" in parameters:
            integration_type = parameters["integration_type"]
            return f"[{priority}] Configure {integration_type} integration for {criterion_eval.criterion_name}"
        elif "environment" in parameters:
            environment = parameters["environment"]
            return f"[{priority}] Set up {environment} environment configuration for {criterion_eval.criterion_name}"
        else:
            return f"[{priority}] {criterion_eval.criterion_name}: {criterion_eval.message}"
    
    def _create_not_evaluated_result(self, component: Component, reason: str) -> ComponentEvaluation:
        """Create evaluation result for components that couldn't be evaluated"""
        return ComponentEvaluation(
            component=component,
            criteria_type="unknown",
            overall_score=0.0,
            completion_percentage=0.0,
            status=EvaluationStatus.NOT_EVALUATED,
            issues=[f"Component not evaluated: {reason}"],
            recommendations=[
                "Define appropriate evaluation criteria for this component",
                f"Verify component category ({component.category.value}) is correct",
                "Check if component path exists and is accessible"
            ]
        )
    
    def detect_component_issues(self, evaluation: ComponentEvaluation) -> Dict[str, List[str]]:
        """Detect and categorize specific types of issues in component evaluation"""
        issue_categories = {
            "configuration_issues": [],
            "missing_files": [],
            "integration_problems": [],
            "quality_issues": [],
            "deployment_issues": [],
            "automation_gaps": []
        }
        
        for criterion_eval in evaluation.criterion_evaluations:
            if criterion_eval.status in [EvaluationStatus.FAILED, EvaluationStatus.WARNING]:
                parameters = criterion_eval.details.get("parameters", {})
                
                # Categorize by criterion type
                if criterion_eval.details.get("evaluation_method") == "file_exists":
                    if "file_path" in parameters:
                        issue_categories["missing_files"].append(f"Missing file: {parameters['file_path']}")
                elif "configuration" in criterion_eval.criterion_name.lower():
                    issue_categories["configuration_issues"].append(criterion_eval.message)
                elif "integration" in criterion_eval.criterion_name.lower():
                    issue_categories["integration_problems"].append(criterion_eval.message)
                elif "quality" in criterion_eval.criterion_name.lower():
                    issue_categories["quality_issues"].append(criterion_eval.message)
                elif "deployment" in criterion_eval.criterion_name.lower():
                    issue_categories["deployment_issues"].append(criterion_eval.message)
                elif "automation" in criterion_eval.criterion_name.lower():
                    issue_categories["automation_gaps"].append(criterion_eval.message)
        
        # Remove empty categories
        return {k: v for k, v in issue_categories.items() if v}
    
    def calculate_completion_trend(self, evaluations: List[ComponentEvaluation]) -> Dict[str, Any]:
        """Calculate completion trends and identify patterns"""
        if not evaluations:
            return {"trend": "no_data", "patterns": []}
        
        # Calculate category performance
        category_scores = {}
        for evaluation in evaluations:
            category = evaluation.component.category.value
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(evaluation.completion_percentage)
        
        # Calculate averages and identify patterns
        patterns = []
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 50:
                patterns.append(f"{category} components significantly underperforming (avg: {avg_score:.1f}%)")
            elif avg_score > 90:
                patterns.append(f"{category} components performing excellently (avg: {avg_score:.1f}%)")
        
        # Overall trend
        overall_avg = sum(e.completion_percentage for e in evaluations) / len(evaluations)
        if overall_avg >= 80:
            trend = "excellent"
        elif overall_avg >= 60:
            trend = "good"
        elif overall_avg >= 40:
            trend = "needs_improvement"
        else:
            trend = "critical"
        
        return {
            "trend": trend,
            "overall_average": overall_avg,
            "category_averages": {k: sum(v)/len(v) for k, v in category_scores.items()},
            "patterns": patterns,
            "total_components": len(evaluations)
        }
    
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
 
    def _validate_existence(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate existence-based criteria (files, directories, etc.)"""
        parameters = criterion.parameters
        
        if "file_path" in parameters:
            file_path = self.project_root / parameters["file_path"]
            if file_path.exists():
                return 1.0, EvaluationStatus.PASSED, f"File {parameters['file_path']} exists"
            else:
                return 0.0, EvaluationStatus.FAILED, f"File {parameters['file_path']} not found"
        
        elif "directory_path" in parameters:
            dir_path = self.project_root / parameters["directory_path"]
            if dir_path.exists() and dir_path.is_dir():
                return 1.0, EvaluationStatus.PASSED, f"Directory {parameters['directory_path']} exists"
            else:
                return 0.0, EvaluationStatus.FAILED, f"Directory {parameters['directory_path']} not found"
        
        elif "file_paths" in parameters:
            # Check if any of the files exist
            found_files = []
            for file_path in parameters["file_paths"]:
                if (self.project_root / file_path).exists():
                    found_files.append(file_path)
            
            if found_files:
                return 1.0, EvaluationStatus.PASSED, f"Found files: {', '.join(found_files)}"
            else:
                return 0.0, EvaluationStatus.FAILED, "None of the required files found"
        
        return 0.5, EvaluationStatus.WARNING, "Existence check parameters not recognized"
    
    def _validate_configuration(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate configuration-based criteria"""
        parameters = criterion.parameters
        
        if "file_path" in parameters:
            file_path = self.project_root / parameters["file_path"]
            if not file_path.exists():
                return 0.0, EvaluationStatus.FAILED, f"Configuration file {parameters['file_path']} not found"
            
            try:
                # Try to parse the configuration file
                if file_path.suffix.lower() == '.json':
                    import json
                    with open(file_path, 'r') as f:
                        config = json.load(f)
                elif file_path.suffix.lower() in ['.yml', '.yaml']:
                    import yaml
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                else:
                    # For other files, just check if they're readable
                    with open(file_path, 'r') as f:
                        content = f.read()
                    return 0.8, EvaluationStatus.PASSED, f"Configuration file {parameters['file_path']} is readable"
                
                # Check for specific configuration keys if specified
                if "json_path" in parameters and "search_key" in parameters:
                    search_key = parameters["search_key"]
                    search_value = parameters.get("search_value")
                    
                    if isinstance(config, dict) and search_key in config:
                        if search_value is None or config[search_key] == search_value:
                            return 1.0, EvaluationStatus.PASSED, f"Configuration key '{search_key}' found with correct value"
                        else:
                            return 0.5, EvaluationStatus.WARNING, f"Configuration key '{search_key}' found but value doesn't match"
                    else:
                        return 0.0, EvaluationStatus.FAILED, f"Configuration key '{search_key}' not found"
                
                return 0.8, EvaluationStatus.PASSED, f"Configuration file {parameters['file_path']} is valid"
                
            except Exception as e:
                return 0.0, EvaluationStatus.FAILED, f"Configuration file parsing error: {e}"
        
        return 0.5, EvaluationStatus.WARNING, "Configuration check parameters not recognized"
    
    def _validate_functionality(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate functionality-based criteria"""
        parameters = criterion.parameters
        
        # Check for hook implementation
        if "hook_type" in parameters and "hooks_path" in parameters:
            hooks_path = self.project_root / parameters["hooks_path"]
            hook_type = parameters["hook_type"]
            
            if not hooks_path.exists():
                return 0.0, EvaluationStatus.FAILED, f"Hooks directory {parameters['hooks_path']} not found"
            
            # Look for hook files related to the hook type
            hook_files = list(hooks_path.rglob(f"*{hook_type}*"))
            if hook_files:
                return 1.0, EvaluationStatus.PASSED, f"Hook implementation found for {hook_type}"
            else:
                return 0.0, EvaluationStatus.FAILED, f"No hook implementation found for {hook_type}"
        
        # Default functionality check based on component status
        from ..models.data_models import ComponentStatus
        if component.status == ComponentStatus.OPERATIONAL:
            return 0.9, EvaluationStatus.PASSED, "Component functionality is operational"
        elif component.status == ComponentStatus.DEGRADED:
            return 0.6, EvaluationStatus.WARNING, "Component functionality is degraded"
        else:
            return 0.2, EvaluationStatus.FAILED, "Component functionality is not working"
    
    def _validate_quality(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate quality-based criteria"""
        parameters = criterion.parameters
        
        if "requirement" in parameters and "script_paths" in parameters:
            requirement = parameters["requirement"]
            script_paths = parameters["script_paths"]
            
            # Check for quality indicators in scripts
            quality_indicators = {
                "error_handling": ["try:", "except:", "catch", "error", "exception"],
                "logging": ["log", "logger", "print", "echo", "Write-Host"],
                "parameter_validation": ["param", "if", "test", "validate"],
                "rollback_capability": ["rollback", "undo", "revert", "backup"],
                "idempotent_operations": ["if exist", "if not", "test -f", "check"]
            }
            
            if requirement in quality_indicators:
                indicators = quality_indicators[requirement]
                found_indicators = 0
                total_scripts = 0
                
                for script_path in script_paths:
                    script_dir = self.project_root / script_path
                    if script_dir.exists():
                        for script_file in script_dir.rglob("*.ps1") or script_dir.rglob("*.sh"):
                            total_scripts += 1
                            try:
                                with open(script_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read().lower()
                                    if any(indicator in content for indicator in indicators):
                                        found_indicators += 1
                            except Exception:
                                continue
                
                if total_scripts == 0:
                    return 0.0, EvaluationStatus.FAILED, f"No scripts found in {script_paths}"
                
                score = found_indicators / total_scripts
                if score >= 0.8:
                    return score, EvaluationStatus.PASSED, f"{requirement} found in {found_indicators}/{total_scripts} scripts"
                elif score >= 0.5:
                    return score, EvaluationStatus.WARNING, f"{requirement} partially implemented in {found_indicators}/{total_scripts} scripts"
                else:
                    return score, EvaluationStatus.FAILED, f"{requirement} missing in most scripts ({found_indicators}/{total_scripts})"
        
        return 0.7, EvaluationStatus.WARNING, "Quality check not fully implemented"
    
    def _validate_integration(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate integration-based criteria"""
        parameters = criterion.parameters
        
        if "integration_type" in parameters and "check_files" in parameters:
            integration_type = parameters["integration_type"]
            check_files = parameters["check_files"]
            
            found_integrations = 0
            for file_path in check_files:
                path = self.project_root / file_path
                if path.exists():
                    found_integrations += 1
            
            score = found_integrations / len(check_files)
            if score >= 0.8:
                return score, EvaluationStatus.PASSED, f"{integration_type} integration files found"
            elif score >= 0.5:
                return score, EvaluationStatus.WARNING, f"{integration_type} integration partially configured"
            else:
                return score, EvaluationStatus.FAILED, f"{integration_type} integration not properly configured"
        
        return 0.6, EvaluationStatus.WARNING, "Integration check not fully implemented"
    
    def _validate_deployment(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate deployment-based criteria"""
        parameters = criterion.parameters
        
        if "environment" in parameters:
            environment = parameters["environment"]
            
            # Check for environment-specific configuration
            env_configs = [
                f"configs/{environment.lower()}.yml",
                f"configs/{environment.lower()}.yaml", 
                f"configs/{environment.lower()}.json",
                f".env.{environment.lower()}",
                f"docker-compose.{environment.lower()}.yml"
            ]
            
            found_configs = []
            for config_path in env_configs:
                if (self.project_root / config_path).exists():
                    found_configs.append(config_path)
            
            if found_configs:
                return 1.0, EvaluationStatus.PASSED, f"{environment} deployment configuration found: {', '.join(found_configs)}"
            else:
                return 0.0, EvaluationStatus.FAILED, f"No {environment} deployment configuration found"
        
        return 0.5, EvaluationStatus.WARNING, "Deployment check not fully implemented"
    
    def _validate_automation(self, component: Component, criterion: EvaluationCriterion) -> Tuple[float, EvaluationStatus, str]:
        """Validate automation-based criteria"""
        parameters = criterion.parameters
        
        if "feature" in parameters:
            feature = parameters["feature"]
            
            # Check for automation features
            automation_indicators = {
                "dependency_management": ["requirements.txt", "pyproject.toml", "package.json", "Pipfile"],
                "test_automation": ["pytest", "test", "spec", "unittest"],
                "artifact_generation": ["build", "dist", "target", "out"],
                "version_management": ["version", "tag", "release"],
                "health_checks": ["health", "ping", "status", "check"],
                "performance_monitoring": ["metrics", "monitor", "prometheus", "grafana"],
                "log_aggregation": ["logs", "logging", "syslog", "fluentd"],
                "alerting": ["alert", "notification", "webhook", "email"]
            }
            
            if feature in automation_indicators:
                indicators = automation_indicators[feature]
                found_indicators = 0
                
                # Check in project files
                for indicator in indicators:
                    # Check for files containing the indicator
                    matching_files = list(self.project_root.rglob(f"*{indicator}*"))
                    if matching_files:
                        found_indicators += 1
                
                score = found_indicators / len(indicators) if indicators else 0
                if score >= 0.6:
                    return score, EvaluationStatus.PASSED, f"{feature} automation indicators found"
                elif score >= 0.3:
                    return score, EvaluationStatus.WARNING, f"{feature} automation partially implemented"
                else:
                    return score, EvaluationStatus.FAILED, f"{feature} automation not found"
        
        return 0.5, EvaluationStatus.WARNING, "Automation check not fully implemented"