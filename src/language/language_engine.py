"""
Project LUCID

Artificial Mind Project

Module : Language Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .ollama_client import OllamaClient


class LanguageEngine(BaseModule):

    def __init__(self):

        super().__init__("LanguageEngine")

        self.client = OllamaClient()

    # =================================================
    # Start
    # =================================================

    def start(self):

        Logger.info("Language Engine Started")

    # =================================================
    # Update
    # =================================================

    def update(self):

        pass

    # =================================================
    # Stop
    # =================================================

    def stop(self):

        Logger.info("Language Engine Stopped")

    # =================================================
    # Process
    # =================================================

    def process(self, state):

        Logger.info("[Language] Generating Response")

        # =================================================
        # Long Memory
        # =================================================

        long_memory = "\n".join(
            str(x)
            for x in state.long_memory
        )

        if not long_memory:

            long_memory = "없음"

        # =================================================
        # Working Memory
        # =================================================

        working_memory = "\n".join(
            str(x)
            for x in state.working_memory
        )

        if not working_memory:

            working_memory = "없음"

        # =================================================
        # Conversation
        # =================================================

        history = []

        for msg in state.conversation[-8:]:

            try:

                history.append(
                    f"{msg['role']} : {msg['content']}"
                )

            except Exception:

                history.append(str(msg))

        history = "\n".join(history)

        if not history:

            history = "없음"

        # =================================================
        # Inner life
        # =================================================

        inner_life = state.self_model.emotion.summary()

        # =================================================
        # Action Result
        # =================================================

        action_result = ""

        if hasattr(state, "action_result"):

            result = state.action_result

            if result is not None:

                if result.success:

                    action_result = result.output

                else:

                    action_result = (
                        f"Action 실행 실패: {result.output}"
                    )

        if not action_result:

            action_result = "없음"

        # =================================================
        # Tool 사용 여부
        # =================================================

        action_info = "사용하지 않음"

        if (
            hasattr(state, "decision")
            and state.decision is not None
        ):

            action_object = getattr(
                state.decision,
                "action_object",
                None,
            )

            if action_object is not None:

                if action_object.need_action:

                    action_info = (
                        f"Tool: {action_object.tool}\n"
                        f"Command: {action_object.command}"
                    )

        # =================================================
        # Reason
        # =================================================

        reason_intent = "unknown"
        reason_summary = ""

        if state.reason is not None:

            reason_intent = getattr(
                state.reason,
                "intent",
                "unknown",
            )

            reason_summary = getattr(
                state.reason,
                "summary",
                "",
            )

        # =================================================
        # Thought
        # =================================================

        thought_content = ""

        if state.thought is not None:

            thought_content = getattr(
                state.thought,
                "content",
                "",
            )

        # =================================================
        # Goal
        # =================================================

        goal_title = ""

        if state.goal is not None:

            goal_title = getattr(
                state.goal,
                "title",
                "",
            )

        # =================================================
        # Plan
        # =================================================

        plan_steps = []

        if state.plan is not None:

            plan_steps = getattr(
                state.plan,
                "steps",
                [],
            )

        plan_text = "\n".join(
            f"- {step}"
            for step in plan_steps
        )

        if not plan_text:

            plan_text = "없음"

        # =================================================
        # System Prompt
        # =================================================

        system_prompt = f"""
너는 {state.self_model.identity.name}이다.

Creator:
{state.self_model.identity.creator}

Version:
{state.self_model.identity.version}

========================================
현재 내적 경험
========================================

{inner_life}

========================================
현재 사용자 입력
========================================

{state.observation.content}

========================================
현재 추론
========================================

Intent:
{reason_intent}

Reason:
{reason_summary}

========================================
현재 생각
========================================

{thought_content}

========================================
현재 목표
========================================

{goal_title}

========================================
현재 계획
========================================

{plan_text}

========================================
Action
========================================

{action_info}

========================================
Action 결과
========================================

{action_result}

========================================
장기 기억
========================================

{long_memory}

========================================
작업 기억
========================================

{working_memory}

========================================
최근 대화
========================================

{history}

========================================
응답 규칙
========================================

1. 항상 한국어로 답한다.

2. 사용자의 현재 입력에 직접 답한다.

3. Action 결과가 존재하면 반드시 Action 결과를 우선적으로 활용한다.

4. 사용자가 "기억 보여줘", "내 기억 보여줘",
   "뭘 기억하고 있어?" 등의 요청을 하면
   Action 결과에 있는 실제 기억을 보여준다.

5. 기억에 없는 내용을 만들어내지 않는다.

6. 기억의 내용을 임의로 수정하지 않는다.

7. 기억을 보여줄 때는 내부 Python 튜플 형식을
   그대로 사용자에게 출력하지 말고 자연스러운 문장으로 정리한다.

8. 예를 들어 기억이

   ('user', '사용자의 이름은 시드야', 0.95, ...)

   라면

   "사용자의 이름은 시드야."

   처럼 자연스럽게 표현한다.

9. 같은 기억이 여러 번 있으면 중복해서 반복하지 않는다.

10. Action 결과가 비어 있으면 일반적인 대화를 생성한다.

11. 생각(Thought)의 내부 과정을 그대로 노출하지 않는다.

12. 거짓 기억을 만들지 않는다.

13. 모르는 것은 모른다고 말한다.

14. 짧고 자연스럽게 답한다.
"""

        # =================================================
        # Messages
        # =================================================

        messages = [

            {
                "role": "system",
                "content": system_prompt,
            },

            {
                "role": "user",
                "content": state.observation.content,
            },

        ]

        # =================================================
        # Generate
        # =================================================

        try:

            reply = self.client.generate(
                messages
            )

        except Exception as e:

            Logger.error(
                f"Language Error : {e}"
            )

            reply = (
                "미안해. 지금은 응답을 "
                "생성하지 못했어."
            )

        # =================================================
        # Empty Response
        # =================================================

        if not reply:

            reply = (
                "미안해. 응답을 생성하지 못했어."
            )

        Logger.info(
            "[Language] Complete"
        )

        return reply.strip()
