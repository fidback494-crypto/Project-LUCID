"""기억과 대화 기록으로 모델에 전달할 메시지를 만든다."""


def format_history(messages, limit):
    """최근 limit개 메시지의 역할과 내용을 여러 줄의 대화 기록으로 반환한다."""
    lines = []
    for message in messages[-limit:] if limit > 0 else ():
        if isinstance(message, dict) and "role" in message and "content" in message:
            lines.append(f"{message['role']} : {message['content']}")
        else:
            lines.append(str(message))
    return "\n".join(lines) or "없음"


def format_memory(items, *, content_only=False):
    """기억 목록을 줄 단위로 합치며, 요청 시 객체의 content 속성을 우선한다."""
    values = (
        getattr(item, "content", item) if content_only else item for item in items
    )
    return "\n".join(str(value) for value in values) or "없음"


class PromptBuilder:
    """기억과 대화 기록으로 모델에 전달할 메시지를 만든다."""

    def build(self, state):
        """장기·작업 기억을 시스템 지시로 구성하고 이전 대화와 현재 발화를 역할별로 반환한다."""
        memory_text = format_memory(state.long_memory)
        working_text = format_memory(state.working_memory)

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

        if hasattr(state, "conversation"):
            messages.extend(state.conversation)

        messages.append(
            {
                "role": "user",
                "content": state.observation.content,
            }
        )
        return messages
