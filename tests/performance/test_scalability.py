"""
Performance and scalability tests for Phoenix Hydra System Review Tool
"""

import pytest
import time
import tempfile
import os
import psutil
import threading
import concurrent.futures
import asyncio
import statistics
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List, Dict, Any, Tuple

from src.phoenix_system_review.discovery.file_scanner import FileSystemScanner
from src.phoenix_system_review.discovery.config_parser import ConfigurationParser
from src.phoenix_system_review.discovery.service_discovery import ServiceDiscovery
from src.phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from src.phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer
from src.phoenix_system_review.analysis.quality_assessor import QualityAssessor
from src.phoenix_system_review.assessment.gap_analyzer import GapAnalyzer
from src.phoenix_system_review.assessment.completion_calculator import CompletionCalculator
from src.phoenix_system_review.assessment.priority_ranker import PriorityRanker


class PerformanceMetrics:
    """Helper class to collect and analyze performance metrics"""
    
    def __init__(self):
        self.execution_times = []
        self.memory_usage = []
        self.cpu_usage = []
        
    def record_execution_time(self, duration: float):
        self.execution_times.append(duration)
        
    def record_memory_usage(self, memory_mb: float):
        self.memory_usage.append(memory_mb)
        
    def record_cpu_usage(self, cpu_percent: float):
        self.cpu_usage.append(cpu_percent)
        
    def get_stats(self) -> Dict[str, Any]:
        return {
            'execution_time': {
                'mean': statistics.mean(self.execution_times) if self.execution_times else 0,
                'median': statistics.median(self.execution_times) if self.execution_times else 0,
                'max': max(self.execution_times) if self.execution_times else 0,
                'min': min(self.execution_times) if self.execution_times else 0
            },
            'memory_usage': {
                'mean': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max': max(self.memory_usage) if self.memory_usage else 0
            },
            'cpu_usage': {
                'mean': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max': max(self.cpu_usage) if self.cpu_usage else 0
            }
        }


