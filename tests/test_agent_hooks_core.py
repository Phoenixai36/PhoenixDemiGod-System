"""
Tests for the core hook framework infrastructure.

This module contains tests for the core hook framework components,
including models, configuration management, and logging.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from src.agent_hooks.core.models import (
    AgentHook, HookContext, HookResult, HookPriority, HookTrigger
)
from src.agent_hooks.utils.logging import (
    StructuredLogger, ErrorReporter, HookError, ErrorCategory, ErrorSeverity
)
from src.agent_hooks.hooks.example_hook import ExampleHook


class TestHookModels:
    """Tests for the core hook models."""
    
    def test_hook_context(self):
        """Test HookContext creation and methods."""
        # Create a basic context
        context = HookContext(
            trigger_event={"type": "file_save", "file_path": "test.py"},
            project_state={"branch": "main"},
            system_metrics={"cpu": 0.5, "memory": 0.7},
            user_preferences={"auto_fix": True}
        )
        
        # Check that the context has the expected values
        assert context.trigger_event["type"] == "file_save"
        assert context.project_state["branch"] == "main"
        assert context.system_metrics["cpu"] == 0.5
        assert context.user_preferences["auto_fix"] is True
        assert isinstance(context.execution_id, str)
        assert isinstance(context.timestamp, datetime)
        
        # Test with_updated_metrics
        updated_context = context.with_updated_metrics({"disk": 0.3})
        assert updated_context.system_metrics["cpu"] == 0.5
        assert updated_context.system_metrics["disk"] == 0.3
        
        # Test with_execution_record
        record = {"hook_id": "test", "status": "success"}
        record_context = context.with_execution_record(record)
        assert len(record_context.execution_history) == 1
        assert record_context.execution_history[0] == record
    
    def test_hook_result(self):
        """Test HookResult creation and methods."""
        # Create a basic result
        result = HookResult(
            success=True,
            message="Test successful",
            actions_taken=["Action 1", "Action 2"],
            suggestions=["Suggestion 1"],
            metrics={"time": 100},
            artifacts=["artifact1.txt"]
        )
        
        # Check that the result has the expected values
        assert result.success is True
        assert result.message == "Test successful"
        assert len(result.actions_taken) == 2
        assert len(result.suggestions) == 1
        assert result.metrics["time"] == 100
        assert len(result.artifacts) == 1
        
        # Test success_result factory method
        success = HookResult.success_result("Success message")
        assert success.success is True
        assert success.message == "Success message"
        
        # Test error_result factory method
        error = HookResult.error_result("Error message", Exception("Test error"))
        assert error.success is False
        assert error.message == "Error message"
        assert isinstance(error.error, Exception)
        
        # Test with_execution_time
        timed_result = result.with_execution_time(123.45)
        assert timed_result.execution_time_ms == 123.45


class TestExampleHook:
    """Tests for the ExampleHook implementation."""
    
    @pytest.fixture
    def example_hook(self):
        """Create an example hook for testing."""
        config = {
            "name": "TestHook",
            "description": "A test hook",
            "message": "Test message",
            "triggers": ["file_save", "manual"]
        }
        return ExampleHook(config)
    
    @pytest.fixture
    def context(self):
        """Create a hook context for testing."""
        return HookContext(
            trigger_event={"type": "file_save", "file_path": "test.py"},
            project_state={"branch": "main"},
            system_metrics={"cpu": 0.5, "memory": 0.7},
            user_preferences={"auto_fix": True}
        )
    
    @pytest.mark.asyncio
    async def test_should_execute(self, example_hook, context):
        """Test the should_execute method."""
        # Should execute for file_save event
        assert await example_hook.should_execute(context) is True
        
        # Should not execute for other event types
        context.trigger_event["type"] = "unknown"
        assert await example_hook.should_execute(context) is False
        
        # Should not execute if disabled
        example_hook.enabled = False
        context.trigger_event["type"] = "file_save"
        assert await example_hook.should_execute(context) is False
    
    @pytest.mark.asyncio
    async def test_execute(self, example_hook, context):
        """Test the execute method."""
        result = await example_hook.execute(context)
        
        assert result.success is True
        assert result.message == "Test message"
        assert len(result.actions_taken) == 1
        assert len(result.suggestions) == 1
        assert "execution_time_ms" in result.metrics
        assert result.execution_time_ms is not None
    
    def test_get_resource_requirements(self, example_hook):
        """Test the get_resource_requirements method."""
        requirements = example_hook.get_resource_requirements()
        
        assert "cpu" in requirements
        assert "memory_mb" in requirements
        assert "disk_mb" in requirements
        assert "network" in requirements


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
