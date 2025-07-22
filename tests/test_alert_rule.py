"""
Tests for alert rules.
"""

import pytest
from datetime import datetime, timedelta

from src.metrics.alerting import (
    AlertCondition, AlertRule, AlertRuleEngine, AlertSeverity, AlertStatus,
    create_cpu_usage_rule, create_memory_usage_rule, create_disk_usage_rule
)
from src.metrics.models import MetricValue


class TestAlertCondition:
    """Test cases for AlertCondition."""
    
    def test_simple_condition_evaluation(self):
        """Test simple condition evaluation."""
        condition = AlertCondition(
            metric_name="cpu_usage",
            operator="gt",
            threshold=80.0
        )
        
        # Matching metric above threshold
        metric_high = MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={})
        assert condition.evaluate(metric_high) is True
        
        # Matching metric below threshold
        metric_low = MetricValue(name="cpu_usage", value=75.0, timestamp=datetime.now(), labels={})
        assert condition.evaluate(metric_low) is False
        
        # Non-matching metric name
        metric_wrong = MetricValue(name="memory_usage", value=85.0, timestamp=datetime.now(), labels={})
        assert condition.evaluate(metric_wrong) is False
    
    def test_condition_operators(self):
        """Test different condition operators."""
        metric = MetricValue(name="test_metric", value=50.0, timestamp=datetime.now(), labels={})
        
        # Greater than
        condition_gt = AlertCondition("test_metric", "gt", 40.0)
        assert condition_gt.evaluate(metric) is True
        
        condition_gt_false = AlertCondition("test_metric", "gt", 60.0)
        assert condition_gt_false.evaluate(metric) is False
        
        # Less than
        condition_lt = AlertCondition("test_metric", "lt", 60.0)
        assert condition_lt.evaluate(metric) is True
        
        # Equal
        condition_eq = AlertCondition("test_metric", "eq", 50.0)
        assert condition_eq.evaluate(metric) is True
        
        # Not equal
        condition_ne = AlertCondition("test_metric", "ne", 40.0)
        assert condition_ne.evaluate(metric) is True
        
        # Greater than or equal
        condition_gte = AlertCondition("test_metric", "gte", 50.0)
        assert condition_gte.evaluate(metric) is True
        
        # Less than or equal
        condition_lte = AlertCondition("test_metric", "lte", 50.0)
        assert condition_lte.evaluate(metric) is True
    
    def test_condition_with_labels(self):
        """Test condition evaluation with label matching."""
        condition = AlertCondition(
            metric_name="cpu_usage",
            operator="gt",
            threshold=80.0,
            labels_match={"host": "server1", "env": "prod"}
        )
        
        # Matching metric with matching labels
        metric_match = MetricValue(
            name="cpu_usage",
            value=85.0,
            timestamp=datetime.now(),
            labels={"host": "server1", "env": "prod", "region": "us-east"}
        )
        assert condition.evaluate(metric_match) is True
        
        # Matching metric with non-matching labels
        metric_no_match = MetricValue(
            name="cpu_usage",
            value=85.0,
            timestamp=datetime.now(),
            labels={"host": "server2", "env": "prod"}
        )
        assert condition.evaluate(metric_no_match) is False
        
        # Matching metric with missing labels
        metric_missing = MetricValue(
            name="cpu_usage",
            value=85.0,
            timestamp=datetime.now(),
            labels={"host": "server1"}  # Missing "env" label
        )
        assert condition.evaluate(metric_missing) is False
    
    def test_string_conditions(self):
        """Test string-based conditions."""
        metric = MetricValue(name="status", value="error_occurred", timestamp=datetime.now(), labels={})
        
        # Contains
        condition_contains = AlertCondition("status", "contains", "error")
        assert condition_contains.evaluate(metric) is True
        
        # Regex
        condition_regex = AlertCondition("status", "regex", r"error_\w+")
        assert condition_regex.evaluate(metric) is True
        
        condition_regex_false = AlertCondition("status", "regex", r"success_\w+")
        assert condition_regex_false.evaluate(metric) is False
    
    def test_operator_symbols(self):
        """Test operator symbol conversion."""
        condition = AlertCondition("test", "gt", 10)
        assert condition.get_operator_symbol() == ">"
        
        condition = AlertCondition("test", "lt", 10)
        assert condition.get_operator_symbol() == "<"
        
        condition = AlertCondition("test", "eq", 10)
        assert condition.get_operator_symbol() == "=="
        
        condition = AlertCondition("test", "ne", 10)
        assert condition.get_operator_symbol() == "!="
        
        condition = AlertCondition("test", "gte", 10)
        assert condition.get_operator_symbol() == ">="
        
        condition = AlertCondition("test", "lte", 10)
        assert condition.get_operator_symbol() == "<="


