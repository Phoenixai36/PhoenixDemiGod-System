import timeit
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RetentionPolicy:
    age: Optional[int] = None  # Tiempo en segundos
    count: Optional[int] = None


class EventStore:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.retention_policies: Dict[str, RetentionPolicy] = {}

    def store(self, event: Dict[str, Any]):
        event['timestamp'] = timeit.default_timer()
        self.events.append(event)

    def get_events(
        self, filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if filter_criteria is None:
            return sorted(self.events, key=lambda x: x['timestamp'])
        else:
            filtered_events = self.events
            if 'start_time' in filter_criteria:
                filtered_events = [
                    e
                    for e in filtered_events
                    if 'timestamp' in e
                    and e['timestamp'] >= filter_criteria['start_time']
                ]
            if 'end_time' in filter_criteria:
                filtered_events = [
                    e
                    for e in filtered_events
                    if 'timestamp' in e
                    and e['timestamp'] <= filter_criteria['end_time']
                ]
            for key, value in filter_criteria.items():
                if key not in ['start_time', 'end_time']:
                    filtered_events = [
                        e for e in filtered_events if e.get(key) == value
                    ]
            return sorted(filtered_events, key=lambda x: x['timestamp'])

    def get_event_by_id(self, event_id: Any) -> Optional[Dict[str, Any]]:
        for event in self.events:
            if event.get('id') == event_id:
                return event
        return None

    def add_retention_policy(self, event_type: str, policy: RetentionPolicy):
        self.retention_policies[event_type] = policy

    def cleanup_expired_events(self):
        now = timeit.default_timer()
        for event_type, policy in self.retention_policies.items():
            if policy.age is not None:
                self.events = [
                    event
                    for event in self.events
                    if event.get('type') != event_type
                    or (event.get('timestamp') is not None
                        and event['timestamp'] >= now - policy.age)
                ]
            if policy.count is not None:
                event_list = [
                    event
                    for event in self.events
                    if event.get('type') == event_type
                ]
                if len(event_list) > policy.count:
                    if policy.count <= len(event_list):
                        self.events = [
                            event
                            for event in self.events
                            if event.get('type') != event_type
                            or event in event_list[policy.count:]
                        ]
                    else:
                        # Si policy.count es mayor que la
                        # longitud de event_list, simplemente
                        # eliminamos todos los eventos de este tipo.
                        self.events = [
                            event
                            for event in self.events
                            if event.get('type') != event_type
                        ]
