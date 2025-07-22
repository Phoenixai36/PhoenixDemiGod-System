"""
Data retention management for metrics storage.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .time_series_storage import TimeSeriesStorage


class RetentionPolicy(Enum):
    """Predefined retention policies."""
    SHORT_TERM = "short_term"      # 1 day
    MEDIUM_TERM = "medium_term"    # 7 days
    LONG_TERM = "long_term"        # 30 days
    EXTENDED = "extended"          # 90 days
    PERMANENT = "permanent"        # No deletion


@dataclass
class RetentionRule:
    """Defines a retention rule for metrics."""
    metric_pattern: str  # Glob pattern for metric names
    retention_period: timedelta
    labels: Optional[Dict[str, str]] = None  # Optional label filters
    priority: int = 0  # Higher priority rules are applied first
    
    def matches_metric(self, metric_name: str, metric_labels: Dict[str, str] = None) -> bool:
        """Check if this rule applies to a metric."""
        import fnmatch
        
        # Check metric name pattern
        if not fnmatch.fnmatch(metric_name, self.metric_pattern):
            return False
        
        # Check label filters if specified
        if self.labels and metric_labels:
            for key, value in self.labels.items():
                if metric_labels.get(key) != value:
                    return False
        
        return True


class RetentionManager:
    """Manages data retention policies and cleanup."""
    
    def __init__(self, storage: TimeSeriesStorage):
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        self.retention_rules: List[RetentionRule] = []
        self.default_retention = timedelta(days=30)
        self._cleanup_task = None
        self._cleanup_interval = timedelta(hours=1)
        self._running = False
    
    def add_retention_rule(self, rule: RetentionRule) -> None:
        """Add a retention rule."""
        self.retention_rules.append(rule)
        # Sort by priority (highest first)
        self.retention_rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"Added retention rule: {rule.metric_pattern} -> {rule.retention_period}")
    
    def remove_retention_rule(self, metric_pattern: str) -> bool:
        """Remove a retention rule by metric pattern."""
        original_count = len(self.retention_rules)
        self.retention_rules = [r for r in self.retention_rules if r.metric_pattern != metric_pattern]
        removed = len(self.retention_rules) < original_count
        
        if removed:
            self.logger.info(f"Removed retention rule for pattern: {metric_pattern}")
        
        return removed
    
    def get_retention_period(self, metric_name: str, labels: Dict[str, str] = None) -> timedelta:
        """Get retention period for a specific metric."""
        # Find the first matching rule (highest priority)
        for rule in self.retention_rules:
            if rule.matches_metric(metric_name, labels):
                return rule.retention_period
        
        # Return default if no rule matches
        return self.default_retention
    
    def setup_default_rules(self) -> None:
        """Setup default retention rules for common metric types."""
        default_rules = [
            # High-frequency metrics - shorter retention
            RetentionRule("container_cpu_*", timedelta(days=7), priority=10),
            RetentionRule("container_memory_*", timedelta(days=7), priority=10),
            RetentionRule("container_network_*", timedelta(days=3), priority=10),
            RetentionRule("container_disk_*", timedelta(days=3), priority=10),
            
            # Lifecycle events - longer retention
            RetentionRule("container_lifecycle_*", timedelta(days=30), priority=20),
            RetentionRule("container_restart_*", timedelta(days=30), priority=20),
            RetentionRule("container_uptime_*", timedelta(days=30), priority=20),
            
            # Error and alert metrics - extended retention
            RetentionRule("*_error_*", timedelta(days=90), priority=30),
            RetentionRule("*_alert_*", timedelta(days=90), priority=30),
            RetentionRule("*_anomaly_*", timedelta(days=90), priority=30),
            
            # Test and debug metrics - very short retention
            RetentionRule("test_*", timedelta(hours=24), priority=5),
            RetentionRule("debug_*", timedelta(hours=24), priority=5),
        ]
        
        for rule in default_rules:
            self.add_retention_rule(rule)
        
        self.logger.info(f"Setup {len(default_rules)} default retention rules")
    
    def apply_retention_policy(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply retention policies and clean up old data.
        
        Args:
            dry_run: If True, only calculate what would be deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        self.logger.info("Starting retention policy application")
        
        stats = {
            "total_deleted": 0,
            "deleted_by_metric": {},
            "deleted_by_rule": {},
            "errors": []
        }
        
        try:
            # Get all metric names
            metric_names = self.storage.get_metric_names()
            
            for metric_name in metric_names:
                try:
                    # Get retention period for this metric
                    retention_period = self.get_retention_period(metric_name)
                    cutoff_time = datetime.now() - retention_period
                    
                    # Find matching rule for statistics
                    matching_rule = None
                    for rule in self.retention_rules:
                        if rule.matches_metric(metric_name):
                            matching_rule = rule
                            break
                    
                    rule_key = matching_rule.metric_pattern if matching_rule else "default"
                    
                    if not dry_run:
                        # Delete old metrics
                        deleted_count = self.storage.delete_metrics(
                            metric_name=metric_name,
                            before_time=cutoff_time
                        )
                    else:
                        # Count what would be deleted
                        old_metrics = self.storage.query_metrics(
                            metric_name=metric_name,
                            end_time=cutoff_time
                        )
                        deleted_count = len(old_metrics)
                    
                    if deleted_count > 0:
                        stats["deleted_by_metric"][metric_name] = deleted_count
                        stats["total_deleted"] += deleted_count
                        
                        if rule_key not in stats["deleted_by_rule"]:
                            stats["deleted_by_rule"][rule_key] = 0
                        stats["deleted_by_rule"][rule_key] += deleted_count
                        
                        self.logger.debug(f"{'Would delete' if dry_run else 'Deleted'} "
                                        f"{deleted_count} old metrics for {metric_name}")
                
                except Exception as e:
                    error_msg = f"Error processing {metric_name}: {str(e)}"
                    self.logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Vacuum database after cleanup (if not dry run)
            if not dry_run and stats["total_deleted"] > 0:
                self.storage.vacuum_database()
            
            action = "Would delete" if dry_run else "Deleted"
            self.logger.info(f"{action} {stats['total_deleted']} metrics total")
            
        except Exception as e:
            error_msg = f"Error during retention policy application: {str(e)}"
            self.logger.error(error_msg)
            stats["errors"].append(error_msg)
        
        return stats
    
    async def start_automatic_cleanup(self) -> None:
        """Start automatic cleanup task."""
        if self._running:
            self.logger.warning("Automatic cleanup already running")
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info(f"Started automatic cleanup with {self._cleanup_interval} interval")
    
    async def stop_automatic_cleanup(self) -> None:
        """Stop automatic cleanup task."""
        if not self._running:
            return
        
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        self.logger.info("Stopped automatic cleanup")
    
    async def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval.total_seconds())
                
                if self._running:  # Check again after sleep
                    self.logger.debug("Running scheduled retention cleanup")
                    stats = self.apply_retention_policy(dry_run=False)
                    
                    if stats["total_deleted"] > 0:
                        self.logger.info(f"Automatic cleanup deleted {stats['total_deleted']} metrics")
                    
                    if stats["errors"]:
                        self.logger.warning(f"Cleanup had {len(stats['errors'])} errors")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
                # Continue running despite errors
    
    def get_retention_summary(self) -> Dict[str, Any]:
        """Get summary of retention rules and their impact."""
        summary = {
            "total_rules": len(self.retention_rules),
            "default_retention_days": self.default_retention.days,
            "rules": []
        }
        
        for rule in self.retention_rules:
            rule_info = {
                "pattern": rule.metric_pattern,
                "retention_days": rule.retention_period.days,
                "retention_hours": rule.retention_period.total_seconds() / 3600,
                "priority": rule.priority,
                "labels": rule.labels
            }
            summary["rules"].append(rule_info)
        
        return summary
    
    def estimate_storage_impact(self) -> Dict[str, Any]:
        """Estimate storage impact of current retention policies."""
        try:
            storage_stats = self.storage.get_storage_stats()
            
            if not storage_stats.get("metrics_by_name"):
                return {"error": "No metrics data available"}
            
            impact = {
                "current_total_metrics": storage_stats["total_metrics"],
                "current_size_mb": storage_stats["database_size_mb"],
                "estimated_after_cleanup": {},
                "potential_savings": {}
            }
            
            # Simulate cleanup to estimate impact
            cleanup_stats = self.apply_retention_policy(dry_run=True)
            
            impact["estimated_after_cleanup"] = {
                "total_metrics": storage_stats["total_metrics"] - cleanup_stats["total_deleted"],
                "deleted_metrics": cleanup_stats["total_deleted"],
                "deletion_percentage": (cleanup_stats["total_deleted"] / storage_stats["total_metrics"] * 100) 
                                     if storage_stats["total_metrics"] > 0 else 0
            }
            
            # Estimate size savings (rough approximation)
            if storage_stats["total_metrics"] > 0:
                avg_metric_size = storage_stats["database_size_bytes"] / storage_stats["total_metrics"]
                estimated_savings_bytes = cleanup_stats["total_deleted"] * avg_metric_size
                
                impact["potential_savings"] = {
                    "size_bytes": estimated_savings_bytes,
                    "size_mb": estimated_savings_bytes / (1024 * 1024),
                    "percentage": (estimated_savings_bytes / storage_stats["database_size_bytes"] * 100)
                                if storage_stats["database_size_bytes"] > 0 else 0
                }
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Error estimating storage impact: {str(e)}")
            return {"error": str(e)}
    
    def create_policy_from_preset(self, preset: RetentionPolicy) -> timedelta:
        """Create retention period from preset policy."""
        policy_map = {
            RetentionPolicy.SHORT_TERM: timedelta(days=1),
            RetentionPolicy.MEDIUM_TERM: timedelta(days=7),
            RetentionPolicy.LONG_TERM: timedelta(days=30),
            RetentionPolicy.EXTENDED: timedelta(days=90),
            RetentionPolicy.PERMANENT: timedelta(days=365 * 100)  # Effectively permanent
        }
        
        return policy_map.get(preset, self.default_retention)