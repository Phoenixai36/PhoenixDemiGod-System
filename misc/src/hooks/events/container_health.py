from dataclasses import dataclass

from src.hooks.core.events import Event


@dataclass
class ContainerHealthChangedEvent(Event):
    container_name: str
    old_status: str
    new_status: str