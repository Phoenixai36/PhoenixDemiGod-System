from dataclasses import dataclass

from src.hooks.core.events import Event


@dataclass
class ContainerLogAnalysisEvent(Event):
    container_name: str
    log_message: str
    log_level: str