"""여러 인지 단계에서 얻은 정보를 모아 언어 응답을 생성한다."""

from lucid.language.ollama import OllamaModule
from lucid.language.prompts import format_history, format_memory
from lucid.log import Logger


class LanguageEngine(OllamaModule):
    """여러 인지 단계에서 얻은 정보를 모아 언어 응답을 생성한다."""

    def process(self, state):
        """관찰, 기억, 행동 결과를 바탕으로 응답 문자열을 반환한다."""
        Logger.info("[Language] Generating Response")

        long_memory = format_memory(state.long_memory)
        working_memory = format_memory(state.working_memory)
        history = format_history(state.conversation, 8)
        inner_life = state.self_model.emotion.summary()

        autonomous_goal = (
            state.self_model.autonomous_goal.describe()
            if state.self_model.autonomous_goal is not None
            else "없음"
        )

        result = getattr(state, "action_result", None)
        action_result = "없음"
        if result is not None:
            action_result = (
                (result.output or "없음")
                if result.success
                else f"Action 실행 실패: {result.output}"
            )
        action_info = "사용하지 않음"
        action = getattr(getattr(state, "decision", None), "action_object", None)
        if action and action.need_action:
            action_info = f"Tool: {action.tool}\nCommand: {action.command}"

        reason_intent = getattr(state.reason, "intent", "unknown")
        reason_summary = getattr(state.reason, "summary", "")
        thought_content = getattr(state.thought, "content", "")
        goal_title = getattr(state.goal, "title", "")
        plan_text = (
            "\n".join(f"- {step}" for step in getattr(state.plan, "steps", []))
            or "없음"
        )

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
지속 관심과 자율 목표
========================================

{autonomous_goal}

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

15. 자율 목표는 내부 배경으로만 사용한다. 사용자의 현재 요청보다
    우선하지 않으며, 사용자가 묻지 않았는데도 목표를 강요하거나
    외부 행동을 했다고 말하지 않는다.
"""

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

        try:
            reply = self.client.generate(messages)

        except Exception as e:
            Logger.error(f"Language Error : {e}")

            reply = "미안해. 지금은 응답을 생성하지 못했어."

        if not reply:
            reply = "미안해. 응답을 생성하지 못했어."

        Logger.info("[Language] Complete")
        return reply.strip()
