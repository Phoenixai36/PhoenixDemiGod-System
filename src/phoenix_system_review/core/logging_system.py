"""
Comprehensive logging and monitoring system for Phoenix Hydra System Review

This module provides structured logging, performance monitoring, metrics collection,
and debugging capabilities for the system review tool.
"""

import logging
import logging.handlers
import json
import time
import threading
import psutil
import os
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from functools import wraps
from collections import defaultdict, deque
from enum import Enum


class LogLevel(Enum):
    """Log levels for structured logging"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: str
    message: str
    component: Optional[str] = None
    operation: Optional[str] = None
    phase: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "component": self.component,
            "operation": self.operation,
            "phase": self.phase,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id
        }
    
    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    metric_type: MetricType
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    process_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system metrics to dictionary"""
        return asdict(self)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def __init__(self, include_system_info: bool = True):
        super().__init__()
        self.include_system_info = include_system_info
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'component'):
            log_entry['component'] = record.component
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'phase'):
            log_entry['phase'] = record.phase
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = record.metadata
        
        # Add system info if enabled
        if self.include_system_info:
            log_entry['process_id'] = os.getpid()
            log_entry['thread_id'] = threading.get_ident()
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class MetricsCollector:
    """Collects and manages performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
            
            metric = PerformanceMetric(
                name=name,
                metric_type=MetricType.COUNTER,
                value=self.counters[key],
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics.append(metric)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        with self._lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
            
            metric = PerformanceMetric(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics.append(metric)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        with self._lock:
            key = self._make_key(name, tags)
            self.histograms[key].append(value)
            
            metric = PerformanceMetric(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics.append(metric)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer value"""
        with self._lock:
            key = self._make_key(name, tags)
            self.timers[key].append(duration_ms)
            
            metric = PerformanceMetric(
                name=name,
                metric_type=MetricType.TIMER,
                value=duration_ms,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics.append(metric)
    
    def get_counter_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value"""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0)
    
    def get_gauge_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value"""
        key = self._make_key(name, tags)
        return self.gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, tags)
        values = self.histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)]
        }
    
    def get_timer_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get timer statistics"""
        key = self._make_key(name, tags)
        values = self.timers.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "min_ms": min(values),
            "max_ms": max(values),
            "mean_ms": sum(values) / count,
            "p50_ms": sorted_values[int(count * 0.5)],
            "p95_ms": sorted_values[int(count * 0.95)],
            "p99_ms": sorted_values[int(count * 0.99)]
        }
    
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all collected metrics"""
        with self._lock:
            return [metric.to_dict() for metric in self.metrics]
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create a unique key for metric storage"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self, collection_interval: float = 30.0):
        self.collection_interval = collection_interval
        self.metrics_history: deque = deque(maxlen=1000)
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start system monitoring in background thread"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Get process count
            process_count = len(psutil.pids())
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                process_count=process_count
            )
        except Exception as e:
            # Return default metrics if collection fails
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                process_count=0
            )
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[SystemMetrics]:
        """Get system metrics history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self._lock:
            return [
                metrics for metrics in self.metrics_history
                if metrics.timestamp >= cutoff_time
            ]
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                metrics = self.get_current_metrics()
                with self._lock:
                    self.metrics_history.append(metrics)
                
                time.sleep(self.collection_interval)
            except Exception:
                # Continue monitoring even if individual collection fails
                time.sleep(self.collection_interval)


class PhoenixSystemLogger:
    """Main logging system for Phoenix Hydra System Review"""
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_metrics: bool = True,
        enable_monitoring: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_level = log_level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_metrics = enable_metrics
        self.enable_monitoring = enable_monitoring
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.logger = self._setup_logger(max_file_size, backup_count)
        self.metrics_collector = MetricsCollector() if enable_metrics else None
        self.system_monitor = SystemMonitor() if enable_monitoring else None
        
        # Start monitoring if enabled
        if self.system_monitor:
            self.system_monitor.start_monitoring()
        
        # Track correlation IDs for request tracing
        self._correlation_ids: Dict[int, str] = {}
    
    def _setup_logger(self, max_file_size: int, backup_count: int) -> logging.Logger:
        """Setup the main logger with handlers"""
        logger = logging.getLogger("phoenix_system_review")
        logger.setLevel(getattr(logging, self.log_level.value))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = StructuredFormatter()
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "phoenix_system_review.log",
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Separate error log
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "phoenix_system_review_errors.log",
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        
        return logger
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread"""
        thread_id = threading.get_ident()
        self._correlation_ids[thread_id] = correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for current thread"""
        thread_id = threading.get_ident()
        return self._correlation_ids.get(thread_id)
    
    def clear_correlation_id(self):
        """Clear correlation ID for current thread"""
        thread_id = threading.get_ident()
        self._correlation_ids.pop(thread_id, None)
    
    def log(
        self,
        level: LogLevel,
        message: str,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        phase: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ):
        """Log a structured message"""
        extra = {
            'component': component,
            'operation': operation,
            'phase': phase,
            'duration_ms': duration_ms,
            'metadata': metadata or {},
            'correlation_id': self.get_correlation_id()
        }
        
        # Remove None values
        extra = {k: v for k, v in extra.items() if v is not None}
        
        self.logger.log(
            getattr(logging, level.value),
            message,
            extra=extra,
            exc_info=exc_info
        )
        
        # Increment metrics if enabled
        if self.metrics_collector:
            tags = {}
            if component:
                tags['component'] = component
            if phase:
                tags['phase'] = phase
            
            self.metrics_collector.increment_counter(
                f"log_entries_{level.value.lower()}",
                tags=tags
            )
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        kwargs.setdefault('exc_info', True)
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        kwargs.setdefault('exc_info', True)
        self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        if self.metrics_collector:
            self.metrics_collector.increment_counter(name, value, tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        if self.metrics_collector:
            self.metrics_collector.set_gauge(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        if self.metrics_collector:
            self.metrics_collector.record_histogram(name, value, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer value"""
        if self.metrics_collector:
            self.metrics_collector.record_timer(name, duration_ms, tags)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        if not self.metrics_collector:
            return {}
        
        return {
            "counters": {
                name: self.metrics_collector.get_counter_value(name.split('[')[0])
                for name in self.metrics_collector.counters.keys()
            },
            "gauges": dict(self.metrics_collector.gauges),
            "histogram_stats": {
                name: self.metrics_collector.get_histogram_stats(name.split('[')[0])
                for name in self.metrics_collector.histograms.keys()
            },
            "timer_stats": {
                name: self.metrics_collector.get_timer_stats(name.split('[')[0])
                for name in self.metrics_collector.timers.keys()
            }
        }
    
    def get_system_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics"""
        if self.system_monitor:
            return self.system_monitor.get_current_metrics()
        return None
    
    def get_system_metrics_history(self, duration_minutes: int = 60) -> List[SystemMetrics]:
        """Get system metrics history"""
        if self.system_monitor:
            return self.system_monitor.get_metrics_history(duration_minutes)
        return []
    
    def shutdown(self):
        """Shutdown logging system"""
        if self.system_monitor:
            self.system_monitor.stop_monitoring()
        
        # Flush and close all handlers
        for handler in self.logger.handlers:
            handler.flush()
            handler.close()


# Decorators for automatic logging and metrics
def log_operation(
    logger: PhoenixSystemLogger,
    component: Optional[str] = None,
    phase: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    record_timing: bool = True
):
    """Decorator to automatically log function operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation = func.__name__
            start_time = time.time()
            
            # Log start
            log_data = {"operation": operation}
            if log_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)
            
            logger.info(
                f"Starting operation: {operation}",
                component=component,
                operation=operation,
                phase=phase,
                metadata=log_data
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log success
                success_data = {"status": "success"}
                if log_result:
                    success_data["result"] = str(result)
                
                logger.info(
                    f"Completed operation: {operation}",
                    component=component,
                    operation=operation,
                    phase=phase,
                    duration_ms=duration_ms,
                    metadata=success_data
                )
                
                # Record timing metric
                if record_timing:
                    tags = {}
                    if component:
                        tags["component"] = component
                    if phase:
                        tags["phase"] = phase
                    
                    logger.record_timer(f"operation_duration", duration_ms, tags)
                    logger.increment_counter("operations_completed", tags=tags)
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log error
                logger.error(
                    f"Failed operation: {operation}",
                    component=component,
                    operation=operation,
                    phase=phase,
                    duration_ms=duration_ms,
                    metadata={"status": "error", "error": str(e)}
                )
                
                # Record error metric
                tags = {}
                if component:
                    tags["component"] = component
                if phase:
                    tags["phase"] = phase
                
                logger.increment_counter("operations_failed", tags=tags)
                
                raise
        
        return wrapper
    
    return decorator


@contextmanager
def log_context(
    logger: PhoenixSystemLogger,
    operation: str,
    component: Optional[str] = None,
    phase: Optional[str] = None,
    correlation_id: Optional[str] = None
):
    """Context manager for logging operations with automatic timing"""
    if correlation_id:
        logger.set_correlation_id(correlation_id)
    
    start_time = time.time()
    
    logger.info(
        f"Starting: {operation}",
        component=component,
        operation=operation,
        phase=phase
    )
    
    try:
        yield logger
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Completed: {operation}",
            component=component,
            operation=operation,
            phase=phase,
            duration_ms=duration_ms
        )
        
        # Record metrics
        tags = {}
        if component:
            tags["component"] = component
        if phase:
            tags["phase"] = phase
        
        logger.record_timer("context_duration", duration_ms, tags)
        logger.increment_counter("contexts_completed", tags=tags)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            f"Failed: {operation}",
            component=component,
            operation=operation,
            phase=phase,
            duration_ms=duration_ms,
            metadata={"error": str(e)}
        )
        
        # Record error metrics
        tags = {}
        if component:
            tags["component"] = component
        if phase:
            tags["phase"] = phase
        
        logger.increment_counter("contexts_failed", tags=tags)
        
        raise
    
    finally:
        if correlation_id:
            logger.clear_correlation_id()


# Global logger instance
_global_logger: Optional[PhoenixSystemLogger] = None


def get_logger() -> PhoenixSystemLogger:
    """Get the global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = PhoenixSystemLogger()
    return _global_logger


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: LogLevel = LogLevel.INFO,
    **kwargs
) -> PhoenixSystemLogger:
    """Setup global logging system"""
    global _global_logger
    _global_logger = PhoenixSystemLogger(
        log_dir=log_dir,
        log_level=log_level,
        **kwargs
    )
    return _global_logger