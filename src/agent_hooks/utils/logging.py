"""
Logging and error handling utilities for the Agent Hooks Enhancement system.

This module provides standardized logging and error handling functionality
for the hook system, including structured logging, error categorization,
and error reporting.
"""

import logging
import sys
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable
import json
import uuid

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


class ErrorCategory(Enum):
    """Categories of errors that can occur in the hook system."""
    CONFIGURATION = "configuration"
    EXECUTION = "execution"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    PERMISSION = "permission"
    NETWORK = "network"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    CRITICAL = "critical"  # System cannot function
    HIGH = "high"          # Major functionality impacted
    MEDIUM = "medium"      # Some functionality impacted
    LOW = "low"            # Minor issues, system still functional
    INFO = "info"          # Informational only


class HookError(Exception):
    """Base exception class for hook-related errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        hook_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize a hook error.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            hook_id: ID of the hook that caused the error
            context: Additional context information
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.hook_id = hook_id
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.error_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        result = {
            "error_id": self.error_id,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.hook_id:
            result["hook_id"] = self.hook_id
        
        if self.context:
            result["context"] = self.context
        
        if self.cause:
            result["cause"] = str(self.cause)
            result["cause_type"] = type(self.cause).__name__
        
        return result
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.severity.value.upper()} {self.category.value} error: {self.message}"


class ConfigurationError(HookError):
    """Error related to hook configuration."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize a configuration error."""
        kwargs["category"] = ErrorCategory.CONFIGURATION
        super().__init__(message, **kwargs)


class ExecutionError(HookError):
    """Error that occurs during hook execution."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize an execution error."""
        kwargs["category"] = ErrorCategory.EXECUTION
        super().__init__(message, **kwargs)


class ResourceError(HookError):
    """Error related to resource constraints."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize a resource error."""
        kwargs["category"] = ErrorCategory.RESOURCE
        super().__init__(message, **kwargs)


class TimeoutError(HookError):
    """Error that occurs when a hook execution times out."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize a timeout error."""
        kwargs["category"] = ErrorCategory.TIMEOUT
        super().__init__(message, **kwargs)


class DependencyError(HookError):
    """Error related to missing or incompatible dependencies."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize a dependency error."""
        kwargs["category"] = ErrorCategory.DEPENDENCY
        super().__init__(message, **kwargs)


class PermissionError(HookError):
    """Error related to insufficient permissions."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize a permission error."""
        kwargs["category"] = ErrorCategory.PERMISSION
        super().__init__(message, **kwargs)


class NetworkError(HookError):
    """Error related to network connectivity."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize a network error."""
        kwargs["category"] = ErrorCategory.NETWORK
        super().__init__(message, **kwargs)


class StructuredLogger:
    """
    Logger that produces structured log messages.
    
    This logger adds context information to log messages and supports
    both text and JSON output formats.
    """
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        json_output: bool = False,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a structured logger.
        
        Args:
            name: Logger name
            level: Logging level
            json_output: Whether to output logs as JSON
            context: Default context information to include in all log messages
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.json_output = json_output
        self.context = context or {}
    
    def _log(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Log a message with context information.
        
        Args:
            level: Logging level
            message: Log message
            context: Additional context information
            error: Exception to include in the log
        """
        log_context = {**self.context}
        if context:
            log_context.update(context)
        
        log_data = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": log_context
        }
        
        if error:
            log_data["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        if self.json_output:
            self.logger.log(level, json.dumps(log_data))
        else:
            context_str = " ".join(f"{k}={v}" for k, v in log_context.items()) if log_context else ""
            error_str = f" | Error: {type(error).__name__}: {error}" if error else ""
            self.logger.log(level, f"{message} | {context_str}{error_str}")
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, message, context, error)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None) -> None:
        """Log an info message."""
        self._log(logging.INFO, message, context, error)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, message, context, error)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None) -> None:
        """Log an error message."""
        self._log(logging.ERROR, message, context, error)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, message, context, error)
    
    def set_level(self, level: int) -> None:
        """Set the logging level."""
        self.logger.setLevel(level)
    
    def with_context(self, context: Dict[str, Any]) -> 'StructuredLogger':
        """Create a new logger with additional context."""
        new_context = {**self.context, **context}
        return StructuredLogger(self.logger.name, self.logger.level, self.json_output, new_context)


class ErrorReporter:
    """
    Reporter for hook errors.
    
    This class is responsible for reporting errors to various destinations,
    such as logs, error tracking services, and notification channels.
    """
    
    def __init__(self, logger: StructuredLogger):
        """
        Initialize an error reporter.
        
        Args:
            logger: Logger to use for error reporting
        """
        self.logger = logger
        self.handlers: Dict[ErrorSeverity, List[Callable[[HookError], None]]] = {
            severity: [] for severity in ErrorSeverity
        }
    
    def register_handler(self, severity: ErrorSeverity, handler: Callable[[HookError], None]) -> None:
        """
        Register an error handler for a specific severity level.
        
        Args:
            severity: Error severity level
            handler: Function to call when an error of the specified severity occurs
        """
        self.handlers[severity].append(handler)
    
    def report(self, error: HookError) -> None:
        """
        Report an error.
        
        Args:
            error: Error to report
        """
        # Log the error
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.DEBUG
        }[error.severity]
        
        self.logger._log(log_level, str(error), error.context, error.cause)
        
        # Call registered handlers
        for handler in self.handlers[error.severity]:
            try:
                handler(error)
            except Exception as e:
                self.logger.error(
                    f"Error in error handler: {e}",
                    {"handler": handler.__name__, "error_id": error.error_id},
                    e
                )
    
    def report_exception(
        self,
        exception: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        hook_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> HookError:
        """
        Report an exception as a hook error.
        
        Args:
            exception: Exception to report
            severity: Error severity
            category: Error category
            hook_id: ID of the hook that caused the error
            context: Additional context information
            
        Returns:
            Created hook error
        """
        error = HookError(
            str(exception),
            category=category,
            severity=severity,
            hook_id=hook_id,
            context=context,
            cause=exception
        )
        
        self.report(error)
        return error


# Create a default logger and error reporter
default_logger = StructuredLogger("agent_hooks")
default_error_reporter = ErrorReporter(default_logger)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger
    """
    return StructuredLogger(f"agent_hooks.{name}")


def get_error_reporter(logger: Optional[StructuredLogger] = None) -> ErrorReporter:
    """
    Get an error reporter.
    
    Args:
        logger: Logger to use for error reporting, or None to use the default logger
        
    Returns:
        Error reporter
    """
    if logger is None:
        return default_error_reporter
    return ErrorReporter(logger)
