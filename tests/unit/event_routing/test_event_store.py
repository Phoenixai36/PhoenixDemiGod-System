import time
import timeit
import unittest

from src.event_routing.event_store import EventStore


class TestEventStore(unittest.TestCase):
    def setUp(self):
        self.event_store = EventStore()

    def test_store_and_get_events(self):
        event1 = {'id': 1, 'data': 'event data 1'}
        event2 = {'id': 2, 'data': 'event data 2'}
        self.event_store.store(event1)
        self.event_store.store(event2)

        events = self.event_store.get_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['id'], 1)
        self.assertEqual(events[1]['id'], 2)

    def test_get_events_filtered_by_time_range(self):
        event1 = {'id': 1, 'data': 'event data 1'}
        time.sleep(0.001)
        event2 = {'id': 2, 'data': 'event data 2'}
        time.sleep(0.001)
        event3 = {'id': 3, 'data': 'event data 3'}
        self.event_store.store(event1)
        self.event_store.store(event2)
        self.event_store.store(event3)

        start_time = event2['timestamp']
        end_time = event3['timestamp']

        filter_criteria = {'start_time': start_time, 'end_time': end_time}
        filtered_events = self.event_store.get_events(filter_criteria)
        self.assertEqual(len(filtered_events), 2)
        self.assertEqual(filtered_events[0]['id'], 2)
        self.assertEqual(filtered_events[1]['id'], 3)

    def test_get_event_by_id(self):
        event1 = {'id': 1, 'data': 'event data 1'}
        event2 = {'id': 2, 'data': 'event data 2'}
        self.event_store.store(event1)
        self.event_store.store(event2)

        retrieved_event = self.event_store.get_event_by_id(2)
        if retrieved_event:
            self.assertEqual(retrieved_event['id'], 2)
            self.assertEqual(retrieved_event['data'], 'event data 2')

        retrieved_event = self.event_store.get_event_by_id(3)
        self.assertIsNone(retrieved_event)

    def test_get_events_filtered_by_data(self):
        event1 = {'id': 1, 'data': 'event data 1'}
        event2 = {'id': 2, 'data': 'event data 2'}
        self.event_store.store(event1)
        self.event_store.store(event2)

        filter_criteria = {'data': 'event data 1'}
        filtered_events = self.event_store.get_events(filter_criteria)
        self.assertEqual(len(filtered_events), 1)
        self.assertEqual(filtered_events[0]['id'], 1)

    def test_get_events_filtered_by_any_field(self):
        event1 = {'id': 1, 'type': 'type1', 'data': 'event data 1'}
        event2 = {'id': 2, 'type': 'type2', 'data': 'event data 2'}
        self.event_store.store(event1)
        self.event_store.store(event2)

        filter_criteria = {'type': 'type1'}
        filtered_events = self.event_store.get_events(filter_criteria)
        self.assertEqual(len(filtered_events), 1)
        self.assertEqual(filtered_events[0]['id'], 1)

    def test_retention_policy(self):
        from src.event_routing.event_store import RetentionPolicy
        event1 = {'id': 1, 'type': 'type1', 'data': 'event data 1',
                  'timestamp': timeit.default_timer() - 1}
        event2 = {'id': 2, 'type': 'type1', 'data': 'event data 2',
                  'timestamp': timeit.default_timer()}
        event3 = {'id': 3, 'type': 'type2', 'data': 'event data 3',
                  'timestamp': timeit.default_timer()}
        self.event_store.store(event1)
        self.event_store.store(event2)
        self.event_store.store(event3)

        # Add retention policy for type1 events
        retention_policy = RetentionPolicy(age=1, count=1)
        self.event_store.add_retention_policy('type1', retention_policy)

        # Cleanup expired events
        self.event_store.cleanup_expired_events()

        # Verify that only one event of type1 remains
        events = self.event_store.get_events()
        type1_events = [e for e in events if e['type'] == 'type1']
        self.assertEqual(len(type1_events), 1)
        self.assertEqual(type1_events[0]['id'], 2)

        # Verify that the type2 event is still present
        type2_events = [e for e in events if e['type'] == 'type2']
        self.assertEqual(len(type2_events), 1)
        self.assertEqual(type2_events[0]['id'], 3)


if __name__ == '__main__':
    unittest.main()
