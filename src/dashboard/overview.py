"""
System overview dashboard implementation.

This module provides the main system overview dashboard with health status,
service grouping, filtering, and color-coded status indicators.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .models import (
    HealthStatus, ServiceStatus, ContainerInfo, ServiceGroup, 
    SystemSummary, DashboardFilter, DashboardConfig, StatusIndicator
)
from .widgets import StatusSummaryWidget, ServiceListWidget, ResourceGaugeWidget
from .layout import DashboardLayout, LayoutSection, WidgetPosition, WidgetSize


@dataclass
class OverviewMetrics:
    """Metrics for system overview display."""
    total_containers: int
    running_containers: int
    failed_containers: int
    restarting_containers: int
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    active_alerts: int
    system_uptime: float
    avg_cpu_usage: float
    avg_memory_usage: float
    last_updated: datetime


class SystemOverviewDashboard:
    """Main system overview dashboard."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.layout = DashboardLayout(columns=4)
        self.current_filter = DashboardFilter()
        self.last_update = datetime.now()
        self._setup_layout()
    
    def _setup_layout(self) -> None:
        """Set up the dashboard layout with sections and widgets."""
        # System Status Section (Top)
        status_section = self.layout.add_section("System Status")
        
        # Resource Metrics Section
        metrics_section = self.layout.add_section("Resource Metrics")
        
        # Services Section
        services_section = self.layout.add_section("Services")
        
        # Alerts Section
        alerts_section = self.layout.add_section("Active Alerts")
    
    async def get_system_summary(self) -> SystemSummary:
        """Get comprehensive system summary."""
        # This would integrate with actual container discovery service
        # For now, return mock data that demonstrates the functionality
        
        containers = await self._get_container_data()
        services = self._group_containers_by_service(containers)
        
        # Calculate overall health
        overall_health = self._calculate_overall_health(services)
        
        # Count containers by status
        running_count = sum(1 for c in containers if c.status == ServiceStatus.RUNNING)
        failed_count = sum(1 for c in containers if c.status == ServiceStatus.FAILED)
        restarting_count = sum(1 for c in containers if c.status == ServiceStatus.RESTARTING)
        
        return SystemSummary(
            total_containers=len(containers),
            running_containers=running_count,
            failed_containers=failed_count,
            restarting_containers=restarting_count,
            overall_health=overall_health,
            services=services,
            alerts_count=await self._get_active_alerts_count(),
            last_updated=datetime.now()
        )
    
    async def get_overview_metrics(self) -> OverviewMetrics:
        """Get key metrics for overview display."""
        summary = await self.get_system_summary()
        
        # Calculate average resource usage
        avg_cpu = await self._calculate_average_cpu_usage()
        avg_memory = await self._calculate_average_memory_usage()
        
        return OverviewMetrics(
            total_containers=summary.total_containers,
            running_containers=summary.running_containers,
            failed_containers=summary.failed_containers,
            restarting_containers=summary.restarting_containers,
            total_services=len(summary.services),
            healthy_services=summary.healthy_services_count,
            warning_services=summary.warning_services_count,
            critical_services=summary.critical_services_count,
            active_alerts=summary.alerts_count,
            system_uptime=summary.uptime_percentage,
            avg_cpu_usage=avg_cpu,
            avg_memory_usage=avg_memory,
            last_updated=summary.last_updated
        )
    
    async def get_filtered_services(self, filter_criteria: Optional[DashboardFilter] = None) -> List[ServiceGroup]:
        """Get services filtered by criteria."""
        filter_criteria = filter_criteria or self.current_filter
        summary = await self.get_system_summary()
        
        filtered_services = []
        for service in summary.services:
            if filter_criteria.matches_service(service):
                # Also filter containers within the service
                filtered_containers = [
                    container for container in service.containers
                    if filter_criteria.matches_container(container)
                ]
                
                if filtered_containers:
                    filtered_service = ServiceGroup(
                        name=service.name,
                        containers=filtered_containers
                    )
                    filtered_services.append(filtered_service)
        
        return filtered_services
    
    async def get_status_indicators(self) -> List[StatusIndicator]:
        """Get status indicators for dashboard display."""
        summary = await self.get_system_summary()
        indicators = []
        
        # Overall system health
        indicators.append(StatusIndicator(
            status=summary.overall_health,
            message=f"System Health: {summary.overall_health.value.title()}",
            details=f"{summary.running_containers}/{summary.total_containers} containers running"
        ))
        
        # Service health
        if summary.critical_services_count > 0:
            indicators.append(StatusIndicator(
                status=HealthStatus.CRITICAL,
                message=f"{summary.critical_services_count} Critical Services",
                details="Immediate attention required"
            ))
        
        if summary.warning_services_count > 0:
            indicators.append(StatusIndicator(
                status=HealthStatus.WARNING,
                message=f"{summary.warning_services_count} Services with Warnings",
                details="Monitor closely"
            ))
        
        # Alerts
        if summary.alerts_count > 0:
            indicators.append(StatusIndicator(
                status=HealthStatus.WARNING if summary.alerts_count < 5 else HealthStatus.CRITICAL,
                message=f"{summary.alerts_count} Active Alerts",
                details="Check alert dashboard for details"
            ))
        
        # Resource usage
        avg_cpu = await self._calculate_average_cpu_usage()
        if avg_cpu > self.config.cpu_critical_threshold:
            indicators.append(StatusIndicator(
                status=HealthStatus.CRITICAL,
                message=f"High CPU Usage: {avg_cpu:.1f}%",
                details="System under heavy load"
            ))
        elif avg_cpu > self.config.cpu_warning_threshold:
            indicators.append(StatusIndicator(
                status=HealthStatus.WARNING,
                message=f"Elevated CPU Usage: {avg_cpu:.1f}%",
                details="Monitor resource usage"
            ))
        
        return indicators
    
    def set_filter(self, filter_criteria: DashboardFilter) -> None:
        """Set filter criteria for dashboard display."""
        self.current_filter = filter_criteria
    
    def get_available_filters(self) -> Dict[str, List[str]]:
        """Get available filter options."""
        # This would be populated from actual data
        return {
            "services": ["nginx-proxy", "api-gateway", "database", "redis-cache", "monitoring"],
            "health_status": [status.value for status in HealthStatus],
            "container_status": [status.value for status in ServiceStatus]
        }
    
    async def _get_container_data(self) -> List[ContainerInfo]:
        """Get container data from discovery service."""
        # Mock data - in real implementation, this would call the container discovery service
        containers = [
            ContainerInfo(
                id="nginx-1",
                name="nginx-proxy-1",
                image="nginx:latest",
                status=ServiceStatus.RUNNING,
                health=HealthStatus.HEALTHY,
                cpu_usage=12.5,
                memory_usage=128 * 1024 * 1024,  # 128MB
                memory_limit=512 * 1024 * 1024,  # 512MB
                uptime=86400 * 5,  # 5 days
                restart_count=0,
                labels={"service": "nginx-proxy", "tier": "frontend"}
            ),
            ContainerInfo(
                id="nginx-2",
                name="nginx-proxy-2",
                image="nginx:latest",
                status=ServiceStatus.RUNNING,
                health=HealthStatus.HEALTHY,
                cpu_usage=15.2,
                memory_usage=142 * 1024 * 1024,
                memory_limit=512 * 1024 * 1024,
                uptime=86400 * 3,  # 3 days
                restart_count=1,
                labels={"service": "nginx-proxy", "tier": "frontend"}
            ),
            ContainerInfo(
                id="api-1",
                name="api-gateway-1",
                image="api-gateway:v1.2.0",
                status=ServiceStatus.RUNNING,
                health=HealthStatus.HEALTHY,
                cpu_usage=25.1,
                memory_usage=256 * 1024 * 1024,
                memory_limit=1024 * 1024 * 1024,  # 1GB
                uptime=86400 * 2,
                restart_count=0,
                labels={"service": "api-gateway", "tier": "backend"}
            ),
            ContainerInfo(
                id="db-1",
                name="database-primary",
                image="postgres:13",
                status=ServiceStatus.RUNNING,
                health=HealthStatus.WARNING,
                cpu_usage=45.8,
                memory_usage=800 * 1024 * 1024,
                memory_limit=2048 * 1024 * 1024,  # 2GB
                uptime=86400,  # 1 day
                restart_count=2,
                labels={"service": "database", "tier": "data", "role": "primary"}
            ),
            ContainerInfo(
                id="redis-1",
                name="redis-cache-1",
                image="redis:6-alpine",
                status=ServiceStatus.RUNNING,
                health=HealthStatus.HEALTHY,
                cpu_usage=8.2,
                memory_usage=64 * 1024 * 1024,
                memory_limit=256 * 1024 * 1024,
                uptime=86400 * 7,  # 7 days
                restart_count=0,
                labels={"service": "redis-cache", "tier": "cache"}
            ),
            ContainerInfo(
                id="monitor-1",
                name="prometheus-1",
                image="prometheus:latest",
                status=ServiceStatus.RUNNING,
                health=HealthStatus.HEALTHY,
                cpu_usage=18.5,
                memory_usage=512 * 1024 * 1024,
                memory_limit=1024 * 1024 * 1024,
                uptime=86400 * 10,  # 10 days
                restart_count=0,
                labels={"service": "monitoring", "tier": "ops"}
            )
        ]
        
        return containers
    
    def _group_containers_by_service(self, containers: List[ContainerInfo]) -> List[ServiceGroup]:
        """Group containers by service name."""
        service_groups = {}
        
        for container in containers:
            service_name = container.service_name
            if service_name not in service_groups:
                service_groups[service_name] = ServiceGroup(name=service_name)
            
            service_groups[service_name].containers.append(container)
        
        return list(service_groups.values())
    
    def _calculate_overall_health(self, services: List[ServiceGroup]) -> HealthStatus:
        """Calculate overall system health based on service health."""
        if not services:
            return HealthStatus.UNKNOWN
        
        critical_count = sum(1 for s in services if s.overall_health == HealthStatus.CRITICAL)
        warning_count = sum(1 for s in services if s.overall_health == HealthStatus.WARNING)
        
        # System is critical if any service is critical
        if critical_count > 0:
            return HealthStatus.CRITICAL
        
        # System has warnings if more than 20% of services have warnings
        if warning_count > len(services) * 0.2:
            return HealthStatus.WARNING
        
        # System is healthy if most services are healthy
        return HealthStatus.HEALTHY
    
    async def _get_active_alerts_count(self) -> int:
        """Get count of active alerts."""
        # Mock data - would integrate with alerting system
        return 3
    
    async def _calculate_average_cpu_usage(self) -> float:
        """Calculate average CPU usage across all containers."""
        containers = await self._get_container_data()
        cpu_values = [c.cpu_usage for c in containers if c.cpu_usage is not None]
        
        if cpu_values:
            return sum(cpu_values) / len(cpu_values)
        return 0.0
    
    async def _calculate_average_memory_usage(self) -> float:
        """Calculate average memory usage percentage across all containers."""
        containers = await self._get_container_data()
        memory_values = [c.memory_usage_percent for c in containers 
                        if c.memory_usage_percent is not None]
        
        if memory_values:
            return sum(memory_values) / len(memory_values)
        return 0.0


