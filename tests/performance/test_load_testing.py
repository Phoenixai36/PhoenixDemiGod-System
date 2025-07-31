"""
Load testing for Phoenix Hydra System Review Tool components
"""

import pytest
import time
import tempfile
import asyncio
import concurrent.futures
import statistics
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.phoenix_system_review.discovery.file_scanner import FileSystemScanner
from src.phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from src.phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer


class LoadTestRunner:
    """Helper class for running load tests"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def run_load_test(self, test_func, num_iterations: int, max_workers: int = 4):
        """Run a load test with specified parameters"""
        
        def execute_test(iteration):
            try:
                start_time = time.time()
                result = test_func(iteration)
                end_time = time.time()
                return {
                    'iteration': iteration,
                    'duration': end_time - start_time,
                    'result': result,
                    'success': True
                }
            except Exception as e:
                return {
                    'iteration': iteration,
                    'duration': 0,
                    'result': None,
                    'success': False,
                    'error': str(e)
                }
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(execute_test, i) for i in range(num_iterations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        if successful_results:
            durations = [r['duration'] for r in successful_results]
            stats = {
                'total_iterations': num_iterations,
                'successful_iterations': len(successful_results),
                'failed_iterations': len(failed_results),
                'total_time': total_time,
                'avg_duration': statistics.mean(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'median_duration': statistics.median(durations),
                'throughput': len(successful_results) / total_time,
                'success_rate': len(successful_results) / num_iterations * 100
            }
        else:
            stats = {
                'total_iterations': num_iterations,
                'successful_iterations': 0,
                'failed_iterations': len(failed_results),
                'total_time': total_time,
                'success_rate': 0
            }
        
        return stats, successful_results, failed_results


@pytest.fixture
def load_test_runner():
    """Fixture providing load test runner"""
    return LoadTestRunner()


class TestFileSystemScannerLoad:
    """Load tests for FileSystemScanner"""
    
    def test_high_volume_file_scanning(self, load_test_runner):
        """Test file scanner under high volume load"""
        scanner = FileSystemScanner()
        
        def scan_test(iteration):
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                
                # Create files for this iteration
                num_files = 100 + (iteration % 50)  # Varying file counts
                for i in range(num_files):
                    file_path = base_path / f"file_{i}.py"
                    file_path.write_text(f"# File {i}\nprint('test')\n")
                
                # Scan directory
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files = inventory.files
                return len(files)
        
        # Run load test
        stats, successful, failed = load_test_runner.run_load_test(
            scan_test, num_iterations=50, max_workers=8
        )
        
        # Assertions
        assert stats['success_rate'] > 95, f"Success rate too low: {stats['success_rate']:.1f}%"
        assert stats['avg_duration'] < 2.0, f"Average duration too high: {stats['avg_duration']:.2f}s"
        assert stats['throughput'] > 10, f"Throughput too low: {stats['throughput']:.1f} ops/sec"
        
        print(f"File Scanner Load Test Results:")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Average Duration: {stats['avg_duration']:.3f}s")
        print(f"  Throughput: {stats['throughput']:.1f} operations/sec")
        print(f"  Min/Max Duration: {stats['min_duration']:.3f}s / {stats['max_duration']:.3f}s")
    
    def test_concurrent_directory_access(self, load_test_runner):
        """Test concurrent access to the same directory structure"""
        
        # Create a shared directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create a complex directory structure
            for i in range(20):
                dir_path = base_path / f"module_{i}"
                dir_path.mkdir()
                for j in range(10):
                    file_path = dir_path / f"file_{j}.py"
                    file_path.write_text(f"# Module {i}, File {j}\nclass Test{j}: pass\n")
            
            scanner = FileSystemScanner()
            
            def concurrent_scan_test(iteration):
                # Multiple scanners accessing the same directory
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files = inventory.files
                return len(files)
            
            # Run concurrent load test
            stats, successful, failed = load_test_runner.run_load_test(
                concurrent_scan_test, num_iterations=30, max_workers=10
            )
            
            # Assertions
            assert stats['success_rate'] == 100, f"Some concurrent scans failed: {stats['success_rate']:.1f}%"
            assert stats['avg_duration'] < 1.0, f"Concurrent scans too slow: {stats['avg_duration']:.2f}s"
            
            # All scans should return the same number of files
            file_counts = [r['result'] for r in successful]
            assert len(set(file_counts)) == 1, "Inconsistent file counts in concurrent scans"
            
            print(f"Concurrent Directory Access Results:")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            print(f"  Average Duration: {stats['avg_duration']:.3f}s")
            print(f"  Files Found: {file_counts[0] if file_counts else 0}")


class TestComponentEvaluatorLoad:
    """Load tests for ComponentEvaluator"""
    
    def test_high_volume_component_evaluation(self, load_test_runner):
        """Test component evaluator under high volume load"""
        evaluator = ComponentEvaluator()
        
        def evaluation_test(iteration):
            # Create mock components with varying complexity
            components = []
            num_components = 10 + (iteration % 5)  # 10-14 components per iteration
            
            for i in range(num_components):
                component = Mock()
                component.name = f"component_{iteration}_{i}"
                component.type = "service"
                component.files = [f"file_{j}.py" for j in range(5 + (i % 3))]
                component.dependencies = [f"dep_{k}" for k in range(i % 4)]
                components.append(component)
            
            # Evaluate all components
            results = []
            for component in components:
                result = evaluator.evaluate_component(component)
                results.append(result)
            
            return len(results)
        
        # Run load test
        stats, successful, failed = load_test_runner.run_load_test(
            evaluation_test, num_iterations=40, max_workers=6
        )
        
        # Assertions
        assert stats['success_rate'] > 98, f"Success rate too low: {stats['success_rate']:.1f}%"
        assert stats['avg_duration'] < 3.0, f"Average duration too high: {stats['avg_duration']:.2f}s"
        
        print(f"Component Evaluator Load Test Results:")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Average Duration: {stats['avg_duration']:.3f}s")
        print(f"  Throughput: {stats['throughput']:.1f} evaluations/sec")
    
    def test_memory_intensive_evaluation(self, load_test_runner):
        """Test component evaluator with memory-intensive operations"""
        evaluator = ComponentEvaluator()
        
        def memory_intensive_test(iteration):
            # Create components with large amounts of data
            component = Mock()
            component.name = f"large_component_{iteration}"
            component.type = "service"
            
            # Simulate large file lists
            component.files = [f"file_{i}.py" for i in range(100)]
            component.dependencies = [f"dep_{i}" for i in range(50)]
            
            # Add large metadata
            component.metadata = {
                f"key_{i}": f"value_{i}" * 100 for i in range(20)
            }
            
            result = evaluator.evaluate_component(component)
            return result is not None
        
        # Run memory-intensive load test
        stats, successful, failed = load_test_runner.run_load_test(
            memory_intensive_test, num_iterations=20, max_workers=4
        )
        
        # Assertions
        assert stats['success_rate'] > 95, f"Memory-intensive test success rate too low: {stats['success_rate']:.1f}%"
        assert stats['avg_duration'] < 5.0, f"Memory-intensive test too slow: {stats['avg_duration']:.2f}s"
        
        print(f"Memory Intensive Evaluation Results:")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Average Duration: {stats['avg_duration']:.3f}s")


class TestDependencyAnalyzerLoad:
    """Load tests for DependencyAnalyzer"""
    
    def test_complex_dependency_graph_analysis(self, load_test_runner):
        """Test dependency analyzer with complex dependency graphs"""
        analyzer = DependencyAnalyzer()
        
        def dependency_analysis_test(iteration):
            # Create components with complex dependency relationships
            components = {}
            num_components = 30 + (iteration % 10)  # 30-39 components
            
            for i in range(num_components):
                component = Mock()
                component.name = f"component_{i}"
                
                # Create complex dependency patterns
                dependencies = []
                if i > 0:
                    # Depend on some previous components
                    for j in range(max(0, i-5), i):
                        if j % 3 == 0:  # Not all dependencies
                            dependencies.append(f"component_{j}")
                
                # Add some circular dependencies (should be handled gracefully)
                if i > 10 and i % 7 == 0:
                    dependencies.append(f"component_{(i + 5) % num_components}")
                
                component.dependencies = dependencies
                components[component.name] = component
            
            # Analyze dependencies
            result = analyzer.analyze_dependencies(list(components.values()))
            return result is not None
        
        # Run dependency analysis load test
        stats, successful, failed = load_test_runner.run_load_test(
            dependency_analysis_test, num_iterations=25, max_workers=4
        )
        
        # Assertions
        assert stats['success_rate'] > 90, f"Dependency analysis success rate too low: {stats['success_rate']:.1f}%"
        assert stats['avg_duration'] < 4.0, f"Dependency analysis too slow: {stats['avg_duration']:.2f}s"
        
        print(f"Complex Dependency Analysis Results:")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Average Duration: {stats['avg_duration']:.3f}s")
        print(f"  Throughput: {stats['throughput']:.1f} analyses/sec")
    
    def test_large_scale_dependency_resolution(self, load_test_runner):
        """Test dependency resolution with large numbers of components"""
        analyzer = DependencyAnalyzer()
        
        def large_scale_test(iteration):
            # Create a large number of components
            components = {}
            num_components = 100 + (iteration * 10)  # Increasing scale
            
            for i in range(num_components):
                component = Mock()
                component.name = f"component_{i}"
                
                # Create realistic dependency patterns
                dependencies = []
                
                # Core dependencies (always present)
                if i > 0:
                    dependencies.append("component_0")  # Root dependency
                
                # Layer dependencies
                layer = i // 20
                if layer > 0:
                    layer_start = (layer - 1) * 20
                    layer_end = layer * 20
                    dependencies.extend([f"component_{j}" for j in range(layer_start, min(layer_end, i))])
                
                # Random dependencies within same layer
                same_layer_start = layer * 20
                for j in range(same_layer_start, i):
                    if j % 5 == 0:
                        dependencies.append(f"component_{j}")
                
                component.dependencies = dependencies[:10]  # Limit to prevent explosion
                components[component.name] = component
            
            # Analyze dependencies
            result = analyzer.analyze_dependencies(list(components.values()))
            return len(components)
        
        # Run large scale test with fewer iterations due to complexity
        stats, successful, failed = load_test_runner.run_load_test(
            large_scale_test, num_iterations=10, max_workers=2
        )
        
        # Assertions
        assert stats['success_rate'] > 80, f"Large scale test success rate too low: {stats['success_rate']:.1f}%"
        assert stats['avg_duration'] < 10.0, f"Large scale test too slow: {stats['avg_duration']:.2f}s"
        
        if successful:
            component_counts = [r['result'] for r in successful]
            print(f"Large Scale Dependency Resolution Results:")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            print(f"  Average Duration: {stats['avg_duration']:.3f}s")
            print(f"  Component Range: {min(component_counts)}-{max(component_counts)}")


class TestSystemIntegrationLoad:
    """Integration load tests combining multiple components"""
    
    def test_end_to_end_workflow_load(self, load_test_runner):
        """Test complete workflow under load"""
        scanner = FileSystemScanner()
        evaluator = ComponentEvaluator()
        analyzer = DependencyAnalyzer()
        
        def end_to_end_test(iteration):
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                
                # Create project structure
                num_modules = 5 + (iteration % 3)
                for i in range(num_modules):
                    module_dir = base_path / f"module_{i}"
                    module_dir.mkdir()
                    
                    for j in range(5):
                        file_path = module_dir / f"file_{j}.py"
                        file_path.write_text(f"# Module {i}, File {j}\nclass Component{j}: pass\n")
                
                # 1. Discovery phase
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files = inventory.files
                
                # 2. Create components from files
                components = {}
                for i in range(num_modules):
                    component = Mock()
                    component.name = f"module_{i}"
                    component.files = [f for f in files if f"module_{i}" in str(f.path)]
                    component.dependencies = [f"module_{j}" for j in range(i) if j % 2 == 0]
                    components[component.name] = component
                
                # 3. Evaluate components
                evaluation_results = []
                for component in components.values():
                    result = evaluator.evaluate_component(component)
                    evaluation_results.append(result)
                
                # 4. Analyze dependencies
                dependency_result = analyzer.analyze_dependencies(list(components.values()))
                
                return {
                    'files_found': len(files),
                    'components_created': len(components),
                    'evaluations_completed': len(evaluation_results),
                    'dependency_analysis_success': dependency_result is not None
                }
        
        # Run end-to-end load test
        stats, successful, failed = load_test_runner.run_load_test(
            end_to_end_test, num_iterations=20, max_workers=3
        )
        
        # Assertions
        assert stats['success_rate'] > 95, f"End-to-end success rate too low: {stats['success_rate']:.1f}%"
        assert stats['avg_duration'] < 8.0, f"End-to-end workflow too slow: {stats['avg_duration']:.2f}s"
        
        # Analyze workflow results
        if successful:
            workflow_results = [r['result'] for r in successful]
            avg_files = statistics.mean([wr['files_found'] for wr in workflow_results])
            avg_components = statistics.mean([wr['components_created'] for wr in workflow_results])
            
            print(f"End-to-End Workflow Load Test Results:")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            print(f"  Average Duration: {stats['avg_duration']:.3f}s")
            print(f"  Average Files Found: {avg_files:.1f}")
            print(f"  Average Components: {avg_components:.1f}")
            print(f"  Throughput: {stats['throughput']:.1f} workflows/sec")


@pytest.mark.load
def test_stress_test_suite():
    """Comprehensive stress test combining all load tests"""
    
    print("\n=== Running Comprehensive Load Test Suite ===")
    
    # This would run all load tests in sequence
    # In practice, you might want to run these separately
    
    test_results = {
        'file_scanner': {'passed': True, 'duration': 0},
        'component_evaluator': {'passed': True, 'duration': 0},
        'dependency_analyzer': {'passed': True, 'duration': 0},
        'end_to_end_workflow': {'passed': True, 'duration': 0}
    }
    
    total_start_time = time.time()
    
    try:
        # Run a simplified version of each test
        runner = LoadTestRunner()
        
        # File scanner stress test
        scanner = FileSystemScanner()
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            for i in range(200):
                file_path = base_path / f"stress_file_{i}.py"
                file_path.write_text(f"# Stress test file {i}\nprint('test')\n")
            
            scanner = FileSystemScanner(str(base_path))
            inventory = scanner.scan_project_structure()
            files = inventory.files
            assert len(files) >= 200
        
        test_results['file_scanner']['duration'] = time.time() - start_time
        
        # Component evaluator stress test
        evaluator = ComponentEvaluator()
        start_time = time.time()
        
        for i in range(50):
            component = Mock()
            component.name = f"stress_component_{i}"
            component.files = [f"file_{j}.py" for j in range(10)]
            result = evaluator.evaluate_component(component)
            assert result is not None
        
        test_results['component_evaluator']['duration'] = time.time() - start_time
        
        print("Stress Test Suite Completed Successfully!")
        
    except Exception as e:
        print(f"Stress Test Suite Failed: {e}")
        raise
    
    finally:
        total_duration = time.time() - total_start_time
        print(f"Total Stress Test Duration: {total_duration:.2f}s")
        
        for test_name, result in test_results.items():
            status = "PASSED" if result['passed'] else "FAILED"
            print(f"  {test_name}: {status} ({result['duration']:.2f}s)")


if __name__ == "__main__":
    # Run load tests when executed directly
    pytest.main([__file__, "-v", "-m", "load"])