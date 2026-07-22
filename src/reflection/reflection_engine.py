"""
Project LUCID

Artificial Mind Project

Module : Reflection Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .reflection import Reflection


class ReflectionEngine(BaseModule):

    def __init__(self):
        super().__init__("ReflectionEngine")

    def start(self):
        Logger.info("Reflection Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Reflection Engine Stopped")

    def process(self, context):

        reflection = Reflection(
            success=True,
            summary="응답을 완료했다.",
            confidence=1.0,
        )

        Logger.info(
            f"[Reflection] {reflection.summary}"
        )

        return reflection