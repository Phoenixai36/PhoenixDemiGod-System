"""
Example usage of the alerting system.

This script demonstrates how to set up and use the complete alerting system
with rules, notifications, and alert management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from ..models import MetricValue
from ..collector_interface import MetricsCollector
from ..collectors.cpu_collector import CPUCollector
from ..collectors.memory_collector import MemoryCollector
from .alert_manager import AlertManager, AlertManagerConfig
from .alert_rule import create_cpu_usage_rule, create_memory_usage_rule, AlertRule, AlertCondition
from .alert import AlertSeverity
from .notification import (
    LogNotificationChannel,
    EmailNotificationChannel,
    EmailConfig,
    WebhookNotificationChannel,
    WebhookConfig,
    SlackNotificationChannel,
    SlackConfig
)


class MockHighCPUCollector(MetricsCollector):
    """Mock collector that simulates high CPU usage."""
    
    def __init__(self):
        self.counter = 0
    
    async def collect_metrics(self) -> List[MetricValue]:
        """Collect mock high CPU metrics."""
        self.counter += 1
        
        # Simulate high CPU usage that triggers alerts
        cpu_value = 85.0 + (self.counter % 10)  # Values between 85-95%
        
        return [
            MetricValue(
                name="cpu_usage_percent",
                value=cpu_value,
                timestamp=datetime.now(),
                labels={"host": "server1", "env": "production"}
            ),
            MetricValue(
                name="memory_usage_percent",
                value=70.0,  # Normal memory usage
                timestamp=datetime.now(),
                labels={"host": "server1", "env": "production"}
            )
        ]
    
    def get_name(self) -> str:
        return "mock_high_cpu"


async def setup_basic_alerting():
    """Set up basic alerting with log notifications."""
    print("=== Basic Alerting Example ===")
    
    # Create alert manager with custom config
    config = AlertManagerConfig(
        evaluation_interval=timedelta(seconds=10),  # Check every 10 seconds
        retention_period=timedelta(hours=1),        # Keep alerts for 1 hour
        max_alerts=100
    )
    alert_manager = AlertManager(config)
    
    # Add collectors
    alert_manager.add_collector("cpu", CPUCollector())
    alert_manager.add_collector("memory", MemoryCollector())
    
    # Add notification channel (log-based for this example)
    log_channel = LogNotificationChannel()
    alert_manager.add_notification_channel(log_channel)
    
    # Add standard alert rules
    cpu_rule = create_cpu_usage_rule(threshold=80.0, duration_minutes=1)
    memory_rule = create_memory_usage_rule(threshold=85.0, duration_minutes=2)
    
    alert_manager.add_rule(cpu_rule)
    alert_manager.add_rule(memory_rule)
    
    # Start alert manager
    await alert_manager.start()
    
    print("Alert manager started. Monitoring for 30 seconds...")
    
    # Let it run for a while
    await asyncio.sleep(30)
    
    # Check stats
    stats = alert_manager.get_stats()
    print(f"Alert Manager Stats: {stats}")
    
    # List active alerts
    active_alerts = alert_manager.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")
    for alert in active_alerts:
        print(f"  - {alert.name}: {alert.metric_name}={alert.metric_value} (severity: {alert.severity.value})")
    
    # Stop alert manager
    await alert_manager.stop()
    print("Alert manager stopped.")


async def setup_advanced_alerting():
    """Set up advanced alerting with multiple notification channels."""
    print("\n=== Advanced Alerting Example ===")
    
    # Create alert manager
    alert_manager = AlertManager()
    
    # Add mock collector that generates high CPU
    alert_manager.add_collector("mock_cpu", MockHighCPUCollector())
    
    # Add multiple notification channels
    
    # 1. Log channel
    log_channel = LogNotificationChannel()
    alert_manager.add_notification_channel(log_channel)
    
    # 2. Email channel (configured but won't actually send)
    email_config = EmailConfig(
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="alerts@example.com",
        password="password",
        from_address="alerts@example.com",
        to_addresses=["admin@example.com", "ops@example.com"],
        subject_template="[{severity}] {name} - {metric_name}",
        body_template="""
Alert Details:
- Name: {name}
- Description: {description}
- Severity: {severity}
- Metric: {metric_name} = {metric_value}
- Threshold: {threshold}
- Condition: {metric_name} {condition} {threshold}
- Time: {created_at}
- Host: {labels}

