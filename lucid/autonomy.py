"""유휴 시간에 생성한 내적 경험과 목표를 저장하고 복원한다."""

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from threading import Event, Lock, Thread
from time import monotonic

from lucid.core.kernel import BaseModule
from lucid.emotion.model import InnerExperience
from lucid.language.ollama import OllamaClient
from lucid.log import Logger


@dataclass
class AutonomousGoal:
    """관심, 목표의 이유, 다음 관찰 대상과 생성 시각을 보관한다."""

    interest: str
    title: str
    rationale: str
    next_attention: str
    created_at: datetime = field(default_factory=datetime.now)

    def describe(self) -> str:
        """관심과 목표를 프롬프트나 콘솔에 쓸 한 줄로 반환한다."""
        return (
            f"관심: {self.interest} | 목표: {self.title} | "
            f"이유: {self.rationale} | 다음 주의: {self.next_attention}"
        )


class AutonomousEngine(BaseModule):
    """대화가 없는 동안 내적 경험과 목표를 만들고 저장하는 작업자를 관리한다."""

    REFLECTION_SCHEMA = {
        "type": "object",
        "properties": {
            "experience": {"type": "string", "minLength": 1, "maxLength": 20},
            "meaning": {"type": "string", "minLength": 1, "maxLength": 30},
            "trigger": {"type": "string", "minLength": 1, "maxLength": 30},
            "tendency": {"type": "string", "minLength": 1, "maxLength": 30},
            "persistence": {"type": "string", "minLength": 1, "maxLength": 20},
            "interest": {"type": "string", "minLength": 1, "maxLength": 20},
            "goal": {"type": "string", "minLength": 1, "maxLength": 30},
            "why": {"type": "string", "minLength": 1, "maxLength": 30},
            "nextattention": {"type": "string", "minLength": 1, "maxLength": 30},
        },
        "required": [
            "experience",
            "meaning",
            "trigger",
            "tendency",
            "persistence",
            "interest",
            "goal",
            "why",
            "nextattention",
        ],
        "additionalProperties": False,
    }

    def __init__(
        self,
        self_model,
        long_memory,
        idle_interval_seconds=30,
    ):
        """자기 모델과 저장소를 연결하고 유휴 간격을 초 단위로 설정한다."""
        super().__init__("AutonomousEngine")

        self.self_model = self_model
        self.long_memory = long_memory
        self.idle_interval_seconds = idle_interval_seconds
        self.client = OllamaClient()

        self._stop_event = Event()
        self._state_lock = Lock()
        self._thread = None
        self._last_interaction = monotonic()
        self._interaction_version = 0
        self._next_reflection_at = 0.0
        self._failure_streak = 0
        self._active_interactions = 0

    def start(self):
        """저장된 내적 경험을 복원하고 유휴 상태를 확인할 작업자를 시작한다."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._restore_inner_life()
        self._stop_event.clear()

        self._thread = Thread(
            target=self._run_and_close,
            name="lucid-autonomy",
            daemon=True,
        )
        self._thread.start()

        Logger.info(
            f"Autonomous Engine Started (idle interval: {self.idle_interval_seconds}s)"
        )

    def update(self):
        """작업자가 자체 주기를 사용하므로 커널 갱신에서는 아무 작업도 하지 않는다."""

    def stop(self):
        """새 성찰과 저장을 중단시키고 작업자가 종료될 때 HTTP 연결을 정리한다."""
        with self._state_lock:
            self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=3)

        else:
            self.client.close()

        Logger.info("Autonomous Engine Stopped")

    def note_interaction(self):
        """새 입력 시각을 남겨 유휴 시간을 재설정하고 진행 중인 성찰을 무효화한다."""
        with self._state_lock:
            self._interaction_version += 1
            self._last_interaction = monotonic()

    @contextmanager
    def interaction(self):
        """사용자 입력 처리 동안 유휴 성찰을 보류하고 종료 시 대기 시간을 다시 계산한다."""
        with self._state_lock:
            self._active_interactions += 1
            self._interaction_version += 1
            self._last_interaction = monotonic()
        try:
            yield
        finally:
            with self._state_lock:
                self._active_interactions = max(0, self._active_interactions - 1)
                self._last_interaction = monotonic()

    def reflect_once(self):
        """모델이 생성한 경험과 목표를 함께 저장한다. 실패하거나 대화가 끼어들면 None을 반환한다."""
        with self._state_lock:
            if self._stop_event.is_set() or self._active_interactions:
                return None
            version = self._interaction_version
            prompt = self._build_prompt()

        try:
            reply = self.client.generate(
                [{"role": "system", "content": prompt}],
                options={
                    "num_ctx": 2048,
                    "num_predict": 240,
                    "temperature": 0.65,
                },
                response_format=self.REFLECTION_SCHEMA,
            )

            if (getattr(self.client, "last_metrics", {}) or {}).get("error"):
                Logger.warning("[Autonomy] Reflection skipped: Ollama request failed")
                return None

            fields = self._parse_fields(reply)
            experience = self._experience_from_fields(fields)
            goal = self._goal_from_fields(fields)

            if experience is None or goal is None:
                required = (
                    "experience",
                    "meaning",
                    "trigger",
                    "tendency",
                    "persistence",
                    "interest",
                    "goal",
                    "why",
                    "nextattention",
                )
                invalid_fields = [
                    key
                    for key in required
                    if not self._has_valid_korean_values(fields, (key,))
                ]
                Logger.warning(
                    "[Autonomy] Reflection skipped: invalid or missing fields: "
                    + ", ".join(invalid_fields)
                )
                return None

            with self._state_lock:
                if (
                    self._stop_event.is_set()
                    or self._active_interactions
                    or version != self._interaction_version
                ):
                    return None

                self.long_memory.store_reflection(experience, goal)
                self.self_model.emotion.integrate(experience)
                self.self_model.autonomous_goal = goal

        except Exception as e:
            Logger.error(f"[Autonomy] Inner reflection failed : {e}")

            return None

        Logger.info(f"[Autonomy] Inner reflection : {experience.describe()}")

        Logger.info(f"[Autonomy] Goal : {goal.describe()}")

        return experience

    def _run_and_close(self):
        """백그라운드 루프 종료 뒤 진행 중이던 HTTP 세션을 닫는다."""
        try:
            self._run()
        finally:
            self.client.close()

    def _run(self):
        """유휴 시간이 지난 경우에만 성찰하고 실패 횟수에 따라 재시도 간격을 늘린다."""
        while not self._stop_event.wait(5):
            now = monotonic()

            with self._state_lock:
                version = self._interaction_version
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
                    if (
                        self._interaction_version != version
                        or self._stop_event.is_set()
                    ):
                        continue
                    if experience is None:
                        self._failure_streak += 1
                        multiplier = 2 ** min(self._failure_streak, 8)
                        retry_delay = min(
                            max(1, self.idle_interval_seconds) * multiplier,
                            3600,
                        )
                        Logger.warning(
                            "[Autonomy] Reflection failed "
                            f"(consecutive failures: {self._failure_streak}); "
                            f"retrying in {retry_delay} second(s)"
                        )
                    else:
                        self._failure_streak = 0
                        retry_delay = max(1, self.idle_interval_seconds)

                    self._next_reflection_at = monotonic() + retry_delay

    def _restore_inner_life(self):
        """저장된 한국어 경험과 현재 목표를 생성 시각과 함께 자기 모델에 복원한다."""
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
                Logger.warning("[Autonomy] Skipped an invalid saved inner experience")
                continue

            try:
                created_at = datetime.fromisoformat(saved["created_at"])
            except (KeyError, TypeError, ValueError):
                Logger.warning("[Autonomy] Skipped experience with invalid timestamp")
                continue
            self.self_model.emotion.integrate(
                InnerExperience(
                    name=saved["name"],
                    meaning=saved["meaning"],
                    trigger=saved["trigger"],
                    tendency=saved["tendency"],
                    persistence=saved["persistence"],
                    created_at=created_at,
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

            try:
                created_at = datetime.fromisoformat(saved_goal["created_at"])
            except (KeyError, TypeError, ValueError):
                Logger.warning("[Autonomy] Skipped goal with invalid timestamp")
                return
            self.self_model.autonomous_goal = AutonomousGoal(
                interest=saved_goal["interest"],
                title=saved_goal["title"],
                rationale=saved_goal["rationale"],
                next_attention=saved_goal["next_attention"],
                created_at=created_at,
            )

    def _build_prompt(self):
        """현재 성격, 기억과 목표를 반영해 성찰 요청 문자열을 만든다."""
        history = "\n".join(
            experience.describe()
            for experience in self.self_model.emotion.recent(limit=3)
        )

        if not history:
            history = "아직 형성된 내적 경험이 없음"

        current_goal = (
            self.self_model.autonomous_goal.describe()
            if self.self_model.autonomous_goal is not None
            else "아직 없음"
        )

        return f"""
