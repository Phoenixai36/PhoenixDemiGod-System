"""
Notification system for alerts.
"""

import asyncio
import logging
import smtplib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiohttp

from .alert import Alert, AlertSeverity, AlertStatus


@dataclass
class NotificationConfig:
    """Base configuration for notifications."""
    enabled: bool = True
    retry_attempts: int = 3
    retry_delay: float = 5.0
    timeout: float = 30.0


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    def __init__(self, channel_id: str, name: str, config: NotificationConfig = None):
        self.channel_id = channel_id
        self.name = name
        self.config = config or NotificationConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert notification."""
        pass
    
    @abstractmethod
    async def send_resolution(self, alert: Alert) -> bool:
        """Send an alert resolution notification."""
        pass
    
    def should_notify(self, alert: Alert) -> bool:
        """Check if this channel should notify for the given alert."""
        return self.config.enabled
    
    async def send_with_retry(self, send_func, *args, **kwargs) -> bool:
        """Send notification with retry logic."""
        for attempt in range(self.config.retry_attempts):
            try:
                return await send_func(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Notification attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    self.logger.error(f"All notification attempts failed for {self.name}")
                    return False
        return False


@dataclass
class EmailConfig(NotificationConfig):
    """Configuration for email notifications."""
    smtp_server: str = "localhost"
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_address: str = "alerts@example.com"
    to_addresses: List[str] = field(default_factory=list)
    subject_template: str = "[{severity}] {name}"
    body_template: str = """
Alert: {name}
Description: {description}
Severity: {severity}
Status: {status}
Metric: {metric_name} = {metric_value}
Condition: {metric_name} {condition} {threshold}
Time: {created_at}
Labels: {labels}
"""


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""
    
    def __init__(self, channel_id: str, name: str, email_config: EmailConfig):
        super().__init__(channel_id, name, email_config)
        self.email_config = email_config
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        if not self.email_config.to_addresses:
            self.logger.warning("No email addresses configured")
            return False
        
        return await self.send_with_retry(self._send_email, alert, is_resolution=False)
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send resolution via email."""
        if not self.email_config.to_addresses:
            self.logger.warning("No email addresses configured")
            return False
        
        return await self.send_with_retry(self._send_email, alert, is_resolution=True)
    
    async def _send_email(self, alert: Alert, is_resolution: bool = False) -> bool:
        """Send email notification."""
        try:
            # Format subject
            prefix = "[RESOLVED]" if is_resolution else ""
            subject = f"{prefix} {self.email_config.subject_template.format(**alert.to_dict())}"
            
            # Format body
            body_data = alert.to_dict()
            body_data['labels'] = ', '.join(f"{k}={v}" for k, v in alert.labels.items())
            body = self.email_config.body_template.format(**body_data)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config.from_address
            msg['To'] = ', '.join(self.email_config.to_addresses)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, msg
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart) -> None:
        """Send email via SMTP (blocking operation)."""
        with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as server:
            if self.email_config.use_tls:
                server.starttls()
            
            if self.email_config.username and self.email_config.password:
                server.login(self.email_config.username, self.email_config.password)
            
            server.send_message(msg)


@dataclass
class WebhookConfig(NotificationConfig):
    """Configuration for webhook notifications."""
    url: str = ""
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    payload_template: Dict[str, Any] = field(default_factory=lambda: {
        "alert_id": "{id}",
        "name": "{name}",
        "description": "{description}",
        "severity": "{severity}",
        "status": "{status}",
        "metric_name": "{metric_name}",
        "metric_value": "{metric_value}",
        "threshold": "{threshold}",
        "condition": "{condition}",
        "created_at": "{created_at}",
        "labels": "{labels}"
    })


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel."""
    
    def __init__(self, channel_id: str, name: str, webhook_config: WebhookConfig):
        super().__init__(channel_id, name, webhook_config)
        self.webhook_config = webhook_config
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        return await self.send_with_retry(self._send_webhook, alert, is_resolution=False)
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send resolution via webhook."""
        return await self.send_with_retry(self._send_webhook, alert, is_resolution=True)
    
    async def _send_webhook(self, alert: Alert, is_resolution: bool = False) -> bool:
        """Send webhook notification."""
        try:
            # Prepare payload
            alert_data = alert.to_dict()
            alert_data['labels'] = alert.labels  # Keep as dict for JSON
            alert_data['is_resolution'] = is_resolution
            
            # Format payload template
            payload = {}
            for key, template in self.webhook_config.payload_template.items():
                if isinstance(template, str):
                    payload[key] = template.format(**alert_data)
                else:
                    payload[key] = template
            
            # Add resolution flag
            payload['is_resolution'] = is_resolution
            
            # Send webhook
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=self.webhook_config.method,
                    url=self.webhook_config.url,
                    json=payload,
                    headers=self.webhook_config.headers
                ) as response:
                    if response.status < 400:
                        return True
                    else:
                        self.logger.error(f"Webhook returned status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook: {str(e)}")
            return False


