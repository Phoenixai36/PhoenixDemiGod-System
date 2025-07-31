"""
Integration tests for logging and monitoring system

Tests the complete logging system including structured logging, metrics collection,
system monitoring, and integration with error handling.
"""

import pytest
import json
import time
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.phoenix_system_review.core.logging_system import (
    PhoenixSystemLogger, LogLevel, MetricType, MetricsCollector,
    SystemMonitor, StructuredFormatter, LogEntry, PerformanceMetric,
    SystemMetrics, log_operation, log_context, get_logger, setup_logging
)


class TestPhoenixSystemLogger:
    """Test PhoenixSystemLogger integration"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger for testing"""
        return PhoenixSystemLogger(
            log_dir=temp_log_dir,
            log_level=LogLevel.DEBUG,
            enable_console=False,  # Disable console for testing
            enable_file=True,
            enable_metrics=True,
            enable_monitoring=True
        )
    
    def test_logger_initialization(self, logger, temp_log_dir):
        """Test logger initialization creates necessary components"""
        assert logger.logger is not None
        assert logger.metrics_collector is not None
        assert logger.system_monitor is not None
        
        # Check log directory was created
        log_dir = Path(temp_log_dir)
        assert log_dir.exists()
        assert log_dir.is_dir()
    
    def test_structured_logging(self, logger, temp_log_dir):
        """Test structured logging to file"""
        # Log various levels
        logger.debug("Debug message", component="test", operation="debug_op")
        logger.info("Info message", component="test", operation="info_op")
        logger.warning("Warning message", component="test", operation="warn_op")
        logger.error("Error message", component="test", operation="error_op")
        
        # Check log file was created and contains structured data
        log_file = Path(temp_log_dir) / "phoenix_system_review.log"
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        
        assert len(log_lines) >= 4  # At least 4 log entries
        
        # Parse and verify structured format
        for line in log_lines:
            log_data = json.loads(line.strip())
            assert "timestamp" in log_data
            assert "level" in log_data
            assert "message" in log_data
            assert "component" in log_data
            assert "operation" in log_data
    
    def test_error_logging_separate_file(self, logger, temp_log_dir):
        """Test error logging goes to separate file"""
        logger.error("Test error", component="test")
        logger.critical("Test critical", component="test")
        
        # Check error log file
        error_log_file = Path(temp_log_dir) / "phoenix_system_review_errors.log"
        assert error_log_file.exists()
        
        with open(error_log_file, 'r') as f:
            error_lines = f.readlines()
        
        assert len(error_lines) >= 2  # At least 2 error entries
    
    def test_correlation_id_tracking(self, logger):
        """Test correlation ID tracking across threads"""
        correlation_id = "test-correlation-123"
        
        # Set correlation ID
        logger.set_correlation_id(correlation_id)
        assert logger.get_correlation_id() == correlation_id
        
        # Test in different thread
        result = {}
        
        def thread_func():
            result['correlation_id'] = logger.get_correlation_id()
        
        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()
        
        # Different thread should not have correlation ID
        assert result['correlation_id'] is None
        
        # Clear correlation ID
        logger.clear_correlation_id()
        assert logger.get_correlation_id() is None
    
    def test_metrics_integration(self, logger):
        """Test metrics collection integration"""
        # Log messages should increment counters
        logger.info("Test info", component="test")
        logger.error("Test error", component="test")
        
        # Check metrics were recorded
        assert logger.metrics_collector.get_counter_value("log_entries_info") > 0
        assert logger.metrics_collector.get_counter_value("log_entries_error") > 0
        
        # Test direct metrics recording
        logger.increment_counter("test_counter", 5, {"component": "test"})
        logger.set_gauge("test_gauge", 42.5, {"component": "test"})
        logger.record_histogram("test_histogram", 100.0, {"component": "test"})
        logger.record_timer("test_timer", 250.0, {"component": "test"})
        
        # Verify metrics
        assert logger.metrics_collector.get_counter_value("test_counter") == 5
        assert logger.metrics_collector.get_gauge_value("test_gauge") == 42.5
        
        histogram_stats = logger.metrics_collector.get_histogram_stats("test_histogram")
        assert histogram_stats["count"] == 1
        assert histogram_stats["mean"] == 100.0
        
        timer_stats = logger.metrics_collector.get_timer_stats("test_timer")
        assert timer_stats["count"] == 1
        assert timer_stats["mean_ms"] == 250.0
    
    def test_system_monitoring_integration(self, logger):
        """Test system monitoring integration"""
        # Get current metrics
        current_metrics = logger.get_system_metrics()
        assert current_metrics is not None
        assert isinstance(current_metrics, SystemMetrics)
        assert current_metrics.cpu_percent >= 0
        assert current_metrics.memory_percent >= 0
        
        # Wait a bit for monitoring to collect data
        time.sleep(0.1)
        
        # Get metrics history
        history = logger.get_system_metrics_history(duration_minutes=1)
        assert isinstance(history, list)
        # History might be empty if monitoring just started
    
    def test_metrics_summary(self, logger):
        """Test metrics summary generation"""
        # Generate some metrics
        logger.increment_counter("test_counter", 10)
        logger.set_gauge("test_gauge", 75.0)
        logger.record_histogram("test_histogram", 50.0)
        logger.record_timer("test_timer", 100.0)
        
        summary = logger.get_metrics_summary()
        
        assert "counters" in summary
        assert "gauges" in summary
        assert "histogram_stats" in summary
        assert "timer_stats" in summary
        
        assert summary["counters"]["test_counter"] == 10
        assert summary["gauges"]["test_gauge"] == 75.0
    
    def test_logger_shutdown(self, logger):
        """Test logger shutdown"""
        # Should not raise exceptions
        logger.shutdown()


