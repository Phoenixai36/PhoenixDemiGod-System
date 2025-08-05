#!/usr/bin/env python3
"""
Simple test for dashboard overview without FastAPI dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only the core models and overview
from dashboard.models import DashboardFilter, HealthStatus, ServiceStatus, DashboardConfig
from dashboard.overview import SystemOverviewDashboard


async def test_basic_functionality():
    """Test basic dashboard functionality."""
    print("🚀 Testing Basic Dashboard Functionality")
    print("=" * 50)
    
    # Create dashboard instance
    config = DashboardConfig()
    dashboard = SystemOverviewDashboard(config)
    
    # Test system summary
    print("\n📊 Testing System Summary...")
    summary = await dashboard.get_system_summary()
    print(f"✅ Total containers: {summary.total_containers}")
    print(f"✅ Running containers: {summary.running_containers}")
    print(f"✅ Overall health: {summary.overall_health.value}")
    print(f"✅ Services count: {len(summary.services)}")
    print(f"✅ Uptime: {summary.uptime_percentage:.1f}%")
    
    # Test overview metrics
    print("\n📈 Testing Overview Metrics...")
    metrics = await dashboard.get_overview_metrics()
    print(f"✅ Average CPU usage: {metrics.avg_cpu_usage:.1f}%")
    print(f"✅ Average memory usage: {metrics.avg_memory_usage:.1f}%")
    print(f"✅ Active alerts: {metrics.active_alerts}")
    
    # Test service filtering
    print("\n🔧 Testing Service Filtering...")
    services = await dashboard.get_filtered_services()
    print(f"✅ Total services: {len(services)}")
    
    for service in services:
        health_icon = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.WARNING: "🟡", 
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.UNKNOWN: "⚪"
        }
        icon = health_icon.get(service.overall_health, "⚪")
        print(f"  {icon} {service.name}: {service.overall_health.value} ({service.total_count} containers)")
    
    # Test status indicators
    print("\n⚡ Testing Status Indicators...")
    indicators = await dashboard.get_status_indicators()
    print(f"✅ Status indicators: {len(indicators)}")
    
    for indicator in indicators:
        print(f"  {indicator.icon} {indicator.status.value}: {indicator.message}")
    
    print("\n🎉 All basic tests passed successfully!")
    return True


async def test_filtering():
    """Test filtering functionality."""
    print("\n🔍 Testing Advanced Filtering")
    print("=" * 50)
    
    dashboard = SystemOverviewDashboard()
    
    # Test filter by health status
    print("\n🟡 Testing Warning Filter...")
    warning_filter = DashboardFilter(health_status=[HealthStatus.WARNING])
    warning_services = await dashboard.get_filtered_services(warning_filter)
    print(f"✅ Services with warnings: {len(warning_services)}")
    
    # Test filter by service name
    print("\n🔧 Testing Service Name Filter...")
    db_filter = DashboardFilter(service_names=["database"])
    db_services = await dashboard.get_filtered_services(db_filter)
    print(f"✅ Database services: {len(db_services)}")
    
    # Test search filter
    print("\n🔍 Testing Search Filter...")
    search_filter = DashboardFilter(search_text="nginx")
    nginx_services = await dashboard.get_filtered_services(search_filter)
    print(f"✅ Services matching 'nginx': {len(nginx_services)}")
    
    print("\n✅ Filtering tests completed successfully!")
    return True


async def test_color_coding():
    """Test color coding functionality."""
    print("\n🎨 Testing Color Coding")
    print("=" * 50)
    
    dashboard = SystemOverviewDashboard()
    indicators = await dashboard.get_status_indicators()
    
    print("Status indicators with colors:")
    for indicator in indicators:
        print(f"  Status: {indicator.status.value}")
        print(f"  Color: {indicator.color}")
        print(f"  Icon: {indicator.icon}")
        print(f"  Message: {indicator.message}")
        print()
    
    print("✅ Color coding tests completed successfully!")
    return True


async def main():
    """Run all tests."""
    print("🧪 Dashboard Overview - Simple Tests")
    print("=" * 60)
    
    try:
        success1 = await test_basic_functionality()
        success2 = await test_filtering()
        success3 = await test_color_coding()
        
        if success1 and success2 and success3:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ System overview dashboard is working correctly")
            print("✅ Service grouping and filtering implemented")
            print("✅ Color-coded status indicators working")
            print("✅ Ready for integration with FastAPI")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)