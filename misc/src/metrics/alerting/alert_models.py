"""
Data models for the alerting system.

This module defines the core data structures used throughout the alerting system.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from ..models import MetricValue


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status values."""
    PENDING = "pending"        # Alert condition detected but not yet firing
    FIRING = "firing"          # Alert is actively firing
    RESOLVED = "resolved"      # Alert condition no longer met
    ACKNOWLEDGED = "acknowledged"  # Alert has been acknowledged by user
    SILENCED = "silenced"      # Alert has been silenced
    SUPPRESSED = "suppressed"  # Alert suppressed by dependency rules


class AlertConditionType(Enum):
    """Types of alert conditions."""
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    ANOMALY = "anomaly"
    COMPOSITE = "composite"


@dataclass
class AlertCondition:
    """Defines a condition that can trigger an alert."""
    condition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    condition_type: AlertConditionType = AlertConditionType.THRESHOLD
    metric_name: str = ""
    
    # Threshold conditions
    operator: str = "gt"  # gt, lt, eq, ne, gte, lte
    threshold_value: Union[float, int] = 0
    
    # Pattern conditions
    pattern: Optional[str] = None
    time_window: Optional[timedelta] = None
    
    # Label filters
    label_filters: Dict[str, str] = field(default_factory=dict)
    
    # Evaluation settings
    evaluation_window: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    min_samples: int = 1
    
    def evaluate(self, metrics: List[MetricValue]) -> bool:
        """Evaluate if this condition is met by the given metrics."""
        if self.condition_type == AlertConditionType.THRESHOLD:
            return self._evaluate_threshold(metrics)
        elif self.condition_type == AlertConditionType.PATTERN:
            return self._evaluate_pattern(metrics)
        else:
            return False
    
    def _evaluate_threshold(self, metrics: List[MetricValue]) -> bool:
        """Evaluate threshold condition."""
        # Filter metrics by name and labels
        relevant_metrics = []
        for metric in metrics:
            if metric.name != self.metric_name:
                continue
            
            # Check label filters
            if self.label_filters:
                matches = all(
                    metric.labels.get(key) == value
                    for key, value in self.label_filters.items()
                )
                if not matches:
                    continue
            
            relevant_metrics.append(metric)
        
        if len(relevant_metrics) < self.min_samples:
            return False
        
        # Evaluate threshold for each metric
        violations = 0
        for metric in relevant_metrics:
            try:
                value = float(metric.value)
                if self._check_threshold(value):
                    violations += 1
            except (ValueError, TypeError):
                continue
        
        # Return true if any metrics violate the threshold
        return violations > 0
    
    def _check_threshold(self, value: float) -> bool:
        """Check if a value violates the threshold."""
        threshold = float(self.threshold_value)
        
        if self.operator == "gt":
            return value > threshold
        elif self.operator == "lt":
            return value < threshold
        elif self.operator == "eq":
            return value == threshold
        elif self.operator == "ne":
            return value != threshold
        elif self.operator == "gte":
            return value >= threshold
        elif self.operator == "lte":
            return value <= threshold
        else:
            return False
    
    def _evaluate_pattern(self, metrics: List[MetricValue]) -> bool:
        """Evaluate pattern condition (placeholder)."""
        # This would implement pattern-based alerting
        # For now, return False
        return False


@dataclass
class AlertRule:
    """Defines a rule for generating alerts."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    
    # Conditions
    conditions: List[AlertCondition] = field(default_factory=list)
    condition_logic: str = "AND"  # AND, OR
    
    # Timing
    for_duration: Optional[timedelta] = None  # How long condition must be true
    evaluation_interval: timedelta = field(default_factory=lambda: timedelta(minutes=1))
    
    # Notification settings
    notification_channels: List[str] = field(default_factory=list)
    notification_template: Optional[str] = None
    
    # Labels and annotations
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    # Suppression
    depends_on: List[str] = field(default_factory=list)  # Other rule IDs
    
    # Internal state
    _first_detected: Optional[datetime] = None
    _last_evaluated: Optional[datetime] = None
    _evaluation_count: int = 0
    
    def evaluate(self, metrics: List[MetricValue]) -> bool:
        """Evaluate if this rule should fire an alert."""
        if not self.enabled or not self.conditions:
            return False
        
        self._last_evaluated = datetime.now()
        self._evaluation_count += 1
        
        # Evaluate conditions
        condition_results = []
        for condition in self.conditions:
            result = condition.evaluate(metrics)
            condition_results.append(result)
        
        # Apply condition logic
        if self.condition_logic == "AND":
            conditions_met = all(condition_results)
        elif self.condition_logic == "OR":
            conditions_met = any(condition_results)
        else:
            conditions_met = any(condition_results)  # Default to OR
        
        # Handle timing requirements
        now = datetime.now()
        
        if conditions_met:
            if self._first_detected is None:
                self._first_detected = now
            
            # Check if duration requirement is met
            if self.for_duration:
                time_since_detection = now - self._first_detected
                if time_since_detection < self.for_duration:
                    return False  # Not firing yet, waiting for duration
            
            return True  # Conditions met and duration satisfied
        else:
            # Conditions no longer met
            self._first_detected = None
            return False
    
    def reset_state(self) -> None:
        """Reset the internal state of the rule."""
        self._first_detected = None
        self._last_evaluated = None
        self._evaluation_count = 0
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get information about the rule's internal state."""
        return {
            "first_detected": self._first_detected.isoformat() if self._first_detected else None,
            "last_evaluated": self._last_evaluated.isoformat() if self._last_evaluated else None,
            "evaluation_count": self._evaluation_count,
            "enabled": self.enabled
        }


