import uuid


class EventCorrelator:
    def __init__(self):
        self.correlation_chains = {}

    def correlate(self, event, correlation_id=None, causation_id=None):
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        event.correlation_id = correlation_id
        event.causation_id = causation_id

        if correlation_id not in self.correlation_chains:
            self.correlation_chains[correlation_id] = []

        self.correlation_chains[correlation_id].append(event)

        return correlation_id

    def get_correlation_chain(self, correlation_id):
        return self.correlation_chains.get(correlation_id) or []
