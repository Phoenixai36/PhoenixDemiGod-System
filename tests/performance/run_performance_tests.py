#!/usr/bin/env python3
"""
Performance test runner for Phoenix Hydra System Review Tool

This script runs comprehensive performance tests and generates reports.
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import psutil


def get_system_info():
    """Get system information for performance context"""
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_count': psutil.cpu_count(),
        'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
        'disk_usage': psutil.disk_usage('/')._asdict(),
        'platform': psutil.os.name,
        'python_version': sys.version
    }


def run_test_suite(test_type, verbose=False, save_results=True):
    """Run a specific test suite and capture results"""
    
    test_commands = {
        'scalability': ['python', '-m', 'pytest', 'tests/performance/test_scalability.py', '-v', '-m', 'performance'],
        'load': ['python', '-m', 'pytest', 'tests/performance/test_load_testing.py', '-v', '-m', 'load'],
        'memory': ['python', '-m', 'pytest', 'tests/performance/test_memory_benchmarks.py', '-v', '-m', 'memory'],
        'all': ['python', '-m', 'pytest', 'tests/performance/', '-v']
    }
    
    if test_type not in test_commands:
        raise ValueError(f"Unknown test type: {test_type}")
    
    command = test_commands[test_type]
    if verbose:
        command.append('-s')
    
    print(f"Running {test_type} performance tests...")
    print(f"Command: {' '.join(command)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        test_result = {
            'test_type': test_type,
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
        if save_results:
            save_test_results(test_result)
        
        return test_result
        
    except subprocess.TimeoutExpired:
        print(f"Test suite {test_type} timed out after 30 minutes")
        return {
            'test_type': test_type,
            'duration': 1800,
            'return_code': -1,
            'stdout': '',
            'stderr': 'Test timed out',
            'success': False
        }


def save_test_results(test_result):
    """Save test results to file"""
    results_dir = Path('tests/performance/results')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{test_result['test_type']}_results_{timestamp}.json"
    filepath = results_dir / filename
    
    # Add system info to results
    full_result = {
        'system_info': get_system_info(),
        'test_result': test_result
    }
    
    with open(filepath, 'w') as f:
        json.dump(full_result, f, indent=2)
    
    print(f"Results saved to: {filepath}")


def generate_performance_report(results_dir=None):
    """Generate a performance report from saved results"""
    if results_dir is None:
        results_dir = Path('tests/performance/results')
    
    if not results_dir.exists():
        print("No results directory found")
        return
    
    result_files = list(results_dir.glob('*_results_*.json'))
    if not result_files:
        print("No result files found")
        return
    
    # Load all results
    all_results = []
    for file_path in sorted(result_files):
        try:
            with open(file_path) as f:
                result = json.load(f)
                all_results.append(result)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    if not all_results:
        print("No valid results found")
        return
    
    # Generate report
    report_path = results_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_path, 'w') as f:
        f.write("# Phoenix Hydra System Review - Performance Test Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        # System info from latest test
        if all_results:
            latest_system = all_results[-1]['system_info']
            f.write("## System Information\n\n")
            f.write(f"- **CPU Cores**: {latest_system['cpu_count']}\n")
            f.write(f"- **Memory**: {latest_system['memory_total_gb']}GB total, {latest_system['memory_available_gb']}GB available\n")
            f.write(f"- **Platform**: {latest_system['platform']}\n")
            f.write(f"- **Python**: {latest_system['python_version']}\n\n")
        
        # Test results summary
        f.write("## Test Results Summary\n\n")
        f.write("| Test Type | Duration | Status | Date |\n")
        f.write("|-----------|----------|--------|---------|\n")
        
        for result in all_results:
            test_info = result['test_result']
            system_info = result['system_info']
            status = "✅ PASS" if test_info['success'] else "❌ FAIL"
            date = datetime.fromisoformat(system_info['timestamp']).strftime('%Y-%m-%d %H:%M')
            
            f.write(f"| {test_info['test_type']} | {test_info['duration']:.1f}s | {status} | {date} |\n")
        
        f.write("\n## Detailed Results\n\n")
        
        # Detailed results for each test
        for result in all_results:
            test_info = result['test_result']
            f.write(f"### {test_info['test_type'].title()} Tests\n\n")
            f.write(f"- **Duration**: {test_info['duration']:.2f} seconds\n")
            f.write(f"- **Status**: {'PASSED' if test_info['success'] else 'FAILED'}\n")
            f.write(f"- **Return Code**: {test_info['return_code']}\n\n")
            
            if test_info['stderr']:
                f.write("**Errors:**\n")
                f.write(f"```\n{test_info['stderr']}\n```\n\n")
            
            # Extract key metrics from stdout
            stdout_lines = test_info['stdout'].split('\n')
            metrics_lines = [line for line in stdout_lines if any(keyword in line.lower() for keyword in 
                           ['memory', 'duration', 'throughput', 'files', 'components'])]
            
            if metrics_lines:
                f.write("**Key Metrics:**\n")
                for line in metrics_lines[:10]:  # Limit to first 10 relevant lines
                    if line.strip():
                        f.write(f"- {line.strip()}\n")
                f.write("\n")
        
        # Performance trends (if multiple results of same type)
        test_types = {}
        for result in all_results:
            test_type = result['test_result']['test_type']
            if test_type not in test_types:
                test_types[test_type] = []
            test_types[test_type].append(result)
        
        f.write("## Performance Trends\n\n")
        for test_type, results in test_types.items():
            if len(results) > 1:
                f.write(f"### {test_type.title()} Performance Over Time\n\n")
                durations = [r['test_result']['duration'] for r in results]
                avg_duration = sum(durations) / len(durations)
                
                f.write(f"- **Average Duration**: {avg_duration:.2f}s\n")
                f.write(f"- **Best Time**: {min(durations):.2f}s\n")
                f.write(f"- **Worst Time**: {max(durations):.2f}s\n")
                
                if len(durations) >= 2:
                    trend = "improving" if durations[-1] < durations[0] else "degrading"
                    f.write(f"- **Trend**: {trend}\n")
                
                f.write("\n")
    
    print(f"Performance report generated: {report_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run Phoenix Hydra performance tests')
    parser.add_argument('test_type', choices=['scalability', 'load', 'memory', 'all'], 
                       help='Type of performance test to run')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--no-save', action='store_true', 
                       help='Do not save results to file')
    parser.add_argument('--report', action='store_true', 
                       help='Generate performance report from existing results')
    parser.add_argument('--results-dir', type=Path, 
                       help='Directory containing test results')
    
    args = parser.parse_args()
    
    if args.report:
        generate_performance_report(args.results_dir)
        return
    
    print("Phoenix Hydra System Review - Performance Test Runner")
    print("=" * 55)
    
    # Display system info
    system_info = get_system_info()
    print(f"System: {system_info['cpu_count']} CPU cores, {system_info['memory_total_gb']}GB RAM")
    print(f"Available Memory: {system_info['memory_available_gb']}GB")
    print()
    
    # Check system resources
    memory = psutil.virtual_memory()
    if memory.percent > 85:
        print(f"WARNING: High memory usage ({memory.percent:.1f}%) - tests may be unreliable")
    
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 70:
        print(f"WARNING: High CPU usage ({cpu_percent:.1f}%) - tests may be unreliable")
    
    print()
    
    # Run tests
    start_time = time.time()
    result = run_test_suite(args.test_type, args.verbose, not args.no_save)
    total_time = time.time() - start_time
    
    # Display results
    print("\n" + "=" * 55)
    print("PERFORMANCE TEST RESULTS")
    print("=" * 55)
    print(f"Test Type: {result['test_type']}")
    print(f"Duration: {result['duration']:.2f} seconds")
    print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Return Code: {result['return_code']}")
    
    if result['stderr']:
        print("\nErrors:")
        print(result['stderr'])
    
    if args.verbose and result['stdout']:
        print("\nDetailed Output:")
        print(result['stdout'])
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()