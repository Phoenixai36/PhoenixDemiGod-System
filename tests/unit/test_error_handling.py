"""
Unit tests for error handling framework

Tests custom exception classes, error handler functionality, retry mechanisms,
and graceful degradation capabilities.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.phoenix_system_review.core.exceptions import (
    SystemReviewError, ErrorSeverity, ErrorCategory,
    DiscoveryError, AnalysisError, AssessmentError, ReportingError,
    FileSystemError, ConfigurationParsingError, ServiceDiscoveryError,
    ComponentEvaluationError, DependencyAnalysisError, QualityAssessmentError,
    GapAnalysisError, CompletionCalculationError, PriorityRankingError,
    TODOGenerationError, StatusReportError, RecommendationError,
    ValidationError, NetworkError, CriticalSystemError, RecoverableError,
    create_error, is_recoverable_error, get_error_severity
)

from src.phoenix_system_review.core.error_handler import (
    ErrorHandler, RetryConfig, ErrorContext, ErrorRecord,
    with_retry, handle_errors
)

from src.phoenix_system_review.models.data_models import Component, ComponentCategory


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_system_review_error_basic(self):
        """Test basic SystemReviewError functionality"""
        error = SystemReviewError(
            "Test error",
            component="test_component",
            phase="test_phase",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DISCOVERY
        )
        
        assert error.message == "Test error"
        assert error.component == "test_component"
        assert error.phase == "test_phase"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.DISCOVERY
        assert error.recoverable is True
        
        # Test string representation
        str_repr = str(error)
        assert "[HIGH]" in str_repr
        assert "Component: test_component" in str_repr
        assert "Phase: test_phase" in str_repr
        assert "Test error" in str_repr
    
    def test_system_review_error_to_dict(self):
        """Test error serialization to dictionary"""
        error = SystemReviewError(
            "Test error",
            component="test_component",
            context={"key": "value"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "SystemReviewError"
        assert error_dict["message"] == "Test error"
        assert error_dict["component"] == "test_component"
        assert error_dict["context"] == {"key": "value"}
        assert error_dict["recoverable"] is True
    
    def test_discovery_error(self):
        """Test DiscoveryError specific functionality"""
        error = DiscoveryError("Discovery failed")
        
        assert isinstance(error, SystemReviewError)
        assert error.category == ErrorCategory.DISCOVERY
        assert error.phase == "discovery"
    
    def test_file_system_error(self):
        """Test FileSystemError with file path context"""
        error = FileSystemError(
            "File not found",
            file_path="/path/to/file.txt",
            operation="read"
        )
        
        assert isinstance(error, DiscoveryError)
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert error.file_path == "/path/to/file.txt"
        assert error.operation == "read"
        assert error.context["file_path"] == "/path/to/file.txt"
        assert error.context["operation"] == "read"
    
    def test_configuration_parsing_error(self):
        """Test ConfigurationParsingError with line number"""
        error = ConfigurationParsingError(
            "Invalid YAML syntax",
            config_file="config.yaml",
            line_number=42
        )
        
        assert isinstance(error, DiscoveryError)
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.config_file == "config.yaml"
        assert error.line_number == 42
        assert error.context["config_file"] == "config.yaml"
        assert error.context["line_number"] == 42
    
    def test_service_discovery_error(self):
        """Test ServiceDiscoveryError with service context"""
        error = ServiceDiscoveryError(
            "Service unreachable",
            service_name="phoenix-core",
            endpoint="http://localhost:8080"
        )
        
        assert isinstance(error, DiscoveryError)
        assert error.category == ErrorCategory.NETWORK
        assert error.service_name == "phoenix-core"
        assert error.endpoint == "http://localhost:8080"
    
    def test_component_evaluation_error(self):
        """Test ComponentEvaluationError"""
        error = ComponentEvaluationError(
            "Evaluation failed",
            component_name="test_component",
            criteria_id="test_criteria"
        )
        
        assert isinstance(error, AnalysisError)
        assert error.component == "test_component"
        assert error.component_name == "test_component"
        assert error.criteria_id == "test_criteria"
    
    def test_critical_system_error(self):
        """Test CriticalSystemError is not recoverable"""
        error = CriticalSystemError("System failure")
        
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.recoverable is False
    
    def test_recoverable_error(self):
        """Test RecoverableError is recoverable"""
        error = RecoverableError("Recoverable issue")
        
        assert error.recoverable is True
    
    def test_create_error_factory(self):
        """Test error factory function"""
        error = create_error("file_not_found", "File missing", file_path="/test/path")
        
        assert isinstance(error, FileSystemError)
        assert error.message == "File missing"
    
    def test_is_recoverable_error(self):
        """Test recoverable error detection"""
        recoverable = RecoverableError("Test")
        critical = CriticalSystemError("Critical")
        standard = Exception("Standard")
        
        assert is_recoverable_error(recoverable) is True
        assert is_recoverable_error(critical) is False
        assert is_recoverable_error(standard) is True  # Non-SystemReviewError defaults to recoverable
    
    def test_get_error_severity(self):
        """Test error severity detection"""
        high_error = SystemReviewError("Test", severity=ErrorSeverity.HIGH)
        standard_error = Exception("Standard")
        
        assert get_error_severity(high_error) == ErrorSeverity.HIGH
        assert get_error_severity(standard_error) == ErrorSeverity.MEDIUM  # Default


class TestErrorHandler:
    """Test ErrorHandler functionality"""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing"""
        logger = Mock(spec=logging.Logger)
        return ErrorHandler(logger=logger)
    
    @pytest.fixture
    def error_context(self):
        """Create error context for testing"""
        return ErrorContext(
            operation="test_operation",
            component="test_component",
            phase="test_phase"
        )
    
    def test_error_handler_initialization(self, error_handler):
        """Test error handler initialization"""
        assert error_handler.logger is not None
        assert len(error_handler.error_history) == 0
        assert len(error_handler.recovery_strategies) > 0
        assert len(error_handler.fallback_handlers) == 0
    
    def test_handle_recoverable_error(self, error_handler, error_context):
        """Test handling of recoverable errors"""
        error = RecoverableError("Test recoverable error")
        
        result = error_handler.handle_error(error, error_context)
        
        # Should attempt recovery (may return None if no strategy works)
        assert len(error_handler.error_history) == 1
        assert error_handler.error_history[0].error == error
    
    def test_handle_critical_error(self, error_handler, error_context):
        """Test handling of critical errors"""
        error = CriticalSystemError("Critical failure")
        
        result = error_handler.handle_error(error, error_context)
        
        assert result is None  # Should not recover
        assert len(error_handler.error_history) == 1
        assert not error_handler.error_history[0].resolved
    
    def test_register_recovery_strategy(self, error_handler):
        """Test registering custom recovery strategy"""
        def custom_strategy(error, context):
            return "recovered"
        
        error_handler.register_recovery_strategy(ValueError, custom_strategy)
        
        context = ErrorContext(operation="test")
        error = ValueError("Test error")
        
        result = error_handler.handle_error(error, context)
        assert result == "recovered"
    
    def test_register_fallback_handler(self, error_handler):
        """Test registering fallback handler"""
        def fallback_handler(error, context):
            return "fallback_result"
        
        error_handler.register_fallback_handler("test_operation", fallback_handler)
        
        context = ErrorContext(operation="test_operation")
        error = Exception("Test error")
        
        result = error_handler.handle_error(error, context)
        assert result == "fallback_result"
    
    def test_file_system_error_recovery(self, error_handler, error_context):
        """Test file system error recovery"""
        error = FileSystemError("File not found", file_path="/test/path")
        
        result = error_handler.handle_error(error, error_context)
        
        # Should return empty dict for file not found
        assert result == {}
    
    def test_network_error_recovery(self, error_handler, error_context):
        """Test network error recovery"""
        error = NetworkError("Connection failed", url="http://test.com")
        
        result = error_handler.handle_error(error, error_context)
        
        assert result["status"] == "unavailable"
        assert "error" in result
    
    def test_config_parsing_error_recovery(self, error_handler, error_context):
        """Test configuration parsing error recovery"""
        error = ConfigurationParsingError("Invalid syntax", config_file="test.yaml")
        
        result = error_handler.handle_error(error, error_context)
        
        assert result["config"] == {}
        assert result["source"] == "default"
    
    def test_graceful_degradation_discovery(self, error_handler):
        """Test graceful degradation for discovery phase"""
        context = ErrorContext(operation="scan_files", phase="discovery")
        error = Exception("Generic error")
        
        result = error_handler.handle_error(error, context)
        
        assert result["components"] == []
        assert result["partial"] is True
        assert result["degraded"] is True
    
    def test_graceful_degradation_analysis(self, error_handler):
        """Test graceful degradation for analysis phase"""
        context = ErrorContext(
            operation="evaluate_component",
            phase="analysis",
            component="test_component"
        )
        error = Exception("Generic error")
        
        result = error_handler.handle_error(error, context)
        
        assert hasattr(result, 'component')
        assert result.completion_percentage == 0.0
        assert len(result.issues) > 0
    
    def test_error_logging(self, error_handler, error_context):
        """Test error logging with different severity levels"""
        critical_error = CriticalSystemError("Critical")
        high_error = SystemReviewError("High", severity=ErrorSeverity.HIGH)
        medium_error = SystemReviewError("Medium", severity=ErrorSeverity.MEDIUM)
        low_error = SystemReviewError("Low", severity=ErrorSeverity.LOW)
        
        error_handler.handle_error(critical_error, error_context, allow_recovery=False)
        error_handler.handle_error(high_error, error_context)
        error_handler.handle_error(medium_error, error_context)
        error_handler.handle_error(low_error, error_context)
        
        # Verify logger was called with appropriate levels
        assert error_handler.logger.critical.called
        assert error_handler.logger.error.called
        assert error_handler.logger.warning.called
        assert error_handler.logger.info.called
    
    def test_get_error_summary(self, error_handler, error_context):
        """Test error summary generation"""
        # Add some errors
        error1 = RecoverableError("Error 1")
        error2 = CriticalSystemError("Error 2")
        
        error_handler.handle_error(error1, error_context)
        error_handler.handle_error(error2, error_context, allow_recovery=False)
        
        # Manually mark first error as resolved for testing
        error_handler.error_history[0].resolved = True
        
        summary = error_handler.get_error_summary()
        
        assert summary["total_errors"] == 2
        assert summary["resolved_errors"] == 1
        assert summary["unresolved_errors"] == 1
        assert summary["resolution_rate"] == 0.5
        assert "RecoverableError" in summary["error_types"]
        assert "CriticalSystemError" in summary["error_types"]
        assert len(summary["recent_errors"]) == 2


