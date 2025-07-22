#!/usr/bin/env python3
"""
Test script for the dashboard overview implementation.

This script tests the system overview dashboard functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only the core components without FastAPI dependencies
from dashboard.overview import SystemOverviewDashboard, OverviewWidgetManager
from dashboard.models import DashboardFilter, HealthStatus, ServiceStatus


async def test_system_overview():
    """Test system overview dashboard functionality."""
    print("🚀 Testing System Overview Dashboard")
    print("=" * 50)
    
    # Create dashboard instance
    dashboard = SystemOverviewDashboard()
    
    # Test system summary
    print("\n📊 Testing System Summary...")
    summary = await dashboard.get_system_summary()
    print(f"Total containers: {summary.total_containers}")
    print(f"Running containers: {summary.running_containers}")
    print(f"Overall health: {summary.overall_health.value}")
    print(f"Services count: {len(summary.services)}")
    print(f"Healthy services: {summary.healthy_services_count}")
    print(f"Warning services: {summary.warning_services_count}")
    print(f"Critical services: {summary.critical_services_count}")
    print(f"Uptime: {summary.uptime_percentage:.1f}%")
    
    # Test overview metrics
    print("\n📈 Testing Overview Metrics...")
    metrics = await dashboard.get_overview_metrics()
    print(f"Average CPU usage: {metrics.avg_cpu_usage:.1f}%")
    print(f"Average memory usage: {metrics.avg_memory_usage:.1f}%")
    print(f"Active alerts: {metrics.active_alerts}")
    
    # Test filtered services
    print("\n🔧 Testing Service Filtering...")
    
    # Test filter by health status
    warning_filter = DashboardFilter(health_status=[HealthStatus.WARNING])
    warning_services = await dashboard.get_filtered_services(warning_filter)
    print(f"Services with warnings: {len(warning_services)}")
    for service in warning_services:
        print(f"  - {service.name}: {service.overall_health.value}")
    
    # Test filter by service name
    db_filter = DashboardFilter(service_names=["database"])
    db_services = await dashboard.get_filtered_services(db_filter)
    print(f"Database services: {len(db_services)}")
    for service in db_services:
        print(f"  - {service.name}: {len(service.containers)} containers")
    
    # Test status indicators
    print("\n⚡ Testing Status Indicators...")
    indicators = await dashboard.get_status_indicators()
    print(f"Status indicators: {len(indicators)}")
    for indicator in indicators:
        print(f"  {indicator.icon} {indicator.status.value}: {indicator.message}")
        if indicator.details:
            print(f"    Details: {indicator.details}")
    
    # Test available filters
    print("\n🔍 Testing Available Filters...")
    filters = dashboard.get_available_filters()
    print(f"Available services: {filters['services']}")
    print(f"Health statuses: {filters['health_status']}")
    print(f"Container statuses: {filters['container_status']}")
    
    print("\n✅ System Overview Dashboard tests completed successfully!")


async def test_widget_manager():
    """Test overview widget manager functionality."""
    print("\n🎛️ Testing Overview Widget Manager")
    print("=" * 50)
    
    # Create dashboard and widget manager
    dashboard = SystemOverviewDashboard()
    widget_manager = OverviewWidgetManager(dashboard)
    
    # Test system status widget
    print("\n📊 Testing System Status Widget...")
    status_data = await widget_manager.get_widget_data("system-status")
    if status_data:
        print("System status widget data:")
        print(f"  Overall status: {status_data['data']['overall_status']}")
        print(f"  Total services: {status_data['data']['services']['total']}")
        print(f"  Healthy services: {status_data['data']['services']['healthy']}")
        print(f"  Total containers: {status_data['data']['containers']['total']}")
        print(f"  Running containers: {status_data['data']['containers']['running']}")
        print(f"  Active alerts: {status_data['data']['alerts']['active']}")
        print(f"  System uptime: {status_data['data']['uptime']}")
    
    # Test services list widget
    print("\n🔧 Testing Services List Widget...")
    services_data = await widget_manager.get_widget_data("services-list")
    if services_data:
        print("Services list widget data:")
        print(f"  Total services: {services_data['data']['total_count']}")
        print(f"  Healthy: {services_data['data']['healthy_count']}")
        print(f"  Warning: {services_data['data']['warning_count']}")
        print(f"  Critical: {services_data['data']['critical_count']}")
        print("  Services:")
        for service in services_data['data']['services'][:3]:  # Show first 3
            print(f"    - {service['name']}: {service['status']} ({service['containers']} containers)")
    
    # Test resource gauge widgets
    print("\n💻 Testing Resource Gauge Widgets...")
    for resource in ["cpu", "memory", "disk"]:
        widget_id = f"{resource}-gauge"
        widget_data = await widget_manager.get_widget_data(widget_id)
        if widget_data:
            data = widget_data['data']
            print(f"  {resource.upper()}: {data['current']:.1f}{data['unit']} (Status: {data['status']})")
    
    print("\n✅ Widget Manager tests completed successfully!")


async def test_color_coding():
    """Test color coding and status indicators."""
    print("\n🎨 Testing Color Coding and Status")
    print("=" * 50)
    
    dashboard = SystemOverviewDashboard()
    
    # Get status indicators to test color coding
    indicators = await dashboard.get_status_indicators()
    
    print("Status indicators with color coding:")
    for indicator in indicators:
        print(f"  {indicator.icon} {indicator.message}")
        print(f"    Status: {indicator.status.value}")
        print(f"    Color: {indicator.color}")
        if indicator.details:
            print(f"    Details: {indicator.details}")
        print()
    
    # Test service grouping with color coding
    services = await dashboard.get_filtered_services()
    print("Service health status:")
    for service in services:
        health_color = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.WARNING: "🟡", 
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.UNKNOWN: "⚪"
        }
        icon = health_color.get(service.overall_health, "⚪")
        print(f"  {icon} {service.name}: {service.overall_health.value}")
    
    print("\n✅ Color coding tests completed successfully!")


async def main():
    """Run all tests."""
    print("🧪 Starting Dashboard Overview Tests")
    print("=" * 60)
    
    try:
        await test_system_overview()
        await test_widget_manager()
        await test_color_coding()
        
        print("\n🎉 All tests passed successfully!")
        print("The system overview dashboard is ready for use.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)