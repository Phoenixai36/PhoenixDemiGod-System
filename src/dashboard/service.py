"""
Dashboard service implementation.

This module provides the main dashboard service for system health monitoring.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .layout import DashboardLayout, LayoutSection, WidgetPosition, WidgetSize
from .widgets import BaseWidget, WidgetFactory, WidgetType, WidgetData
from .models import DashboardConfig


class DashboardService:
    """Main dashboard service."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.layout = DashboardLayout(columns=4)
        self.widgets: Dict[str, BaseWidget] = {}
        self.widget_data_cache: Dict[str, WidgetData] = {}
        self.update_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
    
    async def initialize(self) -> None:
        """Initialize the dashboard service."""
        # Load saved layout if exists
        await self._load_layout()
        
        # Create default layout if none exists
        if not self.layout.sections:
            await self._create_default_layout()
        
        # Start widget update tasks
        await self._start_widget_updates()
        self.is_running = True
    
    async def shutdown(self) -> None:
        """Shutdown the dashboard service."""
        self.is_running = False
        
        # Cancel all update tasks
        for task in self.update_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.update_tasks:
            await asyncio.gather(*self.update_tasks.values(), return_exceptions=True)
        
        self.update_tasks.clear()
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        dashboard_data = {
            "layout": self.layout.to_dict(),
            "widgets": {},
            "last_updated": datetime.now().isoformat()
        }
        
        # Get data for all widgets
        for widget_id, widget in self.widgets.items():
            if widget_id in self.widget_data_cache:
                widget_data = self.widget_data_cache[widget_id]
                dashboard_data["widgets"][widget_id] = {
                    "config": widget.get_config(),
                    "data": widget_data.data,
                    "timestamp": widget_data.timestamp.isoformat()
                }
        
        return dashboard_data
    
    async def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific widget."""
        if widget_id not in self.widgets:
            return None
        
        widget = self.widgets[widget_id]
        if widget_id in self.widget_data_cache:
            widget_data = self.widget_data_cache[widget_id]
            return {
                "config": widget.get_config(),
                "data": widget_data.data,
                "timestamp": widget_data.timestamp.isoformat()
            }
        
        return None
    
    async def add_widget(self, section_index: int, widget_type: WidgetType, 
                        widget_id: str, position: WidgetPosition, **kwargs) -> bool:
        """Add a new widget to the dashboard."""
        try:
            # Create widget instance
            widget = WidgetFactory.create_widget(widget_type, widget_id, **kwargs)
            
            # Add to layout
            if self.layout.add_widget(section_index, widget_id, widget, position):
                self.widgets[widget_id] = widget
                
                # Start update task for the widget
                if self.is_running:
                    await self._start_widget_update_task(widget_id, widget)
                
                # Save layout
                await self._save_layout()
                return True
            
            return False
        except Exception as e:
            print(f"Error adding widget {widget_id}: {e}")
            return False
    
    async def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget from the dashboard."""
        if widget_id not in self.widgets:
            return False
        
        # Cancel update task
        if widget_id in self.update_tasks:
            self.update_tasks[widget_id].cancel()
            del self.update_tasks[widget_id]
        
        # Remove from layout and widgets
        self.layout.remove_widget(widget_id)
        del self.widgets[widget_id]
        
        # Remove cached data
        if widget_id in self.widget_data_cache:
            del self.widget_data_cache[widget_id]
        
        # Save layout
        await self._save_layout()
        return True
    
    async def update_widget_position(self, widget_id: str, position: WidgetPosition) -> bool:
        """Update widget position."""
        # This would require extending the layout system
        # For now, just return success
        await self._save_layout()
        return True
    
    async def refresh_widget(self, widget_id: str) -> bool:
        """Force refresh a specific widget."""
        if widget_id not in self.widgets:
            return False
        
        widget = self.widgets[widget_id]
        try:
            widget_data = await widget.get_data()
            self.widget_data_cache[widget_id] = widget_data
            return True
        except Exception as e:
            print(f"Error refreshing widget {widget_id}: {e}")
            return False
    
    async def refresh_all_widgets(self) -> None:
        """Force refresh all widgets."""
        tasks = []
        for widget_id in self.widgets:
            tasks.append(self.refresh_widget(widget_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _create_default_layout(self) -> None:
        """Create default dashboard layout."""
        # System overview section
        overview_section = self.layout.add_section("System Overview")
        
        # Add default widgets
        default_widgets = WidgetFactory.get_default_widgets()
        
        # Status summary (top, full width)
        status_widget = default_widgets[0]
        self.widgets[status_widget.widget_id] = status_widget
        overview_section.add_widget(
            status_widget.widget_id,
            WidgetPosition(0, 0, WidgetSize.FULL)
        )
        
        # Resource gauges (second row)
        for i, widget in enumerate(default_widgets[1:4]):  # CPU, Memory, Disk
            self.widgets[widget.widget_id] = widget
            overview_section.add_widget(
                widget.widget_id,
                WidgetPosition(1, i, WidgetSize.SMALL)
            )
        
        # Services section
        services_section = self.layout.add_section("Services")
        service_widget = default_widgets[4]  # Service list
        self.widgets[service_widget.widget_id] = service_widget
        services_section.add_widget(
            service_widget.widget_id,
            WidgetPosition(0, 0, WidgetSize.MEDIUM)
        )
    
    async def _start_widget_updates(self) -> None:
        """Start update tasks for all widgets."""
        for widget_id, widget in self.widgets.items():
            await self._start_widget_update_task(widget_id, widget)
    
    async def _start_widget_update_task(self, widget_id: str, widget: BaseWidget) -> None:
        """Start update task for a specific widget."""
        if widget_id in self.update_tasks:
            self.update_tasks[widget_id].cancel()
        
        self.update_tasks[widget_id] = asyncio.create_task(
            self._widget_update_loop(widget_id, widget)
        )
    
    async def _widget_update_loop(self, widget_id: str, widget: BaseWidget) -> None:
        """Update loop for a widget."""
        while self.is_running:
            try:
                if widget.should_refresh():
                    widget_data = await widget.get_data()
                    self.widget_data_cache[widget_id] = widget_data
                
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in widget update loop for {widget_id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _load_layout(self) -> None:
        """Load dashboard layout from file."""
        layout_file = Path(self.config.layout_file)
        if layout_file.exists():
            try:
                with open(layout_file, 'r') as f:
                    layout_data = json.load(f)
                
                # Recreate widgets from saved data
                saved_widgets = {}
                for section_data in layout_data.get("sections", []):
                    for widget_data in section_data.get("widgets", []):
                        widget_id = widget_data["id"]
                        # This would need to store widget type and config
                        # For now, skip loading saved widgets
                        pass
                
                self.layout = DashboardLayout.from_dict(layout_data, saved_widgets)
            except Exception as e:
                print(f"Error loading layout: {e}")
    
    async def _save_layout(self) -> None:
        """Save dashboard layout to file."""
        layout_file = Path(self.config.layout_file)
        layout_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(layout_file, 'w') as f:
                json.dump(self.layout.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving layout: {e}")


class DashboardWebSocketHandler:
    """WebSocket handler for real-time dashboard updates."""
    
    def __init__(self, dashboard_service: DashboardService):
        self.dashboard_service = dashboard_service
        self.connections: List[Any] = []  # WebSocket connections
    
    async def connect(self, websocket) -> None:
        """Handle new WebSocket connection."""
        self.connections.append(websocket)
        
        # Send initial dashboard data
        dashboard_data = await self.dashboard_service.get_dashboard_data()
        await websocket.send_json({
            "type": "dashboard_data",
            "data": dashboard_data
        })
    
    async def disconnect(self, websocket) -> None:
        """Handle WebSocket disconnection."""
        if websocket in self.connections:
            self.connections.remove(websocket)
    
    async def broadcast_update(self, widget_id: str, widget_data: Dict[str, Any]) -> None:
        """Broadcast widget update to all connected clients."""
        message = {
            "type": "widget_update",
            "widget_id": widget_id,
            "data": widget_data
        }
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.connections.remove(websocket)
