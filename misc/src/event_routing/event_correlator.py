import dataclasses
import uuid
from typing import List
from .event_routing import Event, EventRouter, EventPattern
from .event_store import EventStoreBase

class EventCorrelator:
    def __init__(self, router: EventRouter, event_store: EventStoreBase):
        self.router = router
        self.event_store = event_store
        self.router.subscribe(EventPattern("*"), self.handle_event)

    def handle_event(self, event: Event) -> None:
        \"\"\"
        Manejador de eventos para la suscripción.
        Enriquece el evento con IDs de correlación si es necesario.
        \"\"\"
        if event.correlation_id is None:
            # Inicia una nueva cadena de correlación
            correlation_id = str(uuid.uuid4())
            enriched_event = dataclasses.replace(event, correlation_id=correlation_id)

            # Publica el evento enriquecido
            self.router.publish(enriched_event)

    def get_correlation_chain(self, correlation_id: str) -> List[Event]:
        \"\"\"Recupera una cadena completa de eventos correlacionados desde el EventStore.\"\"\"
        return self.event_store.query_events(filter_criteria={'correlation_id': correlation_id})
