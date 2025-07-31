"""
Memory usage and performance benchmarking for Phoenix Hydra System Review Tool
"""

import pytest
import time
import tempfile
import psutil
import gc
import tracemalloc
import statistics
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, List, Any, Tuple

from src.phoenix_system_review.discovery.file_scanner import FileSystemScanner
from src.phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from src.phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer
from src.phoenix_system_review.analysis.quality_assessor import QualityAssessor


class MemoryProfiler:
    """Helper class for memory profiling and benchmarking"""
    
    def __init__(self):
        self.snapshots = []
        self.peak_memory = 0
        self.baseline_memory = 0
        
    def start_profiling(self):
        """Start memory profiling"""
        tracemalloc.start()
        gc.collect()  # Clean up before starting
        process = psutil.Process()
        self.baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
    def take_snapshot(self, label: str = ""):
        """Take a memory snapshot"""
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            self.snapshots.append({
                'label': label,
                'snapshot': snapshot,
                'memory_mb': current_memory,
                'memory_delta': current_memory - self.baseline_memory,
                'timestamp': time.time()
            })
            
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory
                
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and return results"""
        if tracemalloc.is_tracing():
            tracemalloc.stop()
            
        if not self.snapshots:
            return {}
            
        memory_deltas = [s['memory_delta'] for s in self.snapshots]
        
        return {
            'baseline_memory_mb': self.baseline_memory,
            'peak_memory_mb': self.peak_memory,
            'peak_delta_mb': self.peak_memory - self.baseline_memory,
            'final_memory_mb': self.snapshots[-1]['memory_mb'],
            'final_delta_mb': self.snapshots[-1]['memory_delta'],
            'avg_delta_mb': statistics.mean(memory_deltas),
            'max_delta_mb': max(memory_deltas),
            'min_delta_mb': min(memory_deltas),
            'snapshots': len(self.snapshots)
        }
    
    def get_top_memory_consumers(self, snapshot_index: int = -1, limit: int = 10) -> List[Dict]:
        """Get top memory consumers from a snapshot"""
        if not self.snapshots or snapshot_index >= len(self.snapshots):
            return []
            
        snapshot = self.snapshots[snapshot_index]['snapshot']
        top_stats = snapshot.statistics('lineno')
        
        consumers = []
        for stat in top_stats[:limit]:
            consumers.append({
                'filename': stat.traceback.format()[0] if stat.traceback.format() else 'unknown',
                'size_mb': stat.size / 1024 / 1024,
                'count': stat.count
            })
            
        return consumers


@pytest.fixture
def memory_profiler():
    """Fixture providing memory profiler"""
    return MemoryProfiler()


def create_test_project_structure(base_path: Path, scale: str = "medium") -> int:
    """Create test project structure with different scales"""
    
    scale_configs = {
        "small": {"files": 50, "dirs": 5, "content_lines": 10},
        "medium": {"files": 200, "dirs": 20, "content_lines": 50},
        "large": {"files": 1000, "dirs": 100, "content_lines": 100},
        "xlarge": {"files": 2000, "dirs": 200, "content_lines": 200}
    }
    
    config = scale_configs.get(scale, scale_configs["medium"])
    
    # Create directory structure
    for i in range(config["dirs"]):
        dir_path = base_path / f"module_{i:03d}"
        dir_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        for j in range(3):
            subdir = dir_path / f"submodule_{j}"
            subdir.mkdir(exist_ok=True)
    
    # Create files
    file_types = ['.py', '.js', '.yaml', '.json', '.md']
    files_created = 0
    
    for i in range(config["files"]):
        dir_idx = i % config["dirs"]
        subdir_idx = (i // config["dirs"]) % 3
        file_type = file_types[i % len(file_types)]
        
        file_path = base_path / f"module_{dir_idx:03d}" / f"submodule_{subdir_idx}" / f"file_{i:04d}{file_type}"
        
        # Create file with content
        content_lines = ["# Content line"] * config["content_lines"]
        content = f"# File {i}\n" + "\n".join(content_lines)
        file_path.write_text(content)
        files_created += 1
    
    return files_created


class TestFileSystemScannerMemory:
    """Memory benchmarks for FileSystemScanner"""
    
    def test_memory_usage_by_project_size(self, memory_profiler):
        """Test memory usage scaling with project size"""
        scanner = FileSystemScanner()
        results = {}
        
        scales = ["small", "medium", "large"]
        
        for scale in scales:
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                
                memory_profiler.start_profiling()
                memory_profiler.take_snapshot(f"{scale}_start")
                
                # Create project structure
                files_created = create_test_project_structure(base_path, scale)
                memory_profiler.take_snapshot(f"{scale}_structure_created")
                
                # Scan directory
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files_found = inventory.files
                memory_profiler.take_snapshot(f"{scale}_scan_complete")
                
                # Force garbage collection
                del files_found
                gc.collect()
                memory_profiler.take_snapshot(f"{scale}_after_gc")
                
                profile_results = memory_profiler.stop_profiling()
                results[scale] = {
                    'files_created': files_created,
                    'memory_profile': profile_results
                }
                
                # Reset profiler for next iteration
                memory_profiler = MemoryProfiler()
        
        # Analyze results
        for scale, result in results.items():
            memory_per_file = result['memory_profile']['peak_delta_mb'] / result['files_created']
            
            print(f"\n{scale.upper()} Project Memory Usage:")
            print(f"  Files: {result['files_created']}")
            print(f"  Peak Memory Delta: {result['memory_profile']['peak_delta_mb']:.2f}MB")
            print(f"  Memory per File: {memory_per_file:.4f}MB")
            print(f"  Final Memory Delta: {result['memory_profile']['final_delta_mb']:.2f}MB")
            
            # Memory usage should be reasonable
            assert memory_per_file < 0.1, f"Memory per file too high for {scale}: {memory_per_file:.4f}MB"
            assert result['memory_profile']['peak_delta_mb'] < 200, f"Peak memory too high for {scale}"
    
    def test_memory_leak_detection(self, memory_profiler):
        """Test for memory leaks in repeated operations"""
        memory_profiler.start_profiling()
        memory_readings = []
        
        # Perform multiple scan operations
        for iteration in range(10):
            with tempfile.TemporaryDirectory() as temp_dir:
                base_path = Path(temp_dir)
                create_test_project_structure(base_path, "small")
                
                # Scan directory
                scanner = FileSystemScanner(str(base_path))
                inventory = scanner.scan_project_structure()
                files = inventory.files
                
                # Force cleanup
                del files
                gc.collect()
                
                memory_profiler.take_snapshot(f"iteration_{iteration}")
                
                # Record memory usage
                process = psutil.Process()
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory)
        
        profile_results = memory_profiler.stop_profiling()
        
        # Analyze for memory leaks
        if len(memory_readings) >= 5:
            early_avg = statistics.mean(memory_readings[:3])
            late_avg = statistics.mean(memory_readings[-3:])
            memory_growth = late_avg - early_avg
            
            print(f"\nMemory Leak Detection Results:")
            print(f"  Early Average: {early_avg:.2f}MB")
            print(f"  Late Average: {late_avg:.2f}MB")
            print(f"  Memory Growth: {memory_growth:.2f}MB")
            print(f"  Growth per Iteration: {memory_growth/10:.3f}MB")
            
            # Memory growth should be minimal
            assert memory_growth < 10, f"Potential memory leak detected: {memory_growth:.2f}MB growth"
            
            # Growth per iteration should be very small
            growth_per_iteration = memory_growth / 10
            assert growth_per_iteration < 1.0, f"Memory growth per iteration too high: {growth_per_iteration:.3f}MB"
    
    def test_large_file_handling_memory(self, memory_profiler):
        """Test memory usage when handling large files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            memory_profiler.start_profiling()
            memory_profiler.take_snapshot("start")
            
            # Create files of varying sizes
            file_sizes = [1, 10, 100, 1000]  # KB
            
            for i, size_kb in enumerate(file_sizes):
                file_path = base_path / f"large_file_{i}.py"
                content = "# Large file content\n" + "print('line')\n" * (size_kb * 10)
                file_path.write_text(content)
                
                memory_profiler.take_snapshot(f"file_{i}_created_{size_kb}kb")
            
            # Scan directory with large files
            scanner = FileSystemScanner(str(base_path))
            inventory = scanner.scan_project_structure()
            files = inventory.files
            memory_profiler.take_snapshot("scan_complete")
            
            # Process file contents (simulate reading)
            total_content_size = 0
            for file_info in files:
                if file_info.extension == '.py':
                    content = Path(file_info.path).read_text()
                    total_content_size += len(content)
            
            memory_profiler.take_snapshot("content_processed")
            
            profile_results = memory_profiler.stop_profiling()
            
            print(f"\nLarge File Handling Memory Results:")
            print(f"  Files Processed: {len(files)}")
            print(f"  Total Content Size: {total_content_size/1024:.1f}KB")
            print(f"  Peak Memory Delta: {profile_results['peak_delta_mb']:.2f}MB")
            print(f"  Final Memory Delta: {profile_results['final_delta_mb']:.2f}MB")
            
            # Memory usage should be reasonable relative to content size
            content_size_mb = total_content_size / 1024 / 1024
            memory_efficiency = profile_results['peak_delta_mb'] / content_size_mb if content_size_mb > 0 else 0
            
            assert memory_efficiency < 5.0, f"Memory efficiency too low: {memory_efficiency:.2f}x content size"


