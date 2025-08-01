from dataclasses import dataclass

from src.hooks.core.events import Event


@dataclass
class CellularCommunicationEvent(Event):
    device_id: str = ""
    signal_strength: int = 0
    timestamp: float = 0.0