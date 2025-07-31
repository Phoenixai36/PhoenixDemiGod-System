"""
Error handling framework with graceful degradation and retry mechanisms

This module provides comprehensive error handling capabilities for the Phoenix
Hydra System Review Tool, including retry logic, graceful degradation, and
structured error recovery.
"""

import asyncio
import logging
import time
from typing import Optional, Any, Callable, Dict, List, Type, Union
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .exceptions import (
    SystemReviewError, ErrorSeverity, ErrorCategory,
    DiscoveryError, AnalysisError, AssessmentError, ReportingError,
    NetworkError, FileSystemError, ConfigurationParsingError,
    CriticalSystemError, RecoverableError, is_recoverable_error, get_error_severity
)
from ..models.data_models import Component, EvaluationResult


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    stop_on: List[Type[Exception]] = field(default_factory=lambda: [CriticalSystemError])


@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    component: Optional[str] = None
    phase: Optional[str] = None
    attempt: int = 1
    start_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error: Exception
    context: ErrorContext
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_method: Optional[str] = None


class ErrorHandler:
    """Comprehensive error handler with retry and recovery mechanisms"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: List[ErrorRecord] = []
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default recovery strategies for common error types"""
        self.recovery_strategies.update({
            FileSystemError: self._handle_file_system_error,
            NetworkError: self._handle_network_error,
            ConfigurationParsingError: self._handle_config_parsing_error,
            DiscoveryError: self._handle_discovery_error,
            AnalysisError: self._handle_analysis_error,
            AssessmentError: self._handle_assessment_error,
            ReportingError: self._handle_reporting_error,
        })
    
    def register_recovery_strategy(
        self,
        error_type: Type[Exception],
        strategy: Callable[[Exception, ErrorContext], Any]
    ):
        """Register a custom recovery strategy for an error type"""
        self.recovery_strategies[error_type] = strategy
    
    def register_fallback_handler(
        self,
        operation: str,
        handler: Callable[[Exception, ErrorContext], Any]
    ):
        """Register a fallback handler for a specific operation"""
        self.fallback_handlers[operation] = handler
    
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        allow_recovery: bool = True
    ) -> Optional[Any]:
        """
        Handle an error with appropriate recovery strategy
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            allow_recovery: Whether to attempt recovery
            
        Returns:
            Recovery result if successful, None if unrecoverable
        """
        # Record the error
        error_record = ErrorRecord(error=error, context=context)
        self.error_history.append(error_record)
        
        # Log the error
        self._log_error(error, context)
        
        # Check if error is recoverable
        if not allow_recovery or not is_recoverable_error(error):
            self.logger.error(f"Unrecoverable error in {context.operation}: {error}")
            return None
        
        # Try specific recovery strategy
        recovery_result = self._try_recovery_strategy(error, context)
        if recovery_result is not None:
            error_record.resolved = True
            error_record.resolution_method = "recovery_strategy"
            return recovery_result
        
        # Try fallback handler
        fallback_result = self._try_fallback_handler(error, context)
        if fallback_result is not None:
            error_record.resolved = True
            error_record.resolution_method = "fallback_handler"
            return fallback_result
        
        # Try graceful degradation
        degraded_result = self._try_graceful_degradation(error, context)
        if degraded_result is not None:
            error_record.resolved = True
            error_record.resolution_method = "graceful_degradation"
            return degraded_result
        
        self.logger.warning(f"No recovery possible for error in {context.operation}: {error}")
        return None
    
    def _try_recovery_strategy(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Try to recover using registered strategy"""
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                try:
                    self.logger.info(f"Attempting recovery for {error_type.__name__} in {context.operation}")
                    return strategy(error, context)
                except Exception as recovery_error:
                    self.logger.warning(f"Recovery strategy failed: {recovery_error}")
                    break
        return None
    
    def _try_fallback_handler(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Try to use fallback handler"""
        if context.operation in self.fallback_handlers:
            try:
                self.logger.info(f"Using fallback handler for {context.operation}")
                return self.fallback_handlers[context.operation](error, context)
            except Exception as fallback_error:
                self.logger.warning(f"Fallback handler failed: {fallback_error}")
        return None
    
    def _try_graceful_degradation(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Try graceful degradation based on operation type"""
        if context.phase == "discovery":
            return self._degrade_discovery_operation(error, context)
        elif context.phase == "analysis":
            return self._degrade_analysis_operation(error, context)
        elif context.phase == "assessment":
            return self._degrade_assessment_operation(error, context)
        elif context.phase == "reporting":
            return self._degrade_reporting_operation(error, context)
        return None
    
    def _log_error(self, error: Exception, context: ErrorContext):
        """Log error with appropriate level and context"""
        severity = get_error_severity(error)
        
        log_data = {
            'operation': context.operation,
            'component': context.component,
            'phase': context.phase,
            'attempt': context.attempt,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'metadata': context.metadata
        }
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", extra=log_data)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error occurred", extra=log_data)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error occurred", extra=log_data)
        else:
            self.logger.info("Low severity error occurred", extra=log_data)
    
    # Default recovery strategies
    def _handle_file_system_error(self, error: FileSystemError, context: ErrorContext) -> Optional[Any]:
        """Handle file system errors"""
        if hasattr(error, 'file_path') and error.file_path:
            # Try alternative file paths or create missing directories
            if "not found" in str(error).lower():
                self.logger.info(f"File not found: {error.file_path}, attempting to create or find alternative")
                # Return empty result to continue processing
                return {}
        return None
    
    def _handle_network_error(self, error: NetworkError, context: ErrorContext) -> Optional[Any]:
        """Handle network errors"""
        if hasattr(error, 'url'):
            self.logger.info(f"Network error for {error.url}, marking service as unavailable")
            return {"status": "unavailable", "error": str(error)}
        return None
    
    def _handle_config_parsing_error(self, error: ConfigurationParsingError, context: ErrorContext) -> Optional[Any]:
        """Handle configuration parsing errors"""
        if hasattr(error, 'config_file'):
            self.logger.info(f"Config parsing failed for {error.config_file}, using default configuration")
            return {"config": {}, "source": "default", "error": str(error)}
        return None
    
    def _handle_discovery_error(self, error: DiscoveryError, context: ErrorContext) -> Optional[Any]:
        """Handle discovery phase errors"""
        return {"components": [], "partial": True, "error": str(error)}
    
    def _handle_analysis_error(self, error: AnalysisError, context: ErrorContext) -> Optional[Any]:
        """Handle analysis phase errors"""
        if context.component:
            # Return partial evaluation result
            return EvaluationResult(
                component=Component(
                    name=context.component,
                    category=context.metadata.get('category', 'unknown'),
                    path=context.metadata.get('path', ''),
                ),
                completion_percentage=0.0,
                quality_score=0.0,
                issues=[{"severity": "high", "description": f"Analysis failed: {error}"}]
            )
        return None
    
    def _handle_assessment_error(self, error: AssessmentError, context: ErrorContext) -> Optional[Any]:
        """Handle assessment phase errors"""
        return {"completion": 0.0, "gaps": [], "partial": True, "error": str(error)}
    
    def _handle_reporting_error(self, error: ReportingError, context: ErrorContext) -> Optional[Any]:
        """Handle reporting phase errors"""
        return f"# Error Report\n\nReport generation failed: {error}\n\nPlease check logs for details."
    
    # Graceful degradation methods
    def _degrade_discovery_operation(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Graceful degradation for discovery operations"""
        self.logger.info(f"Degrading discovery operation {context.operation}")
        return {"components": [], "partial": True, "degraded": True}
    
    def _degrade_analysis_operation(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Graceful degradation for analysis operations"""
        self.logger.info(f"Degrading analysis operation {context.operation}")
        if context.component:
            return EvaluationResult(
                component=Component(name=context.component, category="unknown", path=""),
                completion_percentage=0.0,
                quality_score=0.0,
                issues=[{"severity": "high", "description": "Analysis degraded due to error"}]
            )
        return None
    
    def _degrade_assessment_operation(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Graceful degradation for assessment operations"""
        self.logger.info(f"Degrading assessment operation {context.operation}")
        return {"completion": 0.0, "degraded": True}
    
    def _degrade_reporting_operation(self, error: Exception, context: ErrorContext) -> Optional[Any]:
        """Graceful degradation for reporting operations"""
        self.logger.info(f"Degrading reporting operation {context.operation}")
        return "# Degraded Report\n\nReport generation encountered errors. Partial results may be available."
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        total_errors = len(self.error_history)
        resolved_errors = sum(1 for record in self.error_history if record.resolved)
        
        error_types = {}
        for record in self.error_history:
            error_type = type(record.error).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_errors,
            "unresolved_errors": total_errors - resolved_errors,
            "resolution_rate": resolved_errors / total_errors if total_errors > 0 else 0,
            "error_types": error_types,
            "recent_errors": [
                {
                    "error": str(record.error),
                    "operation": record.context.operation,
                    "timestamp": record.timestamp.isoformat(),
                    "resolved": record.resolved
                }
                for record in self.error_history[-10:]  # Last 10 errors
            ]
        }


def with_retry(
    config: Optional[RetryConfig] = None,
    error_handler: Optional[ErrorHandler] = None
):
    """
    Decorator to add retry logic to functions
    
    Args:
        config: Retry configuration
        error_handler: Error handler instance
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should stop retrying
                    if any(isinstance(e, stop_type) for stop_type in config.stop_on):
                        break
                    
                    # Check if we should retry
                    if not any(isinstance(e, retry_type) for retry_type in config.retry_on):
                        break
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                    
                    logging.getLogger(__name__).info(
                        f"Attempt {attempt} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # If we have an error handler, try to handle the final error
            if error_handler and last_exception:
                context = ErrorContext(
                    operation=func.__name__,
                    attempt=config.max_attempts,
                    metadata={"args": str(args), "kwargs": str(kwargs)}
                )
                recovery_result = error_handler.handle_error(last_exception, context)
                if recovery_result is not None:
                    return recovery_result
            
            # Re-raise the last exception
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should stop retrying
                    if any(isinstance(e, stop_type) for stop_type in config.stop_on):
                        break
                    
                    # Check if we should retry
                    if not any(isinstance(e, retry_type) for retry_type in config.retry_on):
                        break
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** (attempt - 1)),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                    
                    logging.getLogger(__name__).info(
                        f"Attempt {attempt} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            # If we have an error handler, try to handle the final error
            if error_handler and last_exception:
                context = ErrorContext(
                    operation=func.__name__,
                    attempt=config.max_attempts,
                    metadata={"args": str(args), "kwargs": str(kwargs)}
                )
                recovery_result = error_handler.handle_error(last_exception, context)
                if recovery_result is not None:
                    return recovery_result
            
            # Re-raise the last exception
            raise last_exception
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_errors(
    error_handler: Optional[ErrorHandler] = None,
    operation: Optional[str] = None,
    component: Optional[str] = None,
    phase: Optional[str] = None,
    allow_recovery: bool = True
):
    """
    Decorator to add error handling to functions
    
    Args:
        error_handler: Error handler instance
        operation: Operation name for context
        component: Component name for context
        phase: Phase name for context
        allow_recovery: Whether to attempt error recovery
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    context = ErrorContext(
                        operation=operation or func.__name__,
                        component=component,
                        phase=phase,
                        metadata={"args": str(args), "kwargs": str(kwargs)}
                    )
                    recovery_result = error_handler.handle_error(e, context, allow_recovery)
                    if recovery_result is not None:
                        return recovery_result
                raise
        
        return wrapper
    
    return decorator