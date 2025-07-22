"""
Unit tests for metrics storage and retrieval system.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.metrics.models import MetricValue
from src.metrics.storage import (
    TimeSeriesStorage,
    RetentionManager,
    MetricsQueryInterface,
    StorageManager
)
from src.metrics.storage.retention_manager import RetentionRule, RetentionPolicy
from src.metrics.storage.query_interface import QueryFilter, AggregationQuery, AggregationType, TimeRange


class TestTimeSeriesStorage:
    """Test cases for TimeSeriesStorage."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_metrics.db")
            storage = TimeSeriesStorage(db_path)
            yield storage
            storage.close()
    
    def test_store_single_metric(self, temp_storage):
        """Test storing a single metric."""
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            timestamp=datetime.now(),
            labels={"container": "test", "service": "web"},
            unit="percent"
        )
        
        success = temp_storage.store_metric(metric)
        assert success is True
    
    def test_store_multiple_metrics(self, temp_storage):
        """Test batch storing of metrics."""
        metrics = []
        base_time = datetime.now()
        
        for i in range(10):
            metrics.append(MetricValue(
                name=f"test_metric_{i % 3}",
                value=float(i * 10),
                timestamp=base_time + timedelta(seconds=i),
                labels={"container": f"container_{i}", "index": str(i)}
            ))
        
        stored_count = temp_storage.store_metrics(metrics)
        assert stored_count == 10
    
    def test_query_metrics_by_name(self, temp_storage):
        """Test querying metrics by name."""
        # Store test metrics
        metrics = [
            MetricValue("cpu_usage", 50.0, datetime.now(), {"container": "web"}),
            MetricValue("memory_usage", 75.0, datetime.now(), {"container": "web"}),
            MetricValue("cpu_usage", 60.0, datetime.now(), {"container": "db"})
        ]
        
        temp_storage.store_metrics(metrics)
        
        # Query CPU metrics
        cpu_metrics = temp_storage.query_metrics(metric_name="cpu_usage")
        assert len(cpu_metrics) == 2
        assert all(m.name == "cpu_usage" for m in cpu_metrics)
    
    def test_query_metrics_by_time_range(self, temp_storage):
        """Test querying metrics by time range."""
        base_time = datetime.now()
        
        # Store metrics across different times
        metrics = [
            MetricValue("test_metric", 1.0, base_time - timedelta(hours=2)),
            MetricValue("test_metric", 2.0, base_time - timedelta(hours=1)),
            MetricValue("test_metric", 3.0, base_time),
        ]
        
        temp_storage.store_metrics(metrics)
        
        # Query last hour
        recent_metrics = temp_storage.query_metrics(
            metric_name="test_metric",
            start_time=base_time - timedelta(minutes=30)
        )
        
        assert len(recent_metrics) == 1
        assert recent_metrics[0].value == 3.0
    
    def test_query_metrics_by_labels(self, temp_storage):
        """Test querying metrics by labels."""
        metrics = [
            MetricValue("test_metric", 1.0, datetime.now(), {"env": "prod", "service": "web"}),
            MetricValue("test_metric", 2.0, datetime.now(), {"env": "dev", "service": "web"}),
            MetricValue("test_metric", 3.0, datetime.now(), {"env": "prod", "service": "db"})
        ]
        
        temp_storage.store_metrics(metrics)
        
        # Query production metrics
        prod_metrics = temp_storage.query_metrics(
            metric_name="test_metric",
            labels={"env": "prod"}
        )
        
        assert len(prod_metrics) == 2
        assert all(m.labels["env"] == "prod" for m in prod_metrics)
    
    def test_aggregate_metrics(self, temp_storage):
        """Test metrics aggregation."""
        base_time = datetime.now()
        
        # Store metrics over time
        metrics = []
        for i in range(10):
            metrics.append(MetricValue(
                name="test_metric",
                value=float(i + 1),  # Values 1-10
                timestamp=base_time + timedelta(minutes=i * 5),
                labels={"container": "test"}
            ))
        
        temp_storage.store_metrics(metrics)
        
        # Test aggregation
        aggregated = temp_storage.aggregate_metrics(
            metric_name="test_metric",
            aggregation="avg",
            start_time=base_time,
            end_time=base_time + timedelta(hours=1),
            interval=timedelta(minutes=15)
        )
        
        assert len(aggregated) > 0
        # Should have aggregated values
        for timestamp, value in aggregated:
            assert isinstance(timestamp, datetime)
            assert isinstance(value, (int, float))
    
    def test_delete_metrics(self, temp_storage):
        """Test deleting metrics."""
        base_time = datetime.now()
        
        # Store test metrics
        metrics = [
            MetricValue("old_metric", 1.0, base_time - timedelta(days=2)),
            MetricValue("recent_metric", 2.0, base_time),
        ]
        
        temp_storage.store_metrics(metrics)
        
        # Delete old metrics
        deleted_count = temp_storage.delete_metrics(
            before_time=base_time - timedelta(days=1)
        )
        
        assert deleted_count == 1
        
        # Verify only recent metric remains
        remaining = temp_storage.query_metrics()
        assert len(remaining) == 1
        assert remaining[0].name == "recent_metric"
    
    def test_get_metric_names(self, temp_storage):
        """Test getting metric names."""
        metrics = [
            MetricValue("cpu_usage", 1.0, datetime.now()),
            MetricValue("memory_usage", 2.0, datetime.now()),
            MetricValue("cpu_usage", 3.0, datetime.now())  # Duplicate name
        ]
        
        temp_storage.store_metrics(metrics)
        
        names = temp_storage.get_metric_names()
        assert set(names) == {"cpu_usage", "memory_usage"}
    
    def test_get_label_values(self, temp_storage):
        """Test getting label values."""
        metrics = [
            MetricValue("test_metric", 1.0, datetime.now(), {"env": "prod"}),
            MetricValue("test_metric", 2.0, datetime.now(), {"env": "dev"}),
            MetricValue("test_metric", 3.0, datetime.now(), {"env": "prod"})  # Duplicate
        ]
        
        temp_storage.store_metrics(metrics)
        
        env_values = temp_storage.get_label_values("env")
        assert set(env_values) == {"prod", "dev"}
    
    def test_storage_stats(self, temp_storage):
        """Test getting storage statistics."""
        # Store some test data
        metrics = [
            MetricValue("metric_a", 1.0, datetime.now()),
            MetricValue("metric_b", 2.0, datetime.now()),
            MetricValue("metric_a", 3.0, datetime.now())
        ]
        
        temp_storage.store_metrics(metrics)
        
        stats = temp_storage.get_storage_stats()
        
        assert stats["total_metrics"] == 3
        assert "metric_a" in stats["metrics_by_name"]
        assert "metric_b" in stats["metrics_by_name"]
        assert stats["metrics_by_name"]["metric_a"] == 2
        assert stats["metrics_by_name"]["metric_b"] == 1


