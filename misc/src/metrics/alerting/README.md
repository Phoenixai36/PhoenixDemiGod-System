# Alerting System

A comprehensive alerting system for monitoring metrics and sending notifications when thresholds are exceeded.

## Features

- **Rule-based alerting**: Define alert rules with flexible conditions
- **Multiple notification channels**: Email, Slack, webhooks, and custom channels
- **Alert lifecycle management**: Fire, acknowledge, silence, and resolve alerts
- **Throttling and duration controls**: Prevent alert spam with configurable delays
- **Auto-resolution**: Automatically resolve alerts when conditions improve
- **Rich metadata**: Labels, annotations, and context for alerts
- **Background processing**: Continuous evaluation and notification sending

## Components

### Core Components

1. **Alert**: Represents an individual alert instance
2. **AlertRule**: Defines conditions that trigger alerts
3. **AlertManager**: Orchestrates the entire alerting system
4. **NotificationManager**: Handles sending notifications through various channels

### Alert Lifecycle

```
PENDING → FIRING → RESOLVED
    ↓         ↓
SILENCED  ACKNOWLEDGED
```

- **PENDING**: Condition detected but not yet firing (waiting for duration)
- **FIRING**: Alert is actively firing and notifications are sent
- **RESOLVED**: Alert condition no longer met and alert is resolved
- **ACKNOWLEDGED**: Alert has been acknowledged by a user
- **SILENCED**: Alert is temporarily silenced (no notifications)

## Quick Start

### Basic Setup

```python
import asyncio
from datetime import timedelta
from src.metrics.alerting import (
    AlertManager, AlertManagerConfig,
    create_cpu_usage_rule, create_memory_usage_rule,
    LogNotificationChannel
)
from src.metrics.collectors.cpu_collector import CPUCollector

async def basic_alerting():
    # Create alert manager
    config = AlertManagerConfig(
        evaluation_interval=timedelta(seconds=30),
        retention_period=timedelta(days=7)
    )
    alert_manager = AlertManager(config)
    
    # Add metrics collector
    alert_manager.add_collector("cpu", CPUCollector())
    
    # Add notification channel
    alert_manager.add_notification_channel(LogNotificationChannel())
    
    # Add alert rules
    cpu_rule = create_cpu_usage_rule(threshold=80.0, duration_minutes=5)
    memory_rule = create_memory_usage_rule(threshold=85.0, duration_minutes=3)
    
    alert_manager.add_rule(cpu_rule)
    alert_manager.add_rule(memory_rule)
    
    # Start monitoring
    await alert_manager.start()
    
    # Let it run
    await asyncio.sleep(300)  # 5 minutes
    
    # Stop monitoring
    await alert_manager.stop()

# Run the example
asyncio.run(basic_alerting())
```

### Custom Alert Rules

```python
from src.metrics.alerting import AlertRule, AlertCondition, AlertSeverity
from datetime import timedelta

# Create a custom rule
custom_rule = AlertRule(
    id="high_disk_usage",
    name="High Disk Usage Alert",
    description="Disk usage is critically high",
    conditions=[
        AlertCondition(
            metric_name="disk_usage_percent",
            operator="gt",
            threshold=90.0,
            labels_match={"mount": "/", "host": "server1"}
        )
    ],
    severity=AlertSeverity.CRITICAL,
    for_duration=timedelta(minutes=2),
    throttle_duration=timedelta(minutes=15),
    auto_resolve=True,
    resolve_timeout=timedelta(minutes=5),
    labels={"component": "storage", "team": "infrastructure"},
    annotations={
        "runbook": "https://wiki.company.com/disk-cleanup",
        "dashboard": "https://grafana.company.com/disk-dashboard"
    }
)

alert_manager.add_rule(custom_rule)
```

## Notification Channels

### Email Notifications

```python
from src.metrics.alerting import EmailNotificationChannel, EmailConfig

email_config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="alerts@company.com",
    password="app_password",
    use_tls=True,
    from_address="alerts@company.com",
    to_addresses=["admin@company.com", "ops@company.com"],
    subject_template="[{severity}] {name}",
    body_template="""
Alert: {name}
Description: {description}
Severity: {severity}
Metric: {metric_name} = {metric_value}
Threshold: {threshold}
Time: {created_at}
Labels: {labels}

Please investigate immediately.
    """
)

email_channel = EmailNotificationChannel("email", "Email Alerts", email_config)
alert_manager.add_notification_channel(email_channel)
```

### Slack Notifications

```python
from src.metrics.alerting import SlackNotificationChannel, SlackConfig

slack_config = SlackConfig(
    webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    channel="#alerts",
    username="AlertBot",
    icon_emoji=":warning:",
    color_map={
        "info": "#36a64f",
        "warning": "#ff9500", 
        "error": "#ff0000",
        "critical": "#8b0000"
    }
)

slack_channel = SlackNotificationChannel("slack", "Slack Alerts", slack_config)
alert_manager.add_notification_channel(slack_channel)
```

### Webhook Notifications

