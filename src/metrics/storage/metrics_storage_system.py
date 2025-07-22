"""
Metrics storage and retrieval system.

This module provides a comprehensive system for storing, retrieving, and managing
time series metrics data with configurable retention policies.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from ..models import MetricValue, CollectorConfig, CollectorStatusctorConfig
from .time_series_storage import TimeSeriesStorage, InMemoryTimeSeriesStorage, RetentionPolicy
from .storage_factory import StorageFactory, StorageBackend
from .retention_manager import RetentionManager, RetentionRule
from .query_engine import QueryEngine
from .query_interface import QueryFilter, AggregationQuery, TimeRange, AggregationType


class MetricsStorageSystem:
    """
    Comprehensive system for metrics storage and retrieval.
    
    This class integrates all components of the metrics storage system:
    - Time series storage backend
    - Retention policy management
    - Query interface
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the metrics storage system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Create storage components
        self.storage_factory = StorageFactory()
        self._setup_storage()
        
        # Initialize state
        self._initialized = False
        self._cleanup_task = None
        
        self.logger.info("Metrics storage system created")
    
    def _setup_storage(self) -> None:
        """Set up storage components based on configuration."""
        # Determine storage backend
        backend_name = self.config.get("storage_type", "memory")
        try:
            backend = StorageBackend(backend_name)
        except ValueError:
            self.logger.warning(f"Unknown storage backend: {backend_name}, using memory")
            backend = StorageBackend.MEMORY
        
        # Create storage backend
        storage_config = self.config.get("storage_config", {})
        
        # Set default database path if using SQLite
        if backend == StorageBackend.SQLITE and "db_path" not in storage_config:
            db_path = os.environ.get("METRICS_DB_PATH", "data/metrics.db")
            storage_config["db_path"] = db_path
            
            # Ensure directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        
        # Create storage components
        self.storage = self.storage_factory.create_storage(backend, storage_config)
        
        # Create retention manager
        retention_enabled = self.config.get("retention_enabled", True)
        self.retention_manager = RetentionManager(self.storage)
        
        if retention_enabled:
            # Set up default retention rules if requested
            if self.config.get("setup_default_retention", True):
                self._setup_default_retention()
        
        # Create query engine
        self.query_engine = QueryEngine(self.storage)
    
    def _setup_default_retention(self) -> None:
        """Set up default retention rules."""
        # Get retention days from config or environment
        default_days = int(os.environ.get("METRICS_RETENTION_DAYS", "30"))
        
        # Create default retention rules
        rules = [
            # System metrics - longer retention
            RetentionRule(
                metric_pattern="system_*",
                retention_period=timedelta(days=default_days),
                priority=10
            ),
            
            # Container metrics - medium retention
            RetentionRule(
                metric_pattern="container_*",
                retention_period=timedelta(days=max(7, default_days // 2)),
                priority=20
            ),
            
            # High-frequency metrics - shorter retention
            RetentionRule(
                metric_pattern="*_per_second",
                retention_period=timedelta(days=max(1, default_days // 10)),
                priority=30
            ),
            
            # Default rule for everything else
            RetentionRule(
                metric_pattern="*",
                retention_period=timedelta(days=default_days),
                priority=0
            )
        ]
        
        # Add rules to retention manager
        for rule in rules:
            self.retention_manager.add_retention_rule(rule)
        
        self.logger.info(f"Set up default retention rules with {default_days} days default retention")
    
    async def initialize(self) -> bool:
        """
        Initialize the metrics storage system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self._initialized:
            self.logger.warning("Metrics storage system already initialized")
            return True
        
        try:
            # Start automatic retention cleanup if enabled
            if self.config.get("auto_cleanup", True):
                cleanup_interval = self.config.get("cleanup_interval_hours", 1)
                self.retention_manager._cleanup_interval = timedelta(hours=cleanup_interval)
                await self.retention_manager.start_automatic_cleanup()
            
            self._initialized = True
            self.logger.info("Metrics storage system initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics storage system: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources used by the metrics storage system."""
        try:
            # Stop automatic retention cleanup
            await self.retention_manager.stop_automatic_cleanup()
            
            # Close storage
            if hasattr(self.storage, "close"):
                self.storage.close()
            
            self.logger.info("Metrics storage system cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during metrics storage system cleanup: {str(e)}")
    
    # Storage operations
    
    async def store_metrics(self, metrics: List[MetricValue]) -> bool:
        """
        Store multiple metrics.
        
        Args:
            metrics: List of metrics to store
            
        Returns:
            True if successful, False otherwise
        """
        if not metrics:
            return True
        
        try:
            result = await self.storage.store_metrics(metrics)
            return result
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")
            return False
    
    async def store_metric(self, metric: MetricValue) -> bool:
        """
        Store a single metric.
        
        Args:
            metric: Metric to store
            
        Returns:
            True if successful, False otherwise
        """
        return await self.store_metrics([metric])
    
    # Query operations
    
    async def query_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MetricValue]:
        """
        Query metrics with flexible time range options.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Optional start of time range
            end_time: Optional end of time range
            duration: Optional duration from end_time (or now) backwards
            labels: Optional label filters
            aggregation: Optional aggregation function (avg, sum, min, max, last)
            limit: Optional limit on number of results
            
        Returns:
            List of matching MetricValue objects
        """
        return await self.query_engine.query_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            labels=labels,
            aggregation=aggregation,
            limit=limit
        )
    
    async def query_latest(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricValue]:
        """
        Query the latest value for a metric.
        
        Args:
            metric_name: Name of the metric to query
            labels: Optional label filters
            
        Returns:
            The latest MetricValue or None if not found
        """
        return await self.query_engine.query_latest(metric_name, labels)
    
    async def query_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        step: timedelta,
        labels: Optional[Dict[str, str]] = None,
        aggregation: str = "avg"
    ) -> List[tuple]:
        """
        Query metrics with regular time intervals.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Start of time range
            end_time: End of time range
            step: Time interval between points
            labels: Optional label filters
            aggregation: Aggregation function (avg, sum, min, max, last)
            
        Returns:
            List of (timestamp, value) tuples at regular intervals
        """
        return await self.query_engine.query_range(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            step=step,
            labels=labels,
            aggregation=aggregation
        )
    
    async def get_metric_names(self) -> List[str]:
        """
        Get all available metric names.
        
        Returns:
            List of metric names
        """
        return await self.query_engine.get_metric_names()
    
    async def get_label_keys(self, metric_name: Optional[str] = None) -> List[str]:
        """
        Get all available label keys.
        
        Args:
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label keys
        """
        return await self.query_engine.get_label_keys(metric_name)
    
    async def get_label_values(self, label_key: str, metric_name: Optional[str] = None) -> List[str]:
        """
        Get all available values for a label key.
        
        Args:
            label_key: The label key to get values for
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label values
        """
        return await self.query_engine.get_label_values(label_key, metric_name)
    
    # Retention management
    
    def add_retention_rule(
        self,
        metric_pattern: str,
        retention_days: int,
        labels: Optional[Dict[str, str]] = None,
        priority: int = 0
    ) -> None:
        """
        Add a retention rule.
        
        Args:
            metric_pattern: Glob pattern for metric names
            retention_days: Number of days to retain data
            labels: Optional label filters
            priority: Rule priority (higher values are evaluated first)
        """
        rule = RetentionRule(
            metric_pattern=metric_pattern,
            retention_period=timedelta(days=retention_days),
            labels=labels,
            priority=priority
        )
        self.retention_manager.add_retention_rule(rule)
    
    def remove_retention_rule(self, metric_pattern: str) -> bool:
        """
        Remove a retention rule by metric pattern.
        
        Args:
            metric_pattern: Glob pattern for metric names
            
        Returns:
            True if a rule was removed, False otherwise
        """
        return self.retention_manager.remove_retention_rule(metric_pattern)
    
    async def apply_retention_policy(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply retention policies and clean up old data.
        
        Args:
            dry_run: If True, only calculate what would be deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        return self.retention_manager.apply_retention_policy(dry_run)
    
    def get_retention_summary(self) -> Dict[str, Any]:
        """
        Get summary of retention rules.
        
        Returns:
            Dictionary with retention rule summary
        """
        return self.retention_manager.get_retention_summary()
    
    # Storage information and management
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the storage.
        
        Returns:
            Dictionary with storage statistics
        """
        return await self.query_engine.get_storage_stats()
    
    # Health and diagnostics
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on storage system.
        
        Returns:
            Dictionary with health check results
        """
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test basic storage operations
            test_metric = MetricValue(
                name="health_check_test",
                value=1.0,
                timestamp=datetime.now(),
                labels={"test": "true"}
            )
            
            # Test write
            write_success = await self.store_metric(test_metric)
            health["checks"]["write"] = "pass" if write_success else "fail"
            
            # Test read
            try:
                metrics = await self.query_metrics(
                    metric_name="health_check_test",
                    limit=1
                )
                health["checks"]["read"] = "pass" if metrics else "fail"
            except Exception:
                health["checks"]["read"] = "fail"
            
            # Check retention manager
            try:
                retention_summary = self.retention_manager.get_retention_summary()
                health["checks"]["retention"] = "pass" if retention_summary else "fail"
            except Exception:
                health["checks"]["retention"] = "fail"
            
            # Overall status
            failed_checks = [k for k, v in health["checks"].items() if v == "fail"]
            if failed_checks:
                health["status"] = "degraded" if len(failed_checks) < len(health["checks"]) else "unhealthy"
                health["failed_checks"] = failed_checks
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health
    
    # Utility methods
    
    async def export_metrics(
        self,
        output_path: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"
    ) -> bool:
        """
        Export metrics to file.
        
        Args:
            output_path: Path to output file
            metric_name: Optional metric name to filter by
            start_time: Optional start of time range
            end_time: Optional end of time range
            format: Output format (json or csv)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Query metrics
            if metric_name:
                metrics = await self.query_metrics(
                    metric_name=metric_name,
                    start_time=start_time,
                    end_time=end_time
                )
            else:
                # Get all metric names
                metric_names = await self.get_metric_names()
                metrics = []
                
                for name in metric_names:
                    metrics.extend(await self.query_metrics(
                        metric_name=name,
                        start_time=start_time,
                        end_time=end_time
                    ))
            
            # Create output directory if needed
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                import json
                
                export_data = []
                for metric in metrics:
                    export_data.append({
                        "name": metric.name,
                        "value": metric.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "labels": metric.labels,
                        "unit": metric.unit
                    })
                
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            elif format.lower() == "csv":
                import csv
                
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["name", "value", "timestamp", "labels", "unit"])
                    
                    for metric in metrics:
                        writer.writerow([
                            metric.name,
                            metric.value,
                            metric.timestamp.isoformat(),
                            str(metric.labels),
                            metric.unit or ""
                        ])
            
            self.logger.info(f"Exported {len(metrics)} metrics to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {str(e)}")
            return False


# Factory function to create metrics storage system
def create_metrics_storage_system(config: Optional[Dict[str, Any]] = None) -> MetricsStorageSystem:
    """
    Create a metrics storage system with the specified configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured MetricsStorageSystem instance
    """
    return MetricsStorageSystem(config)