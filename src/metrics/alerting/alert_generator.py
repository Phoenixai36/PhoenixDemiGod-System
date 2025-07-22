"""
Alert generation service.

This module provides the core alert generation functionality, including
rule evaluation and alert creation.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from abc import ABC, abstractmethod

from .alert_models import (
    Alert,
    AlertRule,
    AlertCondition,
    AlertSeverity,
    AlertStatus,
    AlertContext,
    AlertConditionType
)
from ..models import MetricValue
from ..storage import QueryEngine, MetricsQuery


class AlertEvaluator(ABC):
    """Base class for alert condition evaluators."""
    
    @abstractmethod
    def evaluate(self, condition: AlertCondition, metrics: List[MetricValue]) -> bool:
        """Evaluate if a condition is met."""
        pass
    
    @abstractmethod
    def get_context(self, condition: AlertCondition, metrics: List[MetricValue]) -> AlertContext:
        """Get context information for the evaluation."""
        pass


class ThresholdEvaluator(AlertEvaluator):
    """Evaluator for threshold-based alert conditions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate(self, condition: AlertCondition, metrics: List[MetricValue]) -> bool:
        """Evaluate threshold condition."""
        if condition.condition_type != AlertConditionType.THRESHOLD:
            return False
        
        # Filter relevant metrics
        relevant_metrics = self._filter_metrics(condition, metrics)
        
        if len(relevant_metrics) < condition.min_samples:
            self.logger.debug(f"Insufficient samples for condition {condition.condition_id}: "
                            f"{len(relevant_metrics)} < {condition.min_samples}")
            return False
        
        # Check threshold violations
        violations = 0
        for metric in relevant_metrics:
            if self._check_threshold_violation(condition, metric):
                violations += 1
        
        # Return true if any violations found
        result = violations > 0
        self.logger.debug(f"Threshold evaluation for {condition.condition_id}: "
                         f"{violations}/{len(relevant_metrics)} violations, result: {result}")
        
        return result
    
    def get_context(self, condition: AlertCondition, metrics: List[MetricValue]) -> AlertContext:
        """Get context for threshold evaluation."""
        context = AlertContext()
        
        # Add triggering metrics
        relevant_metrics = self._filter_metrics(condition, metrics)
        for metric in relevant_metrics:
            if self._check_threshold_violation(condition, metric):
                context.add_metric(metric)
        
        # Add evaluation details
        context.additional_data = {
            "condition_type": "threshold",
            "operator": condition.operator,
            "threshold_value": condition.threshold_value,
            "total_metrics_evaluated": len(relevant_metrics),
            "violating_metrics": len(context.triggering_metrics)
        }
        
        return context
    
    def _filter_metrics(self, condition: AlertCondition, metrics: List[MetricValue]) -> List[MetricValue]:
        """Filter metrics relevant to the condition."""
        relevant_metrics = []
        
        for metric in metrics:
            # Check metric name
            if metric.name != condition.metric_name:
                continue
            
            # Check label filters
            if condition.label_filters:
                matches = all(
                    metric.labels.get(key) == value
                    for key, value in condition.label_filters.items()
                )
                if not matches:
                    continue
            
            # Check time window if specified
            if condition.evaluation_window:
                age = datetime.now() - metric.timestamp
                if age > condition.evaluation_window:
                    continue
            
            relevant_metrics.append(metric)
        
        return relevant_metrics
    
    def _check_threshold_violation(self, condition: AlertCondition, metric: MetricValue) -> bool:
        """Check if a metric violates the threshold."""
        try:
            value = float(metric.value)
            threshold = float(condition.threshold_value)
            
            if condition.operator == "gt":
                return value > threshold
            elif condition.operator == "lt":
                return value < threshold
            elif condition.operator == "eq":
                return abs(value - threshold) < 1e-9  # Float equality with tolerance
            elif condition.operator == "ne":
                return abs(value - threshold) >= 1e-9
            elif condition.operator == "gte":
                return value >= threshold
            elif condition.operator == "lte":
                return value <= threshold
            else:
                self.logger.warning(f"Unknown operator: {condition.operator}")
                return False
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error comparing values: {e}")
            return False


