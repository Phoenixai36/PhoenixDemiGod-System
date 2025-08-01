"""
Container lifecycle metrics collector.
"""

import asyncio
import docker
from typing import List, Dict, Any
from datetime import datetime, timezone

from ..collector_interface import ContainerMetricsCollector
from ..models import MetricValue, MetricType, CollectorConfig


class LifecycleCollector(ContainerMetricsCollector):
    """Collector for container lifecycle metrics (restarts, uptime, status)."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.docker_client = None
        self.runtime_type = None
    
    async def initialize(self) -> bool:
        """Initialize the lifecycle collector with container runtime clients."""
        try:
            # Try to connect to Docker first
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.runtime_type = "docker"
                self.logger.info("Lifecycle collector connected to Docker daemon")
                return True
            except Exception as docker_error:
                self.logger.debug(f"Docker connection failed: {docker_error}")
            
            # Try Podman if Docker fails
            try:
                self.runtime_type = "podman"
                self.logger.info("Lifecycle collector using Podman runtime")
                return True
            except Exception as podman_error:
                self.logger.debug(f"Podman connection failed: {podman_error}")
            
            self.logger.error("No container runtime available for lifecycle collector")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize lifecycle collector: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.docker_client:
            try:
                self.docker_client.close()
            except Exception as e:
                self.logger.error(f"Error closing Docker client: {str(e)}")
    
    def get_metric_types(self) -> List[MetricType]:
        """Get the metric types this collector provides."""
        return [MetricType.CONTAINER_LIFECYCLE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect lifecycle metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects containing lifecycle metrics
        """
        if self.runtime_type == "docker":
            return await self._collect_docker_lifecycle_metrics(container_id)
        elif self.runtime_type == "podman":
            return await self._collect_podman_lifecycle_metrics(container_id)
        else:
            self.logger.error("No container runtime initialized")
            return []
    
    async def _collect_docker_lifecycle_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect lifecycle metrics from Docker container."""
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Get container metadata
            container_name = container.name
            image_name = container.image.tags[0] if container.image.tags else "unknown"
            
            # Get container status and state
            container.reload()  # Refresh container state
            status = container.status
            state = container.attrs.get('State', {})
            
            # Calculate uptime
            started_at_str = state.get('StartedAt')
            uptime_seconds = 0
            if started_at_str and started_at_str != '0001-01-01T00:00:00Z':
                try:
                    # Parse the timestamp
                    started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    uptime_seconds = (current_time - started_at).total_seconds()
                except Exception as e:
                    self.logger.warning(f"Error calculating uptime: {str(e)}")
            
            # Get restart count
            restart_count = state.get('RestartCount', 0)
            
            # Get exit code (if container has exited)
            exit_code = state.get('ExitCode', 0)
            
            # Create base labels
            labels = {
                "container_id": container_id,
                "container_name": container_name,
                "image": image_name,
                "status": status,
                "runtime": "docker",
                **self.config.custom_labels
            }
            
            # Create metric values
            metrics = []
            
            # Container uptime
            metrics.append(MetricValue(
                name="container_uptime_seconds",
                value=max(0, uptime_seconds),
                timestamp=datetime.now(),
                labels=labels,
                unit="seconds"
            ))
            
            # Container restart count
            metrics.append(MetricValue(
                name="container_restarts_total",
                value=restart_count,
                timestamp=datetime.now(),
                labels=labels,
                unit="count"
            ))
            
            # Container status as numeric value (for easier alerting)
            status_value = self._status_to_numeric(status)
            metrics.append(MetricValue(
                name="container_status",
                value=status_value,
                timestamp=datetime.now(),
                labels=labels,
                unit="status"
            ))
            
            # Exit code (useful for debugging failed containers)
            if status in ['exited', 'dead']:
                metrics.append(MetricValue(
                    name="container_exit_code",
                    value=exit_code,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="code"
                ))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Docker lifecycle metrics for {container_id}: {str(e)}")
            return []
    
    async def _collect_podman_lifecycle_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect lifecycle metrics from Podman container."""
        try:
            # Get container info
            info_proc = await asyncio.create_subprocess_exec(
                'podman', 'inspect', container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            info_stdout, info_stderr = await info_proc.communicate()
            
            if info_proc.returncode != 0:
                self.logger.error(f"Podman inspect failed: {info_stderr.decode()}")
                return []
            
            import json
            container_info = json.loads(info_stdout.decode())[0]
            
            container_name = container_info['Name']
            image_name = container_info['Config']['Image']
            state = container_info.get('State', {})
            status = state.get('Status', 'unknown')
            
            # Calculate uptime
            started_at_str = state.get('StartedAt')
            uptime_seconds = 0
            if started_at_str and started_at_str != '0001-01-01T00:00:00Z':
                try:
                    started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    uptime_seconds = (current_time - started_at).total_seconds()
                except Exception as e:
                    self.logger.warning(f"Error calculating uptime: {str(e)}")
            
            # Get restart count (may not be available in all Podman versions)
            restart_count = state.get('RestartCount', 0)
            
            # Get exit code
            exit_code = state.get('ExitCode', 0)
            
            # Create base labels
            labels = {
                "container_id": container_id,
                "container_name": container_name,
                "image": image_name,
                "status": status,
                "runtime": "podman",
                **self.config.custom_labels
            }
            
            # Create metric values
            metrics = []
            
            # Container uptime
            metrics.append(MetricValue(
                name="container_uptime_seconds",
                value=max(0, uptime_seconds),
                timestamp=datetime.now(),
                labels=labels,
                unit="seconds"
            ))
            
            # Container restart count
            metrics.append(MetricValue(
                name="container_restarts_total",
                value=restart_count,
                timestamp=datetime.now(),
                labels=labels,
                unit="count"
            ))
            
            # Container status as numeric value
            status_value = self._status_to_numeric(status)
            metrics.append(MetricValue(
                name="container_status",
                value=status_value,
                timestamp=datetime.now(),
                labels=labels,
                unit="status"
            ))
            
            # Exit code (useful for debugging failed containers)
            if status in ['exited', 'dead', 'stopped']:
                metrics.append(MetricValue(
                    name="container_exit_code",
                    value=exit_code,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="code"
                ))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Podman lifecycle metrics for {container_id}: {str(e)}")
            return []
    
    def _status_to_numeric(self, status: str) -> int:
        """
        Convert container status to numeric value for easier monitoring.
        
        Args:
            status: Container status string
            
        Returns:
            Numeric representation of status
        """
        status_map = {
            'running': 1,
            'created': 0,
            'restarting': 2,
            'removing': 3,
            'paused': 4,
            'exited': 5,
            'dead': 6,
            'stopped': 5,  # Podman equivalent of exited
            'unknown': -1
        }
        
        return status_map.get(status.lower(), -1)