class TestMetricsCollector:
    """Test MetricsCollector functionality"""
    
    @pytest.fixture
    def collector(self):
        """Create metrics collector for testing"""
        return MetricsCollector(max_metrics=100)
    
    def test_counter_operations(self, collector):
        """Test counter metric operations"""
        # Increment counter
        collector.increment_counter("test_counter", 5)
        assert collector.get_counter_value("test_counter") == 5
        
        # Increment again
        collector.increment_counter("test_counter", 3)
        assert collector.get_counter_value("test_counter") == 8
        
        # Test with tags
        collector.increment_counter("tagged_counter", 1, {"env": "test"})
        collector.increment_counter("tagged_counter", 2, {"env": "prod"})
        
        assert collector.get_counter_value("tagged_counter", {"env": "test"}) == 1
        assert collector.get_counter_value("tagged_counter", {"env": "prod"}) == 2
    
    def test_gauge_operations(self, collector):
        """Test gauge metric operations"""
        # Set gauge value
        collector.set_gauge("test_gauge", 42.5)
        assert collector.get_gauge_value("test_gauge") == 42.5
        
        # Update gauge value
        collector.set_gauge("test_gauge", 75.0)
        assert collector.get_gauge_value("test_gauge") == 75.0
        
        # Test with tags
        collector.set_gauge("tagged_gauge", 10.0, {"type": "cpu"})
        collector.set_gauge("tagged_gauge", 20.0, {"type": "memory"})
        
        assert collector.get_gauge_value("tagged_gauge", {"type": "cpu"}) == 10.0
        assert collector.get_gauge_value("tagged_gauge", {"type": "memory"}) == 20.0
    
    def test_histogram_operations(self, collector):
        """Test histogram metric operations"""
        # Record histogram values
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            collector.record_histogram("test_histogram", value)
        
        stats = collector.get_histogram_stats("test_histogram")
        
        assert stats["count"] == 5
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["mean"] == 30.0
        assert stats["p50"] == 30.0
    
    def test_timer_operations(self, collector):
        """Test timer metric operations"""
        # Record timer values
        durations = [100.0, 200.0, 300.0, 400.0, 500.0]
        for duration in durations:
            collector.record_timer("test_timer", duration)
        
        stats = collector.get_timer_stats("test_timer")
        
        assert stats["count"] == 5
        assert stats["min_ms"] == 100.0
        assert stats["max_ms"] == 500.0
        assert stats["mean_ms"] == 300.0
        assert stats["p50_ms"] == 300.0
    
    def test_metrics_collection_limit(self):
        """Test metrics collection respects max limit"""
        collector = MetricsCollector(max_metrics=5)
        
        # Add more metrics than limit
        for i in range(10):
            collector.increment_counter(f"counter_{i}", 1)
        
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) <= 5  # Should not exceed limit
    
    def test_clear_metrics(self, collector):
        """Test clearing all metrics"""
        # Add some metrics
        collector.increment_counter("test_counter", 5)
        collector.set_gauge("test_gauge", 42.0)
        collector.record_histogram("test_histogram", 100.0)
        collector.record_timer("test_timer", 200.0)
        
        # Verify metrics exist
        assert collector.get_counter_value("test_counter") == 5
        assert len(collector.get_all_metrics()) > 0
        
        # Clear metrics
        collector.clear_metrics()
        
        # Verify metrics are cleared
        assert collector.get_counter_value("test_counter") == 0
        assert collector.get_gauge_value("test_gauge") is None
        assert len(collector.get_all_metrics()) == 0


