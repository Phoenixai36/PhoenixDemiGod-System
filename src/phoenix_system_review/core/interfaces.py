from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.data_models import (
    AssessmentResults,
    CompletionScore,
    Component,
    DependencyGraph,
    EvaluationResult,
    Gap,
    ProjectInventory,
    ServiceRegistry,
    TODOTask,
)
from .exceptions import (
    AnalysisError,
    AssessmentError,
    DiscoveryError,
    PhoenixSystemError,
)


class DiscoveryEngine(ABC):
    """
    Defines the interface for a discovery engine responsible for scanning
    and analyzing the project structure.
    """

    @abstractmethod
    def scan_project_structure(self, root_path: str) -> ProjectInventory:
        ...

    @abstractmethod
    def parse_configurations(
        self, config_files: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        ...

    @abstractmethod
    async def discover_services(self) -> ServiceRegistry:
        ...

    @abstractmethod
    def map_dependencies(self, components: List[Component]) -> DependencyGraph:
        ...


class AnalysisEngine(ABC):
    @abstractmethod
    async def evaluate_component(
        self, component: Component, criteria: Dict[str, Any]
    ) -> EvaluationResult:
        ...

    @abstractmethod
    def analyze_dependencies(
        self, component: Component, dependency_graph: DependencyGraph
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def assess_quality(self, component: Component) -> Dict[str, float]:
        ...

    @abstractmethod
    def validate_configuration(self, component: Component) -> List[str]:
        ...


class AssessmentEngine(ABC):
    @abstractmethod
    def identify_gaps(
        self, evaluation_results: List[EvaluationResult]
    ) -> List[Gap]:
        ...

    @abstractmethod
    def calculate_completion(
        self, evaluation_results: List[EvaluationResult]
    ) -> Dict[str, CompletionScore]:
        ...

    @abstractmethod
    def prioritize_tasks(self, gaps: List[Gap]) -> List[TODOTask]:
        ...

    @abstractmethod
    def assess_production_readiness(
        self, components: List[Component]
    ) -> Dict[str, Any]:
        ...


class ReportingEngine(ABC):
    @abstractmethod
    def generate_todo_checklist(
        self, prioritized_tasks: List[TODOTask]
    ) -> str:
        ...

    @abstractmethod
    def create_status_report(
        self, assessment_results: AssessmentResults
    ) -> str:
        ...

    @abstractmethod
    def generate_executive_summary(
        self, assessment_results: AssessmentResults
    ) -> str:
        ...

    @abstractmethod
    def provide_recommendations(
        self, gaps: List[Gap], priorities: List[TODOTask]
    ) -> List[str]:
        ...


class ComponentEvaluator(ABC):
    @abstractmethod
    def get_evaluation_criteria(
        self, component: Component
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def evaluate(self, component: Component) -> EvaluationResult:
        ...


class QualityAssessor(ABC):
    @abstractmethod
    def analyze_code_quality(self, file_path: str) -> Dict[str, float]:
        """Analyzes the quality of a given code file."""
        ...

    @abstractmethod
    def check_documentation_completeness(
        self, component: Component
    ) -> float:
        """Checks documentation completeness for a component."""
        ...

    @abstractmethod
    def assess_test_coverage(self, component: Component) -> float:
        """Assesses the test coverage for a component."""
        ...

    @abstractmethod
    def validate_configuration_files(self, config_files: List[str]) -> List[str]:
        """Validates a list of configuration files."""
        ...


class ServiceHealthChecker(ABC):
    """
    Defines the interface for a service health checker.
    """

    @abstractmethod
    def check_service_health(self, service_url: str) -> bool:
        ...

    @abstractmethod
    def get_service_metrics(self, service_url: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    def validate_service_configuration(
        self, service_config: Dict[str, Any]
    ) -> List[str]:
        ...


class ErrorHandler(ABC):
    @abstractmethod
    def handle_discovery_error(
        self, error: DiscoveryError, context: str
    ) -> Optional[Any]:
        ...

    @abstractmethod
    def handle_analysis_error(
        self, error: AnalysisError, component: Component
    ) -> Optional[EvaluationResult]:
        ...

    @abstractmethod
    def handle_assessment_error(
        self, error: AssessmentError, context: str
    ) -> Optional[Any]:
        ...

    @abstractmethod
    def log_error(
        self, error: PhoenixSystemError, context: str, severity: str
    ) -> None:
        ...


class ConfigurationManager(ABC):
    @abstractmethod
    def load_evaluation_criteria(
        self,
    ) -> Dict[str, Dict[str, Any]]:
        ...

    @abstractmethod
    def get_component_weights(self) -> Dict[str, float]:
        ...

    @abstractmethod
    def get_service_endpoints(self) -> Dict[str, str]:
        ...

    @abstractmethod
    def get_priority_rules(self) -> Dict[str, Any]:
        ...
