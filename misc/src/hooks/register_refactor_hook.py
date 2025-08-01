from src.hooks.cellular_communication_hook import CellularCommunicationHook
from src.hooks.container_log_analysis_hook import ContainerLogAnalysisHook
from src.hooks.container_resource_scaling_hook import ContainerResourceScalingHook
from src.hooks.core.config import AgentHooksConfig
from src.hooks.core.events import EventBus


async def register_hooks(event_bus: EventBus, config: AgentHooksConfig):
    """Registers the refactored hooks with the event bus."""
    cellular_hook = CellularCommunicationHook(event_bus, config)
    await cellular_hook.start()
    container_log_analysis_hook = ContainerLogAnalysisHook(event_bus, config)
    await container_log_analysis_hook.start()
    container_resource_scaling_hook = ContainerResourceScalingHook(event_bus, config)
    await container_resource_scaling_hook.start()
