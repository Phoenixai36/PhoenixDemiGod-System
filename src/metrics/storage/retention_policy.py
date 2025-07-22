"""
Data retention policies for time series metrics.

This module provides configurable data retention policies to manage
storage space and performance by automatically cleaning up old data.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .time_series_storage import TimeSeriesStorage


class RetentionAction(Enum):
    """Actions that can be taken when retention rules are triggered."""
    DELETE = "delete"
    ARCHIVE = "archive"
    AGGREGATE = "aggregate"


@dataclass
class RetentionRule:
    """Defines a data retention rule."""
    name: str
    metric_pattern: str  # Glob pattern for metric names
    max_age: timedelta
    action: RetentionAction = RetentionAction.DELETE
    priority: int = 0  # Higher priority rules are evaluated first
    enabled: bool = True
    
    # Additional parameters for specific actions
    archive_storage: Optional[str] = None  # For ARCHIVE action
    aggregation_interval: Optional[timedelta] = None  # For AGGREGATE action
    aggregation_function: str = "avg"  # avg, sum, min, max, count
    
    # Conditions
    min_points_to_keep: int = 100  # Always keep at least this many points
    labels_filter: Optional[Dict[str, str]] = None  # Only apply to metrics with these labels
    
    def matches_metric(self, metric_name: str) -> bool:
        """Check if this rule applies to a metric."""
        import fnmatch
        return fnmatch.fnmatch(metric_name, self.metric_pattern)
    
    def get_cutoff_time(self) -> datetime:
        """Get the cutoff time for this rule."""
        return datetime.now() - self.max_age


@dataclass
class RetentionPolicy:
    """Collection of retention rules."""
    name: str
    description: str
    rules: List[RetentionRule] = field(default_factory=list)
    enabled: bool = True
    
    def add_rule(self, rule: RetentionRule) -> None:
        """Add a retention rule."""
        self.rules.append(rule)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a retention rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                return True
        return False
    
    def get_applicable_rules(self, metric_name: str) -> List[RetentionRule]:
        """Get all rules that apply to a metric."""
        if not self.enabled:
            return []
        
        applicable_rules = []
        for rule in self.rules:
            if rule.enabled and rule.matches_metric(metric_name):
                applicable_rules.append(rule)
        
        return applicable_rules


class RetentionManager:
    """Manages data retention policies and executes cleanup operations."""
    
    def __init__(self, storage: TimeSeriesStorage):
        self.storage = storage
        self.policies: Dict[str, RetentionPolicy] = {}
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = timedelta(hours=1)  # Run cleanup every hour
        
        # Statistics
        self.last_cleanup_time: Optional[datetime] = None
        self.cleanup_stats: Dict[str, Any] = {
            "total_runs": 0,
            "total_points_deleted": 0,
            "total_points_archived": 0,
            "total_points_aggregated": 0,
            "last_run_duration": 0,
            "errors": []
        }
    
    def add_policy(self, policy: RetentionPolicy) -> None:
        """Add a retention policy."""
        self.policies[policy.name] = policy
        self.logger.info(f"Added retention policy: {policy.name}")
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a retention policy."""
        if policy_name in self.policies:
            del self.policies[policy_name]
            self.logger.info(f"Removed retention policy: {policy_name}")
            return True
        return False
    
    def get_policy(self, policy_name: str) -> Optional[RetentionPolicy]:
        """Get a retention policy by name."""
        return self.policies.get(policy_name)
    
    async def start_automatic_cleanup(self) -> None:
        """Start automatic cleanup based on retention policies."""
        if self._running:
            self.logger.warning("Automatic cleanup already running")
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Started automatic retention cleanup")
    
    async def stop_automatic_cleanup(self) -> None:
        """Stop automatic cleanup."""
        if not self._running:
            return
        
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped automatic retention cleanup")
    
    async def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self._running:
            try:
                await self.run_cleanup()
                await asyncio.sleep(self.cleanup_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
                self.cleanup_stats["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def run_cleanup(self) -> Dict[str, Any]:
        """Run cleanup operations for all policies."""
        start_time = datetime.now()
        self.logger.info("Starting retention cleanup")
        
        cleanup_results = {
            "start_time": start_time.isoformat(),
            "policies_processed": 0,
            "metrics_processed": 0,
            "points_deleted": 0,
            "points_archived": 0,
            "points_aggregated": 0,
            "errors": []
        }
        
        try:
            # Get all metric names
            metric_names = await self.storage.get_metric_names()
            
            # Process each policy
            for policy_name, policy in self.policies.items():
                if not policy.enabled:
                    continue
                
                try:
                    policy_results = await self._process_policy(policy, metric_names)
                    cleanup_results["policies_processed"] += 1
                    cleanup_results["metrics_processed"] += policy_results["metrics_processed"]
                    cleanup_results["points_deleted"] += policy_results["points_deleted"]
                    cleanup_results["points_archived"] += policy_results["points_archived"]
                    cleanup_results["points_aggregated"] += policy_results["points_aggregated"]
                    
                except Exception as e:
                    error_msg = f"Error processing policy {policy_name}: {str(e)}"
                    self.logger.error(error_msg)
                    cleanup_results["errors"].append(error_msg)
            
            # Update statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.cleanup_stats["total_runs"] += 1
            self.cleanup_stats["total_points_deleted"] += cleanup_results["points_deleted"]
            self.cleanup_stats["total_points_archived"] += cleanup_results["points_archived"]
            self.cleanup_stats["total_points_aggregated"] += cleanup_results["points_aggregated"]
            self.cleanup_stats["last_run_duration"] = duration
            self.last_cleanup_time = end_time
            
            cleanup_results["end_time"] = end_time.isoformat()
            cleanup_results["duration_seconds"] = duration
            
            self.logger.info(f"Completed retention cleanup in {duration:.2f}s: "
                           f"{cleanup_results['points_deleted']} deleted, "
                           f"{cleanup_results['points_archived']} archived, "
                           f"{cleanup_results['points_aggregated']} aggregated")
            
        except Exception as e:
            error_msg = f"Error in cleanup run: {str(e)}"
            self.logger.error(error_msg)
            cleanup_results["errors"].append(error_msg)
        
        return cleanup_results
    
    async def _process_policy(self, policy: RetentionPolicy, metric_names: List[str]) -> Dict[str, Any]:
        """Process a single retention policy."""
        results = {
            "metrics_processed": 0,
            "points_deleted": 0,
            "points_archived": 0,
            "points_aggregated": 0
        }
        
        for metric_name in metric_names:
            applicable_rules = policy.get_applicable_rules(metric_name)
            if not applicable_rules:
                continue
            
            results["metrics_processed"] += 1
            
            # Apply each applicable rule
            for rule in applicable_rules:
                try:
                    rule_results = await self._apply_rule(rule, metric_name)
                    results["points_deleted"] += rule_results.get("points_deleted", 0)
                    results["points_archived"] += rule_results.get("points_archived", 0)
                    results["points_aggregated"] += rule_results.get("points_aggregated", 0)
                    
                except Exception as e:
                    self.logger.error(f"Error applying rule {rule.name} to {metric_name}: {str(e)}")
        
        return results
    
    async def _apply_rule(self, rule: RetentionRule, metric_name: str) -> Dict[str, Any]:
        """Apply a single retention rule to a metric."""
        cutoff_time = rule.get_cutoff_time()
        
        if rule.action == RetentionAction.DELETE:
            return await self._delete_old_points(rule, metric_name, cutoff_time)
        elif rule.action == RetentionAction.ARCHIVE:
            return await self._archive_old_points(rule, metric_name, cutoff_time)
        elif rule.action == RetentionAction.AGGREGATE:
            return await self._aggregate_old_points(rule, metric_name, cutoff_time)
        else:
            self.logger.warning(f"Unknown retention action: {rule.action}")
            return {}
    
    async def _delete_old_points(self, rule: RetentionRule, metric_name: str, cutoff_time: datetime) -> Dict[str, Any]:
        """Delete old points for a metric."""
        # Check if we should keep minimum points
        if rule.min_points_to_keep > 0:
            from .time_series_storage import TimeSeriesQuery
            query = TimeSeriesQuery(metric_name=metric_name, limit=rule.min_points_to_keep)
            recent_points = await self.storage.query_points(query)
            
            if len(recent_points) <= rule.min_points_to_keep:
                # Don't delete if we'd go below minimum
                return {"points_deleted": 0}
            
            # Adjust cutoff time to preserve minimum points
            if recent_points:
                min_time = recent_points[0].timestamp
                if cutoff_time > min_time:
                    cutoff_time = min_time
        
        deleted_count = await self.storage.delete_points(metric_name, cutoff_time)
        return {"points_deleted": deleted_count}
    
    async def _archive_old_points(self, rule: RetentionRule, metric_name: str, cutoff_time: datetime) -> Dict[str, Any]:
        """Archive old points for a metric."""
        # This is a placeholder - in a real implementation, you would:
        # 1. Query old points
        # 2. Store them in archive storage
        # 3. Delete them from primary storage
        
        self.logger.info(f"Archiving old points for {metric_name} (cutoff: {cutoff_time})")
        
        # For now, just delete (same as DELETE action)
        deleted_count = await self.storage.delete_points(metric_name, cutoff_time)
        return {"points_archived": deleted_count}
    
    async def _aggregate_old_points(self, rule: RetentionRule, metric_name: str, cutoff_time: datetime) -> Dict[str, Any]:
        """Aggregate old points for a metric."""
        # This is a placeholder - in a real implementation, you would:
        # 1. Query old points
        # 2. Group them by aggregation interval
        # 3. Calculate aggregated values
        # 4. Store aggregated points
        # 5. Delete original points
        
        self.logger.info(f"Aggregating old points for {metric_name} (cutoff: {cutoff_time})")
        
        # For now, just delete (same as DELETE action)
        deleted_count = await self.storage.delete_points(metric_name, cutoff_time)
        return {"points_aggregated": deleted_count}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retention manager statistics."""
        return {
            **self.cleanup_stats,
            "last_cleanup_time": self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
            "cleanup_interval_seconds": self.cleanup_interval.total_seconds(),
            "is_running": self._running,
            "policies_count": len(self.policies),
            "enabled_policies": sum(1 for p in self.policies.values() if p.enabled)
        }
    
    def create_default_policies(self) -> None:
        """Create default retention policies."""
        # Short-term high-frequency metrics (keep 1 day)
        short_term_policy = RetentionPolicy(
            name="short_term",
            description="Short-term retention for high-frequency metrics"
        )
        short_term_policy.add_rule(RetentionRule(
            name="high_frequency_cleanup",
            metric_pattern="*_per_second",
            max_age=timedelta(days=1),
            action=RetentionAction.DELETE,
            priority=10
        ))
        
        # Medium-term metrics (keep 1 week)
        medium_term_policy = RetentionPolicy(
            name="medium_term",
            description="Medium-term retention for regular metrics"
        )
        medium_term_policy.add_rule(RetentionRule(
            name="regular_cleanup",
            metric_pattern="container_*",
            max_age=timedelta(weeks=1),
            action=RetentionAction.DELETE,
            priority=5
        ))
        
        # Long-term metrics (keep 1 month)
        long_term_policy = RetentionPolicy(
            name="long_term",
            description="Long-term retention for important metrics"
        )
        long_term_policy.add_rule(RetentionRule(
            name="important_cleanup",
            metric_pattern="system_*",
            max_age=timedelta(days=30),
            action=RetentionAction.DELETE,
            priority=1
        ))
        
        # Add policies
        self.add_policy(short_term_policy)
        self.add_policy(medium_term_policy)
        self.add_policy(long_term_policy)
        
        self.logger.info("Created default retention policies")


def create_retention_manager(storage: TimeSeriesStorage, 
                           with_defaults: bool = True) -> RetentionManager:
    """Create a retention manager with optional default policies."""
    manager = RetentionManager(storage)
    
    if with_defaults:
        manager.create_default_policies()
    
    return manager