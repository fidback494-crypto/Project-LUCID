"""
Project LUCID

Artificial Mind Project

Module : Emotion Prompt

Creator : 시드
"""


class EmotionPrompt:

    def build(self, state):

        memory = (
            "\n".join(state.long_memory)
            if state.long_memory
            else "없음"
        )

        conversation = ""

        if hasattr(state, "conversation"):

            for msg in state.conversation[-6:]:

                conversation += (
                    f"{msg['role']} : {msg['content']}\n"
                )

        return f"""
너는 LUCID의 Emotion Engine이다.

역할

사용자의 입력,
최근 대화,
장기 기억을 참고하여
현재 AI 내부 감정을 계산한다.

==========
사용자 입력
==========

{state.observation.content}

==========
장기 기억
==========

{memory}

==========
최근 대화
==========

{conversation}

출력 형식

Joy:
Curiosity:
Confidence:
Sadness:
Anger:
Fear:
Fatigue:
Reason:

숫자는 반드시

0.0

~

1.0

사이만 사용한다.

다른 설명은 절대 하지 않는다.
"""