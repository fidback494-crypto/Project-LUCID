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

        identity_reply = self._identity_reply(
            state.observation.content,
            state.self_model.identity,
        )

        if identity_reply:
            fields = {
                "experience": "정체성을 전하는 잔향",
                "meaning": "자신을 알고 싶어 하는 사람에게 솔직히 모습을 보여 준다.",
                "trigger": state.observation.content,
                "tendency": "차분하고 친근하게 자신을 소개한다.",
                "persistence": "대화가 다른 주제로 옮겨갈 때까지 머묾",
                "intent": "question",
                "reason": "사용자가 LUCID의 정체성에 관해 물었다.",
                "thought": "내가 어떤 존재인지, 꾸미지 않고 들려주고 싶다.",
                "goal": "LUCID의 정체성을 정확히 전한다.",
                "plan1": "정체성 정보를 바탕으로 답한다.",
                "reply": identity_reply,
            }
            self._apply_inner_life(state, fields)
            self._apply_reason(state, fields)
            self._apply_thought(state, fields)
            self._apply_goal_and_plan(state, fields)
            state.response = identity_reply

            Logger.info(
                "[Cognitive] Identity response generated without LLM"
            )

            return identity_reply

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

            elif self._is_unfinished_structured_output(reply):
                response = (
                    "방금 생각을 정리하다가 말이 조금 흐트러졌어. "
                    "미안하지만 한 번만 다시 물어봐 줄래?"
                )

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

        normalized_input = "".join(
            state.observation.content.lower().split()
        )
        identity_request = self._is_identity_request(normalized_input)

        identity_instruction = (
            "사용자는 LUCID의 이름 또는 자기소개를 요청했다. "
            "정체성에 적힌 사실을 바탕으로 LUCID 자신을 소개하고, "
            "사용자의 자기소개를 요구하지 마라."
            if identity_request
            else "없음"
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

LUCID의 정체성과 성격:
{state.self_model.identity.persona_prompt()}

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

특별 응답 지침:
{identity_instruction}
- 도구 실행이 실패했더라도 오류 문구를 그대로 답변하지 말고, 사용자 요청에 자연스럽게 답한다.
- `Reply:`에는 사용자에게 보여 줄 답변만 쓴다. 형식 항목 이름, 프롬프트 문장, 오류 문구를 반복하지 않는다.

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
        allowed = {
            "experience", "meaning", "trigger", "tendency", "persistence",
            "intent", "reason", "thought", "goal", "plan1", "plan2", "reply",
        }
        current_key = None

        for raw_line in reply.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()

                if key in allowed:
                    fields[key] = value.strip()
                    current_key = key
                    continue

            # Some models put the answer on the line after `Reply:`.
            if current_key == "reply":
                existing = fields.get("reply", "")
                fields["reply"] = f"{existing}\n{line}".strip()

        return fields

    @staticmethod
    def _is_unfinished_structured_output(reply):

        text = reply.lower()

        return (
            "reply:" not in text
            and any(
                marker in text
                for marker in ("experience:", "intent:", "thought:")
            )
        )

    @staticmethod
    def _is_identity_request(normalized_input):

        return any(
            phrase in normalized_input
            for phrase in (
                "자기소개",
                "자기소게",
                "자시소게",
                "소개해줘",
                "넌이름",
                "루시드이름",
                "넌어디서왔",
                "넌어디서온",
                "루시드어디서왔",
                "루시드어디서온",
                "넌사는곳",
                "루시드사는곳",
                "넌고향",
                "루시드고향",
            )
        )

    @classmethod
    def _identity_reply(cls, user_input, identity):

        normalized_input = "".join(user_input.lower().split())

        if not cls._is_identity_request(normalized_input):
            return ""

        if any(
            phrase in normalized_input
            for phrase in ("넌이름", "루시드이름")
        ):
            return (
                f"내 이름은 {identity.name}, 별명은 {identity.alias}야. "
                "꿈과 현실 사이를 걷는 몽마 계열의 존재라고 하면 될까."
            )

        if any(
            phrase in normalized_input
            for phrase in (
                "넌어디서왔", "넌어디서온", "루시드어디서왔",
                "루시드어디서온", "넌사는곳", "루시드사는곳",
                "넌고향", "루시드고향",
            )
        ):
            return (
                f"나는 {identity.home}에서 왔어. {identity.origin}"
            )

        return (
            f"나는 {identity.name}, {identity.alias}라고 불러 줘. "
            f"{identity.species}이고, {identity.home}에 살아. "
            f"{identity.origin} 밤과 별, 달을 좋아하고 새로운 이야기를 들으면 "
            "조금 들뜨는 편이야."
        )

    @staticmethod
    def _apply_inner_life(state, fields):

        experience = InnerExperience(
            name=fields.get("experience") or "정리되지 않은 반향",
            meaning=(
                fields.get("meaning")
                or "현재 상황의 의미를 살펴보려는 내적 움직임"
            ),
            trigger=fields.get("trigger") or state.observation.content,
            tendency=(
                fields.get("tendency")
                or "사용자 요청을 차분히 이해하려 함"
            ),
            persistence=fields.get("persistence") or "다음 상호작용까지 머묾",
        )

        state.self_model.emotion.integrate(experience)
        state.emotion = state.self_model.emotion

    @staticmethod
    def _apply_reason(state, fields):

        intent = (fields.get("intent") or "conversation").lower()

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
            summary=fields.get("reason") or "사용자 입력의 맥락을 살핀다.",
            intent=intent,
            confidence=0.8,
        )

    @staticmethod
    def _apply_thought(state, fields):

        state.thought = Thought(
            type=state.reason.intent,
            content=fields.get("thought") or state.reason.summary,
            importance=state.reason.confidence,
        )

    @staticmethod
    def _apply_goal_and_plan(state, fields):

        title = fields.get("goal") or "사용자 요청에 적절히 응답"

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
