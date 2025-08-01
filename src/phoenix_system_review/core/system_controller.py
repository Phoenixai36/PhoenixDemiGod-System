"""
System Controller module for Phoenix Hydra system review.

This module provides the main orchestration logic for discovering, analyzing,
and evaluating system components, adhering to the defined core interfaces.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Awaitable, Callable, List, Optional, TypeVar

from ..models.data_models import (
    AssessmentResults,
    Component,
    DependencyGraph,
    EvaluationResult,
    ServiceRegistry,
)
from .interfaces import AnalysisEngine, ConfigurationManager, DiscoveryEngine

# --- Enhanced Utilities ---

T = TypeVar("T")


def retry_on_failure(
    _func: Optional[Callable[..., Awaitable[T]]] = None,
    *,
    retries: int = 3,
    delay: float = 1.0,
) -> Any:
    """
    A decorator to add robust retry logic to an async function.

    Args:
        _func: The function to be decorated (passed automatically).
        retries: The maximum number of attempts.
        delay: The delay in seconds between retries.

    Returns:
        The decorated function or a decorator instance.
    """

    def decorator(
        func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            """Wrapper function that implements the retry logic."""
            last_exception: Optional[Exception] = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except (OSError, asyncio.TimeoutError) as e:
                    last_exception = e
                    logging.warning(
                        "Attempt %d/%d failed for '%s' due to %s: %s",
                        attempt + 1,
                        retries,
                        func.__name__,
                        type(e).__name__,
                        str(e),
                    )
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)

            if last_exception is not None:
                logging.error(
                    "Function '%s' failed permanently after %d retries.",
                    func.__name__,
                    retries,
                )
                raise last_exception from last_exception

            # This path should be theoretically unreachable if retries > 0.
            raise RuntimeError(
                f"Function {func.__name__} failed after {retries} attempts "
                "without exception."
            )

        return wrapper

    if _func is None:
        return decorator
    return decorator(_func)


# --- Main Implementation ---


class SystemController:
    """
    Orchestrates the discovery, dependency mapping, and evaluation of system
    components by leveraging specialized engines.

    This controller coordinates the high-level review process by delegating
    tasks to injected engine implementations, ensuring testability and
    separation of concerns.
    """

    def __init__(
        self,
        discovery_engine: DiscoveryEngine,
        analysis_engine: AnalysisEngine,
        config_manager: ConfigurationManager,
    ):
        """
        Initializes the SystemController with its dependencies.

        Args:
            discovery_engine: An engine for discovering services and
                dependencies.
            analysis_engine: An engine for evaluating components.
            config_manager: A manager for handling configuration.
        """
        dependencies = (discovery_engine, analysis_engine, config_manager)
        if not all(dependencies):
            raise ValueError(
                "All engine and manager dependencies must be provided."
            )

        self.discovery_engine = discovery_engine
        self.analysis_engine = analysis_engine
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    @retry_on_failure
    async def discover_components(self) -> ServiceRegistry:
        """
        Discovers all available system components using the discovery engine.

        Returns:
            A ServiceRegistry instance containing all discovered components.
        """
        self.logger.info("Initiating component discovery...")
        registry = await self.discovery_engine.discover_services()
        self.logger.info(
            "Component discovery completed. Found %d services.",
            registry.service_count,
        )
        return registry

    def map_dependencies(self, components: List[Component]) -> DependencyGraph:
        """
        Maps dependencies between components using the discovery engine.

        Args:
            components: A list of components to analyze for dependencies.

        Returns:
            A DependencyGraph instance representing component relationships.
        """
        self.logger.info(
            "Mapping dependencies for %d components...",
            len(components),
        )
        dependency_graph = self.discovery_engine.map_dependencies(
            components
        )
        self.logger.info("Dependency mapping completed.")
        return dependency_graph

    @retry_on_failure
    async def evaluate_component(
        self, component: Component
    ) -> EvaluationResult:
        """Evaluates a single component using the analysis engine.

        Args:
            component: The component to evaluate.

        Returns:
            An EvaluationResult for the component.
        """
        self.logger.debug("Evaluating component '%s'...", component.name)
        all_criteria = self.config_manager.load_evaluation_criteria()
        criteria = all_criteria.get(component.component_type, {})
        return await self.analysis_engine.evaluate_component(
            component, criteria
        )

    async def run_system_review(self) -> AssessmentResults:
        """
        Executes the full system review workflow.

        Steps:
        1. Discovers all system components.
        2. Maps dependencies between them.
        3. Evaluates all components concurrently.
        4. Returns a summary of the results.

        Returns:
            An AssessmentResults object containing the review summary.
        """
        self.logger.info("--- Starting System Review ---")
        try:
            # 1. Discovery
            service_registry = await self.discover_components()
            components = service_registry.get_components()
            if not components:
                self.logger.warning(
                    "No components discovered. Finalizing review."
                )
                return AssessmentResults(
                    summary="No components found.",
                    results=[],
                    dependency_graph=DependencyGraph(),
                )

            # 2. Dependency Mapping
            dependency_graph = self.map_dependencies(components)

            # 3. Concurrent Evaluation
            self.logger.info(
                "Starting concurrent evaluation of %d components...",
                len(components),
            )
            evaluation_tasks = [self.evaluate_component(c) for c in components]
            evaluation_results = await asyncio.gather(*evaluation_tasks)
            self.logger.info("All components evaluated.")

            # 4. Return Summary
            summary_text = (
                f"Review complete. Evaluated {len(evaluation_results)} "
                "components."
            )
            results = AssessmentResults(
                summary=summary_text,
                results=evaluation_results,
                dependency_graph=dependency_graph,
            )
            self.logger.info("--- System Review Finished ---")
            return results

        except Exception as e:
            self.logger.error(
                "A critical error occurred during the system review: %s",
                str(e),
                exc_info=True,
            )
            # Re-throw to signal a catastrophic failure.
            raise
