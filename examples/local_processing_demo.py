#!/usr/bin/env python3
"""
Local Processing Infrastructure Demo

This script demonstrates the Phoenix Hydra local processing infrastructure,
showing how to set up offline AI processing with automatic fallbacks.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.local_processing import (
    ModelMetadata,
    ModelStatus,
    ProcessingMode,
    ProcessingRequest,
    create_local_pipeline,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def setup_demo_models(pipeline):
    """Set up some demo models for testing."""
    logger.info("Setting up demo models...")

    # Create demo model metadata
    demo_models = [
        ModelMetadata(
            name="phoenix-ssm-default",
            version="1.0.0",
            model_type="mamba",
            file_path="models/phoenix-ssm-default-1.0.0/model.bin",
            checksum="abc123def456",
            size_bytes=2048 * 1024 * 1024,  # 2GB
            performance_profile={
                "quality_score": 0.95,
                "inference_speed_ms": 150,
                "energy_efficiency": 0.8,
            },
            dependencies=["numpy", "torch"],
            created_at=datetime.now(),
            status=ModelStatus.AVAILABLE,
        ),
        ModelMetadata(
            name="phoenix-ssm-lite",
            version="1.0.0",
            model_type="mamba",
            file_path="models/phoenix-ssm-lite-1.0.0/model.bin",
            checksum="def456ghi789",
            size_bytes=512 * 1024 * 1024,  # 512MB
            performance_profile={
                "quality_score": 0.75,
                "inference_speed_ms": 80,
                "energy_efficiency": 0.9,
            },
            dependencies=["numpy"],
            created_at=datetime.now(),
            status=ModelStatus.AVAILABLE,
        ),
        ModelMetadata(
            name="phoenix-ssm-backup",
            version="1.0.0",
            model_type="mamba",
            file_path="models/phoenix-ssm-backup-1.0.0/model.bin",
            checksum="ghi789jkl012",
            size_bytes=256 * 1024 * 1024,  # 256MB
            performance_profile={
                "quality_score": 0.65,
                "inference_speed_ms": 50,
                "energy_efficiency": 0.95,
            },
            dependencies=[],
            created_at=datetime.now(),
            status=ModelStatus.AVAILABLE,
        ),
    ]

    # Register models (in a real scenario, these would be actual model files)
    for model in demo_models:
        # Create dummy model file for demo
        model_path = Path(model.file_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(f"Demo model: {model.name}")

        # Update checksum for demo file
        import hashlib

        model.checksum = hashlib.sha256(model_path.read_bytes()).hexdigest()

        # Register with model manager
        success = pipeline.orchestrator.model_manager.register_model(model_path, model)
        if success:
            logger.info(f"Registered demo model: {model.name}")
        else:
            logger.warning(f"Failed to register demo model: {model.name}")


async def demo_basic_processing(pipeline):
    """Demonstrate basic processing capabilities."""
    logger.info("\n=== Demo: Basic Processing ===")

    # Create a simple processing request
    request = ProcessingRequest(
        id="demo_basic_001",
        input_data="Analyze the Phoenix Hydra system architecture",
        task_type="system_analysis",
        mode=ProcessingMode.FULL_CAPABILITY,
    )

    logger.info(f"Submitting request: {request.id}")

    # Submit and wait for result
    request_id = await pipeline.submit_request(request)
    result = await pipeline.get_result(request_id, timeout=10.0)

    if result:
        logger.info(f"Request completed successfully!")
        logger.info(f"  Model used: {result.model_used}")
        logger.info(f"  Processing time: {result.processing_time:.2f}s")
        logger.info(f"  Fallback used: {result.fallback_used}")
        logger.info(f"  Result: {result.result}")
    else:
        logger.error("Request failed or timed out")


async def demo_energy_efficient_mode(pipeline):
    """Demonstrate energy-efficient processing mode."""
    logger.info("\n=== Demo: Energy Efficient Mode ===")

    request = ProcessingRequest(
        id="demo_energy_001",
        input_data="Perform lightweight log analysis",
        task_type="log_analysis",
        mode=ProcessingMode.ENERGY_EFFICIENT,
        energy_budget=5.0,  # 5 joules max
    )

    logger.info(f"Submitting energy-efficient request: {request.id}")

    request_id = await pipeline.submit_request(request)
    result = await pipeline.get_result(request_id, timeout=10.0)

    if result:
        logger.info(f"Energy-efficient processing completed!")
        logger.info(f"  Model used: {result.model_used}")
        logger.info(f"  Processing time: {result.processing_time:.2f}s")
        logger.info(f"  Energy consumed: {result.energy_consumed} joules")
    else:
        logger.error("Energy-efficient request failed")


async def demo_minimal_resources_mode(pipeline):
    """Demonstrate minimal resources processing mode."""
    logger.info("\n=== Demo: Minimal Resources Mode ===")

    request = ProcessingRequest(
        id="demo_minimal_001",
        input_data="Quick status check",
        task_type="status_check",
        mode=ProcessingMode.MINIMAL_RESOURCES,
        max_processing_time=5.0,
    )

    logger.info(f"Submitting minimal resources request: {request.id}")

    request_id = await pipeline.submit_request(request)
    result = await pipeline.get_result(request_id, timeout=10.0)

    if result:
        logger.info(f"Minimal resources processing completed!")
        logger.info(f"  Model used: {result.model_used}")
        logger.info(f"  Processing time: {result.processing_time:.2f}s")
        logger.info(f"  Fallback used: {result.fallback_used}")
    else:
        logger.error("Minimal resources request failed")


async def demo_connectivity_status(pipeline):
    """Demonstrate connectivity status monitoring."""
    logger.info("\n=== Demo: Connectivity Status ===")

    detector = pipeline.orchestrator.offline_detector

    logger.info(f"Current connectivity status: {detector.get_current_status().value}")

    # Perform a manual connectivity check
    logger.info("Performing connectivity check...")
    status = await detector._perform_connectivity_check()
    logger.info(f"Connectivity check result: {status.value}")

    # Show connectivity history
    history = detector.get_connectivity_history()
    if history:
        logger.info("Recent connectivity history:")
        for timestamp, status in history[-5:]:  # Last 5 entries
            logger.info(f"  {datetime.fromtimestamp(timestamp)}: {status.value}")
    else:
        logger.info("No connectivity history available yet")


async def demo_system_status(pipeline):
    """Demonstrate system status reporting."""
    logger.info("\n=== Demo: System Status ===")

    status = pipeline.get_system_status()

    logger.info("Current system status:")
    logger.info(f"  Connectivity: {status['connectivity']}")
    logger.info(f"  Loaded models: {status['loaded_models']}")
    logger.info(f"  Total models: {status['total_models']}")
    logger.info(f"  Active requests: {status['active_requests']}")
    logger.info(f"  Queue size: {status['queue_size']}")

    metrics = status["performance_metrics"]
    logger.info("Performance metrics:")
    logger.info(f"  Total requests: {metrics['total_requests']}")
    logger.info(
        f"  Success rate: {metrics['successful_requests']}/{metrics['total_requests']}"
    )
    logger.info(f"  Average processing time: {metrics['average_processing_time']:.2f}s")
    logger.info(f"  Fallback usage rate: {metrics['fallback_usage_rate']:.2%}")


async def demo_concurrent_processing(pipeline):
    """Demonstrate concurrent processing capabilities."""
    logger.info("\n=== Demo: Concurrent Processing ===")

    # Create multiple requests
    requests = []
    for i in range(5):
        request = ProcessingRequest(
            id=f"demo_concurrent_{i:03d}",
            input_data=f"Process batch item {i}",
            task_type="batch_processing",
            mode=ProcessingMode.ENERGY_EFFICIENT,
        )
        requests.append(request)

    logger.info(f"Submitting {len(requests)} concurrent requests...")

    # Submit all requests
    request_ids = []
    for request in requests:
        request_id = await pipeline.submit_request(request)
        request_ids.append(request_id)

    # Wait for all results
    results = []
    for request_id in request_ids:
        result = await pipeline.get_result(request_id, timeout=15.0)
        results.append(result)

    # Report results
    successful = sum(1 for r in results if r and r.success)
    total_time = sum(r.processing_time for r in results if r)

    logger.info(f"Concurrent processing completed!")
    logger.info(f"  Successful requests: {successful}/{len(requests)}")
    logger.info(f"  Total processing time: {total_time:.2f}s")
    logger.info(f"  Average per request: {total_time/len(requests):.2f}s")


async def main():
    """Main demo function."""
    logger.info("Starting Phoenix Hydra Local Processing Infrastructure Demo")

    try:
        # Create and start the pipeline
        logger.info("Creating local processing pipeline...")
        pipeline = await create_local_pipeline()

        # Set up demo models
        await setup_demo_models(pipeline)

        # Wait a moment for initialization
        await asyncio.sleep(1.0)

        # Run demonstrations
        await demo_basic_processing(pipeline)
        await demo_energy_efficient_mode(pipeline)
        await demo_minimal_resources_mode(pipeline)
        await demo_connectivity_status(pipeline)
        await demo_concurrent_processing(pipeline)
        await demo_system_status(pipeline)

        logger.info("\n=== Demo Complete ===")
        logger.info("Local processing infrastructure is working correctly!")

        # Shutdown gracefully
        await pipeline.shutdown()

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