```python
from src.metrics.alerting import WebhookNotificationChannel, WebhookConfig

webhook_config = WebhookConfig(
    url="https://api.company.com/alerts",
    method="POST",
    headers={
        "Authorization": "Bearer your-api-token",
        "Content-Type": "application/json"
    },
    payload_template={
        "alert_id": "{id}",
        "name": "{name}",
        "severity": "{severity}",
        "metric": "{metric_name}",
        "value": "{metric_value}",
        "threshold": "{threshold}",
        "timestamp": "{created_at}",
        "labels": "{labels}"
    }
)

webhook_channel = WebhookNotificationChannel("webhook", "API Alerts", webhook_config)
alert_manager.add_notification_channel(webhook_channel)
```

## Alert Management

### Viewing Alerts

```python
# Get active alerts
active_alerts = alert_manager.get_active_alerts()
for alert in active_alerts:
    print(f"Alert: {alert.name} - {alert.severity.value}")

# Get alerts by severity
critical_alerts = alert_manager.get_active_alerts(AlertSeverity.CRITICAL)

# Get resolved alerts
resolved_alerts = alert_manager.get_resolved_alerts(limit=10)

# Get specific alert
alert = alert_manager.get_alert("alert-id-here")
```

### Managing Alert State

```python
# Acknowledge an alert
alert_manager.acknowledge_alert("alert-id")

# Silence an alert for 1 hour
alert_manager.silence_alert("alert-id", duration=timedelta(hours=1))

# Unsilence an alert
alert_manager.unsilence_alert("alert-id")

# Get alert manager statistics
stats = alert_manager.get_stats()
print(f"Active alerts: {stats['active_alerts']}")
print(f"Rules: {stats['rules_count']}")
```

## Alert Conditions

### Operators

- `gt`: Greater than
- `lt`: Less than
- `eq`: Equal to
- `ne`: Not equal to
- `gte`: Greater than or equal to
- `lte`: Less than or equal to
- `contains`: String contains
- `regex`: Regular expression match

### Examples

```python
# Numeric comparisons
AlertCondition("cpu_usage", "gt", 80.0)
AlertCondition("memory_free_mb", "lt", 1000)
AlertCondition("response_time_ms", "gte", 500)

# String matching
AlertCondition("service_status", "eq", "down")
AlertCondition("log_message", "contains", "ERROR")
AlertCondition("error_type", "regex", r"timeout|connection")

# With label matching
AlertCondition(
    "disk_usage_percent", 
    "gt", 
    90.0,
    labels_match={"mount": "/var", "host": "web-server"}
)
```

## Standard Rules

The system provides pre-built rules for common scenarios:

```python
from src.metrics.alerting import (
    create_cpu_usage_rule,
    create_memory_usage_rule,
    create_disk_usage_rule
)

# CPU usage > 80% for 5 minutes
cpu_rule = create_cpu_usage_rule(threshold=80.0, duration_minutes=5)

# Memory usage > 85% for 3 minutes  
memory_rule = create_memory_usage_rule(threshold=85.0, duration_minutes=3)

# Disk usage > 90% for 1 minute
disk_rule = create_disk_usage_rule(threshold=90.0, duration_minutes=1)
```

## Configuration

### AlertManagerConfig

```python
from src.metrics.alerting import AlertManagerConfig
from datetime import timedelta

config = AlertManagerConfig(
    evaluation_interval=timedelta(seconds=30),  # How often to check rules
    retention_period=timedelta(days=7),         # How long to keep resolved alerts
    max_alerts=1000,                            # Maximum number of alerts to store
    enable_auto_resolve=True,                   # Enable automatic resolution
    default_resolve_timeout=timedelta(minutes=5) # Default resolution timeout
)
```

### NotificationConfig

```python
from src.metrics.alerting import NotificationConfig

config = NotificationConfig(
    enabled=True,           # Enable/disable notifications
    retry_attempts=3,       # Number of retry attempts
    retry_delay=5.0,        # Delay between retries (seconds)
    timeout=30.0           # Request timeout (seconds)
)
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_alert.py tests/test_alert_rule.py -v
```

## Examples

See the `example.py` file for comprehensive examples including:

- Basic alerting setup
- Advanced multi-channel notifications
- Alert lifecycle demonstration
- Custom rule creation
- Alert management operations

Run the examples:

```bash
python -m src.metrics.alerting.example
```

## Best Practices

### Rule Design

1. **Use appropriate durations**: Avoid false positives with `for_duration`
2. **Set throttling**: Prevent alert spam with `throttle_duration`
3. **Add context**: Use labels and annotations for debugging
4. **Choose severity wisely**: Reserve CRITICAL for truly critical issues

### Notification Strategy

1. **Multiple channels**: Use different channels for different severities
2. **Escalation**: Route critical alerts to immediate notification channels
3. **Grouping**: Use labels to group related alerts
4. **Rate limiting**: Configure throttling to prevent notification storms

### Performance

1. **Collector efficiency**: Ensure metric collectors are performant
2. **Rule complexity**: Keep rule conditions simple and fast
3. **Retention**: Configure appropriate retention periods
4. **Monitoring**: Monitor the alert manager itself

### Operational

1. **Runbooks**: Always include runbook links in annotations
2. **Dashboards**: Link to relevant dashboards for context
3. **Testing**: Test alert rules in non-production environments
4. **Documentation**: Document custom rules and their purpose