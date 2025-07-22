"""
Metrics collection framework for container monitoring.
"""

from .models import (
    MetricType,
    MetricValue,
    ContainerMetrics,
    CollectorConfig,
    CollectorStatus
)

from .collector_interface import (
    MetricsCollector,
    ContainerMetricsCollector,
    SystemMetricsCollector,
    CollectionError,
    CollectorRegistry
)

from .collector_factory import (
    CollectorFactory,
    collector_factory,
    register_default_collectors,
    CollectorBuilder,
    create_collector_builder
)

from .collectors import (
    CPUCollector,
    MemoryCollector,
    NetworkCollector,
    DiskCollector,
    LifecycleCollector
)

from .config_loader import (
    ConfigLoader,
    get_config_loader,
    load_collector_configs
)

from .lifecycle import (
    ContainerEventCollector,
    RestartTracker,
    UptimeTracker,
    LifecycleManager
)

from .storage import (
    RetentionPolicy,
    TimeSeriesStorage,
    InMemoryTimeSeriesStorage,
    QueryEngine
)

from .prometheus import (
    PrometheusExporter,
    PrometheusFormatter,
    ScrapeEndpoint,
    PrometheusRegistry
)

from .api import (
    create_metrics_router,
    MetricResponse,
    MetricsQueryParams,
    StorageStatsResponse
)

__all__ = [
    # Models
    'MetricType',
    'MetricValue',
    'ContainerMetrics',
    'CollectorConfig',
    'CollectorStatus',
    
    # Interfaces
    'MetricsCollector',
    'ContainerMetricsCollector',
    'SystemMetricsCollector',
    'CollectionError',
    'CollectorRegistry',
    
    # Factory
    'CollectorFactory',
    'collector_factory',
    'register_default_collectors',
    'CollectorBuilder',
    'create_collector_builder',
    
    # Collectors
    'CPUCollector',
    'MemoryCollector',
    'NetworkCollector',
    'DiskCollector',
    'LifecycleCollector',
    
    # Configuration
    'ConfigLoader',
    'get_config_loader',
    'load_collector_configs',
    
    # Lifecycle
    'ContainerEventCollector',
    'RestartTracker',
    'UptimeTracker',
    'LifecycleManager',
    
    # Storage
    'RetentionPolicy',
    'TimeSeriesStorage',
    'InMemoryTimeSeriesStorage',
    'QueryEngine',
    
    # Prometheus
    'PrometheusExporter',
    'PrometheusFormatter',
    'ScrapeEndpoint',
    'PrometheusRegistry',
    
    # API
    'create_metrics_router',
    'MetricResponse',
    'MetricsQueryParams',
    'StorageStatsResponse'
]

# Initialize default collectors when module is imported
register_default_collectors()