class TestRetryDecorator:
    """Test retry decorator functionality"""
    
    @pytest.mark.asyncio
    async def test_async_retry_success_on_second_attempt(self):
        """Test async retry succeeds on second attempt"""
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=3, base_delay=0.01))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await failing_function()
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_retry_max_attempts_exceeded(self):
        """Test async retry fails after max attempts"""
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=2, base_delay=0.01))
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            await always_failing_function()
        
        assert call_count == 2
    
    def test_sync_retry_success_on_second_attempt(self):
        """Test sync retry succeeds on second attempt"""
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=3, base_delay=0.01))
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_function()
        
        assert result == "success"
        assert call_count == 2
    
    def test_sync_retry_max_attempts_exceeded(self):
        """Test sync retry fails after max attempts"""
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=2, base_delay=0.01))
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_failing_function()
        
        assert call_count == 2
    
    def test_retry_stop_on_critical_error(self):
        """Test retry stops on critical errors"""
        call_count = 0
        
        @with_retry(RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            stop_on=[CriticalSystemError]
        ))
        def critical_failing_function():
            nonlocal call_count
            call_count += 1
            raise CriticalSystemError("Critical failure")
        
        with pytest.raises(CriticalSystemError):
            critical_failing_function()
        
        assert call_count == 1  # Should not retry
    
    def test_retry_only_on_specific_errors(self):
        """Test retry only occurs for specific error types"""
        call_count = 0
        
        @with_retry(RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            retry_on=[ValueError]
        ))
        def specific_error_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable error")
            else:
                raise TypeError("Non-retryable error")
        
        with pytest.raises(TypeError):
            specific_error_function()
        
        assert call_count == 2  # Retried once, then failed with different error
    
    @pytest.mark.asyncio
    async def test_retry_with_error_handler_recovery(self):
        """Test retry with error handler recovery"""
        error_handler = ErrorHandler()
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=2, base_delay=0.01), error_handler)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise RecoverableError("Recoverable failure")
        
        # Register a recovery strategy
        def recovery_strategy(error, context):
            return "recovered_result"
        
        error_handler.register_recovery_strategy(RecoverableError, recovery_strategy)
        
        result = await failing_function()
        
        assert result == "recovered_result"
        assert call_count == 2  # Should exhaust retries then recover