def create_large_project_structure(base_path: Path, num_files: int = 1000, num_dirs: int = 100):
    """Create a large project structure for load testing"""
    
    # Create directory structure
    for i in range(num_dirs):
        dir_path = base_path / f"module_{i:03d}"
        dir_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        for j in range(3):
            subdir = dir_path / f"submodule_{j}"
            subdir.mkdir(exist_ok=True)
    
    # Create files with various extensions
    file_types = ['.py', '.js', '.yaml', '.json', '.md', '.txt', '.sh', '.ps1']
    
    for i in range(num_files):
        dir_idx = i % num_dirs
        subdir_idx = (i // num_dirs) % 3
        file_type = file_types[i % len(file_types)]
        
        file_path = base_path / f"module_{dir_idx:03d}" / f"submodule_{subdir_idx}" / f"file_{i:04d}{file_type}"
        
        # Create file with some content
        content = f"# File {i}\n" + "# Content line\n" * (i % 50 + 1)
        file_path.write_text(content)
    
    # Create configuration files
    config_files = [
        ('docker-compose.yaml', 'version: "3.8"\nservices:\n  app:\n    image: test\n'),
        ('package.json', '{"name": "test", "version": "1.0.0"}'),
        ('pyproject.toml', '[tool.pytest]\ntestpaths = ["tests"]'),
        ('.env', 'DEBUG=true\nPORT=8080'),
        ('config.json', '{"database": {"host": "localhost"}}')
    ]
    
    for filename, content in config_files:
        (base_path / filename).write_text(content)


@pytest.fixture
def large_project_structure():
    """Fixture that creates a large project structure for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        create_large_project_structure(base_path, num_files=500, num_dirs=50)
        yield base_path


@pytest.fixture
def performance_metrics():
    """Fixture that provides performance metrics collection"""
    return PerformanceMetrics()


class TestFileSystemScannerPerformance:
    """Performance tests for FileSystemScanner"""
    
    def test_large_directory_scan_performance(self, large_project_structure, performance_metrics):
        """Test file scanner performance with large directory structures"""
        scanner = FileSystemScanner(str(large_project_structure))
        
        # Performance test
        start_time = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        inventory = scanner.scan_project_structure()
        files = inventory.files
        
        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_used = final_memory - initial_memory
        
        performance_metrics.record_execution_time(execution_time)
        performance_metrics.record_memory_usage(memory_used)
        
        # Assertions
        assert len(files) > 500  # Should find all created files
        assert execution_time < 10.0  # Should complete within 10 seconds
        assert memory_used < 100  # Should use less than 100MB additional memory
        
        print(f"Scanned {len(files)} files in {execution_time:.2f}s using {memory_used:.2f}MB")
    
    def test_concurrent_directory_scans(self, large_project_structure, performance_metrics):
        """Test concurrent file scanning performance"""
        num_workers = 4
        
        def scan_worker():
            start_time = time.time()
            scanner = FileSystemScanner(str(large_project_structure))
            inventory = scanner.scan_project_structure()
            files = inventory.files
            end_time = time.time()
            return len(files), end_time - start_time
        
        # Run concurrent scans
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(scan_worker) for _ in range(num_workers)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Verify all scans completed successfully
        assert len(results) == num_workers
        for file_count, scan_time in results:
            assert file_count > 500
            performance_metrics.record_execution_time(scan_time)
        
        # Concurrent execution should not take much longer than sequential
        assert total_time < 15.0  # Should complete within 15 seconds
        
        print(f"Completed {num_workers} concurrent scans in {total_time:.2f}s")
    
    def test_memory_usage_scaling(self, performance_metrics):
        """Test memory usage scaling with increasing file counts"""
        file_counts = [100, 500, 1000, 2000]
        
        for file_count in file_counts:
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                create_large_project_structure(base_path, num_files=file_count, num_dirs=file_count//10)
                
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024
                
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files = inventory.files
                
                final_memory = process.memory_info().rss / 1024 / 1024
                memory_used = final_memory - initial_memory
                
                performance_metrics.record_memory_usage(memory_used)
                
                # Memory usage should scale reasonably
                memory_per_file = memory_used / len(files) if files else 0
                assert memory_per_file < 0.1  # Less than 0.1MB per file
                
                print(f"Files: {len(files)}, Memory: {memory_used:.2f}MB, Per file: {memory_per_file:.4f}MB")


class TestAnalysisEnginePerformance:
    """Performance tests for Analysis Engine components"""
    
    def test_component_evaluator_performance(self, large_project_structure, performance_metrics):
        """Test component evaluator performance with many components"""
        evaluator = ComponentEvaluator()
        
        # Create mock components
        components = []
        for i in range(100):
            component = Mock()
            component.name = f"component_{i}"
            component.type = "service"
            component.files = [f"file_{j}.py" for j in range(10)]
            components.append(component)
        
        start_time = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Evaluate all components
        results = []
        for component in components:
            result = evaluator.evaluate_component(component)
            results.append(result)
        
        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        execution_time = end_time - start_time
        memory_used = final_memory - initial_memory
        
        performance_metrics.record_execution_time(execution_time)
        performance_metrics.record_memory_usage(memory_used)
        
        # Assertions
        assert len(results) == 100
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert memory_used < 50  # Should use less than 50MB
        
        print(f"Evaluated {len(results)} components in {execution_time:.2f}s using {memory_used:.2f}MB")
    
    def test_dependency_analyzer_performance(self, performance_metrics):
        """Test dependency analyzer performance with complex dependency graphs"""
        analyzer = DependencyAnalyzer()
        
        # Create mock components with dependencies
        components = {}
        for i in range(50):
            component = Mock()
            component.name = f"component_{i}"
            component.dependencies = [f"component_{j}" for j in range(max(0, i-5), i)]
            components[component.name] = component
        
        start_time = time.time()
        
        # Analyze dependencies
        result = analyzer.analyze_dependencies(list(components.values()))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        performance_metrics.record_execution_time(execution_time)
        
        # Assertions
        assert result is not None
        assert execution_time < 3.0  # Should complete within 3 seconds
        
        print(f"Analyzed dependencies for {len(components)} components in {execution_time:.2f}s")
    
    def test_quality_assessor_performance(self, large_project_structure, performance_metrics):
        """Test quality assessor performance with many files"""
        assessor = QualityAssessor()
        
        # Get all Python files from the large project structure
        python_files = list(large_project_structure.rglob("*.py"))
        
        start_time = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Assess quality of all files
        results = []
        for file_path in python_files[:50]:  # Limit to first 50 files for performance
            result = assessor.assess_file_quality(str(file_path))
            results.append(result)
        
        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        execution_time = end_time - start_time
        memory_used = final_memory - initial_memory
        
        performance_metrics.record_execution_time(execution_time)
        performance_metrics.record_memory_usage(memory_used)
        
        # Assertions
        assert len(results) > 0
        assert execution_time < 10.0  # Should complete within 10 seconds
        
        print(f"Assessed quality of {len(results)} files in {execution_time:.2f}s")


class TestAssessmentEnginePerformance:
    """Performance tests for Assessment Engine components"""
    
    def test_gap_analyzer_performance(self, performance_metrics):
        """Test gap analyzer performance with many components"""
        analyzer = GapAnalyzer()
        
        # Create mock evaluation results
        evaluation_results = []
        for i in range(100):
            result = Mock()
            result.component_name = f"component_{i}"
            result.completion_percentage = (i * 7) % 100  # Varying completion
            result.issues = [f"issue_{j}" for j in range(i % 5)]
            evaluation_results.append(result)
        
        start_time = time.time()
        
        # Analyze gaps
        gap_result = analyzer.analyze_gaps(evaluation_results)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        performance_metrics.record_execution_time(execution_time)
        
        # Assertions
        assert gap_result is not None
        assert execution_time < 2.0  # Should complete within 2 seconds
        
        print(f"Analyzed gaps for {len(evaluation_results)} components in {execution_time:.2f}s")
    
    def test_completion_calculator_performance(self, performance_metrics):
        """Test completion calculator performance with many components"""
        calculator = CompletionCalculator()
        
        # Create mock components with varying completion
        components = []
        for i in range(200):
            component = Mock()
            component.name = f"component_{i}"
            component.completion_percentage = (i * 3) % 100
            component.weight = 1.0 + (i % 5) * 0.5  # Varying weights
            components.append(component)
        
        start_time = time.time()
        
        # Calculate completion
        result = calculator.calculate_completion(components)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        performance_metrics.record_execution_time(execution_time)
        
        # Assertions
        assert result is not None
        assert execution_time < 1.0  # Should complete within 1 second
        
        print(f"Calculated completion for {len(components)} components in {execution_time:.2f}s")
    
    def test_priority_ranker_performance(self, performance_metrics):
        """Test priority ranker performance with many tasks"""
        ranker = PriorityRanker()
        
        # Create mock tasks
        tasks = []
        for i in range(150):
            task = Mock()
            task.name = f"task_{i}"
            task.business_impact = (i % 10) + 1
            task.technical_complexity = (i % 5) + 1
            task.dependencies = [f"task_{j}" for j in range(max(0, i-3), i)]
            tasks.append(task)
        
        start_time = time.time()
        
        # Rank priorities
        result = ranker.rank_priorities(tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        performance_metrics.record_execution_time(execution_time)
        
        # Assertions
        assert result is not None
        assert execution_time < 2.0  # Should complete within 2 seconds
        
        print(f"Ranked priorities for {len(tasks)} tasks in {execution_time:.2f}s")


class TestConcurrentProcessing:
    """Tests for concurrent processing capabilities"""
    
    def test_concurrent_component_evaluation(self, performance_metrics):
        """Test concurrent evaluation of multiple components"""
        evaluator = ComponentEvaluator()
        
        # Create mock components
        components = []
        for i in range(20):
            component = Mock()
            component.name = f"component_{i}"
            component.type = "service"
            component.files = [f"file_{j}.py" for j in range(5)]
            components.append(component)
        
        def evaluate_component(component):
            start_time = time.time()
            result = evaluator.evaluate_component(component)
            end_time = time.time()
            return result, end_time - start_time
        
        # Test sequential processing
        start_time = time.time()
        sequential_results = [evaluate_component(comp) for comp in components]
        sequential_time = time.time() - start_time
        
        # Test concurrent processing
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_results = list(executor.map(evaluate_component, components))
        concurrent_time = time.time() - start_time
        
        performance_metrics.record_execution_time(sequential_time)
        performance_metrics.record_execution_time(concurrent_time)
        
        # Assertions
        assert len(sequential_results) == len(concurrent_results) == len(components)
        # Concurrent should be faster (allowing for some overhead)
        assert concurrent_time < sequential_time * 0.8
        
        print(f"Sequential: {sequential_time:.2f}s, Concurrent: {concurrent_time:.2f}s")
        print(f"Speedup: {sequential_time/concurrent_time:.2f}x")
    
    def test_concurrent_file_processing(self, large_project_structure, performance_metrics):
        """Test concurrent processing of multiple files"""
        scanner = FileSystemScanner()
        
        # Get files to process
        scanner = FileSystemScanner(str(large_project_structure))
        inventory = scanner.scan_project_structure()
        files = inventory.files[:100]  # Limit for performance
        
        def process_file(file_info):
            # Simulate file processing
            time.sleep(0.01)  # Small delay to simulate work
            file_path = Path(file_info.path)
            return len(file_path.read_text() if file_path.exists() else "")
        
        # Test sequential processing
        start_time = time.time()
        sequential_results = [process_file(f) for f in files]
        sequential_time = time.time() - start_time
        
        # Test concurrent processing
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            concurrent_results = list(executor.map(process_file, files))
        concurrent_time = time.time() - start_time
        
        performance_metrics.record_execution_time(sequential_time)
        performance_metrics.record_execution_time(concurrent_time)
        
        # Assertions
        assert len(sequential_results) == len(concurrent_results) == len(files)
        assert concurrent_time < sequential_time  # Should be faster
        
        print(f"Processed {len(files)} files:")
        print(f"Sequential: {sequential_time:.2f}s, Concurrent: {concurrent_time:.2f}s")
        print(f"Speedup: {sequential_time/concurrent_time:.2f}x")


class TestMemoryUsageAndLeaks:
    """Tests for memory usage and potential memory leaks"""
    
    def test_memory_usage_stability(self, performance_metrics):
        """Test memory usage stability over multiple operations"""
        evaluator = ComponentEvaluator()
        
        memory_readings = []
        process = psutil.Process()
        
        # Perform multiple operations and track memory
        for i in range(10):
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                create_large_project_structure(base_path, num_files=100, num_dirs=10)
                
                # Scan files
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files = inventory.files
                
                # Create and evaluate mock components
                components = []
                for j in range(20):
                    component = Mock()
                    component.name = f"component_{j}"
                    component.files = [f.path for f in files[:5]]
                    components.append(component)
                    evaluator.evaluate_component(component)
                
                # Record memory usage
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_readings.append(memory_mb)
                performance_metrics.record_memory_usage(memory_mb)
        
        # Check for memory leaks (memory should not continuously increase)
        if len(memory_readings) >= 5:
            early_avg = statistics.mean(memory_readings[:3])
            late_avg = statistics.mean(memory_readings[-3:])
            memory_increase = late_avg - early_avg
            
            # Memory increase should be minimal (less than 20MB)
            assert memory_increase < 20, f"Potential memory leak detected: {memory_increase:.2f}MB increase"
        
        print(f"Memory usage over {len(memory_readings)} iterations:")
        print(f"Min: {min(memory_readings):.2f}MB, Max: {max(memory_readings):.2f}MB")
        print(f"Average: {statistics.mean(memory_readings):.2f}MB")
    
    def test_large_dataset_memory_efficiency(self, performance_metrics):
        """Test memory efficiency with large datasets"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            # Create a very large project structure
            create_large_project_structure(base_path, num_files=2000, num_dirs=200)
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # Scan the large project structure
            scanner = FileSystemScanner(str(base_path))
            inventory = scanner.scan_project_structure()
            all_files = inventory.files
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_used = current_memory - initial_memory
            
            # Memory usage should not exceed reasonable limits
            assert memory_used < 200, f"Memory usage too high: {memory_used:.2f}MB"
            
            final_memory = process.memory_info().rss / 1024 / 1024
            total_memory_used = final_memory - initial_memory
            
            performance_metrics.record_memory_usage(total_memory_used)
            
            print(f"Processed {len(all_files)} files using {total_memory_used:.2f}MB")
            print(f"Memory per file: {total_memory_used/len(all_files):.4f}MB")


class TestScalabilityLimits:
    """Tests to determine system scalability limits"""
    
    def test_maximum_file_count_handling(self, performance_metrics):
        """Test handling of maximum file counts"""
        file_counts = [1000, 2000, 5000]
        
        for file_count in file_counts:
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                
                try:
                    create_large_project_structure(base_path, num_files=file_count, num_dirs=file_count//20)
                    
                    start_time = time.time()
                    scanner = FileSystemScanner(str(base_path))
                    inventory = scanner.scan_project_structure()
                    files = inventory.files
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    performance_metrics.record_execution_time(execution_time)
                    
                    # Should handle large file counts within reasonable time
                    time_per_file = execution_time / len(files) if files else float('inf')
                    assert time_per_file < 0.01, f"Too slow: {time_per_file:.4f}s per file"
                    
                    print(f"Handled {len(files)} files in {execution_time:.2f}s ({time_per_file:.4f}s per file)")
                    
                except Exception as e:
                    print(f"Failed at {file_count} files: {e}")
                    break
    
    def test_concurrent_user_simulation(self, performance_metrics):
        """Simulate multiple concurrent users of the system"""
        num_users = 5
        operations_per_user = 10
        
        def simulate_user(user_id):
            evaluator = ComponentEvaluator()
            results = []
            
            for i in range(operations_per_user):
                with tempfile.TemporaryDirectory() as temp_dir:
                    base_path = Path(temp_dir)
                    create_large_project_structure(base_path, num_files=50, num_dirs=5)
                    
                    start_time = time.time()
                    
                    # Simulate user operations
                    scanner = FileSystemScanner(str(base_path))
                    inventory = scanner.scan_project_structure()
                    files = inventory.files
                    
                    # Create mock component
                    component = Mock()
                    component.name = f"user_{user_id}_component_{i}"
                    component.files = [f.path for f in files[:10]]
                    
                    result = evaluator.evaluate_component(component)
                    
                    end_time = time.time()
                    results.append(end_time - start_time)
            
            return user_id, results
        
        # Run concurrent user simulations
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(num_users)]
            user_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        all_operation_times = []
        for user_id, operation_times in user_results:
            all_operation_times.extend(operation_times)
            for op_time in operation_times:
                performance_metrics.record_execution_time(op_time)
        
        avg_operation_time = statistics.mean(all_operation_times)
        max_operation_time = max(all_operation_times)
        
        # Assertions
        assert avg_operation_time < 2.0, f"Average operation too slow: {avg_operation_time:.2f}s"
        assert max_operation_time < 5.0, f"Slowest operation too slow: {max_operation_time:.2f}s"
        
        print(f"Simulated {num_users} concurrent users, {operations_per_user} ops each")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average operation time: {avg_operation_time:.2f}s")
        print(f"Max operation time: {max_operation_time:.2f}s")


@pytest.mark.performance
def test_performance_regression_suite(performance_metrics):
    """Comprehensive performance regression test suite"""
    
    # This test combines multiple performance aspects
    evaluator = ComponentEvaluator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        create_large_project_structure(base_path, num_files=1000, num_dirs=100)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Full workflow performance test
        start_time = time.time()
        
        # 1. Discovery phase
        scanner = FileSystemScanner(str(base_path))
        inventory = scanner.scan_project_structure()
        files = inventory.files
        discovery_time = time.time()
        
        # 2. Analysis phase
        components = []
        for i in range(0, len(files), 20):  # Create components from file groups
            component = Mock()
            component.name = f"component_{i//20}"
            component.files = [f.path for f in files[i:i+20]]
            components.append(component)
        
        evaluation_results = []
        for component in components:
            result = evaluator.evaluate_component(component)
            evaluation_results.append(result)
        
        analysis_time = time.time()
        
        # 3. Assessment phase (simulated)
        # In a real scenario, this would involve gap analysis, completion calculation, etc.
        assessment_results = []
        for result in evaluation_results:
            # Simulate assessment processing
            assessment_results.append({"component": result, "gaps": [], "completion": 85.0})
        
        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # Calculate metrics
        total_time = end_time - start_time
        discovery_duration = discovery_time - start_time
        analysis_duration = analysis_time - discovery_time
        assessment_duration = end_time - analysis_time
        memory_used = final_memory - initial_memory
        
        # Record metrics
        performance_metrics.record_execution_time(total_time)
        performance_metrics.record_memory_usage(memory_used)
        
        # Performance assertions
        assert total_time < 30.0, f"Total workflow too slow: {total_time:.2f}s"
        assert memory_used < 150, f"Memory usage too high: {memory_used:.2f}MB"
        assert len(files) > 900, "Should discover most files"
        assert len(components) > 40, "Should create reasonable number of components"
        
        # Print detailed results
        print("\n=== Performance Regression Test Results ===")
        print(f"Files discovered: {len(files)}")
        print(f"Components analyzed: {len(components)}")
        print(f"Discovery time: {discovery_duration:.2f}s")
        print(f"Analysis time: {analysis_duration:.2f}s")
        print(f"Assessment time: {assessment_duration:.2f}s")
        print(f"Total time: {total_time:.2f}s")
        print(f"Memory used: {memory_used:.2f}MB")
        print(f"Files per second: {len(files)/total_time:.1f}")
        print("=" * 45)
        
        # Store baseline metrics for future comparisons
        baseline_metrics = {
            'total_time': total_time,
            'memory_used': memory_used,
            'files_per_second': len(files) / total_time,
            'components_per_second': len(components) / analysis_duration
        }
        
        return baseline_metrics


if __name__ == "__main__":
    # Run performance tests when executed directly
    pytest.main([__file__, "-v", "-m", "performance"])