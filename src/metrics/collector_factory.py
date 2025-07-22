"""
Factory for creating different types of metrics collectors.
"""

from typing import Dict, Type, Optional, Any
import logging

from .collector_interface import MetricsCollector, ContainerMetricsCollector, SystemMetricsCollector
from .models import CollectorConfig, MetricType


class CollectorFactory:
    """Factory class for creating metrics collectors."""
    
    def __init__(self):
        self._collector_types: Dict[str, Type[MetricsCollector]] = {}
        self.logger = logging.getLogger("collector.factory")
    
    def register_collector_type(self, collector_type: str, collector_class: Type[MetricsCollector]) -> None:
        """
        Register a collector type with the factory.
        
        Args:
            collector_type: String identifier for the collector type
            collector_class: The collector class to register
        """
        self._collector_types[collector_type] = collector_class
        self.logger.info(f"Registered collector type: {collector_type}")
    
    def create_collector(self, collector_type: str, config: CollectorConfig) -> Optional[MetricsCollector]:
        """
        Create a collector instance of the specified type.
        
        Args:
            collector_type: Type of collector to create
            config: Configuration for the collector
            
        Returns:
            Collector instance or None if type not found
        """
        if collector_type not in self._collector_types:
            self.logger.error(f"Unknown collector type: {collector_type}")
            return None
        
        try:
            collector_class = self._collector_types[collector_type]
            collector = collector_class(config)
            self.logger.info(f"Created collector: {config.name} of type {collector_type}")
            return collector
        except Exception as e:
            self.logger.error(f"Failed to create collector {config.name}: {str(e)}")
            return None
    
    def get_available_types(self) -> list[str]:
        """Get list of available collector types."""
        return list(self._collector_types.keys())
    
    def create_default_collectors(self) -> Dict[str, MetricsCollector]:
        """
        Create a set of default collectors with standard configurations.
        
        Returns:
            Dictionary mapping collector names to collector instances
        """
        collectors = {}
        
        # CPU collector
        cpu_config = CollectorConfig(
            name="cpu_collector",
            enabled=True,
            collection_interval=30,
            timeout=10
        )
        cpu_collector = self.create_collector("cpu", cpu_config)
        if cpu_collector:
            collectors["cpu_collector"] = cpu_collector
        
        # Memory collector
        memory_config = CollectorConfig(
            name="memory_collector",
            enabled=True,
            collection_interval=30,
            timeout=10
        )
        memory_collector = self.create_collector("memory", memory_config)
        if memory_collector:
            collectors["memory_collector"] = memory_collector
        
        # Network collector
        network_config = CollectorConfig(
            name="network_collector",
            enabled=True,
            collection_interval=60,
            timeout=15
        )
        network_collector = self.create_collector("network", network_collector)
        if network_collector:
            collectors["network_collector"] = network_collector
        
        # Disk collector
        disk_config = CollectorConfig(
            name="disk_collector",
            enabled=True,
            collection_interval=60,
            timeout=15
        )
        disk_collector = self.create_collector("disk", disk_config)
        if disk_collector:
            collectors["disk_collector"] = disk_collector
        
        # Container lifecycle collector
        lifecycle_config = CollectorConfig(
            name="lifecycle_collector",
            enabled=True,
            collection_interval=30,
            timeout=10
        )
        lifecycle_collector = self.create_collector("lifecycle", lifecycle_config)
        if lifecycle_collector:
            collectors["lifecycle_collector"] = lifecycle_collector
        
        # Container lifecycle metrics collector
        container_lifecycle_config = CollectorConfig(
            name="container_lifecycle_metrics",
            enabled=True,
            collection_interval=30,
            timeout=10,
            parameters={
                "restart_analysis_hours": 1,
                "uptime_tracking_days": 7,
                "max_history_size": 1000
            }
        )
        container_lifecycle_metrics = self.create_collector("container_lifecycle", container_lifecycle_config)
        if container_lifecycle_metrics:
            collectors["container_lifecycle_metrics"] = container_lifecycle_metrics
        
        return collectors


# Global factory instance
collector_factory = CollectorFactory()


def register_default_collectors():
    """Register default collector types with the factory."""
    # Import here to avoid circular imports
    from .collectors.cpu_collector import CPUCollector
    from .collectors.memory_collector import MemoryCollector
    from .collectors.network_collector import NetworkCollector
    from .collectors.disk_collector import DiskCollector
    from .lifecycle.lifecycle_collector import ContainerLifecycleCollector
    from .lifecycle.container_lifecycle_collector import ContainerLifecycleMetricsCollector
    
    collector_factory.register_collector_type("cpu", CPUCollector)
    collector_factory.register_collector_type("memory", MemoryCollector)
    collector_factory.register_collector_type("network", NetworkCollector)
    collector_factory.register_collector_type("disk", DiskCollector)
    collector_factory.register_collector_type("lifecycle", ContainerLifecycleCollector)
    collector_factory.register_collector_type("container_lifecycle", ContainerLifecycleMetricsCollector)


class CollectorBuilder:
    """Builder class for creating collectors with fluent interface."""
    
    def __init__(self, factory: CollectorFactory):
        self.factory = factory
        self.config = CollectorConfig(name="")
    
    def name(self, name: str) -> 'CollectorBuilder':
        """Set the collector name."""
        self.config.name = name
        return self
    
    def enabled(self, enabled: bool = True) -> 'CollectorBuilder':
        """Set whether the collector is enabled."""
        self.config.enabled = enabled
        return self
    
    def interval(self, seconds: int) -> 'CollectorBuilder':
        """Set the collection interval in seconds."""
        self.config.collection_interval = seconds
        return self
    
    def timeout(self, seconds: int) -> 'CollectorBuilder':
        """Set the collection timeout in seconds."""
        self.config.timeout = seconds
        return self
    
    def retry_attempts(self, attempts: int) -> 'CollectorBuilder':
        """Set the number of retry attempts."""
        self.config.retry_attempts = attempts
        return self
    
    def retry_delay(self, seconds: int) -> 'CollectorBuilder':
        """Set the delay between retry attempts."""
        self.config.retry_delay = seconds
        return self
    
    def custom_labels(self, labels: Dict[str, str]) -> 'CollectorBuilder':
        """Set custom labels for the collector."""
        self.config.custom_labels = labels
        return self
    
    def parameters(self, params: Dict[str, Any]) -> 'CollectorBuilder':
        """Set custom parameters for the collector."""
        self.config.parameters = params
        return self
    
    def build(self, collector_type: str) -> Optional[MetricsCollector]:
        """Build the collector with the specified type."""
        if not self.config.name:
            raise ValueError("Collector name is required")
        
        return self.factory.create_collector(collector_type, self.config)


def create_collector_builder(factory: CollectorFactory = None) -> CollectorBuilder:
    """Create a new collector builder instance."""
    if factory is None:
        factory = collector_factory
    return CollectorBuilder(factory)