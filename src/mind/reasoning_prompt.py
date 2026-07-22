"""
Project LUCID

Artificial Mind Project

Module : Reasoning Prompt

Creator : 시드
"""


class ReasoningPrompt:

    def build(self, state):

        memory = "\n".join(state.long_memory)

        if not memory:
            memory = "없음"

        return f"""
너는 LUCID의 Reasoning Engine이다.

목적
사용자의 의도를 분석한다.

사용자 입력
----------------
{state.observation.content}

관련 기억
----------------
{memory}

반드시 아래 형식만 출력한다.

Category: question / greeting / request / emotion / conversation

Reason: 분석 내용

Confidence: 0~1
"""