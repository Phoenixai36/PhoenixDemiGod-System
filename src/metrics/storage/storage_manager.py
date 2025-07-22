"""
Storage manager that coordinates all storage components.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..models import MetricValue, CollectorConfig
from .time_series_storage import TimeSeriesStorage
from .retention_manager import RetentionManager, RetentionRule
from .query_interface import MetricsQueryInterface, QueryFilter, AggregationQuery


class StorageManager:
    """Manages all aspects of metrics storage and retrieval."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize storage components
        db_path = self.config.get('database_path', 'data/metrics.db')
        self.storage = TimeSeriesStorage(db_path)
        self.retention_manager = RetentionManager(self.storage)
        self.query_interface = MetricsQueryInterface(self.storage)
        
        # Setup default retention rules
        if self.config.get('setup_default_retention', True):
            self.retention_manager.setup_default_rules()
        
        # Storage statistics
        self._last_stats_update = None
        self._cached_stats = {}
        self._stats_cache_duration = timedelta(minutes=5)
        
        self.logger.info("Storage manager initialized")
    
    async def initialize(self) -> bool:
        """Initialize the storage manager."""
        try:
            # Start automatic retention cleanup if configured
            if self.config.get('auto_cleanup', True):
                cleanup_interval = self.config.get('cleanup_interval_hours', 1)
                self.retention_manager._cleanup_interval = timedelta(hours=cleanup_interval)
                await self.retention_manager.start_automatic_cleanup()
            
            self.logger.info("Storage manager initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize storage manager: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up storage manager resources."""
        try:
            await self.retention_manager.stop_automatic_cleanup()
            self.storage.close()
            self.logger.info("Storage manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during storage manager cleanup: {str(e)}")
    
    # Storage operations
    
    def store_metric(self, metric: MetricValue) -> bool:
        """Store a single metric."""
        return self.storage.store_metric(metric)
    
    def store_metrics(self, metrics: List[MetricValue]) -> int:
        """Store multiple metrics in batch."""
        return self.storage.store_metrics(metrics)
    
    # Query operations
    
    def query_metrics(self, filters: QueryFilter) -> List[MetricValue]:
        """Query metrics with advanced filtering."""
        result = self.query_interface.query(filters)
        return result.metrics
    
    def aggregate_metrics(self, query: AggregationQuery) -> List[tuple]:
        """Execute aggregation query."""
        result = self.query_interface.aggregate(query)
        return result.data_points
    
    def get_metric_statistics(self, metric_name: str, 
                            time_range: Optional[str] = None) -> Dict[str, Any]:
        """Get statistical summary for a metric."""
        from .query_interface import TimeRange
        
        tr = None
        if time_range:
            try:
                tr = TimeRange(time_range)
            except ValueError:
                self.logger.warning(f"Invalid time range: {time_range}")
        
        return self.query_interface.get_metric_statistics(metric_name, tr)
    
    def find_anomalies(self, metric_name: str, 
                      threshold_multiplier: float = 2.0) -> List[MetricValue]:
        """Find anomalous metric values."""
        return self.query_interface.find_anomalies(metric_name, threshold_multiplier)
    
    def get_top_metrics(self, aggregation: str = "avg", limit: int = 10) -> List[Dict[str, Any]]:
        """Get top metrics by aggregated value."""
        from .query_interface import AggregationType
        
        try:
            agg_type = AggregationType(aggregation)
        except ValueError:
            agg_type = AggregationType.AVG
        
        return self.query_interface.get_top_metrics(agg_type, limit=limit)
    
    # Retention management
    
    def add_retention_rule(self, pattern: str, retention_days: int, 
                          labels: Optional[Dict[str, str]] = None,
                          priority: int = 0) -> None:
        """Add a retention rule."""
        rule = RetentionRule(
            metric_pattern=pattern,
            retention_period=timedelta(days=retention_days),
            labels=labels,
            priority=priority
        )
        self.retention_manager.add_retention_rule(rule)
    
    def remove_retention_rule(self, pattern: str) -> bool:
        """Remove a retention rule."""
        return self.retention_manager.remove_retention_rule(pattern)
    
    def apply_retention_policy(self, dry_run: bool = False) -> Dict[str, Any]:
        """Apply retention policies."""
        return self.retention_manager.apply_retention_policy(dry_run)
    
    def get_retention_summary(self) -> Dict[str, Any]:
        """Get retention rules summary."""
        return self.retention_manager.get_retention_summary()
    
    # Storage information and management
    
    def get_storage_stats(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive storage statistics."""
        now = datetime.now()
        
        # Use cached stats if recent and not forcing refresh
        if (not force_refresh and self._last_stats_update and 
            now - self._last_stats_update < self._stats_cache_duration):
            return self._cached_stats
        
        try:
            # Get basic storage stats
            storage_stats = self.storage.get_storage_stats()
            
            # Get retention impact
            retention_impact = self.retention_manager.estimate_storage_impact()
            
            # Combine statistics
            combined_stats = {
                "storage": storage_stats,
                "retention": {
                    "rules_count": len(self.retention_manager.retention_rules),
                    "impact": retention_impact
                },
                "query_performance": {
                    "available_metrics": len(self.storage.get_metric_names()),
                    "last_updated": now.isoformat()
                }
            }
            
            # Cache the results
            self._cached_stats = combined_stats
            self._last_stats_update = now
            
            return combined_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {str(e)}")
            return {"error": str(e)}
    
    def get_metric_names(self) -> List[str]:
        """Get all available metric names."""
        return self.storage.get_metric_names()
    
    def get_label_values(self, label_key: str) -> List[str]:
        """Get all values for a specific label key."""
        return self.storage.get_label_values(label_key)
    
    def vacuum_database(self) -> bool:
        """Vacuum the database to reclaim space."""
        return self.storage.vacuum_database()
    
    # Health and diagnostics
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage system."""
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
            write_success = self.storage.store_metric(test_metric)
            health["checks"]["write"] = "pass" if write_success else "fail"
            
            # Test read
            try:
                metrics = self.storage.query_metrics(
                    metric_name="health_check_test",
                    limit=1
                )
                health["checks"]["read"] = "pass" if metrics else "fail"
            except Exception:
                health["checks"]["read"] = "fail"
            
            # Test cleanup (delete test metric)
            try:
                self.storage.delete_metrics(metric_name="health_check_test")
                health["checks"]["delete"] = "pass"
            except Exception:
                health["checks"]["delete"] = "fail"
            
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
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the storage system."""
        try:
            stats = self.get_storage_stats()
            
            # Calculate some performance indicators
            storage_info = stats.get("storage", {})
            total_metrics = storage_info.get("total_metrics", 0)
            db_size_mb = storage_info.get("database_size_mb", 0)
            
            performance = {
                "metrics_per_mb": total_metrics / db_size_mb if db_size_mb > 0 else 0,
                "storage_efficiency": {
                    "total_metrics": total_metrics,
                    "database_size_mb": db_size_mb,
                    "avg_metric_size_bytes": (db_size_mb * 1024 * 1024) / total_metrics if total_metrics > 0 else 0
                },
                "retention_efficiency": stats.get("retention", {}).get("impact", {})
            }
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {str(e)}")
            return {"error": str(e)}
    
    # Configuration management
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update storage manager configuration."""
        try:
            self.config.update(new_config)
            
            # Apply configuration changes
            if 'cleanup_interval_hours' in new_config:
                new_interval = timedelta(hours=new_config['cleanup_interval_hours'])
                self.retention_manager._cleanup_interval = new_interval
                self.logger.info(f"Updated cleanup interval to {new_interval}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update config: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    # Utility methods
    
    def export_metrics(self, output_path: str, 
                      filters: Optional[QueryFilter] = None,
                      format: str = "json") -> bool:
        """Export metrics to file."""
        try:
            if filters:
                metrics = self.query_metrics(filters)
            else:
                # Export all metrics (be careful with large datasets)
                metrics = self.storage.query_metrics(limit=10000)
            
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