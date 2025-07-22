"""
Dashboard API endpoints.

This module provides FastAPI endpoints for the dashboard service.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from .service import DashboardService, DashboardWebSocketHandler
from .widgets import WidgetType
from .layout import WidgetPosition, WidgetSize
from .overview import SystemOverviewDashboard, OverviewWidgetManager
from .models import DashboardFilter, HealthStatus, ServiceStatus


# Request/Response models
class AddWidgetRequest(BaseModel):
    section_index: int
    widget_type: str
    widget_id: str
    position: Dict[str, Any]  # row, col, size
    config: Optional[Dict[str, Any]] = None


class UpdatePositionRequest(BaseModel):
    widget_id: str
    position: Dict[str, Any]  # row, col, size


class DashboardResponse(BaseModel):
    layout: Dict[str, Any]
    widgets: Dict[str, Any]
    last_updated: str


# Global dashboard service instances
dashboard_service: Optional[DashboardService] = None
websocket_handler: Optional[DashboardWebSocketHandler] = None
overview_dashboard: Optional[SystemOverviewDashboard] = None
overview_widget_manager: Optional[OverviewWidgetManager] = None


async def get_dashboard_service() -> DashboardService:
    """Get dashboard service dependency."""
    global dashboard_service
    if dashboard_service is None:
        dashboard_service = DashboardService()
        await dashboard_service.initialize()
    return dashboard_service


async def get_websocket_handler() -> DashboardWebSocketHandler:
    """Get WebSocket handler dependency."""
    global websocket_handler
    if websocket_handler is None:
        service = await get_dashboard_service()
        websocket_handler = DashboardWebSocketHandler(service)
    return websocket_handler


async def get_overview_dashboard() -> SystemOverviewDashboard:
    """Get overview dashboard dependency."""
    global overview_dashboard
    if overview_dashboard is None:
        overview_dashboard = SystemOverviewDashboard()
    return overview_dashboard


async def get_overview_widget_manager() -> OverviewWidgetManager:
    """Get overview widget manager dependency."""
    global overview_widget_manager
    if overview_widget_manager is None:
        overview = await get_overview_dashboard()
        overview_widget_manager = OverviewWidgetManager(overview)
    return overview_widget_manager


# Create router
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, Any]:
    """Get complete dashboard data."""
    try:
        return await service.get_dashboard_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/widgets/{widget_id}")
async def get_widget_data(
    widget_id: str,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, Any]:
    """Get data for a specific widget."""
    widget_data = await service.get_widget_data(widget_id)
    if widget_data is None:
        raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")
    return widget_data


@router.post("/widgets")
async def add_widget(
    request: AddWidgetRequest,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, str]:
    """Add a new widget to the dashboard."""
    try:
        # Parse widget type
        widget_type = WidgetType(request.widget_type)
        
        # Parse position
        position = WidgetPosition(
            row=request.position["row"],
            col=request.position["col"],
            size=WidgetSize(request.position.get("size", "medium"))
        )
        
        # Add widget
        success = await service.add_widget(
            request.section_index,
            widget_type,
            request.widget_id,
            position,
            **(request.config or {})
        )
        
        if success:
            return {"message": f"Widget {request.widget_id} added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add widget")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid widget type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add widget: {str(e)}")


@router.delete("/widgets/{widget_id}")
async def remove_widget(
    widget_id: str,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, str]:
    """Remove a widget from the dashboard."""
    success = await service.remove_widget(widget_id)
    if success:
        return {"message": f"Widget {widget_id} removed successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")


@router.put("/widgets/position")
async def update_widget_position(
    request: UpdatePositionRequest,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, str]:
    """Update widget position."""
    try:
        position = WidgetPosition(
            row=request.position["row"],
            col=request.position["col"],
            size=WidgetSize(request.position.get("size", "medium"))
        )
        
        success = await service.update_widget_position(request.widget_id, position)
        if success:
            return {"message": f"Widget {request.widget_id} position updated"}
        else:
            raise HTTPException(status_code=404, detail=f"Widget {request.widget_id} not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update position: {str(e)}")


@router.post("/widgets/{widget_id}/refresh")
async def refresh_widget(
    widget_id: str,
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, str]:
    """Force refresh a specific widget."""
    success = await service.refresh_widget(widget_id)
    if success:
        return {"message": f"Widget {widget_id} refreshed successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")


@router.post("/refresh")
async def refresh_all_widgets(
    service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, str]:
    """Force refresh all widgets."""
    await service.refresh_all_widgets()
    return {"message": "All widgets refreshed successfully"}


@router.get("/widget-types")
async def get_widget_types() -> List[Dict[str, str]]:
    """Get available widget types."""
    return [
        {"type": wt.value, "name": wt.value.replace("_", " ").title()}
        for wt in WidgetType
    ]


# Overview Dashboard Endpoints
@router.get("/overview/summary")
async def get_system_summary(
    overview: SystemOverviewDashboard = Depends(get_overview_dashboard)
) -> Dict[str, Any]:
    """Get system summary for overview dashboard."""
    try:
        summary = await overview.get_system_summary()
        return {
            "total_containers": summary.total_containers,
            "running_containers": summary.running_containers,
            "failed_containers": summary.failed_containers,
            "restarting_containers": summary.restarting_containers,
            "overall_health": summary.overall_health.value,
            "services_count": len(summary.services),
            "healthy_services": summary.healthy_services_count,
            "warning_services": summary.warning_services_count,
            "critical_services": summary.critical_services_count,
            "alerts_count": summary.alerts_count,
            "uptime_percentage": summary.uptime_percentage,
            "last_updated": summary.last_updated.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system summary: {str(e)}")


@router.get("/overview/metrics")
async def get_overview_metrics(
    overview: SystemOverviewDashboard = Depends(get_overview_dashboard)
) -> Dict[str, Any]:
    """Get key metrics for overview display."""
    try:
        metrics = await overview.get_overview_metrics()
        return {
            "total_containers": metrics.total_containers,
            "running_containers": metrics.running_containers,
            "failed_containers": metrics.failed_containers,
            "restarting_containers": metrics.restarting_containers,
            "total_services": metrics.total_services,
            "healthy_services": metrics.healthy_services,
            "warning_services": metrics.warning_services,
            "critical_services": metrics.critical_services,
            "active_alerts": metrics.active_alerts,
            "system_uptime": metrics.system_uptime,
            "avg_cpu_usage": metrics.avg_cpu_usage,
            "avg_memory_usage": metrics.avg_memory_usage,
            "last_updated": metrics.last_updated.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview metrics: {str(e)}")


@router.get("/overview/services")
async def get_filtered_services(
    service_names: Optional[str] = None,
    health_status: Optional[str] = None,
    container_status: Optional[str] = None,
    search_text: Optional[str] = None,
    overview: SystemOverviewDashboard = Depends(get_overview_dashboard)
) -> Dict[str, Any]:
    """Get services with optional filtering."""
    try:
        # Build filter criteria
        filter_criteria = DashboardFilter()
        
        if service_names:
            filter_criteria.service_names = service_names.split(",")
        
        if health_status:
            filter_criteria.health_status = [HealthStatus(status) for status in health_status.split(",")]
        
        if container_status:
            filter_criteria.container_status = [ServiceStatus(status) for status in container_status.split(",")]
        
        if search_text:
            filter_criteria.search_text = search_text
        
        services = await overview.get_filtered_services(filter_criteria)
        
        services_data = []
        for service in services:
            services_data.append({
                "name": service.name,
                "overall_health": service.overall_health.value,
                "total_containers": service.total_count,
                "running_containers": service.running_count,
                "average_cpu_usage": service.average_cpu_usage,
                "average_memory_usage_percent": service.average_memory_usage_percent,
                "containers": [
                    {
                        "id": container.id,
                        "name": container.name,
                        "image": container.image,
                        "status": container.status.value,
                        "health": container.health.value,
                        "cpu_usage": container.cpu_usage,
                        "memory_usage_percent": container.memory_usage_percent,
                        "uptime": container.uptime,
                        "restart_count": container.restart_count
                    }
                    for container in service.containers
                ]
            })
        
        return {
            "services": services_data,
            "total_count": len(services),
            "healthy_count": sum(1 for s in services if s.overall_health == HealthStatus.HEALTHY),
            "warning_count": sum(1 for s in services if s.overall_health == HealthStatus.WARNING),
            "critical_count": sum(1 for s in services if s.overall_health == HealthStatus.CRITICAL)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")


@router.get("/overview/status-indicators")
async def get_status_indicators(
    overview: SystemOverviewDashboard = Depends(get_overview_dashboard)
) -> List[Dict[str, Any]]:
    """Get status indicators for dashboard display."""
    try:
        indicators = await overview.get_status_indicators()
        return [
            {
                "status": indicator.status.value,
                "message": indicator.message,
                "details": indicator.details,
                "color": indicator.color,
                "icon": indicator.icon,
                "timestamp": indicator.timestamp.isoformat()
            }
            for indicator in indicators
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status indicators: {str(e)}")


@router.get("/overview/filters")
async def get_available_filters(
    overview: SystemOverviewDashboard = Depends(get_overview_dashboard)
) -> Dict[str, List[str]]:
    """Get available filter options."""
    try:
        return overview.get_available_filters()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filters: {str(e)}")


@router.get("/overview/widgets/{widget_id}")
async def get_overview_widget_data(
    widget_id: str,
    widget_manager: OverviewWidgetManager = Depends(get_overview_widget_manager)
) -> Dict[str, Any]:
    """Get data for a specific overview widget."""
    try:
        widget_data = await widget_manager.get_widget_data(widget_id)
        if widget_data is None:
            raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")
        return widget_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get widget data: {str(e)}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    handler: DashboardWebSocketHandler = Depends(get_websocket_handler)
):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    await handler.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Handle client messages if needed
            pass
    except WebSocketDisconnect:
        await handler.disconnect(websocket)


@router.get("/ui", response_class=HTMLResponse)
async def dashboard_ui():
    """Serve dashboard UI."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Health Dashboard</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .dashboard { 
                display: grid; 
                grid-template-columns: repeat(4, 1fr); 
                gap: 20px; 
                max-width: 1400px;
                margin: 0 auto;
            }
            .widget { 
                background: white;
                border: none;
                border-radius: 12px; 
                padding: 20px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .widget:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            }
            .widget-small { grid-column: span 1; }
            .widget-medium { grid-column: span 2; }
            .widget-large { grid-column: span 2; grid-row: span 2; }
            .widget-full { grid-column: span 4; }
            
            .status-healthy { color: #28a745; font-weight: bold; }
            .status-warning { color: #ffc107; font-weight: bold; }
            .status-critical { color: #dc3545; font-weight: bold; }
            .status-unknown { color: #6c757d; font-weight: bold; }
            
            .metric-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
            .metric-label { color: #666; font-size: 0.9em; }
            .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            
            .service-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            .service-item:last-child { border-bottom: none; }
            
            .loading { text-align: center; color: #666; }
            .error { color: #dc3545; text-align: center; }
            
            .refresh-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9em;
            }
            .refresh-btn:hover { background: #0056b3; }
            
            .status-indicator {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
            }
            .indicator-healthy { background: #d4edda; color: #155724; }
            .indicator-warning { background: #fff3cd; color: #856404; }
            .indicator-critical { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Phoenix DemiGod - System Health Dashboard</h1>
            <p>Real-time monitoring and health status overview</p>
        </div>
        
        <div id="dashboard" class="dashboard">
            <!-- System Overview Widget -->
            <div class="widget widget-full" id="system-overview">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3>📊 System Overview</h3>
                    <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
                </div>
                <div class="loading">Loading system overview...</div>
            </div>
            
            <!-- CPU Usage Widget -->
            <div class="widget widget-small" id="cpu-widget">
                <h4>💻 CPU Usage</h4>
                <div class="loading">Loading...</div>
            </div>
            
            <!-- Memory Usage Widget -->
            <div class="widget widget-small" id="memory-widget">
                <h4>🧠 Memory Usage</h4>
                <div class="loading">Loading...</div>
            </div>
            
            <!-- Disk Usage Widget -->
            <div class="widget widget-small" id="disk-widget">
                <h4>💾 Disk Usage</h4>
                <div class="loading">Loading...</div>
            </div>
            
            <!-- Status Indicators Widget -->
            <div class="widget widget-small" id="status-indicators">
                <h4>⚡ Status Indicators</h4>
                <div class="loading">Loading...</div>
            </div>
            
            <!-- Services Widget -->
            <div class="widget widget-medium" id="services-widget">
                <h4>🔧 Services</h4>
                <div class="loading">Loading services...</div>
            </div>
            
            <!-- Metrics Widget -->
            <div class="widget widget-medium" id="metrics-widget">
                <h4>📈 Key Metrics</h4>
                <div class="loading">Loading metrics...</div>
            </div>
        </div>
        
        <script>
            let ws = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/dashboard/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    console.log('Dashboard update:', data);
                    if (data.type === 'widget_update') {
                        updateWidget(data.widget_id, data.data);
                    }
                };
                
                ws.onclose = function() {
                    console.log('WebSocket closed, reconnecting in 5 seconds...');
                    setTimeout(connectWebSocket, 5000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            async function loadDashboardData() {
                try {
                    // Load system overview
                    const summaryResponse = await fetch('/api/dashboard/overview/summary');
                    const summary = await summaryResponse.json();
                    updateSystemOverview(summary);
                    
                    // Load services
                    const servicesResponse = await fetch('/api/dashboard/overview/services');
                    const services = await servicesResponse.json();
                    updateServicesWidget(services);
                    
                    // Load metrics
                    const metricsResponse = await fetch('/api/dashboard/overview/metrics');
                    const metrics = await metricsResponse.json();
                    updateMetricsWidget(metrics);
                    
                    // Load status indicators
                    const indicatorsResponse = await fetch('/api/dashboard/overview/status-indicators');
                    const indicators = await indicatorsResponse.json();
                    updateStatusIndicators(indicators);
                    
                    // Load individual widget data
                    await loadWidgetData('cpu-gauge', 'cpu-widget');
                    await loadWidgetData('memory-gauge', 'memory-widget');
                    await loadWidgetData('disk-gauge', 'disk-widget');
                    
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                    showError('Failed to load dashboard data');
                }
            }
            
            async function loadWidgetData(widgetId, elementId) {
                try {
                    const response = await fetch(`/api/dashboard/overview/widgets/${widgetId}`);
                    const widgetData = await response.json();
                    updateResourceWidget(elementId, widgetData);
                } catch (error) {
                    console.error(`Error loading widget ${widgetId}:`, error);
                    document.getElementById(elementId).innerHTML = '<div class="error">Failed to load</div>';
                }
            }
            
            function updateSystemOverview(summary) {
                const element = document.getElementById('system-overview');
                const statusClass = `status-${summary.overall_health}`;
                
                element.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>📊 System Overview</h3>
                        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
                    </div>
                    <div class="metric-grid">
                        <div>
                            <div class="metric-label">Overall Health</div>
                            <div class="metric-value ${statusClass}">${summary.overall_health.toUpperCase()}</div>
                        </div>
                        <div>
                            <div class="metric-label">System Uptime</div>
                            <div class="metric-value">${summary.uptime_percentage.toFixed(1)}%</div>
                        </div>
                        <div>
                            <div class="metric-label">Total Containers</div>
                            <div class="metric-value">${summary.total_containers}</div>
                            <div class="metric-label">Running: ${summary.running_containers} | Failed: ${summary.failed_containers}</div>
                        </div>
                        <div>
                            <div class="metric-label">Services</div>
                            <div class="metric-value">${summary.services_count}</div>
                            <div class="metric-label">
                                <span class="status-healthy">●</span> ${summary.healthy_services}
                                <span class="status-warning">●</span> ${summary.warning_services}
                                <span class="status-critical">●</span> ${summary.critical_services}
                            </div>
                        </div>
                    </div>
                `;
            }
            
            function updateServicesWidget(services) {
                const element = document.getElementById('services-widget');
                let servicesHtml = '<h4>🔧 Services</h4>';
                
                if (services.services.length === 0) {
                    servicesHtml += '<div class="loading">No services found</div>';
                } else {
                    services.services.forEach(service => {
                        const statusClass = `status-${service.overall_health}`;
                        servicesHtml += `
                            <div class="service-item">
                                <div>
                                    <strong>${service.name}</strong>
                                    <div class="metric-label">${service.total_containers} containers</div>
                                </div>
                                <div>
                                    <div class="${statusClass}">${service.overall_health.toUpperCase()}</div>
                                    <div class="metric-label">CPU: ${(service.average_cpu_usage || 0).toFixed(1)}%</div>
                                </div>
                            </div>
                        `;
                    });
                }
                
                element.innerHTML = servicesHtml;
            }
            
            function updateMetricsWidget(metrics) {
                const element = document.getElementById('metrics-widget');
                element.innerHTML = `
                    <h4>📈 Key Metrics</h4>
                    <div class="metric-grid">
                        <div>
                            <div class="metric-label">Avg CPU Usage</div>
                            <div class="metric-value">${metrics.avg_cpu_usage.toFixed(1)}%</div>
                        </div>
                        <div>
                            <div class="metric-label">Avg Memory Usage</div>
                            <div class="metric-value">${metrics.avg_memory_usage.toFixed(1)}%</div>
                        </div>
                        <div>
                            <div class="metric-label">Active Alerts</div>
                            <div class="metric-value ${metrics.active_alerts > 0 ? 'status-warning' : 'status-healthy'}">${metrics.active_alerts}</div>
                        </div>
                        <div>
                            <div class="metric-label">Last Updated</div>
                            <div class="metric-label">${new Date(metrics.last_updated).toLocaleTimeString()}</div>
                        </div>
                    </div>
                `;
            }
            
            function updateStatusIndicators(indicators) {
                const element = document.getElementById('status-indicators');
                let indicatorsHtml = '<h4>⚡ Status Indicators</h4>';
                
                if (indicators.length === 0) {
                    indicatorsHtml += '<div class="status-indicator indicator-healthy">✓ All systems normal</div>';
                } else {
                    indicators.forEach(indicator => {
                        const indicatorClass = `indicator-${indicator.status}`;
                        indicatorsHtml += `
                            <div class="status-indicator ${indicatorClass}" title="${indicator.details || ''}">
                                ${indicator.icon} ${indicator.message}
                            </div>
                        `;
                    });
                }
                
                element.innerHTML = indicatorsHtml;
            }
            
            function updateResourceWidget(elementId, widgetData) {
                const element = document.getElementById(elementId);
                const data = widgetData.data;
                const statusClass = `status-${data.status}`;
                
                element.innerHTML = `
                    <h4>${element.querySelector('h4').textContent}</h4>
                    <div class="metric-value ${statusClass}">${data.current.toFixed(1)}${data.unit}</div>
                    <div class="metric-label">Threshold: ${(data.threshold || 0).toFixed(1)}${data.unit}</div>
                `;
            }
            
            function updateWidget(widgetId, data) {
                // Handle real-time widget updates
                console.log(`Updating widget ${widgetId}:`, data);
            }
            
            function showError(message) {
                document.getElementById('dashboard').innerHTML = `<div class="error">${message}</div>`;
            }
            
            function refreshDashboard() {
                loadDashboardData();
            }
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                loadDashboardData();
                connectWebSocket();
                
                // Auto-refresh every 30 seconds
                setInterval(loadDashboardData, 30000);
            });
        </script>
    </body>
    </html>
    """
