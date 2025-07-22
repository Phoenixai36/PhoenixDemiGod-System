"""
Hook dispatcher for the Agent Hooks Automation system.

This module implements a dispatcher for executing hooks in response to events,
with support for prioritization, concurrency control, and error handling.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set, Tuple
import uuid
from datetime import datetime

from src.agent_hooks.core.models import AgentHook, HookContext, HookResult, HookPriority
from src.agent_hooks.core.hook_registry import HookRegistry
from src.agent_hooks.events.models import BaseEvent, EventType
from src.agent_hooks.utils.logging import get_logger, ExecutionError, TimeoutError


class HookExecutionStats:
    """Statistics about hook execution."""
    
    def __init__(self):
        """Initialize hook execution statistics."""
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time_ms = 0
        self.average_execution_time_ms = 0
        self.max_execution_time_ms = 0
        self.min_execution_time_ms = float('inf')
        self.executions_by_hook: Dict[str, int] = {}
        self.failures_by_hook: Dict[str, int] = {}
        self.start_time = datetime.now()
    
    def record_execution(self, hook_id: str, success: bool, execution_time_ms: float) -> None:
        """
        Record a hook execution.
        
        Args:
            hook_id: ID of the executed hook
            success: Whether the execution was successful
            execution_time_ms: Execution time in milliseconds
        """
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            self.failures_by_hook[hook_id] = self.failures_by_hook.get(hook_id, 0) + 1
        
        self.total_execution_time_ms += execution_time_ms
        self.average_execution_time_ms = self.total_execution_time_ms / self.total_executions
        self.max_execution_time_ms = max(self.max_execution_time_ms, execution_time_ms)
        self.min_execution_time_ms = min(self.min_execution_time_ms, execution_time_ms)
        
        self.executions_by_hook[hook_id] = self.executions_by_hook.get(hook_id, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary of execution statistics
        """
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.successful_executions / self.total_executions if self.total_executions > 0 else 0,
            "total_execution_time_ms": self.total_execution_time_ms,
            "average_execution_time_ms": self.average_execution_time_ms,
            "max_execution_time_ms": self.max_execution_time_ms,
            "min_execution_time_ms": self.min_execution_time_ms if self.min_execution_time_ms != float('inf') else 0,
            "executions_by_hook": self.executions_by_hook,
            "failures_by_hook": self.failures_by_hook,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


