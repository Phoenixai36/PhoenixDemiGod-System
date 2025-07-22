"""
Event router and processing pipeline for the Agent Hooks Enhancement system.

This module implements the central event routing and processing functionality.
"""

from typing import List, TypeVar
from src.agent_hooks.core.models import AgentHook, HookContext
from src.agent_hooks.events.models import BaseEvent
from src.agent_hooks.events.matcher import HookMatcher
from src.agent_hooks.events.components.correlator import EventCorrelator
from src.agent_hooks.utils.logging import get_logger

T = TypeVar("T", bound=BaseEvent)

class EventRouter:
    """
    Routes events to the appropriate hooks.
    """
    def __init__(self, hooks: List[AgentHook]):
        self.hooks = hooks
        self.matcher = HookMatcher()
        self.correlator = EventCorrelator()
        self.logger = get_logger("event_router")

    async def route_event(self, event: BaseEvent):
        """
        Route an event to all matching hooks.
        """
        matching_hooks = self.matcher.get_matching_hooks(event, self.hooks)
        
        for hook in matching_hooks:
            context = HookContext(
                trigger_event=event.dict(),
                project_state={},  # Placeholder
                system_metrics={}, # Placeholder
                user_preferences={}, # Placeholder
            )
            try:
                if await hook.should_execute(context):
                    await hook.execute(context)
            except Exception as e:
                self.logger.error(f"Error executing hook {hook.name}: {e}")

        correlated_event = self.correlator.add_event(event)
        if correlated_event:
            await self.route_event(correlated_event)