@dataclass
class SlackConfig(NotificationConfig):
    """Configuration for Slack notifications."""
    webhook_url: str = ""
    channel: Optional[str] = None
    username: str = "AlertBot"
    icon_emoji: str = ":warning:"
    color_map: Dict[str, str] = field(default_factory=lambda: {
        "info": "#36a64f",      # Green
        "warning": "#ff9500",   # Orange
        "error": "#ff0000",     # Red
        "critical": "#8b0000"   # Dark red
    })


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""
    
    def __init__(self, channel_id: str, name: str, slack_config: SlackConfig):
        super().__init__(channel_id, name, slack_config)
        self.slack_config = slack_config
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        return await self.send_with_retry(self._send_slack_message, alert, is_resolution=False)
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Send resolution to Slack."""
        return await self.send_with_retry(self._send_slack_message, alert, is_resolution=True)
    
    async def _send_slack_message(self, alert: Alert, is_resolution: bool = False) -> bool:
        """Send Slack message."""
        try:
            # Prepare message
            color = self.slack_config.color_map.get(alert.severity.value, "#cccccc")
            
            if is_resolution:
                title = f"🟢 RESOLVED: {alert.name}"
                color = "#36a64f"  # Green for resolved
            else:
                emoji = self._get_severity_emoji(alert.severity)
                title = f"{emoji} {alert.name}"
            
            # Create attachment
            attachment = {
                "color": color,
                "title": title,
                "fields": [
                    {"title": "Description", "value": alert.description, "short": False},
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Status", "value": alert.status.value.upper(), "short": True},
                    {"title": "Metric", "value": f"{alert.metric_name} = {alert.metric_value}", "short": True},
                    {"title": "Condition", "value": f"{alert.metric_name} {alert.condition} {alert.threshold}", "short": True},
                    {"title": "Time", "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ],
                "footer": "System Health Monitor",
                "ts": int(alert.created_at.timestamp())
            }
            
            # Add labels if present
            if alert.labels:
                labels_text = ", ".join(f"{k}={v}" for k, v in alert.labels.items())
                attachment["fields"].append({"title": "Labels", "value": labels_text, "short": False})
            
            # Prepare payload
            payload = {
                "username": self.slack_config.username,
                "icon_emoji": self.slack_config.icon_emoji,
                "attachments": [attachment]
            }
            
            if self.slack_config.channel:
                payload["channel"] = self.slack_config.channel
            
            # Send to Slack
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.slack_config.webhook_url,
                    json=payload
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        self.logger.error(f"Slack webhook returned status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send Slack message: {str(e)}")
            return False
    
    def _get_severity_emoji(self, severity: AlertSeverity) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }
        return emoji_map.get(severity, "❓")


class LogNotificationChannel(NotificationChannel):
    """Log-based notification channel for testing and debugging."""
    
    def __init__(self, channel_id: str = "log", name: str = "Log Channel"):
        super().__init__(channel_id, name)
    
    async def send_alert(self, alert: Alert) -> bool:
        """Log alert notification."""
        self.logger.info(f"ALERT: {alert.name} - {alert.description} "
                        f"(Severity: {alert.severity.value}, "
                        f"Metric: {alert.metric_name}={alert.metric_value})")
        return True
    
    async def send_resolution(self, alert: Alert) -> bool:
        """Log resolution notification."""
        self.logger.info(f"RESOLVED: {alert.name} - Alert has been resolved")
        return True


class NotificationManager:
    """Manages notification channels and sending notifications."""
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_channel(self, channel: NotificationChannel) -> None:
        """Add a notification channel."""
        self.channels[channel.channel_id] = channel
        self.logger.info(f"Added notification channel: {channel.name} ({channel.channel_id})")
    
    def remove_channel(self, channel_id: str) -> bool:
        """Remove a notification channel."""
        if channel_id in self.channels:
            channel = self.channels.pop(channel_id)
            self.logger.info(f"Removed notification channel: {channel.name} ({channel_id})")
            return True
        return False
    
    def get_channel(self, channel_id: str) -> Optional[NotificationChannel]:
        """Get a notification channel by ID."""
        return self.channels.get(channel_id)
    
    def list_channels(self) -> List[NotificationChannel]:
        """List all notification channels."""
        return list(self.channels.values())
    
    async def send_alert_notification(self, alert: Alert) -> Dict[str, bool]:
        """Send alert notification to all applicable channels."""
        results = {}
        
        for channel in self.channels.values():
            if channel.should_notify(alert):
                try:
                    success = await channel.send_alert(alert)
                    results[channel.channel_id] = success
                    if success:
                        self.logger.debug(f"Sent alert notification via {channel.name}")
                    else:
                        self.logger.warning(f"Failed to send alert notification via {channel.name}")
                except Exception as e:
                    self.logger.error(f"Error sending alert via {channel.name}: {str(e)}")
                    results[channel.channel_id] = False
        
        return results
    
    async def send_resolution_notification(self, alert: Alert) -> Dict[str, bool]:
        """Send resolution notification to all applicable channels."""
        results = {}
        
        for channel in self.channels.values():
            if channel.should_notify(alert):
                try:
                    success = await channel.send_resolution(alert)
                    results[channel.channel_id] = success
                    if success:
                        self.logger.debug(f"Sent resolution notification via {channel.name}")
                    else:
                        self.logger.warning(f"Failed to send resolution notification via {channel.name}")
                except Exception as e:
                    self.logger.error(f"Error sending resolution via {channel.name}: {str(e)}")
                    results[channel.channel_id] = False
        
        return results