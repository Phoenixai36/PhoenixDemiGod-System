"""
Integration example for metrics storage and retrieval system.

This module demonstrates how to use the metrics storage system
in a real application.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import random
import os

from ..models import MetricValue
from .metrics_storage_system import MetricsStorageSystem, create_metrics_storage_system


async def generate_sample_metrics(count: int = 100):
    """Generate sample metrics for testing."""
    metrics = []
    now = datetime.now()
    
    # Generate CPU metrics
    for i in range(count):
        timestamp = now - timedelta(minutes=i)
        
        # CPU metrics for different containers
        for container_id in ["container_1", "container_2", "container_3"]:
            metrics.append(MetricValue(
                name="container_cpu_usage_percent",
                value=random.uniform(0, 100),
                timestamp=timestamp,
                labels={
                    "container_id": container_id,
                    "host": "host_1"
                },
                unit="percent"
            ))
        
        # Memory metrics for different containers
        for container_id in ["container_1", "container_2", "container_3"]:
            metrics.append(MetricValue(
                name="container_memory_usage_bytes",
                value=random.randint(1000000, 1000000000),
                timestamp=timestamp,
                labels={
                    "container_id": container_id,
                    "host": "host_1"
                },
                unit="bytes"
            ))
        
        # System metrics
        metrics.append(MetricValue(
            name="system_load_1m",
            value=random.uniform(0, 5),
            timestamp=timestamp,
            labels={"host": "host_1"},
            unit="load"
        ))
    
    return metrics


async def storage_system_example():
    """Example of using the metrics storage system."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create storage system
    config = {
        "storage_type": "memory",  # Use in-memory storage for example
        "auto_cleanup": True,
        "cleanup_interval_hours": 1,
        "setup_default_retention": True
    }
    
    storage_system = create_metrics_storage_system(config)
    
    # Initialize storage system
    await storage_system.initialize()
    
    try:
        # Generate and store sample metrics
        logging.info("Generating sample metrics...")
        metrics = await generate_sample_metrics(100)
        logging.info(f"Generated {len(metrics)} sample metrics")
        
        # Store metrics
        logging.info("Storing metrics...")
        success = await storage_system.store_metrics(metrics)
        logging.info(f"Stored metrics: {'success' if success else 'failed'}")
        
        # Query metrics
        logging.info("Querying metrics...")
        
        # Get all metric names
        metric_names = await storage_system.get_metric_names()
        logging.info(f"Available metrics: {metric_names}")
        
        # Query CPU usage for container_1
        cpu_metrics = await storage_system.query_metrics(
            metric_name="container_cpu_usage_percent",
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            labels={"container_id": "container_1"}
        )
        logging.info(f"Found {len(cpu_metrics)} CPU metrics for container_1")
        
        # Get latest memory usage for all containers
        for container_id in ["container_1", "container_2", "container_3"]:
            latest = await storage_system.query_latest(
                metric_name="container_memory_usage_bytes",
                labels={"container_id": container_id}
            )
            if latest:
                memory_mb = latest.value / 1024 / 1024
                logging.info(f"Latest memory usage for {container_id}: {memory_mb:.2f} MB")
        
        # Query with time range
        system_load = await storage_system.query_range(
            metric_name="system_load_1m",
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now(),
            step=timedelta(minutes=5)
        )
        logging.info(f"System load over time (5-minute intervals): {len(system_load)} points")
        for timestamp, value in system_load:
            if value is not None:
                logging.info(f"  {timestamp.strftime('%H:%M:%S')}: {value:.2f}")
        
        # Get storage statistics
        stats = await storage_system.get_storage_stats()
        logging.info(f"Storage statistics: {stats}")
        
        # Get retention summary
        retention = storage_system.get_retention_summary()
        logging.info(f"Retention rules: {retention}")
        
        # Run health check
        health = await storage_system.health_check()
        logging.info(f"Health check: {health['status']}")
        
        # Export metrics to file
        export_path = "metrics_export.json"
        await storage_system.export_metrics(
            output_path=export_path,
            metric_name="container_cpu_usage_percent",
            start_time=datetime.now() - timedelta(minutes=30),
            format="json"
        )
        logging.info(f"Exported metrics to {export_path}")
        
        # Apply retention policy (dry run)
        retention_impact = await storage_system.apply_retention_policy(dry_run=True)
        logging.info(f"Retention policy impact: {retention_impact}")
        
    finally:
        # Clean up
        await storage_system.cleanup()
        logging.info("Storage system cleaned up")


if __name__ == "__main__":
    asyncio.run(storage_system_example())