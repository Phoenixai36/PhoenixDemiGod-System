"""
Dashboard widget components.

This module provides widget implementations for the system health dashboard.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum

from .models import WidgetSize, WidgetPosition


class WidgetType(Enum):
    """Widget type definitions."""
    STATUS_SUMMARY = "status_summary"
    METRIC_CHART = "metric_chart"
    SERVICE_LIST = "service_list"
    ALERT_LIST = "alert_list"
    RESOURCE_GAUGE = "resource_gauge"
    EVENT_TIMELINE = "event_timeline"
    CONTAINER_GRID = "container_grid"


class StatusLevel(Enum):
    """Status level definitions."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class WidgetData:
    """Base widget data structure."""
    timestamp: datetime
    widget_id: str
    widget_type: WidgetType
    data: Dict[str, Any]


class BaseWidget(ABC):
    """Base widget class."""
    
    def __init__(self, widget_id: str, title: str, size: WidgetSize = WidgetSize.MEDIUM):
        self.widget_id = widget_id
        self.title = title
        self.size = size
        self.last_updated = datetime.now()
        self.refresh_interval = 30  # seconds
    
    @abstractmethod
    async def get_data(self) -> WidgetData:
        """Get widget data."""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get widget configuration."""
        pass
    
    def should_refresh(self) -> bool:
        """Check if widget should be refreshed."""
        return (datetime.now() - self.last_updated).seconds >= self.refresh_interval


class StatusSummaryWidget(BaseWidget):
    """System status summary widget."""
    
    def __init__(self, widget_id: str, title: str = "System Status"):
        super().__init__(widget_id, title, WidgetSize.LARGE)
        self.refresh_interval = 10
    
    async def get_data(self) -> WidgetData:
        """Get system status summary data."""
        # This would integrate with actual services
        data = {
            "overall_status": StatusLevel.HEALTHY.value,
            "services": {
                "total": 12,
                "healthy": 10,
                "warning": 2,
                "critical": 0
            },
            "containers": {
                "total": 25,
                "running": 23,
                "stopped": 2,
                "error": 0
            },
            "alerts": {
                "active": 3,
                "critical": 0,
                "warning": 3
            },
            "uptime": "99.8%",
            "last_incident": "2 days ago"
        }
        
        self.last_updated = datetime.now()
        return WidgetData(
            timestamp=self.last_updated,
            widget_id=self.widget_id,
            widget_type=WidgetType.STATUS_SUMMARY,
            data=data
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Get widget configuration."""
        return {
            "type": WidgetType.STATUS_SUMMARY.value,
            "title": self.title,
            "size": self.size.value,
            "refresh_interval": self.refresh_interval,
            "show_details": True,
            "color_coding": True
        }


class ResourceGaugeWidget(BaseWidget):
    """Resource usage gauge widget."""
    
    def __init__(self, widget_id: str, resource_type: str, title: Optional[str] = None):
        self.resource_type = resource_type
        title = title or f"{resource_type.title()} Usage"
        super().__init__(widget_id, title, WidgetSize.SMALL)
        self.refresh_interval = 5
    
    async def get_data(self) -> WidgetData:
        """Get resource usage data."""
        # This would integrate with metrics collectors
        usage_data = {
            "cpu": {"current": 45.2, "max": 100, "threshold": 80},
            "memory": {"current": 68.5, "max": 100, "threshold": 85},
            "disk": {"current": 32.1, "max": 100, "threshold": 90},
            "network": {"current": 12.8, "max": 100, "threshold": 75}
        }
        
        data = usage_data.get(self.resource_type, {"current": 0, "max": 100, "threshold": 80})
        data["status"] = self._get_status_level(data["current"], data["threshold"])
        data["unit"] = "%" if self.resource_type != "network" else "Mbps"
        
        self.last_updated = datetime.now()
        return WidgetData(
            timestamp=self.last_updated,
            widget_id=self.widget_id,
            widget_type=WidgetType.RESOURCE_GAUGE,
            data=data
        )
    
    def _get_status_level(self, current: float, threshold: float) -> str:
        """Determine status level based on usage."""
        if current >= threshold:
            return StatusLevel.CRITICAL.value
        elif current >= threshold * 0.8:
            return StatusLevel.WARNING.value
        else:
            return StatusLevel.HEALTHY.value
    
    def get_config(self) -> Dict[str, Any]:
        """Get widget configuration."""
        return {
            "type": WidgetType.RESOURCE_GAUGE.value,
            "title": self.title,
            "size": self.size.value,
            "refresh_interval": self.refresh_interval,
            "resource_type": self.resource_type,
            "show_threshold": True,
            "animate": True
        }


