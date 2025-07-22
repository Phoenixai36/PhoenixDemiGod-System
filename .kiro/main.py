import asyncio
import os
import importlib.util
from typing import List
from .engine.core.models import AgentHook
from .engine.events.router import EventRouter
from .engine.events.models import BaseEvent, EventType

def load_hooks_from_directory(directory: str) -> List[AgentHook]:
    """Dynamically load hooks from a directory."""
    hooks = []
    for filename in os.listdir(directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            filepath = os.path.join(directory, filename)
            module_name = f"kiro.hooks.{filename[:-3]}"
            
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                for item in dir(module):
                    obj = getattr(module, item)
                    if isinstance(obj, type) and issubclass(obj, AgentHook) and obj is not AgentHook:
                        # This assumes hooks can be instantiated with a default config
                        hooks.append(obj(config={}))
    return hooks

async def main():
    """Main entry point for the Kiro agent hook system."""
    hooks_dir = os.path.join(os.path.dirname(__file__), "hooks")
    loaded_hooks = load_hooks_from_directory(hooks_dir)
    
    router = EventRouter(hooks=loaded_hooks)
    
    # Example: simulate a file save event
    print("Simulating a file save event...")
    test_event = BaseEvent(
        source="test_runner",
        type=EventType.FILE_SAVE,
        correlation_id="test_run_123"
    )
    await router.route_event(test_event)
    print("Event processing complete.")

if __name__ == "__main__":
    asyncio.run(main())