"""A low-frequency, opt-in visual attention loop for LUCID."""

import os
import threading
import time

from src.utils import Logger


class VisualPresence:
    """Observes user-shared screen changes without recording a video."""

    def __init__(self, page_store, vision_engine, on_observation):
        self.page_store = page_store
        self.vision_engine = vision_engine
        self.on_observation = on_observation
        self.interval = float(
            os.getenv("LUCID_VISUAL_REACTION_INTERVAL", "12")
        )
        self._running = False
        self._thread = None
        self._last_version = 0
        self._last_reaction_at = 0.0

    def start(self):
        if self._running:
            return

        self._running = True
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
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _run(self):
        while self._running:
            page = self.page_store.latest()

            if (
                page is None
                or not page.continuous
                or not page.has_image
                or page.version <= self._last_version
            ):
                time.sleep(0.5)
                continue

            self._last_version = page.version

            if time.monotonic() - self._last_reaction_at < self.interval:
                time.sleep(0.5)
                continue

            observation = self.vision_engine.observe(
                page,
                "화면에서 지금 실제로 보이는 변화나 활동을 짧게 관찰해 줘.",
            )
            self._last_reaction_at = time.monotonic()

            if observation and self._running:
                Logger.info("[Vision] Continuous screen change noticed")
                self.on_observation(observation)
