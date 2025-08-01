from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Se asume que 'src' está en PYTHONPATH, permitiendo importaciones absolutas.
from event_routing.event_routing import Event


class EventStoreBase(ABC):
    """
    Interfaz abstracta para el Event Store.

    Define el contrato para la persistencia y recuperación de eventos,
    desacoplando la lógica del router del almacenamiento subyacente.
    """

    @abstractmethod
    def store(self, event: Event) -> None:
        """Persiste un único evento en el almacenamiento."""
        raise NotImplementedError

    @abstractmethod
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Recupera un evento específico por su ID único."""
        raise NotImplementedError

    @abstractmethod
    def query_events(self, filter_criteria: Dict[str, Any]) -> List[Event]:
        """
        Consulta eventos basados en un diccionario de criterios de filtrado.

        Args:
            filter_criteria: Un diccionario que define los filtros a aplicar.
                             Ej: {'type': 'user.created', 'source': 'api'}

        Returns:
            Una lista de eventos que coinciden con los criterios de búsqueda.
        """
        raise NotImplementedError


class InMemoryEventStore(EventStoreBase):
    """
    Implementación en memoria del Event Store.

    Utiliza un diccionario para almacenar eventos, sirviendo como un sustituto
    ligero para desarrollo y pruebas. No es persistente.
    """

    def __init__(self):
        self._events: Dict[str, Event] = {}

    def store(self, event: Event) -> None:
        """Persiste un único evento en el diccionario en memoria."""
        self._events[event.id] = event

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Recupera un evento por su ID desde el diccionario."""
        return self._events.get(event_id)

    def query_events(self, filter_criteria: Dict[str, Any]) -> List[Event]:
        """
        Consulta eventos en memoria basados en criterios de filtrado.

        Nota: Esta implementación de consulta es básica y solo admite
        coincidencias exactas en los campos de primer nivel del evento.
        """
        results: List[Event] = []
        for event in self._events.values():
            match = True
            for key, value in filter_criteria.items():
                if not hasattr(event, key) or getattr(event, key) != value:
                    match = False
                    break
            if match:
                results.append(event)
        return results
