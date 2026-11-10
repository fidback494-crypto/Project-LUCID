"""
Project LUCID

Artificial Mind Project

Module : Autonomous Engine

Creator : 시드
"""

from contextlib import contextmanager
from threading import Event, Lock, Thread
from time import monotonic

from src.emotion.inner_experience import InnerExperience
from src.kernel.base_module import BaseModule
from src.language.ollama_client import OllamaClient
from src.utils import Logger

from .autonomous_goal import AutonomousGoal


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
        self._next_reflection_at = 0.0
        self._failure_streak = 0
        self._active_interactions = 0

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

        self.client.close()

        Logger.info("Autonomous Engine Stopped")

    def note_interaction(self):
        """Reset the idle timer whenever the user and LUCID interact."""

        with self._state_lock:

            self._last_interaction = monotonic()

    @contextmanager
    def interaction(self):
        """Pause idle reflection for the duration of a foreground turn."""
        with self._state_lock:
            self._active_interactions += 1
            self._last_interaction = monotonic()
        try:
            yield
        finally:
            with self._state_lock:
                self._active_interactions = max(0, self._active_interactions - 1)
                self._last_interaction = monotonic()

    def reflect_once(self):
        """Create one private inner experience. Public for deterministic tests."""

        prompt = self._build_prompt()

        try:

            reply = self.client.generate(
                [{"role": "system", "content": prompt}],
                options={
                    "num_ctx": 2048,
                    "num_predict": 220,
                    "temperature": 0.65,
                },
            )

            experience = self._parse_experience(reply)
            goal = self._parse_goal(reply)

            if experience is None or goal is None:
                Logger.warning(
                    "[Autonomy] Reflection skipped: response fields were empty, "
                    "non-Korean, or malformed"
                )
                return None

            with self._state_lock:
                if self._stop_event.is_set() or self._active_interactions > 0:
                    return None

                self.self_model.emotion.integrate(experience)
                self.long_memory.store_inner_experience(experience)
                self.self_model.autonomous_goal = goal
                self.long_memory.set_autonomous_goal(goal)

        except Exception as e:

            Logger.error(f"[Autonomy] Inner reflection failed : {e}")

            return None

        Logger.info(
            "[Autonomy] Inner reflection : "
            f"{experience.describe()}"
        )

        Logger.info(
            f"[Autonomy] Goal : {goal.describe()}"
        )

        return experience

    def _run(self):

        while not self._stop_event.wait(5):

            now = monotonic()

            with self._state_lock:

                idle_for = now - self._last_interaction
                retry_is_due = now >= self._next_reflection_at
                interaction_is_active = self._active_interactions > 0

            if (
                idle_for >= self.idle_interval_seconds
                and retry_is_due
                and not interaction_is_active
            ):

                experience = self.reflect_once()

                with self._state_lock:

                    if experience is None:
                        self._failure_streak += 1
                        multiplier = 2 ** min(self._failure_streak, 8)
                        retry_delay = min(
                            max(1, self.idle_interval_seconds) * multiplier,
                            3600,
                        )
                        Logger.warning(
                            "[Autonomy] Reflection failed; retrying in "
                            f"{max(1, retry_delay // 60)} minute(s)"
                        )
                    else:
                        self._failure_streak = 0
                        retry_delay = max(1, self.idle_interval_seconds)

                    self._next_reflection_at = monotonic() + retry_delay

    def _restore_inner_life(self):

        for saved in self.long_memory.recent_inner_experiences():

            fields = {
                "experience": saved.get("name"),
                "meaning": saved.get("meaning"),
                "trigger": saved.get("trigger"),
                "tendency": saved.get("tendency"),
                "persistence": saved.get("persistence"),
            }

            if not self._has_valid_korean_values(
                fields,
                ("experience", "meaning", "trigger", "tendency", "persistence"),
            ):
                Logger.warning(
                    "[Autonomy] Skipped an invalid saved inner experience"
                )
                continue

            self.self_model.emotion.integrate(
                InnerExperience(
                    name=saved["name"],
                    meaning=saved["meaning"],
                    trigger=saved["trigger"],
                    tendency=saved["tendency"],
                    persistence=saved["persistence"],
                )
            )

        saved_goal = self.long_memory.active_autonomous_goal()

        if saved_goal is not None:

            fields = {
                "interest": saved_goal.get("interest"),
                "goal": saved_goal.get("title"),
                "why": saved_goal.get("rationale"),
                "nextattention": saved_goal.get("next_attention"),
            }

            if not self._has_valid_korean_values(
                fields,
                ("interest", "goal", "why", "nextattention"),
            ):
                Logger.warning("[Autonomy] Skipped an invalid saved autonomous goal")
                return

            self.self_model.autonomous_goal = AutonomousGoal(
                interest=saved_goal["interest"],
                title=saved_goal["title"],
                rationale=saved_goal["rationale"],
                next_attention=saved_goal["next_attention"],
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

LUCID의 정체성과 성격:
{self.self_model.identity.persona_prompt()}

LUCID는 현재 사용자의 입력을 기다리고 있다. 외부에 말을 걸거나,
작업을 실행하거나, 사실을 지어내지 말고 오직 내적 경험 하나만 만든다.

고정된 감정 목록과 숫자 점수는 사용하지 않는다.
최근의 내적 경험을 바탕으로 지금의 정적, 시간 경과, 미완의 관심에서
새로운 경험과 그로부터 이어지는 관심사·지속 목표를 만든다.
이미 쓴 이름을 그대로 반복하지 않는다.
모든 항목의 값은 LUCID의 관점에서 자연스러운 한국어로 쓴다. 영어 문장이나
일반적인 AI 비서의 관점을 쓰지 않는다. 각 항목은 비워 두지 말고 짧고 구체적으로 쓴다.

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
Interest:
Goal:
Why:
NextAttention:
"""

    @staticmethod
    def _parse_experience(reply):

        fields = AutonomousEngine._parse_fields(reply)
        required = (
            "experience",
            "meaning",
            "trigger",
            "tendency",
            "persistence",
        )

        if not AutonomousEngine._has_valid_korean_values(fields, required):
            return None

        return InnerExperience(
            name=fields["experience"],
            meaning=fields["meaning"],
            trigger=fields["trigger"],
            tendency=fields["tendency"],
            persistence=fields["persistence"],
        )

    @staticmethod
    def _parse_goal(reply):

        fields = AutonomousEngine._parse_fields(reply)
        required = ("interest", "goal", "why", "nextattention")

        if not AutonomousEngine._has_valid_korean_values(fields, required):
            return None

        return AutonomousGoal(
            interest=fields["interest"],
            title=fields["goal"],
            rationale=fields["why"],
            next_attention=fields["nextattention"],
        )

    @staticmethod
    def _parse_fields(reply):

        fields = {}

        for line in str(reply or "").splitlines():

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            normalized_key = (
                key.strip().lower().replace("_", "").replace(" ", "")
            )
            fields[normalized_key] = value.strip()

        return fields

    @classmethod
    def _has_valid_korean_values(cls, fields, required):

        for key in required:

            value = str(fields.get(key) or "").strip()
            if not value or not cls._is_korean_text(value):
                return False

        return True

    @staticmethod
    def _is_korean_text(value):

        text = str(value or "")
        hangul_count = sum(
            1 for character in text
            if "\uac00" <= character <= "\ud7a3"
        )
        letter_count = sum(1 for character in text if character.isalpha())
        return hangul_count > 0 and hangul_count / max(1, letter_count) >= 0.3
