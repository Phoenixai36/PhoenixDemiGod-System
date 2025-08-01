"""
Dashboard layout management.

This module provides layout management for the system health dashboard.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class WidgetSize(Enum):
    """Widget size options."""
    SMALL = "small"      # 1x1
    MEDIUM = "medium"    # 2x1
    LARGE = "large"      # 2x2
    FULL = "full"        # Full width


class WidgetPosition:
    """Position of a widget in the dashboard grid."""
    
    def __init__(self, row: int, col: int, size: WidgetSize = WidgetSize.MEDIUM):
        self.row = row
        self.col = col
        self.size = size
    
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


@dataclass
class LayoutSection:
    """Section of the dashboard layout."""
    title: str
    widgets: List[Tuple[str, WidgetPosition]] = field(default_factory=list)
    collapsed: bool = False
    
    def add_widget(self, widget_id: str, position: WidgetPosition) -> bool:
        """
        Add a widget to this section.
        
        Args:
            widget_id: ID of the widget to add
            position: Position of the widget
            
        Returns:
            True if widget was added, False if position overlaps with existing widget
        """
        # Check for overlaps
        for existing_id, existing_pos in self.widgets:
            if position.overlaps(existing_pos):
                return False
        
        self.widgets.append((widget_id, position))
        return True
    
    def remove_widget(self, widget_id: str) -> bool:
        """
        Remove a widget from this section.
        
        Args:
            widget_id: ID of the widget to remove
            
        Returns:
            True if widget was removed, False if not found
        """
        for i, (wid, _) in enumerate(self.widgets):
            if wid == widget_id:
                self.widgets.pop(i)
                return True
        return False


class DashboardLayout:
    """Layout manager for dashboard."""
    
    def __init__(self, columns: int = 4):
        self.columns = columns
        self.sections: List[LayoutSection] = []
        self.widgets: Dict[str, Any] = {}
    
    def add_section(self, title: str) -> LayoutSection:
        """
        Add a new section to the dashboard.
        
        Args:
            title: Section title
            
        Returns:
            The created section
        """
        section = LayoutSection(title)
        self.sections.append(section)
        return section
    
    def add_widget(self, section_index: int, widget_id: str, widget: Any, 
                  position: WidgetPosition) -> bool:
        """
        Add a widget to a section.
        
        Args:
            section_index: Index of the section to add to
            widget_id: ID for the widget
            widget: Widget instance
            position: Position of the widget
            
        Returns:
            True if widget was added, False if position overlaps or section not found
        """
        if section_index < 0 or section_index >= len(self.sections):
            return False
        
        section = self.sections[section_index]
        if section.add_widget(widget_id, position):
            self.widgets[widget_id] = widget
            return True
        return False
    
    def remove_widget(self, widget_id: str) -> bool:
        """
        Remove a widget from the dashboard.
        
        Args:
            widget_id: ID of the widget to remove
            
        Returns:
            True if widget was removed, False if not found
        """
        if widget_id not in self.widgets:
            return False
        
        # Remove from section
        for section in self.sections:
            if section.remove_widget(widget_id):
                break
        
        # Remove from widgets dict
        del self.widgets[widget_id]
        return True
    
    def get_widget(self, widget_id: str) -> Optional[Any]:
        """
        Get a widget by ID.
        
        Args:
            widget_id: ID of the widget to get
            
        Returns:
            Widget instance or None if not found
        """
        return self.widgets.get(widget_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert layout to dictionary for serialization.
        
        Returns:
            Dictionary representation of layout
        """
        return {
            "columns": self.columns,
            "sections": [
                {
                    "title": section.title,
                    "collapsed": section.collapsed,
                    "widgets": [
                        {
                            "id": widget_id,
                            "row": position.row,
                            "col": position.col,
                            "size": position.size.value
                        }
                        for widget_id, position in section.widgets
                    ]
                }
                for section in self.sections
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], widgets: Dict[str, Any]) -> 'DashboardLayout':
        """
        Create layout from dictionary.
        
        Args:
            data: Dictionary representation of layout
            widgets: Dictionary of widget instances by ID
            
        Returns:
            DashboardLayout instance
        """
        layout = cls(columns=data.get("columns", 4))
        layout.widgets = widgets
        
        for section_data in data.get("sections", []):
            section = layout.add_section(section_data["title"])
            section.collapsed = section_data.get("collapsed", False)
            
            for widget_data in section_data.get("widgets", []):
                widget_id = widget_data["id"]
                position = WidgetPosition(
                    row=widget_data["row"],
                    col=widget_data["col"],
                    size=WidgetSize(widget_data.get("size", "medium"))
                )
                section.add_widget(widget_id, position)
        
        return layout
    
    def create_default_layout(self) -> None:
        """Create default dashboard layout."""
        # System overview section
        overview_section = self.add_section("System Overview")
        
        # Service status section
        services_section = self.add_section("Services")
        
        # Resource usage section
        resources_section = self.add_section("Resource Usage")
        
        # Events section
        events_section = self.add_section("Recent Events")
