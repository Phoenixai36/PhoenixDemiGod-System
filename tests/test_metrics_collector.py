"""
Unit tests for the metrics collector framework.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.metrics.models import (
    MetricType, MetricValue, ContainerMetrics, 
    CollectorConfig, CollectorStatus
)
from src.metrics.collector_interface import (
    MetricsCollector, ContainerMetricsCollector, 
    CollectorRegistry, CollectionError
)
from src.metrics.collector_factory import (
    CollectorFactory, CollectorBuilder
)


class TestMetricValue:
    """Test cases for MetricValue model."""
    
    def test_metric_value_creation(self):
        """Test creating a MetricValue instance."""
        timestamp = datetime.now()
        labels = {"container_id": "test123", "name": "test-container"}
        
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            timestamp=timestamp,
            labels=labels,
            unit="percent"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.timestamp == timestamp
        assert metric.labels == labels
        assert metric.unit == "percent"
    
    def test_prometheus_format(self):
        """Test converting MetricValue to Prometheus format."""
        timestamp = datetime.now()
        labels = {"container_id": "test123", "name": "test-container"}
        
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            timestamp=timestamp,
            labels=labels
        )
        
        prometheus_str = metric.to_prometheus_format()
        expected_timestamp = int(timestamp.timestamp() * 1000)
        
        assert "test_metric" in prometheus_str
        assert "42.5" in prometheus_str
        assert str(expected_timestamp) in prometheus_str
        assert 'container_id="test123"' in prometheus_str
        assert 'name="test-container"' in prometheus_str


class TestContainerMetrics:
    """Test cases for ContainerMetrics model."""
    
    def test_container_metrics_creation(self):
        """Test creating a ContainerMetrics instance."""
        metrics = ContainerMetrics(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            cpu_usage_percent=25.5,
            memory_usage_bytes=1024*1024*100,  # 100MB
            restart_count=2
        )
        
        assert metrics.container_id == "test123"
        assert metrics.container_name == "test-container"
        assert metrics.image == "nginx:latest"
        assert metrics.cpu_usage_percent == 25.5
        assert metrics.memory_usage_bytes == 1024*1024*100
        assert metrics.restart_count == 2
    
    def test_to_metric_values(self):
        """Test converting ContainerMetrics to MetricValue list."""
        metrics = ContainerMetrics(
            container_id="test123",
            container_name="test-container",
            image="nginx:latest",
            cpu_usage_percent=25.5,
            memory_usage_bytes=1024*1024*100,
            restart_count=2
        )
        
        metric_values = metrics.to_metric_values()
        
        # Should have metrics for CPU, memory, and restart count
        assert len(metric_values) >= 3
        
        # Check that all metrics have correct labels
        for metric in metric_values:
            assert metric.labels["container_id"] == "test123"
            assert metric.labels["container_name"] == "test-container"
            assert metric.labels["image"] == "nginx:latest"
        
        # Check specific metrics exist
        metric_names = [m.name for m in metric_values]
        assert "container_cpu_usage_percent" in metric_names
        assert "container_memory_usage_bytes" in metric_names
        assert "container_restarts_total" in metric_names


class MockCollector(ContainerMetricsCollector):
    """Mock collector for testing."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.initialize_called = False
        self.cleanup_called = False
        self.collect_calls = []
    
    async def initialize(self) -> bool:
        self.initialize_called = True
        return True
    
    async def cleanup(self) -> None:
        self.cleanup_called = True
    
    def get_metric_types(self) -> list[MetricType]:
        return [MetricType.CPU_USAGE]
    
    async def collect_container_metrics(self, container_id: str) -> list[MetricValue]:
        self.collect_calls.append(container_id)
        return [
            MetricValue(
                name="test_metric",
                value=42.0,
                timestamp=datetime.now(),
                labels={"container_id": container_id}
            )
        ]


class TestCollectorRegistry:
    """Test cases for CollectorRegistry."""
    
    def test_register_collector(self):
        """Test registering a collector."""
        registry = CollectorRegistry()
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        registry.register_collector(collector)
        
        assert "test_collector" in registry._collectors
        assert registry.get_collector("test_collector") == collector
    
    def test_unregister_collector(self):
        """Test unregistering a collector."""
        registry = CollectorRegistry()
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        registry.register_collector(collector)
        registry.unregister_collector("test_collector")
        
        assert "test_collector" not in registry._collectors
        assert registry.get_collector("test_collector") is None
    
    def test_get_enabled_collectors(self):
        """Test getting only enabled collectors."""
        registry = CollectorRegistry()
        
        # Create enabled collector
        enabled_config = CollectorConfig(name="enabled_collector", enabled=True)
        enabled_collector = MockCollector(enabled_config)
        
        # Create disabled collector
        disabled_config = CollectorConfig(name="disabled_collector", enabled=False)
        disabled_collector = MockCollector(disabled_config)
        
        registry.register_collector(enabled_collector)
        registry.register_collector(disabled_collector)
        
        enabled_collectors = registry.get_enabled_collectors()
        
        assert "enabled_collector" in enabled_collectors
        assert "disabled_collector" not in enabled_collectors
    
    @pytest.mark.asyncio
    async def test_collect_all_metrics(self):
        """Test collecting metrics from all collectors."""
        registry = CollectorRegistry()
        
        config1 = CollectorConfig(name="collector1")
        collector1 = MockCollector(config1)
        
        config2 = CollectorConfig(name="collector2")
        collector2 = MockCollector(config2)
        
        registry.register_collector(collector1)
        registry.register_collector(collector2)
        
        metrics = await registry.collect_all_metrics("test_container")
        
        # Should have metrics from both collectors
        assert len(metrics) == 2
        
        # Both collectors should have been called
        assert "test_container" in collector1.collect_calls
        assert "test_container" in collector2.collect_calls
    
    @pytest.mark.asyncio
    async def test_initialize_all(self):
        """Test initializing all collectors."""
        registry = CollectorRegistry()
        
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        registry.register_collector(collector)
        
        results = await registry.initialize_all()
        
        assert results["test_collector"] is True
        assert collector.initialize_called
    
    @pytest.mark.asyncio
    async def test_cleanup_all(self):
        """Test cleaning up all collectors."""
        registry = CollectorRegistry()
        
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        registry.register_collector(collector)
        
        await registry.cleanup_all()
        
        assert collector.cleanup_called