class TestSystemMonitor:
    """Test SystemMonitor functionality"""
    
    @pytest.fixture
    def monitor(self):
        """Create system monitor for testing"""
        return SystemMonitor(collection_interval=0.1)  # Fast interval for testing
    
    def test_current_metrics_collection(self, monitor):
        """Test current system metrics collection"""
        metrics = monitor.get_current_metrics()
        
        assert isinstance(metrics, SystemMetrics)
        assert isinstance(metrics.timestamp, datetime)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_used_mb >= 0
        assert metrics.disk_usage_percent >= 0
        assert metrics.process_count >= 0
    
    def test_monitoring_start_stop(self, monitor):
        """Test starting and stopping monitoring"""
        # Start monitoring
        monitor.start_monitoring()
        assert monitor._monitoring is True
        assert monitor._monitor_thread is not None
        
        # Wait for some data collection
        time.sleep(0.2)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert monitor._monitoring is False
    
    def test_metrics_history(self, monitor):
        """Test metrics history collection"""
        # Start monitoring
        monitor.start_monitoring()
        
        # Wait for some data collection
        time.sleep(0.3)
        
        # Get history
        history = monitor.get_metrics_history(duration_minutes=1)
        
        # Should have collected some metrics
        assert isinstance(history, list)
        # May be empty if collection just started
        
        # Stop monitoring
        monitor.stop_monitoring()


class TestLogDecorators:
    """Test logging decorators"""
    
    @pytest.fixture
    def logger(self):
        """Create logger for testing"""
        return PhoenixSystemLogger(
            enable_console=False,
            enable_file=False,
            enable_metrics=True,
            enable_monitoring=False
        )
    
    def test_log_operation_decorator(self, logger):
        """Test log_operation decorator"""
        @log_operation(logger, component="test", phase="testing")
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        
        assert result == 5
        
        # Check metrics were recorded
        assert logger.metrics_collector.get_counter_value("operations_completed") > 0
        
        # Test with exception
        @log_operation(logger, component="test", phase="testing")
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Check error metrics were recorded
        assert logger.metrics_collector.get_counter_value("operations_failed") > 0
    
    def test_log_context_manager(self, logger):
        """Test log_context context manager"""
        correlation_id = "test-123"
        
        with log_context(
            logger,
            operation="test_operation",
            component="test",
            phase="testing",
            correlation_id=correlation_id
        ) as ctx_logger:
            assert ctx_logger == logger
            assert logger.get_correlation_id() == correlation_id
            
            # Do some work
            time.sleep(0.01)
        
        # Correlation ID should be cleared
        assert logger.get_correlation_id() is None
        
        # Check metrics were recorded
        assert logger.metrics_collector.get_counter_value("contexts_completed") > 0
        
        # Test with exception
        with pytest.raises(ValueError):
            with log_context(logger, operation="failing_operation") as ctx_logger:
                raise ValueError("Test error")
        
        # Check error metrics were recorded
        assert logger.metrics_collector.get_counter_value("contexts_failed") > 0


class TestStructuredFormatter:
    """Test StructuredFormatter"""
    
    def test_structured_formatting(self):
        """Test structured log formatting"""
        formatter = StructuredFormatter(include_system_info=False)
        
        # Create mock log record
        record = Mock()
        record.created = time.time()
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.name = "test_logger"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.exc_info = None
        
        # Add extra attributes
        record.component = "test_component"
        record.operation = "test_operation"
        record.phase = "test_phase"
        record.duration_ms = 123.45
        record.correlation_id = "test-correlation"
        record.metadata = {"key": "value"}
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["component"] == "test_component"
        assert log_data["operation"] == "test_operation"
        assert log_data["phase"] == "test_phase"
        assert log_data["duration_ms"] == 123.45
        assert log_data["correlation_id"] == "test-correlation"
        assert log_data["metadata"] == {"key": "value"}
    
    def test_structured_formatting_with_exception(self):
        """Test structured formatting with exception info"""
        formatter = StructuredFormatter()
        
        # Create mock log record with exception
        record = Mock()
        record.created = time.time()
        record.levelname = "ERROR"
        record.getMessage.return_value = "Error message"
        record.name = "test_logger"
        record.module = "test_module"
        record.funcName = "test_function"
        record.lineno = 42
        record.exc_info = (ValueError, ValueError("Test error"), None)
        
        # Mock formatException
        formatter.formatException = Mock(return_value="Formatted exception")
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "ERROR"
        assert log_data["exception"] == "Formatted exception"


