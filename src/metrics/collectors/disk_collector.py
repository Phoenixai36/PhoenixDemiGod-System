"""
Disk I/O metrics collector for containers.
"""

import asyncio
import docker
from typing import List, Dict, Any
from datetime import datetime

from ..collector_interface import ContainerMetricsCollector
from ..models import MetricValue, MetricType, CollectorConfig


class DiskCollector(ContainerMetricsCollector):
    """Collector for disk I/O metrics from containers."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.docker_client = None
        self.runtime_type = None
    
    async def initialize(self) -> bool:
        """Initialize the disk collector with container runtime clients."""
        try:
            # Try to connect to Docker first
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.runtime_type = "docker"
                self.logger.info("Disk collector connected to Docker daemon")
                return True
            except Exception as docker_error:
                self.logger.debug(f"Docker connection failed: {docker_error}")
            
            # Try Podman if Docker fails
            try:
                self.runtime_type = "podman"
                self.logger.info("Disk collector using Podman runtime")
                return True
            except Exception as podman_error:
                self.logger.debug(f"Podman connection failed: {podman_error}")
            
            self.logger.error("No container runtime available for disk collector")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize disk collector: {str(e)}")
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
        return [MetricType.DISK_IO]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect disk I/O metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects containing disk I/O metrics
        """
        if self.runtime_type == "docker":
            return await self._collect_docker_disk_metrics(container_id)
        elif self.runtime_type == "podman":
            return await self._collect_podman_disk_metrics(container_id)
        else:
            self.logger.error("No container runtime initialized")
            return []
    
    async def _collect_docker_disk_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect disk I/O metrics from Docker container."""
        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Extract block I/O statistics
            blkio_stats = stats.get('blkio_stats', {})
            
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
            
            metrics = []
            
            # Process read/write bytes
            io_service_bytes_recursive = blkio_stats.get('io_service_bytes_recursive', [])
            
            total_read_bytes = 0
            total_write_bytes = 0
            
            for entry in io_service_bytes_recursive:
                if entry.get('op') == 'Read':
                    total_read_bytes += entry.get('value', 0)
                elif entry.get('op') == 'Write':
                    total_write_bytes += entry.get('value', 0)
            
            # Create disk I/O metrics
            metrics.extend([
                MetricValue(
                    name="container_disk_read_bytes_total",
                    value=total_read_bytes,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="bytes"
                ),
                MetricValue(
                    name="container_disk_write_bytes_total",
                    value=total_write_bytes,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="bytes"
                )
            ])
            
            # Process read/write operations count
            io_serviced_recursive = blkio_stats.get('io_serviced_recursive', [])
            
            total_read_ops = 0
            total_write_ops = 0
            
            for entry in io_serviced_recursive:
                if entry.get('op') == 'Read':
                    total_read_ops += entry.get('value', 0)
                elif entry.get('op') == 'Write':
                    total_write_ops += entry.get('value', 0)
            
            # Create disk operation metrics
            metrics.extend([
                MetricValue(
                    name="container_disk_read_ops_total",
                    value=total_read_ops,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="operations"
                ),
                MetricValue(
                    name="container_disk_write_ops_total",
                    value=total_write_ops,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="operations"
                )
            ])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Docker disk metrics for {container_id}: {str(e)}")
            return []
    
    async def _collect_podman_disk_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect disk I/O metrics from Podman container."""
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
            
            # Extract block I/O (format may vary)
            block_io_str = stats_data.get('BlockIO', '0B / 0B')
            read_bytes, write_bytes = self._parse_block_io(block_io_str)
            
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
            metrics = [
                MetricValue(
                    name="container_disk_read_bytes_total",
                    value=read_bytes,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="bytes"
                ),
                MetricValue(
                    name="container_disk_write_bytes_total",
                    value=write_bytes,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="bytes"
                )
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Podman disk metrics for {container_id}: {str(e)}")
            return []
    
    def _parse_block_io(self, block_io_str: str) -> tuple[int, int]:
        """
        Parse block I/O string from Podman stats.
        
        Args:
            block_io_str: Block I/O string like "100MB / 50MB"
            
        Returns:
            Tuple of (read_bytes, write_bytes)
        """
        try:
            parts = block_io_str.split(' / ')
            if len(parts) != 2:
                return 0, 0
            
            read_bytes = self._parse_size_string(parts[0].strip())
            write_bytes = self._parse_size_string(parts[1].strip())
            
            return read_bytes, write_bytes
            
        except Exception as e:
            self.logger.warning(f"Error parsing block I/O string '{block_io_str}': {str(e)}")
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