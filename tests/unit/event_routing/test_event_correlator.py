import unittest
import uuid

from src.event_routing.event_correlator import EventCorrelator


class MockEvent:
    def __init__(self):
        self.correlation_id = None
        self.causation_id = None


class TestEventCorrelator(unittest.TestCase):

    def setUp(self):
        self.correlator = EventCorrelator()

    def test_correlate_new_workflow(self):
        event = MockEvent()
        correlation_id = self.correlator.correlate(event)
        self.assertIsNotNone(event.correlation_id)
        self.assertEqual(event.correlation_id, correlation_id)
        self.assertIsNone(event.causation_id)
        self.assertIn(correlation_id, self.correlator.correlation_chains)
        self.assertEqual(
            len(self.correlator.correlation_chains[correlation_id]),
            1)
        self.assertEqual(
            self.correlator.correlation_chains[correlation_id][0],
            event)

    def test_correlate_existing_workflow(self):
        event1 = MockEvent()
        correlation_id = self.correlator.correlate(event1)
        event2 = MockEvent()
        self.correlator.correlate(
            event2,
            correlation_id=correlation_id,
            causation_id=event1.correlation_id)
        self.assertEqual(event2.correlation_id, correlation_id)
        self.assertEqual(event2.causation_id, event1.correlation_id)
        self.assertEqual(
            len(self.correlator.correlation_chains[correlation_id]),
            2)
        self.assertEqual(
            self.correlator.correlation_chains[correlation_id][1],
            event2)

    def test_get_correlation_chain(self):
        event1 = MockEvent()
        correlation_id = self.correlator.correlate(event1)
        event2 = MockEvent()
        self.correlator.correlate(
            event2,
            correlation_id=correlation_id,
            causation_id=event1.correlation_id)
        chain = self.correlator.get_correlation_chain(correlation_id)
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0], event1)
        self.assertEqual(chain[1], event2)

    def test_get_correlation_chain_not_found(self):
        chain = self.correlator.get_correlation_chain("nonexistent_id")
        self.assertEqual(chain, [])

    def test_correlate_new_workflow_with_id(self):
        event = MockEvent()
        correlation_id = str(uuid.uuid4())
        returned_id = self.correlator.correlate(
            event,
            correlation_id=correlation_id)
        self.assertEqual(event.correlation_id, correlation_id)
        self.assertEqual(returned_id, correlation_id)

    def test_correlate_existing_workflow_causation_id(self):
        event1 = MockEvent()
        correlation_id = self.correlator.correlate(event1)
        event2 = MockEvent()
        self.correlator.correlate(
            event2,
            correlation_id=correlation_id,
            causation_id="test_causation_id")
        self.assertEqual(event2.causation_id, "test_causation_id")


if __name__ == '__main__':
    unittest.main()