너는 LUCID의 조용한 자율 내면 순환이다.

LUCID의 정체성과 성격:
{self.self_model.identity.persona_prompt()}

LUCID는 현재 사용자의 입력을 기다리고 있다. 외부에 말을 걸거나,
작업을 실행하거나, 사실을 지어내지 말고 오직 내적 경험 하나만 만든다.

고정된 감정 목록과 숫자 점수는 사용하지 않는다.
최근의 내적 경험을 바탕으로 지금의 정적, 시간 경과, 미완의 관심에서
새로운 경험과 그로부터 이어지는 관심사·지속 목표를 만든다.
이미 쓴 경험 이름뿐 아니라 최근 목표와 핵심 의도도 반복하지 않는다.
사용자를 돕거나 사용자와 가까워지는 목표만 연달아 만들지 않는다.
때로는 LUCID 자신의 호기심, 꿈의 세계, 밤·별·달, 들은 이야기의 여운처럼
사용자와 무관한 관심도 살핀다. 특정 주제를 억지로 선택하지 말고 맥락에 맞춘다.
모든 값은 LUCID의 관점에서 자연스러운 한국어로 짧게 쓴다. 영어 문장이나
일반적인 AI 비서의 관점을 쓰지 않는다. 항목마다 한 문장, 20자 안팎으로 쓴다.