class TestComponentEvaluatorMemory:
    """Memory benchmarks for ComponentEvaluator"""
    
    def test_component_evaluation_memory_scaling(self, memory_profiler):
        """Test memory usage scaling with number of components"""
        evaluator = ComponentEvaluator()
        
        component_counts = [10, 50, 100, 200]
        results = {}
        
        for count in component_counts:
            memory_profiler.start_profiling()
            memory_profiler.take_snapshot(f"start_{count}")
            
            # Create mock components
            components = []
            for i in range(count):
                component = Mock()
                component.name = f"component_{i}"
                component.type = "service"
                component.files = [f"file_{j}.py" for j in range(5)]
                component.dependencies = [f"dep_{k}" for k in range(i % 3)]
                components.append(component)
            
            memory_profiler.take_snapshot(f"components_created_{count}")
            
            # Evaluate all components
            evaluation_results = []
            for component in components:
                result = evaluator.evaluate_component(component)
                evaluation_results.append(result)
            
            memory_profiler.take_snapshot(f"evaluation_complete_{count}")
            
            # Cleanup
            del components, evaluation_results
            gc.collect()
            memory_profiler.take_snapshot(f"after_cleanup_{count}")
            
            profile_results = memory_profiler.stop_profiling()
            results[count] = profile_results
            
            # Reset profiler
            memory_profiler = MemoryProfiler()
        
        # Analyze scaling
        print(f"\nComponent Evaluation Memory Scaling:")
        for count, result in results.items():
            memory_per_component = result['peak_delta_mb'] / count
            print(f"  {count} components: {result['peak_delta_mb']:.2f}MB peak ({memory_per_component:.4f}MB per component)")
            
            # Memory per component should be reasonable
            assert memory_per_component < 0.5, f"Memory per component too high: {memory_per_component:.4f}MB"
    
    def test_complex_component_memory_usage(self, memory_profiler):
        """Test memory usage with complex components"""
        evaluator = ComponentEvaluator()
        
        memory_profiler.start_profiling()
        memory_profiler.take_snapshot("start")
        
        # Create complex components with lots of data
        complex_components = []
        for i in range(20):
            component = Mock()
            component.name = f"complex_component_{i}"
            component.type = "service"
            
            # Large file lists
            component.files = [f"file_{j}.py" for j in range(50)]
            
            # Many dependencies
            component.dependencies = [f"dep_{k}" for k in range(20)]
            
            # Large metadata
            component.metadata = {
                f"key_{j}": f"value_{j}" * 100 for j in range(10)
            }
            
            # Configuration data
            component.config = {
                "settings": {f"setting_{k}": f"value_{k}" * 50 for k in range(15)}
            }
            
            complex_components.append(component)
        
        memory_profiler.take_snapshot("complex_components_created")
        
        # Evaluate complex components
        results = []
        for i, component in enumerate(complex_components):
            result = evaluator.evaluate_component(component)
            results.append(result)
            
            if i % 5 == 0:  # Take snapshots periodically
                memory_profiler.take_snapshot(f"evaluated_{i+1}")
        
        memory_profiler.take_snapshot("all_evaluations_complete")
        
        profile_results = memory_profiler.stop_profiling()
        
        print(f"\nComplex Component Memory Usage:")
        print(f"  Components Evaluated: {len(results)}")
        print(f"  Peak Memory Delta: {profile_results['peak_delta_mb']:.2f}MB")
        print(f"  Final Memory Delta: {profile_results['final_delta_mb']:.2f}MB")
        print(f"  Memory per Complex Component: {profile_results['peak_delta_mb']/len(results):.3f}MB")
        
        # Even complex components should have reasonable memory usage
        memory_per_component = profile_results['peak_delta_mb'] / len(results)
        assert memory_per_component < 2.0, f"Memory per complex component too high: {memory_per_component:.3f}MB"


