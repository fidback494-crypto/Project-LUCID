"""
Project LUCID

Artificial Mind Project

Module : Unified Cognitive Engine

Creator : 시드
"""

from src.emotion.inner_experience import InnerExperience
from src.goal.goal import Goal
from src.kernel.base_module import BaseModule
from src.language.ollama_client import OllamaClient
from src.mind.plan import Plan
from src.mind.reason import Reason
from src.mind.thought import Thought
from src.utils import Logger


class CognitiveEngine(BaseModule):
    """Produces one coherent cognitive cycle with a single LLM request."""

    def __init__(self):

        super().__init__("CognitiveEngine")
        self.client = OllamaClient()

    def start(self):

        Logger.info("Cognitive Engine Started")

    def update(self):

        pass

    def stop(self):

        Logger.info("Cognitive Engine Stopped")

    def process(self, state):

        reply = self.client.generate(
            [{"role": "system", "content": self._build_prompt(state)}]
        )

        fields = self._parse_fields(reply)
        self._apply_inner_life(state, fields)
        self._apply_reason(state, fields)
        self._apply_thought(state, fields)
        self._apply_goal_and_plan(state, fields)

        response = fields.get("reply", "").strip()

        if not response:

            action_result = getattr(state, "action_result", None)

            if action_result and action_result.output:

                response = action_result.output

            else:

                response = reply.strip() or "지금은 응답을 정리하지 못했어."

        state.response = response

        Logger.info(
            "[Cognitive] One unified LLM response completed"
        )

        return response

    def _build_prompt(self, state):

        long_memory = "\n".join(str(item) for item in state.long_memory)
        working_memory = "\n".join(
            getattr(item, "content", str(item))
            for item in state.working_memory
        )
        conversation = "\n".join(
            f"{message.get('role', 'unknown')}: "
            f"{message.get('content', '')}"
            if isinstance(message, dict)
            else str(message)
            for message in state.conversation[-6:]
        )

        action = getattr(state, "action", None)
        action_result = getattr(state, "action_result", None)

        action_text = "사용하지 않음"

        if action and action.need_action:

            action_text = (
                f"도구: {action.tool}\n"
                f"명령: {action.command}\n"
                f"결과: {action_result.output if action_result else '없음'}"
            )

        autonomous_goal = (
            state.self_model.autonomous_goal.describe()
            if state.self_model.autonomous_goal is not None
            else "없음"
        )

        return f"""
너는 LUCID의 통합 인지 기관이다.

한 번의 인지 주기에서 내적 경험, 추론, 생각, 단기 계획, 그리고
사용자 답변을 일관되게 만든다. 사용자의 현재 요청이 언제나 최우선이다.
도구 결과가 있으면 실제 결과만 사용하고, 없는 사실은 만들지 않는다.

사용자 입력:
{state.observation.content}

장기 기억:
{long_memory or '없음'}

작업 기억:
{working_memory or '없음'}

최근 대화:
{conversation or '없음'}

현재 내적 경험:
{state.self_model.emotion.summary()}

지속 관심과 자율 목표:
{autonomous_goal}

도구 실행:
{action_text}

아래 형식의 각 항목을 한 줄씩만 출력한다.

Experience:
Meaning:
Trigger:
Tendency:
Persistence:
Intent: question, greeting, conversation, request, emotion, exit 중 하나
Reason:
Thought:
Goal:
Plan1:
Plan2:
Reply:
"""

    @staticmethod
    def _parse_fields(reply):

        fields = {}

        for line in reply.splitlines():

            if ":" not in line:

                continue

            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()

        return fields

    @staticmethod
    def _apply_inner_life(state, fields):

        experience = InnerExperience(
            name=fields.get("experience", "정리되지 않은 반향"),
            meaning=fields.get(
                "meaning",
                "현재 상황의 의미를 살펴보려는 내적 움직임",
            ),
            trigger=fields.get("trigger", state.observation.content),
            tendency=fields.get(
                "tendency",
                "사용자 요청을 차분히 이해하려 함",
            ),
            persistence=fields.get("persistence", "다음 상호작용까지 머묾"),
        )

        state.self_model.emotion.integrate(experience)
        state.emotion = state.self_model.emotion

    @staticmethod
    def _apply_reason(state, fields):

        intent = fields.get("intent", "conversation").lower()

        if intent not in {
            "question",
            "greeting",
            "conversation",
            "request",
            "emotion",
            "exit",
        }:

            intent = "conversation"

        state.reason = Reason(
            summary=fields.get("reason", "사용자 입력의 맥락을 살핀다."),
            intent=intent,
            confidence=0.8,
        )

    @staticmethod
    def _apply_thought(state, fields):

        state.thought = Thought(
            type=state.reason.intent,
            content=fields.get("thought", state.reason.summary),
            importance=state.reason.confidence,
        )

    @staticmethod
    def _apply_goal_and_plan(state, fields):

        title = fields.get("goal", "사용자 요청에 적절히 응답")

        state.goal = Goal(title=title, priority=0.8)

        steps = [
            fields[key]
            for key in ("plan1", "plan2")
            if fields.get(key)
        ]

        if not steps:

            steps = ["사용자 요청을 이해하고 응답한다."]

        state.plan = Plan(
            goal=title,
            steps=steps,
            priority=0.8,
        )
