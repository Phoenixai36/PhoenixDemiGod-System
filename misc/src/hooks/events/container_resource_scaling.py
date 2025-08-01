from dataclasses import dataclass, field
from typing import Optional

from src.hooks.core.events import Event


@dataclass
class ContainerResourceScalingEvent(Event):
    container_name: Optional[str] = field(default=None)
    old_cpu: Optional[float] = field(default=None)
    new_cpu: Optional[float] = field(default=None)
    old_memory: Optional[float] = field(default=None)
    new_memory: Optional[float] = field(default=None)