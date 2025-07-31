"""
Configuration and fixtures for performance tests
"""

import pytest
import psutil
import time
from pathlib import Path


def pytest_configure(config):
    """Configure pytest for performance testing"""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "load: mark test as a load test"
    )
    config.addinivalue_line(
        "markers", "memory: mark test as a memory test"
    )
    config.addinivalue_line(
        "markers", "scalability: mark test as a scalability test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture(scope="session")
def system_info():
    """Provide system information for performance tests"""
    return {
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': psutil.virtual_memory().total / (1024**3),
        'platform': psutil.os.name,
        'python_version': pytest.__version__
    }


@pytest.fixture
def performance_thresholds(system_info):
    """Provide performance thresholds based on system capabilities"""
    
    # Adjust thresholds based on system specs
    cpu_factor = max(1.0, 4.0 / system_info['cpu_count'])  # Scale for CPU cores
    memory_factor = max(1.0, 8.0 / system_info['memory_total_gb'])  # Scale for memory
    
    return {
        'file_scan_time_per_file_ms': 1.0 * cpu_factor,
        'component_evaluation_time_ms': 50.0 * cpu_factor,
        'dependency_analysis_time_ms': 100.0 * cpu_factor,
        'memory_per_file_mb': 0.01 * memory_factor,
        'memory_per_component_mb': 0.1 * memory_factor,
        'max_memory_usage_mb': 100.0 * memory_factor,
        'concurrent_speedup_factor': 0.7,  # Expect at least 70% of theoretical speedup
    }


@pytest.fixture
def performance_monitor():
    """Fixture for monitoring performance during tests"""
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
            self.process = psutil.Process()
            
        def start(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
        def stop(self):
            self.end_time = time.time()
            self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
            
        @property
        def memory_delta(self):
            if self.start_memory and self.end_memory:
                return self.end_memory - self.start_memory
            return 0
            
        def assert_performance(self, max_duration=None, max_memory_mb=None):
            if max_duration and self.duration > max_duration:
                pytest.fail(f"Performance test exceeded time limit: {self.duration:.2f}s > {max_duration}s")
            
            if max_memory_mb and self.memory_delta > max_memory_mb:
                pytest.fail(f"Performance test exceeded memory limit: {self.memory_delta:.2f}MB > {max_memory_mb}MB")
    
    return PerformanceMonitor()


@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure for testing"""
    import tempfile
    
    def _create_structure(num_files=100, num_dirs=10):
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir)
        
        # Create directory structure
        for i in range(num_dirs):
            dir_path = base_path / f"module_{i}"
            dir_path.mkdir()
            
            # Create files in each directory
            files_per_dir = num_files // num_dirs
            for j in range(files_per_dir):
                file_path = dir_path / f"file_{j}.py"
                content = f"# Module {i}, File {j}\nclass Component{j}:\n    pass\n"
                file_path.write_text(content)
        
        return base_path
    
    return _create_structure


def pytest_runtest_setup(item):
    """Setup for performance tests"""
    if "performance" in item.keywords or "load" in item.keywords or "memory" in item.keywords:
        # Ensure we have enough system resources
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            pytest.skip("System memory usage too high for performance testing")
        
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            pytest.skip("System CPU usage too high for performance testing")


def pytest_runtest_teardown(item):
    """Cleanup after performance tests"""
    if "performance" in item.keywords or "load" in item.keywords or "memory" in item.keywords:
        # Force garbage collection after performance tests
        import gc
        gc.collect()


@pytest.fixture(autouse=True)
def performance_test_timeout():
    """Automatically timeout long-running performance tests"""
    import signal
    
    def timeout_handler(signum, frame):
        pytest.fail("Performance test timed out")
    
    # Set a 5-minute timeout for performance tests
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes
    
    yield
    
    signal.alarm(0)  # Cancel the alarm


class PerformanceAssertion:
    """Helper class for performance assertions"""
    
    @staticmethod
    def assert_execution_time(actual_time, expected_max_time, operation_name="Operation"):
        """Assert that execution time is within expected bounds"""
        if actual_time > expected_max_time:
            pytest.fail(
                f"{operation_name} took too long: {actual_time:.3f}s > {expected_max_time:.3f}s"
            )
    
    @staticmethod
    def assert_memory_usage(actual_memory_mb, expected_max_mb, operation_name="Operation"):
        """Assert that memory usage is within expected bounds"""
        if actual_memory_mb > expected_max_mb:
            pytest.fail(
                f"{operation_name} used too much memory: {actual_memory_mb:.2f}MB > {expected_max_mb:.2f}MB"
            )
    
    @staticmethod
    def assert_throughput(operations, duration, min_ops_per_sec, operation_name="Operation"):
        """Assert that throughput meets minimum requirements"""
        actual_throughput = operations / duration if duration > 0 else 0
        if actual_throughput < min_ops_per_sec:
            pytest.fail(
                f"{operation_name} throughput too low: {actual_throughput:.1f} ops/sec < {min_ops_per_sec} ops/sec"
            )
    
    @staticmethod
    def assert_scalability(small_time, large_time, size_ratio, max_time_ratio, operation_name="Operation"):
        """Assert that operation scales reasonably with input size"""
        actual_time_ratio = large_time / small_time if small_time > 0 else float('inf')
        expected_max_ratio = size_ratio * max_time_ratio
        
        if actual_time_ratio > expected_max_ratio:
            pytest.fail(
                f"{operation_name} doesn't scale well: {actual_time_ratio:.2f}x time increase for {size_ratio}x size increase"
            )


@pytest.fixture
def perf_assert():
    """Fixture providing performance assertion helpers"""
    return PerformanceAssertion()