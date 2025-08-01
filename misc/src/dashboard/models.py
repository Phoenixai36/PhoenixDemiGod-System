"""
Data models for dashboard components.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Health status levels with color coding."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ServiceStatus(Enum):
    """Service status types."""
    RUNNING = "running"
    STOPPED = "stopped"
    RESTARTING = "restarting"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class StatusIndicator:
    """Status indicator with color coding."""
    status: HealthStatus
    message: str
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def color(self) -> str:
        """Get color code for status."""
        color_map = {
            HealthStatus.HEALTHY: "#28a745",    # Green
            HealthStatus.WARNING: "#ffc107",    # Yellow
            HealthStatus.CRITICAL: "#dc3545",   # Red
            HealthStatus.UNKNOWN: "#6c757d"     # Gray
        }
        return color_map[self.status]
    
    @property
    def icon(self) -> str:
        """Get icon for status."""
        icon_map = {
            HealthStatus.HEALTHY: "✓",
            HealthStatus.WARNING: "⚠",
            HealthStatus.CRITICAL: "✗",
            HealthStatus.UNKNOWN: "?"
        }
        return icon_map[self.status]


@dataclass
class ContainerInfo:
    """Container information for dashboard display."""
    id: str
    name: str
    image: str
    status: ServiceStatus
    health: HealthStatus
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    memory_limit: Optional[float] = None
    uptime: Optional[float] = None
    restart_count: Optional[int] = None
    labels: Dict[str, str] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def memory_usage_percent(self) -> Optional[float]:
        """Calculate memory usage percentage."""
        if self.memory_usage is not None and self.memory_limit is not None and self.memory_limit > 0:
            return (self.memory_usage / self.memory_limit) * 100
        return None
    
    @property
    def service_name(self) -> str:
        """Extract service name from container name or labels."""
        # Try to get from labels first
        if "service" in self.labels:
            return self.labels["service"]
        
        # Extract from container name (assume format: service-instance)
        parts = self.name.split('-')
        if len(parts) > 1:
            return parts[0]
        
        return self.name


@dataclass
class ServiceGroup:
    """Group of containers belonging to the same service."""
    name: str
    containers: List[ContainerInfo] = field(default_factory=list)
    
    @property
    def overall_health(self) -> HealthStatus:
        """Calculate overall health of the service."""
        if not self.containers:
            return HealthStatus.UNKNOWN
        
        health_counts = {status: 0 for status in HealthStatus}
        for container in self.containers:
            health_counts[container.health] += 1
        
        # Determine overall health based on container health
        if health_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif health_counts[HealthStatus.WARNING] > 0:
            return HealthStatus.WARNING
        elif health_counts[HealthStatus.HEALTHY] > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    @property
    def running_count(self) -> int:
        """Count of running containers."""
        return sum(1 for c in self.containers if c.status == ServiceStatus.RUNNING)
    
    @property
    def total_count(self) -> int:
        """Total number of containers."""
        return len(self.containers)
    
    @property
    def average_cpu_usage(self) -> Optional[float]:
        """Average CPU usage across containers."""
        cpu_values = [c.cpu_usage for c in self.containers if c.cpu_usage is not None]
        if cpu_values:
            return sum(cpu_values) / len(cpu_values)
        return None
    
    @property
    def average_memory_usage_percent(self) -> Optional[float]:
        """Average memory usage percentage across containers."""
        memory_values = [c.memory_usage_percent for c in self.containers 
                        if c.memory_usage_percent is not None]
        if memory_values:
            return sum(memory_values) / len(memory_values)
        return None


@dataclass
class SystemSummary:
    """Overall system health summary."""
    total_containers: int
    running_containers: int
    failed_containers: int
    restarting_containers: int
    overall_health: HealthStatus
    services: List[ServiceGroup] = field(default_factory=list)
    alerts_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def healthy_services_count(self) -> int:
        """Count of healthy services."""
        return sum(1 for s in self.services if s.overall_health == HealthStatus.HEALTHY)
    
    @property
    def warning_services_count(self) -> int:
        """Count of services with warnings."""
        return sum(1 for s in self.services if s.overall_health == HealthStatus.WARNING)
    
    @property
    def critical_services_count(self) -> int:
        """Count of critical services."""
        return sum(1 for s in self.services if s.overall_health == HealthStatus.CRITICAL)
    
    @property
    def uptime_percentage(self) -> float:
        """Calculate overall system uptime percentage."""
        if self.total_containers == 0:
            return 100.0
        return (self.running_containers / self.total_containers) * 100


@dataclass
class MetricSummary:
    """Summary of key metrics for dashboard display."""
    name: str
    current_value: Union[float, int]
    unit: Optional[str] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    change_percent: Optional[float] = None
    status: HealthStatus = HealthStatus.HEALTHY
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    
    def evaluate_status(self) -> HealthStatus:
        """Evaluate status based on thresholds."""
        if self.threshold_critical is not None and self.current_value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.threshold_warning is not None and self.current_value >= self.threshold_warning:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY


@dataclass
class DashboardFilter:
    """Filter criteria for dashboard data."""
    service_names: Optional[List[str]] = None
    health_status: Optional[List[HealthStatus]] = None
    container_status: Optional[List[ServiceStatus]] = None
    search_text: Optional[str] = None
    
    def matches_container(self, container: ContainerInfo) -> bool:
        """Check if container matches filter criteria."""
        # Service name filter
        if self.service_names and container.service_name not in self.service_names:
            return False
        
        # Health status filter
        if self.health_status and container.health not in self.health_status:
            return False
        
        # Container status filter
        if self.container_status and container.status not in self.container_status:
            return False
        
        # Search text filter
        if self.search_text:
            search_lower = self.search_text.lower()
            searchable_text = f"{container.name} {container.image} {container.service_name}".lower()
            if search_lower not in searchable_text:
                return False
        
        return True
    
    def matches_service(self, service: ServiceGroup) -> bool:
        """Check if service matches filter criteria."""
        # Service name filter
        if self.service_names and service.name not in self.service_names:
            return False
        
        # Health status filter
        if self.health_status and service.overall_health not in self.health_status:
            return False
        
        # Search text filter
        if self.search_text:
            search_lower = self.search_text.lower()
            if search_lower not in service.name.lower():
                return False
        
        return True


@dataclass
class DashboardConfig:
    """Configuration for dashboard display."""
    refresh_interval: int = 30  # seconds
    max_containers_per_service: int = 10
    show_healthy_services: bool = True
    show_warning_services: bool = True
    show_critical_services: bool = True
    auto_refresh: bool = True
    theme: str = "light"  # "light" or "dark"
    layout_file: str = "config/dashboard_layout.json"
    
    # Thresholds for status indicators
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 90.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 95.0
    
    # Display options
    show_metrics_charts: bool = True
    show_event_timeline: bool = True
    compact_view: bool = False


# Additional models for layout integration
from dataclasses import dataclass
from enum import Enum


class WidgetSize(Enum):
    """Widget size options."""
    SMALL = "small"      # 1x1
    MEDIUM = "medium"    # 2x1
    LARGE = "large"      # 2x2
    FULL = "full"        # Full width


@dataclass
class WidgetPosition:
    """Position of a widget in the dashboard grid."""
    row: int
    col: int
    size: WidgetSize = WidgetSize.MEDIUM
    
    @property
    def width(self) -> int:
        """Get widget width in grid units."""
        if self.size == WidgetSize.SMALL:
            return 1
        elif self.size == WidgetSize.MEDIUM or self.size == WidgetSize.LARGE:
            return 2
        elif self.size == WidgetSize.FULL:
            return 4  # Assuming a 4-column grid
        return 1
    
    @property
    def height(self) -> int:
        """Get widget height in grid units."""
        if self.size == WidgetSize.SMALL or self.size == WidgetSize.MEDIUM:
            return 1
        elif self.size == WidgetSize.LARGE:
            return 2
        elif self.size == WidgetSize.FULL:
            return 1
        return 1
    
    def overlaps(self, other: 'WidgetPosition') -> bool:
        """Check if this position overlaps with another."""
        # Check if rectangles overlap
        return not (
            self.col + self.width <= other.col or
            other.col + other.width <= self.col or
            self.row + self.height <= other.row or
            other.row + other.height <= self.row
        )