class ServiceListWidget(BaseWidget):
    """Service list widget."""
    
    def __init__(self, widget_id: str, title: str = "Services", max_items: int = 10):
        super().__init__(widget_id, title, WidgetSize.MEDIUM)
        self.max_items = max_items
        self.refresh_interval = 15
    
    async def get_data(self) -> WidgetData:
        """Get service list data."""
        # This would integrate with container discovery service
        services = [
            {
                "name": "nginx-proxy",
                "status": StatusLevel.HEALTHY.value,
                "containers": 2,
                "uptime": "5d 12h",
                "cpu": 12.5,
                "memory": 45.2
            },
            {
                "name": "api-gateway",
                "status": StatusLevel.HEALTHY.value,
                "containers": 3,
                "uptime": "3d 8h",
                "cpu": 25.1,
                "memory": 62.8
            },
            {
                "name": "database",
                "status": StatusLevel.WARNING.value,
                "containers": 1,
                "uptime": "1d 2h",
                "cpu": 45.8,
                "memory": 78.5
            },
            {
                "name": "redis-cache",
                "status": StatusLevel.HEALTHY.value,
                "containers": 2,
                "uptime": "7d 15h",
                "cpu": 8.2,
                "memory": 32.1
            }
        ]
        
        data = {
            "services": services[:self.max_items],
            "total_count": len(services),
            "healthy_count": len([s for s in services if s["status"] == StatusLevel.HEALTHY.value]),
            "warning_count": len([s for s in services if s["status"] == StatusLevel.WARNING.value]),
            "critical_count": len([s for s in services if s["status"] == StatusLevel.CRITICAL.value])
        }
        
        self.last_updated = datetime.now()
        return WidgetData(
            timestamp=self.last_updated,
            widget_id=self.widget_id,
            widget_type=WidgetType.SERVICE_LIST,
            data=data
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Get widget configuration."""
        return {
            "type": WidgetType.SERVICE_LIST.value,
            "title": self.title,
            "size": self.size.value,
            "refresh_interval": self.refresh_interval,
            "max_items": self.max_items,
            "show_metrics": True,
            "sortable": True
        }


class WidgetFactory:
    """Factory for creating widgets."""
    
    @staticmethod
    def create_widget(widget_type: WidgetType, widget_id: str, **kwargs) -> BaseWidget:
        """Create a widget instance."""
        if widget_type == WidgetType.STATUS_SUMMARY:
            return StatusSummaryWidget(widget_id, **kwargs)
        elif widget_type == WidgetType.RESOURCE_GAUGE:
            return ResourceGaugeWidget(widget_id, **kwargs)
        elif widget_type == WidgetType.SERVICE_LIST:
            return ServiceListWidget(widget_id, **kwargs)
        else:
            raise ValueError(f"Unknown widget type: {widget_type}")
    
    @staticmethod
    def get_default_widgets() -> List[BaseWidget]:
        """Get default widget set for system overview."""
        return [
            StatusSummaryWidget("status-summary", "System Overview"),
            ResourceGaugeWidget("cpu-gauge", "cpu", "CPU Usage"),
            ResourceGaugeWidget("memory-gauge", "memory", "Memory Usage"),
            ResourceGaugeWidget("disk-gauge", "disk", "Disk Usage"),
            ServiceListWidget("service-list", "Services")
        ]
