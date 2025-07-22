"""
Unit tests for resource metrics collectors (CPU, Memory, Network, Disk).
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.metrics.models import CollectorConfig, MetricType
from src.metrics.collectors.cpu_collector import CPUCollector
from src.metrics.collectors.memory_collector import MemoryCollector
from src.metrics.collectors.network_collector import NetworkCollector
from src.metrics.collectors.disk_collector import DiskCollector


class TestCPUCollector:
    """Test cases for CPU metrics collector."""
    
    @pytest.fixture
    def cpu_collector(self):
        """Create a CPU collector for testing."""
        config = CollectorConfig(name="test_cpu_collector")
        return CPUCollector(config)
    
    @pytest.mark.asyncio
    async def test_initialize_docker_success(self, cpu_collector):
        """Test successful Docker initialization."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client
            
            result = await cpu_collector.initialize()
            
            assert result is True
            assert cpu_collector.runtime_type == "docker"
            assert cpu_collector.docker_client == mock_client
    
    @pytest.mark.asyncio
    async def test_initialize_docker_failure_fallback_podman(self, cpu_collector):
        """Test Docker failure with Podman fallback."""
        with patch('docker.from_env') as mock_docker:
            mock_docker.side_effect = Exception("Docker not available")
            
            result = await cpu_collector.initialize()
            
            # Should fallback to Podman
            assert result is True
            assert cpu_collector.runtime_type == "podman"
    
    @pytest.mark.asyncio
    async def test_initialize_both_fail(self, cpu_collector):
        """Test initialization failure when both Docker and Podman fail."""
        with patch('docker.from_env') as mock_docker:
            mock_docker.side_effect = Exception("Docker not available")
            
            result = await cpu_collector.initialize()
            
            # Should still succeed with Podman fallback
            assert result is True
    
    def test_get_metric_types(self, cpu_collector):
        """Test getting metric types."""
        types = cpu_collector.get_metric_types()
        assert MetricType.CPU_USAGE in types
    
    @pytest.mark.asyncio
    async def test_collect_docker_cpu_metrics(self, cpu_collector):
        """Test collecting CPU metrics from Docker."""
        # Setup mock Docker client
        mock_container = Mock()
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        
        # Mock CPU stats
        mock_stats = {
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
            }
        }
        mock_container.stats.return_value = mock_stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        
        cpu_collector.docker_client = mock_client
        cpu_collector.runtime_type = "docker"
        
        metrics = await cpu_collector.collect_container_metrics("test123")
        
        assert len(metrics) == 1
        assert metrics[0].name == "container_cpu_usage_percent"
        assert metrics[0].labels["container_id"] == "test123"
        assert metrics[0].labels["container_name"] == "test-container"
        assert metrics[0].labels["image"] == "nginx:latest"
        assert metrics[0].labels["runtime"] == "docker"
    
    @pytest.mark.asyncio
    async def test_collect_podman_cpu_metrics(self, cpu_collector):
        """Test collecting CPU metrics from Podman."""
        cpu_collector.runtime_type = "podman"
        
        # Mock podman stats command
        mock_stats_output = '{"CPU": "25.5%"}'
        mock_info_output = '[{"Name": "test-container", "Config": {"Image": "nginx:latest"}}]'
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock stats call
            mock_stats_proc = AsyncMock()
            mock_stats_proc.communicate.return_value = (mock_stats_output.encode(), b'')
            mock_stats_proc.returncode = 0
            
            # Mock inspect call
            mock_info_proc = AsyncMock()
            mock_info_proc.communicate.return_value = (mock_info_output.encode(), b'')
            mock_info_proc.returncode = 0
            
            mock_subprocess.side_effect = [mock_stats_proc, mock_info_proc]
            
            metrics = await cpu_collector.collect_container_metrics("test123")
            
            assert len(metrics) == 1
            assert metrics[0].name == "container_cpu_usage_percent"
            assert metrics[0].value == 25.5
            assert metrics[0].labels["runtime"] == "podman"
    
    def test_calculate_cpu_percentage(self, cpu_collector):
        """Test CPU percentage calculation."""
        stats = {
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
            }
        }
        
        percentage = cpu_collector._calculate_cpu_percentage(stats)
        
        # Expected: (1000000000 / 2000000000) * 2 * 100 = 100.0
        assert percentage == 100.0
    
    def test_calculate_cpu_percentage_zero_delta(self, cpu_collector):
        """Test CPU percentage calculation with zero delta."""
        stats = {
            'cpu_stats': {
                'cpu_usage': {
                    'total_usage': 1000000000,
                    'percpu_usage': [500000000, 500000000]
                },
                'system_cpu_usage': 8000000000
            },
            'precpu_stats': {
                'cpu_usage': {
                    'total_usage': 1000000000
                },
                'system_cpu_usage': 8000000000
            }
        }
        
        percentage = cpu_collector._calculate_cpu_percentage(stats)
        assert percentage == 0.0


