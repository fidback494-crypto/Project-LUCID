"""
Project LUCID

Artificial Mind Project

Module : Emotion Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from src.language.ollama_client import OllamaClient

from .emotion_prompt import EmotionPrompt
from .emotion_state import EmotionState
from .inner_experience import InnerExperience


class EmotionEngine(BaseModule):

    def __init__(self):

        super().__init__("EmotionEngine")

        self.client = OllamaClient()
        self.prompt = EmotionPrompt()

    def start(self):

        Logger.info("Emotion Engine Started")

    def update(self):
        pass

    def stop(self):

        Logger.info("Emotion Engine Stopped")

    def process(self, state):

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

        Logger.info(
            "[Inner Life] "
            f"{inner_life.summary()}"
        )

        return inner_life