class TestRetentionManager:
    """Test cases for RetentionManager."""
    
    @pytest.fixture
    def temp_retention_manager(self):
        """Create temporary retention manager for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_retention.db")
            storage = TimeSeriesStorage(db_path)
            manager = RetentionManager(storage)
            yield manager
            storage.close()
    
    def test_add_retention_rule(self, temp_retention_manager):
        """Test adding retention rules."""
        rule = RetentionRule(
            metric_pattern="test_*",
            retention_period=timedelta(days=7),
            priority=10
        )
        
        temp_retention_manager.add_retention_rule(rule)
        
        assert len(temp_retention_manager.retention_rules) == 1
        assert temp_retention_manager.retention_rules[0].metric_pattern == "test_*"
    
    def test_retention_rule_matching(self, temp_retention_manager):
        """Test retention rule matching."""
        rule = RetentionRule(
            metric_pattern="cpu_*",
            retention_period=timedelta(days=7),
            labels={"env": "prod"}
        )
        
        # Test pattern matching
        assert rule.matches_metric("cpu_usage") is True
        assert rule.matches_metric("memory_usage") is False
        
        # Test label matching
        assert rule.matches_metric("cpu_usage", {"env": "prod"}) is True
        assert rule.matches_metric("cpu_usage", {"env": "dev"}) is False
        assert rule.matches_metric("cpu_usage", {}) is False
    
    def test_get_retention_period(self, temp_retention_manager):
        """Test getting retention period for metrics."""
        # Add rules with different priorities
        rule1 = RetentionRule("cpu_*", timedelta(days=3), priority=10)
        rule2 = RetentionRule("*", timedelta(days=30), priority=1)  # Lower priority
        
        temp_retention_manager.add_retention_rule(rule1)
        temp_retention_manager.add_retention_rule(rule2)
        
        # CPU metrics should match higher priority rule
        cpu_retention = temp_retention_manager.get_retention_period("cpu_usage")
        assert cpu_retention == timedelta(days=3)
        
        # Other metrics should match lower priority rule
        memory_retention = temp_retention_manager.get_retention_period("memory_usage")
        assert memory_retention == timedelta(days=30)
    
    def test_apply_retention_policy_dry_run(self, temp_retention_manager):
        """Test retention policy dry run."""
        storage = temp_retention_manager.storage
        
        # Add old and new metrics
        old_time = datetime.now() - timedelta(days=10)
        new_time = datetime.now()
        
        metrics = [
            MetricValue("old_metric", 1.0, old_time),
            MetricValue("new_metric", 2.0, new_time)
        ]
        
        storage.store_metrics(metrics)
        
        # Add retention rule
        rule = RetentionRule("*", timedelta(days=5))
        temp_retention_manager.add_retention_rule(rule)
        
        # Dry run
        stats = temp_retention_manager.apply_retention_policy(dry_run=True)
        
        assert stats["total_deleted"] == 1
        assert "old_metric" in stats["deleted_by_metric"]
        
        # Verify no actual deletion occurred
        remaining = storage.query_metrics()
        assert len(remaining) == 2
    
    def test_apply_retention_policy_actual(self, temp_retention_manager):
        """Test actual retention policy application."""
        storage = temp_retention_manager.storage
        
        # Add old metrics
        old_time = datetime.now() - timedelta(days=10)
        metrics = [MetricValue("old_metric", 1.0, old_time)]
        storage.store_metrics(metrics)
        
        # Add retention rule
        rule = RetentionRule("*", timedelta(days=5))
        temp_retention_manager.add_retention_rule(rule)
        
        # Apply policy
        stats = temp_retention_manager.apply_retention_policy(dry_run=False)
        
        assert stats["total_deleted"] == 1
        
        # Verify actual deletion
        remaining = storage.query_metrics()
        assert len(remaining) == 0
    
    def test_setup_default_rules(self, temp_retention_manager):
        """Test setting up default retention rules."""
        temp_retention_manager.setup_default_rules()
        
        assert len(temp_retention_manager.retention_rules) > 0
        
        # Check some expected patterns
        patterns = [rule.metric_pattern for rule in temp_retention_manager.retention_rules]
        assert "container_cpu_*" in patterns
        assert "container_lifecycle_*" in patterns


class TestMetricsQueryInterface:
    """Test cases for MetricsQueryInterface."""
    
    @pytest.fixture
    def temp_query_interface(self):
        """Create temporary query interface for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_query.db")
            storage = TimeSeriesStorage(db_path)
            interface = MetricsQueryInterface(storage)
            
            # Add test data
            base_time = datetime.now()
            test_metrics = []
            
            for i in range(20):
                test_metrics.extend([
                    MetricValue(
                        name="cpu_usage",
                        value=50.0 + (i % 10),
                        timestamp=base_time + timedelta(minutes=i),
                        labels={"container": f"web-{i % 3}", "env": "prod"}
                    ),
                    MetricValue(
                        name="memory_usage",
                        value=70.0 + (i % 5),
                        timestamp=base_time + timedelta(minutes=i),
                        labels={"container": f"web-{i % 3}", "env": "prod"}
                    )
                ])
            
            storage.store_metrics(test_metrics)
            
            yield interface
            storage.close()
    
    def test_basic_query(self, temp_query_interface):
        """Test basic metric query."""
        filters = QueryFilter(
            metric_names=["cpu_usage"],
            limit=10
        )
        
        result = temp_query_interface.query(filters)
        
        assert len(result.metrics) == 10
        assert all(m.name == "cpu_usage" for m in result.metrics)
        assert result.total_count == 10
        assert result.query_time_ms > 0
    
    def test_query_with_time_range(self, temp_query_interface):
        """Test query with time range."""
        filters = QueryFilter(
            metric_names=["cpu_usage"],
            time_range=TimeRange.LAST_HOUR
        )
        
        result = temp_query_interface.query(filters)
        
        assert len(result.metrics) > 0
        # All metrics should be within the last hour
        cutoff = datetime.now() - timedelta(hours=1)
        assert all(m.timestamp >= cutoff for m in result.metrics)
    
    def test_query_with_labels(self, temp_query_interface):
        """Test query with label filters."""
        filters = QueryFilter(
            metric_names=["cpu_usage"],
            labels={"env": "prod"}
        )
        
        result = temp_query_interface.query(filters)
        
        assert len(result.metrics) > 0
        assert all(m.labels.get("env") == "prod" for m in result.metrics)
    
    def test_aggregation_query(self, temp_query_interface):
        """Test aggregation query."""
        query = AggregationQuery(
            metric_name="cpu_usage",
            aggregation=AggregationType.AVG,
            interval=timedelta(minutes=5)
        )
        
        result = temp_query_interface.aggregate(query)
        
        assert len(result.data_points) > 0
        assert result.aggregation_type == AggregationType.AVG
        assert result.total_samples > 0
        
        # Check data point format
        for timestamp, value in result.data_points:
            assert isinstance(timestamp, datetime)
            assert isinstance(value, (int, float))
    
    def test_get_metric_statistics(self, temp_query_interface):
        """Test getting metric statistics."""
        stats = temp_query_interface.get_metric_statistics("cpu_usage")
        
        assert "statistics" in stats
        assert "min" in stats["statistics"]
        assert "max" in stats["statistics"]
        assert "avg" in stats["statistics"]
        assert "percentiles" in stats["statistics"]
        assert stats["sample_count"] > 0
    
    def test_find_anomalies(self, temp_query_interface):
        """Test anomaly detection."""
        # Add some extreme values to create anomalies
        extreme_metrics = [
            MetricValue("cpu_usage", 999.0, datetime.now(), {"container": "anomaly"}),
            MetricValue("cpu_usage", -50.0, datetime.now(), {"container": "anomaly"})
        ]
        
        temp_query_interface.storage.store_metrics(extreme_metrics)
        
        anomalies = temp_query_interface.find_anomalies("cpu_usage", threshold_multiplier=1.5)
        
        # Should find the extreme values
        assert len(anomalies) >= 2
        extreme_values = [m.value for m in anomalies]
        assert 999.0 in extreme_values or -50.0 in extreme_values
    
    def test_get_top_metrics(self, temp_query_interface):
        """Test getting top metrics."""
        top_metrics = temp_query_interface.get_top_metrics(
            aggregation=AggregationType.AVG,
            limit=5
        )
        
        assert len(top_metrics) <= 5
        assert len(top_metrics) > 0
        
        # Should be sorted by aggregated value
        for i in range(1, len(top_metrics)):
            assert top_metrics[i-1]["aggregated_value"] >= top_metrics[i]["aggregated_value"]


