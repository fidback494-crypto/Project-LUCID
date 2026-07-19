from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    event_type: str
    content: str
    timestamp: datetime = datetime.now()