class PatternEvaluator(AlertEvaluator):
    """Evaluator for pattern-based alert conditions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate(self, condition: AlertCondition, metrics: List[MetricValue]) -> bool:
        """Evaluate pattern condition."""
        if condition.condition_type != AlertConditionType.PATTERN:
            return False
        
        # This is a placeholder for pattern-based evaluation
        # In a real implementation, this would analyze metric patterns
        # such as sudden spikes, trends, or anomalies
        
        self.logger.debug(f"Pattern evaluation not yet implemented for condition {condition.condition_id}")
        return False
    
    def get_context(self, condition: AlertCondition, metrics: List[MetricValue]) -> AlertContext:
        """Get context for pattern evaluation."""
        context = AlertContext()
        context.additional_data = {
            "condition_type": "pattern",
            "pattern": condition.pattern,
            "evaluation_status": "not_implemented"
        }
        return context


class AlertGenerator:
    """Main alert generation service."""
    
    def __init__(self, query_engine: QueryEngine = None):
        self.query_engine = query_engine
        self.logger = logging.getLogger(__name__)
        
        # Rule management
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        
        # Evaluators
        self.evaluators: Dict[AlertConditionType, AlertEvaluator] = {
            AlertConditionType.THRESHOLD: ThresholdEvaluator(),
            AlertConditionType.PATTERN: PatternEvaluator()
        }
        
        # Callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Statistics
        self.stats = {
            "evaluations_total": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "last_evaluation_time": None,
            "evaluation_duration_ms": 0
        }
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.name} ({rule.rule_id})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            del self.rules[rule_id]
            self.logger.info(f"Removed alert rule: {rule.name} ({rule_id})")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return list(self.rules.values())
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback to be called when alerts are generated or updated."""
        self.alert_callbacks.append(callback)
    
    async def evaluate_rules(self, metrics: List[MetricValue] = None) -> List[Alert]:
        """Evaluate all rules and generate alerts."""
        start_time = datetime.now()
        
        try:
            self.stats["evaluations_total"] += 1
            
            # Get metrics if not provided
            if metrics is None and self.query_engine:
                metrics = await self._fetch_recent_metrics()
            elif metrics is None:
                metrics = []
            
            new_alerts = []
            resolved_alerts = []
            
            # Evaluate each rule
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    alert_result = await self._evaluate_rule(rule, metrics)
                    
                    if alert_result:
                        if alert_result.status == AlertStatus.FIRING:
                            new_alerts.append(alert_result)
                        elif alert_result.status == AlertStatus.RESOLVED:
                            resolved_alerts.append(alert_result)
                            
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
            
            # Update statistics
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.stats["last_evaluation_time"] = start_time.isoformat()
            self.stats["evaluation_duration_ms"] = duration
            self.stats["alerts_generated"] += len(new_alerts)
            self.stats["alerts_resolved"] += len(resolved_alerts)
            
            # Trigger callbacks
            all_alerts = new_alerts + resolved_alerts
            for alert in all_alerts:
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        self.logger.error(f"Error in alert callback: {str(e)}")
            
            self.logger.info(f"Rule evaluation completed: {len(new_alerts)} new alerts, "
                           f"{len(resolved_alerts)} resolved alerts in {duration:.2f}ms")
            
            return all_alerts
            
        except Exception as e:
            self.logger.error(f"Error in rule evaluation: {str(e)}")
            return []
    
    async def _evaluate_rule(self, rule: AlertRule, metrics: List[MetricValue]) -> Optional[Alert]:
        """Evaluate a single rule."""
        # Check if rule should fire
        should_fire = rule.evaluate(metrics)
        
        # Get existing alert for this rule
        existing_alert = self._get_active_alert_for_rule(rule.rule_id)
        
        if should_fire:
            if existing_alert is None:
                # Create new alert
                alert = self._create_alert_from_rule(rule, metrics)
                self.active_alerts[alert.alert_id] = alert
                return alert
            else:
                # Update existing alert
                existing_alert.updated_at = datetime.now()
                if existing_alert.status == AlertStatus.PENDING:
                    existing_alert.status = AlertStatus.FIRING
                return existing_alert
        else:
            if existing_alert and existing_alert.is_active():
                # Resolve existing alert
                existing_alert.resolve()
                if existing_alert.alert_id in self.active_alerts:
                    del self.active_alerts[existing_alert.alert_id]
                return existing_alert
        
        return None
    
    def _get_active_alert_for_rule(self, rule_id: str) -> Optional[Alert]:
        """Get active alert for a rule."""
        for alert in self.active_alerts.values():
            if alert.rule_id == rule_id and alert.is_active():
                return alert
        return None
    
    def _create_alert_from_rule(self, rule: AlertRule, metrics: List[MetricValue]) -> Alert:
        """Create a new alert from a rule."""
        # Generate alert context
        context = AlertContext()
        
        for condition in rule.conditions:
            evaluator = self.evaluators.get(condition.condition_type)
            if evaluator:
                condition_context = evaluator.get_context(condition, metrics)
                context.triggering_metrics.extend(condition_context.triggering_metrics)
                context.additional_data.update(condition_context.additional_data)
        
        # Create alert
        alert = Alert(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.FIRING,
            message=self._generate_alert_message(rule, context),
            description=rule.description,
            context=context,
            labels=rule.labels.copy(),
            annotations=rule.annotations.copy()
        )
        
        return alert
    
    def _generate_alert_message(self, rule: AlertRule, context: AlertContext) -> str:
        """Generate alert message from rule and context."""
        # Use custom template if available
        if rule.notification_template:
            # This would use a template engine in a real implementation
            return rule.notification_template
        
        # Generate default message
        metric_summary = context.get_metric_summary()
        if metric_summary:
            metric_info = []
            for name, stats in metric_summary.items():
                metric_info.append(f"{name}: {stats['latest']}")
            
            return f"Alert: {rule.name} - {', '.join(metric_info)}"
        else:
            return f"Alert: {rule.name}"
    
    async def _fetch_recent_metrics(self) -> List[MetricValue]:
        """Fetch recent metrics for evaluation."""
        if not self.query_engine:
            return []
        
        try:
            # Get all metric names
            metric_names = await self.query_engine.storage.get_metric_names()
            
            # Query recent data (last 10 minutes)
            recent_time = datetime.now() - timedelta(minutes=10)
            
            all_metrics = []
            for metric_name in metric_names:
                query = MetricsQuery(
                    metric_names=[metric_name],
                    start_time=recent_time,
                    limit=100  # Limit per metric
                )
                
                result = await self.query_engine.execute_query(query)
                
                # Convert points back to MetricValue
                for point in result.points:
                    metric_value = MetricValue(
                        name=metric_name,
                        value=point.value,
                        timestamp=point.timestamp,
                        labels=point.labels
                    )
                    all_metrics.append(metric_value)
            
            return all_metrics
            
        except Exception as e:
            self.logger.error(f"Error fetching metrics: {str(e)}")
            return []
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.active_alerts.values() if alert.is_active()]
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self.active_alerts.get(alert_id)
    
    def acknowledge_alert(self, alert_id: str, user: str, note: str = None) -> bool:
        """Acknowledge an alert."""
        alert = self.get_alert(alert_id)
        if alert:
            alert.acknowledge(user, note)
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str = None, note: str = None) -> bool:
        """Manually resolve an alert."""
        alert = self.get_alert(alert_id)
        if alert:
            alert.resolve(user, note)
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert generation statistics."""
        return {
            **self.stats,
            "active_alerts_count": len(self.get_active_alerts()),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled)
        }
    
    def create_default_rules(self) -> None:
        """Create some default alert rules for common scenarios."""
        # High CPU usage rule
        cpu_rule = AlertRule(
            name="High CPU Usage",
            description="Alert when CPU usage exceeds 80%",
            severity=AlertSeverity.WARNING,
            conditions=[
                AlertCondition(
                    condition_type=AlertConditionType.THRESHOLD,
                    metric_name="cpu_usage_percent",
                    operator="gt",
                    threshold_value=80.0,
                    evaluation_window=timedelta(minutes=5)
                )
            ],
            for_duration=timedelta(minutes=2),
            labels={"category": "system", "resource": "cpu"}
        )
        
        # High memory usage rule
        memory_rule = AlertRule(
            name="High Memory Usage",
            description="Alert when memory usage exceeds 90%",
            severity=AlertSeverity.ERROR,
            conditions=[
                AlertCondition(
                    condition_type=AlertConditionType.THRESHOLD,
                    metric_name="memory_usage_percent",
                    operator="gt",
                    threshold_value=90.0,
                    evaluation_window=timedelta(minutes=5)
                )
            ],
            for_duration=timedelta(minutes=1),
            labels={"category": "system", "resource": "memory"}
        )
        
        # Container restart rule
        restart_rule = AlertRule(
            name="Container Restart",
            description="Alert when container restart count increases",
            severity=AlertSeverity.WARNING,
            conditions=[
                AlertCondition(
                    condition_type=AlertConditionType.THRESHOLD,
                    metric_name="container_restart_count",
                    operator="gt",
                    threshold_value=0,
                    evaluation_window=timedelta(minutes=1)
                )
            ],
            labels={"category": "container", "event": "restart"}
        )
        
        # Add rules
        self.add_rule(cpu_rule)
        self.add_rule(memory_rule)
        self.add_rule(restart_rule)
        
        self.logger.info("Created default alert rules")