class TestStorageManager:
    """Test cases for StorageManager."""
    
    @pytest.fixture
    def temp_storage_manager(self):
        """Create temporary storage manager for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'database_path': os.path.join(temp_dir, "test_manager.db"),
                'auto_cleanup': False,  # Disable for testing
                'setup_default_retention': True
            }
            
            manager = StorageManager(config)
            yield manager
            manager.storage.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_storage_manager):
        """Test storage manager initialization."""
        success = await temp_storage_manager.initialize()
        assert success is True
    
    def test_store_and_query_metrics(self, temp_storage_manager):
        """Test storing and querying through storage manager."""
        # Store metrics
        metrics = [
            MetricValue("test_metric", 1.0, datetime.now(), {"service": "web"}),
            MetricValue("test_metric", 2.0, datetime.now(), {"service": "db"})
        ]
        
        stored_count = temp_storage_manager.store_metrics(metrics)
        assert stored_count == 2
        
        # Query metrics
        filters = QueryFilter(metric_names=["test_metric"])
        result_metrics = temp_storage_manager.query_metrics(filters)
        
        assert len(result_metrics) == 2
    
    def test_retention_management(self, temp_storage_manager):
        """Test retention management through storage manager."""
        # Add retention rule
        temp_storage_manager.add_retention_rule("test_*", retention_days=7)
        
        # Get retention summary
        summary = temp_storage_manager.get_retention_summary()
        
        assert summary["total_rules"] > 0
        
        # Check if our rule is there
        rule_patterns = [rule["pattern"] for rule in summary["rules"]]
        assert "test_*" in rule_patterns
    
    def test_storage_stats(self, temp_storage_manager):
        """Test getting storage statistics."""
        # Add some test data
        metrics = [MetricValue("test_metric", 1.0, datetime.now())]
        temp_storage_manager.store_metrics(metrics)
        
        stats = temp_storage_manager.get_storage_stats()
        
        assert "storage" in stats
        assert "retention" in stats
        assert stats["storage"]["total_metrics"] >= 1
    
    def test_health_check(self, temp_storage_manager):
        """Test storage manager health check."""
        health = temp_storage_manager.health_check()
        
        assert "status" in health
        assert "checks" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Should have basic checks
        expected_checks = ["write", "read", "delete", "retention"]
        for check in expected_checks:
            assert check in health["checks"]
    
    def test_export_metrics(self, temp_storage_manager):
        """Test exporting metrics."""
        # Store test data
        metrics = [
            MetricValue("export_test", 1.0, datetime.now(), {"test": "true"}),
            MetricValue("export_test", 2.0, datetime.now(), {"test": "true"})
        ]
        temp_storage_manager.store_metrics(metrics)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            success = temp_storage_manager.export_metrics(export_path, format="json")
            assert success is True
            
            # Verify file exists and has content
            assert os.path.exists(export_path)
            assert os.path.getsize(export_path) > 0
            
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])