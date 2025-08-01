"""
Alert rule definitions and evaluation engine.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from ..models import MetricValue
from .alert import Alert, AlertSeverity, AlertStatus


@dataclass
class AlertCondition:
    """Represents a condition for triggering an alert."""
    metric_name: str
    operator: str  # gt, lt, eq, ne, gte, lte, contains, regex
    threshold: Union[float, str]
    for_duration: Optional[timedelta] = None
    labels_match: Optional[Dict[str, str]] = None
    
    def evaluate(self, metric: MetricValue) -> bool:
        """Evaluate if the metric matches this condition."""
        # Check metric name
        if metric.name != self.metric_name:
            return False
        
        # Check labels if specified
        if self.labels_match:
            for key, value in self.labels_match.items():
                if key not in metric.labels or metric.labels[key] != value:
                    return False
        
        # Check value against threshold
        return self._compare_value(metric.value)
    
    def _compare_value(self, value: Any) -> bool:
        """Compare metric value against threshold."""
        try:
            if self.operator == "gt":
                return float(value) > float(self.threshold)
            elif self.operator == "lt":
                return float(value) < float(self.threshold)
            elif self.operator == "eq":
                return float(value) == float(self.threshold)
            elif self.operator == "ne":
                return float(value) != float(self.threshold)
            elif self.operator == "gte":
                return float(value) >= float(self.threshold)
            elif self.operator == "lte":
                return float(value) <= float(self.threshold)
            elif self.operator == "contains":
                return str(self.threshold) in str(value)
            elif self.operator == "regex":
                return bool(re.search(str(self.threshold), str(value)))
            else:
                return False
        except (ValueError, TypeError):
            # Handle non-numeric comparisons
            if self.operator == "eq":
                return str(value) == str(self.threshold)
            elif self.operator == "ne":
                return str(value) != str(self.threshold)
            elif self.operator == "contains":
                return str(self.threshold) in str(value)
            elif self.operator == "regex":
                return bool(re.search(str(self.threshold), str(value)))
            return False
    
    def get_operator_symbol(self) -> str:
        """Get the symbol representation of the operator."""
        symbols = {
            "gt": ">",
            "lt": "<",
            "eq": "==",
            "ne": "!=",
            "gte": ">=",
            "lte": "<=",
            "contains": "contains",
            "regex": "matches"
        }
        return symbols.get(self.operator, self.operator)


@dataclass
class AlertRule:
    """Defines a rule for generating alerts based on metric conditions."""
    id: str
    name: str
    description: str
    conditions: List[AlertCondition]
    severity: AlertSeverity
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    # Alert behavior
    for_duration: Optional[timedelta] = None  # How long condition must be true before firing
    throttle_duration: Optional[timedelta] = None  # Minimum time between repeated alerts
    auto_resolve: bool = True  # Whether to auto-resolve when condition is no longer true
    resolve_timeout: Optional[timedelta] = None  # How long until auto-resolve
    
    # Internal state
    _first_detected: Optional[datetime] = None
    _last_fired: Optional[datetime] = None
    _status: AlertStatus = AlertStatus.PENDING
    _firing_count: int = 0
    
    def evaluate(self, metrics: List[MetricValue]) -> bool:
        """
        Evaluate if the alert should fire based on metrics.
        
        Args:
            metrics: List of metrics to evaluate against conditions
            
        Returns:
            True if alert should fire, False otherwise
        """
        now = datetime.now()
        
        # Check if all conditions are met
        all_conditions_met = True
        matching_metrics = []
        
        for condition in self.conditions:
            condition_met = False
            
            for metric in metrics:
                if condition.evaluate(metric):
                    condition_met = True
                    matching_metrics.append(metric)
                    break
            
            if not condition_met:
                all_conditions_met = False
                break
        
        # Update state based on conditions
        if all_conditions_met:
            # First detection
            if self._first_detected is None:
                self._first_detected = now
                self._status = AlertStatus.PENDING
                return False  # Not firing yet, just detected
            
            # Check if duration threshold is met
            if self.for_duration and now - self._first_detected < self.for_duration:
                self._status = AlertStatus.PENDING
                return False  # Not firing yet, waiting for duration
            
            # Check throttling
            if self._last_fired and self.throttle_duration and now - self._last_fired < self.throttle_duration:
                return False  # Already fired recently, throttling
            
            # Alert should fire
            self._status = AlertStatus.FIRING
            self._last_fired = now
            self._firing_count += 1
            return True
            
        else:
            # Conditions no longer met
            if self._status == AlertStatus.FIRING and self.auto_resolve:
                if self.resolve_timeout:
                    # Check if enough time has passed since last firing
                    if self._last_fired and now - self._last_fired >= self.resolve_timeout:
                        self._status = AlertStatus.RESOLVED
                else:
                    # Immediately resolve
                    self._status = AlertStatus.RESOLVED
            
            # Reset detection time if not firing
            if self._status != AlertStatus.FIRING:
                self._first_detected = None
            
            return False
    
    def create_alert(self, metrics: List[MetricValue]) -> Optional[Alert]:
        """Create an alert from this rule if conditions are met."""
        # Find matching metrics for each condition
        matching_metrics = []
        for condition in self.conditions:
            for metric in metrics:
                if condition.evaluate(metric):
                    matching_metrics.append(metric)
                    break
        
        if len(matching_metrics) != len(self.conditions):
            return None  # Not all conditions have matching metrics
        
        # Use the first condition and matching metric for the alert details
        condition = self.conditions[0]
        metric = next((m for m in metrics if condition.evaluate(m)), None)
        if not metric:
            return None
        
        # Create alert
        alert = Alert(
            name=self.name,
            description=self.description,
            severity=self.severity,
            rule_id=self.id,
            metric_name=metric.name,
            metric_value=metric.value,
            threshold=condition.threshold,
            condition=condition.get_operator_symbol(),
            labels={**self.labels, **metric.labels},
            annotations=self.annotations,
            source_metrics=matching_metrics
        )
        
        return alert
    
    def reset_state(self) -> None:
        """Reset the internal state of the rule."""
        self._first_detected = None
        self._last_fired = None
        self._status = AlertStatus.PENDING
        self._firing_count = 0
    
    def get_status(self) -> AlertStatus:
        """Get the current status of the rule."""
        return self._status
    
    def get_firing_count(self) -> int:
        """Get the number of times this rule has fired."""
        return self._firing_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": [
                {
                    "metric_name": c.metric_name,
                    "operator": c.operator,
                    "threshold": c.threshold,
                    "for_duration": c.for_duration.total_seconds() if c.for_duration else None,
                    "labels_match": c.labels_match
                }
                for c in self.conditions
            ],
            "severity": self.severity.value,
            "labels": self.labels,
            "annotations": self.annotations,
            "for_duration": self.for_duration.total_seconds() if self.for_duration else None,
            "throttle_duration": self.throttle_duration.total_seconds() if self.throttle_duration else None,
            "auto_resolve": self.auto_resolve,
            "resolve_timeout": self.resolve_timeout.total_seconds() if self.resolve_timeout else None,
            "firing_count": self._firing_count,
            "status": self._status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertRule':
        """Create rule from dictionary."""
        # Parse conditions
        conditions = []
        for cond_data in data.get("conditions", []):
            condition = AlertCondition(
                metric_name=cond_data["metric_name"],
                operator=cond_data["operator"],
                threshold=cond_data["threshold"],
                for_duration=timedelta(seconds=cond_data["for_duration"]) if cond_data.get("for_duration") else None,
                labels_match=cond_data.get("labels_match")
            )
            conditions.append(condition)
        
        # Parse durations
        for_duration = timedelta(seconds=data["for_duration"]) if data.get("for_duration") else None
        throttle_duration = timedelta(seconds=data["throttle_duration"]) if data.get("throttle_duration") else None
        resolve_timeout = timedelta(seconds=data["resolve_timeout"]) if data.get("resolve_timeout") else None
        
        # Create rule
        rule = cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            conditions=conditions,
            severity=AlertSeverity(data["severity"]),
            labels=data.get("labels", {}),
            annotations=data.get("annotations", {}),
            for_duration=for_duration,
            throttle_duration=throttle_duration,
            auto_resolve=data.get("auto_resolve", True),
            resolve_timeout=resolve_timeout
        )
        
        # Restore state
        rule._firing_count = data.get("firing_count", 0)
        rule._status = AlertStatus(data.get("status", "pending"))
        
        return rule


class AlertRuleEngine:
    """Engine for evaluating alert rules against metrics."""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules[rule.id] = rule
        self.logger.info(f"Added alert rule: {rule.name} ({rule.id})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self.rules:
            rule = self.rules.pop(rule_id)
            self.logger.info(f"Removed alert rule: {rule.name} ({rule_id})")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self) -> List[AlertRule]:
        """List all rules."""
        return list(self.rules.values())
    
    def evaluate_rules(self, metrics: List[MetricValue]) -> List[Alert]:
        """Evaluate all rules against metrics and return fired alerts."""
        alerts = []
        
        for rule in self.rules.values():
            try:
                if rule.evaluate(metrics):
                    alert = rule.create_alert(metrics)
                    if alert:
                        alert.fire()
                        alerts.append(alert)
                        self.logger.info(f"Alert fired: {alert.name} ({alert.id})")
            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
        
        return alerts
    
    def reset_all_rules(self) -> None:
        """Reset the state of all rules."""
        for rule in self.rules.values():
            rule.reset_state()
        self.logger.info("Reset state for all alert rules")


def create_cpu_usage_rule(threshold: float = 80.0, duration_minutes: int = 5) -> AlertRule:
    """Create a standard CPU usage alert rule."""
    return AlertRule(
        id="cpu_usage_high",
        name="High CPU Usage",
        description=f"CPU usage is above {threshold}% for more than {duration_minutes} minutes",
        conditions=[
            AlertCondition(
                metric_name="cpu_usage_percent",
                operator="gt",
                threshold=threshold
            )
        ],
        severity=AlertSeverity.WARNING,
        for_duration=timedelta(minutes=duration_minutes),
        throttle_duration=timedelta(minutes=15),
        labels={"component": "cpu", "type": "usage"},
        annotations={"runbook": "Check CPU-intensive processes"}
    )


def create_memory_usage_rule(threshold: float = 85.0, duration_minutes: int = 3) -> AlertRule:
    """Create a standard memory usage alert rule."""
    return AlertRule(
        id="memory_usage_high",
        name="High Memory Usage",
        description=f"Memory usage is above {threshold}% for more than {duration_minutes} minutes",
        conditions=[
            AlertCondition(
                metric_name="memory_usage_percent",
                operator="gt",
                threshold=threshold
            )
        ],
        severity=AlertSeverity.WARNING,
        for_duration=timedelta(minutes=duration_minutes),
        throttle_duration=timedelta(minutes=10),
        labels={"component": "memory", "type": "usage"},
        annotations={"runbook": "Check memory-intensive processes"}
    )


def create_disk_usage_rule(threshold: float = 90.0, duration_minutes: int = 1) -> AlertRule:
    """Create a standard disk usage alert rule."""
    return AlertRule(
        id="disk_usage_high",
        name="High Disk Usage",
        description=f"Disk usage is above {threshold}% for more than {duration_minutes} minutes",
        conditions=[
            AlertCondition(
                metric_name="disk_usage_percent",
                operator="gt",
                threshold=threshold
            )
        ],
        severity=AlertSeverity.ERROR,
        for_duration=timedelta(minutes=duration_minutes),
        throttle_duration=timedelta(minutes=30),
        labels={"component": "disk", "type": "usage"},
        annotations={"runbook": "Clean up disk space or expand storage"}
    )