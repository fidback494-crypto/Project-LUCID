"""사용자가 공유 중인 화면의 의미 있는 변화를 일정 간격으로 분석한다."""

import math
import os
import threading
import time

from lucid.log import Logger


class VisualPresence:
    """공유 화면 저장소와 분석 엔진을 받아 변화가 감지되면 콜백에 관찰 문장을 전달한다."""

    def __init__(self, page_store, vision_engine, on_observation):
        """화면 저장소, 분석 엔진, 관찰 문장을 받을 콜백을 등록한다."""
        self.page_store = page_store
        self.vision_engine = vision_engine
        self.on_observation = on_observation
        try:
            interval = float(os.getenv("LUCID_VISUAL_REACTION_INTERVAL", "12"))
            if not math.isfinite(interval):
                raise ValueError("interval must be finite")
            self.interval = max(3.0, min(interval, 3600.0))
        except ValueError:
            self.interval = 12.0
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._session_id = None
        self._last_version = 0
        self._last_reaction_at = 0.0
        self._previous_observation = ""

    def start(self):
        """관찰용 스레드를 한 번만 시작한다."""
        if self._running or (self._thread is not None and self._thread.is_alive()):
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="LUCIDVisualPresence",
            daemon=True,
        )
        self._thread.start()
        Logger.info(
            "[Vision] Visual presence is ready; it reacts only to shared screen changes"
        )

    def stop(self):
        """새 관찰을 중단하고 이미 진행 중인 분석 결과를 무시한다."""
        self._running = False
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=2)
            if not self._thread.is_alive():
                self._thread = None

    def _run(self):
        """같은 공유 세션의 최신 프레임을 관찰 간격에 맞춰 분석한다."""
        while self._running and not self._stop_event.is_set():
            page = self.page_store.latest_screen()

            if (
                page is None
                or not page.continuous
                or not page.has_image
                or page.version <= self._last_version
            ):
                self._stop_event.wait(0.5)
                continue

            if page.session_id != self._session_id:
                self._session_id = page.session_id
                self._previous_observation = ""
                self._last_reaction_at = float("-inf")

            if time.monotonic() - self._last_reaction_at < self.interval:
                self._stop_event.wait(0.5)
                continue

            self._last_version = page.version

            observation = self.vision_engine.observe(
                page,
                "현재 화면과 이전 관찰을 비교해. 장면과 의미 있는 변화만 짧게 알려 줘.",
                previous_observation=self._previous_observation,
            )
            self._last_reaction_at = time.monotonic()

            if not observation:
                continue

            latest_page = self.page_store.latest_screen()

            if (
                not self._running
                or self._stop_event.is_set()
                or latest_page is None
                or not latest_page.continuous
                or latest_page.session_id != page.session_id
            ):
                continue

            if self._is_no_change(observation):
                continue

            self._previous_observation = observation

            if self._running and not self._stop_event.is_set():
                Logger.info("[Vision] Continuous screen change noticed")
                try:
                    self.on_observation(observation)
                except Exception as error:
                    Logger.error(f"[Vision] Presence reaction failed: {error}")

    @staticmethod
    def _is_no_change(observation):
        """분석기가 장면 변화가 없다고 응답했는지 판정한다."""
        normalized = " ".join(observation.lower().strip().split())
        return any(
            marker in normalized
            for marker in (
                "변화 없음",
                "변화가 없음",
                "의미 있는 변화가 없",
                "no change",
                "no meaningful change",
            )
        )
