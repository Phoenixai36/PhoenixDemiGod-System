import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent_hooks.events.router import EventRouter
from src.agent_hooks.events.models import BaseEvent, EventType
from src.agent_hooks.core.models import AgentHook, HookTrigger

class MockHook(AgentHook):
    def __init__(self, config):
        super().__init__(config)
        self.executed = False

    async def should_execute(self, context):
        return True

    async def execute(self, context):
        self.executed = True
        return MagicMock()

    def get_resource_requirements(self):
        return {}

@pytest.mark.asyncio
async def test_route_event_to_matching_hook():
    # Arrange
    hook_config = {
        "trigger": {
            "event_types": ["file_save"]
        }
    }
    hook = MockHook(hook_config)
    router = EventRouter(hooks=[hook])
    event = BaseEvent(source="test", type=EventType.FILE_SAVE, correlation_id="test_correlation")

    # Act
    await router.route_event(event)

    # Assert
    assert hook.executed