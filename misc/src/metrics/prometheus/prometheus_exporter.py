"""
Prometheus exporter for converting metrics to Prometheus format.

This module handles the conversion of internal metrics to Prometheus-compatible
format and provides registry functionality for metric management.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from ..models import MetricValue
from ..storage import TimeSeriesStorage, QueryEngine, MetricsQuery


class PrometheusMetricType(Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    UNTYPED = "untyped"


@dataclass
class PrometheusMetric:
    """Represents a Prometheus metric with metadata."""
    name: str
    metric_type: PrometheusMetricType
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: Union[float, int] = 0
    timestamp: Optional[datetime] = None
    
    def to_prometheus_line(self) -> str:
        """Convert metric to Prometheus exposition format line."""
        from .prometheus_formatter import PrometheusFormatter
        formatter = PrometheusFormatter()
        return formatter.format_metric_line(self)


class PrometheusRegistry:
    """Registry for managing Prometheus metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, PrometheusMetric] = {}
        self.metric_families: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_metric(self, metric: PrometheusMetric) -> None:
        """Register a metric in the registry."""
        metric_key = self._get_metric_key(metric.name, metric.labels)
        self.metrics[metric_key] = metric
        
        # Update metric family info
        if metric.name not in self.metric_families:
            self.metric_families[metric.name] = {
                "type": metric.metric_type,
                "help": metric.help_text,
                "metrics": []
            }
        
        self.metric_families[metric.name]["metrics"].append(metric)
        self.logger.debug(f"Registered metric: {metric.name}")
    
    def unregister_metric(self, name: str, labels: Dict[str, str] = None) -> bool:
        """Unregister a metric from the registry."""
        labels = labels or {}
        metric_key = self._get_metric_key(name, labels)
        
        if metric_key in self.metrics:
            metric = self.metrics[metric_key]
            del self.metrics[metric_key]
            
            # Update metric family
            if name in self.metric_families:
                family = self.metric_families[name]
                family["metrics"] = [m for m in family["metrics"] if m != metric]
                
                # Remove family if no metrics left
                if not family["metrics"]:
                    del self.metric_families[name]
            
            self.logger.debug(f"Unregistered metric: {name}")
            return True
        
        return False
    
    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[PrometheusMetric]:
        """Get a metric from the registry."""
        labels = labels or {}
        metric_key = self._get_metric_key(name, labels)
        return self.metrics.get(metric_key)
    
    def get_all_metrics(self) -> List[PrometheusMetric]:
        """Get all metrics from the registry."""
        return list(self.metrics.values())
    
    def get_metric_families(self) -> Dict[str, Dict[str, Any]]:
        """Get all metric families."""
        return self.metric_families.copy()
    
    def clear(self) -> None:
        """Clear all metrics from the registry."""
        self.metrics.clear()
        self.metric_families.clear()
        self.logger.info("Cleared all metrics from registry")
    
    def _get_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Generate a unique key for a metric."""
        if not labels:
            return name
        
        # Sort labels for consistent key generation
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}{{{label_str}}}"


class PrometheusExporter:
    """Exports metrics in Prometheus format."""
    
    def __init__(self, storage: TimeSeriesStorage = None, query_engine: QueryEngine = None):
        self.storage = storage
        self.query_engine = query_engine
        self.registry = PrometheusRegistry()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.metric_prefix = ""
        self.default_labels = {}
        self.metric_type_mapping = self._create_default_type_mapping()
        self.help_text_mapping = self._create_default_help_mapping()
        
        # Cache settings
        self.cache_ttl = timedelta(seconds=30)
        self._last_export_time: Optional[datetime] = None
        self._cached_output: Optional[str] = None
    
    def set_metric_prefix(self, prefix: str) -> None:
        """Set a prefix for all exported metrics."""
        self.metric_prefix = prefix.rstrip("_")
        if self.metric_prefix:
            self.metric_prefix += "_"
    
    def set_default_labels(self, labels: Dict[str, str]) -> None:
        """Set default labels to be added to all metrics."""
        self.default_labels = labels.copy()
    
    def add_metric_type_mapping(self, metric_name_pattern: str, prometheus_type: PrometheusMetricType) -> None:
        """Add a mapping from metric name pattern to Prometheus type."""
        self.metric_type_mapping[metric_name_pattern] = prometheus_type
    
    def add_help_text_mapping(self, metric_name_pattern: str, help_text: str) -> None:
        """Add help text for a metric name pattern."""
        self.help_text_mapping[metric_name_pattern] = help_text
    
    async def export_metrics(self, use_cache: bool = True) -> str:
        """Export all metrics in Prometheus format."""
        # Check cache
        if use_cache and self._is_cache_valid():
            return self._cached_output
        
        start_time = time.time()
        
        try:
            # Clear registry
            self.registry.clear()
            
            # Load metrics from storage if available
            if self.storage and self.query_engine:
                await self._load_metrics_from_storage()
            
            # Generate Prometheus output
            output = self._generate_prometheus_output()
            
            # Update cache
            self._cached_output = output
            self._last_export_time = datetime.now()
            
            export_time = time.time() - start_time
            self.logger.info(f"Exported {len(self.registry.metrics)} metrics in {export_time:.3f}s")
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {str(e)}")
            return f"# Error exporting metrics: {str(e)}\n"
    
    async def export_metric_family(self, metric_name: str) -> str:
        """Export a specific metric family in Prometheus format."""
        if not self.storage or not self.query_engine:
            return f"# No storage backend configured\n"
        
        try:
            # Query specific metric
            query = MetricsQuery(metric_names=[metric_name])
            result = await self.query_engine.execute_query(query)
            
            # Convert to Prometheus metrics
            prometheus_metrics = []
            for point in result.points:
                metric_value = MetricValue(
                    name=metric_name,
                    value=point.value,
                    timestamp=point.timestamp,
                    labels=point.labels
                )
                prometheus_metric = self._convert_to_prometheus_metric(metric_value)
                prometheus_metrics.append(prometheus_metric)
            
            # Generate output for this family
            return self._generate_family_output(metric_name, prometheus_metrics)
            
        except Exception as e:
            self.logger.error(f"Error exporting metric family {metric_name}: {str(e)}")
            return f"# Error exporting metric family {metric_name}: {str(e)}\n"
    
    def register_metric_value(self, metric_value: MetricValue) -> None:
        """Register a single metric value."""
        prometheus_metric = self._convert_to_prometheus_metric(metric_value)
        self.registry.register_metric(prometheus_metric)
    
    def register_metric_values(self, metric_values: List[MetricValue]) -> None:
        """Register multiple metric values."""
        for metric_value in metric_values:
            self.register_metric_value(metric_value)
    
    async def _load_metrics_from_storage(self) -> None:
        """Load metrics from storage backend."""
        try:
            # Get all metric names
            metric_names = await self.storage.get_metric_names()
            
            # Query recent data for each metric (last 5 minutes)
            recent_time = datetime.now() - timedelta(minutes=5)
            
            for metric_name in metric_names:
                query = MetricsQuery(
                    metric_names=[metric_name],
                    start_time=recent_time,
                    limit=1000  # Limit to prevent memory issues
                )
                
                result = await self.query_engine.execute_query(query)
                
                # Convert to Prometheus metrics
                for point in result.points:
                    metric_value = MetricValue(
                        name=metric_name,
                        value=point.value,
                        timestamp=point.timestamp,
                        labels=point.labels
                    )
                    prometheus_metric = self._convert_to_prometheus_metric(metric_value)
                    self.registry.register_metric(prometheus_metric)
                    
        except Exception as e:
            self.logger.error(f"Error loading metrics from storage: {str(e)}")
    
    def _convert_to_prometheus_metric(self, metric_value: MetricValue) -> PrometheusMetric:
        """Convert a MetricValue to PrometheusMetric."""
        # Apply prefix
        prometheus_name = self.metric_prefix + metric_value.name
        
        # Combine labels with defaults
        labels = {**self.default_labels, **metric_value.labels}
        
        # Determine metric type
        metric_type = self._determine_metric_type(metric_value.name)
        
        # Get help text
        help_text = self._get_help_text(metric_value.name)
        
        return PrometheusMetric(
            name=prometheus_name,
            metric_type=metric_type,
            help_text=help_text,
            labels=labels,
            value=metric_value.value,
            timestamp=metric_value.timestamp
        )
    
    def _determine_metric_type(self, metric_name: str) -> PrometheusMetricType:
        """Determine Prometheus metric type from metric name."""
        import fnmatch
        
        for pattern, metric_type in self.metric_type_mapping.items():
            if fnmatch.fnmatch(metric_name, pattern):
                return metric_type
        
        return PrometheusMetricType.GAUGE  # Default type
    
    def _get_help_text(self, metric_name: str) -> str:
        """Get help text for a metric."""
        import fnmatch
        
        for pattern, help_text in self.help_text_mapping.items():
            if fnmatch.fnmatch(metric_name, pattern):
                return help_text
        
        return f"Metric {metric_name}"  # Default help text
    
    def _generate_prometheus_output(self) -> str:
        """Generate complete Prometheus exposition format output."""
        from .prometheus_formatter import PrometheusFormatter
        
        formatter = PrometheusFormatter()
        output_lines = []
        
        # Add header comment
        output_lines.append("# Metrics exported by System Health Monitor")
        output_lines.append(f"# Generated at {datetime.now().isoformat()}")
        output_lines.append("")
        
        # Group metrics by family
        families = self.registry.get_metric_families()
        
        for family_name, family_info in sorted(families.items()):
            # Add TYPE and HELP comments
            output_lines.append(f"# TYPE {family_name} {family_info['type'].value}")
            output_lines.append(f"# HELP {family_name} {family_info['help']}")
            
            # Add metric lines
            for metric in sorted(family_info['metrics'], key=lambda m: str(m.labels)):
                line = formatter.format_metric_line(metric)
                output_lines.append(line)
            
            output_lines.append("")  # Empty line between families
        
        return "\n".join(output_lines)
    
    def _generate_family_output(self, family_name: str, metrics: List[PrometheusMetric]) -> str:
        """Generate output for a specific metric family."""
        from .prometheus_formatter import PrometheusFormatter
        
        if not metrics:
            return f"# No data for metric family: {family_name}\n"
        
        formatter = PrometheusFormatter()
        output_lines = []
        
        # Use first metric for family metadata
        first_metric = metrics[0]
        output_lines.append(f"# TYPE {family_name} {first_metric.metric_type.value}")
        output_lines.append(f"# HELP {family_name} {first_metric.help_text}")
        
        # Add metric lines
        for metric in sorted(metrics, key=lambda m: str(m.labels)):
            line = formatter.format_metric_line(metric)
            output_lines.append(line)
        
        output_lines.append("")
        return "\n".join(output_lines)
    
    def _is_cache_valid(self) -> bool:
        """Check if cached output is still valid."""
        if not self._last_export_time or not self._cached_output:
            return False
        
        return datetime.now() - self._last_export_time < self.cache_ttl
    
    def _create_default_type_mapping(self) -> Dict[str, PrometheusMetricType]:
        """Create default metric type mappings."""
        return {
            "*_total": PrometheusMetricType.COUNTER,
            "*_count": PrometheusMetricType.COUNTER,
            "*_counter": PrometheusMetricType.COUNTER,
            "*_requests": PrometheusMetricType.COUNTER,
            "*_errors": PrometheusMetricType.COUNTER,
            "*_bytes": PrometheusMetricType.COUNTER,
            "*_seconds": PrometheusMetricType.COUNTER,
            "*_usage": PrometheusMetricType.GAUGE,
            "*_percent": PrometheusMetricType.GAUGE,
            "*_ratio": PrometheusMetricType.GAUGE,
            "*_temperature": PrometheusMetricType.GAUGE,
            "*_pressure": PrometheusMetricType.GAUGE,
            "*_uptime": PrometheusMetricType.GAUGE,
            "*_running": PrometheusMetricType.GAUGE,
            "container_*": PrometheusMetricType.GAUGE,
            "system_*": PrometheusMetricType.GAUGE,
        }
    
    def _create_default_help_mapping(self) -> Dict[str, str]:
        """Create default help text mappings."""
        return {
            "cpu_*": "CPU related metrics",
            "memory_*": "Memory related metrics",
            "disk_*": "Disk related metrics",
            "network_*": "Network related metrics",
            "container_*": "Container related metrics",
            "system_*": "System related metrics",
            "*_usage": "Resource usage metric",
            "*_percent": "Percentage metric",
            "*_total": "Total counter metric",
            "*_count": "Count metric",
            "*_bytes": "Bytes metric",
            "*_seconds": "Time duration in seconds",
            "*_uptime": "Uptime in seconds",
            "*_running": "Running status (1=running, 0=stopped)",
        }