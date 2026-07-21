"""
Project LUCID

Artificial Mind Project

Module : BaseModule

Creator : 시드
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseModule(ABC):
    """
    LUCID의 모든 기관(Organ)이 상속받는 기본 클래스
    """

    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    @abstractmethod
    def start(self):
        """기관 시작"""
        pass

    @abstractmethod
    def update(self):
        """매 Heartbeat마다 호출"""
        pass

    @abstractmethod
    def stop(self):
        """기관 종료"""
        pass