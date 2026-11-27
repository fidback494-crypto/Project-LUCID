"""추론에 필요한 관찰과 기억을 시스템 프롬프트로 구성한다."""

from lucid.language.prompts import format_history, format_memory


class ReasoningPrompt:
    """추론에 필요한 관찰과 기억을 시스템 프롬프트로 구성한다."""

    def build(self, state):
        """관찰 내용과 최근 대화, 기억을 사용해 의도 분류용 시스템 지시를 만든다."""
        observation = state.observation.content if state.observation else ""
        working_memory = format_memory(state.working_memory, content_only=True)
        memory = format_memory(state.long_memory)
        history = format_history(state.conversation, 6)
        inner_life = state.self_model.emotion.summary()

        autonomous_goal = (
            state.self_model.autonomous_goal.describe()
            if state.self_model.autonomous_goal is not None
            else "없음"
        )

        return f"""
너는 LUCID의 Reasoning Engine이다.

목표

사용자의 진짜 의도를 분석한다.

단순히 질문인지 판단하지 말고

감정

맥락

기억

최근 대화

현재 감정을 모두 고려하여 판단한다.

====================================

사용자 입력

{observation}

====================================

최근 대화

{history}

====================================

Working Memory

{working_memory}

====================================

Long Memory

{memory}

====================================

현재 내적 경험

{inner_life}

====================================

지속 관심과 자율 목표

{autonomous_goal}

이 목표는 배경 맥락일 뿐이며 사용자의 현재 요청보다 우선하지 않는다.

====================================

반드시 아래 형식만 출력한다.

Category:

Reason:

Confidence:
"""
