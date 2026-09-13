"""
Project LUCID

Artificial Mind Project

Module : Reasoning Prompt

Creator : 시드
"""


class ReasoningPrompt:

    def build(self, state):

        # ---------------------------------
        # Observation
        # ---------------------------------

        observation = ""

        if state.observation:

            observation = state.observation.content

        # ---------------------------------
        # Working Memory
        # ---------------------------------

        working = []

        for item in state.working_memory:

            try:
                working.append(item.content)
            except AttributeError:
                working.append(str(item))

        working_memory = "\n".join(working)

        if not working_memory:

            working_memory = "없음"

        # ---------------------------------
        # Long Memory
        # ---------------------------------

        long_memory = []

        for item in state.long_memory:

            long_memory.append(str(item))

        memory = "\n".join(long_memory)

        if not memory:

            memory = "없음"

        # ---------------------------------
        # Conversation
        # ---------------------------------

        conversation = []

        for msg in state.conversation[-6:]:

            try:
                conversation.append(
                    f"{msg['role']} : {msg['content']}"
                )
            except Exception:
                conversation.append(str(msg))

        history = "\n".join(conversation)

        if not history:

            history = "없음"

        # ---------------------------------
        # Inner life
        # ---------------------------------

        inner_life = state.self_model.emotion.summary()

        autonomous_goal = (
            state.self_model.autonomous_goal.describe()
            if state.self_model.autonomous_goal is not None
            else "없음"
        )

        # ---------------------------------
        # Prompt
        # ---------------------------------

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
