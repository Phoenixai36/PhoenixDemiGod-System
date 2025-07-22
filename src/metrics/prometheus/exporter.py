"""
Main Prometheus exporter that integrates all components.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta

from ..models import MetricValue
from ..storage import StorageManager
from .registry import PrometheusRegistry, default_registry
from .scrape_endpoint import ScrapeEndpoint, SimpleScrapeEndpoint


class PrometheusExporter:
    """
    Main Prometheus exporter that coordinates metrics collection and export.
    """
    
    def __init__(self, 
                 storage_manager: Optional[StorageManager] = None,
                 registry: Optional[PrometheusRegistry] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.storage_manager = storage_manager
        self.registry = registry or default_registry
        self.config = config or {}
        
        # Components
        self.scrape_endpoint: Optional[ScrapeEndpoint] = None
        self.simple_endpoint: Optional[SimpleScrapeEndpoint] = None
        
        # Background tasks
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Configuration
        self.collection_interval = timedelta(seconds=self.config.get('collection_interval', 15))
        self.enable_http_endpoint = self.config.get('enable_http_endpoint', True)
        self.http_host = self.config.get('http_host', '0.0.0.0')
        self.http_port = self.config.get('http_port', 8080)
        
        # Setup default metric metadata
        self._setup_default_metadata()
        
        self.logger.info("Prometheus exporter initialized")
    
    async def initialize(self) -> bool:
        """Initialize the Prometheus exporter."""
        try:
            # Setup HTTP endpoint if enabled
            if self.enable_http_endpoint:
                try:
                    self.scrape_endpoint = ScrapeEndpoint(
                        registry=self.registry,
                        host=self.http_host,
                        port=self.http_port
                    )
                    
                    # Configure endpoint
                    endpoint_config = {
                        'include_timestamp': self.config.get('include_timestamp', False),
                        'include_help': self.config.get('include_help', True),
                        'custom_headers': self.config.get('custom_headers', {})
                    }
                    self.scrape_endpoint.configure(endpoint_config)
                    
                except ImportError:
                    self.logger.warning("aiohttp not available, using simple endpoint")
                    self.simple_endpoint = SimpleScrapeEndpoint(self.registry)
            
            # Configure registry
            registry_config = {
                'max_metrics_per_name': self.config.get('max_metrics_per_name', 1000),
                'metric_ttl_minutes': self.config.get('metric_ttl_minutes', 5),
                'global_labels': self.config.get('global_labels', {})
            }
            self.registry.configure(registry_config)
            
            # Register storage collector if available
            if self.storage_manager:
                self.registry.register_collector(self._collect_from_storage)
            
            self.logger.info("Prometheus exporter initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Prometheus exporter: {str(e)}")
            return False
    
    async def start(self) -> bool:
        """Start the Prometheus exporter."""
        try:
            # Start HTTP endpoint
            if self.scrape_endpoint:
                success = await self.scrape_endpoint.start()
                if not success:
                    return False
            
            # Start background collection
            if self.storage_manager and self.collection_interval:
                self._running = True
                self._collection_task = asyncio.create_task(self._collection_loop())
            
            self.logger.info("Prometheus exporter started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus exporter: {str(e)}")
            return False
    
    async def stop(self) -> None:
        """Stop the Prometheus exporter."""
        try:
            # Stop background collection
            self._running = False
            if self._collection_task:
                self._collection_task.cancel()
                try:
                    await self._collection_task
                except asyncio.CancelledError:
                    pass
                self._collection_task = None
            
            # Stop HTTP endpoint
            if self.scrape_endpoint:
                await self.scrape_endpoint.stop()
            
            self.logger.info("Prometheus exporter stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Prometheus exporter: {str(e)}")
    
    def add_metric(self, metric: MetricValue) -> None:
        """Add a single metric to the registry."""
        self.registry.add_metric(metric)
    
    def add_metrics(self, metrics: List[MetricValue]) -> None:
        """Add multiple metrics to the registry."""
        self.registry.add_metrics(metrics)
    
    def register_collector(self, collector: Callable[[], List[MetricValue]]) -> None:
        """Register a custom metrics collector."""
        self.registry.register_collector(collector)
    
    def set_metric_metadata(self, metric_name: str, metric_type: str, help_text: str) -> None:
        """Set metadata for a metric."""
        self.registry.set_metric_metadata(metric_name, metric_type, help_text)
    
    def get_metrics_text(self, include_timestamp: bool = False,
                        include_help: bool = True) -> str:
        """Get current metrics in Prometheus text format."""
        return self.registry.generate_prometheus_output(
            include_timestamp=include_timestamp,
            include_help=include_help
        )
    
    def export_to_file(self, file_path: str, include_timestamp: bool = False) -> bool:
        """Export current metrics to a file."""
        return self.registry.export_to_file(file_path, include_timestamp)
    
    def get_exporter_stats(self) -> Dict[str, Any]:
        """Get comprehensive exporter statistics."""
        stats = {
            'exporter': {
                'running': self._running,
                'collection_interval_seconds': self.collection_interval.total_seconds(),
                'http_endpoint_enabled': self.enable_http_endpoint,
                'http_host': self.http_host,
                'http_port': self.http_port,
                'storage_manager_connected': self.storage_manager is not None
            },
            'registry': self.registry.get_registry_stats()
        }
        
        # Add endpoint stats if available
        if self.scrape_endpoint:
            stats['endpoint'] = {
                'scrape_count': self.scrape_endpoint.scrape_count,
                'error_count': self.scrape_endpoint.error_count,
                'last_scrape_time': self.scrape_endpoint.last_scrape_time.isoformat() if self.scrape_endpoint.last_scrape_time else None
            }
        
        return stats
    
    def validate_metrics(self) -> List[str]:
        """Validate current metrics format."""
        return self.registry.validate_output()
    
    async def _collection_loop(self) -> None:
        """Background loop for collecting metrics from storage."""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval.total_seconds())
                
                if self._running and self.storage_manager:
                    # This will trigger the collector we registered
                    self.registry.collect_metrics()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in collection loop: {str(e)}")
    
    def _collect_from_storage(self) -> List[MetricValue]:
        """Collect recent metrics from storage manager."""
        if not self.storage_manager:
            return []
        
        try:
            from ..storage.query_interface import QueryFilter, TimeRange
            
            # Get recent metrics (last 5 minutes)
            filters = QueryFilter(
                time_range=TimeRange.LAST_HOUR,  # Use last hour to ensure we have data
                limit=1000  # Limit to prevent memory issues
            )
            
            metrics = self.storage_manager.query_metrics(filters)
            
            # Filter to only recent metrics (last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
            self.logger.debug(f"Collected {len(recent_metrics)} recent metrics from storage")
            return recent_metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting from storage: {str(e)}")
            return []
    
    def _setup_default_metadata(self) -> None:
        """Setup default metadata for common metrics."""
        default_metadata = [
            # Container resource metrics
            ("container_cpu_usage_percent", "gauge", "CPU usage percentage for container"),
            ("container_memory_usage_bytes", "gauge", "Memory usage in bytes for container"),
            ("container_memory_limit_bytes", "gauge", "Memory limit in bytes for container"),
            ("container_memory_usage_percent", "gauge", "Memory usage percentage for container"),
            
            # Network metrics
            ("container_network_receive_bytes_total", "counter", "Total bytes received by container"),
            ("container_network_transmit_bytes_total", "counter", "Total bytes transmitted by container"),
            ("container_network_receive_packets_total", "counter", "Total packets received by container"),
            ("container_network_transmit_packets_total", "counter", "Total packets transmitted by container"),
            
            # Disk I/O metrics
            ("container_disk_read_bytes_total", "counter", "Total bytes read from disk by container"),
            ("container_disk_write_bytes_total", "counter", "Total bytes written to disk by container"),
            ("container_disk_read_ops_total", "counter", "Total disk read operations by container"),
            ("container_disk_write_ops_total", "counter", "Total disk write operations by container"),
            
            # Lifecycle metrics
            ("container_uptime_seconds", "gauge", "Container uptime in seconds"),
            ("container_restarts_total", "counter", "Total number of container restarts"),
            ("container_lifecycle_event", "counter", "Container lifecycle events"),
            ("container_restart_count", "gauge", "Current restart count for container"),
            ("container_restart_rate_per_hour", "gauge", "Container restart rate per hour"),
            ("container_is_restart_loop", "gauge", "Whether container is in restart loop (1=yes, 0=no)"),
            ("container_uptime_percentage", "gauge", "Container uptime percentage"),
            ("container_uptime_sessions_count", "gauge", "Number of uptime sessions for container"),
            
            # System metrics
            ("system_health_score", "gauge", "Overall system health score"),
            ("system_containers_total", "gauge", "Total number of containers"),
            ("system_containers_running", "gauge", "Number of running containers"),
            ("system_containers_failed", "gauge", "Number of failed containers"),
        ]
        
        for metric_name, metric_type, help_text in default_metadata:
            self.registry.set_metric_metadata(metric_name, metric_type, help_text)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()