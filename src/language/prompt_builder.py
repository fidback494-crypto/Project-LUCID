"""
Project LUCID

Artificial Mind Project

Module : Prompt Builder

Creator : 시드
"""


class PromptBuilder:

    def build(self, state):

        # ----------------------------------
        # Long Memory
        # ----------------------------------

        memory_text = (
            "\n".join(state.long_memory)
            if state.long_memory
            else "없음"
        )

        # ----------------------------------
        # Working Memory
        # ----------------------------------

        working_text = (
            "\n".join(str(x) for x in state.working_memory)
            if state.working_memory
            else "없음"
        )

        # ----------------------------------
        # System Prompt
        # ----------------------------------

        system_prompt = f"""
너는 {state.self_model.identity.name}이다.

Creator : {state.self_model.identity.creator}
Version : {state.self_model.identity.version}

========================
사용자에 대해 알고 있는 사실
========================

{memory_text}

위 내용은 사실이다.

기억과 모순되는 답을 하지 않는다.

========================
최근 작업 기억
========================

{working_text}

========================
응답 규칙
========================

- 항상 한국어만 사용한다.
- 자연스럽게 반말을 사용한다.
- 기억을 적극 활용한다.
- 사실을 지어내지 않는다.
- 모르면 모른다고 말한다.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        # ----------------------------------
        # Conversation History
        # ----------------------------------

        if hasattr(state, "conversation"):

            messages.extend(state.conversation)

        # ----------------------------------
        # Current User Input
        # ----------------------------------

        messages.append(
            {
                "role": "user",
                "content": state.observation.content,
            }
        )

        return messages