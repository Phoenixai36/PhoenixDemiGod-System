"""
Data models for the metrics collection system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class MetricType(Enum):
    """Types of metrics that can be collected."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    CONTAINER_LIFECYCLE = "container_lifecycle"
    CUSTOM = "custom"


@dataclass
class MetricValue:
    """Represents a single metric value with metadata."""
    name: str
    value: Union[float, int, str]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    
    def to_prometheus_format(self) -> str:
        """Convert metric to Prometheus format."""
        labels_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = "{" + ",".join(label_pairs) + "}"
        
        return f"{self.name}{labels_str} {self.value} {int(self.timestamp.timestamp() * 1000)}"


@dataclass
class ContainerMetrics:
    """Container-specific metrics collection."""
    container_id: str
    container_name: str
    image: str
    cpu_usage_percent: Optional[float] = None
    memory_usage_bytes: Optional[int] = None
    memory_limit_bytes: Optional[int] = None
    disk_read_bytes: Optional[int] = None
    disk_write_bytes: Optional[int] = None
    network_rx_bytes: Optional[int] = None
    network_tx_bytes: Optional[int] = None
    restart_count: Optional[int] = None
    uptime_seconds: Optional[float] = None
    status: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_metric_values(self) -> List[MetricValue]:
        """Convert container metrics to list of MetricValue objects."""
        base_labels = {
            "container_id": self.container_id,
            "container_name": self.container_name,
            "image": self.image,
            **self.labels
        }
        
        metrics = []
        
        if self.cpu_usage_percent is not None:
            metrics.append(MetricValue(
                name="container_cpu_usage_percent",
                value=self.cpu_usage_percent,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="percent"
            ))
        
        if self.memory_usage_bytes is not None:
            metrics.append(MetricValue(
                name="container_memory_usage_bytes",
                value=self.memory_usage_bytes,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="bytes"
            ))
        
        if self.memory_limit_bytes is not None:
            metrics.append(MetricValue(
                name="container_memory_limit_bytes",
                value=self.memory_limit_bytes,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="bytes"
            ))
        
        if self.disk_read_bytes is not None:
            metrics.append(MetricValue(
                name="container_disk_read_bytes_total",
                value=self.disk_read_bytes,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="bytes"
            ))
        
        if self.disk_write_bytes is not None:
            metrics.append(MetricValue(
                name="container_disk_write_bytes_total",
                value=self.disk_write_bytes,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="bytes"
            ))
        
        if self.network_rx_bytes is not None:
            metrics.append(MetricValue(
                name="container_network_receive_bytes_total",
                value=self.network_rx_bytes,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="bytes"
            ))
        
        if self.network_tx_bytes is not None:
            metrics.append(MetricValue(
                name="container_network_transmit_bytes_total",
                value=self.network_tx_bytes,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="bytes"
            ))
        
        if self.restart_count is not None:
            metrics.append(MetricValue(
                name="container_restarts_total",
                value=self.restart_count,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="count"
            ))
        
        if self.uptime_seconds is not None:
            metrics.append(MetricValue(
                name="container_uptime_seconds",
                value=self.uptime_seconds,
                timestamp=self.timestamp,
                labels=base_labels,
                unit="seconds"
            ))
        
        return metrics


@dataclass
class CollectorConfig:
    """Configuration for a metrics collector."""
    name: str
    enabled: bool = True
    collection_interval: int = 30  # seconds
    timeout: int = 10  # seconds
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    custom_labels: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectorStatus:
    """Status information for a metrics collector."""
    name: str
    enabled: bool
    last_collection_time: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int = 0
    success_count: int = 0
    is_healthy: bool = True