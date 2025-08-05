class ContextManager:
    def __init__(self):
        self.zone_contexts = {}

    def update_context(self, zone, context_data):
        if zone not in self.zone_contexts:
            self.zone_contexts[zone] = []
        # Mantener solo las últimas 10 entradas (ventana lightweight)
        self.zone_contexts[zone].append(context_data)
        self.zone_contexts[zone] = self.zone_contexts[zone][-10:]

    def get_context(self, zone):
        return self.zone_contexts.get(zone, [])
