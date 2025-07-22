"""
Alert manager for handling alert lifecycle and notifications.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..models import MetricValue
from ..collector_interface import MetricsCollector
from .alert import Alert, AlertSeverity, AlertStatus
from .alert_rule import AlertRule, AlertRuleEngine
from .notification import NotificationChannel, NotificationManager


@dataclass
class AlertManagerConfig:
    """Configuration for the alert manager."""
    evaluation_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    retention_period: timedelta = field(default_factory=lambda: timedelta(days=7))
    max_alerts: int = 1000
    enable_auto_resolve: bool = True
    default_resolve_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))


class AlertManager:
    """Manages alert lifecycle, evaluation, and notifications."""
    
    def __init__(self, config: AlertManagerConfig = None):
        self.config = config or AlertManagerConfig()
        self.rule_engine = AlertRuleEngine()
        self.notification_manager = NotificationManager()
        self.logger = logging.getLogger(__name__)
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: Dict[str, Alert] = {}
        self.silenced_alerts: Set[str] = set()
        
        # Metrics collectors
        self.collectors: Dict[str, MetricsCollector] = {}
        
        # Background tasks
        self._evaluation_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    def add_collector(self, name: str, collector: MetricsCollector) -> None:
        """Add a metrics collector."""
        self.collectors[name] = collector
        self.logger.info(f"Added metrics collector: {name}")
    
    def remove_collector(self, name: str) -> bool:
        """Remove a metrics collector."""
        if name in self.collectors:
            del self.collectors[name]
            self.logger.info(f"Removed metrics collector: {name}")
            return True
        return False
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rule_engine.add_rule(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        return self.rule_engine.remove_rule(rule_id)
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        return self.rule_engine.get_rule(rule_id)
    
    def list_rules(self) -> List[AlertRule]:
        """List all alert rules."""
        return self.rule_engine.list_rules()
    
    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """Add a notification channel."""
        self.notification_manager.add_channel(channel)
    
    def remove_notification_channel(self, channel_id: str) -> bool:
        """Remove a notification channel."""
        return self.notification_manager.remove_channel(channel_id)
    
    async def collect_metrics(self) -> List[MetricValue]:
        """Collect metrics from all collectors."""
        all_metrics = []
        
        for name, collector in self.collectors.items():
            try:
                metrics = await collector.collect_metrics()
                all_metrics.extend(metrics)
                self.logger.debug(f"Collected {len(metrics)} metrics from {name}")
            except Exception as e:
                self.logger.error(f"Error collecting metrics from {name}: {str(e)}")
        
        return all_metrics
    
    async def evaluate_alerts(self) -> List[Alert]:
        """Evaluate alert rules against current metrics."""
        try:
            # Collect current metrics
            metrics = await self.collect_metrics()
            
            # Evaluate rules
            new_alerts = self.rule_engine.evaluate_rules(metrics)
            
            # Process new alerts
            for alert in new_alerts:
                await self._process_new_alert(alert)
            
            # Check for resolved alerts
            await self._check_resolved_alerts(metrics)
            
            return new_alerts
            
        except Exception as e:
            self.logger.error(f"Error evaluating alerts: {str(e)}")
            return []
    
    async def _process_new_alert(self, alert: Alert) -> None:
        """Process a newly fired alert."""
        # Check if alert is silenced
        if alert.id in self.silenced_alerts:
            alert.silence()
            self.logger.info(f"Alert silenced: {alert.name} ({alert.id})")
            return
        
        # Add to active alerts
        self.active_alerts[alert.id] = alert
        
        # Send notifications
        try:
            await self.notification_manager.send_alert_notification(alert)
            alert.mark_notified()
            self.logger.info(f"Sent notification for alert: {alert.name} ({alert.id})")
        except Exception as e:
            self.logger.error(f"Failed to send notification for alert {alert.id}: {str(e)}")
    
    async def _check_resolved_alerts(self, current_metrics: List[MetricValue]) -> None:
        """Check if any active alerts should be resolved."""
        if not self.config.enable_auto_resolve:
            return
        
        resolved_alert_ids = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.status != AlertStatus.FIRING:
                continue
            
            # Get the rule for this alert
            rule = self.rule_engine.get_rule(alert.rule_id)
            if not rule or not rule.auto_resolve:
                continue
            
            # Check if conditions are still met
            conditions_met = False
            for condition in rule.conditions:
                for metric in current_metrics:
                    if condition.evaluate(metric):
                        conditions_met = True
                        break
                if conditions_met:
                    break
            
            # Resolve if conditions are no longer met
            if not conditions_met:
                resolve_timeout = rule.resolve_timeout or self.config.default_resolve_timeout
                if alert.fired_at and datetime.now() - alert.fired_at >= resolve_timeout:
                    alert.resolve()
                    resolved_alert_ids.append(alert_id)
                    self.logger.info(f"Auto-resolved alert: {alert.name} ({alert.id})")
        
        # Move resolved alerts
        for alert_id in resolved_alert_ids:
            alert = self.active_alerts.pop(alert_id)
            self.resolved_alerts[alert_id] = alert
            
            # Send resolution notification
            try:
                await self.notification_manager.send_resolution_notification(alert)
            except Exception as e:
                self.logger.error(f"Failed to send resolution notification for alert {alert_id}: {str(e)}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def get_resolved_alerts(self, limit: int = 100) -> List[Alert]:
        """Get resolved alerts."""
        alerts = list(self.resolved_alerts.values())
        return sorted(alerts, key=lambda a: a.resolved_at or a.created_at, reverse=True)[:limit]
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.active_alerts.get(alert_id) or self.resolved_alerts.get(alert_id)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        alert = self.active_alerts.get(alert_id)
        if alert and alert.status == AlertStatus.FIRING:
            alert.acknowledge()
            self.logger.info(f"Acknowledged alert: {alert.name} ({alert_id})")
            return True
        return False
    
    def silence_alert(self, alert_id: str, duration: Optional[timedelta] = None) -> bool:
        """Silence an alert."""
        alert = self.get_alert(alert_id)
        if alert:
            self.silenced_alerts.add(alert_id)
            alert.silence()
            
            # Schedule unsilencing if duration is specified
            if duration:
                asyncio.create_task(self._unsilence_after_delay(alert_id, duration))
            
            self.logger.info(f"Silenced alert: {alert.name} ({alert_id})")
            return True
        return False
    
    async def _unsilence_after_delay(self, alert_id: str, duration: timedelta) -> None:
        """Unsilence an alert after a delay."""
        await asyncio.sleep(duration.total_seconds())
        self.silenced_alerts.discard(alert_id)
        self.logger.info(f"Unsilenced alert: {alert_id}")
    
    def unsilence_alert(self, alert_id: str) -> bool:
        """Unsilence an alert."""
        if alert_id in self.silenced_alerts:
            self.silenced_alerts.remove(alert_id)
            alert = self.get_alert(alert_id)
            if alert and alert.status == AlertStatus.SILENCED:
                alert.status = AlertStatus.FIRING
                alert.updated_at = datetime.now()
            self.logger.info(f"Unsilenced alert: {alert_id}")
            return True
        return False
    
    async def start(self) -> None:
        """Start the alert manager background tasks."""
        if self._running:
            return
        
        self._running = True
        self.logger.info("Starting alert manager")
        
        # Start evaluation task
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self) -> None:
        """Stop the alert manager background tasks."""
        if not self._running:
            return
        
        self._running = False
        self.logger.info("Stopping alert manager")
        
        # Cancel tasks
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _evaluation_loop(self) -> None:
        """Background task for evaluating alerts."""
        while self._running:
            try:
                await self.evaluate_alerts()
                await asyncio.sleep(self.config.evaluation_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in evaluation loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up old alerts."""
        while self._running:
            try:
                await self._cleanup_old_alerts()
                await asyncio.sleep(3600)  # Run cleanup every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(300)  # Brief pause before retrying
    
    async def _cleanup_old_alerts(self) -> None:
        """Clean up old resolved alerts."""
        cutoff_time = datetime.now() - self.config.retention_period
        
        # Clean up resolved alerts
        old_alert_ids = []
        for alert_id, alert in self.resolved_alerts.items():
            if alert.resolved_at and alert.resolved_at < cutoff_time:
                old_alert_ids.append(alert_id)
        
        for alert_id in old_alert_ids:
            del self.resolved_alerts[alert_id]
        
        if old_alert_ids:
            self.logger.info(f"Cleaned up {len(old_alert_ids)} old resolved alerts")
        
        # Limit total number of alerts
        if len(self.resolved_alerts) > self.config.max_alerts:
            # Keep only the most recent alerts
            sorted_alerts = sorted(
                self.resolved_alerts.items(),
                key=lambda x: x[1].resolved_at or x[1].created_at,
                reverse=True
            )
            
            # Keep only max_alerts
            to_keep = dict(sorted_alerts[:self.config.max_alerts])
            removed_count = len(self.resolved_alerts) - len(to_keep)
            self.resolved_alerts = to_keep
            
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} old alerts to maintain limit")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert manager statistics."""
        active_by_severity = {}
        for severity in AlertSeverity:
            active_by_severity[severity.value] = len([
                a for a in self.active_alerts.values() 
                if a.severity == severity
            ])
        
        return {
            "active_alerts": len(self.active_alerts),
            "resolved_alerts": len(self.resolved_alerts),
            "silenced_alerts": len(self.silenced_alerts),
            "active_by_severity": active_by_severity,
            "rules_count": len(self.rule_engine.rules),
            "collectors_count": len(self.collectors),
            "notification_channels": len(self.notification_manager.channels),
            "running": self._running
        }