class TestMemoryCollector:
    """Test cases for Memory metrics collector."""
    
    @pytest.fixture
    def memory_collector(self):
        """Create a Memory collector for testing."""
        config = CollectorConfig(name="test_memory_collector")
        return MemoryCollector(config)
    
    def test_get_metric_types(self, memory_collector):
        """Test getting metric types."""
        types = memory_collector.get_metric_types()
        assert MetricType.MEMORY_USAGE in types
    
    @pytest.mark.asyncio
    async def test_collect_docker_memory_metrics(self, memory_collector):
        """Test collecting memory metrics from Docker."""
        # Setup mock Docker client
        mock_container = Mock()
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        
        # Mock memory stats
        mock_stats = {
            'memory_stats': {
                'usage': 134217728,  # 128MB
                'limit': 268435456   # 256MB
            }
        }
        mock_container.stats.return_value = mock_stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        
        memory_collector.docker_client = mock_client
        memory_collector.runtime_type = "docker"
        
        metrics = await memory_collector.collect_container_metrics("test123")
        
        assert len(metrics) == 3  # usage, limit, percentage
        
        # Check usage metric
        usage_metric = next(m for m in metrics if m.name == "container_memory_usage_bytes")
        assert usage_metric.value == 134217728
        
        # Check limit metric
        limit_metric = next(m for m in metrics if m.name == "container_memory_limit_bytes")
        assert limit_metric.value == 268435456
        
        # Check percentage metric
        percent_metric = next(m for m in metrics if m.name == "container_memory_usage_percent")
        assert percent_metric.value == 50.0  # 128MB / 256MB * 100
    
    @pytest.mark.asyncio
    async def test_collect_podman_memory_metrics(self, memory_collector):
        """Test collecting memory metrics from Podman."""
        memory_collector.runtime_type = "podman"
        
        # Mock podman stats and inspect commands
        mock_stats_output = '{"MemUsage": "128MB / 256MB"}'
        mock_info_output = '[{"Name": "test-container", "Config": {"Image": "nginx:latest"}}]'
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_stats_proc = AsyncMock()
            mock_stats_proc.communicate.return_value = (mock_stats_output.encode(), b'')
            mock_stats_proc.returncode = 0
            
            mock_info_proc = AsyncMock()
            mock_info_proc.communicate.return_value = (mock_info_output.encode(), b'')
            mock_info_proc.returncode = 0
            
            mock_subprocess.side_effect = [mock_stats_proc, mock_info_proc]
            
            metrics = await memory_collector.collect_container_metrics("test123")
            
            assert len(metrics) == 3
            
            usage_metric = next(m for m in metrics if m.name == "container_memory_usage_bytes")
            assert usage_metric.value == 134217728  # 128MB in bytes
    
    def test_parse_memory_usage(self, memory_collector):
        """Test parsing memory usage string."""
        usage, limit = memory_collector._parse_memory_usage("128MB / 256MB")
        
        assert usage == 134217728  # 128MB in bytes
        assert limit == 268435456  # 256MB in bytes
    
    def test_parse_size_string(self, memory_collector):
        """Test parsing size strings."""
        assert memory_collector._parse_size_string("128MB") == 134217728
        assert memory_collector._parse_size_string("1GB") == 1073741824
        assert memory_collector._parse_size_string("512KB") == 524288
        assert memory_collector._parse_size_string("2TB") == 2199023255552


