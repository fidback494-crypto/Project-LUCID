"""
Project LUCID

Artificial Mind Project

Module : Reasoning Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .reason import Reason


class ReasoningEngine(BaseModule):

    def __init__(self):
        super().__init__("ReasoningEngine")

    def start(self):
        Logger.info("Reasoning Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Reasoning Engine Stopped")

    def process(self, observation):

        text = observation.content.strip().lower()

        # 인사
        if any(word in text for word in ["안녕", "ㅎㅇ", "hello", "hi"]):
            reason = Reason(
                summary="사용자가 인사했다.",
                intent="greeting",
                confidence=0.98,
            )

        # 질문
        elif "?" in text or text.endswith("까") or text.endswith("요"):
            reason = Reason(
                summary="사용자가 정보를 요청했다.",
                intent="question",
                confidence=0.90,
            )

        # 종료
        elif text in ["exit", "quit"]:
            reason = Reason(
                summary="사용자가 종료를 원한다.",
                intent="exit",
                confidence=1.0,
            )

        # 기본
        else:
            reason = Reason(
                summary=f"사용자가 '{observation.content}'라고 말했다.",
                intent="conversation",
                confidence=0.75,
            )

        Logger.info(
            f"[Reason] {reason.intent} ({reason.confidence:.2f})"
        )

        return reason