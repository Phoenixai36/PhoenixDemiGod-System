# Performance and Scalability Tests

This directory contains comprehensive performance and scalability tests for the Phoenix Hydra System Review Tool.

## Test Structure

### Test Files

- **`test_scalability.py`** - Core scalability and performance tests
- **`test_load_testing.py`** - Load testing for high-volume scenarios
- **`test_memory_benchmarks.py`** - Memory usage and leak detection tests
- **`conftest.py`** - Test configuration and fixtures
- **`run_performance_tests.py`** - Test runner script

### Test Categories

#### Scalability Tests (`test_scalability.py`)
- File system scanner performance with large directory structures
- Component evaluator scaling with increasing component counts
- Dependency analyzer performance with complex dependency graphs
- Memory usage stability and leak detection
- Concurrent processing capabilities
- System scalability limits

#### Load Tests (`test_load_testing.py`)
- High-volume file scanning operations
- Concurrent component evaluation
- Complex dependency graph analysis
- End-to-end workflow load testing
- Stress testing with multiple concurrent users

#### Memory Benchmarks (`test_memory_benchmarks.py`)
- Memory usage scaling with project size
- Memory leak detection across repeated operations
- Large file handling memory efficiency
- Component evaluation memory scaling
- Dependency analysis memory usage
- Full workflow memory profiling

## Running Performance Tests

### Using pytest directly

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific test categories
pytest tests/performance/ -v -m performance
pytest tests/performance/ -v -m load
pytest tests/performance/ -v -m memory
pytest tests/performance/ -v -m scalability

# Run specific test files
pytest tests/performance/test_scalability.py -v
pytest tests/performance/test_load_testing.py -v
pytest tests/performance/test_memory_benchmarks.py -v
```

### Using the test runner script

```bash
# Run scalability tests
python tests/performance/run_performance_tests.py scalability

# Run load tests
python tests/performance/run_performance_tests.py load

# Run memory benchmarks
python tests/performance/run_performance_tests.py memory

# Run all performance tests
python tests/performance/run_performance_tests.py all

# Run with verbose output
python tests/performance/run_performance_tests.py scalability -v

# Generate performance report
python tests/performance/run_performance_tests.py --report
```

## Performance Thresholds

The tests include performance thresholds that are automatically adjusted based on system capabilities:

### File System Scanner
- **File scan time**: < 1ms per file (adjusted for CPU cores)
- **Memory usage**: < 0.01MB per file (adjusted for available memory)
- **Concurrent speedup**: At least 70% of theoretical maximum

### Component Evaluator
- **Evaluation time**: < 50ms per component (adjusted for CPU cores)
- **Memory usage**: < 0.1MB per component (adjusted for available memory)
- **Scalability**: Linear scaling up to 200 components

### Dependency Analyzer
- **Analysis time**: < 100ms for complex graphs (adjusted for CPU cores)
- **Memory usage**: < 0.2MB per component in dependency graph
- **Circular dependency handling**: Graceful handling without memory leaks

### Overall System
- **Maximum memory usage**: < 100MB (adjusted for system memory)
- **End-to-end workflow**: < 30 seconds for medium-sized projects
- **Memory cleanup**: < 20MB residual memory after operations

## Test Results and Reporting

### Automatic Result Saving

Test results are automatically saved to `tests/performance/results/` with timestamps:
- `scalability_results_YYYYMMDD_HHMMSS.json`
- `load_results_YYYYMMDD_HHMMSS.json`
- `memory_results_YYYYMMDD_HHMMSS.json`

### Performance Reports

Generate comprehensive performance reports:

```bash
python tests/performance/run_performance_tests.py --report
```

Reports include:
- System information
- Test results summary
- Detailed metrics
- Performance trends over time
- Recommendations for optimization

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Disk**: 1GB free space
- **Python**: 3.8+

### Recommended for Performance Testing
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Disk**: SSD with 5GB+ free space
- **System Load**: < 70% CPU, < 85% memory usage

## Performance Optimization Guidelines

### For Development
1. **File Operations**: Use chunked processing for large file sets
2. **Memory Management**: Implement proper cleanup and garbage collection
3. **Concurrency**: Utilize thread pools for I/O-bound operations
4. **Caching**: Cache expensive computations and file system operations

### For Production
1. **Resource Limits**: Set appropriate memory and CPU limits
2. **Monitoring**: Implement performance monitoring and alerting
3. **Scaling**: Design for horizontal scaling when needed
4. **Optimization**: Profile regularly and optimize bottlenecks

## Troubleshooting Performance Issues

### Common Issues

#### High Memory Usage
- Check for memory leaks in repeated operations
- Verify proper cleanup of large data structures
- Monitor garbage collection effectiveness

#### Slow File Scanning
- Verify file system performance
- Check for excessive file I/O operations
- Consider implementing file system caching

#### Poor Concurrent Performance
- Check for thread contention issues
- Verify proper use of thread pools
- Monitor CPU utilization during concurrent operations

### Debugging Tools

#### Memory Profiling
```python
import tracemalloc
tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
```

#### Performance Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... your code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

## Continuous Integration

### GitHub Actions Integration

Add to `.github/workflows/performance.yml`:

```yaml
name: Performance Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    
    - name: Run performance tests
      run: |
        python tests/performance/run_performance_tests.py all
    
    - name: Generate performance report
      run: |
        python tests/performance/run_performance_tests.py --report
    
    - name: Upload performance results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: tests/performance/results/
```

### Performance Regression Detection

The test runner can detect performance regressions by comparing results over time:

1. **Baseline Establishment**: First run establishes performance baseline
2. **Regression Detection**: Subsequent runs compare against baseline
3. **Threshold Alerts**: Automatic alerts when performance degrades beyond thresholds
4. **Trend Analysis**: Long-term performance trend analysis

## Contributing

When adding new performance tests:

1. **Follow Naming Convention**: Use descriptive test names with `test_` prefix
2. **Add Appropriate Markers**: Use `@pytest.mark.performance`, `@pytest.mark.load`, etc.
3. **Include Assertions**: Always include performance assertions with reasonable thresholds
4. **Document Expected Behavior**: Add docstrings explaining what the test measures
5. **Consider System Variations**: Make thresholds adaptive to different system capabilities

### Example Test Structure

```python
@pytest.mark.performance
def test_new_component_performance(performance_metrics, performance_thresholds):
    """Test performance of new component with large datasets"""
    
    # Setup
    component = NewComponent()
    large_dataset = create_large_dataset(size=1000)
    
    # Performance test
    start_time = time.time()
    result = component.process(large_dataset)
    end_time = time.time()
    
    # Record metrics
    execution_time = end_time - start_time
    performance_metrics.record_execution_time(execution_time)
    
    # Assertions
    assert execution_time < performance_thresholds['new_component_time_ms'] / 1000
    assert result is not None
    assert len(result) == len(large_dataset)
```

This comprehensive performance testing suite ensures that the Phoenix Hydra System Review Tool maintains high performance and scalability as it evolves.