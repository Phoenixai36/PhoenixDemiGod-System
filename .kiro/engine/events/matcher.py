"""
Event matcher for the Agent Hooks Enhancement system.

This module implements the event matching functionality, which is responsible
for matching events against hook trigger conditions.
"""

from typing import List
from ..core.models import AgentHook
from .models import BaseEvent
from ..utils.logging import get_logger


class HookMatcher:
    """Matches events against hook triggers."""

    def __init__(self):
        """Initialize the matcher."""
        self.logger = get_logger("hook_matcher")

    def get_matching_hooks(self, event: BaseEvent, hooks: List[AgentHook]) -> List[AgentHook]:
        """
        Find all hooks that match the given event.

        Args:
            event: The event to match against.
            hooks: A list of all available hooks.

        Returns:
            A list of hooks that are triggered by the event.
        """
        matching_hooks = []
        for hook in hooks:
            if self._matches_trigger(event, hook):
                matching_hooks.append(hook)
        self.logger.info(f"Event {event.id} ({event.type}) matched {len(matching_hooks)} hooks.")
        return matching_hooks

    def _matches_trigger(self, event: BaseEvent, hook: AgentHook) -> bool:
        """
        Check if an event matches a single hook's trigger.

        Args:
            event: The event to check.
            hook: The hook containing the trigger to match against.

        Returns:
            True if the event matches the trigger, False otherwise.
        """
        trigger = hook.trigger
        if event.type not in trigger.event_types:
            return False

        if trigger.filter_group and not trigger.filter_group.matches(event):
            return False

        return True
