"""
Test the basic structure and imports for Phoenix System Review Tool
"""

import pytest
from datetime import datetime

def test_imports():
    """Test that all core imports work correctly"""
    from src.phoenix_system_review.models.data_models import (
        Component, ComponentCategory, Priority, TaskStatus, EvaluationResult, Gap, TODOTask
    )
    from src.phoenix_system_review.core.interfaces import (
        DiscoveryEngine, AnalysisEngine, AssessmentEngine, ReportingEngine
    )
    
    # Test that enums work
    assert ComponentCategory.INFRASTRUCTURE.value == "infrastructure"
    assert Priority.CRITICAL.value == "critical"
    assert TaskStatus.COMPLETE.value == "complete"


def test_component_creation():
    """Test creating a Component instance"""
    from src.phoenix_system_review.models.data_models import Component, ComponentCategory, ComponentStatus
    
    component = Component(
        name="NCA Toolkit",
        category=ComponentCategory.INFRASTRUCTURE,
        path="/src/nca_toolkit",
        dependencies=["database", "storage"],
        status=ComponentStatus.OPERATIONAL
    )
    
    assert component.name == "NCA Toolkit"
    assert component.category == ComponentCategory.INFRASTRUCTURE
    assert len(component.dependencies) == 2
    assert component.status == ComponentStatus.OPERATIONAL


def test_evaluation_result():
    """Test creating an EvaluationResult instance"""
    from src.phoenix_system_review.models.data_models import (
        Component, ComponentCategory, ComponentStatus, EvaluationResult, Issue, Priority
    )
    
    component = Component(
        name="Test Component",
        category=ComponentCategory.INFRASTRUCTURE,
        path="/test",
        status=ComponentStatus.OPERATIONAL
    )
    
    issue = Issue(
        severity=Priority.HIGH,
        description="Missing health check endpoint",
        component="Test Component"
    )
    
    result = EvaluationResult(
        component=component,
        criteria_met=["has_configuration", "has_documentation"],
        criteria_missing=["has_health_check"],
        completion_percentage=75.0,
        quality_score=80.0,
        issues=[issue]
    )
    
    assert result.completion_percentage == 75.0
    assert not result.is_complete
    assert len(result.issues) == 1
    assert result.issues[0].severity == Priority.HIGH


def test_todo_task():
    """Test creating a TODOTask instance"""
    from src.phoenix_system_review.models.data_models import TODOTask, Priority, TaskStatus
    
    task = TODOTask(
        id="TASK-001",
        title="Implement health check endpoint",
        description="Add health check endpoint to NCA Toolkit API",
        category="infrastructure",
        priority=Priority.HIGH,
        status=TaskStatus.NOT_STARTED,
        effort_hours=8,
        dependencies=["database_setup"],
        acceptance_criteria=["Endpoint returns 200 OK", "Includes service status"]
    )
    
    assert task.effort_days == 1.0
    assert task.is_blocked  # Has dependencies and not started
    assert task.priority == Priority.HIGH


def test_gap_creation():
    """Test creating a Gap instance"""
    from src.phoenix_system_review.models.data_models import Gap, ImpactLevel, ComponentCategory, Priority
    
    gap = Gap(
        component="NCA Toolkit",
        description="Missing health check endpoint",
        impact=ImpactLevel.HIGH,
        effort_estimate=16,
        dependencies=["api_framework"],
        acceptance_criteria=["Health endpoint responds", "Status includes all services"],
        category=ComponentCategory.INFRASTRUCTURE,
        priority=Priority.HIGH
    )
    
    assert gap.effort_days == 2.0
    assert gap.impact == ImpactLevel.HIGH
    assert len(gap.acceptance_criteria) == 2


if __name__ == "__main__":
    pytest.main([__file__])