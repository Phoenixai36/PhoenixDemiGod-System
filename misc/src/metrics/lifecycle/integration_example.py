"""
Integration example for container lifecycle metrics.

This module demonstrates how to use the container lifecycle metrics collector
in a real application.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from ..models import CollectorConfig
from ..collector_factory import create_collector_builder
from .container_lifecycle_collector import ContainerLifecycleMetricsCollector


async def lifecycle_metrics_example():
    """Example of using the container lifecycle metrics collector."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create collector configuration
    config = CollectorConfig(
        name="container_lifecycle_metrics",
        enabled=True,
        collection_interval=30,
        timeout=10,
        parameters={
            "restart_analysis_hours": 1,
            "uptime_tracking_days": 7,
            "max_history_size": 1000
        }
    )
    
    # Create collector using builder pattern
    collector = create_collector_builder() \
        .name("container_lifecycle_metrics") \
        .enabled(True) \
        .interval(30) \
        .timeout(10) \
        .parameters({
            "restart_analysis_hours": 1,
            "uptime_tracking_days": 7,
            "max_history_size": 1000
        }) \
        .build("container_lifecycle")
    
    if not collector:
        logging.error("Failed to create collector")
        return
    
    # Initialize collector
    success = await collector.initialize()
    if not success:
        logging.error("Failed to initialize collector")
        return
    
    try:
        # Register callback for lifecycle events
        def lifecycle_callback(event_type, data):
            logging.info(f"Lifecycle event: {event_type} - {data}")
        
        collector.lifecycle_manager.add_lifecycle_callback(lifecycle_callback)
        
        # Collect metrics periodically
        for _ in range(5):  # Collect 5 times
            # Get all running containers
            running_containers = collector.get_running_containers()
            logging.info(f"Running containers: {len(running_containers)}")
            
            # Collect metrics for each container
            for container in running_containers:
                container_id = container.container_id
                metrics = await collector.collect_container_metrics(container_id)
                logging.info(f"Collected {len(metrics)} metrics for container {container_id}")
                
                # Print metric values
                for metric in metrics:
                    logging.info(f"  {metric.name}: {metric.value} {metric.unit or ''}")
            
            # Get lifecycle summary
            summary = collector.get_lifecycle_summary()
            logging.info(f"Lifecycle summary: {summary}")
            
            # Check for restart loops
            restart_loops = collector.get_restart_loops()
            if restart_loops:
                logging.warning(f"Found {len(restart_loops)} containers in restart loops")
                for loop in restart_loops:
                    logging.warning(f"  {loop.container_name}: {loop.restart_count} restarts")
            
            # Wait for next collection interval
            await asyncio.sleep(collector.config.collection_interval)
    
    finally:
        # Clean up
        await collector.cleanup()
        logging.info("Collector cleaned up")


if __name__ == "__main__":
    asyncio.run(lifecycle_metrics_example())