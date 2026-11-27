"""모델로 내적 경험을 생성하기 위한 프롬프트와 엔진."""

from lucid.emotion.model import EmotionState, InnerExperience
from lucid.language.ollama import OllamaModule
from lucid.log import Logger


class EmotionPrompt:
    def build(self, state) -> str:
        """상태에서 관찰·기억을 읽어 내적 경험 생성 프롬프트를 반환한다."""

        memory = "\n".join(state.long_memory) if state.long_memory else "없음"

        conversation = "".join(
            f"{message['role']} : {message['content']}\n"
            for message in getattr(state, "conversation", [])[-6:]
        )

        inner_life = state.self_model.emotion

        previous_experiences = "\n".join(
            experience.describe() for experience in inner_life.recent()
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


class EmotionEngine(OllamaModule):
    """상태에서 모델 응답을 받아 캐릭터의 감정 이력에 반영한다."""

    def __init__(self) -> None:
        """내적 경험을 생성할 모델 클라이언트와 프롬프트를 준비한다."""

        super().__init__()
        self.prompt = EmotionPrompt()

    def process(self, state) -> EmotionState:
        """대화 상태에서 내적 경험을 생성·반영하고 갱신된 감정 상태를 반환한다."""

        messages = [
            {
                "role": "system",
                "content": self.prompt.build(state),
            }
        ]

        inner_life = state.self_model.emotion

        try:
            reply = self.client.generate(messages)

            Logger.info(f"[Emotion LLM]\n{reply}")

            fields = {}

            for line in reply.splitlines():
                line = line.strip()

                if ":" not in line:
                    continue

                key, value = line.split(":", 1)
                fields[key.strip().lower()] = value.strip()

            experience = InnerExperience(
                name=fields.get("experience", "정리되지 않은 반향"),
                meaning=fields.get(
                    "meaning",
                    "현재 상황의 의미를 더 살펴보려는 내적 움직임",
                ),
                trigger=fields.get("trigger", state.observation.content),
                tendency=fields.get(
                    "tendency",
                    "상황을 이해하기 위해 차분히 관찰함",
                ),
                persistence=fields.get("persistence", "잠시 머묾"),
            )

            inner_life.integrate(experience)

        except Exception as e:
            Logger.error(f"Emotion Error : {e}")

        state.self_model.emotion = inner_life

        Logger.info(f"[Inner Life] {inner_life.summary()}")

        return inner_life
