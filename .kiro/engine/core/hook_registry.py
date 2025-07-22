"""
Hook registry for the Agent Hooks Automation system.

This module implements a registry for managing hook definitions, including
registration, deregistration, and lookup functionality.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import uuid
from datetime import datetime

from src.agent_hooks.core.models import AgentHook, HookPriority, HookTrigger
from src.agent_hooks.events.models import EventType
from src.agent_hooks.utils.logging import get_logger, ConfigurationError


class HookRegistry:
    """
    Registry for managing hook definitions.
    
    The hook registry maintains a collection of registered hooks and provides
    methods for registering, deregistering, and looking up hooks.
    """
    
    def __init__(self):
        """Initialize the hook registry."""
        self.logger = get_logger("core.hook_registry")
        self.hooks: Dict[str, AgentHook] = {}
        self.hooks_by_event_type: Dict[EventType, List[str]] = {event_type: [] for event_type in EventType}
        self.hooks_by_priority: Dict[HookPriority, List[str]] = {priority: [] for priority in HookPriority}
        self.hook_dependencies: Dict[str, Set[str]] = {}
        self.dependent_hooks: Dict[str, Set[str]] = {}
    
    def register_hook(self, hook: AgentHook) -> str:
        """
        Register a hook with the registry.
        
        Args:
            hook: Hook to register
            
        Returns:
            ID of the registered hook
            
        Raises:
            ConfigurationError: If a hook with the same ID is already registered
        """
        if hook.id in self.hooks:
            raise ConfigurationError(f"Hook with ID {hook.id} is already registered")
        
        self.hooks[hook.id] = hook
        
        # Index by event type
        for trigger in hook.triggers:
            event_type = EventType(trigger.value)
            if hook.id not in self.hooks_by_event_type[event_type]:
                self.hooks_by_event_type[event_type].append(hook.id)
        
        # Index by priority
        if hook.id not in self.hooks_by_priority[hook.priority]:
            self.hooks_by_priority[hook.priority].append(hook.id)
        
        self.logger.info(
            f"Hook registered: {hook.name} ({hook.id})",
            {"hook_id": hook.id, "hook_name": hook.name}
        )
        
        return hook.id
    
    def unregister_hook(self, hook_id: str) -> bool:
        """
        Unregister a hook from the registry.
        
        Args:
            hook_id: ID of the hook to unregister
            
        Returns:
            True if the hook was found and unregistered, False otherwise
        """
        if hook_id not in self.hooks:
            return False
        
        hook = self.hooks[hook_id]
        
        # Remove from main registry
        del self.hooks[hook_id]
        
        # Remove from event type index
        for trigger in hook.triggers:
            event_type = EventType(trigger.value)
            if hook_id in self.hooks_by_event_type[event_type]:
                self.hooks_by_event_type[event_type].remove(hook_id)
        
        # Remove from priority index
        if hook_id in self.hooks_by_priority[hook.priority]:
            self.hooks_by_priority[hook.priority].remove(hook_id)
        
        # Remove from dependency tracking
        if hook_id in self.hook_dependencies:
            for dependency_id in self.hook_dependencies[hook_id]:
                if dependency_id in self.dependent_hooks and hook_id in self.dependent_hooks[dependency_id]:
                    self.dependent_hooks[dependency_id].remove(hook_id)
            del self.hook_dependencies[hook_id]
        
        if hook_id in self.dependent_hooks:
            del self.dependent_hooks[hook_id]
        
        self.logger.info(
            f"Hook unregistered: {hook.name} ({hook_id})",
            {"hook_id": hook_id, "hook_name": hook.name}
        )
        
        return True
    
    def get_hook(self, hook_id: str) -> Optional[AgentHook]:
        """
        Get a hook by ID.
        
        Args:
            hook_id: ID of the hook to get
            
        Returns:
            Hook with the specified ID, or None if not found
        """
        return self.hooks.get(hook_id)
    
    def get_hooks_for_event_type(self, event_type: EventType) -> List[AgentHook]:
        """
        Get all hooks that handle a specific event type.
        
        Args:
            event_type: Event type to get hooks for
            
        Returns:
            List of hooks that handle the specified event type
        """
        hook_ids = self.hooks_by_event_type.get(event_type, [])
        return [self.hooks[hook_id] for hook_id in hook_ids if hook_id in self.hooks]
    
    def get_hooks_by_priority(self, priority: HookPriority) -> List[AgentHook]:
        """
        Get all hooks with a specific priority.
        
        Args:
            priority: Priority to get hooks for
            
        Returns:
            List of hooks with the specified priority
        """
        hook_ids = self.hooks_by_priority.get(priority, [])
        return [self.hooks[hook_id] for hook_id in hook_ids if hook_id in self.hooks]
    
    def get_all_hooks(self) -> List[AgentHook]:
        """
        Get all registered hooks.
        
        Returns:
            List of all registered hooks
        """
        return list(self.hooks.values())
    
    def add_hook_dependency(self, hook_id: str, dependency_id: str) -> None:
        """
        Add a dependency between hooks.
        
        Args:
            hook_id: ID of the dependent hook
            dependency_id: ID of the hook that is depended on
            
        Raises:
            ConfigurationError: If either hook is not registered or if adding the dependency would create a cycle
        """
        if hook_id not in self.hooks:
            raise ConfigurationError(f"Hook with ID {hook_id} is not registered")
        
        if dependency_id not in self.hooks:
            raise ConfigurationError(f"Hook with ID {dependency_id} is not registered")
        
        # Check for cycles
        if self._would_create_cycle(hook_id, dependency_id):
            raise ConfigurationError(f"Adding dependency from {hook_id} to {dependency_id} would create a cycle")
        
        # Add dependency
        if hook_id not in self.hook_dependencies:
            self.hook_dependencies[hook_id] = set()
        self.hook_dependencies[hook_id].add(dependency_id)
        
        # Add reverse mapping
        if dependency_id not in self.dependent_hooks:
            self.dependent_hooks[dependency_id] = set()
        self.dependent_hooks[dependency_id].add(hook_id)
        
        self.logger.info(
            f"Hook dependency added: {hook_id} depends on {dependency_id}",
            {"hook_id": hook_id, "dependency_id": dependency_id}
        )
    
    def remove_hook_dependency(self, hook_id: str, dependency_id: str) -> bool:
        """
        Remove a dependency between hooks.
        
        Args:
            hook_id: ID of the dependent hook
            dependency_id: ID of the hook that is depended on
            
        Returns:
            True if the dependency was found and removed, False otherwise
        """
        if hook_id not in self.hook_dependencies or dependency_id not in self.hook_dependencies[hook_id]:
            return False
        
        # Remove dependency
        self.hook_dependencies[hook_id].remove(dependency_id)
        if not self.hook_dependencies[hook_id]:
            del self.hook_dependencies[hook_id]
        
        # Remove reverse mapping
        if dependency_id in self.dependent_hooks and hook_id in self.dependent_hooks[dependency_id]:
            self.dependent_hooks[dependency_id].remove(hook_id)
            if not self.dependent_hooks[dependency_id]:
                del self.dependent_hooks[dependency_id]
        
        self.logger.info(
            f"Hook dependency removed: {hook_id} no longer depends on {dependency_id}",
            {"hook_id": hook_id, "dependency_id": dependency_id}
        )
        
        return True
    
    def get_hook_dependencies(self, hook_id: str) -> Set[str]:
        """
        Get the dependencies of a hook.
        
        Args:
            hook_id: ID of the hook to get dependencies for
            
        Returns:
            Set of IDs of hooks that the specified hook depends on
        """
        return self.hook_dependencies.get(hook_id, set())
    
    def get_dependent_hooks(self, hook_id: str) -> Set[str]:
        """
        Get the hooks that depend on a hook.
        
        Args:
            hook_id: ID of the hook to get dependents for
            
        Returns:
            Set of IDs of hooks that depend on the specified hook
        """
        return self.dependent_hooks.get(hook_id, set())
    
    def get_hook_execution_order(self, hook_ids: List[str]) -> List[str]:
        """
        Get the order in which hooks should be executed based on dependencies.
        
        Args:
            hook_ids: IDs of hooks to order
            
        Returns:
            List of hook IDs in execution order
            
        Raises:
            ConfigurationError: If there is a dependency cycle
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        for hook_id in hook_ids:
            graph[hook_id] = set()
            if hook_id in self.hook_dependencies:
                for dependency_id in self.hook_dependencies[hook_id]:
                    if dependency_id in hook_ids:
                        graph[hook_id].add(dependency_id)
        
        # Topological sort
        result: List[str] = []
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        
        def visit(node: str) -> None:
            if node in temp_visited:
                raise ConfigurationError(f"Dependency cycle detected involving hook {node}")
            
            if node not in visited:
                temp_visited.add(node)
                
                for dependency in graph[node]:
                    visit(dependency)
                
                temp_visited.remove(node)
                visited.add(node)
                result.append(node)
        
        for hook_id in hook_ids:
            if hook_id not in visited:
                visit(hook_id)
        
        # Reverse the result to get the correct execution order
        return list(reversed(result))
    
    def _would_create_cycle(self, hook_id: str, dependency_id: str) -> bool:
        """
        Check if adding a dependency would create a cycle.
        
        Args:
            hook_id: ID of the dependent hook
            dependency_id: ID of the hook that is depended on
            
        Returns:
            True if adding the dependency would create a cycle, False otherwise
        """
        # If the dependency already depends on the hook, adding the dependency would create a cycle
        if dependency_id in self.hook_dependencies and hook_id in self._get_all_dependencies(dependency_id):
            return True
        
        return False
    
    def _get_all_dependencies(self, hook_id: str) -> Set[str]:
        """
        Get all dependencies of a hook, including transitive dependencies.
        
        Args:
            hook_id: ID of the hook to get dependencies for
            
        Returns:
            Set of IDs of all hooks that the specified hook depends on, directly or indirectly
        """
        result = set()
        to_visit = [hook_id]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            
            visited.add(current)
            
            if current in self.hook_dependencies:
                for dependency_id in self.hook_dependencies[current]:
                    result.add(dependency_id)
                    if dependency_id not in visited:
                        to_visit.append(dependency_id)
        
        return result