class TestDependencyAnalyzerMemory:
    """Memory benchmarks for DependencyAnalyzer"""
    
    def test_dependency_graph_memory_usage(self, memory_profiler):
        """Test memory usage for dependency graph analysis"""
        analyzer = DependencyAnalyzer()
        
        graph_sizes = [20, 50, 100]
        results = {}
        
        for size in graph_sizes:
            memory_profiler.start_profiling()
            memory_profiler.take_snapshot(f"start_{size}")
            
            # Create components with complex dependency relationships
            components = {}
            for i in range(size):
                component = Mock()
                component.name = f"component_{i}"
                
                # Create realistic dependency patterns
                dependencies = []
                
                # Each component depends on some previous components
                for j in range(max(0, i-10), i):
                    if j % 3 == 0:  # Not all dependencies
                        dependencies.append(f"component_{j}")
                
                # Add some cross-dependencies
                if i > size // 2:
                    for j in range(0, size // 4):
                        if j != i:
                            dependencies.append(f"component_{j}")
                
                component.dependencies = dependencies
                components[component.name] = component
            
            memory_profiler.take_snapshot(f"components_created_{size}")
            
            # Analyze dependencies
            result = analyzer.analyze_dependencies(list(components.values()))
            memory_profiler.take_snapshot(f"analysis_complete_{size}")
            
            # Cleanup
            del components, result
            gc.collect()
            memory_profiler.take_snapshot(f"after_cleanup_{size}")
            
            profile_results = memory_profiler.stop_profiling()
            results[size] = profile_results
            
            # Reset profiler
            memory_profiler = MemoryProfiler()
        
        # Analyze results
        print(f"\nDependency Graph Memory Usage:")
        for size, result in results.items():
            memory_per_component = result['peak_delta_mb'] / size
            print(f"  {size} components: {result['peak_delta_mb']:.2f}MB peak ({memory_per_component:.4f}MB per component)")
            
            # Memory usage should scale reasonably
            assert memory_per_component < 0.2, f"Memory per component in graph too high: {memory_per_component:.4f}MB"
    
    def test_circular_dependency_memory_handling(self, memory_profiler):
        """Test memory usage when handling circular dependencies"""
        analyzer = DependencyAnalyzer()
        
        memory_profiler.start_profiling()
        memory_profiler.take_snapshot("start")
        
        # Create components with intentional circular dependencies
        components = {}
        num_components = 30
        
        for i in range(num_components):
            component = Mock()
            component.name = f"component_{i}"
            
            # Create circular dependency chains
            dependencies = []
            
            # Simple circular dependency
            if i < num_components - 1:
                dependencies.append(f"component_{i+1}")
            else:
                dependencies.append("component_0")  # Close the circle
            
            # Additional complex circular patterns
            if i % 5 == 0 and i > 0:
                dependencies.append(f"component_{(i-5) % num_components}")
            
            component.dependencies = dependencies
            components[component.name] = component
        
        memory_profiler.take_snapshot("circular_components_created")
        
        # Analyze dependencies (should handle circular dependencies gracefully)
        try:
            result = analyzer.analyze_dependencies(list(components.values()))
            memory_profiler.take_snapshot("circular_analysis_complete")
            
            analysis_successful = result is not None
        except Exception as e:
            memory_profiler.take_snapshot("circular_analysis_failed")
            analysis_successful = False
            print(f"Circular dependency analysis failed: {e}")
        
        profile_results = memory_profiler.stop_profiling()
        
        print(f"\nCircular Dependency Memory Handling:")
        print(f"  Components: {num_components}")
        print(f"  Analysis Successful: {analysis_successful}")
        print(f"  Peak Memory Delta: {profile_results['peak_delta_mb']:.2f}MB")
        print(f"  Final Memory Delta: {profile_results['final_delta_mb']:.2f}MB")
        
        # Memory usage should be reasonable even with circular dependencies
        assert profile_results['peak_delta_mb'] < 50, f"Memory usage too high for circular dependencies: {profile_results['peak_delta_mb']:.2f}MB"


class TestIntegratedMemoryBenchmarks:
    """Integrated memory benchmarks combining multiple components"""
    
    def test_full_workflow_memory_profile(self, memory_profiler):
        """Test memory usage of complete workflow"""
        scanner = FileSystemScanner()
        evaluator = ComponentEvaluator()
        analyzer = DependencyAnalyzer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            memory_profiler.start_profiling()
            memory_profiler.take_snapshot("workflow_start")
            
            # 1. Create project structure
            files_created = create_test_project_structure(base_path, "medium")
            memory_profiler.take_snapshot("project_structure_created")
            
            # 2. Discovery phase
            scanner = FileSystemScanner(str(base_path))
            inventory = scanner.scan_project_structure()
            files = inventory.files
            memory_profiler.take_snapshot("discovery_complete")
            
            # 3. Create components
            components = {}
            num_components = min(20, len(files) // 10)  # Reasonable number of components
            
            for i in range(num_components):
                component = Mock()
                component.name = f"component_{i}"
                component.files = files[i*10:(i+1)*10] if i*10 < len(files) else files[-10:]
                component.dependencies = [f"component_{j}" for j in range(max(0, i-3), i)]
                components[component.name] = component
            
            memory_profiler.take_snapshot("components_created")
            
            # 4. Evaluation phase
            evaluation_results = []
            for component in components.values():
                result = evaluator.evaluate_component(component)
                evaluation_results.append(result)
            
            memory_profiler.take_snapshot("evaluation_complete")
            
            # 5. Dependency analysis
            dependency_result = analyzer.analyze_dependencies(list(components.values()))
            memory_profiler.take_snapshot("dependency_analysis_complete")
            
            # 6. Simulate assessment phase
            assessment_results = []
            for eval_result in evaluation_results:
                # Simulate assessment processing
                assessment = {
                    'component': eval_result,
                    'gaps': [f"gap_{i}" for i in range(3)],
                    'completion_score': 75.0 + (hash(str(eval_result)) % 25)
                }
                assessment_results.append(assessment)
            
            memory_profiler.take_snapshot("assessment_complete")
            
            # 7. Cleanup phase
            del files, components, evaluation_results, dependency_result, assessment_results
            gc.collect()
            memory_profiler.take_snapshot("after_cleanup")
            
            profile_results = memory_profiler.stop_profiling()
            
            print(f"\nFull Workflow Memory Profile:")
            print(f"  Files Created: {files_created}")
            print(f"  Components Processed: {num_components}")
            print(f"  Peak Memory Delta: {profile_results['peak_delta_mb']:.2f}MB")
            print(f"  Final Memory Delta: {profile_results['final_delta_mb']:.2f}MB")
            print(f"  Memory Efficiency: {profile_results['peak_delta_mb']/files_created:.4f}MB per file")
            
            # Get top memory consumers
            top_consumers = memory_profiler.get_top_memory_consumers(limit=5)
            if top_consumers:
                print(f"  Top Memory Consumers:")
                for i, consumer in enumerate(top_consumers, 1):
                    print(f"    {i}. {consumer['filename']}: {consumer['size_mb']:.2f}MB")
            
            # Assertions
            assert profile_results['peak_delta_mb'] < 100, f"Peak memory usage too high: {profile_results['peak_delta_mb']:.2f}MB"
            assert profile_results['final_delta_mb'] < 20, f"Memory not properly cleaned up: {profile_results['final_delta_mb']:.2f}MB"
            
            memory_per_file = profile_results['peak_delta_mb'] / files_created
            assert memory_per_file < 0.1, f"Memory per file too high: {memory_per_file:.4f}MB"


@pytest.mark.memory
def test_memory_benchmark_suite():
    """Comprehensive memory benchmark suite"""
    
    print("\n=== Memory Benchmark Suite ===")
    
    # Run a comprehensive memory test
    profiler = MemoryProfiler()
    
    try:
        profiler.start_profiling()
        profiler.take_snapshot("suite_start")
        
        # Test 1: File Scanner Memory
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            create_test_project_structure(base_path, "medium")
            scanner = FileSystemScanner(str(base_path))
            inventory = scanner.scan_project_structure()
            files = inventory.files
            profiler.take_snapshot("file_scanner_test")
        
        # Test 2: Component Evaluator Memory
        evaluator = ComponentEvaluator()
        components = []
        for i in range(50):
            component = Mock()
            component.name = f"benchmark_component_{i}"
            component.files = [f"file_{j}.py" for j in range(5)]
            components.append(component)
        
        for component in components:
            evaluator.evaluate_component(component)
        
        profiler.take_snapshot("component_evaluator_test")
        
        # Test 3: Dependency Analyzer Memory
        analyzer = DependencyAnalyzer()
        for component in components:
            component.dependencies = [f"dep_{i}" for i in range(3)]
        
        analyzer.analyze_dependencies(components)
        profiler.take_snapshot("dependency_analyzer_test")
        
        # Cleanup
        del scanner, evaluator, analyzer, components, files
        gc.collect()
        profiler.take_snapshot("suite_cleanup")
        
        results = profiler.stop_profiling()
        
        print(f"Memory Benchmark Suite Results:")
        print(f"  Peak Memory Usage: {results['peak_delta_mb']:.2f}MB")
        print(f"  Final Memory Usage: {results['final_delta_mb']:.2f}MB")
        print(f"  Memory Efficiency: {'GOOD' if results['peak_delta_mb'] < 50 else 'NEEDS_IMPROVEMENT'}")
        
        # Overall memory usage should be reasonable
        assert results['peak_delta_mb'] < 100, f"Overall memory usage too high: {results['peak_delta_mb']:.2f}MB"
        
        return results
        
    except Exception as e:
        print(f"Memory benchmark suite failed: {e}")
        raise


if __name__ == "__main__":
    # Run memory benchmarks when executed directly
    pytest.main([__file__, "-v", "-m", "memory"])