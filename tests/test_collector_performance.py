"""
Performance tests for metrics collectors.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from statistics import mean, stdev

from src.metrics import (
    CollectorRegistry,
    collector_factory,
    CollectorConfig
)
from src.metrics.collectors import CPUCollector, MemoryCollector


class TestCollectorPerformance:
    """Performance tests for metrics collectors."""
    
    @pytest.fixture
    def mock_fast_docker_environment(self):
        """Setup a fast-responding mock Docker environment."""
        mock_container = Mock()
        mock_container.name = "perf-test-container"
        mock_container.image.tags = ["nginx:latest"]
        
        # Minimal stats for fast response
        mock_stats = {
            'cpu_stats': {
                'cpu_usage': {'total_usage': 1000000, 'percpu_usage': [500000, 500000]},
                'system_cpu_usage': 10000000
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 500000},
                'system_cpu_usage': 8000000
            },
            'memory_stats': {'usage': 1000000, 'limit': 2000000},
            'networks': {'eth0': {'rx_bytes': 1000, 'tx_bytes': 1000, 'rx_packets': 10, 'tx_packets': 10}},
            'blkio_stats': {
                'io_service_bytes_recursive': [{'op': 'Read', 'value': 1000}, {'op': 'Write', 'value': 1000}],
                'io_serviced_recursive': [{'op': 'Read', 'value': 10}, {'op': 'Write', 'value': 10}]
            }
        }
        
        mock_container.stats.return_value = mock_stats
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_client.ping.return_value = True
        
        return mock_client
    
    @pytest.mark.asyncio
    async def test_single_collector_performance(self, mock_fast_docker_environment):
        """Test performance of a single collector."""
        collector = CPUCollector(CollectorConfig(name="perf_cpu_collector"))
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_fast_docker_environment
            
            await collector.initialize()
            
            # Warm up
            await collector.collect_container_metrics("test-container")
            
            # Performance test
            iterations = 100
            times = []
            
            for _ in range(iterations):
                start_time = time.perf_counter()
                metrics = await collector.collect_container_metrics("test-container")
                end_time = time.perf_counter()
                
                times.append(end_time - start_time)
                assert len(metrics) > 0  # Ensure we got metrics
            
            # Calculate statistics
            avg_time = mean(times)
            max_time = max(times)
            min_time = min(times)
            std_dev = stdev(times) if len(times) > 1 else 0
            
            print(f"\nSingle Collector Performance ({iterations} iterations):")
            print(f"  Average time: {avg_time:.4f}s")
            print(f"  Min time: {min_time:.4f}s")
            print(f"  Max time: {max_time:.4f}s")
            print(f"  Std deviation: {std_dev:.4f}s")
            
            # Performance assertions
            assert avg_time < 0.1, f"Average collection time too slow: {avg_time:.4f}s"
            assert max_time < 0.5, f"Max collection time too slow: {max_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_multiple_collectors_performance(self, mock_fast_docker_environment):
        """Test performance of multiple collectors working together."""
        registry = CollectorRegistry()
        
        # Create all default collectors
        collectors = collector_factory.create_default_collectors()
        for collector in collectors.values():
            registry.register_collector(collector)
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_fast_docker_environment
            
            await registry.initialize_all()
            
            # Warm up
            await registry.collect_all_metrics("test-container")
            
            # Performance test
            iterations = 50
            times = []
            
            for _ in range(iterations):
                start_time = time.perf_counter()
                metrics = await registry.collect_all_metrics("test-container")
                end_time = time.perf_counter()
                
                times.append(end_time - start_time)
                assert len(metrics) > 0
            
            # Calculate statistics
            avg_time = mean(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"\nMultiple Collectors Performance ({iterations} iterations):")
            print(f"  Average time: {avg_time:.4f}s")
            print(f"  Min time: {min_time:.4f}s")
            print(f"  Max time: {max_time:.4f}s")
            print(f"  Collectors count: {len(collectors)}")
            
            # Performance assertions (more lenient for multiple collectors)
            assert avg_time < 0.5, f"Average collection time too slow: {avg_time:.4f}s"
            assert max_time < 2.0, f"Max collection time too slow: {max_time:.4f}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_collection_performance(self, mock_fast_docker_environment):
        """Test performance when collecting from multiple containers concurrently."""
        registry = CollectorRegistry()
        
        # Use fewer collectors for this test to focus on concurrency
        cpu_collector = CPUCollector(CollectorConfig(name="cpu_collector"))
        memory_collector = MemoryCollector(CollectorConfig(name="memory_collector"))
        
        registry.register_collector(cpu_collector)
        registry.register_collector(memory_collector)
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_fast_docker_environment
            
            await registry.initialize_all()
            
            # Test concurrent collection from multiple containers
            container_count = 20
            container_ids = [f"container-{i}" for i in range(container_count)]
            
            # Sequential collection (baseline)
            start_time = time.perf_counter()
            sequential_results = []
            for container_id in container_ids:
                metrics = await registry.collect_all_metrics(container_id)
                sequential_results.append(metrics)
            sequential_time = time.perf_counter() - start_time
            
            # Concurrent collection
            start_time = time.perf_counter()
            concurrent_tasks = [
                registry.collect_all_metrics(container_id) 
                for container_id in container_ids
            ]
            concurrent_results = await asyncio.gather(*concurrent_tasks)
            concurrent_time = time.perf_counter() - start_time
            
            print(f"\nConcurrent Collection Performance ({container_count} containers):")
            print(f"  Sequential time: {sequential_time:.4f}s")
            print(f"  Concurrent time: {concurrent_time:.4f}s")
            print(f"  Speedup: {sequential_time / concurrent_time:.2f}x")
            
            # Verify results are equivalent
            assert len(sequential_results) == len(concurrent_results)
            for seq_result, conc_result in zip(sequential_results, concurrent_results):
                assert len(seq_result) == len(conc_result)
            
            # Concurrent should be significantly faster
            assert concurrent_time < sequential_time * 0.8, "Concurrent collection not faster enough"
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, mock_fast_docker_environment):
        """Test that collectors don't have memory leaks during extended operation."""
        import psutil
        import gc
        
        collector = CPUCollector(CollectorConfig(name="memory_test_collector"))
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_fast_docker_environment
            
            await collector.initialize()
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Run many collection cycles
            iterations = 1000
            for i in range(iterations):
                metrics = await collector.collect_container_metrics(f"container-{i % 10}")
                assert len(metrics) > 0
                
                # Force garbage collection periodically
                if i % 100 == 0:
                    gc.collect()
            
            # Get final memory usage
            gc.collect()  # Final cleanup
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            print(f"\nMemory Usage Test ({iterations} iterations):")
            print(f"  Initial memory: {initial_memory / (1024 * 1024):.2f} MB")
            print(f"  Final memory: {final_memory / (1024 * 1024):.2f} MB")
            print(f"  Memory increase: {memory_increase_mb:.2f} MB")
            
            # Memory increase should be reasonable (less than 50MB for 1000 iterations)
            assert memory_increase_mb < 50, f"Memory usage increased too much: {memory_increase_mb:.2f} MB"
    
    @pytest.mark.asyncio
    async def test_error_handling_performance_impact(self, mock_fast_docker_environment):
        """Test that error handling doesn't significantly impact performance."""
        collector = CPUCollector(CollectorConfig(name="error_test_collector"))
        
        with patch('docker.from_env') as mock_docker:
            mock_docker.return_value = mock_fast_docker_environment
            
            await collector.initialize()
            
            # Test normal operation performance
            normal_times = []
            for _ in range(50):
                start_time = time.perf_counter()
                metrics = await collector.collect_container_metrics("valid-container")
                end_time = time.perf_counter()
                normal_times.append(end_time - start_time)
                assert len(metrics) > 0
            
            # Test error handling performance
            mock_docker.return_value.containers.get.side_effect = Exception("Container not found")
            
            error_times = []
            for _ in range(50):
                start_time = time.perf_counter()
                metrics = await collector.collect_container_metrics("invalid-container")
                end_time = time.perf_counter()
                error_times.append(end_time - start_time)
                assert len(metrics) == 0  # Should return empty list on error
            
            normal_avg = mean(normal_times)
            error_avg = mean(error_times)
            
            print(f"\nError Handling Performance Impact:")
            print(f"  Normal operation avg: {normal_avg:.4f}s")
            print(f"  Error handling avg: {error_avg:.4f}s")
            print(f"  Overhead: {((error_avg - normal_avg) / normal_avg * 100):.1f}%")
            
            # Error handling shouldn't be more than 2x slower
            assert error_avg < normal_avg * 2, "Error handling too slow"
    
    @pytest.mark.asyncio
    async def test_collector_initialization_performance(self):
        """Test collector initialization performance."""
        
        # Test single collector initialization
        start_time = time.perf_counter()
        collector = CPUCollector(CollectorConfig(name="init_test_collector"))
        
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client
            
            success = await collector.initialize()
            
        init_time = time.perf_counter() - start_time
        
        assert success is True
        print(f"\nSingle Collector Initialization: {init_time:.4f}s")
        assert init_time < 1.0, f"Initialization too slow: {init_time:.4f}s"
        
        # Test multiple collectors initialization
        registry = CollectorRegistry()
        collectors = collector_factory.create_default_collectors()
        
        for collector in collectors.values():
            registry.register_collector(collector)
        
        start_time = time.perf_counter()
        
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_docker.return_value = mock_client
            
            results = await registry.initialize_all()
        
        total_init_time = time.perf_counter() - start_time
        
        assert all(results.values())
        print(f"Multiple Collectors Initialization ({len(collectors)} collectors): {total_init_time:.4f}s")
        assert total_init_time < 5.0, f"Multiple initialization too slow: {total_init_time:.4f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements