"""
Tests for alert models.
"""

import pytest
from datetime import datetime, timedelta

from src.metrics.alerting import Alert, AlertSeverity, AlertStatus
from src.metrics.models import MetricValue


class TestAlert:
    """Test cases for Alert class."""
    
    @pytest.fixture
    def sample_alert(self):
        """Create a sample alert for testing."""
        return Alert(
            name="Test Alert",
            description="Test alert description",
            severity=AlertSeverity.WARNING,
            rule_id="test_rule",
            metric_name="test_metric",
            metric_value=85.0,
            threshold=80.0,
            condition=">",
            labels={"host": "server1", "env": "prod"}
        )
    
    def test_alert_creation(self, sample_alert):
        """Test alert creation."""
        assert sample_alert.name == "Test Alert"
        assert sample_alert.severity == AlertSeverity.WARNING
        assert sample_alert.status == AlertStatus.PENDING
        assert sample_alert.metric_value == 85.0
        assert sample_alert.threshold == 80.0
        assert sample_alert.condition == ">"
        assert sample_alert.labels["host"] == "server1"
        assert not sample_alert.notified
        assert sample_alert.notification_attempts == 0
    
    def test_alert_fire(self, sample_alert):
        """Test firing an alert."""
        assert sample_alert.status == AlertStatus.PENDING
        assert sample_alert.fired_at is None
        
        sample_alert.fire()
        
        assert sample_alert.status == AlertStatus.FIRING
        assert sample_alert.fired_at is not None
        assert isinstance(sample_alert.fired_at, datetime)
    
    def test_alert_resolve(self, sample_alert):
        """Test resolving an alert."""
        # First fire the alert
        sample_alert.fire()
        assert sample_alert.status == AlertStatus.FIRING
        
        # Then resolve it
        sample_alert.resolve()
        
        assert sample_alert.status == AlertStatus.RESOLVED
        assert sample_alert.resolved_at is not None
        assert isinstance(sample_alert.resolved_at, datetime)
    
    def test_alert_acknowledge(self, sample_alert):
        """Test acknowledging an alert."""
        sample_alert.acknowledge()
        
        assert sample_alert.status == AlertStatus.ACKNOWLEDGED
        assert sample_alert.updated_at is not None
    
    def test_alert_silence(self, sample_alert):
        """Test silencing an alert."""
        sample_alert.silence()
        
        assert sample_alert.status == AlertStatus.SILENCED
        assert sample_alert.updated_at is not None
    
    def test_mark_notified(self, sample_alert):
        """Test marking alert as notified."""
        assert not sample_alert.notified
        assert sample_alert.notification_attempts == 0
        assert sample_alert.last_notification_at is None
        
        sample_alert.mark_notified()
        
        assert sample_alert.notified
        assert sample_alert.notification_attempts == 1
        assert sample_alert.last_notification_at is not None
        
        # Mark notified again
        sample_alert.mark_notified()
        assert sample_alert.notification_attempts == 2
    
    def test_alert_to_dict(self, sample_alert):
        """Test converting alert to dictionary."""
        alert_dict = sample_alert.to_dict()
        
        assert alert_dict["name"] == "Test Alert"
        assert alert_dict["severity"] == "warning"
        assert alert_dict["status"] == "pending"
        assert alert_dict["metric_value"] == 85.0
        assert alert_dict["threshold"] == 80.0
        assert alert_dict["condition"] == ">"
        assert alert_dict["labels"]["host"] == "server1"
        assert "created_at" in alert_dict
        assert "updated_at" in alert_dict
    
    def test_alert_from_dict(self, sample_alert):
        """Test creating alert from dictionary."""
        alert_dict = sample_alert.to_dict()
        restored_alert = Alert.from_dict(alert_dict)
        
        assert restored_alert.name == sample_alert.name
        assert restored_alert.severity == sample_alert.severity
        assert restored_alert.status == sample_alert.status
        assert restored_alert.metric_value == sample_alert.metric_value
        assert restored_alert.threshold == sample_alert.threshold
        assert restored_alert.condition == sample_alert.condition
        assert restored_alert.labels == sample_alert.labels
    
    def test_alert_with_source_metrics(self):
        """Test alert with source metrics."""
        source_metric = MetricValue(
            name="test_metric",
            value=85.0,
            timestamp=datetime.now(),
            labels={"host": "server1"}
        )
        
        alert = Alert(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.ERROR,
            rule_id="test_rule",
            metric_name="test_metric",
            metric_value=85.0,
            threshold=80.0,
            condition=">",
            source_metrics=[source_metric]
        )
        
        assert len(alert.source_metrics) == 1
        assert alert.source_metrics[0].name == "test_metric"
        assert alert.source_metrics[0].value == 85.0


class TestAlertSeverity:
    """Test cases for AlertSeverity enum."""
    
    def test_severity_values(self):
        """Test severity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"
    
    def test_severity_ordering(self):
        """Test that we can compare severities."""
        # Note: Enum comparison is by definition order, not value
        severities = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        assert len(set(severities)) == 4  # All unique


class TestAlertStatus:
    """Test cases for AlertStatus enum."""
    
    def test_status_values(self):
        """Test status enum values."""
        assert AlertStatus.PENDING.value == "pending"
        assert AlertStatus.FIRING.value == "firing"
        assert AlertStatus.RESOLVED.value == "resolved"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlertStatus.SILENCED.value == "silenced"
    
    def test_status_transitions(self):
        """Test valid status transitions."""
        alert = Alert(
            name="Test",
            description="Test",
            severity=AlertSeverity.INFO,
            rule_id="test",
            metric_name="test",
            metric_value=1,
            threshold=0,
            condition=">"
        )
        
        # Initial state
        assert alert.status == AlertStatus.PENDING
        
        # Fire alert
        alert.fire()
        assert alert.status == AlertStatus.FIRING
        
        # Resolve alert
        alert.resolve()
        assert alert.status == AlertStatus.RESOLVED
        
        # Test other transitions
        alert.status = AlertStatus.FIRING
        alert.acknowledge()
        assert alert.status == AlertStatus.ACKNOWLEDGED
        
        alert.status = AlertStatus.FIRING
        alert.silence()
        assert alert.status == AlertStatus.SILENCED