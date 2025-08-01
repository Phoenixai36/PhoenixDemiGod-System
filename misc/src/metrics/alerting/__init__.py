"""
Alerting system for metrics monitoring.

This module provides a comprehensive alerting system that can:
- Define alert rules based on metric conditions
- Evaluate metrics against rules to generate alerts
- Manage alert lifecycle (firing, resolving, acknowledging, silencing)
- Send notifications through multiple channels (email, webhook, Slack, etc.)
- Provide a complete alert management interface
"""

from .alert import Alert, AlertSeverity, AlertStatus
from .alert_rule import (
    AlertCondition,
    AlertRule,
    AlertRuleEngine,
    create_cpu_usage_rule,
    create_memory_usage_rule,
    create_disk_usage_rule
)
from .alert_manager import AlertManager, AlertManagerConfig
from .notification import (
    NotificationChannel,
    NotificationManager,
    NotificationConfig,
    EmailNotificationChannel,
    EmailConfig,
    WebhookNotificationChannel,
    WebhookConfig,
    SlackNotificationChannel,
    SlackConfig,
    LogNotificationChannel
)

__all__ = [
    # Core alert types
    'Alert',
    'AlertSeverity',
    'AlertStatus',
    
    # Alert rules
    'AlertCondition',
    'AlertRule',
    'AlertRuleEngine',
    'create_cpu_usage_rule',
    'create_memory_usage_rule',
    'create_disk_usage_rule',
    
    # Alert management
    'AlertManager',
    'AlertManagerConfig',
    
    # Notifications
    'NotificationChannel',
    'NotificationManager',
    'NotificationConfig',
    'EmailNotificationChannel',
    'EmailConfig',
    'WebhookNotificationChannel',
    'WebhookConfig',
    'SlackNotificationChannel',
    'SlackConfig',
    'LogNotificationChannel'
]