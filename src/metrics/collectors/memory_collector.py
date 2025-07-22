"""
Memory metrics collector for containers.
"""

import asyncio
import docker
from typing import List, Dict, Any
from datetime import datetime

from ..collector_interface import ContainerMetricsCollector
from ..models import MetricValue, MetricType, CollectorConfig


class MemoryCollector(ContainerMetricsCollector):
    """Collector for memory usage metrics from containers."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.docker_client = None
        self.runtime_type = None
    
    async def initialize(self) -> bool:
        """Initialize the memory collector with container runtime clients."""
        try:
            # Try to connect to Docker first
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.runtime_type = "docker"
                self.logger.info("Memory collector connected to Docker daemon")
                return True
            except Exception as docker_error:
                self.logger.debug(f"Docker connection failed: {docker_error}")
            
            # Try Podman if Docker fails
            try:
                self.runtime_type = "podman"
                self.logger.info("Memory collector using Podman runtime")
                return True
            except Exception as podman_error:
                self.logger.debug(f"Podman connection failed: {podman_error}")
            
            self.logger.error("No container runtime available for memory collector")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory collector: {str(e)}")
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
        return [MetricType.MEMORY_USAGE]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect memory metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects containing memory metrics
        """
        if self.runtime_type == "docker":
            return await self._collect_docker_memory_metrics(container_id)
        elif self.runtime_type == "podman":
            return await self._collect_podman_memory_metrics(container_id)
        else:
            self.logger.error("No container runtime initialized")
            return []
    
    async def _collect_docker_memory_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect memory metrics from Docker container."""
        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Extract memory statistics
            memory_stats = stats['memory_stats']
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            
            # Calculate memory usage percentage
            memory_percent = 0.0
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100.0
            
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
            
            # Create metric values
            metrics = []
            
            # Memory usage in bytes
            metrics.append(MetricValue(
                name="container_memory_usage_bytes",
                value=memory_usage,
                timestamp=datetime.now(),
                labels=labels,
                unit="bytes"
            ))
            
            # Memory limit in bytes
            metrics.append(MetricValue(
                name="container_memory_limit_bytes",
                value=memory_limit,
                timestamp=datetime.now(),
                labels=labels,
                unit="bytes"
            ))
            
            # Memory usage percentage
            metrics.append(MetricValue(
                name="container_memory_usage_percent",
                value=round(memory_percent, 2),
                timestamp=datetime.now(),
                labels=labels,
                unit="percent"
            ))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Docker memory metrics for {container_id}: {str(e)}")
            return []
    
    async def _collect_podman_memory_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect memory metrics from Podman container."""
        try:
            # Get container stats
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
            
            # Extract memory usage (format may vary)
            memory_usage_str = stats_data.get('MemUsage', '0B / 0B')
            memory_usage, memory_limit = self._parse_memory_usage(memory_usage_str)
            
            # Calculate memory usage percentage
            memory_percent = 0.0
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100.0
            
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
            
            # Create metric values
            metrics = []
            
            # Memory usage in bytes
            metrics.append(MetricValue(
                name="container_memory_usage_bytes",
                value=memory_usage,
                timestamp=datetime.now(),
                labels=labels,
                unit="bytes"
            ))
            
            # Memory limit in bytes
            metrics.append(MetricValue(
                name="container_memory_limit_bytes",
                value=memory_limit,
                timestamp=datetime.now(),
                labels=labels,
                unit="bytes"
            ))
            
            # Memory usage percentage
            metrics.append(MetricValue(
                name="container_memory_usage_percent",
                value=round(memory_percent, 2),
                timestamp=datetime.now(),
                labels=labels,
                unit="percent"
            ))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Podman memory metrics for {container_id}: {str(e)}")
            return []
    
    def _parse_memory_usage(self, memory_str: str) -> tuple[int, int]:
        """
        Parse memory usage string from Podman stats.
        
        Args:
            memory_str: Memory usage string like "100MB / 2GB"
            
        Returns:
            Tuple of (usage_bytes, limit_bytes)
        """
        try:
            parts = memory_str.split(' / ')
            if len(parts) != 2:
                return 0, 0
            
            usage_bytes = self._parse_size_string(parts[0].strip())
            limit_bytes = self._parse_size_string(parts[1].strip())
            
            return usage_bytes, limit_bytes
            
        except Exception as e:
            self.logger.warning(f"Error parsing memory usage string '{memory_str}': {str(e)}")
            return 0, 0
    
    def _parse_size_string(self, size_str: str) -> int:
        """
        Parse size string like "100MB" to bytes.
        
        Args:
            size_str: Size string with unit
            
        Returns:
            Size in bytes
        """
        size_str = size_str.upper().strip()
        
        # Extract number and unit
        import re
        match = re.match(r'([0-9.]+)([A-Z]*)', size_str)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        # Convert to bytes
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
            'K': 1024,
            'M': 1024 ** 2,
            'G': 1024 ** 3,
            'T': 1024 ** 4
        }
        
        multiplier = multipliers.get(unit, 1)
        return int(number * multiplier)