class TestGlobalLogger:
    """Test global logger functions"""
    
    def test_get_logger_singleton(self):
        """Test get_logger returns singleton"""
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2
    
    def test_setup_logging(self):
        """Test setup_logging configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = setup_logging(
                log_dir=temp_dir,
                log_level=LogLevel.DEBUG,
                enable_console=False
            )
            
            assert isinstance(logger, PhoenixSystemLogger)
            assert logger.log_level == LogLevel.DEBUG
            assert logger.log_dir == Path(temp_dir)


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_complete_logging_workflow(self, temp_log_dir):
        """Test complete logging workflow with all components"""
        # Setup logger
        logger = PhoenixSystemLogger(
            log_dir=temp_log_dir,
            log_level=LogLevel.DEBUG,
            enable_console=False,
            enable_file=True,
            enable_metrics=True,
            enable_monitoring=True
        )
        
        correlation_id = "integration-test-123"
        
        # Test complete workflow
        with log_context(
            logger,
            operation="integration_test",
            component="test_suite",
            phase="integration",
            correlation_id=correlation_id
        ):
            # Log various messages
            logger.info("Starting integration test", metadata={"test_id": "001"})
            logger.debug("Debug information", metadata={"debug_data": "test"})
            
            # Record metrics
            logger.increment_counter("test_operations", 1, {"type": "integration"})
            logger.set_gauge("test_progress", 50.0, {"phase": "middle"})
            logger.record_histogram("test_duration", 125.5, {"operation": "setup"})
            logger.record_timer("test_timer", 250.0, {"phase": "execution"})
            
            # Simulate some work
            time.sleep(0.1)
            
            logger.info("Integration test completed successfully")
        
        # Verify log files were created
        log_file = Path(temp_log_dir) / "phoenix_system_review.log"
        assert log_file.exists()
        
        # Verify structured logging
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        
        assert len(log_lines) >= 4  # At least 4 log entries
        
        # Verify all log entries are valid JSON with expected structure
        for line in log_lines:
            log_data = json.loads(line.strip())
            assert "timestamp" in log_data
            assert "level" in log_data
            assert "message" in log_data
            
            # Context entries should have correlation ID
            if "Starting:" in log_data["message"] or "Completed:" in log_data["message"]:
                assert log_data.get("correlation_id") == correlation_id
        
        # Verify metrics were collected
        metrics_summary = logger.get_metrics_summary()
        assert "counters" in metrics_summary
        assert "gauges" in metrics_summary
        assert "histogram_stats" in metrics_summary
        assert "timer_stats" in metrics_summary
        
        # Verify system metrics
        system_metrics = logger.get_system_metrics()
        assert system_metrics is not None
        assert isinstance(system_metrics, SystemMetrics)
        
        # Cleanup
        logger.shutdown()
    
    def test_error_handling_integration(self, temp_log_dir):
        """Test integration with error handling"""
        logger = PhoenixSystemLogger(
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
            enable_metrics=True
        )
        
        @log_operation(logger, component="error_test", phase="testing")
        def operation_with_error():
            logger.info("About to raise an error")
            raise ValueError("Test error for integration")
        
        # Execute operation that will fail
        with pytest.raises(ValueError):
            operation_with_error()
        
        # Verify error was logged
        error_log_file = Path(temp_log_dir) / "phoenix_system_review_errors.log"
        assert error_log_file.exists()
        
        with open(error_log_file, 'r') as f:
            error_lines = f.readlines()
        
        assert len(error_lines) >= 1
        
        # Verify error metrics
        assert logger.metrics_collector.get_counter_value("operations_failed") > 0
        
        # Cleanup
        logger.shutdown()