class TestAlertRule:
    """Test cases for AlertRule."""
    
    @pytest.fixture
    def simple_rule(self):
        """Create a simple alert rule for testing."""
        return AlertRule(
            id="test_rule",
            name="Test Rule",
            description="Test rule description",
            conditions=[
                AlertCondition("cpu_usage", "gt", 80.0)
            ],
            severity=AlertSeverity.WARNING
        )
    
    def test_rule_creation(self, simple_rule):
        """Test rule creation."""
        assert simple_rule.id == "test_rule"
        assert simple_rule.name == "Test Rule"
        assert simple_rule.severity == AlertSeverity.WARNING
        assert len(simple_rule.conditions) == 1
        assert simple_rule.conditions[0].metric_name == "cpu_usage"
        assert simple_rule.auto_resolve is True
    
    def test_rule_evaluation_simple(self, simple_rule):
        """Test simple rule evaluation."""
        # Metrics that should trigger the rule
        triggering_metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={})
        ]
        
        # First evaluation should not fire (pending state)
        assert simple_rule.evaluate(triggering_metrics) is False
        assert simple_rule.get_status() == AlertStatus.PENDING
        
        # Metrics that should not trigger the rule
        non_triggering_metrics = [
            MetricValue(name="cpu_usage", value=75.0, timestamp=datetime.now(), labels={})
        ]
        
        assert simple_rule.evaluate(non_triggering_metrics) is False
    
    def test_rule_evaluation_with_duration(self):
        """Test rule evaluation with for_duration."""
        rule = AlertRule(
            id="duration_rule",
            name="Duration Rule",
            description="Rule with duration",
            conditions=[AlertCondition("cpu_usage", "gt", 80.0)],
            severity=AlertSeverity.WARNING,
            for_duration=timedelta(minutes=5)
        )
        
        triggering_metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={})
        ]
        
        # First evaluation - should be pending
        assert rule.evaluate(triggering_metrics) is False
        assert rule.get_status() == AlertStatus.PENDING
        
        # Simulate time passing but not enough
        rule._first_detected = datetime.now() - timedelta(minutes=3)
        assert rule.evaluate(triggering_metrics) is False
        
        # Simulate enough time passing
        rule._first_detected = datetime.now() - timedelta(minutes=6)
        assert rule.evaluate(triggering_metrics) is True
        assert rule.get_status() == AlertStatus.FIRING
    
    def test_rule_evaluation_with_throttling(self):
        """Test rule evaluation with throttling."""
        rule = AlertRule(
            id="throttle_rule",
            name="Throttle Rule",
            description="Rule with throttling",
            conditions=[AlertCondition("cpu_usage", "gt", 80.0)],
            severity=AlertSeverity.WARNING,
            throttle_duration=timedelta(minutes=10)
        )
        
        triggering_metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={})
        ]
        
        # First firing
        rule._first_detected = datetime.now() - timedelta(minutes=1)
        assert rule.evaluate(triggering_metrics) is True
        
        # Second evaluation should be throttled
        assert rule.evaluate(triggering_metrics) is False
        
        # After throttle period
        rule._last_fired = datetime.now() - timedelta(minutes=11)
        assert rule.evaluate(triggering_metrics) is True
    
    def test_rule_create_alert(self, simple_rule):
        """Test creating alert from rule."""
        metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={"host": "server1"})
        ]
        
        alert = simple_rule.create_alert(metrics)
        
        assert alert is not None
        assert alert.name == "Test Rule"
        assert alert.rule_id == "test_rule"
        assert alert.metric_name == "cpu_usage"
        assert alert.metric_value == 85.0
        assert alert.threshold == 80.0
        assert alert.condition == ">"
        assert alert.severity == AlertSeverity.WARNING
        assert "host" in alert.labels
        assert alert.labels["host"] == "server1"
    
    def test_rule_multiple_conditions(self):
        """Test rule with multiple conditions."""
        rule = AlertRule(
            id="multi_rule",
            name="Multi Condition Rule",
            description="Rule with multiple conditions",
            conditions=[
                AlertCondition("cpu_usage", "gt", 80.0),
                AlertCondition("memory_usage", "gt", 90.0)
            ],
            severity=AlertSeverity.ERROR
        )
        
        # Only CPU condition met
        cpu_only_metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={}),
            MetricValue(name="memory_usage", value=70.0, timestamp=datetime.now(), labels={})
        ]
        assert rule.evaluate(cpu_only_metrics) is False
        
        # Both conditions met
        both_metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={}),
            MetricValue(name="memory_usage", value=95.0, timestamp=datetime.now(), labels={})
        ]
        rule._first_detected = datetime.now() - timedelta(seconds=1)
        assert rule.evaluate(both_metrics) is True
    
    def test_rule_to_dict_and_from_dict(self, simple_rule):
        """Test rule serialization."""
        rule_dict = simple_rule.to_dict()
        
        assert rule_dict["id"] == "test_rule"
        assert rule_dict["name"] == "Test Rule"
        assert rule_dict["severity"] == "warning"
        assert len(rule_dict["conditions"]) == 1
        
        # Restore from dict
        restored_rule = AlertRule.from_dict(rule_dict)
        assert restored_rule.id == simple_rule.id
        assert restored_rule.name == simple_rule.name
        assert restored_rule.severity == simple_rule.severity
        assert len(restored_rule.conditions) == len(simple_rule.conditions)