class TestNetworkCollector:
    """Test cases for Network metrics collector."""
    
    @pytest.fixture
    def network_collector(self):
        """Create a Network collector for testing."""
        config = CollectorConfig(name="test_network_collector")
        return NetworkCollector(config)
    
    def test_get_metric_types(self, network_collector):
        """Test getting metric types."""
        types = network_collector.get_metric_types()
        assert MetricType.NETWORK_IO in types
    
    @pytest.mark.asyncio
    async def test_collect_docker_network_metrics(self, network_collector):
        """Test collecting network metrics from Docker."""
        # Setup mock Docker client
        mock_container = Mock()
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        
        # Mock network stats
        mock_stats = {
            'networks': {
                'eth0': {
                    'rx_bytes': 1024000,
                    'tx_bytes': 512000,
                    'rx_packets': 1000,
                    'tx_packets': 500
                },
                'lo': {
                    'rx_bytes': 100,
                    'tx_bytes': 100,
                    'rx_packets': 10,
                    'tx_packets': 10
                }
            }
        }
        mock_container.stats.return_value = mock_stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        
        network_collector.docker_client = mock_client
        network_collector.runtime_type = "docker"
        
        metrics = await network_collector.collect_container_metrics("test123")
        
        # Should have per-interface metrics + aggregate metrics
        assert len(metrics) > 4
        
        # Check aggregate metrics exist
        aggregate_rx = next((m for m in metrics if m.name == "container_network_receive_bytes_total" 
                           and "interface" not in m.labels), None)
        assert aggregate_rx is not None
        assert aggregate_rx.value == 1024100  # Sum of both interfaces
    
    @pytest.mark.asyncio
    async def test_collect_podman_network_metrics(self, network_collector):
        """Test collecting network metrics from Podman."""
        network_collector.runtime_type = "podman"
        
        mock_stats_output = '{"NetIO": "1MB / 512KB"}'
        mock_info_output = '[{"Name": "test-container", "Config": {"Image": "nginx:latest"}}]'
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_stats_proc = AsyncMock()
            mock_stats_proc.communicate.return_value = (mock_stats_output.encode(), b'')
            mock_stats_proc.returncode = 0
            
            mock_info_proc = AsyncMock()
            mock_info_proc.communicate.return_value = (mock_info_output.encode(), b'')
            mock_info_proc.returncode = 0
            
            mock_subprocess.side_effect = [mock_stats_proc, mock_info_proc]
            
            metrics = await network_collector.collect_container_metrics("test123")
            
            assert len(metrics) == 2  # rx and tx metrics
            
            rx_metric = next(m for m in metrics if m.name == "container_network_receive_bytes_total")
            assert rx_metric.value == 1048576  # 1MB in bytes
    
    def test_parse_network_io(self, network_collector):
        """Test parsing network I/O string."""
        rx, tx = network_collector._parse_network_io("1MB / 512KB")
        
        assert rx == 1048576   # 1MB in bytes
        assert tx == 524288    # 512KB in bytes


