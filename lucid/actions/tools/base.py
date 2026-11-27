"""행동 엔진에 등록하는 도구의 인터페이스."""

from abc import ABC, abstractmethod

from lucid.actions.models import ActionResult


class BaseTool(ABC):
    """레지스트리가 조회할 이름과 명령 실행 진입점을 정의한다."""

    @property
    @abstractmethod
    def name(self) -> str:
        """행동 결정에 사용하는 도구 식별자를 반환한다."""

    @abstractmethod
    def execute(self, command: str) -> ActionResult:
        """사용자 명령을 해석하고 실행 성공 여부와 표시할 결과를 반환한다."""
