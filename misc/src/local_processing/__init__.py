"""
Local Processing Infrastructure for Phoenix Hydra

This package provides the complete infrastructure for offline AI processing,
including model management, connectivity detection, and fallback strategies.

Key Components:
- LocalModelManager: Manages local AI model storage and versioning
- OfflineDetector: Detects network connectivity and manages offline transitions
- FallbackManager: Handles fallback strategies when primary models fail
- LocalAIPipeline: Main processing pipeline orchestrating all components

Usage:
    from src.local_processing import create_local_pipeline, ProcessingRequest

    # Create and start pipeline
    pipeline = await create_local_pipeline()

    # Submit processing request
    request = ProcessingRequest(
        id="example_001",
        input_data="Analyze this system log",
        task_type="log_analysis"
    )

    result = await pipeline.submit_request(request)
"""

from .model_manager import LocalModelManager, ModelMetadata, ModelStatus
from .offline_detector import (
    ConnectivityStatus,
    FallbackManager,
    FallbackStrategy,
    LocalProcessingOrchestrator,
    OfflineDetector,
)
from .pipeline import (
    LocalAIPipeline,
    ProcessingMode,
    ProcessingRequest,
    ProcessingResult,
    create_local_pipeline,
    process_simple_request,
)

__all__ = [
    # Model Management
    "LocalModelManager",
    "ModelMetadata",
    "ModelStatus",
    # Offline Detection & Fallbacks
    "OfflineDetector",
    "FallbackManager",
    "LocalProcessingOrchestrator",
    "ConnectivityStatus",
    "FallbackStrategy",
    # Main Pipeline
    "LocalAIPipeline",
    "ProcessingRequest",
    "ProcessingResult",
    "ProcessingMode",
    "create_local_pipeline",
    "process_simple_request",
]

__version__ = "1.0.0"
