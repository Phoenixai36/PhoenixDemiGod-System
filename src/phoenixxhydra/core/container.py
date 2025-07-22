"""
Dependency injection container for PHOENIXxHYDRA system
"""

from typing import Dict, Any, Type, TypeVar, Callable, Optional
from abc import ABC
import inspect
import asyncio

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._interfaces: Dict[Type, Type] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register a singleton service"""
        self._interfaces[interface] = implementation
        return self
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """Register a transient service (new instance each time)"""
        self._factories[interface.__name__] = implementation
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """Register a specific instance"""
        self._services[interface.__name__] = instance
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'DIContainer':
        """Register a factory function"""
        self._factories[interface.__name__] = factory
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance"""
        interface_name = interface.__name__
        
        # Check for registered instance
        if interface_name in self._services:
            return self._services[interface_name]
        
        # Check for singleton
        if interface in self._interfaces:
            if interface_name not in self._singletons:
                implementation = self._interfaces[interface]
                instance = self._create_instance(implementation)
                self._singletons[interface_name] = instance
            return self._singletons[interface_name]
        
        # Check for factory
        if interface_name in self._factories:
            factory = self._factories[interface_name]
            if callable(factory) and not inspect.isclass(factory):
                return factory()
            else:
                return self._create_instance(factory)
        
        # Try to create instance directly
        if inspect.isclass(interface) and not inspect.isabstract(interface):
            return self._create_instance(interface)
        
        raise ValueError(f"Cannot resolve service: {interface_name}")
    
    async def resolve_async(self, interface: Type[T]) -> T:
        """Resolve a service instance asynchronously"""
        instance = self.resolve(interface)
        
        # If the instance has an async initialize method, call it
        if hasattr(instance, 'initialize') and asyncio.iscoroutinefunction(instance.initialize):
            await instance.initialize()
        
        return instance
    
    def _create_instance(self, implementation: Type[T]) -> T:
        """Create an instance with dependency injection"""
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)
        
        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != inspect.Parameter.empty:
                try:
                    dependency = self.resolve(param.annotation)
                    kwargs[param_name] = dependency
                except ValueError:
                    # If we can't resolve the dependency and it has a default, use it
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        # Skip unresolvable dependencies without defaults
                        pass
        
        return implementation(**kwargs)
    
    def clear(self):
        """Clear all registrations"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._interfaces.clear()


# Global container instance
container = DIContainer()


def inject(interface: Type[T]) -> T:
    """Convenience function to resolve dependencies"""
    return container.resolve(interface)


async def inject_async(interface: Type[T]) -> T:
    """Convenience function to resolve dependencies asynchronously"""
    return await container.resolve_async(interface)