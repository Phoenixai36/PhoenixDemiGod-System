"""
Prometheus metrics formatting utilities.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from ..models import MetricValue


class PrometheusFormatter:
    """Formats metrics for Prometheus exposition format."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._metric_types: Dict[str, str] = {}
        self._metric_help: Dict[str, str] = {}
    
    def format_metrics(self, metrics: List[MetricValue], 
                      include_timestamp: bool = True,
                      include_help: bool = True) -> str:
        """
        Format metrics in Prometheus exposition format.
        
        Args:
            metrics: List of MetricValue objects to format
            include_timestamp: Whether to include timestamps
            include_help: Whether to include HELP and TYPE comments
            
        Returns:
            Formatted Prometheus metrics string
        """
        if not metrics:
            return ""
        
        # Group metrics by name for better organization
        metrics_by_name = self._group_metrics_by_name(metrics)
        
        output_lines = []
        
        for metric_name, metric_list in sorted(metrics_by_name.items()):
            # Sanitize metric name for Prometheus
            prometheus_name = self._sanitize_metric_name(metric_name)
            
            if include_help:
                # Add TYPE and HELP comments
                metric_type = self._infer_metric_type(metric_name, metric_list)
                help_text = self._get_help_text(metric_name)
                
                if help_text:
                    output_lines.append(f"# HELP {prometheus_name} {help_text}")
                
                output_lines.append(f"# TYPE {prometheus_name} {metric_type}")
            
            # Format individual metric samples
            for metric in metric_list:
                formatted_line = self._format_metric_sample(
                    prometheus_name, 
                    metric, 
                    include_timestamp
                )
                if formatted_line:
                    output_lines.append(formatted_line)
            
            # Add empty line between metric families
            if include_help:
                output_lines.append("")
        
        return "\n".join(output_lines)
    
    def format_single_metric(self, metric: MetricValue, 
                           include_timestamp: bool = True) -> str:
        """Format a single metric value."""
        prometheus_name = self._sanitize_metric_name(metric.name)
        return self._format_metric_sample(prometheus_name, metric, include_timestamp)
    
    def _group_metrics_by_name(self, metrics: List[MetricValue]) -> Dict[str, List[MetricValue]]:
        """Group metrics by name."""
        grouped = {}
        for metric in metrics:
            if metric.name not in grouped:
                grouped[metric.name] = []
            grouped[metric.name].append(metric)
        return grouped
    
    def _sanitize_metric_name(self, name: str) -> str:
        """
        Sanitize metric name for Prometheus format.
        
        Prometheus metric names must match: [a-zA-Z_:][a-zA-Z0-9_:]*
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
        
        # Ensure it starts with a letter or underscore
        if sanitized and not re.match(r'^[a-zA-Z_:]', sanitized):
            sanitized = '_' + sanitized
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove trailing underscores
        sanitized = sanitized.rstrip('_')
        
        return sanitized or 'unnamed_metric'
    
    def _sanitize_label_name(self, name: str) -> str:
        """
        Sanitize label name for Prometheus format.
        
        Label names must match: [a-zA-Z_][a-zA-Z0-9_]*
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it starts with a letter or underscore
        if sanitized and not re.match(r'^[a-zA-Z_]', sanitized):
            sanitized = '_' + sanitized
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove trailing underscores
        sanitized = sanitized.rstrip('_')
        
        return sanitized or 'unnamed_label'
    
    def _escape_label_value(self, value: str) -> str:
        """Escape label value for Prometheus format."""
        if not isinstance(value, str):
            value = str(value)
        
        # Escape backslashes, newlines, tabs, and double quotes
        value = value.replace('\\', '\\\\')
        value = value.replace('\n', '\\n')
        value = value.replace('\t', '\\t')
        value = value.replace('"', '\\"')
        
        return value
    
    def _format_metric_sample(self, metric_name: str, metric: MetricValue, 
                            include_timestamp: bool) -> str:
        """Format a single metric sample."""
        try:
            # Format labels
            labels_str = ""
            if metric.labels:
                label_pairs = []
                for key, value in sorted(metric.labels.items()):
                    sanitized_key = self._sanitize_label_name(key)
                    escaped_value = self._escape_label_value(value)
                    label_pairs.append(f'{sanitized_key}="{escaped_value}"')
                
                if label_pairs:
                    labels_str = "{" + ",".join(label_pairs) + "}"
            
            # Format value
            if isinstance(metric.value, bool):
                value_str = "1" if metric.value else "0"
            elif isinstance(metric.value, (int, float)):
                if metric.value == float('inf'):
                    value_str = "+Inf"
                elif metric.value == float('-inf'):
                    value_str = "-Inf"
                elif metric.value != metric.value:  # NaN check
                    value_str = "NaN"
                else:
                    value_str = str(metric.value)
            else:
                # Convert other types to string, then to float if possible
                try:
                    value_str = str(float(metric.value))
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid metric value: {metric.value}")
                    return ""
            
            # Format timestamp
            timestamp_str = ""
            if include_timestamp:
                timestamp_ms = int(metric.timestamp.timestamp() * 1000)
                timestamp_str = f" {timestamp_ms}"
            
            return f"{metric_name}{labels_str} {value_str}{timestamp_str}"
            
        except Exception as e:
            self.logger.error(f"Error formatting metric {metric_name}: {str(e)}")
            return ""
    
    def _infer_metric_type(self, metric_name: str, metrics: List[MetricValue]) -> str:
        """
        Infer Prometheus metric type from metric name and values.
        
        Returns: counter, gauge, histogram, or summary
        """
        # Check if explicitly set
        if metric_name in self._metric_types:
            return self._metric_types[metric_name]
        
        name_lower = metric_name.lower()
        
        # Counter indicators
        counter_indicators = [
            '_total', '_count', 'requests_', 'errors_', 'bytes_sent',
            'bytes_received', 'packets_', 'restarts_'
        ]
        
        if any(indicator in name_lower for indicator in counter_indicators):
            return "counter"
        
        # Histogram indicators
        histogram_indicators = ['_bucket', '_sum', '_count']
        if any(name_lower.endswith(indicator) for indicator in histogram_indicators):
            return "histogram"
        
        # Summary indicators
        if '_quantile' in name_lower or name_lower.endswith('_sum'):
            return "summary"
        
        # Default to gauge
        return "gauge"
    
    def _get_help_text(self, metric_name: str) -> str:
        """Get help text for a metric."""
        if metric_name in self._metric_help:
            return self._metric_help[metric_name]
        
        # Generate basic help text based on metric name
        name_parts = metric_name.replace('_', ' ').title()
        return f"{name_parts} metric"
    
    def set_metric_type(self, metric_name: str, metric_type: str) -> None:
        """Set explicit type for a metric."""
        valid_types = ["counter", "gauge", "histogram", "summary"]
        if metric_type not in valid_types:
            raise ValueError(f"Invalid metric type: {metric_type}")
        
        self._metric_types[metric_name] = metric_type
    
    def set_metric_help(self, metric_name: str, help_text: str) -> None:
        """Set help text for a metric."""
        self._metric_help[metric_name] = help_text
    
    def validate_prometheus_format(self, prometheus_text: str) -> List[str]:
        """
        Validate Prometheus format and return any issues found.
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        lines = prometheus_text.strip().split('\n')
        
        current_metric_family = None
        seen_metrics = set()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith('#'):
                # Handle comments
                if line.startswith('# TYPE '):
                    parts = line.split(' ', 3)
                    if len(parts) >= 3:
                        current_metric_family = parts[2]
                continue
            
            # Parse metric line
            try:
                # Basic format validation
                if ' ' not in line:
                    issues.append(f"Line {line_num}: Invalid format - missing value")
                    continue
                
                # Extract metric name (with labels)
                metric_part, value_part = line.rsplit(' ', 1)
                
                # Extract metric name
                if '{' in metric_part:
                    metric_name = metric_part.split('{')[0]
                else:
                    metric_name = metric_part
                
                # Validate metric name
                if not re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$', metric_name):
                    issues.append(f"Line {line_num}: Invalid metric name '{metric_name}'")
                
                # Validate value
                try:
                    if value_part not in ['+Inf', '-Inf', 'NaN']:
                        float(value_part)
                except ValueError:
                    issues.append(f"Line {line_num}: Invalid metric value '{value_part}'")
                
                # Check for duplicate metrics
                metric_key = metric_part
                if metric_key in seen_metrics:
                    issues.append(f"Line {line_num}: Duplicate metric '{metric_key}'")
                seen_metrics.add(metric_key)
                
            except Exception as e:
                issues.append(f"Line {line_num}: Parse error - {str(e)}")
        
        return issues
    
    def get_metric_families(self, prometheus_text: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse Prometheus text and extract metric families information.
        
        Returns:
            Dictionary with metric family information
        """
        families = {}
        lines = prometheus_text.strip().split('\n')
        
        current_family = None
        current_type = "gauge"
        current_help = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('# HELP '):
                parts = line.split(' ', 3)
                if len(parts) >= 3:
                    current_family = parts[2]
                    current_help = parts[3] if len(parts) > 3 else ""
                    
            elif line.startswith('# TYPE '):
                parts = line.split(' ', 3)
                if len(parts) >= 3:
                    current_family = parts[2]
                    current_type = parts[3] if len(parts) > 3 else "gauge"
                    
            elif line and not line.startswith('#'):
                # Metric sample line
                if '{' in line:
                    metric_name = line.split('{')[0]
                else:
                    metric_name = line.split(' ')[0]
                
                if metric_name not in families:
                    families[metric_name] = {
                        'type': current_type,
                        'help': current_help,
                        'samples': []
                    }
                
                families[metric_name]['samples'].append(line)
        
        return families