"""
Local AI Processing Pipeline

This module provides the main pipeline for completely offline AI processing,
integrating model management, offline detection, and processing orchestration.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .model_manager import LocalModelManager, ModelMetadata, ModelStatus
from .offline_detector import ConnectivityStatus, LocalProcessingOrchestrator

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """AI processing modes."""

    FULL_CAPABILITY = "full_capability"
    ENERGY_EFFICIENT = "energy_efficient"
    MINIMAL_RESOURCES = "minimal_resources"
    OFFLINE_ONLY = "offline_only"


@dataclass
class ProcessingRequest:
    """Request for AI processing."""

    id: str
    input_data: Any
    task_type: str  # "analysis", "generation", "classification", etc.
    model_preference: Optional[str] = None
    mode: ProcessingMode = ProcessingMode.FULL_CAPABILITY
    max_processing_time: float = 30.0
    energy_budget: Optional[float] = None  # Joules
    metadata: Dict[str, Any] = None


@dataclass
class ProcessingResult:
    """Result from AI processing."""

    request_id: str
    success: bool
    result: Any
    model_used: str
    processing_time: float
    energy_consumed: Optional[float] = None
    fallback_used: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class LocalAIPipeline:
    """
    Main pipeline for local AI processing with zero cloud dependencies.

    This class orchestrates the entire local AI processing workflow,
    from request intake to result delivery, with intelligent resource
    management and fallback handling.
    """

    def __init__(self, config_dir: Path = Path("config")):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize core components
        self.orchestrator = LocalProcessingOrchestrator()
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.active_requests: Dict[str, ProcessingRequest] = {}
        self.request_callbacks: Dict[str, Callable] = {}

        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "total_energy_consumed": 0.0,
            "fallback_usage_rate": 0.0,
        }

        # Processing modes configuration
        self.mode_configs = {
            ProcessingMode.FULL_CAPABILITY: {
                "max_model_size_mb": 8192,
                "max_processing_time": 60.0,
                "energy_limit_joules": None,
                "quality_threshold": 0.95,
            },
            ProcessingMode.ENERGY_EFFICIENT: {
                "max_model_size_mb": 2048,
                "max_processing_time": 30.0,
                "energy_limit_joules": 10.0,
                "quality_threshold": 0.85,
            },
            ProcessingMode.MINIMAL_RESOURCES: {
                "max_model_size_mb": 512,
                "max_processing_time": 15.0,
                "energy_limit_joules": 5.0,
                "quality_threshold": 0.70,
            },
            ProcessingMode.OFFLINE_ONLY: {
                "max_model_size_mb": 1024,
                "max_processing_time": 45.0,
                "energy_limit_joules": 8.0,
                "quality_threshold": 0.80,
                "require_offline": True,
            },
        }

    async def start(self):
        """Start the local AI processing pipeline."""
        logger.info("Starting Local AI Processing Pipeline")

        # Start the orchestrator
        await self.orchestrator.start()

        # Start the processing worker
        asyncio.create_task(self._processing_worker())

        logger.info("Local AI Processing Pipeline started successfully")

    async def submit_request(
        self, request: ProcessingRequest, callback: Optional[Callable] = None
    ) -> str:
        """
        Submit a processing request to the pipeline.

        Args:
            request: The processing request
            callback: Optional callback for result notification

        Returns:
            Request ID for tracking
        """
        # Validate request
        if not self._validate_request(request):
            raise ValueError(f"Invalid processing request: {request.id}")

        # Store request and callback
        self.active_requests[request.id] = request
        if callback:
            self.request_callbacks[request.id] = callback

        # Add to processing queue
        await self.processing_queue.put(request)

        logger.info(f"Submitted processing request: {request.id}")
        return request.id

    async def get_result(
        self, request_id: str, timeout: float = 60.0
    ) -> Optional[ProcessingResult]:
        """
        Get the result of a processing request.

        Args:
            request_id: The request ID
            timeout: Maximum time to wait for result

        Returns:
            ProcessingResult or None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if request is still active
            if request_id not in self.active_requests:
                # Request completed, but we need to return the result
                # In a real implementation, results would be stored
                logger.warning(f"Request {request_id} completed but result not found")
                return None

            await asyncio.sleep(0.1)

        logger.warning(f"Timeout waiting for result: {request_id}")
        return None

    async def _processing_worker(self):
        """Main processing worker that handles queued requests."""
        logger.info("Starting processing worker")

        while True:
            try:
                # Get next request from queue
                request = await self.processing_queue.get()

                # Process the request
                result = await self._process_request(request)

                # Handle result
                await self._handle_result(request, result)

                # Mark task as done
                self.processing_queue.task_done()

            except Exception as e:
                logger.error(f"Error in processing worker: {e}")
                await asyncio.sleep(1.0)

    async def _process_request(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Process a single AI request.

        Args:
            request: The processing request

        Returns:
            ProcessingResult with outcome
        """
        start_time = time.time()

        try:
            # Check processing mode constraints
            mode_config = self.mode_configs[request.mode]

            # Verify offline requirements
            if mode_config.get("require_offline", False):
                if not self.orchestrator.offline_detector.is_offline():
                    return ProcessingResult(
                        request_id=request.id,
                        success=False,
                        result=None,
                        model_used="none",
                        processing_time=time.time() - start_time,
                        error_message="Offline mode required but system is online",
                    )

            # Select appropriate model based on mode
            model_name = await self._select_model_for_request(request, mode_config)
            if not model_name:
                return ProcessingResult(
                    request_id=request.id,
                    success=False,
                    result=None,
                    model_used="none",
                    processing_time=time.time() - start_time,
                    error_message="No suitable model available for request",
                )

            # Prepare processing context
            processing_context = {
                "id": request.id,
                "model": model_name,
                "input": request.input_data,
                "task_type": request.task_type,
                "mode": request.mode.value,
                "max_time": min(
                    request.max_processing_time, mode_config["max_processing_time"]
                ),
            }

            # Process with orchestrator
            orchestrator_result = await self.orchestrator.process_request(
                processing_context
            )

            processing_time = time.time() - start_time

            if orchestrator_result["success"]:
                # Update metrics
                self._update_metrics(
                    True,
                    processing_time,
                    orchestrator_result.get("fallback_used", False),
                )

                return ProcessingResult(
                    request_id=request.id,
                    success=True,
                    result=orchestrator_result["result"],
                    model_used=orchestrator_result["model_used"],
                    processing_time=processing_time,
                    fallback_used=orchestrator_result["fallback_used"],
                    metadata={
                        "connectivity_status": orchestrator_result[
                            "connectivity_status"
                        ],
                        "mode": request.mode.value,
                    },
                )
            else:
                # Update metrics
                self._update_metrics(False, processing_time, False)

                return ProcessingResult(
                    request_id=request.id,
                    success=False,
                    result=None,
                    model_used="none",
                    processing_time=processing_time,
                    error_message=orchestrator_result.get(
                        "error", "Unknown processing error"
                    ),
                )

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_metrics(False, processing_time, False)

            logger.error(f"Request processing failed: {e}")
            return ProcessingResult(
                request_id=request.id,
                success=False,
                result=None,
                model_used="none",
                processing_time=processing_time,
                error_message=str(e),
            )

    async def _select_model_for_request(
        self, request: ProcessingRequest, mode_config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Select the most appropriate model for a request based on mode constraints.

        Args:
            request: The processing request
            mode_config: Configuration for the processing mode

        Returns:
            Model name or None if no suitable model
        """
        # If specific model requested, check if it meets constraints
        if request.model_preference:
            model_metadata = self.orchestrator.model_manager.get_model_metadata(
                request.model_preference
            )
            if model_metadata and self._model_meets_constraints(
                model_metadata, mode_config
            ):
                return request.model_preference

        # Find best model for task type and constraints
        available_models = self.orchestrator.model_manager.list_models()
        suitable_models = []

        for model in available_models:
            if model.status == ModelStatus.AVAILABLE and self._model_meets_constraints(
                model, mode_config
            ):
                suitable_models.append(model)

        if not suitable_models:
            return None

        # Sort by performance and size (prefer better performance, smaller size)
        suitable_models.sort(
            key=lambda m: (
                -m.performance_profile.get("quality_score", 0.5),
                m.size_bytes,
            )
        )

        return suitable_models[0].name

    def _model_meets_constraints(
        self, model: ModelMetadata, mode_config: Dict[str, Any]
    ) -> bool:
        """Check if a model meets the constraints for a processing mode."""
        # Size constraint
        max_size_bytes = mode_config["max_model_size_mb"] * 1024 * 1024
        if model.size_bytes > max_size_bytes:
            return False

        # Quality threshold
        quality_score = model.performance_profile.get("quality_score", 0.0)
        if quality_score < mode_config["quality_threshold"]:
            return False

        return True

    async def _handle_result(
        self, request: ProcessingRequest, result: ProcessingResult
    ):
        """Handle the result of a processed request."""
        # Remove from active requests
        if request.id in self.active_requests:
            del self.active_requests[request.id]

        # Call callback if registered
        if request.id in self.request_callbacks:
            callback = self.request_callbacks[request.id]
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Error in result callback: {e}")
            finally:
                del self.request_callbacks[request.id]

        # Log result
        if result.success:
            logger.info(
                f"Request {request.id} completed successfully in {result.processing_time:.2f}s"
            )
        else:
            logger.warning(f"Request {request.id} failed: {result.error_message}")

    def _validate_request(self, request: ProcessingRequest) -> bool:
        """Validate a processing request."""
        if not request.id:
            return False

        if not request.task_type:
            return False

        if request.max_processing_time <= 0:
            return False

        return True

    def _update_metrics(
        self, success: bool, processing_time: float, fallback_used: bool
    ):
        """Update performance metrics."""
        self.performance_metrics["total_requests"] += 1

        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1

        # Update average processing time
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_processing_time"]
        self.performance_metrics["average_processing_time"] = (
            current_avg * (total_requests - 1) + processing_time
        ) / total_requests

        # Update fallback usage rate
        if fallback_used:
            current_fallback_rate = self.performance_metrics["fallback_usage_rate"]
            self.performance_metrics["fallback_usage_rate"] = (
                current_fallback_rate * (total_requests - 1) + 1.0
            ) / total_requests

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        orchestrator_status = self.orchestrator.get_system_status()

        return {
            **orchestrator_status,
            "active_requests": len(self.active_requests),
            "queue_size": self.processing_queue.qsize(),
            "performance_metrics": self.get_performance_metrics(),
        }

    async def shutdown(self):
        """Gracefully shutdown the pipeline."""
        logger.info("Shutting down Local AI Processing Pipeline")

        # Wait for queue to empty
        await self.processing_queue.join()

        # Cancel any remaining requests
        for request_id in list(self.active_requests.keys()):
            del self.active_requests[request_id]
            if request_id in self.request_callbacks:
                del self.request_callbacks[request_id]

        logger.info("Local AI Processing Pipeline shutdown complete")


# Convenience functions for easy integration


async def create_local_pipeline(config_dir: Path = Path("config")) -> LocalAIPipeline:
    """Create and start a local AI processing pipeline."""
    pipeline = LocalAIPipeline(config_dir)
    await pipeline.start()
    return pipeline


async def process_simple_request(
    pipeline: LocalAIPipeline, input_data: Any, task_type: str, timeout: float = 30.0
) -> Optional[ProcessingResult]:
    """
    Process a simple request synchronously.

    Args:
        pipeline: The processing pipeline
        input_data: Input data for processing
        task_type: Type of processing task
        timeout: Maximum time to wait

    Returns:
        ProcessingResult or None if failed
    """
    request = ProcessingRequest(
        id=f"simple_{int(time.time())}",
        input_data=input_data,
        task_type=task_type,
        max_processing_time=timeout,
    )

    request_id = await pipeline.submit_request(request)
    return await pipeline.get_result(request_id, timeout)
