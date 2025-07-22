"""
Tests for the Example Hook.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

# Add the .kiro directory to the Python path
kiro_path = Path(__file__).parent.parent / ".kiro"
sys.path.insert(0, str(kiro_path))

from engine.hooks.example_hook import ExampleHook
from engine.core.models import HookContext
from engine.events.models import EventType


class TestExampleHook:
    """Test the ExampleHook class."""
    
    @pytest.fixture
    def hook_config(self):
        """Create a basic hook configuration."""
        return {
            "id": "test_example_hook",
            "name": "Test Example Hook",
            "enabled": True,
            "message": "Test message from example hook",
            "execution_delay": 0.01,  # Very short delay for tests
            "max_executions": 10,
            "log_level": "info",
            "simulate_work": True,
            "custom_actions": ["count_event_data", "simulate_delay"]
        }
    
    @pytest.fixture
    def hook(self, hook_config):
        """Create a hook instance."""
        return ExampleHook(hook_config)
    
    @pytest.fixture
    def custom_context(self):
        """Create a context for custom events."""
        return HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {
                    "test_field": "test_value",
                    "number_field": 42
                }
            },
            project_state={"project_name": "test_project"},
            system_metrics={"cpu_usage": 50.0, "memory_usage": 60.0},
            user_preferences={"theme": "dark"}
        )
    
    @pytest.fixture
    def manual_context(self):
        """Create a context for manual events."""
        return HookContext(
            trigger_event={
                "type": EventType.MANUAL.value,
                "data": {"user_id": "test_user"}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    def test_hook_initialization(self, hook, hook_config):
        """Test hook initialization."""
        assert hook.id == "test_example_hook"
        assert hook.name == "Test Example Hook"
        assert hook.enabled is True
        assert hook.message == "Test message from example hook"
        assert hook.execution_delay == 0.01
        assert hook.max_executions == 10
        assert hook.log_level == "info"
        assert hook.simulate_work is True
        assert hook.custom_actions == ["count_event_data", "simulate_delay"]
        assert hook.execution_count == 0
        assert len(hook.execution_history) == 0
    
    @pytest.mark.asyncio
    async def test_should_execute_enabled_hook(self, hook, custom_context):
        """Test that enabled hook should execute for valid events."""
        result = await hook.should_execute(custom_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_execute_disabled_hook(self, hook_config, custom_context):
        """Test that disabled hook should not execute."""
        hook_config["enabled"] = False
        hook = ExampleHook(hook_config)
        
        result = await hook.should_execute(custom_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_max_executions_reached(self, hook, custom_context):
        """Test that hook should not execute when max executions are reached."""
        # Set execution count to maximum
        hook.execution_count = hook.max_executions
        
        result = await hook.should_execute(custom_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_rate_limited(self, hook, custom_context):
        """Test that hook respects rate limiting."""
        # Set last execution time to very recent
        hook.last_execution_time = time.time()
        
        result = await hook.should_execute(custom_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_skip_flag(self, hook):
        """Test that hook respects skip flag in event data."""
        context = HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {"skip_example_hook": True}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_successful(self, hook, custom_context):
        """Test successful hook execution."""
        result = await hook.execute(custom_context)
        
        assert result.success is True
        assert "Test message from example hook" in result.message
        assert len(result.actions_taken) > 0
        assert hook.execution_count == 1
        assert len(hook.execution_history) == 1
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
        
        # Check that custom actions were executed
        action_descriptions = " ".join(result.actions_taken)
        assert "Simulated work" in action_descriptions
        assert "Logged message" in action_descriptions
        assert "custom action" in action_descriptions
    
    @pytest.mark.asyncio
    async def test_execute_with_different_log_levels(self, hook_config):
        """Test execution with different log levels."""
        log_levels = ["debug", "info", "warning", "error"]
        
        for log_level in log_levels:
            hook_config["log_level"] = log_level
            hook = ExampleHook(hook_config)
            
            context = HookContext(
                trigger_event={"type": EventType.CUSTOM.value, "data": {}},
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            
            result = await hook.execute(context)
            assert result.success is True
            assert f"Logged message at {log_level} level" in result.actions_taken
    
    @pytest.mark.asyncio
    async def test_execute_without_simulate_work(self, hook_config, custom_context):
        """Test execution without work simulation."""
        hook_config["simulate_work"] = False
        hook = ExampleHook(hook_config)
        
        result = await hook.execute(custom_context)
        
        assert result.success is True
        # Should not have simulated work action
        action_descriptions = " ".join(result.actions_taken)
        assert "Simulated work" not in action_descriptions
    
    @pytest.mark.asyncio
    async def test_execute_custom_actions(self, hook):
        """Test execution of custom actions."""
        # Test different custom actions
        test_actions = [
            "count_event_data",
            "log_system_metrics", 
            "analyze_project_state",
            "simulate_delay",
            "unknown_action"
        ]
        
        for action in test_actions:
            context = HookContext(
                trigger_event={
                    "type": EventType.CUSTOM.value,
                    "data": {"field1": "value1", "field2": "value2"}
                },
                project_state={"key1": "value1"},
                system_metrics={"metric1": 100},
                user_preferences={}
            )
            
            result = await hook._execute_custom_action(action, context)
            assert isinstance(result, str)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_executions(self, hook):
        """Test multiple executions and history tracking."""
        # Execute the hook multiple times with different contexts
        for i in range(3):
            # Add delay to avoid rate limiting
            if i > 0:
                await asyncio.sleep(1.1)
            
            # Create a new context for each execution
            context = HookContext(
                trigger_event={
                    "type": EventType.CUSTOM.value,
                    "data": {"execution_number": i}
                },
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            
            result = await hook.execute(context)
            assert result.success is True
            assert hook.execution_count == i + 1
        
        # Check execution history
        assert len(hook.execution_history) == 3
        
        # Check that execution IDs are different
        execution_ids = [record["execution_id"] for record in hook.execution_history]
        assert len(set(execution_ids)) == 3
    
    def test_matches_trigger_events(self, hook):
        """Test event type matching."""
        # Should match common event types when no specific triggers configured
        assert hook._matches_trigger_events(EventType.CUSTOM.value) is True
        assert hook._matches_trigger_events(EventType.MANUAL.value) is True
        assert hook._matches_trigger_events(EventType.FILE_SAVE.value) is True
        
        # Should not match uncommon event types
        assert hook._matches_trigger_events(EventType.BUILD_FAILURE.value) is False
    
    def test_analyze_trigger_event(self, hook):
        """Test trigger event analysis."""
        # Test with comprehensive event
        event = {
            "type": EventType.CUSTOM.value,
            "data": {
                "field1": "value1",
                "field2": "value2",
                "error": "Something went wrong"
            }
        }
        
        analysis = hook._analyze_trigger_event(event)
        assert analysis is not None
        assert "Event type" in analysis
        assert "Data fields: 3" in analysis
        assert "Contains error information" in analysis
        
        # Test with minimal event
        minimal_event = {"type": EventType.MANUAL.value}
        analysis = hook._analyze_trigger_event(minimal_event)
        assert "Event type" in analysis
    
    def test_generate_suggestions(self, hook):
        """Test suggestion generation."""
        # Test first execution
        hook.execution_count = 1
        suggestions = hook._generate_suggestions()
        assert any("first execution" in s.lower() for s in suggestions)
        
        # Test 10th execution
        hook.execution_count = 10
        suggestions = hook._generate_suggestions()
        assert any("10 executions" in s.lower() for s in suggestions)
        
        # Test approaching maximum
        hook.execution_count = int(hook.max_executions * 0.9)
        suggestions = hook._generate_suggestions()
        assert any("approaching maximum" in s.lower() for s in suggestions)
    
    def test_calculate_average_execution_time(self, hook):
        """Test average execution time calculation."""
        # No history
        assert hook._calculate_average_execution_time() == 0.0
        
        # Add some execution records
        hook.execution_history = [
            {"execution_time_ms": 100},
            {"execution_time_ms": 200},
            {"execution_time_ms": 300}
        ]
        
        avg_time = hook._calculate_average_execution_time()
        assert avg_time == 200.0
    
    def test_get_execution_statistics(self, hook):
        """Test execution statistics."""
        # Test with no executions
        stats = hook.get_execution_statistics()
        assert stats["total_executions"] == 0
        assert stats["average_execution_time_ms"] == 0.0
        
        # Add some execution history
        hook.execution_count = 3
        hook.execution_history = [
            {"execution_time_ms": 100, "event_type": "custom"},
            {"execution_time_ms": 150, "event_type": "manual"},
            {"execution_time_ms": 200, "event_type": "custom"}
        ]
        
        stats = hook.get_execution_statistics()
        assert stats["total_executions"] == 3
        assert stats["average_execution_time_ms"] == 150.0
        assert stats["min_execution_time_ms"] == 100
        assert stats["max_execution_time_ms"] == 200
        assert stats["executions_remaining"] == 7  # max_executions - execution_count
        assert len(stats["recent_executions"]) == 3
        assert stats["event_type_distribution"]["custom"] == 2
        assert stats["event_type_distribution"]["manual"] == 1
    
    def test_reset_execution_count(self, hook):
        """Test resetting execution count."""
        # Set some state
        hook.execution_count = 5
        hook.execution_history = [{"test": "data"}]
        hook.last_execution_time = time.time()
        
        # Reset
        hook.reset_execution_count()
        
        # Check reset state
        assert hook.execution_count == 0
        assert len(hook.execution_history) == 0
        assert hook.last_execution_time == 0
    
    def test_get_configuration_info(self, hook):
        """Test configuration information retrieval."""
        config_info = hook.get_configuration_info()
        
        assert config_info["hook_id"] == hook.id
        assert config_info["hook_name"] == hook.name
        assert config_info["enabled"] == hook.enabled
        assert config_info["message"] == hook.message
        assert config_info["execution_delay"] == hook.execution_delay
        assert config_info["max_executions"] == hook.max_executions
        assert config_info["log_level"] == hook.log_level
        assert config_info["simulate_work"] == hook.simulate_work
        assert config_info["custom_actions"] == hook.custom_actions
        assert "priority" in config_info
        assert "timeout_seconds" in config_info
        assert "max_retries" in config_info
    
    def test_get_resource_requirements(self, hook):
        """Test resource requirements."""
        requirements = hook.get_resource_requirements()
        
        assert "cpu" in requirements
        assert "memory_mb" in requirements
        assert "disk_mb" in requirements
        assert "network" in requirements
        assert requirements["cpu"] > 0
        assert requirements["memory_mb"] > 0
        assert requirements["network"] is False  # Example hook doesn't need network
    
    @pytest.mark.asyncio
    async def test_execution_history_limit(self, hook):
        """Test that execution history is limited to prevent memory issues."""
        # Set a small history limit for testing
        original_limit = 50
        
        # Execute more than the limit
        for i in range(55):
            hook.execution_history.append({
                "timestamp": time.time(),
                "execution_id": f"exec_{i}",
                "event_type": "test",
                "actions_count": 1,
                "execution_time_ms": 100
            })
        
        # Simulate execution to trigger history cleanup
        context = HookContext(
            trigger_event={"type": EventType.CUSTOM.value, "data": {}},
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        await hook.execute(context)
        
        # History should be limited
        assert len(hook.execution_history) <= original_limit
    
    @pytest.mark.asyncio
    async def test_error_handling(self, hook):
        """Test error handling in hook execution."""
        # Mock an error in custom action execution
        with patch.object(hook, '_execute_custom_action', side_effect=Exception("Test error")):
            context = HookContext(
                trigger_event={"type": EventType.CUSTOM.value, "data": {}},
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            
            result = await hook.execute(context)
            
            assert result.success is False
            assert "Error executing" in result.message
            assert result.error is not None
            assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self, hook):
        """Test concurrent execution of the hook."""
        contexts = []
        for i in range(3):
            context = HookContext(
                trigger_event={
                    "type": EventType.CUSTOM.value,
                    "data": {"execution_id": i}
                },
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            contexts.append(context)
        
        # Execute all contexts concurrently
        results = await asyncio.gather(*[hook.execute(ctx) for ctx in contexts])
        
        # All should succeed
        assert all(result.success for result in results)
        assert hook.execution_count == 3
        assert len(hook.execution_history) == 3