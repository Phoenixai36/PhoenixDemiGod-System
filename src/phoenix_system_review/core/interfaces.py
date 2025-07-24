"""
Core interfaces for Phoenix Hydra System Review Tool
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.data_models import (
    Component, EvaluationResult, Gap, TODOTask, ProjectInventory,
    ServiceRegistry, DependencyGraph, AssessmentResults, CompletionScore
)


class DiscoveryEngine(ABC):
    """Abstract interface for system discovery functionality"""
    
    @abstractmethod
    def scan_project_structure(self, root_path: str) -> ProjectInventory:
        """Scan project structure and return inventory of components"""
        pass
    
    @abstractmethod
    def parse_configurations(self, config_files: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse configuration files and return structured data"""
        pass
    
    @abstractmethod
    def discover_services(self) -> ServiceRegistry:
        """Discover running services and their health status"""
        pass
    
    @abstractmethod
    def map_dependencies(self, components: List[Component]) -> DependencyGraph:
        """Map dependencies between components"""
        pass


class AnalysisEngine(ABC):
    """Abstract interface for component analysis functionality"""
    
    @abstractmethod
    def evaluate_component(self, component: Component, criteria: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a component against specified criteria"""
        pass
    
    @abstractmethod
    def analyze_dependencies(self, component: Component, dependency_graph: DependencyGraph) -> Dict[str, Any]:
        """Analyze component dependencies and relationships"""
        pass
    
    @abstractmethod
    def assess_quality(self, component: Component) -> Dict[str, float]:
        """Assess code quality, documentation, and testing coverage"""
        pass
    
    @abstractmethod
    def validate_configuration(self, component: Component) -> List[str]:
        """Validate component configuration and return issues"""
        pass


class AssessmentEngine(ABC):
    """Abstract interface for gap analysis and completion assessment"""
    
    @abstractmethod
    def identify_gaps(self, evaluation_results: List[EvaluationResult]) -> List[Gap]:
        """Identify gaps between current state and completion targets"""
        pass
    
    @abstractmethod
    def calculate_completion(self, evaluation_results: List[EvaluationResult]) -> Dict[str, CompletionScore]:
        """Calculate completion percentages for components and overall system"""
        pass
    
    @abstractmethod
    def prioritize_tasks(self, gaps: List[Gap]) -> List[TODOTask]:
        """Convert gaps into prioritized tasks with effort estimates"""
        pass
    
    @abstractmethod
    def assess_production_readiness(self, components: List[Component]) -> Dict[str, Any]:
        """Assess overall production readiness of the system"""
        pass


class ReportingEngine(ABC):
    """Abstract interface for report generation and TODO checklist creation"""
    
    @abstractmethod
    def generate_todo_checklist(self, prioritized_tasks: List[TODOTask]) -> str:
        """Generate formatted TODO checklist from prioritized tasks"""
        pass
    
    @abstractmethod
    def create_status_report(self, assessment_results: AssessmentResults) -> str:
        """Create comprehensive status report"""
        pass
    
    @abstractmethod
    def generate_executive_summary(self, assessment_results: AssessmentResults) -> str:
        """Generate executive summary with key findings"""
        pass
    
    @abstractmethod
    def provide_recommendations(self, gaps: List[Gap], priorities: List[TODOTask]) -> List[str]:
        """Provide strategic recommendations based on analysis"""
        pass


class ComponentEvaluator(ABC):
    """Abstract interface for component-specific evaluation logic"""
    
    @abstractmethod
    def get_evaluation_criteria(self, component_type: str) -> Dict[str, Any]:
        """Get evaluation criteria for specific component type"""
        pass
    
    @abstractmethod
    def evaluate_infrastructure_component(self, component: Component) -> EvaluationResult:
        """Evaluate infrastructure components (NCA Toolkit, Podman, etc.)"""
        pass
    
    @abstractmethod
    def evaluate_monetization_component(self, component: Component) -> EvaluationResult:
        """Evaluate monetization components (affiliate programs, grants, etc.)"""
        pass
    
    @abstractmethod
    def evaluate_automation_component(self, component: Component) -> EvaluationResult:
        """Evaluate automation components (VS Code tasks, scripts, etc.)"""
        pass


class QualityAssessor(ABC):
    """Abstract interface for code quality and documentation assessment"""
    
    @abstractmethod
    def analyze_code_quality(self, file_path: str) -> Dict[str, float]:
        """Analyze code quality metrics for a file"""
        pass
    
    @abstractmethod
    def check_documentation_completeness(self, component: Component) -> float:
        """Check documentation completeness for a component"""
        pass
    
    @abstractmethod
    def assess_test_coverage(self, component: Component) -> float:
        """Assess test coverage for a component"""
        pass
    
    @abstractmethod
    def validate_configuration_files(self, config_files: List[str]) -> List[str]:
        """Validate configuration files and return issues"""
        pass


class ServiceHealthChecker(ABC):
    """Abstract interface for service health checking"""
    
    @abstractmethod
    def check_service_health(self, service_url: str) -> bool:
        """Check if a service is healthy and responding"""
        pass
    
    @abstractmethod
    def get_service_metrics(self, service_url: str) -> Dict[str, Any]:
        """Get performance metrics for a service"""
        pass
    
    @abstractmethod
    def validate_service_configuration(self, service_config: Dict[str, Any]) -> List[str]:
        """Validate service configuration"""
        pass


class ErrorHandler(ABC):
    """Abstract interface for error handling and recovery"""
    
    @abstractmethod
    def handle_discovery_error(self, error: Exception, context: str) -> Optional[Any]:
        """Handle errors during discovery phase"""
        pass
    
    @abstractmethod
    def handle_analysis_error(self, error: Exception, component: Component) -> Optional[EvaluationResult]:
        """Handle errors during analysis phase"""
        pass
    
    @abstractmethod
    def handle_assessment_error(self, error: Exception, context: str) -> Optional[Any]:
        """Handle errors during assessment phase"""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: str, severity: str) -> None:
        """Log error with context and severity"""
        pass


class ConfigurationManager(ABC):
    """Abstract interface for configuration management"""
    
    @abstractmethod
    def load_evaluation_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Load evaluation criteria from configuration"""
        pass
    
    @abstractmethod
    def get_component_weights(self) -> Dict[str, float]:
        """Get component weights for completion calculation"""
        pass
    
    @abstractmethod
    def get_service_endpoints(self) -> Dict[str, str]:
        """Get service endpoints for health checking"""
        pass
    
    @abstractmethod
    def get_priority_rules(self) -> Dict[str, Any]:
        """Get rules for task prioritization"""
        pass