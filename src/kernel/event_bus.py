"""
Project LUCID

Artificial Mind Project

Module : EventBus

Creator : 시드
"""

from collections import defaultdict

from src.utils import Logger


class EventBus:
    """LUCID의 모든 기관이 사용하는 이벤트 시스템"""

    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_name: str, callback):
        """이벤트 구독"""

        self.subscribers[event_name].append(callback)

        Logger.info(
            f"Subscribed : {callback.__qualname__} -> {event_name}"
        )

    def publish(self, event_name: str, data=None):
        """이벤트 발생"""

        Logger.info(f"Event : {event_name}")

        if event_name not in self.subscribers:
            return

        for callback in self.subscribers[event_name]:
            callback(data)