#!/usr/bin/env python3
"""
Simple test script to verify the CellularCommunicationHook implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from .kiro.engine.hooks.cellular_communication_hook import CellularCommunicationHook
from .kiro.engine.core.models import HookContext
from .kiro.engine.events.models import EventType


async def test_cellular_communication_hook():
    """Test the cellular communication hook."""
    print("Testing CellularCommunicationHook...")
    
    # Create hook configuration
    config = {
        "id": "test-cellular-hook",
        "name": "Test Cellular Communication Hook",
        "description": "Test hook for cellular communication",
        "enabled": True,
        "max_message_history": 100,
        "stats_reporting_interval": 60,
        "topology_check_interval": 300,
        "resonance_optimization_threshold": 0.7,
        "security_alert_cooldown": 30
    }
    
    # Create hook instance
    hook = CellularCommunicationHook(config)
    
    # Test 1: Check resource requirements
    print("✓ Testing resource requirements...")
    requirements = hook.get_resource_requirements()
    assert requirements["cpu"] == 0.3
    assert requirements["memory_mb"] == 150
    assert requirements["network"] is True
    print(f"  Resource requirements: {requirements}")
    
    # Test 2: Test should_execute with valid event
    print("✓ Testing should_execute with valid event...")
    context = HookContext(
        trigger_event={
            "type": EventType.CUSTOM.value,
            "data": {"event_name": "ccp_message_sent"}
        },
        project_state={},
        system_metrics={},
        user_preferences={}
    )
    
    should_execute = await hook.should_execute(context)
    assert should_execute is True
    print("  Should execute for ccp_message_sent: True")
    
    # Test 3: Test should_execute with invalid event
    print("✓ Testing should_execute with invalid event...")
    context_invalid = HookContext(
        trigger_event={
            "type": EventType.FILE_SAVE.value,
            "data": {"file_path": "test.py"}
        },
        project_state={},
        system_metrics={},
        user_preferences={}
    )
    
    should_execute_invalid = await hook.should_execute(context_invalid)
    assert should_execute_invalid is False
    print("  Should execute for file_save: False")
    
    # Test 4: Test execute with ccp_message_sent event
    print("✓ Testing execute with ccp_message_sent event...")
    context_sent = HookContext(
        trigger_event={
            "type": EventType.CUSTOM.value,
            "data": {
                "event_name": "ccp_message_sent",
                "message_id": "test-msg-001",
                "source_id": "cell-001",
                "target_id": "cell-002",
                "priority": "HIGH",
                "encryption_level": "QUANTUM"
            }
        },
        project_state={},
        system_metrics={},
        user_preferences={}
    )
    
    result = await hook.execute(context_sent)
    assert result.success is True
    assert "Processed message sent from cell-001 to cell-002" in result.actions_taken
    print(f"  Execution result: {result.message}")
    print(f"  Actions taken: {result.actions_taken}")
    
    # Test 5: Test execute with ccp_message_received event
    print("✓ Testing execute with ccp_message_received event...")
    context_received = HookContext(
        trigger_event={
            "type": EventType.CUSTOM.value,
            "data": {
                "event_name": "ccp_message_received",
                "message_id": "test-msg-002",
                "source_id": "cell-002",
                "target_id": "cell-001",
                "latency_ms": 45
            }
        },
        project_state={},
        system_metrics={},
        user_preferences={}
    )
    
    result_received = await hook.execute(context_received)
    assert result_received.success is True
    assert "Processed message received from cell-002 to cell-001 (latency: 45ms)" in result_received.actions_taken
    print(f"  Execution result: {result_received.message}")
    print(f"  Actions taken: {result_received.actions_taken}")
    
    # Test 6: Test execute with ccp_security_alert event
    print("✓ Testing execute with ccp_security_alert event...")
    context_alert = HookContext(
        trigger_event={
            "type": EventType.CUSTOM.value,
            "data": {
                "event_name": "ccp_security_alert",
                "level": "WARNING",
                "message": "Unusual communication pattern detected"
            }
        },
        project_state={},
        system_metrics={},
        user_preferences={}
    )
    
    result_alert = await hook.execute(context_alert)
    assert result_alert.success is True
    assert "Processed security alert: WARNING" in result_alert.actions_taken[0]
    print(f"  Execution result: {result_alert.message}")
    print(f"  Actions taken: {result_alert.actions_taken}")
    
    # Test 7: Check metrics collection
    print("✓ Testing metrics collection...")
    assert hook.message_counter == 3  # 2 messages + 1 alert
    assert len(hook.active_cells) == 2  # cell-001 and cell-002
    assert hook.communication_stats["messages_sent"] == 1
    assert hook.communication_stats["messages_received"] == 1
    print(f"  Message counter: {hook.message_counter}")
    print(f"  Active cells: {len(hook.active_cells)}")
    print(f"  Communication stats: {hook.communication_stats}")
    
    print("\n🎉 All tests passed! CellularCommunicationHook is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_cellular_communication_hook())