class OverviewWidgetManager:
    """Manager for overview dashboard widgets."""
    
    def __init__(self, overview_dashboard: SystemOverviewDashboard):
        self.overview = overview_dashboard
        self.widgets = {}
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create widgets for overview dashboard."""
        # System status summary widget
        self.widgets["system-status"] = StatusSummaryWidget(
            "system-status",
            "System Overview"
        )
        
        # Resource gauge widgets
        self.widgets["cpu-gauge"] = ResourceGaugeWidget(
            "cpu-gauge",
            "cpu",
            "CPU Usage"
        )
        
        self.widgets["memory-gauge"] = ResourceGaugeWidget(
            "memory-gauge", 
            "memory",
            "Memory Usage"
        )
        
        self.widgets["disk-gauge"] = ResourceGaugeWidget(
            "disk-gauge",
            "disk", 
            "Disk Usage"
        )
        
        # Services list widget
        self.widgets["services-list"] = ServiceListWidget(
            "services-list",
            "Services",
            max_items=15
        )
    
    async def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific widget."""
        if widget_id not in self.widgets:
            return None
        
        widget = self.widgets[widget_id]
        
        # Override widget data with real overview data
        if widget_id == "system-status":
            return await self._get_system_status_data()
        elif widget_id == "services-list":
            return await self._get_services_list_data()
        else:
            # Use default widget data for resource gauges
            widget_data = await widget.get_data()
            return {
                "config": widget.get_config(),
                "data": widget_data.data,
                "timestamp": widget_data.timestamp.isoformat()
            }
    
    async def _get_system_status_data(self) -> Dict[str, Any]:
        """Get system status widget data."""
        metrics = await self.overview.get_overview_metrics()
        
        data = {
            "overall_status": self._get_overall_status_string(metrics),
            "services": {
                "total": metrics.total_services,
                "healthy": metrics.healthy_services,
                "warning": metrics.warning_services,
                "critical": metrics.critical_services
            },
            "containers": {
                "total": metrics.total_containers,
                "running": metrics.running_containers,
                "stopped": metrics.total_containers - metrics.running_containers,
                "error": metrics.failed_containers
            },
            "alerts": {
                "active": metrics.active_alerts,
                "critical": 0,  # Would be calculated from actual alerts
                "warning": metrics.active_alerts
            },
            "uptime": f"{metrics.system_uptime:.1f}%",
            "last_incident": "2 hours ago",  # Would come from incident tracking
            "avg_cpu": f"{metrics.avg_cpu_usage:.1f}%",
            "avg_memory": f"{metrics.avg_memory_usage:.1f}%"
        }
        
        return {
            "config": self.widgets["system-status"].get_config(),
            "data": data,
            "timestamp": metrics.last_updated.isoformat()
        }
    
    async def _get_services_list_data(self) -> Dict[str, Any]:
        """Get services list widget data."""
        services = await self.overview.get_filtered_services()
        
        services_data = []
        for service in services:
            services_data.append({
                "name": service.name,
                "status": service.overall_health.value,
                "containers": service.total_count,
                "uptime": self._format_uptime(service.containers[0].uptime if service.containers else 0),
                "cpu": service.average_cpu_usage or 0,
                "memory": service.average_memory_usage_percent or 0
            })
        
        data = {
            "services": services_data,
            "total_count": len(services),
            "healthy_count": sum(1 for s in services if s.overall_health == HealthStatus.HEALTHY),
            "warning_count": sum(1 for s in services if s.overall_health == HealthStatus.WARNING),
            "critical_count": sum(1 for s in services if s.overall_health == HealthStatus.CRITICAL)
        }
        
        return {
            "config": self.widgets["services-list"].get_config(),
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_overall_status_string(self, metrics: OverviewMetrics) -> str:
        """Get overall status string based on metrics."""
        if metrics.critical_services > 0 or metrics.failed_containers > 0:
            return HealthStatus.CRITICAL.value
        elif metrics.warning_services > 0 or metrics.avg_cpu_usage > 80:
            return HealthStatus.WARNING.value
        else:
            return HealthStatus.HEALTHY.value
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format."""
        if uptime_seconds < 3600:  # Less than 1 hour
            minutes = int(uptime_seconds / 60)
            return f"{minutes}m"
        elif uptime_seconds < 86400:  # Less than 1 day
            hours = int(uptime_seconds / 3600)
            return f"{hours}h"
        else:  # Days
            days = int(uptime_seconds / 86400)
            hours = int((uptime_seconds % 86400) / 3600)
            return f"{days}d {hours}h"