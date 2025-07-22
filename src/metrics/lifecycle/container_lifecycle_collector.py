"""
Container lifecycle metrics collector.

This module integrates the event collector, restart tracker, and uptime tracker
to provide comprehensive container lifecycle metrics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..models import MetricValue, CollectorConfig, MetricType
from ..collector_interface import ContainerMetricsCollector
from .event_collector import ContainerEventCollector, ContainerEvent, ContainerEventType
from .restart_tracker import RestartTracker
from .uptime_tracker import UptimeTracker
from .lifecycle_manager import LifecycleManager


class ContainerLifecycleMetricsCollector(ContainerMetricsCollector):
    """
    Collector for container lifecycle metrics including start/stop events,
    restart counts, and uptime tracking.
    """
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Create lifecycle manager which integrates all components
        self.lifecycle_manager = LifecycleManager(config)
        
        # Track containers we've seen
        self.known_containers = set()
    
    async def initialize(self) -> bool:
        """Initialize the collector."""
        try:
            # Initialize the lifecycle manager
            success = await self.lifecycle_manager.initialize()
            
            if success:
                self.logger.info("Container lifecycle metrics collector initialized successfully")
                
                # Register callback to track containers
                self.lifecycle_manager.add_lifecycle_callback(self._handle_lifecycle_event)
            else:
                self.logger.error("Failed to initialize lifecycle manager")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to initialize container lifecycle metrics collector: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Remove callback
            self.lifecycle_manager.remove_lifecycle_callback(self._handle_lifecycle_event)
            
            # Clean up lifecycle manager
            await self.lifecycle_manager.cleanup()
            
            self.logger.info("Container lifecycle metrics collector cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up container lifecycle metrics collector: {str(e)}")
    
    def get_metric_types(self) -> List[MetricType]:
        """Get the types of metrics this collector can gather."""
        return [MetricType.CONTAINER_LIFECYCLE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect lifecycle metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects
        """
        try:
            # Get metrics from lifecycle manager
            metrics = await self.lifecycle_manager.collect_container_metrics(container_id)
            
            # Add container to known containers
            self.known_containers.add(container_id)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting lifecycle metrics for container {container_id}: {str(e)}")
            return []
    
    def _handle_lifecycle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle lifecycle events to track containers."""
        if event_type == "lifecycle_event" and "container_id" in data:
            self.known_containers.add(data["container_id"])
    
    # Additional methods for accessing lifecycle data
    
    def get_container_restart_pattern(self, container_id: str):
        """Get restart pattern for a container."""
        return self.lifecycle_manager.get_container_restart_pattern(container_id)
    
    def get_container_uptime_statistics(self, container_id: str):
        """Get uptime statistics for a container."""
        return self.lifecycle_manager.get_container_uptime_statistics(container_id)
    
    def get_restart_loops(self):
        """Get all containers currently in restart loops."""
        return self.lifecycle_manager.get_restart_loops()
    
    def get_running_containers(self):
        """Get all currently running containers."""
        return self.lifecycle_manager.get_running_containers()
    
    def get_recent_events(self, container_id=None, limit=100):
        """Get recent lifecycle events."""
        return self.lifecycle_manager.get_recent_events(container_id, limit)
    
    def get_lifecycle_summary(self):
        """Get comprehensive lifecycle summary."""
        return self.lifecycle_manager.get_lifecycle_summary()
    
    def analyze_container_health(self, container_id: str):
        """Analyze overall health of a container based on lifecycle data."""
        return self.lifecycle_manager.analyze_container_health(container_id)