class HookDispatcher:
    """
    Dispatcher for executing hooks in response to events.
    
    The hook dispatcher is responsible for determining which hooks should execute
    in response to an event, executing them in the appropriate order, and handling
    any errors that occur during execution.
    """
    
    def __init__(self, registry: HookRegistry, max_concurrent_hooks: int = 5):
        """
        Initialize the hook dispatcher.
        
        Args:
            registry: Hook registry to use for looking up hooks
            max_concurrent_hooks: Maximum number of hooks to execute concurrently
        """
        self.logger = get_logger("core.hook_dispatcher")
        self.registry = registry
        self.max_concurrent_hooks = max_concurrent_hooks
        self.semaphore = asyncio.Semaphore(max_concurrent_hooks)
        self.stats = HookExecutionStats()
        self.executing_hooks: Set[str] = set()
    
    async def dispatch_event(self, event: BaseEvent) -> List[HookResult]:
        """
        Dispatch an event to appropriate hooks.
        
        Args:
            event: Event to dispatch
            
        Returns:
            List of hook execution results
        """
        # Get hooks that handle this event type
        hooks = self.registry.get_hooks_for_event_type(event.type)
        
        if not hooks:
            self.logger.debug(
                f"No hooks found for event type: {event.type.value}",
                {"event_id": event.id, "event_type": event.type.value}
            )
            return []
        
        # Create execution context
        context = HookContext(
            trigger_event=event.dict(),
            project_state={},  # This would be populated with actual project state
            system_metrics={},  # This would be populated with actual system metrics
            user_preferences={}  # This would be populated with actual user preferences
        )
        
        # Determine execution order based on dependencies and priorities
        try:
            hook_ids = [hook.id for hook in hooks]
            execution_order = self.registry.get_hook_execution_order(hook_ids)
            ordered_hooks = [self.registry.get_hook(hook_id) for hook_id in execution_order if self.registry.get_hook(hook_id)]
        except Exception as e:
            self.logger.error(
                f"Error determining hook execution order: {e}",
                {"event_id": event.id, "event_type": event.type.value},
                e
            )
            # Fall back to priority-based ordering
            ordered_hooks = sorted(hooks, key=lambda h: h.priority.value)
        
        # Execute hooks
        results = []
        for hook in ordered_hooks:
            # Check if the hook should execute
            should_execute = False
            try:
                should_execute = await hook.should_execute(context)
            except Exception as e:
                self.logger.error(
                    f"Error checking if hook should execute: {e}",
                    {"hook_id": hook.id, "hook_name": hook.name, "event_id": event.id},
                    e
                )
            
            if not should_execute:
                self.logger.debug(
                    f"Hook {hook.name} ({hook.id}) skipped execution",
                    {"hook_id": hook.id, "hook_name": hook.name, "event_id": event.id}
                )
                continue
            
            # Execute the hook
            result = await self._execute_hook(hook, context)
            results.append(result)
            
            # Update context with execution record
            context = context.with_execution_record({
                "hook_id": hook.id,
                "hook_name": hook.name,
                "success": result.success,
                "message": result.message,
                "execution_time_ms": result.execution_time_ms
            })
        
        return results
    
    async def _execute_hook(self, hook: AgentHook, context: HookContext) -> HookResult:
        """
        Execute a hook with the given context.
        
        Args:
            hook: Hook to execute
            context: Execution context
            
        Returns:
            Hook execution result
        """
        # Acquire semaphore to limit concurrency
        async with self.semaphore:
            start_time = time.time()
            self.executing_hooks.add(hook.id)
            
            try:
                self.logger.info(
                    f"Executing hook: {hook.name} ({hook.id})",
                    {"hook_id": hook.id, "hook_name": hook.name, "execution_id": context.execution_id}
                )
                
                # Execute the hook with timeout
                try:
                    result = await asyncio.wait_for(
                        hook.execute(context),
                        timeout=hook.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    execution_time_ms = (time.time() - start_time) * 1000
                    error_message = f"Hook execution timed out after {hook.timeout_seconds} seconds"
                    self.logger.error(
                        error_message,
                        {"hook_id": hook.id, "hook_name": hook.name, "execution_id": context.execution_id}
                    )
                    result = HookResult(
                        success=False,
                        message=error_message,
                        actions_taken=[],
                        suggestions=["Increase the hook timeout", "Optimize the hook execution"],
                        metrics={"execution_time_ms": execution_time_ms},
                        execution_time_ms=execution_time_ms,
                        error=TimeoutError(error_message, hook_id=hook.id)
                    )
                
                # Ensure execution time is set
                execution_time_ms = (time.time() - start_time) * 1000
                if result.execution_time_ms is None:
                    result = result.with_execution_time(execution_time_ms)
                
                # Log result
                if result.success:
                    self.logger.info(
                        f"Hook executed successfully: {hook.name} ({hook.id})",
                        {
                            "hook_id": hook.id,
                            "hook_name": hook.name,
                            "execution_id": context.execution_id,
                            "execution_time_ms": result.execution_time_ms
                        }
                    )
                else:
                    self.logger.error(
                        f"Hook execution failed: {hook.name} ({hook.id}): {result.message}",
                        {
                            "hook_id": hook.id,
                            "hook_name": hook.name,
                            "execution_id": context.execution_id,
                            "execution_time_ms": result.execution_time_ms
                        },
                        result.error
                    )
                
                # Update statistics
                self.stats.record_execution(hook.id, result.success, result.execution_time_ms)
                
                return result
            
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                self.logger.error(
                    f"Error executing hook: {e}",
                    {"hook_id": hook.id, "hook_name": hook.name, "execution_id": context.execution_id},
                    e
                )
                
                result = HookResult(
                    success=False,
                    message=f"Error executing hook: {e}",
                    actions_taken=[],
                    suggestions=["Check the hook implementation"],
                    metrics={"execution_time_ms": execution_time_ms},
                    execution_time_ms=execution_time_ms,
                    error=ExecutionError(str(e), hook_id=hook.id, cause=e)
                )
                
                # Update statistics
                self.stats.record_execution(hook.id, False, execution_time_ms)
                
                return result
            
            finally:
                self.executing_hooks.remove(hook.id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get dispatcher statistics.
        
        Returns:
            Dictionary of dispatcher statistics
        """
        return {
            "max_concurrent_hooks": self.max_concurrent_hooks,
            "currently_executing": len(self.executing_hooks),
            "executing_hooks": list(self.executing_hooks),
            "execution_stats": self.stats.get_stats()
        }