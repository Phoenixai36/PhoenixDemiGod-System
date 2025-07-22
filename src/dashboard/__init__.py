"""
Dashboard service for system health monitoring.
"""

from .widgets import BaseWidget, WidgetFactory, WidgetType, StatusLevel
from .layout import DashboardLayout, LayoutSection, WidgetPosition, WidgetSize
from .models import DashboardConfig, HealthStatus, ServiceStatus

# Optional imports that require FastAPI
try:
    from .service import DashboardService, DashboardWebSocketHandler
    from .api import router as dashboard_router
    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False

__all__ = [
    'BaseWidget',
    'WidgetFactory',
    'WidgetType',
    'StatusLevel',
    'DashboardLayout',
    'LayoutSection',
    'WidgetPosition',
    'WidgetSize',
    'DashboardConfig',
    'HealthStatus',
    'ServiceStatus'
]

# Add FastAPI-dependent exports if available
if _HAS_FASTAPI:
    __all__.extend([
        'DashboardService',
        'DashboardWebSocketHandler',
        'dashboard_router'
    ])
