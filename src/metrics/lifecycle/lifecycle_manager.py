"""
Lifecycle manager that coordinates event collection, restart tracking, and uptime tracking.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from ..models import MetricValue, CollectorConfig
from ..collector_interface import ContainerMetricsCollector, MetricType
from .event_collector import ContainerEventCollector, ContainerEvent
from .restart_tracker import RestartTracker, RestartPattern
from .uptime_tracker import UptimeTracker, UptimeStatistics


class LifecycleManager(ContainerMetricsCollector):
    """
    Comprehensive lifecycle manager that coordinates all lifecycle tracking.
    """
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        
        # Initialize sub-components
        self.event_collector = ContainerEventCollector(config)
        self.restart_tracker = RestartTracker(
            analysis_window=timedelta(hours=config.parameters.get('restart_analysis_hours', 1))
        )
        self.uptime_tracker = UptimeTracker(
            tracking_window=timedelta(days=config.parameters.get('uptime_tracking_days', 7))
        )
        
        # Callbacks for external notifications
        self.lifecycle_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Setup event forwarding
        self.event_collector.add_event_callback(self._handle_lifecycle_event)
        self.restart_tracker.add_restart_loop_callback(self._handle_restart_loop)
        self.uptime_tracker.add_uptime_callback(self._handle_uptime_session_end)
        
        # Cleanup task
        self._cleanup_task = None
        self._cleanup_interval = timedelta(hours=1)
    
    async def initialize(self) -> bool:
        """Initialize the lifecycle manager."""
        success = await self.event_collector.initialize()
        
        if success:
            # Start event listening
            await self.event_collector.start_listening()
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            self.logger.info("Lifecycle manager initialized successfully")
        
        return success
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup event collector
        await self.event_collector.cleanup()
        
        self.logger.info("Lifecycle manager cleaned up")
    
    def get_metric_types(self) -> List[MetricType]:
        """Get metric types this manager provides."""
        return [MetricType.CONTAINER_LIFECYCLE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect comprehensive lifecycle metrics for a container."""
        metrics = []
        
        try:
            # Get basic event metrics
            event_metrics = await self.event_collector.collect_container_metrics(container_id)
            metrics.extend(event_metrics)
            
            # Get restart metrics
            restart_pattern = self.restart_tracker.get_restart_pattern(container_id)
            if restart_pattern:
                metrics.extend(self._create_restart_metrics(restart_pattern))
            
            # Get uptime metrics
            uptime_stats = self.uptime_tracker.get_uptime_statistics(container_id)
            if uptime_stats:
                metrics.extend(self._create_uptime_metrics(uptime_stats))
            
            # Add current status metrics
            current_uptime = self.uptime_tracker.get_current_uptime(container_id)
            if current_uptime is not None:
                metrics.append(MetricValue(
                    name="container_current_uptime_seconds",
                    value=current_uptime,
                    timestamp=datetime.now(),
                    labels={
                        "container_id": container_id,
                        "status": "running"
                    },
                    unit="seconds"
                ))
            
        except Exception as e:
            self.logger.error(f"Error collecting lifecycle metrics for {container_id}: {str(e)}")
        
        return metrics
    
    def _create_restart_metrics(self, pattern: RestartPattern) -> List[MetricValue]:
        """Create metrics from restart pattern."""
        base_labels = {
            "container_id": pattern.container_id,
            "container_name": pattern.container_name,
            "severity": pattern.severity
        }
        
        metrics = [
            MetricValue(
                name="container_restart_count",
                value=pattern.restart_count,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="count"
            ),
            MetricValue(
                name="container_restart_rate_per_hour",
                value=pattern.restart_rate,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="rate"
            ),
            MetricValue(
                name="container_average_restart_interval_seconds",
                value=pattern.average_interval,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="seconds"
            ),
            MetricValue(
                name="container_is_restart_loop",
                value=1 if pattern.is_restart_loop else 0,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="boolean"
            )
        ]
        
        return metrics
    
    def _create_uptime_metrics(self, stats: UptimeStatistics) -> List[MetricValue]:
        """Create metrics from uptime statistics."""
        base_labels = {
            "container_id": stats.container_id,
            "container_name": stats.container_name,
            "availability_score": stats.availability_score
        }
        
        metrics = [
            MetricValue(
                name="container_total_uptime_seconds",
                value=stats.total_uptime_seconds,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="seconds"
            ),
            MetricValue(
                name="container_uptime_percentage",
                value=stats.uptime_percentage,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="percent"
            ),
            MetricValue(
                name="container_uptime_sessions_count",
                value=stats.uptime_sessions,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="count"
            ),
            MetricValue(
                name="container_average_session_duration_seconds",
                value=stats.average_session_duration,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="seconds"
            ),
            MetricValue(
                name="container_longest_session_duration_seconds",
                value=stats.longest_session_duration,
                timestamp=datetime.now(),
                labels=base_labels,
                unit="seconds"
            )
        ]
        
        return metrics
    
    def _handle_lifecycle_event(self, event: ContainerEvent) -> None:
        """Handle lifecycle events from event collector."""
        # Forward to trackers
        self.restart_tracker.add_event(event)
        self.uptime_tracker.add_event(event)
        
        # Notify external callbacks
        event_data = {
            "type": "lifecycle_event",
            "event_type": event.event_type.value,
            "container_id": event.container_id,
            "container_name": event.container_name,
            "timestamp": event.timestamp.isoformat(),
            "exit_code": event.exit_code,
            "signal": event.signal
        }
        
        self._notify_callbacks("lifecycle_event", event_data)
    
    def _handle_restart_loop(self, pattern: RestartPattern) -> None:
        """Handle restart loop detection."""
        loop_data = {
            "type": "restart_loop",
            "container_id": pattern.container_id,
            "container_name": pattern.container_name,
            "restart_count": pattern.restart_count,
            "time_window": str(pattern.time_window),
            "restart_rate": pattern.restart_rate,
            "severity": pattern.severity
        }
        
        self._notify_callbacks("restart_loop", loop_data)
    
    def _handle_uptime_session_end(self, session) -> None:
        """Handle uptime session end."""
        session_data = {
            "type": "uptime_session_end",
            "container_id": session.container_id,
            "container_name": session.container_name,
            "uptime_seconds": session.uptime_seconds,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None
        }
        
        self._notify_callbacks("uptime_session_end", session_data)
    
    def _notify_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify registered callbacks."""
        for callback in self.lifecycle_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self.logger.error(f"Error in lifecycle callback: {str(e)}")
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old data."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval.total_seconds())
                
                self.logger.debug("Running periodic lifecycle data cleanup")
                self.restart_tracker.cleanup_old_data()
                self.uptime_tracker.cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {str(e)}")
    
    # Public API methods
    
    def add_lifecycle_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for lifecycle events."""
        self.lifecycle_callbacks.append(callback)
    
    def remove_lifecycle_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Remove lifecycle callback."""
        if callback in self.lifecycle_callbacks:
            self.lifecycle_callbacks.remove(callback)
    
    def get_container_restart_pattern(self, container_id: str) -> Optional[RestartPattern]:
        """Get restart pattern for a container."""
        return self.restart_tracker.get_restart_pattern(container_id)
    
    def get_container_uptime_statistics(self, container_id: str) -> Optional[UptimeStatistics]:
        """Get uptime statistics for a container."""
        return self.uptime_tracker.get_uptime_statistics(container_id)
    
    def get_restart_loops(self) -> List[RestartPattern]:
        """Get all containers currently in restart loops."""
        return self.restart_tracker.get_restart_loops()
    
    def get_running_containers(self) -> List:
        """Get all currently running containers."""
        return self.uptime_tracker.get_all_running_containers()
    
    def get_recent_events(self, container_id: Optional[str] = None, limit: int = 100) -> List[ContainerEvent]:
        """Get recent lifecycle events."""
        return self.event_collector.get_recent_events(container_id=container_id, limit=limit)
    
    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Get comprehensive lifecycle summary."""
        return {
            "events": self.event_collector.get_event_statistics(),
            "restarts": self.restart_tracker.get_restart_statistics(),
            "uptime": self.uptime_tracker.get_uptime_summary(),
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_container_health(self, container_id: str) -> Dict[str, Any]:
        """Analyze overall health of a container based on lifecycle data."""
        analysis = {
            "container_id": container_id,
            "health_score": 100,  # Start with perfect score
            "issues": [],
            "recommendations": []
        }
        
        # Check restart patterns
        restart_pattern = self.restart_tracker.get_restart_pattern(container_id)
        if restart_pattern:
            if restart_pattern.is_restart_loop:
                analysis["health_score"] -= 50
                analysis["issues"].append("Container is in a restart loop")
                analysis["recommendations"].append("Investigate application logs and configuration")
            elif restart_pattern.restart_count > 5:
                analysis["health_score"] -= 20
                analysis["issues"].append("High restart count")
                analysis["recommendations"].append("Monitor for stability issues")
        
        # Check uptime statistics
        uptime_stats = self.uptime_tracker.get_uptime_statistics(container_id)
        if uptime_stats:
            if uptime_stats.uptime_percentage < 95:
                analysis["health_score"] -= 30
                analysis["issues"].append(f"Low uptime: {uptime_stats.uptime_percentage:.1f}%")
                analysis["recommendations"].append("Improve application reliability")
            elif uptime_stats.uptime_percentage < 99:
                analysis["health_score"] -= 10
                analysis["issues"].append(f"Moderate uptime: {uptime_stats.uptime_percentage:.1f}%")
        
        # Determine overall health status
        if analysis["health_score"] >= 90:
            analysis["status"] = "healthy"
        elif analysis["health_score"] >= 70:
            analysis["status"] = "warning"
        else:
            analysis["status"] = "critical"
        
        return analysis