class TestCollectorFactory:
    """Test cases for CollectorFactory."""
    
    def test_register_collector_type(self):
        """Test registering a collector type."""
        factory = CollectorFactory()
        
        factory.register_collector_type("mock", MockCollector)
        
        assert "mock" in factory._collector_types
        assert factory._collector_types["mock"] == MockCollector
    
    def test_create_collector(self):
        """Test creating a collector instance."""
        factory = CollectorFactory()
        factory.register_collector_type("mock", MockCollector)
        
        config = CollectorConfig(name="test_collector")
        collector = factory.create_collector("mock", config)
        
        assert collector is not None
        assert isinstance(collector, MockCollector)
        assert collector.config.name == "test_collector"
    
    def test_create_collector_unknown_type(self):
        """Test creating collector with unknown type."""
        factory = CollectorFactory()
        
        config = CollectorConfig(name="test_collector")
        collector = factory.create_collector("unknown", config)
        
        assert collector is None
    
    def test_get_available_types(self):
        """Test getting available collector types."""
        factory = CollectorFactory()
        factory.register_collector_type("mock1", MockCollector)
        factory.register_collector_type("mock2", MockCollector)
        
        types = factory.get_available_types()
        
        assert "mock1" in types
        assert "mock2" in types


class TestCollectorBuilder:
    """Test cases for CollectorBuilder."""
    
    def test_builder_pattern(self):
        """Test using the builder pattern to create collectors."""
        factory = CollectorFactory()
        factory.register_collector_type("mock", MockCollector)
        
        builder = CollectorBuilder(factory)
        
        collector = (builder
                    .name("test_collector")
                    .enabled(True)
                    .interval(60)
                    .timeout(30)
                    .custom_labels({"env": "test"})
                    .build("mock"))
        
        assert collector is not None
        assert collector.config.name == "test_collector"
        assert collector.config.enabled is True
        assert collector.config.collection_interval == 60
        assert collector.config.timeout == 30
        assert collector.config.custom_labels == {"env": "test"}
    
    def test_builder_missing_name(self):
        """Test builder fails when name is missing."""
        factory = CollectorFactory()
        factory.register_collector_type("mock", MockCollector)
        
        builder = CollectorBuilder(factory)
        
        with pytest.raises(ValueError, match="Collector name is required"):
            builder.build("mock")


class TestMetricsCollectorErrorHandling:
    """Test error handling in metrics collectors."""
    
    @pytest.mark.asyncio
    async def test_collect_with_error_handling_success(self):
        """Test successful collection with error handling."""
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        metrics = await collector.collect_with_error_handling("test_container")
        
        assert len(metrics) == 1
        assert collector.status.success_count == 1
        assert collector.status.error_count == 0
        assert collector.status.is_healthy is True
    
    @pytest.mark.asyncio
    async def test_collect_with_error_handling_failure(self):
        """Test collection failure with error handling."""
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        # Mock the collect_metrics method to raise an exception
        collector.collect_container_metrics = AsyncMock(side_effect=Exception("Test error"))
        
        metrics = await collector.collect_with_error_handling("test_container")
        
        assert len(metrics) == 0
        assert collector.status.success_count == 0
        assert collector.status.error_count == 1
        assert collector.status.last_error == "Test error"
    
    @pytest.mark.asyncio
    async def test_collector_becomes_unhealthy_after_errors(self):
        """Test collector becomes unhealthy after too many errors."""
        config = CollectorConfig(name="test_collector")
        collector = MockCollector(config)
        
        # Mock the collect_metrics method to always raise an exception
        collector.collect_container_metrics = AsyncMock(side_effect=Exception("Test error"))
        
        # Trigger multiple failures
        for _ in range(6):  # More than the threshold of 5
            await collector.collect_with_error_handling("test_container")
        
        assert collector.status.error_count == 6
        assert collector.status.is_healthy is False
    
    def test_disabled_collector_not_enabled(self):
        """Test that disabled collectors are not enabled."""
        config = CollectorConfig(name="test_collector", enabled=False)
        collector = MockCollector(config)
        
        assert collector.is_enabled() is False
    
    def test_unhealthy_collector_not_enabled(self):
        """Test that unhealthy collectors are not enabled."""
        config = CollectorConfig(name="test_collector", enabled=True)
        collector = MockCollector(config)
        collector.status.is_healthy = False
        
        assert collector.is_enabled() is False


if __name__ == "__main__":
    pytest.main([__file__])