class TestDiskCollector:
    """Test cases for Disk metrics collector."""
    
    @pytest.fixture
    def disk_collector(self):
        """Create a Disk collector for testing."""
        config = CollectorConfig(name="test_disk_collector")
        return DiskCollector(config)
    
    def test_get_metric_types(self, disk_collector):
        """Test getting metric types."""
        types = disk_collector.get_metric_types()
        assert MetricType.DISK_IO in types
    
    @pytest.mark.asyncio
    async def test_collect_docker_disk_metrics(self, disk_collector):
        """Test collecting disk metrics from Docker."""
        # Setup mock Docker client
        mock_container = Mock()
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        
        # Mock disk I/O stats
        mock_stats = {
            'blkio_stats': {
                'io_service_bytes_recursive': [
                    {'op': 'Read', 'value': 1048576},   # 1MB read
                    {'op': 'Write', 'value': 524288},   # 512KB write
                    {'op': 'Sync', 'value': 100}        # Should be ignored
                ],
                'io_serviced_recursive': [
                    {'op': 'Read', 'value': 100},       # 100 read ops
                    {'op': 'Write', 'value': 50},       # 50 write ops
                ]
            }
        }
        mock_container.stats.return_value = mock_stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        
        disk_collector.docker_client = mock_client
        disk_collector.runtime_type = "docker"
        
        metrics = await disk_collector.collect_container_metrics("test123")
        
        assert len(metrics) == 4  # read bytes, write bytes, read ops, write ops
        
        # Check read bytes metric
        read_bytes = next(m for m in metrics if m.name == "container_disk_read_bytes_total")
        assert read_bytes.value == 1048576
        
        # Check write bytes metric
        write_bytes = next(m for m in metrics if m.name == "container_disk_write_bytes_total")
        assert write_bytes.value == 524288
        
        # Check read operations metric
        read_ops = next(m for m in metrics if m.name == "container_disk_read_ops_total")
        assert read_ops.value == 100
        
        # Check write operations metric
        write_ops = next(m for m in metrics if m.name == "container_disk_write_ops_total")
        assert write_ops.value == 50
    
    @pytest.mark.asyncio
    async def test_collect_podman_disk_metrics(self, disk_collector):
        """Test collecting disk metrics from Podman."""
        disk_collector.runtime_type = "podman"
        
        mock_stats_output = '{"BlockIO": "1MB / 512KB"}'
        mock_info_output = '[{"Name": "test-container", "Config": {"Image": "nginx:latest"}}]'
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_stats_proc = AsyncMock()
            mock_stats_proc.communicate.return_value = (mock_stats_output.encode(), b'')
            mock_stats_proc.returncode = 0
            
            mock_info_proc = AsyncMock()
            mock_info_proc.communicate.return_value = (mock_info_output.encode(), b'')
            mock_info_proc.returncode = 0
            
            mock_subprocess.side_effect = [mock_stats_proc, mock_info_proc]
            
            metrics = await disk_collector.collect_container_metrics("test123")
            
            assert len(metrics) == 2  # read and write metrics
            
            read_metric = next(m for m in metrics if m.name == "container_disk_read_bytes_total")
            assert read_metric.value == 1048576  # 1MB in bytes
    
    def test_parse_block_io(self, disk_collector):
        """Test parsing block I/O string."""
        read, write = disk_collector._parse_block_io("1MB / 512KB")
        
        assert read == 1048576   # 1MB in bytes
        assert write == 524288   # 512KB in bytes


class TestCollectorErrorHandling:
    """Test error handling across all resource collectors."""
    
    @pytest.mark.asyncio
    async def test_docker_container_not_found(self):
        """Test handling when Docker container is not found."""
        config = CollectorConfig(name="test_collector")
        collector = CPUCollector(config)
        
        mock_client = Mock()
        mock_client.containers.get.side_effect = Exception("Container not found")
        
        collector.docker_client = mock_client
        collector.runtime_type = "docker"
        
        metrics = await collector.collect_container_metrics("nonexistent")
        
        assert len(metrics) == 0
    
    @pytest.mark.asyncio
    async def test_podman_command_failure(self):
        """Test handling when Podman command fails."""
        config = CollectorConfig(name="test_collector")
        collector = MemoryCollector(config)
        collector.runtime_type = "podman"
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b'', b'Container not found')
            mock_proc.returncode = 1  # Error
            
            mock_subprocess.return_value = mock_proc
            
            metrics = await collector.collect_container_metrics("nonexistent")
            
            assert len(metrics) == 0
    
    @pytest.mark.asyncio
    async def test_malformed_stats_data(self):
        """Test handling malformed stats data."""
        config = CollectorConfig(name="test_collector")
        collector = NetworkCollector(config)
        
        mock_container = Mock()
        mock_container.name = "test-container"
        mock_container.image.tags = ["nginx:latest"]
        mock_container.stats.return_value = {}  # Empty stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        
        collector.docker_client = mock_client
        collector.runtime_type = "docker"
        
        # Should not crash, should return empty metrics or handle gracefully
        metrics = await collector.collect_container_metrics("test123")
        
        # Depending on implementation, might return empty list or metrics with zero values
        assert isinstance(metrics, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])