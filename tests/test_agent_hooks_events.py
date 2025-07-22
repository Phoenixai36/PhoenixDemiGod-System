"""
Tests for event data models and schemas.

This module contains tests for the event models, serialization, and validation
functionality in the Agent Hooks Enhancement system.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.agent_hooks.events.models import (
    BaseEvent, FileEvent, MetricEvent, SystemEvent, GitEvent, BuildEvent, DependencyEvent,
    EventType, EventSeverity, MetricThreshold, EventSerializer, EventValidator
)


class TestEventModels:
    """Tests for the event models."""
    
    def test_base_event(self):
        """Test BaseEvent creation and methods."""
        # Create a basic event
        event = BaseEvent(
            source="test",
            type=EventType.MANUAL,
            data={"key": "value"},
            context={"user": "test_user"}
        )
        
        # Check that the event has the expected values
        assert event.source == "test"
        assert event.type == EventType.MANUAL
        assert event.data["key"] == "value"
        assert event.context["user"] == "test_user"
        assert isinstance(event.id, str)
        assert isinstance(event.timestamp, datetime)
        assert event.correlation_id is None
        assert event.severity == EventSeverity.INFO
        
        # Test with_correlation
        correlated_event = event.with_correlation("correlation-123")
        assert correlated_event.correlation_id == "correlation-123"
        
        # Test with_context
        context_event = event.with_context({"session": "abc123"})
        assert context_event.context["user"] == "test_user"
        assert context_event.context["session"] == "abc123"
        
        # Test to_json and from_json
        json_str = event.to_json()
        assert isinstance(json_str, str)
        
        parsed_event = BaseEvent.from_json(json_str)
        assert parsed_event.source == event.source
        assert parsed_event.type == event.type
        assert parsed_event.data == event.data
        assert parsed_event.context == event.context
    
    def test_file_event(self):
        """Test FileEvent creation and methods."""
        # Create a file save event
        event = FileEvent.create_save_event(
            file_path="test.py",
            content_hash="abc123",
            data={"size": 1024}
        )
        
        # Check that the event has the expected values
        assert event.source == "file_system"
        assert event.type == EventType.FILE_SAVE
        assert isinstance(event.file_path, Path)
        assert str(event.file_path) == "test.py"
        assert event.file_type == "py"
        assert event.operation == "save"
        assert event.content_hash == "abc123"
        assert event.data["size"] == 1024
        
        # Test create_create_event
        create_event = FileEvent.create_create_event(
            file_path="new_file.txt"
        )
        assert create_event.type == EventType.FILE_CREATE
        assert str(create_event.file_path) == "new_file.txt"
        assert create_event.file_type == "txt"
        assert create_event.operation == "create"
        
        # Test create_delete_event
        delete_event = FileEvent.create_delete_event(
            file_path="delete_file.js"
        )
        assert delete_event.type == EventType.FILE_DELETE
        assert str(delete_event.file_path) == "delete_file.js"
        assert delete_event.file_type == "js"
        assert delete_event.operation == "delete"
        
        # Test create_modify_event
        modify_event = FileEvent.create_modify_event(
            file_path="modify_file.css",
            content_hash="def456"
        )
        assert modify_event.type == EventType.FILE_MODIFY
        assert str(modify_event.file_path) == "modify_file.css"
        assert modify_event.file_type == "css"
        assert modify_event.operation == "modify"
        assert modify_event.content_hash == "def456"
        
        # Test create_rename_event
        rename_event = FileEvent.create_rename_event(
            old_path="old_name.html",
            new_path="new_name.html"
        )
        assert rename_event.type == EventType.FILE_RENAME
        assert str(rename_event.file_path) == "new_name.html"
        assert str(rename_event.old_path) == "old_name.html"
        assert rename_event.file_type == "html"
        assert rename_event.operation == "rename"
        
        # Test validation
        with pytest.raises(ValueError):
            # Invalid operation
            FileEvent(
                source="file_system",
                type=EventType.FILE_SAVE,
                file_path="test.py",
                file_type="py",
                operation="invalid"
            )
        
        with pytest.raises(ValueError):
            # Missing old_path for rename operation
            FileEvent(
                source="file_system",
                type=EventType.FILE_RENAME,
                file_path="new_name.html",
                file_type="html",
                operation="rename"
            )
    
    def test_metric_event(self):
        """Test MetricEvent creation and methods."""
        # Create a metric threshold event
        event = MetricEvent.create_threshold_event(
            metric_name="cpu_usage",
            value=85.0,
            threshold_value=80.0,
            comparison="gt",
            duration_seconds=300,
            data={"host": "server1"}
        )
        
        # Check that the event has the expected values
        assert event.source == "metrics"
        assert event.type == EventType.METRIC_THRESHOLD
        assert event.metric_name == "cpu_usage"
        assert event.value == 85.0
        assert event.threshold.value == 80.0
        assert event.threshold.comparison == "gt"
        assert event.threshold.duration_seconds == 300
        assert event.duration_seconds == 300
        assert event.data["host"] == "server1"
        assert event.severity == EventSeverity.MEDIUM  # Based on threshold
        
        # Test threshold.is_exceeded
        assert event.threshold.is_exceeded(85.0, 300)
        assert not event.threshold.is_exceeded(75.0, 300)
        assert not event.threshold.is_exceeded(85.0, 200)
        
        # Test different comparisons
        lt_threshold = MetricThreshold(value=80.0, comparison="lt")
        assert lt_threshold.is_exceeded(75.0)
        assert not lt_threshold.is_exceeded(85.0)
        
        gte_threshold = MetricThreshold(value=80.0, comparison="gte")
        assert gte_threshold.is_exceeded(80.0)
        assert gte_threshold.is_exceeded(85.0)
        assert not gte_threshold.is_exceeded(75.0)
        
        lte_threshold = MetricThreshold(value=80.0, comparison="lte")
        assert lte_threshold.is_exceeded(80.0)
        assert lte_threshold.is_exceeded(75.0)
        assert not lte_threshold.is_exceeded(85.0)
        
        eq_threshold = MetricThreshold(value=80.0, comparison="eq")
        assert eq_threshold.is_exceeded(80.0)
        assert not eq_threshold.is_exceeded(85.0)
        assert not eq_threshold.is_exceeded(75.0)
        
        neq_threshold = MetricThreshold(value=80.0, comparison="neq")
        assert neq_threshold.is_exceeded(85.0)
        assert neq_threshold.is_exceeded(75.0)
        assert not neq_threshold.is_exceeded(80.0)
        
        # Test validation
        with pytest.raises(ValueError):
            # Invalid comparison
            MetricThreshold(value=80.0, comparison="invalid")
    
    def test_system_event(self):
        """Test SystemEvent creation and methods."""
        # Create a service health event
        event = SystemEvent.create_service_health_event(
            component="api_server",
            status="degraded",
            details={"error": "High latency"},
            affected_services=["auth", "payments"]
        )
        
        # Check that the event has the expected values
        assert event.source == "system"
        assert event.type == EventType.SERVICE_HEALTH
        assert event.component == "api_server"
        assert event.status == "degraded"
        assert event.details["error"] == "High latency"
        assert "auth" in event.affected_services
        assert "payments" in event.affected_services
        assert event.severity == EventSeverity.HIGH  # Based on status
        
        # Test different statuses
        critical_event = SystemEvent.create_service_health_event(
            component="database",
            status="down"
        )
        assert critical_event.severity == EventSeverity.CRITICAL
        
        warning_event = SystemEvent.create_service_health_event(
            component="cache",
            status="warning"
        )
        assert warning_event.severity == EventSeverity.HIGH
        
        info_event = SystemEvent.create_service_health_event(
            component="logger",
            status="up"
        )
        assert info_event.severity == EventSeverity.INFO
    
    def test_git_event(self):
        """Test GitEvent creation and methods."""
        # Create a git commit event
        event = GitEvent.create_commit_event(
            repository="my-repo",
            branch="main",
            commit_hash="abc123",
            author="test@example.com",
            message="Fix bug",
            files_changed=["src/main.py", "tests/test_main.py"]
        )
        
        # Check that the event has the expected values
        assert event.source == "git"
        assert event.type == EventType.GIT_COMMIT
        assert event.repository == "my-repo"
        assert event.branch == "main"
        assert event.commit_hash == "abc123"
        assert event.author == "test@example.com"
        assert event.message == "Fix bug"
        assert len(event.files_changed) == 2
        assert "src/main.py" in event.files_changed
        assert "tests/test_main.py" in event.files_changed
    
    def test_build_event(self):
        """Test BuildEvent creation and methods."""
        # Create a build success event
        success_event = BuildEvent.create_build_success_event(
            project="my-project",
            build_id="build-123",
            build_type="production",
            duration_seconds=120.5,
            artifacts=["dist/app.js", "dist/app.css"]
        )
        
        # Check that the event has the expected values
        assert success_event.source == "build"
        assert success_event.type == EventType.BUILD_SUCCESS
        assert success_event.project == "my-project"
        assert success_event.build_id == "build-123"
        assert success_event.build_type == "production"
        assert success_event.duration_seconds == 120.5
        assert len(success_event.artifacts) == 2
        assert "dist/app.js" in success_event.artifacts
        assert "dist/app.css" in success_event.artifacts
        assert len(success_event.errors) == 0
        assert success_event.severity == EventSeverity.INFO
        
        # Create a build failure event
        failure_event = BuildEvent.create_build_failure_event(
            project="my-project",
            build_id="build-124",
            build_type="production",
            duration_seconds=45.2,
            errors=["Failed to compile", "Missing dependency"]
        )
        
        # Check that the event has the expected values
        assert failure_event.source == "build"
        assert failure_event.type == EventType.BUILD_FAILURE
        assert failure_event.project == "my-project"
        assert failure_event.build_id == "build-124"
        assert failure_event.build_type == "production"
        assert failure_event.duration_seconds == 45.2
        assert len(failure_event.errors) == 2
        assert "Failed to compile" in failure_event.errors
        assert "Missing dependency" in failure_event.errors
        assert len(failure_event.artifacts) == 0
        assert failure_event.severity == EventSeverity.HIGH
    
    def test_dependency_event(self):
        """Test DependencyEvent creation and methods."""
        # Create a dependency vulnerability event
        vulnerabilities = [
            {
                "id": "CVE-2023-1234",
                "description": "Remote code execution vulnerability",
                "severity": "critical",
                "fixed_in": "1.2.3"
            },
            {
                "id": "CVE-2023-5678",
                "description": "Information disclosure vulnerability",
                "severity": "medium",
                "fixed_in": "1.2.3"
            }
        ]
        
        event = DependencyEvent.create_vulnerability_event(
            package_name="vulnerable-package",
            package_version="1.1.0",
            package_type="npm",
            vulnerabilities=vulnerabilities
        )
        
        # Check that the event has the expected values
        assert event.source == "dependencies"
        assert event.type == EventType.DEPENDENCY_VULNERABILITY
        assert event.package_name == "vulnerable-package"
        assert event.package_version == "1.1.0"
        assert event.package_type == "npm"
        assert len(event.vulnerabilities) == 2
        assert event.vulnerabilities[0]["id"] == "CVE-2023-1234"
        assert event.vulnerabilities[1]["id"] == "CVE-2023-5678"
        assert event.severity == EventSeverity.CRITICAL  # Based on highest vulnerability severity


class TestEventSerializer:
    """Tests for the EventSerializer class."""
    
    def test_serialize_deserialize(self):
        """Test serializing and deserializing events."""
        # Create a file event
        original_event = FileEvent.create_save_event(
            file_path="test.py",
            content_hash="abc123"
        )
        
        # Serialize to dictionary
        serialized = EventSerializer.serialize(original_event)
        assert isinstance(serialized, dict)
        assert serialized["source"] == "file_system"
        assert serialized["type"] == "file_save"
        assert serialized["file_path"] == "test.py"
        
        # Deserialize from dictionary
        deserialized = EventSerializer.deserialize(serialized)
        assert isinstance(deserialized, FileEvent)
        assert deserialized.source == original_event.source
        assert deserialized.type == original_event.type
        assert str(deserialized.file_path) == str(original_event.file_path)
        assert deserialized.content_hash == original_event.content_hash
        
        # Serialize to JSON
        json_str = EventSerializer.to_json(original_event)
        assert isinstance(json_str, str)
        
        # Deserialize from JSON
        from_json = EventSerializer.from_json(json_str)
        assert isinstance(from_json, FileEvent)
        assert from_json.source == original_event.source
        assert from_json.type == original_event.type
        assert str(from_json.file_path) == str(original_event.file_path)
        assert from_json.content_hash == original_event.content_hash
    
    def test_deserialize_different_event_types(self):
        """Test deserializing different event types."""
        # Test FileEvent
        file_data = {
            "source": "file_system",
            "type": "file_save",
            "file_path": "test.py",
            "file_type": "py",
            "operation": "save"
        }
        file_event = EventSerializer.deserialize(file_data)
        assert isinstance(file_event, FileEvent)
        
        # Test MetricEvent
        metric_data = {
            "source": "metrics",
            "type": "metric_threshold",
            "metric_name": "cpu_usage",
            "value": 85.0
        }
        metric_event = EventSerializer.deserialize(metric_data)
        assert isinstance(metric_event, MetricEvent)
        
        # Test SystemEvent
        system_data = {
            "source": "system",
            "type": "service_health",
            "component": "api_server",
            "status": "degraded"
        }
        system_event = EventSerializer.deserialize(system_data)
        assert isinstance(system_event, SystemEvent)
        
        # Test GitEvent
        git_data = {
            "source": "git",
            "type": "git_commit",
            "repository": "my-repo",
            "branch": "main"
        }
        git_event = EventSerializer.deserialize(git_data)
        assert isinstance(git_event, GitEvent)
        
        # Test BuildEvent
        build_data = {
            "source": "build",
            "type": "build_success",
            "project": "my-project",
            "build_id": "build-123",
            "build_type": "production"
        }
        build_event = EventSerializer.deserialize(build_data)
        assert isinstance(build_event, BuildEvent)
        
        # Test DependencyEvent
        dependency_data = {
            "source": "dependencies",
            "type": "dependency_vulnerability",
            "package_name": "vulnerable-package",
            "package_type": "npm"
        }
        dependency_event = EventSerializer.deserialize(dependency_data)
        assert isinstance(dependency_event, DependencyEvent)
        
        # Test unknown event type
        unknown_data = {
            "source": "unknown",
            "type": "custom",
            "data": {"custom": "data"}
        }
        unknown_event = EventSerializer.deserialize(unknown_data)
        assert isinstance(unknown_event, BaseEvent)
        assert not isinstance(unknown_event, FileEvent)
        assert not isinstance(unknown_event, MetricEvent)
    
    def test_invalid_json(self):
        """Test deserializing invalid JSON."""
        with pytest.raises(ValueError):
            EventSerializer.from_json("invalid json")
    
    def test_missing_type(self):
        """Test deserializing event with missing type."""
        with pytest.raises(ValueError):
            EventSerializer.deserialize({"source": "test"})


class TestEventValidator:
    """Tests for the EventValidator class."""
    
    def test_validate_base_event(self):
        """Test validating a base event."""
        # Valid event
        event = BaseEvent(
            source="test",
            type=EventType.MANUAL
        )
        errors = EventValidator.validate(event)
        assert len(errors) == 0
        
        # Missing source
        invalid_event = BaseEvent(
            source="",
            type=EventType.MANUAL
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "source" in errors[0]
    
    def test_validate_file_event(self):
        """Test validating a file event."""
        # Valid event
        event = FileEvent.create_save_event(
            file_path="test.py"
        )
        errors = EventValidator.validate(event)
        assert len(errors) == 0
        
        # Missing file path
        invalid_event = FileEvent(
            source="file_system",
            type=EventType.FILE_SAVE,
            file_path="",
            file_type="py",
            operation="save"
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "path" in errors[0]
        
        # Missing operation
        invalid_event = FileEvent(
            source="file_system",
            type=EventType.FILE_SAVE,
            file_path="test.py",
            file_type="py",
            operation=""
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "operation" in errors[0]
        
        # Missing old_path for rename operation
        invalid_event = FileEvent(
            source="file_system",
            type=EventType.FILE_RENAME,
            file_path="new_name.py",
            file_type="py",
            operation="rename"
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "path" in errors[0]
    
    def test_validate_metric_event(self):
        """Test validating a metric event."""
        # Valid event
        event = MetricEvent.create_threshold_event(
            metric_name="cpu_usage",
            value=85.0,
            threshold_value=80.0
        )
        errors = EventValidator.validate(event)
        assert len(errors) == 0
        
        # Missing metric name
        invalid_event = MetricEvent(
            source="metrics",
            type=EventType.METRIC_THRESHOLD,
            metric_name="",
            value=85.0
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "metric" in errors[0]
    
    def test_validate_system_event(self):
        """Test validating a system event."""
        # Valid event
        event = SystemEvent.create_service_health_event(
            component="api_server",
            status="degraded"
        )
        errors = EventValidator.validate(event)
        assert len(errors) == 0
        
        # Missing component
        invalid_event = SystemEvent(
            source="system",
            type=EventType.SERVICE_HEALTH,
            component="",
            status="degraded"
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "component" in errors[0]
        
        # Missing status
        invalid_event = SystemEvent(
            source="system",
            type=EventType.SERVICE_HEALTH,
            component="api_server",
            status=""
        )
        errors = EventValidator.validate(invalid_event)
        assert len(errors) > 0
        assert "status" in errors[0]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
