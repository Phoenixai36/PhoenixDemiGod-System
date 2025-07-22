"""
Tests for the Cellular Communication Hook.
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

from engine.hooks.cellular_communication_hook import CellularCommunicationHook, MessagePriority, EncryptionLevel, AlertLevel
from engine.core.models import HookContext
from engine.events.models import EventType


class TestCellularCommunicationHook:
    """Test the CellularCommunicationHook class."""
    
    @pytest.fixture
    def hook_config(self):
        """Create a basic hook configuration."""
        return {
            "id": "test_ccp_hook",
            "name": "Test CCP Hook",
            "enabled": True,
            "max_message_history": 100,
            "stats_reporting_interval": 10,
            "topology_check_interval": 30,
            "resonance_optimization_threshold": 0.7,
            "security_alert_cooldown": 5
        }
    
    @pytest.fixture
    def hook(self, hook_config):
        """Create a hook instance."""
        return CellularCommunicationHook(hook_config)
    
    @pytest.fixture
    def message_sent_context(self):
        """Create a context for message sent events."""
        return HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {
                    "event_name": "ccp_message_sent",
                    "message_id": "msg_001",
                    "source_id": "cell_alpha",
                    "target_id": "cell_beta",
                    "priority": "HIGH",
                    "encryption_level": "QUANTUM"
                }
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    @pytest.fixture
    def message_received_context(self):
        """Create a context for message received events."""
        return HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {
                    "event_name": "ccp_message_received",
                    "message_id": "msg_002",
                    "source_id": "cell_gamma",
                    "target_id": "cell_delta",
                    "latency_ms": 45.5
                }
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    @pytest.fixture
    def security_alert_context(self):
        """Create a context for security alert events."""
        return HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {
                    "event_name": "ccp_security_alert",
                    "level": "CRITICAL",
                    "message": "Unauthorized access attempt detected"
                }
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    def test_hook_initialization(self, hook, hook_config):
        """Test hook initialization."""
        assert hook.id == "test_ccp_hook"
        assert hook.name == "Test CCP Hook"
        assert hook.enabled is True
        assert hook.max_message_history == 100
        assert hook.stats_reporting_interval == 10
        assert hook.topology_check_interval == 30
        assert hook.message_counter == 0
        assert len(hook.active_cells) == 0
        assert hook.communication_stats["messages_sent"] == 0
        assert hook.communication_stats["messages_received"] == 0
    
    @pytest.mark.asyncio
    async def test_should_execute_enabled_hook(self, hook, message_sent_context):
        """Test that enabled hook should execute for valid CCP events."""
        result = await hook.should_execute(message_sent_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_execute_disabled_hook(self, hook_config, message_sent_context):
        """Test that disabled hook should not execute."""
        hook_config["enabled"] = False
        hook = CellularCommunicationHook(hook_config)
        
        result = await hook.should_execute(message_sent_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_wrong_event_type(self, hook):
        """Test that hook should not execute for wrong event types."""
        context = HookContext(
            trigger_event={
                "type": EventType.FILE_SAVE.value,
                "data": {"event_name": "ccp_message_sent"}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_wrong_event_name(self, hook):
        """Test that hook should not execute for wrong event names."""
        context = HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {"event_name": "unknown_event"}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_message_sent_event(self, hook, message_sent_context):
        """Test successful execution of message sent event."""
        result = await hook.execute(message_sent_context)
        
        assert result.success is True
        assert "ccp_message_sent" in result.message
        assert len(result.actions_taken) > 0
        assert "cell_alpha" in hook.active_cells
        assert "cell_beta" in hook.active_cells
        assert hook.communication_stats["messages_sent"] == 1
        assert hook.message_counter == 1
        assert len(hook.message_history) == 1
        assert result.execution_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_execute_message_received_event(self, hook, message_received_context):
        """Test successful execution of message received event."""
        result = await hook.execute(message_received_context)
        
        assert result.success is True
        assert "ccp_message_received" in result.message
        assert len(result.actions_taken) > 0
        assert "cell_gamma" in hook.active_cells
        assert "cell_delta" in hook.active_cells
        assert hook.communication_stats["messages_received"] == 1
        assert hook.communication_stats["avg_latency_ms"] == 45.5
        assert hook.message_counter == 1
        assert len(hook.message_history) == 1
    
    @pytest.mark.asyncio
    async def test_execute_security_alert_event(self, hook, security_alert_context):
        """Test successful execution of security alert event."""
        result = await hook.execute(security_alert_context)
        
        assert result.success is True
        assert "ccp_security_alert" in result.message
        assert len(result.actions_taken) > 0
        assert hook.communication_stats["security_alerts"]["CRITICAL"] == 1
        assert "security alert" in result.actions_taken[0].lower()
    
    @pytest.mark.asyncio
    async def test_security_alert_cooldown(self, hook, security_alert_context):
        """Test security alert cooldown functionality."""
        # First alert should be processed
        result1 = await hook.execute(security_alert_context)
        assert result1.success is True
        assert len(result1.actions_taken) > 0
        
        # Second alert within cooldown should be ignored
        result2 = await hook.execute(security_alert_context)
        assert result2.success is True
        # Should have fewer actions due to cooldown
        assert len([a for a in result2.actions_taken if "security alert" in a.lower()]) == 0
    
    @pytest.mark.asyncio
    async def test_message_history_limit(self, hook):
        """Test message history size limiting."""
        hook.max_message_history = 5
        
        # Send more messages than the limit
        for i in range(10):
            context = HookContext(
                trigger_event={
                    "type": EventType.CUSTOM.value,
                    "data": {
                        "event_name": "ccp_message_sent",
                        "message_id": f"msg_{i:03d}",
                        "source_id": f"cell_{i}",
                        "target_id": "cell_target"
                    }
                },
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            await hook.execute(context)
        
        # History should be limited to max_message_history
        assert len(hook.message_history) == 5
        assert hook.message_counter == 10
        
        # Should contain the last 5 messages
        message_ids = [msg["message_id"] for msg in hook.message_history]
        expected_ids = [f"msg_{i:03d}" for i in range(5, 10)]
        assert message_ids == expected_ids
    
    @pytest.mark.asyncio
    async def test_stats_reporting(self, hook, message_sent_context):
        """Test periodic stats reporting."""
        # Set short reporting interval
        hook.stats_reporting_interval = 0.1
        hook.last_stats_report = 0  # Force stats reporting
        
        result = await hook.execute(message_sent_context)
        
        assert result.success is True
        # Should include stats reporting action
        stats_actions = [a for a in result.actions_taken if "stats report" in a.lower()]
        assert len(stats_actions) > 0
    
    @pytest.mark.asyncio
    async def test_topology_monitoring(self, hook, message_sent_context):
        """Test network topology monitoring."""
        # Set short topology check interval
        hook.topology_check_interval = 0.1
        hook.last_topology_check = 0  # Force topology check
        
        result = await hook.execute(message_sent_context)
        
        assert result.success is True
        # Should include topology analysis action
        topology_actions = [a for a in result.actions_taken if "topology" in a.lower()]
        assert len(topology_actions) > 0
    
    @pytest.mark.asyncio
    async def test_tesla_resonance_optimization(self, hook):
        """Test Tesla resonance optimization."""
        # Add some active cells
        hook.active_cells.add("cell_alpha")
        hook.active_cells.add("cell_beta")
        
        # Set conditions that trigger optimization
        hook.communication_stats["avg_latency_ms"] = 150  # Above threshold
        
        context = HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": {
                    "event_name": "ccp_message_sent",
                    "source_id": "cell_alpha",
                    "target_id": "cell_beta"
                }
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.execute(context)
        
        assert result.success is True
        # Should include resonance optimization action
        resonance_actions = [a for a in result.actions_taken if "resonance" in a.lower()]
        assert len(resonance_actions) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_cell_resonance(self, hook):
        """Test individual cell resonance optimization."""
        result = await hook._optimize_cell_resonance("test_cell")
        
        assert result["success"] is True
        assert result["cell_id"] == "test_cell"
        assert result["base_frequency"] == 150000
        assert result["sacred_multiplier"] == 9
        assert 0 <= result["quality"] <= 1
        assert result["estimated_improvement"] > 0
    
    def test_should_optimize_resonance_conditions(self, hook):
        """Test conditions for Tesla resonance optimization."""
        # No active cells - should not optimize
        assert hook._should_optimize_resonance() is False
        
        # Add cells but low latency - should not optimize
        hook.active_cells.add("cell_1")
        hook.active_cells.add("cell_2")
        hook.communication_stats["avg_latency_ms"] = 50
        assert hook._should_optimize_resonance() is False
        
        # High latency - should optimize
        hook.communication_stats["avg_latency_ms"] = 150
        assert hook._should_optimize_resonance() is True
        
        # Low resonance quality - should optimize
        hook.communication_stats["avg_latency_ms"] = 50
        hook.resonance_quality_cache["cell_1-cell_2"] = 0.5  # Below threshold
        assert hook._should_optimize_resonance() is True
    
    def test_communication_stats_tracking(self, hook):
        """Test communication statistics tracking."""
        # Initial state
        assert hook.communication_stats["messages_sent"] == 0
        assert hook.communication_stats["messages_received"] == 0
        assert hook.communication_stats["avg_latency_ms"] == 0
        
        # Check that all enum values are tracked
        for priority in MessagePriority:
            assert priority.name in hook.communication_stats["priorities"]
        
        for level in EncryptionLevel:
            assert level.name in hook.communication_stats["encryption_levels"]
        
        for alert_level in AlertLevel:
            assert alert_level.name in hook.communication_stats["security_alerts"]
    
    @pytest.mark.asyncio
    async def test_handle_message_sent(self, hook):
        """Test message sent handling."""
        event_data = {
            "message_id": "test_msg",
            "source_id": "cell_a",
            "target_id": "cell_b",
            "priority": "HIGH",
            "encryption_level": "QUANTUM"
        }
        
        actions = await hook._handle_message_sent(event_data)
        
        assert len(actions) > 0
        assert "cell_a" in hook.active_cells
        assert "cell_b" in hook.active_cells
        assert hook.communication_stats["messages_sent"] == 1
        assert hook.communication_stats["priorities"]["HIGH"] == 1
        assert hook.communication_stats["encryption_levels"]["QUANTUM"] == 1
        assert len(hook.message_history) == 1
    
    @pytest.mark.asyncio
    async def test_handle_message_received(self, hook):
        """Test message received handling."""
        event_data = {
            "message_id": "test_msg",
            "source_id": "cell_c",
            "target_id": "cell_d",
            "latency_ms": 75.5
        }
        
        actions = await hook._handle_message_received(event_data)
        
        assert len(actions) > 0
        assert "cell_c" in hook.active_cells
        assert "cell_d" in hook.active_cells
        assert hook.communication_stats["messages_received"] == 1
        assert hook.communication_stats["avg_latency_ms"] == 75.5
        assert hook.communication_stats["total_latency_ms"] == 75.5
        assert len(hook.message_history) == 1
    
    @pytest.mark.asyncio
    async def test_handle_security_alert(self, hook):
        """Test security alert handling."""
        event_data = {
            "level": "ERROR",
            "message": "Test security alert"
        }
        
        actions = await hook._handle_security_alert(event_data)
        
        assert len(actions) > 0
        assert hook.communication_stats["security_alerts"]["ERROR"] == 1
        assert "security alert" in actions[0].lower()
    
    @pytest.mark.asyncio
    async def test_report_stats(self, hook):
        """Test stats reporting functionality."""
        # Set up some stats
        hook.message_counter = 10
        hook.active_cells.add("cell_1")
        hook.active_cells.add("cell_2")
        hook.communication_stats["avg_latency_ms"] = 42.5
        
        actions = await hook._report_stats()
        
        assert len(actions) > 0
        assert "stats report" in actions[0].lower()
        assert "10 messages" in actions[0]
        assert "2 cells" in actions[0]
    
    @pytest.mark.asyncio
    async def test_check_network_topology(self, hook):
        """Test network topology checking."""
        # Add some message history
        hook.message_history = [
            {"source_id": "cell_1", "target_id": "cell_2"},
            {"source_id": "cell_2", "target_id": "cell_3"},
            {"source_id": "cell_1", "target_id": "cell_3"}
        ]
        hook.active_cells.update(["cell_1", "cell_2", "cell_3"])
        
        actions = await hook._check_network_topology()
        
        assert len(actions) > 0
        assert "topology" in actions[0].lower()
        assert "3 active cells" in actions[0]
    
    def test_get_resource_requirements(self, hook):
        """Test resource requirements."""
        requirements = hook.get_resource_requirements()
        
        assert "cpu" in requirements
        assert "memory_mb" in requirements
        assert "disk_mb" in requirements
        assert "network" in requirements
        assert requirements["cpu"] > 0
        assert requirements["memory_mb"] > 0
        assert requirements["network"] is True  # CCP hook needs network
    
    @pytest.mark.asyncio
    async def test_error_handling(self, hook):
        """Test error handling in hook execution."""
        # Create a context that will cause an error
        context = HookContext(
            trigger_event={
                "type": EventType.CUSTOM.value,
                "data": None  # This should cause an error
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.execute(context)
        
        assert result.success is False
        assert "Error executing cellular communication hook" in result.message
        assert result.error is not None
        assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_latency_calculation(self, hook):
        """Test latency calculation with multiple messages."""
        # Process multiple messages with different latencies
        latencies = [10.5, 25.0, 15.5, 30.0]
        
        for i, latency in enumerate(latencies):
            event_data = {
                "message_id": f"msg_{i}",
                "source_id": f"cell_{i}",
                "target_id": "target_cell",
                "latency_ms": latency
            }
            await hook._handle_message_received(event_data)
        
        # Check average latency calculation
        expected_avg = sum(latencies) / len(latencies)
        assert abs(hook.communication_stats["avg_latency_ms"] - expected_avg) < 0.01
        assert hook.communication_stats["total_latency_ms"] == sum(latencies)
        assert hook.communication_stats["messages_received"] == len(latencies)
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self, hook):
        """Test concurrent execution of multiple events."""
        contexts = []
        for i in range(5):
            context = HookContext(
                trigger_event={
                    "type": EventType.CUSTOM.value,
                    "data": {
                        "event_name": "ccp_message_sent",
                        "message_id": f"concurrent_msg_{i}",
                        "source_id": f"cell_{i}",
                        "target_id": "target_cell"
                    }
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
        assert hook.message_counter == 5
        assert len(hook.active_cells) == 6  # 5 source cells + 1 target cell
        assert len(hook.message_history) == 5