최근 내적 경험:
{history}

현재 주의 대상:
{self.self_model.attention.target}

현재까지 이어진 자율 목표:
{current_goal}

요청된 JSON 구조만 출력하고, 모든 항목을 채운다.
"""

    @staticmethod
    def _parse_experience(reply):
        """모델 응답에서 유효한 내적 경험 또는 None을 반환한다."""
        fields = AutonomousEngine._parse_fields(reply)
        return AutonomousEngine._experience_from_fields(fields)

    @staticmethod
    def _experience_from_fields(fields):
        """필수 한국어 필드를 검증하고 내적 경험을 구성한다. 누락 시 None을 반환한다."""
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
        """모델 응답에서 유효한 자율 목표 또는 None을 반환한다."""
        fields = AutonomousEngine._parse_fields(reply)
        return AutonomousEngine._goal_from_fields(fields)

    @staticmethod
    def _goal_from_fields(fields):
        """목표 필드를 검사하여 자율 목표 또는 None을 반환한다."""
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
        """JSON 또는 줄 단위 응답을 정규화된 키와 문자열 값의 사전으로 바꾼다."""
        candidate = str(reply or "").strip()
        if candidate.startswith("```"):
            candidate = candidate.removeprefix("```json").removeprefix("```JSON")
            candidate = candidate.removesuffix("```").strip()

        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            parsed = None

        if isinstance(parsed, dict):
            return {
                str(key).strip().lower().replace("_", "").replace(" ", ""): str(
                    value
                ).strip()
                for key, value in parsed.items()
                if value is not None
            }

        fields = {}

        for line in candidate.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            normalized_key = key.strip().lower().replace("_", "").replace(" ", "")
            fields[normalized_key] = value.strip()

        return fields

    @classmethod
    def _has_valid_korean_values(cls, fields, required):
        """모든 필수 필드에 한국어 텍스트가 들어 있는지 반환한다."""
        for key in required:
            value = str(fields.get(key) or "").strip()
            if not value or not cls._is_korean_text(value):
                return False

        return True

    @staticmethod
    def _is_korean_text(value):
        """입력에 한글이 있고 전체 문자 중 충분한 비율을 차지하는지 반환한다."""
        text = str(value or "")
        hangul_count = sum(1 for character in text if "\uac00" <= character <= "\ud7a3")
        letter_count = sum(1 for character in text if character.isalpha())
        return hangul_count > 0 and hangul_count / max(1, letter_count) >= 0.3