Please investigate immediately.
        """
    )
    email_channel = EmailNotificationChannel("email", "Email Alerts", email_config)
    alert_manager.add_notification_channel(email_channel)
    
    # 3. Webhook channel
    webhook_config = WebhookConfig(
        url="https://hooks.example.com/alerts",
        headers={"Authorization": "Bearer token123"},
        payload_template={
            "alert_name": "{name}",
            "severity": "{severity}",
            "metric": "{metric_name}",
            "value": "{metric_value}",
            "threshold": "{threshold}",
            "timestamp": "{created_at}",
            "environment": "production"
        }
    )
    webhook_channel = WebhookNotificationChannel("webhook", "Webhook Alerts", webhook_config)
    alert_manager.add_notification_channel(webhook_channel)
    
    # 4. Slack channel
    slack_config = SlackConfig(
        webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        channel="#alerts",
        username="AlertBot",
        icon_emoji=":warning:"
    )
    slack_channel = SlackNotificationChannel("slack", "Slack Alerts", slack_config)
    alert_manager.add_notification_channel(slack_channel)
    
    # Add custom alert rules
    
    # High CPU rule with short duration for demo
    high_cpu_rule = AlertRule(
        id="demo_high_cpu",
        name="Demo High CPU Usage",
        description="CPU usage is critically high",
        conditions=[
            AlertCondition("cpu_usage_percent", "gt", 80.0)
        ],
        severity=AlertSeverity.CRITICAL,
        for_duration=timedelta(seconds=5),  # Short duration for demo
        throttle_duration=timedelta(minutes=2),
        labels={"component": "cpu", "environment": "production"},
        annotations={
            "runbook": "https://wiki.example.com/runbooks/high-cpu",
            "dashboard": "https://grafana.example.com/cpu-dashboard"
        }
    )
    
    # Custom application error rule
    app_error_rule = AlertRule(
        id="app_errors",
        name="Application Errors",
        description="Application error rate is too high",
        conditions=[
            AlertCondition("error_rate_percent", "gt", 5.0)
        ],
        severity=AlertSeverity.ERROR,
        for_duration=timedelta(minutes=1),
        throttle_duration=timedelta(minutes=5),
        labels={"component": "application", "type": "error_rate"}
    )
    
    alert_manager.add_rule(high_cpu_rule)
    alert_manager.add_rule(app_error_rule)
    
    # Start alert manager
    await alert_manager.start()
    
    print("Advanced alert manager started. Running for 60 seconds...")
    print("This will generate high CPU alerts to demonstrate the system.")
    
    # Let it run and generate some alerts
    for i in range(6):  # Run for 60 seconds total
        await asyncio.sleep(10)
        
        # Show current status
        stats = alert_manager.get_stats()
        active_alerts = alert_manager.get_active_alerts()
        
        print(f"\n--- Status Update {i+1} ---")
        print(f"Active alerts: {stats['active_alerts']}")
        print(f"Resolved alerts: {stats['resolved_alerts']}")
        
        if active_alerts:
            print("Current active alerts:")
            for alert in active_alerts[:3]:  # Show first 3
                print(f"  - {alert.name}: {alert.metric_name}={alert.metric_value}")
        
        # Demonstrate alert management
        if i == 2 and active_alerts:  # After 30 seconds
            alert_id = active_alerts[0].id
            print(f"Acknowledging alert: {alert_id}")
            alert_manager.acknowledge_alert(alert_id)
        
        if i == 4 and len(active_alerts) > 1:  # After 50 seconds
            alert_id = active_alerts[1].id
            print(f"Silencing alert for 30 seconds: {alert_id}")
            alert_manager.silence_alert(alert_id, duration=timedelta(seconds=30))
    
    # Final stats
    print("\n--- Final Stats ---")
    stats = alert_manager.get_stats()
    print(f"Final stats: {stats}")
    
    # Show resolved alerts
    resolved_alerts = alert_manager.get_resolved_alerts(limit=5)
    print(f"Recent resolved alerts: {len(resolved_alerts)}")
    for alert in resolved_alerts:
        print(f"  - {alert.name}: resolved at {alert.resolved_at}")
    
    # Stop alert manager
    await alert_manager.stop()
    print("Advanced alert manager stopped.")


async def demonstrate_alert_lifecycle():
    """Demonstrate the complete alert lifecycle."""
    print("\n=== Alert Lifecycle Demo ===")
    
    alert_manager = AlertManager()
    
    # Add mock collector
    mock_collector = MockHighCPUCollector()
    alert_manager.add_collector("mock", mock_collector)
    
    # Add log notification
    alert_manager.add_notification_channel(LogNotificationChannel())
    
    # Add a rule with very short duration for demo
    quick_rule = AlertRule(
        id="quick_demo",
        name="Quick Demo Alert",
        description="Quick alert for demonstration",
        conditions=[AlertCondition("cpu_usage_percent", "gt", 80.0)],
        severity=AlertSeverity.WARNING,
        for_duration=timedelta(seconds=2),
        auto_resolve=True,
        resolve_timeout=timedelta(seconds=5)
    )
    alert_manager.add_rule(quick_rule)
    
    await alert_manager.start()
    
    print("Demonstrating alert lifecycle...")
    
    # Phase 1: Alert detection and firing
    print("\nPhase 1: Waiting for alert to fire...")
    await asyncio.sleep(8)  # Wait for alert to fire
    
    active_alerts = alert_manager.get_active_alerts()
    if active_alerts:
        alert = active_alerts[0]
        print(f"Alert fired: {alert.name} (Status: {alert.status.value})")
        
        # Phase 2: Acknowledge alert
        print("\nPhase 2: Acknowledging alert...")
        alert_manager.acknowledge_alert(alert.id)
        print(f"Alert acknowledged (Status: {alert.status.value})")
        
        # Phase 3: Silence alert
        print("\nPhase 3: Silencing alert for 10 seconds...")
        alert_manager.silence_alert(alert.id, duration=timedelta(seconds=10))
        print(f"Alert silenced (Status: {alert.status.value})")
        
        await asyncio.sleep(5)
        
        # Phase 4: Unsilence alert
        print("\nPhase 4: Unsilencing alert...")
        alert_manager.unsilence_alert(alert.id)
        print(f"Alert unsilenced (Status: {alert.status.value})")
    
    await alert_manager.stop()
    print("Alert lifecycle demo completed.")


async def main():
    """Main example function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("System Health Monitor - Alerting System Examples")
    print("=" * 50)
    
    try:
        # Run basic example
        await setup_basic_alerting()
        
        # Run advanced example
        await setup_advanced_alerting()
        
        # Run lifecycle demo
        await demonstrate_alert_lifecycle()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user.")
    except Exception as e:
        print(f"Error running examples: {str(e)}")
        logging.exception("Error in alerting examples")


if __name__ == "__main__":
    asyncio.run(main())