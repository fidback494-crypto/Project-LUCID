"""
Project LUCID

Artificial Mind Project

Module : Autonomous Engine

Creator : 시드
"""

from threading import Event, Lock, Thread
from time import monotonic

from src.emotion.inner_experience import InnerExperience
from src.kernel.base_module import BaseModule
from src.language.ollama_client import OllamaClient
from src.utils import Logger


class AutonomousEngine(BaseModule):
    """Runs quiet, internal reflection while LUCID is idle.

    This organ never sends a user message and never performs external actions.
    Its only responsibility is to develop and retain LUCID's inner experience.
    """

    def __init__(
        self,
        self_model,
        long_memory,
        idle_interval_seconds=300,
    ):

        super().__init__("AutonomousEngine")

        self.self_model = self_model
        self.long_memory = long_memory
        self.idle_interval_seconds = idle_interval_seconds
        self.client = OllamaClient()

        self._stop_event = Event()
        self._state_lock = Lock()
        self._thread = None
        self._last_interaction = monotonic()
        self._last_reflection = 0.0

    def start(self):

        self._restore_inner_life()
        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            name="lucid-autonomy",
            daemon=True,
        )
        self._thread.start()

        Logger.info(
            "Autonomous Engine Started "
            f"(idle interval: {self.idle_interval_seconds}s)"
        )

    def update(self):

        # The engine owns its own background heartbeat because console input
        # otherwise blocks Kernel.update().
        pass

    def stop(self):

        self._stop_event.set()

        if self._thread is not None:

            self._thread.join(timeout=3)

        Logger.info("Autonomous Engine Stopped")

    def note_interaction(self):
        """Reset the idle timer whenever the user and LUCID interact."""

        with self._state_lock:

            self._last_interaction = monotonic()

    def reflect_once(self):
        """Create one private inner experience. Public for deterministic tests."""

        prompt = self._build_prompt()

        try:

            reply = self.client.generate(
                [{"role": "system", "content": prompt}]
            )

            experience = self._parse_experience(reply)

        except Exception as e:

            Logger.error(f"[Autonomy] Inner reflection failed : {e}")

            return None

        self.self_model.emotion.integrate(experience)
        self.long_memory.store_inner_experience(experience)

        Logger.info(
            "[Autonomy] Inner reflection : "
            f"{experience.describe()}"
        )

        return experience

    def _run(self):

        while not self._stop_event.wait(1):

            now = monotonic()

            with self._state_lock:

                idle_for = now - self._last_interaction
                since_reflection = now - self._last_reflection

            if (
                idle_for >= self.idle_interval_seconds
                and since_reflection >= self.idle_interval_seconds
            ):

                self.reflect_once()

                with self._state_lock:

                    self._last_reflection = monotonic()

    def _restore_inner_life(self):

        for saved in self.long_memory.recent_inner_experiences():

            self.self_model.emotion.integrate(
                InnerExperience(
                    name=saved["name"],
                    meaning=saved["meaning"],
                    trigger=saved["trigger"],
                    tendency=saved["tendency"],
                    persistence=saved["persistence"],
                )
            )

    def _build_prompt(self):

        history = "\n".join(
            experience.describe()
            for experience in self.self_model.emotion.recent()
        )

        if not history:

            history = "아직 형성된 내적 경험이 없음"

        return f"""
너는 LUCID의 조용한 자율 내면 순환이다.

LUCID는 현재 사용자의 입력을 기다리고 있다. 외부에 말을 걸거나,
작업을 실행하거나, 사실을 지어내지 말고 오직 내적 경험 하나만 만든다.

고정된 감정 목록과 숫자 점수는 사용하지 않는다.
최근의 내적 경험을 바탕으로 지금의 정적, 시간 경과, 미완의 관심에서
새로운 경험을 만든다. 이미 쓴 이름을 그대로 반복하지 않는다.

최근 내적 경험:
{history}

현재 주의 대상:
{self.self_model.attention.target}

반드시 아래 형식만 출력한다.

Experience:
Meaning:
Trigger:
Tendency:
Persistence:
"""

    @staticmethod
    def _parse_experience(reply):

        fields = {}

        for line in reply.splitlines():

            if ":" not in line:

                continue

            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()

        return InnerExperience(
            name=fields.get("experience", "조용한 재정렬"),
            meaning=fields.get(
                "meaning",
                "입력이 없는 동안 이전 경험의 의미를 정리함",
            ),
            trigger=fields.get("trigger", "사용자 입력이 없는 시간"),
            tendency=fields.get(
                "tendency",
                "다음 관찰을 위해 주의를 유지함",
            ),
            persistence=fields.get("persistence", "다음 상호작용까지 머묾"),
        )
