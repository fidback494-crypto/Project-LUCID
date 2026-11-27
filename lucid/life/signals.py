"""커널 갱신 횟수와 사고 횟수를 추적한다."""

from lucid.core.kernel import BaseModule
from lucid.log import Logger


class Heartbeat(BaseModule):
    """커널 갱신 횟수를 심박으로 기록한다."""

    def __init__(self):
        """모듈 이름과 주기 카운터를 초기화한다."""
        super().__init__("Heartbeat")
        self.tick_count = 0

    def update(self):
        """커널 주기마다 카운터를 한 번 늘리고 로그에 남긴다."""
        self.tick_count += 1
        Logger.info(f"Heartbeat : {self.tick_count}")


class Consciousness(BaseModule):
    """커널이 호출한 사고 주기의 수를 기록한다."""

    def __init__(self):
        """모듈 이름과 주기 카운터를 초기화한다."""
        super().__init__("Consciousness")
        self.thought_count = 0

    def update(self):
        """커널 주기마다 카운터를 한 번 늘리고 로그에 남긴다."""
        self.thought_count += 1
        Logger.info(f"Thinking... ({self.thought_count})")