@dataclass
class AlertContext:
    """Context information for an alert."""
    triggering_metrics: List[MetricValue] = field(default_factory=list)
    evaluation_time: datetime = field(default_factory=datetime.now)
    rule_state: Dict[str, Any] = field(default_factory=dict)
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_metric(self, metric: MetricValue) -> None:
        """Add a triggering metric to the context."""
        self.triggering_metrics.append(metric)
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get a summary of triggering metrics."""
        if not self.triggering_metrics:
            return {}
        
        # Group by metric name
        by_name = {}
        for metric in self.triggering_metrics:
            if metric.name not in by_name:
                by_name[metric.name] = []
            by_name[metric.name].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for name, values in by_name.items():
            numeric_values = []
            for value in values:
                try:
                    numeric_values.append(float(value))
                except (ValueError, TypeError):
                    continue
            
            if numeric_values:
                summary[name] = {
                    "count": len(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "avg": sum(numeric_values) / len(numeric_values),
                    "latest": numeric_values[-1] if numeric_values else None
                }
        
        return summary


@dataclass
class Alert:
    """Represents an active or historical alert."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    
    # Alert details
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.PENDING
    message: str = ""
    description: str = ""
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Context
    context: AlertContext = field(default_factory=AlertContext)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    # Notification tracking
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)
    last_notification_at: Optional[datetime] = None
    
    # User actions
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    def update_status(self, new_status: AlertStatus, user: str = None) -> None:
        """Update the alert status."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == AlertStatus.ACKNOWLEDGED:
            self.acknowledged_at = datetime.now()
            self.acknowledged_by = user
        elif new_status == AlertStatus.RESOLVED:
            self.resolved_at = datetime.now()
            self.resolved_by = user
        
        # Add note about status change
        if user:
            self.add_note(f"Status changed from {old_status.value} to {new_status.value} by {user}")
        else:
            self.add_note(f"Status changed from {old_status.value} to {new_status.value}")
    
    def acknowledge(self, user: str, note: str = None) -> None:
        """Acknowledge the alert."""
        self.update_status(AlertStatus.ACKNOWLEDGED, user)
        if note:
            self.add_note(f"Acknowledged by {user}: {note}")
    
    def resolve(self, user: str = None, note: str = None) -> None:
        """Resolve the alert."""
        self.update_status(AlertStatus.RESOLVED, user)
        if note:
            self.add_note(f"Resolved: {note}")
    
    def add_note(self, note: str) -> None:
        """Add a note to the alert."""
        timestamp = datetime.now().isoformat()
        self.notes.append(f"[{timestamp}] {note}")
    
    def add_notification_record(self, channel: str, success: bool, details: str = None) -> None:
        """Record a notification attempt."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "success": success,
            "details": details
        }
        self.notifications_sent.append(record)
        
        if success:
            self.last_notification_at = datetime.now()
    
    def get_duration(self) -> Optional[timedelta]:
        """Get the duration the alert has been active."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        else:
            return datetime.now() - self.created_at
    
    def is_active(self) -> bool:
        """Check if the alert is currently active."""
        return self.status in [AlertStatus.PENDING, AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization."""
        return {
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "labels": self.labels,
            "annotations": self.annotations,
            "notifications_sent": self.notifications_sent,
            "last_notification_at": self.last_notification_at.isoformat() if self.last_notification_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "notes": self.notes,
            "duration_seconds": self.get_duration().total_seconds() if self.get_duration() else None,
            "is_active": self.is_active(),
            "context": {
                "triggering_metrics_count": len(self.context.triggering_metrics),
                "metric_summary": self.context.get_metric_summary(),
                "evaluation_time": self.context.evaluation_time.isoformat(),
                "additional_data": self.context.additional_data
            }
        }