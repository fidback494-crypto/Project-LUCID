from .event import Event


class EventManager:
    def __init__(self):
        self.events = []

    def add_event(self, event_type, content):
        event = Event(event_type, content)
        self.events.append(event)
        return event

    def get_events(self):
        return self.events