class TestHandleErrorsDecorator:
    """Test handle_errors decorator functionality"""
    
    def test_handle_errors_with_recovery(self):
        """Test handle_errors decorator with successful recovery"""
        error_handler = ErrorHandler()
        
        # Register recovery strategy
        def recovery_strategy(error, context):
            return "recovered"
        
        error_handler.register_recovery_strategy(ValueError, recovery_strategy)
        
        @handle_errors(error_handler, operation="test_op")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "recovered"
    
    def test_handle_errors_without_recovery(self):
        """Test handle_errors decorator without recovery"""
        error_handler = ErrorHandler()
        
        @handle_errors(error_handler, operation="test_op")
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
    
    def test_handle_errors_no_error(self):
        """Test handle_errors decorator when no error occurs"""
        error_handler = ErrorHandler()
        
        @handle_errors(error_handler, operation="test_op")
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"


class TestRetryConfig:
    """Test RetryConfig functionality"""
    
    def test_retry_config_defaults(self):
        """Test default retry configuration"""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert Exception in config.retry_on
        assert CriticalSystemError in config.stop_on
    
    def test_retry_config_custom(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False,
            retry_on=[ValueError],
            stop_on=[SystemError]
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter is False
        assert config.retry_on == [ValueError]
        assert config.stop_on == [SystemError]


class TestErrorContext:
    """Test ErrorContext functionality"""
    
    def test_error_context_creation(self):
        """Test error context creation"""
        context = ErrorContext(
            operation="test_operation",
            component="test_component",
            phase="test_phase",
            attempt=2,
            metadata={"key": "value"}
        )
        
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.phase == "test_phase"
        assert context.attempt == 2
        assert context.metadata == {"key": "value"}
        assert isinstance(context.start_time, datetime)
    
    def test_error_context_defaults(self):
        """Test error context with defaults"""
        context = ErrorContext(operation="test")
        
        assert context.operation == "test"
        assert context.component is None
        assert context.phase is None
        assert context.attempt == 1
        assert context.metadata == {}


class TestErrorRecord:
    """Test ErrorRecord functionality"""
    
    def test_error_record_creation(self):
        """Test error record creation"""
        error = ValueError("Test error")
        context = ErrorContext(operation="test")
        
        record = ErrorRecord(error=error, context=context)
        
        assert record.error == error
        assert record.context == context
        assert isinstance(record.timestamp, datetime)
        assert record.resolved is False
        assert record.resolution_method is None
    
    def test_error_record_resolution(self):
        """Test error record resolution tracking"""
        error = ValueError("Test error")
        context = ErrorContext(operation="test")
        
        record = ErrorRecord(
            error=error,
            context=context,
            resolved=True,
            resolution_method="recovery_strategy"
        )
        
        assert record.resolved is True
        assert record.resolution_method == "recovery_strategy"