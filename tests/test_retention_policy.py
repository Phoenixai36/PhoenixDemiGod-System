"""
Tests for retention policy system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

from src.metrics.storage import (
    RetentionPolicy,
    RetentionRule,
    RetentionManager,
    RetentionAction,
    TimeSeriesPoint,
    MemoryTimeSeriesStorage
)


class TestRetentionRule:
    """Test cases for RetentionRule."""
    
    def test_creation(self):
        """Test creating a retention rule."""
        rule = RetentionRule(
            name="test_rule",
            metric_pattern="cpu_*",
            max_age=timedelta(days=7),
            action=RetentionAction.DELETE,
            priority=5
        )
        
        assert rule.name == "test_rule"
        assert rule.metric_pattern == "cpu_*"
        assert rule.max_age == timedelta(days=7)
        assert rule.action == RetentionAction.DELETE
        assert rule.priority == 5
        assert rule.enabled is True
    
    def test_matches_metric(self):
        """Test metric pattern matching."""
        rule = RetentionRule(
            name="cpu_rule",
            metric_pattern="cpu_*",
            max_age=timedelta(hours=1)
        )
        
        assert rule.matches_metric("cpu_usage")
        assert rule.matches_metric("cpu_load")
        assert not rule.matches_metric("memory_usage")
        assert not rule.matches_metric("disk_cpu_usage")  # Doesn't start with cpu_
    
    def test_matches_metric_wildcard(self):
        """Test wildcard pattern matching."""
        rule = RetentionRule(
            name="all_rule",
            metric_pattern="*",
            max_age=timedelta(days=1)
        )
        
        assert rule.matches_metric("any_metric")
        assert rule.matches_metric("cpu_usage")
        assert rule.matches_metric("memory_usage")
    
    def test_matches_metric_complex_pattern(self):
        """Test complex pattern matching."""
        rule = RetentionRule(
            name="container_rule",
            metric_pattern="container_*_usage",
            max_age=timedelta(hours=12)
        )
        
        assert rule.matches_metric("container_cpu_usage")
        assert rule.matches_metric("container_memory_usage")
        assert not rule.matches_metric("container_cpu")
        assert not rule.matches_metric("system_cpu_usage")
    
    def test_get_cutoff_time(self):
        """Test cutoff time calculation."""
        rule = RetentionRule(
            name="time_rule",
            metric_pattern="*",
            max_age=timedelta(hours=2)
        )
        
        cutoff = rule.get_cutoff_time()
        expected_cutoff = datetime.now() - timedelta(hours=2)
        
        # Allow for small time differences in test execution
        assert abs((cutoff - expected_cutoff).total_seconds()) < 1


class TestRetentionPolicy:
    """Test cases for RetentionPolicy."""
    
    def test_creation(self):
        """Test creating a retention policy."""
        policy = RetentionPolicy(
            name="test_policy",
            description="Test policy for unit tests"
        )
        
        assert policy.name == "test_policy"
        assert policy.description == "Test policy for unit tests"
        assert len(policy.rules) == 0
        assert policy.enabled is True
    
    def test_add_rule(self):
        """Test adding rules to a policy."""
        policy = RetentionPolicy(name="test", description="test")
        
        rule1 = RetentionRule(
            name="rule1",
            metric_pattern="cpu_*",
            max_age=timedelta(days=1),
            priority=5
        )
        
        rule2 = RetentionRule(
            name="rule2",
            metric_pattern="memory_*",
            max_age=timedelta(days=2),
            priority=10
        )
        
        policy.add_rule(rule1)
        policy.add_rule(rule2)
        
        assert len(policy.rules) == 2
        # Should be sorted by priority (highest first)
        assert policy.rules[0].name == "rule2"  # Priority 10
        assert policy.rules[1].name == "rule1"  # Priority 5
    
    def test_remove_rule(self):
        """Test removing rules from a policy."""
        policy = RetentionPolicy(name="test", description="test")
        
        rule = RetentionRule(
            name="removable_rule",
            metric_pattern="*",
            max_age=timedelta(hours=1)
        )
        
        policy.add_rule(rule)
        assert len(policy.rules) == 1
        
        # Remove existing rule
        assert policy.remove_rule("removable_rule") is True
        assert len(policy.rules) == 0
        
        # Try to remove non-existent rule
        assert policy.remove_rule("non_existent") is False
    
    def test_get_applicable_rules(self):
        """Test getting applicable rules for a metric."""
        policy = RetentionPolicy(name="test", description="test")
        
        cpu_rule = RetentionRule(
            name="cpu_rule",
            metric_pattern="cpu_*",
            max_age=timedelta(hours=1)
        )
        
        memory_rule = RetentionRule(
            name="memory_rule",
            metric_pattern="memory_*",
            max_age=timedelta(hours=2)
        )
        
        all_rule = RetentionRule(
            name="all_rule",
            metric_pattern="*",
            max_age=timedelta(days=1)
        )
        
        policy.add_rule(cpu_rule)
        policy.add_rule(memory_rule)
        policy.add_rule(all_rule)
        
        # Test CPU metric
        cpu_rules = policy.get_applicable_rules("cpu_usage")
        assert len(cpu_rules) == 2  # cpu_rule and all_rule
        rule_names = [rule.name for rule in cpu_rules]
        assert "cpu_rule" in rule_names
        assert "all_rule" in rule_names
        
        # Test memory metric
        memory_rules = policy.get_applicable_rules("memory_usage")
        assert len(memory_rules) == 2  # memory_rule and all_rule
        rule_names = [rule.name for rule in memory_rules]
        assert "memory_rule" in rule_names
        assert "all_rule" in rule_names
        
        # Test other metric
        other_rules = policy.get_applicable_rules("disk_usage")
        assert len(other_rules) == 1  # only all_rule
        assert other_rules[0].name == "all_rule"
    
    def test_disabled_policy(self):
        """Test that disabled policies return no applicable rules."""
        policy = RetentionPolicy(name="test", description="test", enabled=False)
        
        rule = RetentionRule(
            name="test_rule",
            metric_pattern="*",
            max_age=timedelta(hours=1)
        )
        policy.add_rule(rule)
        
        # Should return no rules when policy is disabled
        rules = policy.get_applicable_rules("any_metric")
        assert len(rules) == 0


class TestRetentionManager:
    """Test cases for RetentionManager."""
    
    @pytest.fixture
    def storage(self):
        """Create memory storage for testing."""
        return MemoryTimeSeriesStorage()
    
    @pytest.fixture
    def manager(self, storage):
        """Create retention manager for testing."""
        return RetentionManager(storage)
    
    def test_creation(self, storage):
        """Test creating a retention manager."""
        manager = RetentionManager(storage)
        
        assert manager.storage == storage
        assert len(manager.policies) == 0
        assert not manager._running
        assert manager.cleanup_interval == timedelta(hours=1)
    
    def test_add_remove_policy(self, manager):
        """Test adding and removing policies."""
        policy = RetentionPolicy(name="test_policy", description="test")
        
        # Add policy
        manager.add_policy(policy)
        assert len(manager.policies) == 1
        assert manager.get_policy("test_policy") == policy
        
        # Remove policy
        assert manager.remove_policy("test_policy") is True
        assert len(manager.policies) == 0
        assert manager.get_policy("test_policy") is None
        
        # Try to remove non-existent policy
        assert manager.remove_policy("non_existent") is False
    
    @pytest.mark.asyncio
    async def test_start_stop_automatic_cleanup(self, manager):
        """Test starting and stopping automatic cleanup."""
        assert not manager._running
        
        # Start cleanup
        await manager.start_automatic_cleanup()
        assert manager._running
        assert manager._cleanup_task is not None
        
        # Stop cleanup
        await manager.stop_automatic_cleanup()
        assert not manager._running
    
    @pytest.mark.asyncio
    async def test_run_cleanup_empty(self, manager):
        """Test running cleanup with no policies."""
        results = await manager.run_cleanup()
        
        assert results["policies_processed"] == 0
        assert results["metrics_processed"] == 0
        assert results["points_deleted"] == 0
        assert "start_time" in results
        assert "end_time" in results
    
    @pytest.mark.asyncio
    async def test_run_cleanup_with_policy(self, manager, storage):
        """Test running cleanup with a policy."""
        # Add some test data
        base_time = datetime.now()
        old_points = [
            TimeSeriesPoint(
                timestamp=base_time - timedelta(hours=i+2),  # 2-6 hours old
                value=float(i),
                labels={}
            )
            for i in range(5)
        ]
        
        recent_points = [
            TimeSeriesPoint(
                timestamp=base_time - timedelta(minutes=i),  # Recent
                value=float(i+10),
                labels={}
            )
            for i in range(3)
        ]
        
        await storage.store_points("test_metric", old_points + recent_points)
        
        # Create policy to delete points older than 1 hour
        policy = RetentionPolicy(name="test_policy", description="test")
        rule = RetentionRule(
            name="cleanup_rule",
            metric_pattern="test_*",
            max_age=timedelta(hours=1),
            action=RetentionAction.DELETE
        )
        policy.add_rule(rule)
        manager.add_policy(policy)
        
        # Run cleanup
        results = await manager.run_cleanup()
        
        assert results["policies_processed"] == 1
        assert results["metrics_processed"] == 1
        assert results["points_deleted"] == 5  # Should delete the 5 old points
        
        # Verify points were actually deleted
        from src.metrics.storage import TimeSeriesQuery
        query = TimeSeriesQuery(metric_name="test_metric")
        remaining_points = await storage.query_points(query)
        assert len(remaining_points) == 3  # Only recent points remain
    
    @pytest.mark.asyncio
    async def test_min_points_to_keep(self, manager, storage):
        """Test that minimum points are preserved."""
        # Add test data
        base_time = datetime.now()
        points = [
            TimeSeriesPoint(
                timestamp=base_time - timedelta(hours=i),
                value=float(i),
                labels={}
            )
            for i in range(10)
        ]
        
        await storage.store_points("min_points_metric", points)
        
        # Create policy with min_points_to_keep
        policy = RetentionPolicy(name="min_points_policy", description="test")
        rule = RetentionRule(
            name="min_points_rule",
            metric_pattern="min_points_*",
            max_age=timedelta(hours=1),  # Would delete most points
            action=RetentionAction.DELETE,
            min_points_to_keep=5  # But keep at least 5
        )
        policy.add_rule(rule)
        manager.add_policy(policy)
        
        # Run cleanup
        results = await manager.run_cleanup()
        
        # Should delete some points but keep at least 5
        from src.metrics.storage import TimeSeriesQuery
        query = TimeSeriesQuery(metric_name="min_points_metric")
        remaining_points = await storage.query_points(query)
        assert len(remaining_points) >= 5
    
    def test_create_default_policies(self, manager):
        """Test creating default retention policies."""
        manager.create_default_policies()
        
        assert len(manager.policies) == 3
        assert "short_term" in manager.policies
        assert "medium_term" in manager.policies
        assert "long_term" in manager.policies
        
        # Check that policies have rules
        short_term = manager.get_policy("short_term")
        assert len(short_term.rules) > 0
        assert short_term.rules[0].metric_pattern == "*_per_second"
    
    def test_get_statistics(self, manager):
        """Test getting retention manager statistics."""
        stats = manager.get_statistics()
        
        assert "total_runs" in stats
        assert "total_points_deleted" in stats
        assert "last_cleanup_time" in stats
        assert "is_running" in stats
        assert "policies_count" in stats
        
        assert stats["total_runs"] == 0
        assert stats["is_running"] is False
        assert stats["policies_count"] == 0


class TestRetentionIntegration:
    """Integration tests for retention system."""
    
    @pytest.mark.asyncio
    async def test_full_retention_workflow(self):
        """Test complete retention workflow."""
        # Create storage and manager
        storage = MemoryTimeSeriesStorage()
        manager = RetentionManager(storage)
        
        # Add test data with different ages
        base_time = datetime.now()
        
        # Old CPU data (should be deleted)
        old_cpu_points = [
            TimeSeriesPoint(
                timestamp=base_time - timedelta(days=2, hours=i),
                value=float(i * 10),
                labels={"host": "server1"}
            )
            for i in range(5)
        ]
        
        # Recent CPU data (should be kept)
        recent_cpu_points = [
            TimeSeriesPoint(
                timestamp=base_time - timedelta(hours=i),
                value=float(i * 5),
                labels={"host": "server1"}
            )
            for i in range(3)
        ]
        
        # Memory data (different retention rule)
        memory_points = [
            TimeSeriesPoint(
                timestamp=base_time - timedelta(days=1, hours=i),
                value=float(i * 20),
                labels={"host": "server1"}
            )
            for i in range(4)
        ]
        
        await storage.store_points("cpu_usage", old_cpu_points + recent_cpu_points)
        await storage.store_points("memory_usage", memory_points)
        
        # Create retention policy
        policy = RetentionPolicy(name="test_retention", description="Test retention")
        
        # CPU data: keep 1 day
        cpu_rule = RetentionRule(
            name="cpu_retention",
            metric_pattern="cpu_*",
            max_age=timedelta(days=1),
            action=RetentionAction.DELETE,
            priority=10
        )
        
        # Memory data: keep 12 hours
        memory_rule = RetentionRule(
            name="memory_retention",
            metric_pattern="memory_*",
            max_age=timedelta(hours=12),
            action=RetentionAction.DELETE,
            priority=5
        )
        
        policy.add_rule(cpu_rule)
        policy.add_rule(memory_rule)
        manager.add_policy(policy)
        
        # Run cleanup
        results = await manager.run_cleanup()
        
        # Verify results
        assert results["policies_processed"] == 1
        assert results["metrics_processed"] == 2
        assert results["points_deleted"] > 0
        
        # Check remaining data
        from src.metrics.storage import TimeSeriesQuery
        
        cpu_query = TimeSeriesQuery(metric_name="cpu_usage")
        remaining_cpu = await storage.query_points(cpu_query)
        # Should have only recent CPU points
        assert len(remaining_cpu) == 3
        
        memory_query = TimeSeriesQuery(metric_name="memory_usage")
        remaining_memory = await storage.query_points(memory_query)
        # Memory points should be mostly deleted (older than 12 hours)
        assert len(remaining_memory) < len(memory_points)