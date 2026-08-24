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

        emotion = state.self_model.emotion

        try:

            reply = self.client.generate(messages)

            Logger.info(f"[Emotion LLM]\n{reply}")

            for line in reply.splitlines():

                line = line.strip()

                if ":" not in line:
                    continue

                key, value = line.split(":", 1)

                key = key.strip().lower()

                value = value.strip()

                if key == "joy":

                    emotion.joy = float(value)

                elif key == "curiosity":

                    emotion.curiosity = float(value)

                elif key == "confidence":

                    emotion.confidence = float(value)

                elif key == "sadness":

                    emotion.sadness = float(value)

                elif key == "anger":

                    emotion.anger = float(value)

                elif key == "fear":

                    emotion.fear = float(value)

                elif key == "fatigue":

                    emotion.fatigue = float(value)

                elif key == "reason":

                    Logger.info(f"[Emotion Reason] {value}")

        except Exception as e:

            Logger.error(f"Emotion Error : {e}")

        state.self_model.emotion = emotion

        Logger.info(
            "[Emotion] "
            f"Joy={emotion.joy:.2f} "
            f"Curiosity={emotion.curiosity:.2f} "
            f"Confidence={emotion.confidence:.2f}"
        )

        return emotion