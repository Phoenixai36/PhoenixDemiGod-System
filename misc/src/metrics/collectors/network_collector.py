"""
Network metrics collector for containers.
"""

import asyncio
import docker
from typing import List, Dict, Any
from datetime import datetime

from ..collector_interface import ContainerMetricsCollector
from ..models import MetricValue, MetricType, CollectorConfig


class NetworkCollector(ContainerMetricsCollector):
    """Collector for network I/O metrics from containers."""
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.docker_client = None
        self.runtime_type = None
    
    async def initialize(self) -> bool:
        """Initialize the network collector with container runtime clients."""
        try:
            # Try to connect to Docker first
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                self.runtime_type = "docker"
                self.logger.info("Network collector connected to Docker daemon")
                return True
            except Exception as docker_error:
                self.logger.debug(f"Docker connection failed: {docker_error}")
            
            # Try Podman if Docker fails
            try:
                self.runtime_type = "podman"
                self.logger.info("Network collector using Podman runtime")
                return True
            except Exception as podman_error:
                self.logger.debug(f"Podman connection failed: {podman_error}")
            
            self.logger.error("No container runtime available for network collector")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize network collector: {str(e)}")
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
        return [MetricType.NETWORK_IO]
    
    async def collect_container_metrics(self, container_id: str) -> List[MetricValue]:
        """
        Collect network metrics for a specific container.
        
        Args:
            container_id: The container ID to collect metrics for
            
        Returns:
            List of MetricValue objects containing network metrics
        """
        if self.runtime_type == "docker":
            return await self._collect_docker_network_metrics(container_id)
        elif self.runtime_type == "podman":
            return await self._collect_podman_network_metrics(container_id)
        else:
            self.logger.error("No container runtime initialized")
            return []
    
    async def _collect_docker_network_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect network metrics from Docker container."""
        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Extract network statistics
            networks = stats.get('networks', {})
            
            # Get container metadata
            container_name = container.name
            image_name = container.image.tags[0] if container.image.tags else "unknown"
            
            metrics = []
            
            # Aggregate network stats across all interfaces
            total_rx_bytes = 0
            total_tx_bytes = 0
            total_rx_packets = 0
            total_tx_packets = 0
            
            for interface_name, interface_stats in networks.items():
                rx_bytes = interface_stats.get('rx_bytes', 0)
                tx_bytes = interface_stats.get('tx_bytes', 0)
                rx_packets = interface_stats.get('rx_packets', 0)
                tx_packets = interface_stats.get('tx_packets', 0)
                
                total_rx_bytes += rx_bytes
                total_tx_bytes += tx_bytes
                total_rx_packets += rx_packets
                total_tx_packets += tx_packets
                
                # Create per-interface metrics
                interface_labels = {
                    "container_id": container_id,
                    "container_name": container_name,
                    "image": image_name,
                    "interface": interface_name,
                    "runtime": "docker",
                    **self.config.custom_labels
                }
                
                metrics.extend([
                    MetricValue(
                        name="container_network_receive_bytes_total",
                        value=rx_bytes,
                        timestamp=datetime.now(),
                        labels=interface_labels,
                        unit="bytes"
                    ),
                    MetricValue(
                        name="container_network_transmit_bytes_total",
                        value=tx_bytes,
                        timestamp=datetime.now(),
                        labels=interface_labels,
                        unit="bytes"
                    ),
                    MetricValue(
                        name="container_network_receive_packets_total",
                        value=rx_packets,
                        timestamp=datetime.now(),
                        labels=interface_labels,
                        unit="packets"
                    ),
                    MetricValue(
                        name="container_network_transmit_packets_total",
                        value=tx_packets,
                        timestamp=datetime.now(),
                        labels=interface_labels,
                        unit="packets"
                    )
                ])
            
            # Create aggregate metrics
            aggregate_labels = {
                "container_id": container_id,
                "container_name": container_name,
                "image": image_name,
                "runtime": "docker",
                **self.config.custom_labels
            }
            
            metrics.extend([
                MetricValue(
                    name="container_network_receive_bytes_total",
                    value=total_rx_bytes,
                    timestamp=datetime.now(),
                    labels=aggregate_labels,
                    unit="bytes"
                ),
                MetricValue(
                    name="container_network_transmit_bytes_total",
                    value=total_tx_bytes,
                    timestamp=datetime.now(),
                    labels=aggregate_labels,
                    unit="bytes"
                ),
                MetricValue(
                    name="container_network_receive_packets_total",
                    value=total_rx_packets,
                    timestamp=datetime.now(),
                    labels=aggregate_labels,
                    unit="packets"
                ),
                MetricValue(
                    name="container_network_transmit_packets_total",
                    value=total_tx_packets,
                    timestamp=datetime.now(),
                    labels=aggregate_labels,
                    unit="packets"
                )
            ])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Docker network metrics for {container_id}: {str(e)}")
            return []
    
    async def _collect_podman_network_metrics(self, container_id: str) -> List[MetricValue]:
        """Collect network metrics from Podman container."""
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
            
            # Extract network I/O (format may vary)
            net_io_str = stats_data.get('NetIO', '0B / 0B')
            rx_bytes, tx_bytes = self._parse_network_io(net_io_str)
            
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
                    name="container_network_receive_bytes_total",
                    value=rx_bytes,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="bytes"
                ),
                MetricValue(
                    name="container_network_transmit_bytes_total",
                    value=tx_bytes,
                    timestamp=datetime.now(),
                    labels=labels,
                    unit="bytes"
                )
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Podman network metrics for {container_id}: {str(e)}")
            return []
    
    def _parse_network_io(self, net_io_str: str) -> tuple[int, int]:
        """
        Parse network I/O string from Podman stats.
        
        Args:
            net_io_str: Network I/O string like "100MB / 50MB"
            
        Returns:
            Tuple of (rx_bytes, tx_bytes)
        """
        try:
            parts = net_io_str.split(' / ')
            if len(parts) != 2:
                return 0, 0
            
            rx_bytes = self._parse_size_string(parts[0].strip())
            tx_bytes = self._parse_size_string(parts[1].strip())
            
            return rx_bytes, tx_bytes
            
        except Exception as e:
            self.logger.warning(f"Error parsing network I/O string '{net_io_str}': {str(e)}")
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