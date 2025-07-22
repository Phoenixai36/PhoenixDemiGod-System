"""
Example hook implementation for the Agent Hooks Enhancement system.

This module provides a simple example hook that demonstrates the basic
functionality of the hook system.
"""

import time
from typing import Dict, Any, List, Optional

from src.agent_hooks.core.models import AgentHook, HookContext, HookResult, HookPriority, HookTrigger
from src.agent_hooks.utils.logging import get_logger, ExecutionError


class ExampleHook(AgentHook):
    """
    Example hook that demonstrates the basic functionality of the hook system.
    
    This hook simply logs a message and returns a success result.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the example hook."""
        super().__init__(config)
        self.logger = get_logger(f"hooks.{self.__class__.__name__}")
        self.message = config.get("message", "Hello from ExampleHook!")
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This example hook always executes if it is enabled and the trigger event
        matches one of its triggers.
        """
        if not self.enabled:
            return False
        
        event_type = context.trigger_event.get("type")
        return any(trigger.value == event_type for trigger in self.triggers)
    
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook.
        
        This example hook simply logs a message and returns a success result.
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Executing {self.name}",
                {"hook_id": self.id, "execution_id": context.execution_id}
            )
            
            # Simulate some work
            time.sleep(0.5)
            
            # Log the message
            self.logger.info(
                self.message,
                {"hook_id": self.id, "execution_id": context.execution_id}
            )
            
            # Return a success result
            execution_time_ms = (time.time() - start_time) * 1000
            return HookResult(
                success=True,
                message=self.message,
                actions_taken=["Logged a message"],
                suggestions=["Try configuring a different message"],
                metrics={"execution_time_ms": execution_time_ms},
                execution_time_ms=execution_time_ms
            )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing {self.name}: {e}",
                {"hook_id": self.id, "execution_id": context.execution_id},
                e
            )
            
            return HookResult(
                success=False,
                message=f"Error executing {self.name}: {e}",
                actions_taken=[],
                suggestions=["Check the hook configuration"],
                metrics={"execution_time_ms": execution_time_ms},
                execution_time_ms=execution_time_ms,
                error=ExecutionError(str(e), hook_id=self.id)
            )
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """
        Get resource requirements for this hook.
        
        This example hook has minimal resource requirements.
        """
        return {
            "cpu": 0.1,
            "memory_mb": 50,
            "disk_mb": 10,
            "network": False
        }
