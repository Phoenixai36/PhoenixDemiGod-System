"""
Prometheus metrics registry for managing metric collection and export.
"""

import logging
import threading
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ..models import MetricValue
from .formatter import PrometheusFormatter


class PrometheusRegistry:
    """Registry for managing Prometheus metrics collection and formatting."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.formatter = PrometheusFormatter()
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self._collectors: List[Callable[[], List[MetricValue]]] = []
        
        # Configuration
        self._max_metrics_per_name = 1000  # Prevent memory issues
        self._metric_ttl = timedelta(minutes=5)  # Auto-expire old metrics
        
        # Metadata
        self._metric_metadata: Dict[str, Dict[str, str]] = {}
        self._global_labels: Dict[str, str] = {}
        
        # Statistics
        self._collection_count = 0
        self._last_collection_time: Optional[datetime] = None
    
    def register_collector(self, collector: Callable[[], List[MetricValue]]) -> None:
        """
        Register a collector function that returns metrics.
        
        Args:
            collector: Function that returns list of MetricValue objects
        """
        with self._lock:
            self._collectors.append(collector)
            self.logger.info(f"Registered collector: {collector.__name__ if hasattr(collector, '__name__') else 'anonymous'}")
    
    def unregister_collector(self, collector: Callable[[], List[MetricValue]]) -> bool:
        """
        Unregister a collector function.
        
        Args:
            collector: Collector function to remove
            
        Returns:
            True if collector was found and removed
        """
        with self._lock:
            try:
                self._collectors.remove(collector)
                self.logger.info("Unregistered collector")
                return True
            except ValueError:
                return False
    
    def add_metric(self, metric: MetricValue) -> None:
        """Add a single metric to the registry."""
        with self._lock:
            # Add global labels if configured
            if self._global_labels:
                enhanced_labels = {**metric.labels, **self._global_labels}
                metric = MetricValue(
                    name=metric.name,
                    value=metric.value,
                    timestamp=metric.timestamp,
                    labels=enhanced_labels,
                    unit=metric.unit
                )
            
            # Add to storage
            self._metrics[metric.name].append(metric)
            
            # Enforce limits
            if len(self._metrics[metric.name]) > self._max_metrics_per_name:
                # Remove oldest metrics
                self._metrics[metric.name] = self._metrics[metric.name][-self._max_metrics_per_name:]
    
    def add_metrics(self, metrics: List[MetricValue]) -> None:
        """Add multiple metrics to the registry."""
        for metric in metrics:
            self.add_metric(metric)
    
    def collect_metrics(self) -> List[MetricValue]:
        """
        Collect all current metrics from registry and collectors.
        
        Returns:
            List of all current metrics
        """
        with self._lock:
            all_metrics = []
            
            # Collect from registered collectors
            for collector in self._collectors:
                try:
                    collector_metrics = collector()
                    if collector_metrics:
                        all_metrics.extend(collector_metrics)
                except Exception as e:
                    self.logger.error(f"Error collecting from collector: {str(e)}")
            
            # Add stored metrics (after cleaning expired ones)
            self._cleanup_expired_metrics()
            
            for metric_list in self._metrics.values():
                all_metrics.extend(metric_list)
            
            # Update statistics
            self._collection_count += 1
            self._last_collection_time = datetime.now()
            
            self.logger.debug(f"Collected {len(all_metrics)} metrics from {len(self._collectors)} collectors")
            
            return all_metrics
    
    def generate_prometheus_output(self, include_timestamp: bool = False,
                                 include_help: bool = True) -> str:
        """
        Generate Prometheus exposition format output.
        
        Args:
            include_timestamp: Whether to include timestamps
            include_help: Whether to include HELP and TYPE comments
            
        Returns:
            Prometheus formatted metrics string
        """
        metrics = self.collect_metrics()
        return self.formatter.format_metrics(
            metrics, 
            include_timestamp=include_timestamp,
            include_help=include_help
        )
    
    def set_global_labels(self, labels: Dict[str, str]) -> None:
        """Set global labels to be added to all metrics."""
        with self._lock:
            self._global_labels = labels.copy()
            self.logger.info(f"Set global labels: {labels}")
    
    def add_global_label(self, key: str, value: str) -> None:
        """Add a single global label."""
        with self._lock:
            self._global_labels[key] = value
    
    def remove_global_label(self, key: str) -> bool:
        """Remove a global label."""
        with self._lock:
            if key in self._global_labels:
                del self._global_labels[key]
                return True
            return False
    
    def set_metric_metadata(self, metric_name: str, metric_type: str, 
                          help_text: str) -> None:
        """
        Set metadata for a metric.
        
        Args:
            metric_name: Name of the metric
            metric_type: Prometheus metric type (counter, gauge, histogram, summary)
            help_text: Help text describing the metric
        """
        with self._lock:
            self._metric_metadata[metric_name] = {
                'type': metric_type,
                'help': help_text
            }
            
            # Update formatter
            self.formatter.set_metric_type(metric_name, metric_type)
            self.formatter.set_metric_help(metric_name, help_text)
    
    def get_metric_names(self) -> Set[str]:
        """Get all metric names currently in the registry."""
        with self._lock:
            # Get names from stored metrics
            stored_names = set(self._metrics.keys())
            
            # Get names from collectors (sample collection)
            try:
                sample_metrics = self.collect_metrics()
                collector_names = {m.name for m in sample_metrics}
                return stored_names.union(collector_names)
            except Exception as e:
                self.logger.error(f"Error getting metric names: {str(e)}")
                return stored_names
    
    def get_metric_count(self) -> int:
        """Get total number of metrics in registry."""
        with self._lock:
            return sum(len(metrics) for metrics in self._metrics.values())
    
    def clear_metrics(self, metric_name: Optional[str] = None) -> None:
        """
        Clear metrics from registry.
        
        Args:
            metric_name: Specific metric to clear, or None to clear all
        """
        with self._lock:
            if metric_name:
                if metric_name in self._metrics:
                    del self._metrics[metric_name]
                    self.logger.info(f"Cleared metrics for: {metric_name}")
            else:
                self._metrics.clear()
                self.logger.info("Cleared all metrics from registry")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry."""
        with self._lock:
            stats = {
                'total_metrics': self.get_metric_count(),
                'metric_families': len(self._metrics),
                'registered_collectors': len(self._collectors),
                'collection_count': self._collection_count,
                'last_collection_time': self._last_collection_time.isoformat() if self._last_collection_time else None,
                'global_labels': self._global_labels.copy(),
                'metric_metadata_count': len(self._metric_metadata)
            }
            
            # Add per-metric statistics
            metrics_stats = {}
            for name, metric_list in self._metrics.items():
                metrics_stats[name] = {
                    'count': len(metric_list),
                    'oldest': min(m.timestamp for m in metric_list).isoformat() if metric_list else None,
                    'newest': max(m.timestamp for m in metric_list).isoformat() if metric_list else None
                }
            
            stats['metrics_by_name'] = metrics_stats
            
            return stats
    
    def _cleanup_expired_metrics(self) -> None:
        """Remove expired metrics based on TTL."""
        if not self._metric_ttl:
            return
        
        cutoff_time = datetime.now() - self._metric_ttl
        expired_count = 0
        
        for metric_name in list(self._metrics.keys()):
            original_count = len(self._metrics[metric_name])
            
            # Filter out expired metrics
            self._metrics[metric_name] = [
                m for m in self._metrics[metric_name] 
                if m.timestamp >= cutoff_time
            ]
            
            expired_count += original_count - len(self._metrics[metric_name])
            
            # Remove empty metric families
            if not self._metrics[metric_name]:
                del self._metrics[metric_name]
        
        if expired_count > 0:
            self.logger.debug(f"Cleaned up {expired_count} expired metrics")
    
    def validate_output(self) -> List[str]:
        """
        Validate the current Prometheus output format.
        
        Returns:
            List of validation issues (empty if valid)
        """
        try:
            output = self.generate_prometheus_output()
            return self.formatter.validate_prometheus_format(output)
        except Exception as e:
            return [f"Error generating output: {str(e)}"]
    
    def export_to_file(self, file_path: str, include_timestamp: bool = False) -> bool:
        """
        Export current metrics to a file in Prometheus format.
        
        Args:
            file_path: Path to write the metrics file
            include_timestamp: Whether to include timestamps
            
        Returns:
            True if export successful
        """
        try:
            output = self.generate_prometheus_output(include_timestamp=include_timestamp)
            
            with open(file_path, 'w') as f:
                f.write(output)
            
            self.logger.info(f"Exported metrics to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to {file_path}: {str(e)}")
            return False
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the registry with settings.
        
        Args:
            config: Configuration dictionary
        """
        with self._lock:
            if 'max_metrics_per_name' in config:
                self._max_metrics_per_name = config['max_metrics_per_name']
            
            if 'metric_ttl_minutes' in config:
                self._metric_ttl = timedelta(minutes=config['metric_ttl_minutes'])
            
            if 'global_labels' in config:
                self.set_global_labels(config['global_labels'])
            
            self.logger.info(f"Registry configured with: {config}")


# Global registry instance
default_registry = PrometheusRegistry()