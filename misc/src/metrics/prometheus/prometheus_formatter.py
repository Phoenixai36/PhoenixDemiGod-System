"""
Prometheus format utilities for metric formatting.

This module provides utilities for formatting metrics according to the
Prometheus exposition format specification.
"""

import re
from typing import Dict, Any, Union
from .prometheus_exporter import PrometheusMetric


def format_metric_name(name: str) -> str:
    """
    Format a metric name according to Prometheus naming conventions.
    
    Prometheus metric names must match the regex [a-zA-Z_:][a-zA-Z0-9_:]*
    """
    # Replace invalid characters with underscores
    formatted = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
    
    # Ensure it starts with a letter, underscore, or colon
    if formatted and not re.match(r'^[a-zA-Z_:]', formatted):
        formatted = '_' + formatted
    
    # Remove consecutive underscores
    formatted = re.sub(r'_+', '_', formatted)
    
    # Remove trailing underscores
    formatted = formatted.rstrip('_')
    
    return formatted or 'unnamed_metric'


def format_label_value(value: Any) -> str:
    """Format a label value for Prometheus exposition format."""
    return str(value)


def escape_label_value(value: str) -> str:
    """
    Escape a label value according to Prometheus format.
    
    Label values can contain any Unicode characters, but backslashes,
    double quotes, and line feeds must be escaped.
    """
    # Escape backslashes first
    escaped = value.replace('\\', '\\\\')
    
    # Escape double quotes
    escaped = escaped.replace('"', '\\"')
    
    # Escape line feeds
    escaped = escaped.replace('\n', '\\n')
    
    return escaped


class PrometheusFormatter:
    """Formatter for Prometheus exposition format."""
    
    def __init__(self):
        self.include_timestamps = False
        self.timestamp_precision = 3  # milliseconds
    
    def format_metric_line(self, metric: PrometheusMetric) -> str:
        """Format a single metric line in Prometheus exposition format."""
        # Format metric name
        name = format_metric_name(metric.name)
        
        # Format labels
        labels_str = self._format_labels(metric.labels)
        
        # Format value
        value_str = self._format_value(metric.value)
        
        # Build the line
        if labels_str:
            line = f"{name}{{{labels_str}}} {value_str}"
        else:
            line = f"{name} {value_str}"
        
        # Add timestamp if configured and available
        if self.include_timestamps and metric.timestamp:
            timestamp_ms = int(metric.timestamp.timestamp() * 1000)
            line += f" {timestamp_ms}"
        
        return line
    
    def format_help_line(self, metric_name: str, help_text: str) -> str:
        """Format a HELP comment line."""
        name = format_metric_name(metric_name)
        return f"# HELP {name} {help_text}"
    
    def format_type_line(self, metric_name: str, metric_type: str) -> str:
        """Format a TYPE comment line."""
        name = format_metric_name(metric_name)
        return f"# TYPE {name} {metric_type}"
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus exposition format."""
        if not labels:
            return ""
        
        formatted_labels = []
        for key, value in sorted(labels.items()):
            # Format label name (same rules as metric names)
            formatted_key = format_metric_name(key)
            
            # Format and escape label value
            formatted_value = format_label_value(value)
            escaped_value = escape_label_value(formatted_value)
            
            formatted_labels.append(f'{formatted_key}="{escaped_value}"')
        
        return ",".join(formatted_labels)
    
    def _format_value(self, value: Union[float, int]) -> str:
        """Format a metric value."""
        if isinstance(value, float):
            # Handle special float values
            if value != value:  # NaN
                return "NaN"
            elif value == float('inf'):
                return "+Inf"
            elif value == float('-inf'):
                return "-Inf"
            else:
                # Format with appropriate precision
                return f"{value:.6g}"
        else:
            return str(value)
    
    def format_metric_family(self, family_name: str, metrics: list, metric_type: str, help_text: str) -> str:
        """Format a complete metric family."""
        lines = []
        
        # Add TYPE and HELP comments
        lines.append(self.format_type_line(family_name, metric_type))
        lines.append(self.format_help_line(family_name, help_text))
        
        # Add metric lines
        for metric in metrics:
            lines.append(self.format_metric_line(metric))
        
        return "\n".join(lines)
    
    def validate_metric_name(self, name: str) -> bool:
        """Validate a metric name according to Prometheus rules."""
        if not name:
            return False
        
        # Check if it matches the required pattern
        return bool(re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$', name))
    
    def validate_label_name(self, name: str) -> bool:
        """Validate a label name according to Prometheus rules."""
        if not name:
            return False
        
        # Label names must match [a-zA-Z_][a-zA-Z0-9_]*
        # They cannot start with __
        if name.startswith('__'):
            return False
        
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
    
    def sanitize_metric_name(self, name: str) -> str:
        """Sanitize a metric name to make it Prometheus-compatible."""
        return format_metric_name(name)
    
    def sanitize_label_name(self, name: str) -> str:
        """Sanitize a label name to make it Prometheus-compatible."""
        # Similar to metric names but cannot start with __
        sanitized = format_metric_name(name)
        
        # Remove __ prefix if present
        if sanitized.startswith('__'):
            sanitized = sanitized[2:]
        
        # Ensure it's not empty
        return sanitized or 'label'