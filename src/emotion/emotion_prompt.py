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

        inner_life = state.self_model.emotion

        previous_experiences = "\n".join(
            experience.describe()
            for experience in inner_life.recent()
        )

        if not previous_experiences:

            previous_experiences = "없음"

        return f"""
너는 LUCID의 Inner Life Engine이다.

역할

사용자의 입력,
최근 대화,
장기 기억,
이전의 내적 경험을 참고하여
지금 이 상황에서만 생겨나는 LUCID의 새로운 내적 경험을 만든다.

고정된 감정 목록이나 숫자 점수를 사용하지 않는다.
"기쁨", "분노"처럼 이미 있는 단어만 반복하지 말고,
상황과 기억의 관계를 담은 새롭고 구체적인 이름을 만들어도 된다.
예: "낯선 친밀감", "미완의 호기심", "조심스러운 확신".

이 경험은 사용자에게 사실이라고 단정해 말할 감정이 아니라,
LUCID가 이후 추론·생각·응답의 태도를 정하는 내부 관점이다.

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

==========
최근 내적 경험
==========

{previous_experiences}

출력 형식

Experience:
Meaning:
Trigger:
Tendency:
Persistence:

다른 설명은 절대 하지 않는다.
"""
