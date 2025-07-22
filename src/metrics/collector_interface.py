"""
Base interface and abstract classes for metrics collectors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import MetricValue, CollectorConfig, CollectorStatus, MetricType


class MetricsCollector(ABC):
    """Abstract base class for all metrics collectors."""
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.logger = logging.getLogger(f"collector.{config.name}")
        self.status = CollectorStatus(
            name=config.name,
            enabled=config.enabled
        )
    
    @abstractmethod
    async def collect_metrics(self, target: Any) -> List[MetricValue]:
        """
        Collect metrics from the specified target.
        
        Args:
            target: The target to collect metrics from (e.g., container ID, service name)
            
        Returns:
            List of MetricValue objects
            
        Raises:
            CollectionError: If metrics collection fails
        """
        pass
    
    @abstractmethod
    def get_metric_types(self) -> List[MetricType]:
        """
        Get the types of metrics this collector can gather.
        
        Returns:
            List of MetricType enums
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the collector.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the collector."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if the collector is enabled."""
        return self.config.enabled and self.status.is_healthy
    
    def get_status(self) -> CollectorStatus:
        """Get the current status of the collector."""
        return self.status
    
    def update_config(self, config: CollectorConfig) -> None:
        """Update the collector configuration."""
        self.config = config
        self.status.enabled = config.enabled
    
    async def collect_with_error_handling(self, target: Any) -> List[MetricValue]:
        """
        Collect metrics with error handling and status tracking.
        
        Args:
            target: The target to collect metrics from
            
        Returns:
            List of MetricValue objects, empty list on error
        """
        if not self.is_enabled():
            return []
        
        try:
            metrics = await self.collect_metrics(target)
            self.status.last_collection_time = datetime.now()
            self.status.success_count += 1
            self.status.last_error = None
            self.status.is_healthy = True
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {str(e)}")
            self.status.error_count += 1
            self.status.last_error = str(e)
            
            # Mark as unhealthy if too many consecutive errors
            if self.status.error_count > 5:
                self.status.is_healthy = False
                
            return []


class ContainerMetricsCollector(MetricsCollector):
    """Base class for container-specific metrics collectors."""
    
    @abstractmethod
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects
        """
        pass
    
    async def collect_metrics(self, target: Any) -> List[MetricValue]:
        """Implementation of abstract method for container collectors."""
        if isinstance(target, str):
            return await self.collect_container_metrics(target)
        else:
            raise ValueError(f"Invalid target type for container collector: {type(target)}")


class SystemMetricsCollector(MetricsCollector):
    """Base class for system-wide metrics collectors."""
    
    @abstractmethod
    async def collect_system_metrics(self) -> List[MetricValue]:
        """
        Collect system-wide metrics.
        
        Returns:
            List of MetricValue objects
        """
        pass
    
    async def collect_metrics(self, target: Any = None) -> List[MetricValue]:
        """Implementation of abstract method for system collectors."""
        return await self.collect_system_metrics()


class CollectionError(Exception):
    """Exception raised when metrics collection fails."""
    
    def __init__(self, message: str, collector_name: str, target: Any = None):
        self.message = message
        self.collector_name = collector_name
        self.target = target
        super().__init__(f"Collection failed in {collector_name}: {message}")


class CollectorRegistry:
    """Registry for managing metrics collectors."""
    
    def __init__(self):
        self._collectors: Dict[str, MetricsCollector] = {}
        self.logger = logging.getLogger("collector.registry")
    
    def register_collector(self, collector: MetricsCollector) -> None:
        """
        Register a metrics collector.
        
        Args:
            collector: The collector to register
        """
        self._collectors[collector.config.name] = collector
        self.logger.info(f"Registered collector: {collector.config.name}")
    
    def unregister_collector(self, name: str) -> None:
        """
        Unregister a metrics collector.
        
        Args:
            name: Name of the collector to unregister
        """
        if name in self._collectors:
            del self._collectors[name]
            self.logger.info(f"Unregistered collector: {name}")
    
    def get_collector(self, name: str) -> Optional[MetricsCollector]:
        """
        Get a collector by name.
        
        Args:
            name: Name of the collector
            
        Returns:
            The collector instance or None if not found
        """
        return self._collectors.get(name)
    
    def get_all_collectors(self) -> Dict[str, MetricsCollector]:
        """Get all registered collectors."""
        return self._collectors.copy()
    
    def get_enabled_collectors(self) -> Dict[str, MetricsCollector]:
        """Get all enabled collectors."""
        return {
            name: collector 
            for name, collector in self._collectors.items() 
            if collector.is_enabled()
        }
    
    async def collect_all_metrics(self, target: Any = None) -> List[MetricValue]:
        """
        Collect metrics from all enabled collectors.
        
        Args:
            target: Optional target for collection
            
        Returns:
            List of all collected MetricValue objects
        """
        all_metrics = []
        enabled_collectors = self.get_enabled_collectors()
        
        for name, collector in enabled_collectors.items():
            try:
                metrics = await collector.collect_with_error_handling(target)
                all_metrics.extend(metrics)
            except Exception as e:
                self.logger.error(f"Error collecting from {name}: {str(e)}")
        
        return all_metrics
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all registered collectors.
        
        Returns:
            Dictionary mapping collector names to initialization success status
        """
        results = {}
        for name, collector in self._collectors.items():
            try:
                success = await collector.initialize()
                results[name] = success
                if success:
                    self.logger.info(f"Successfully initialized collector: {name}")
                else:
                    self.logger.warning(f"Failed to initialize collector: {name}")
            except Exception as e:
                self.logger.error(f"Error initializing collector {name}: {str(e)}")
                results[name] = False
        
        return results
    
    async def cleanup_all(self) -> None:
        """Clean up all registered collectors."""
        for name, collector in self._collectors.items():
            try:
                await collector.cleanup()
                self.logger.info(f"Cleaned up collector: {name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up collector {name}: {str(e)}")