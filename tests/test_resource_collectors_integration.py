"""
Integration tests for resource metrics collectors working together.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.metrics import (
    CollectorRegistry,
    collector_factory,
    CollectorConfig,
    create_collector_builder
)
from src.metrics.collectors import (
    CPUCollector,
    MemoryCollector,
    NetworkCollector,
    DiskCollector
)


class TestResourceCollectorsIntegration:
    """Integration tests for all resource collectors working together."""
    
    @pytest.fixture
    def mock_docker_environment(self):
        """Setup a mock Docker environment for testing."""
        mock_container = Mock()
        mock_container.name = "test-web-server"
        mock_container.image.tags = ["nginx:1.21"]
        
        # Mock comprehensive stats
        mock_stats = {
            # CPU stats
            'cpu_stats': {
                'cpu_usage': {
                    'total_usage': 2000000000,
                    'percpu_usage': [1000000000, 1000000000]
                },
                'system_cpu_usage': 10000000000
            },
            'precpu_stats': {
                'cpu_usage': {
                    'total_usage': 1000000000
                },
                'system_cpu_usage': 8000000000
            },
            # Memory stats
            'memory_stats': {
                'usage': 268435456,  # 256MB
                'limit': 536870912   # 512MB
            },
            # Network stats
            'networks': {
                'eth0': {
                    'rx_bytes': 2048000,
                    'tx_bytes': 1024000,
                    'rx_packets': 2000,
                    'tx_packets': 1000
                }
            },
            # Block I/O stats
            'blkio_stats': {
                'io_service_bytes_recursive': [
                    {'op': 'Read', 'value': 10485760},   # 10MB read
                    {'op': 'Write', 'value': 5242880},   # 5MB write
                ],
                'io_serviced_recursive': [
                    {'op': 'Read', 'value': 1000},       # 1000 read ops
                    {'op': 'Write', 'value': 500},       # 500 write ops
                ]
            }
        }
        
        mock_container.stats.return_value = mock_stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_client.ping.return_value = True
        
        return mock_client
    
    @pytest.mark.asyncio
    async def test_all_collectors_initialization(self, mock_docker_environment):
        """Test that all resource collectors can be initialized together."""
        registry = CollectorRegistry()
        
        # Create all resource collectors
        collectors = {
            'cpu': CPUCollector(CollectorConfig(name="cpu_collector")),
            'memory': MemoryCollector(CollectorConfig(name="memory_collector")),
            'network': NetworkCollector(CollectorConfig(name="network_collector")),
            'disk': DiskCollector(CollectorConfig(name="disk_collector"))
        }
        
        # Register all collectors
        for collector in collectors.values():
            registry.register_collector(collector)
        
        # Mock Docker for all collectors
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_docker_environment
            
            # Initialize all collectors
            results = await registry.initialize_all()
            
            # All should initialize successfully
            assert all(results.values())
            assert len(results) == 4
    
    @pytest.mark.asyncio
    async def test_comprehensive_metrics_collection(self, mock_docker_environment):
        """Test collecting comprehensive metrics from all collectors."""
        registry = CollectorRegistry()
        
        # Create collectors using factory
        collectors = {
            'cpu': collector_factory.create_collector('cpu', CollectorConfig(name="cpu_collector")),
            'memory': collector_factory.create_collector('memory', CollectorConfig(name="memory_collector")),
            'network': collector_factory.create_collector('network', CollectorConfig(name="network_collector")),
            'disk': collector_factory.create_collector('disk', CollectorConfig(name="disk_collector"))
        }
        
        # Register collectors
        for collector in collectors.values():
            if collector:
                registry.register_collector(collector)
        
        # Mock Docker environment
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_docker_environment
            
            # Initialize collectors
            await registry.initialize_all()
            
            # Collect metrics for a container
            container_id = "test-container-123"
            all_metrics = await registry.collect_all_metrics(container_id)
            
            # Should have metrics from all collectors
            assert len(all_metrics) > 0
            
            # Group metrics by type
            metric_names = [m.name for m in all_metrics]
            
            # Check we have CPU metrics
            cpu_metrics = [m for m in all_metrics if 'cpu' in m.name]
            assert len(cpu_metrics) > 0
            
            # Check we have memory metrics
            memory_metrics = [m for m in all_metrics if 'memory' in m.name]
            assert len(memory_metrics) > 0
            
            # Check we have network metrics
            network_metrics = [m for m in all_metrics if 'network' in m.name]
            assert len(network_metrics) > 0
            
            # Check we have disk metrics
            disk_metrics = [m for m in all_metrics if 'disk' in m.name]
            assert len(disk_metrics) > 0
            
            # Verify all metrics have proper labels
            for metric in all_metrics:
                assert 'container_id' in metric.labels
                assert 'container_name' in metric.labels
                assert 'image' in metric.labels
                assert 'runtime' in metric.labels
                assert metric.labels['container_id'] == container_id
    
    @pytest.mark.asyncio
    async def test_collector_performance_under_load(self, mock_docker_environment):
        """Test collector performance when collecting from multiple containers."""
        registry = CollectorRegistry()
        
        # Create collectors
        collectors = collector_factory.create_default_collectors()
        for collector in collectors.values():
            registry.register_collector(collector)
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_docker_environment
            
            await registry.initialize_all()
            
            # Simulate collecting from multiple containers
            container_ids = [f"container-{i}" for i in range(10)]
            
            start_time = datetime.now()
            
            # Collect metrics from all containers concurrently
            tasks = [
                registry.collect_all_metrics(container_id) 
                for container_id in container_ids
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert duration < 5.0  # 5 seconds for 10 containers
            
            # All collections should succeed
            for result in results:
                assert not isinstance(result, Exception)
                assert isinstance(result, list)
                assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_mixed_runtime_environment(self):
        """Test collectors working in mixed Docker/Podman environment."""
        registry = CollectorRegistry()
        
        # Create collectors with different runtime preferences
        cpu_collector = CPUCollector(CollectorConfig(name="cpu_collector"))
        memory_collector = MemoryCollector(CollectorConfig(name="memory_collector"))
        
        registry.register_collector(cpu_collector)
        registry.register_collector(memory_collector)
        
        # Mock Docker available for CPU collector
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client
            
            # Initialize collectors
            results = await registry.initialize_all()
            
            # Both should initialize (CPU with Docker, Memory with fallback)
            assert results['cpu_collector'] is True
            assert results['memory_collector'] is True
    
    @pytest.mark.asyncio
    async def test_collector_failure_isolation(self, mock_docker_environment):
        """Test that failure in one collector doesn't affect others."""
        registry = CollectorRegistry()
        
        # Create collectors
        cpu_collector = CPUCollector(CollectorConfig(name="cpu_collector"))
        memory_collector = MemoryCollector(CollectorConfig(name="memory_collector"))
        
        registry.register_collector(cpu_collector)
        registry.register_collector(memory_collector)
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_docker_environment
            
            await registry.initialize_all()
            
            # Make CPU collector fail
            cpu_collector.collect_container_metrics = AsyncMock(
                side_effect=Exception("CPU collector failed")
            )
            
            # Collect metrics
            metrics = await registry.collect_all_metrics("test-container")
            
            # Should still have metrics from memory collector
            memory_metrics = [m for m in metrics if 'memory' in m.name]
            assert len(memory_metrics) > 0
            
            # CPU collector should have recorded the error
            assert cpu_collector.status.error_count > 0
            assert "CPU collector failed" in cpu_collector.status.last_error
    
    @pytest.mark.asyncio
    async def test_custom_collector_integration(self):
        """Test integrating custom collectors with built-in ones."""
        
        # Create a custom collector
        class CustomCollector:
            def __init__(self, config):
                self.config = config
                self.status = Mock()
                self.status.is_healthy = True
            
            async def initialize(self):
                return True
            
            async def cleanup(self):
                pass
            
            def is_enabled(self):
                return True
            
            def get_status(self):
                return self.status
            
            async def collect_with_error_handling(self, target):
                from src.metrics.models import MetricValue
                return [
                    MetricValue(
                        name="custom_metric",
                        value=42.0,
                        timestamp=datetime.now(),
                        labels={"container_id": target, "type": "custom"}
                    )
                ]
        
        registry = CollectorRegistry()
        
        # Add built-in collector
        cpu_collector = CPUCollector(CollectorConfig(name="cpu_collector"))
        registry.register_collector(cpu_collector)
        
        # Add custom collector
        custom_collector = CustomCollector(CollectorConfig(name="custom_collector"))
        registry.register_collector(custom_collector)
        
        # Initialize
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client
            
            await registry.initialize_all()
            
            # Collect metrics
            metrics = await registry.collect_all_metrics("test-container")
            
            # Should have metrics from both collectors
            custom_metrics = [m for m in metrics if m.name == "custom_metric"]
            assert len(custom_metrics) == 1
            assert custom_metrics[0].value == 42.0
    
    @pytest.mark.asyncio
    async def test_prometheus_format_consistency(self, mock_docker_environment):
        """Test that all collectors produce consistent Prometheus format."""
        registry = CollectorRegistry()
        
        # Create all collectors
        collectors = collector_factory.create_default_collectors()
        for collector in collectors.values():
            registry.register_collector(collector)
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_docker_environment
            
            await registry.initialize_all()
            
            # Collect metrics
            metrics = await registry.collect_all_metrics("test-container")
            
            # Convert all metrics to Prometheus format
            prometheus_lines = [m.to_prometheus_format() for m in metrics]
            
            # All lines should be valid Prometheus format
            for line in prometheus_lines:
                assert isinstance(line, str)
                assert len(line) > 0
                
                # Should contain metric name, value, and timestamp
                parts = line.split()
                assert len(parts) >= 2  # metric_name{labels} value [timestamp]
                
                # Metric name should not be empty
                metric_part = parts[0]
                assert len(metric_part) > 0
                
                # Value should be numeric
                value_part = parts[1]
                try:
                    float(value_part)
                except ValueError:
                    pytest.fail(f"Invalid numeric value in Prometheus line: {line}")
    
    @pytest.mark.asyncio
    async def test_collector_configuration_flexibility(self):
        """Test that collectors can be configured with different parameters."""
        
        # Create collectors with different configurations
        configs = [
            CollectorConfig(
                name="fast_cpu_collector",
                collection_interval=10,
                timeout=5,
                custom_labels={"priority": "high"}
            ),
            CollectorConfig(
                name="slow_memory_collector", 
                collection_interval=60,
                timeout=30,
                custom_labels={"priority": "low"}
            )
        ]
        
        collectors = []
        for config in configs:
            if "cpu" in config.name:
                collector = CPUCollector(config)
            else:
                collector = MemoryCollector(config)
            collectors.append(collector)
        
        # Verify configurations are applied
        assert collectors[0].config.collection_interval == 10
        assert collectors[0].config.custom_labels["priority"] == "high"
        
        assert collectors[1].config.collection_interval == 60
        assert collectors[1].config.custom_labels["priority"] == "low"
        
        # Test that custom labels appear in metrics
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_container = Mock()
            mock_container.name = "test"
            mock_container.image.tags = ["test:latest"]
            mock_container.stats.return_value = {
                'cpu_stats': {'cpu_usage': {'total_usage': 1000, 'percpu_usage': [500, 500]}, 'system_cpu_usage': 10000},
                'precpu_stats': {'cpu_usage': {'total_usage': 500}, 'system_cpu_usage': 8000},
                'memory_stats': {'usage': 1000000, 'limit': 2000000}
            }
            mock_client.containers.get.return_value = mock_container
            mock_docker.return_value = mock_client
            
            await collectors[0].initialize()
            await collectors[1].initialize()
            
            cpu_metrics = await collectors[0].collect_container_metrics("test")
            memory_metrics = await collectors[1].collect_container_metrics("test")
            
            # Check custom labels are present
            if cpu_metrics:
                assert cpu_metrics[0].labels["priority"] == "high"
            if memory_metrics:
                assert memory_metrics[0].labels["priority"] == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])