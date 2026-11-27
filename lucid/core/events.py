"""이벤트 기록과 동기식 구독 알림."""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from lucid.log import Logger


@dataclass
class Event:
    """종류와 내용을 저장하고 생성 시각을 기록하는 이벤트 한 건."""

    event_type: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class EventManager:
    """발생 순서대로 이벤트를 기록한다."""

    def __init__(self) -> None:
        """이벤트를 발생 순으로 보관할 빈 목록을 준비한다."""
        self.events: list[Event] = []

    def add_event(self, event_type: str, content: str) -> Event:
        """종류와 내용으로 이벤트를 생성하여 기록하고 그 이벤트를 반환한다."""
        event = Event(event_type, content)
        self.events.append(event)
        return event

    def get_events(self) -> list[Event]:
        """발생 순서로 정렬된 이벤트 목록을 반환한다."""
        return self.events


class EventBus:
    """이벤트 이름별로 등록한 콜백을 동기적으로 호출한다."""

    def __init__(self) -> None:
        """이벤트 이름별로 빈 구독 목록을 준비한다."""
        self.subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """event_name 알림에 데이터 하나를 받는 callback을 등록한다."""
        self.subscribers[event_name].append(callback)
        Logger.info(
            f"Subscribed : {getattr(callback, '__qualname__', type(callback).__name__)} -> {event_name}"
        )

    def publish(self, event_name: str, data=None) -> None:
        """event_name에 등록된 구독자들에게 data를 순차적으로 전달한다."""
        Logger.info(f"Event : {event_name}")
        for callback in tuple(self.subscribers.get(event_name, ())):
            callback(data)
