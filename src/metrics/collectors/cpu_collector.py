"""
CPU metrics collector for containers.
"""

import asyncio
import docker
import podman
from typing import List, Dict, Any
from datetime import datetime

from ..collector_interface import ContainerMetricsCollector
from ..models import MetricValue, MetricType, CollectorConfig


class CPUCollector(ContainerMetricsCollector):
    """Collector for CPU usage metrics from containers."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.docker_client = None
        self.podman_client = None
        self.runtime_type = None
    
    async def initialize(self) -> bool:
        """Initialize the CPU collector with container runtime clients."""
        try:
            # Try to connect to Docker first
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.runtime_type = "docker"
                self.logger.info("Connected to Docker daemon")
                return True
            except Exception as docker_error:
                self.logger.debug(f"Docker connection failed: {docker_error}")
            
            # Try Podman if Docker fails
            try:
                # Note: This is a simplified Podman connection
                # In practice, you might need to use podman-py or subprocess calls
                self.runtime_type = "podman"
                self.logger.info("Using Podman runtime")
                return True
            except Exception as podman_error:
                self.logger.debug(f"Podman connection failed: {podman_error}")
            
            self.logger.error("No container runtime available")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CPU collector: {str(e)}")
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
        return [MetricType.CPU_USAGE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect CPU metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects containing CPU metrics
        """
        if self.runtime_type == "docker":
            return await self._collect_docker_cpu_metrics(container_id)
        elif self.runtime_type == "podman":
            return await self._collect_podman_cpu_metrics(container_id)
        else:
            self.logger.error("No container runtime initialized")
            return []
    
    async def _collect_docker_cpu_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect CPU metrics from Docker container."""
        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU usage percentage
            cpu_usage = self._calculate_cpu_percentage(stats)
            
            # Get container metadata
            container_name = container.name
            image_name = container.image.tags[0] if container.image.tags else "unknown"
            
            # Create base labels
            labels = {
                "container_id": container_id,
                "container_name": container_name,
                "image": image_name,
                "runtime": "docker",
                **self.config.custom_labels
            }
            
            # Create metric value
            metric = MetricValue(
                name="container_cpu_usage_percent",
                value=cpu_usage,
                timestamp=datetime.now(),
                labels=labels,
                unit="percent"
            )
            
            return [metric]
            
        except Exception as e:
            self.logger.error(f"Failed to collect Docker CPU metrics for {container_id}: {str(e)}")
            return []
    
    async def _collect_podman_cpu_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect CPU metrics from Podman container."""
        try:
            # This is a simplified implementation
            # In practice, you would use podman stats command or API
            proc = await asyncio.create_subprocess_exec(
                'podman', 'stats', '--no-stream', '--format', 'json', container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                self.logger.error(f"Podman stats failed: {stderr.decode()}")
                return []
            
            import json
            stats_data = json.loads(stdout.decode())
            
            # Extract CPU usage (format may vary)
            cpu_usage = float(stats_data.get('CPU', '0%').rstrip('%'))
            
            # Get container info
            info_proc = await asyncio.create_subprocess_exec(
                'podman', 'inspect', container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            info_stdout, _ = await info_proc.communicate()
            container_info = json.loads(info_stdout.decode())[0]
            
            container_name = container_info['Name']
            image_name = container_info['Config']['Image']
            
            # Create base labels
            labels = {
                "container_id": container_id,
                "container_name": container_name,
                "image": image_name,
                "runtime": "podman",
                **self.config.custom_labels
            }
            
            # Create metric value
            metric = MetricValue(
                name="container_cpu_usage_percent",
                value=cpu_usage,
                timestamp=datetime.now(),
                labels=labels,
                unit="percent"
            )
            
            return [metric]
            
        except Exception as e:
            self.logger.error(f"Failed to collect Podman CPU metrics for {container_id}: {str(e)}")
            return []
    
    def _calculate_cpu_percentage(self, stats: Dict[str, Any]) -> float:
        """
        Calculate CPU usage percentage from Docker stats.
        
        Args:
            stats: Docker container stats dictionary
            
        Returns:
            CPU usage percentage
        """
        try:
            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']
            
            # Calculate CPU delta
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            # Calculate number of CPUs
            num_cpus = len(cpu_stats['cpu_usage']['percpu_usage'])
            
            # Calculate percentage
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
                return round(cpu_percent, 2)
            else:
                return 0.0
                
        except (KeyError, ZeroDivisionError, TypeError) as e:
            self.logger.warning(f"Error calculating CPU percentage: {str(e)}")
            return 0.0