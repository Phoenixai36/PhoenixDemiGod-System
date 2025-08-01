"""
Notification system for alerts.

This module provides notification channels and routing for alert notifications.
"""

import logging
import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .alert_models import Alert, AlertSeverity


@dataclass
class NotificationTemplate:
    """Template for formatting alert notifications."""
    name: str
    subject_template: str
    body_template: str
    format_type: str = "text"  # text, html, json
    
    def render(self, alert: Alert, additional_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Render the template with alert data."""
        data = self._prepare_template_data(alert, additional_data or {})
        
        subject = self._render_template(self.subject_template, data)
        body = self._render_template(self.body_template, data)
        
        return {
            "subject": subject,
            "body": body,
            "format": self.format_type
        }
    
    def _prepare_template_data(self, alert: Alert, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for template rendering."""
        data = {
            "alert_id": alert.alert_id,
            "rule_name": alert.rule_name,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "message": alert.message,
            "description": alert.description,
            "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": alert.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(alert.get_duration()) if alert.get_duration() else "N/A",
            "labels": alert.labels,
            "annotations": alert.annotations,
            **additional_data
        }
        
        # Add metric summary if available
        if alert.context:
            metric_summary = alert.context.get_metric_summary()
            data["metrics"] = metric_summary
            data["metric_count"] = len(alert.context.triggering_metrics)
        
        return data
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Simple template rendering with variable substitution."""
        rendered = template
        
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, dict):
                # Handle nested dictionaries
                for nested_key, nested_value in value.items():
                    nested_placeholder = f"{{{key}.{nested_key}}}"
                    rendered = rendered.replace(nested_placeholder, str(nested_value))
            else:
                rendered = rendered.replace(placeholder, str(value))
        
        return rendered


class NotificationChannel(ABC):
    """Base class for notification channels."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"notification.{name}")
        self.enabled = config.get("enabled", True)
        
        # Statistics
        self.stats = {
            "notifications_sent": 0,
            "notifications_failed": 0,
            "last_notification_time": None,
            "last_error": None
        }
    
    @abstractmethod
    async def send_notification(self, alert: Alert, template: NotificationTemplate = None) -> bool:
        """Send a notification for an alert."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if the channel is enabled."""
        return self.enabled
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get channel statistics."""
        stats = self.stats.copy()
        if stats["last_notification_time"]:
            stats["last_notification_time"] = stats["last_notification_time"].isoformat()
        return stats
    
    def _record_success(self) -> None:
        """Record successful notification."""
        self.stats["notifications_sent"] += 1
        self.stats["last_notification_time"] = datetime.now()
    
    def _record_failure(self, error: str) -> None:
        """Record failed notification."""
        self.stats["notifications_failed"] += 1
        self.stats["last_error"] = error
        self.logger.error(f"Notification failed: {error}")


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Email configuration
        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_username = config.get("smtp_username")
        self.smtp_password = config.get("smtp_password")
        self.use_tls = config.get("use_tls", True)
        self.from_address = config.get("from_address", "alerts@example.com")
        self.to_addresses = config.get("to_addresses", [])
        
        if not self.to_addresses:
            self.logger.warning("No recipient addresses configured for email channel")
    
    async def send_notification(self, alert: Alert, template: NotificationTemplate = None) -> bool:
        """Send email notification."""
        if not self.is_enabled() or not self.to_addresses:
            return False
        
        try:
            # Use default template if none provided
            if template is None:
                template = self._get_default_template()
            
            # Render template
            rendered = template.render(alert)
            
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = ", ".join(self.to_addresses)
            msg["Subject"] = rendered["subject"]
            
            # Add body
            if rendered["format"] == "html":
                msg.attach(MIMEText(rendered["body"], "html"))
            else:
                msg.attach(MIMEText(rendered["body"], "plain"))
            
            # Send email
            await self._send_email(msg)
            
            self._record_success()
            self.logger.info(f"Email notification sent for alert {alert.alert_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send email notification: {str(e)}"
            self._record_failure(error_msg)
            return False
    
    async def _send_email(self, msg: MIMEMultipart) -> None:
        """Send email using SMTP."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_email_sync, msg)
    
    def _send_email_sync(self, msg: MIMEMultipart) -> None:
        """Synchronous email sending."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
    
    def _get_default_template(self) -> NotificationTemplate:
        """Get default email template."""
        return NotificationTemplate(
            name="default_email",
            subject_template="[{severity}] {rule_name}",
            body_template="""Alert: {rule_name}
Severity: {severity}
Status: {status}
Message: {message}
Description: {description}

Created: {created_at}
Duration: {duration}

Alert ID: {alert_id}
""",
            format_type="text"
        )


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        if not AIOHTTP_AVAILABLE:
            self.logger.error("aiohttp is required for Slack notifications")
            self.enabled = False
            return
        
        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel")
        self.username = config.get("username", "AlertBot")
        self.icon_emoji = config.get("icon_emoji", ":warning:")
        
        if not self.webhook_url:
            self.logger.error("No webhook URL configured for Slack channel")
            self.enabled = False
    
    async def send_notification(self, alert: Alert, template: NotificationTemplate = None) -> bool:
        """Send Slack notification."""
        if not self.is_enabled():
            return False
        
        try:
            # Create Slack message
            message = self._create_slack_message(alert, template)
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    if response.status == 200:
                        self._record_success()
                        self.logger.info(f"Slack notification sent for alert {alert.alert_id}")
                        return True
                    else:
                        error_msg = f"Slack API returned status {response.status}"
                        self._record_failure(error_msg)
                        return False
                        
        except Exception as e:
            error_msg = f"Failed to send Slack notification: {str(e)}"
            self._record_failure(error_msg)
            return False
    
    def _create_slack_message(self, alert: Alert, template: NotificationTemplate = None) -> Dict[str, Any]:
        """Create Slack message payload."""
        # Determine color based on severity
        color_map = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "danger"
        }
        color = color_map.get(alert.severity, "warning")
        
        # Create attachment
        attachment = {
            "color": color,
            "title": f"{alert.severity.value.upper()}: {alert.rule_name}",
            "text": alert.message,
            "fields": [
                {
                    "title": "Status",
                    "value": alert.status.value,
                    "short": True
                },
                {
                    "title": "Duration",
                    "value": str(alert.get_duration()) if alert.get_duration() else "N/A",
                    "short": True
                },
                {
                    "title": "Created",
                    "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "short": True
                }
            ],
            "footer": f"Alert ID: {alert.alert_id}",
            "ts": int(alert.created_at.timestamp())
        }
        
        # Add metric information if available
        if alert.context:
            metric_summary = alert.context.get_metric_summary()
            if metric_summary:
                metric_text = []
                for name, stats in metric_summary.items():
                    metric_text.append(f"{name}: {stats['latest']}")
                
                attachment["fields"].append({
                    "title": "Metrics",
                    "value": "\n".join(metric_text),
                    "short": False
                })
        
        message = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [attachment]
        }
        
        if self.channel:
            message["channel"] = self.channel
        
        return message


class WebhookNotificationChannel(NotificationChannel):
    """Generic webhook notification channel."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        if not AIOHTTP_AVAILABLE:
            self.logger.error("aiohttp is required for webhook notifications")
            self.enabled = False
            return
        
        self.webhook_url = config.get("webhook_url")
        self.headers = config.get("headers", {})
        self.method = config.get("method", "POST").upper()
        self.timeout = config.get("timeout", 30)
        
        if not self.webhook_url:
            self.logger.error("No webhook URL configured")
            self.enabled = False
    
    async def send_notification(self, alert: Alert, template: NotificationTemplate = None) -> bool:
        """Send webhook notification."""
        if not self.is_enabled():
            return False
        
        try:
            # Create payload
            payload = self._create_webhook_payload(alert, template)
            
            # Send webhook
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    self.method,
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    if 200 <= response.status < 300:
                        self._record_success()
                        self.logger.info(f"Webhook notification sent for alert {alert.alert_id}")
                        return True
                    else:
                        error_msg = f"Webhook returned status {response.status}"
                        self._record_failure(error_msg)
                        return False
                        
        except Exception as e:
            error_msg = f"Failed to send webhook notification: {str(e)}"
            self._record_failure(error_msg)
            return False
    
    def _create_webhook_payload(self, alert: Alert, template: NotificationTemplate = None) -> Dict[str, Any]:
        """Create webhook payload."""
        payload = alert.to_dict()
        
        # Add timestamp
        payload["timestamp"] = datetime.now().isoformat()
        
        # Add template rendering if provided
        if template:
            rendered = template.render(alert)
            payload["rendered"] = rendered
        
        return payload


class NotificationRouter:
    """Routes notifications to appropriate channels."""
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.routing_rules: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        
        # Setup default templates
        self._setup_default_templates()
    
    def add_channel(self, channel: NotificationChannel) -> None:
        """Add a notification channel."""
        self.channels[channel.name] = channel
        self.logger.info(f"Added notification channel: {channel.name}")
    
    def remove_channel(self, channel_name: str) -> bool:
        """Remove a notification channel."""
        if channel_name in self.channels:
            del self.channels[channel_name]
            self.logger.info(f"Removed notification channel: {channel_name}")
            return True
        return False
    
    def add_template(self, template: NotificationTemplate) -> None:
        """Add a notification template."""
        self.templates[template.name] = template
        self.logger.info(f"Added notification template: {template.name}")
    
    def add_routing_rule(self, rule: Dict[str, Any]) -> None:
        """Add a routing rule."""
        self.routing_rules.append(rule)
        self.logger.info(f"Added routing rule: {rule}")
    
    async def send_notification(self, alert: Alert) -> Dict[str, bool]:
        """Send notification through appropriate channels."""
        results = {}
        
        # Determine which channels to use
        target_channels = self._determine_channels(alert)
        
        # Determine which template to use
        template = self._determine_template(alert)
        
        # Send to each channel
        for channel_name in target_channels:
            channel = self.channels.get(channel_name)
            if channel and channel.is_enabled():
                try:
                    success = await channel.send_notification(alert, template)
                    results[channel_name] = success
                    
                    # Record notification attempt in alert
                    alert.add_notification_record(channel_name, success)
                    
                except Exception as e:
                    self.logger.error(f"Error sending notification via {channel_name}: {str(e)}")
                    results[channel_name] = False
                    alert.add_notification_record(channel_name, False, str(e))
            else:
                results[channel_name] = False
                alert.add_notification_record(channel_name, False, "Channel disabled or not found")
        
        return results
    
    def _determine_channels(self, alert: Alert) -> List[str]:
        """Determine which channels to use for an alert."""
        channels = []
        
        # Apply routing rules
        for rule in self.routing_rules:
            if self._rule_matches_alert(rule, alert):
                rule_channels = rule.get("channels", [])
                channels.extend(rule_channels)
        
        # Default channels if no rules match
        if not channels:
            channels = list(self.channels.keys())
        
        return list(set(channels))  # Remove duplicates
    
    def _determine_template(self, alert: Alert) -> Optional[NotificationTemplate]:
        """Determine which template to use for an alert."""
        # Check routing rules for template specification
        for rule in self.routing_rules:
            if self._rule_matches_alert(rule, alert):
                template_name = rule.get("template")
                if template_name and template_name in self.templates:
                    return self.templates[template_name]
        
        # Use severity-based template
        severity_template = f"default_{alert.severity.value}"
        if severity_template in self.templates:
            return self.templates[severity_template]
        
        # Use default template
        return self.templates.get("default")
    
    def _rule_matches_alert(self, rule: Dict[str, Any], alert: Alert) -> bool:
        """Check if a routing rule matches an alert."""
        # Check severity filter
        if "severity" in rule:
            if alert.severity.value not in rule["severity"]:
                return False
        
        # Check label filters
        if "labels" in rule:
            for key, value in rule["labels"].items():
                if alert.labels.get(key) != value:
                    return False
        
        # Check rule name pattern
        if "rule_pattern" in rule:
            import fnmatch
            if not fnmatch.fnmatch(alert.rule_name, rule["rule_pattern"]):
                return False
        
        return True
    
    def _setup_default_templates(self) -> None:
        """Setup default notification templates."""
        # Default template
        default_template = NotificationTemplate(
            name="default",
            subject_template="[{severity}] {rule_name}",
            body_template="""Alert: {rule_name}
Severity: {severity}
Status: {status}
Message: {message}

Created: {created_at}
Duration: {duration}

Alert ID: {alert_id}
""",
            format_type="text"
        )
        
        # Critical alert template
        critical_template = NotificationTemplate(
            name="default_critical",
            subject_template="🚨 CRITICAL ALERT: {rule_name}",
            body_template="""🚨 CRITICAL ALERT 🚨

Alert: {rule_name}
Severity: CRITICAL
Status: {status}
Message: {message}
Description: {description}

Created: {created_at}
Duration: {duration}

⚠️ IMMEDIATE ACTION REQUIRED ⚠️

Alert ID: {alert_id}
""",
            format_type="text"
        )
        
        self.add_template(default_template)
        self.add_template(critical_template)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics."""
        stats = {
            "channels": {},
            "total_channels": len(self.channels),
            "enabled_channels": sum(1 for ch in self.channels.values() if ch.is_enabled()),
            "routing_rules": len(self.routing_rules),
            "templates": len(self.templates)
        }
        
        for name, channel in self.channels.items():
            stats["channels"][name] = channel.get_statistics()
        
        return stats