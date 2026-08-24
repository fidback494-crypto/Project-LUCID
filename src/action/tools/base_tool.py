"""
Project LUCID

Artificial Mind Project

Module : Base Tool

Creator : 시드
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool 이름
        """
        pass

    @abstractmethod
    def execute(self, command: str):
        """
        Tool 실행
        """
        pass