class TestAlertRuleEngine:
    """Test cases for AlertRuleEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create an alert rule engine for testing."""
        return AlertRuleEngine()
    
    @pytest.fixture
    def sample_rule(self):
        """Create a sample rule."""
        return AlertRule(
            id="test_rule",
            name="Test Rule",
            description="Test rule",
            conditions=[AlertCondition("cpu_usage", "gt", 80.0)],
            severity=AlertSeverity.WARNING
        )
    
    def test_add_remove_rule(self, engine, sample_rule):
        """Test adding and removing rules."""
        # Add rule
        engine.add_rule(sample_rule)
        assert "test_rule" in engine.rules
        assert engine.get_rule("test_rule") == sample_rule
        
        # Remove rule
        assert engine.remove_rule("test_rule") is True
        assert "test_rule" not in engine.rules
        assert engine.get_rule("test_rule") is None
        
        # Try to remove non-existent rule
        assert engine.remove_rule("non_existent") is False
    
    def test_list_rules(self, engine, sample_rule):
        """Test listing rules."""
        assert len(engine.list_rules()) == 0
        
        engine.add_rule(sample_rule)
        rules = engine.list_rules()
        assert len(rules) == 1
        assert rules[0] == sample_rule
    
    def test_evaluate_rules(self, engine, sample_rule):
        """Test evaluating rules."""
        engine.add_rule(sample_rule)
        
        # Metrics that should trigger
        triggering_metrics = [
            MetricValue(name="cpu_usage", value=85.0, timestamp=datetime.now(), labels={})
        ]
        
        # First evaluation - should not fire yet
        alerts = engine.evaluate_rules(triggering_metrics)
        assert len(alerts) == 0
        
        # Simulate rule being ready to fire
        sample_rule._first_detected = datetime.now() - timedelta(seconds=1)
        alerts = engine.evaluate_rules(triggering_metrics)
        assert len(alerts) == 1
        assert alerts[0].name == "Test Rule"
        assert alerts[0].status == AlertStatus.FIRING
    
    def test_reset_all_rules(self, engine, sample_rule):
        """Test resetting all rules."""
        engine.add_rule(sample_rule)
        
        # Set some state
        sample_rule._first_detected = datetime.now()
        sample_rule._firing_count = 5
        
        # Reset
        engine.reset_all_rules()
        
        assert sample_rule._first_detected is None
        assert sample_rule._firing_count == 0


class TestStandardRules:
    """Test cases for standard rule creators."""
    
    def test_create_cpu_usage_rule(self):
        """Test creating CPU usage rule."""
        rule = create_cpu_usage_rule(threshold=85.0, duration_minutes=3)
        
        assert rule.id == "cpu_usage_high"
        assert rule.name == "High CPU Usage"
        assert rule.severity == AlertSeverity.WARNING
        assert len(rule.conditions) == 1
        assert rule.conditions[0].metric_name == "cpu_usage_percent"
        assert rule.conditions[0].threshold == 85.0
        assert rule.for_duration == timedelta(minutes=3)
        assert rule.throttle_duration == timedelta(minutes=15)
    
    def test_create_memory_usage_rule(self):
        """Test creating memory usage rule."""
        rule = create_memory_usage_rule(threshold=90.0, duration_minutes=2)
        
        assert rule.id == "memory_usage_high"
        assert rule.name == "High Memory Usage"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.conditions[0].metric_name == "memory_usage_percent"
        assert rule.conditions[0].threshold == 90.0
        assert rule.for_duration == timedelta(minutes=2)
    
    def test_create_disk_usage_rule(self):
        """Test creating disk usage rule."""
        rule = create_disk_usage_rule(threshold=95.0, duration_minutes=1)
        
        assert rule.id == "disk_usage_high"
        assert rule.name == "High Disk Usage"
        assert rule.severity == AlertSeverity.ERROR
        assert rule.conditions[0].metric_name == "disk_usage_percent"
        assert rule.conditions[0].threshold == 95.0
        assert rule.for_duration == timedelta(minutes=1)