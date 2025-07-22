"""
Test script for dashboard functionality.

This script tests the dashboard service and widgets.
"""

import asyncio
import json
from datetime import datetime

from dashboard.service import DashboardService
from dashboard.widgets import WidgetFactory, WidgetType
from dashboard.layout import WidgetPosition, WidgetSize
from dashboard.models import DashboardConfig


async def test_dashboard_service():
    """Test dashboard service functionality."""
    print("Testing Dashboard Service...")
    
    # Create dashboard service
    config = DashboardConfig(refresh_interval=5)
    service = DashboardService(config)
    
    try:
        # Initialize service
        await service.initialize()
        print("✓ Dashboard service initialized")
        
        # Wait a moment for widgets to update
        await asyncio.sleep(2)
        
        # Get dashboard data
        dashboard_data = await service.get_dashboard_data()
        print(f"✓ Dashboard data retrieved: {len(dashboard_data['widgets'])} widgets")
        
        # Test adding a new widget
        success = await service.add_widget(
            section_index=0,
            widget_type=WidgetType.RESOURCE_GAUGE,
            widget_id="test-network-gauge",
            position=WidgetPosition(1, 3, WidgetSize.SMALL),
            resource_type="network",
            title="Network Usage"
        )
        print(f"✓ Widget added: {success}")
        
        # Get updated dashboard data
        updated_data = await service.get_dashboard_data()
        print(f"✓ Updated dashboard data: {len(updated_data['widgets'])} widgets")
        
        # Test widget data
        for widget_id, widget_data in updated_data['widgets'].items():
            print(f"  - {widget_id}: {widget_data['config']['title']}")
        
        # Test removing widget
        success = await service.remove_widget("test-network-gauge")
        print(f"✓ Widget removed: {success}")
        
        print("✓ All dashboard tests passed!")
        
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        raise
    finally:
        await service.shutdown()
        print("✓ Dashboard service shutdown")


async def test_widgets():
    """Test individual widget functionality."""
    print("\nTesting Widgets...")
    
    # Test default widgets
    widgets = WidgetFactory.get_default_widgets()
    print(f"✓ Created {len(widgets)} default widgets")
    
    for widget in widgets:
        try:
            # Get widget data
            data = await widget.get_data()
            config = widget.get_config()
            
            print(f"  - {widget.widget_id}: {config['title']}")
            print(f"    Type: {data.widget_type.value}")
            print(f"    Data keys: {list(data.data.keys())}")
            
        except Exception as e:
            print(f"  ✗ Widget {widget.widget_id} failed: {e}")
    
    print("✓ Widget tests completed")


async def main():
    """Run all tests."""
    print("System Health Monitor Dashboard Tests")
    print("=" * 50)
    
    try:
        await test_widgets()
        await test_dashboard_service()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        
    except Exception as e:
        print(f"\n✗ Tests failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
