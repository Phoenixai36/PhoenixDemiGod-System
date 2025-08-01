import dataclasses
import time
from datetime import datetime
from typing import Any, Dict, List

from .event_routing import Event, EventRouter
from .event_store import EventStoreBase


class EventReplayer:
    def __init__(self, router: EventRouter, event_store: EventStoreBase):
        self.router = router
        self.event_store = event_store

    def replay_by_correlation_id(
        self, correlation_id: str, speed_multiplier: float = 0
    ) -> None:
        """
        Reproduce una cadena de eventos por su ID de correlación.
        Si speed_multiplier es 0, la reproducción es instantánea.
        """
        events = self.event_store.query_events({"correlation_id": correlation_id})
        self._replay_events(events, speed_multiplier)

    def replay_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, Any] = {},
        speed_multiplier: float = 0,
    ) -> None:
        """
        Reproduce eventos dentro de un rango de tiempo, con filtros opcionales.
        """
        query = {"start_time": start_time, "end_time": end_time, **filters}
        events = self.event_store.query_events(query)
        self._replay_events(events, speed_multiplier)

    def _replay_events(self, events: List[Event], speed_multiplier: float) -> None:
        """Lógica central de reproducción de eventos."""
        # Ordenar por timestamp para una reproducción correcta
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        for i, event in enumerate(sorted_events):
            # Marcar como evento de replay
            replayed_event = dataclasses.replace(event, is_replay=True)
            self.router.publish(replayed_event)

            if speed_multiplier > 0 and i + 1 < len(sorted_events):
                # Esperar para simular el tiempo original
                time_diff = (
                    sorted_events[i + 1].timestamp - event.timestamp
                ).total_seconds()
                time.sleep(time_diff / speed_multiplier)