"""
Example Hook implementation for the Agent Hooks Enhancement system.

This module provides a simple example hook that demonstrates the basic
functionality of the hook system and serves as a template for creating new hooks.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional

from ..core.models import AgentHook, HookContext, HookResult
from ..events.models import EventType, BaseEvent
from ..utils.logging import get_logger, ExecutionError


class ExampleHook(AgentHook):
    """
    Example hook that demonstrates the basic functionality of the hook system.
    
    This hook serves as a template and educational example for creating new hooks.
    It demonstrates:
    - Basic hook structure and initialization
    - Event filtering and trigger conditions
    - Hook execution with proper error handling
    - Resource requirements specification
    - Configuration management
    - Logging and metrics collection
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the example hook."""
        super().__init__(config)
        self.logger = get_logger(f"hooks.{self.__class__.__name__}")
        
        # Load configuration with defaults
        self.message = config.get("message", "Hello from ExampleHook!")
        self.execution_delay = config.get("execution_delay", 0.1)  # seconds
        self.max_executions = config.get("max_executions", 100)
        self.log_level = config.get("log_level", "info").lower()
        self.simulate_work = config.get("simulate_work", True)
        self.custom_actions = config.get("custom_actions", [])
        
        # Internal state
        self.execution_count = 0
        self.last_execution_time = 0
        self.execution_history: List[Dict[str, Any]] = []
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This example hook demonstrates various trigger conditions:
        1. Hook must be enabled
        2. Must not exceed maximum executions
        3. Event type must match configured triggers
        4. Can include custom filtering logic
        
        Args:
            context: Current execution context
            
        Returns:
            True if the hook should execute, False otherwise
        """
        if not self.enabled:
            self.logger.debug("Hook is disabled, skipping execution")
            return False
        
        # Check execution limit
        if self.execution_count >= self.max_executions:
            self.logger.warning(
                f"Maximum executions ({self.max_executions}) reached, skipping execution",
                {"execution_count": self.execution_count}
            )
            return False
        
        # Check event type against configured triggers
        event_type = context.trigger_event.get("type")
        if not self._matches_trigger_events(event_type):
            self.logger.debug(f"Event type {event_type} does not match configured triggers")
            return False
        
        # Example of custom filtering logic
        event_data = context.trigger_event.get("data", {})
        if event_data.get("skip_example_hook"):
            self.logger.debug("Event marked to skip example hook")
            return False
        
        # Example of rate limiting
        current_time = time.time()
        if current_time - self.last_execution_time < 1.0:  # Minimum 1 second between executions
            self.logger.debug("Rate limit active, skipping execution")
            return False
        
        return True
    
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook.
        
        This example demonstrates:
        - Proper error handling
        - Logging with context
        - Metrics collection
        - Action tracking
        - Execution time measurement
        
        Args:
            context: Current execution context
            
        Returns:
            Result of the hook execution
        """
        start_time = time.time()
        
        try:
            # Update execution tracking
            self.execution_count += 1
            self.last_execution_time = start_time
            
            self.logger.info(
                f"Executing {self.name} (execution #{self.execution_count})",
                {
                    "hook_id": self.id,
                    "execution_id": context.execution_id,
                    "execution_count": self.execution_count
                }
            )
            
            actions_taken = []
            
            # Simulate work if configured
            if self.simulate_work:
                await asyncio.sleep(self.execution_delay)
                actions_taken.append(f"Simulated work for {self.execution_delay} seconds")
            
            # Log the configured message
            if self.log_level == "debug":
                self.logger.debug(self.message)
            elif self.log_level == "warning":
                self.logger.warning(self.message)
            elif self.log_level == "error":
                self.logger.error(self.message)
            else:
                self.logger.info(self.message)
            
            actions_taken.append(f"Logged message at {self.log_level} level")
            
            # Execute custom actions if configured
            for action in self.custom_actions:
                action_result = await self._execute_custom_action(action, context)
                actions_taken.append(f"Executed custom action: {action_result}")
            
            # Analyze trigger event
            event_analysis = self._analyze_trigger_event(context.trigger_event)
            if event_analysis:
                actions_taken.append(f"Analyzed trigger event: {event_analysis}")
            
            # Record execution in history
            execution_record = {
                "timestamp": start_time,
                "execution_id": context.execution_id,
                "event_type": context.trigger_event.get("type"),
                "actions_count": len(actions_taken),
                "execution_time_ms": (time.time() - start_time) * 1000
            }
            
            self.execution_history.append(execution_record)
            
            # Limit history size
            if len(self.execution_history) > 50:
                self.execution_history = self.execution_history[-50:]
            
            # Generate suggestions based on execution count
            suggestions = self._generate_suggestions()
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Create success result
            message = f"Successfully executed {self.name}: {self.message}"
            
            self.logger.info(
                f"Completed execution #{self.execution_count}",
                {
                    "hook_id": self.id,
                    "execution_id": context.execution_id,
                    "execution_time_ms": execution_time_ms,
                    "actions_taken": len(actions_taken)
                }
            )
            
            return HookResult(
                success=True,
                message=message,
                actions_taken=actions_taken,
                suggestions=suggestions,
                metrics={
                    "execution_time_ms": execution_time_ms,
                    "execution_count": self.execution_count,
                    "total_executions": self.execution_count,
                    "average_execution_time": self._calculate_average_execution_time(),
                    "event_type": context.trigger_event.get("type")
                },
                execution_time_ms=execution_time_ms
            )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing {self.name}: {e}",
                {
                    "hook_id": self.id,
                    "execution_id": context.execution_id,
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return HookResult(
                success=False,
                message=f"Error executing {self.name}: {e}",
                actions_taken=[],
                suggestions=[
                    "Check the hook configuration",
                    "Verify event data format",
                    "Review hook logs for details"
                ],
                metrics={
                    "execution_time_ms": execution_time_ms,
                    "execution_count": self.execution_count,
                    "error_type": type(e).__name__
                },
                execution_time_ms=execution_time_ms,
                error=ExecutionError(str(e), hook_id=self.id)
            )
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """
        Get resource requirements for this hook.
        
        This example hook has minimal resource requirements since it's primarily
        for demonstration purposes.
        
        Returns:
            Dictionary of resource requirements
        """
        return {
            "cpu": 0.1,
            "memory_mb": 50,
            "disk_mb": 10,
            "network": False
        }
    
    def _matches_trigger_events(self, event_type: str) -> bool:
        """
        Check if the event type matches configured trigger events.
        
        Args:
            event_type: Type of the event
            
        Returns:
            True if the event type matches, False otherwise
        """
        # If no specific trigger is configured, accept common event types
        if not hasattr(self.trigger, 'event_types') or not self.trigger.event_types:
            common_events = {
                EventType.CUSTOM.value,
                EventType.MANUAL.value,
                EventType.FILE_SAVE.value
            }
            return event_type in common_events
        
        # Check against configured trigger event types
        return any(et.value == event_type for et in self.trigger.event_types)
    
    async def _execute_custom_action(self, action: str, context: HookContext) -> str:
        """
        Execute a custom action.
        
        Args:
            action: Action to execute
            context: Execution context
            
        Returns:
            Description of the action result
        """
        if action == "count_event_data":
            data_count = len(context.trigger_event.get("data", {}))
            return f"Counted {data_count} data fields in trigger event"
        
        elif action == "log_system_metrics":
            metrics_count = len(context.system_metrics)
            return f"Logged {metrics_count} system metrics"
        
        elif action == "analyze_project_state":
            state_keys = len(context.project_state)
            return f"Analyzed project state with {state_keys} keys"
        
        elif action == "simulate_delay":
            await asyncio.sleep(0.05)  # 50ms delay
            return "Simulated processing delay"
        
        else:
            return f"Unknown action: {action}"
    
    def _analyze_trigger_event(self, trigger_event: Dict[str, Any]) -> Optional[str]:
        """
        Analyze the trigger event and return insights.
        
        Args:
            trigger_event: The event that triggered this hook
            
        Returns:
            Analysis result or None
        """
        event_type = trigger_event.get("type")
        data = trigger_event.get("data", {})
        
        analysis_parts = []
        
        # Analyze event type
        if event_type:
            analysis_parts.append(f"Event type: {event_type}")
        
        # Analyze data size
        if data:
            analysis_parts.append(f"Data fields: {len(data)}")
        
        # Look for interesting patterns
        if "error" in str(data).lower():
            analysis_parts.append("Contains error information")
        
        if "warning" in str(data).lower():
            analysis_parts.append("Contains warning information")
        
        return ", ".join(analysis_parts) if analysis_parts else None
    
    def _generate_suggestions(self) -> List[str]:
        """
        Generate suggestions based on current state.
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Suggest based on execution count
        if self.execution_count == 1:
            suggestions.append("This is your first execution - welcome to the example hook!")
        elif self.execution_count == 10:
            suggestions.append("You've reached 10 executions - consider reviewing the hook's performance")
        elif self.execution_count >= self.max_executions * 0.8:
            suggestions.append(f"Approaching maximum executions ({self.max_executions})")
        
        # Suggest based on execution time
        avg_time = self._calculate_average_execution_time()
        if avg_time > 1000:  # More than 1 second
            suggestions.append("Consider optimizing hook execution time")
        
        # General suggestions
        suggestions.extend([
            "Try configuring a different message",
            "Experiment with custom actions",
            "Adjust the execution delay for different behavior"
        ])
        
        return suggestions
    
    def _calculate_average_execution_time(self) -> float:
        """
        Calculate average execution time from history.
        
        Returns:
            Average execution time in milliseconds
        """
        if not self.execution_history:
            return 0.0
        
        total_time = sum(record["execution_time_ms"] for record in self.execution_history)
        return total_time / len(self.execution_history)
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about hook executions.
        
        Returns:
            Dictionary containing execution statistics
        """
        if not self.execution_history:
            return {
                "total_executions": self.execution_count,
                "average_execution_time_ms": 0.0,
                "min_execution_time_ms": 0.0,
                "max_execution_time_ms": 0.0,
                "recent_executions": []
            }
        
        execution_times = [record["execution_time_ms"] for record in self.execution_history]
        
        return {
            "total_executions": self.execution_count,
            "average_execution_time_ms": sum(execution_times) / len(execution_times),
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "executions_remaining": max(0, self.max_executions - self.execution_count),
            "recent_executions": self.execution_history[-10:],  # Last 10 executions
            "event_type_distribution": self._get_event_type_distribution()
        }
    
    def _get_event_type_distribution(self) -> Dict[str, int]:
        """
        Get distribution of event types from execution history.
        
        Returns:
            Dictionary mapping event types to counts
        """
        distribution = {}
        for record in self.execution_history:
            event_type = record.get("event_type", "unknown")
            distribution[event_type] = distribution.get(event_type, 0) + 1
        return distribution
    
    def reset_execution_count(self) -> None:
        """Reset the execution count and clear history."""
        self.execution_count = 0
        self.execution_history.clear()
        self.last_execution_time = 0
        self.logger.info("Reset execution count and cleared history")
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """
        Get information about the current configuration.
        
        Returns:
            Dictionary containing configuration details
        """
        return {
            "hook_id": self.id,
            "hook_name": self.name,
            "enabled": self.enabled,
            "message": self.message,
            "execution_delay": self.execution_delay,
            "max_executions": self.max_executions,
            "log_level": self.log_level,
            "simulate_work": self.simulate_work,
            "custom_actions": self.custom_actions,
            "priority": self.priority.name if self.priority else "MEDIUM",
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries
        }