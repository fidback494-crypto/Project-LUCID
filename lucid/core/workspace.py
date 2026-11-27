"""대화 턴의 작업 상태와 커널에서 사용하는 접근 인터페이스."""

from dataclasses import dataclass

from lucid.core.kernel import BaseModule
from lucid.core.state import BrainState


@dataclass
class Workspace(BrainState):
    """엔진들 사이에서 공유하는 현재 턴의 작업 상태."""

    response: str | None = None
    voice_response: str | None = None
    context: object | None = None

    def clear(self) -> None:
        """자기 모델은 유지하고 대화·기억 목록과 이전 턴의 결과를 비운다."""
        self.conversation.clear()
        self.working_memory.clear()
        self.long_memory.clear()
        self.__init__(
            self_model=self.self_model,
            conversation=self.conversation,
            working_memory=self.working_memory,
            long_memory=self.long_memory,
        )

    def summary(self) -> dict:
        """현재 관찰에서 결정까지의 주요 값을 표시용 사전으로 반환한다."""
        return {
            "observation": self.observation,
            "reason": self.reason,
            "thought": self.thought,
            "goal": self.goal,
            "plan": self.plan,
            "decision": self.decision,
        }


class WorkspaceManager:
    """커널 밖에서도 사용할 수 있는 작업 공간의 소유자."""

    def __init__(self) -> None:
        """첫 턴의 작업 공간을 만든다."""
        self._workspace = Workspace()

    def current(self) -> Workspace:
        """현재 쓰고 있는 작업 공간을 반환한다."""
        return self._workspace

    def reset(self) -> None:
        """현재 작업 공간을 다음 턴에 사용할 수 있도록 비운다."""
        self._workspace.clear()

    def replace(self, workspace: Workspace) -> None:
        """전달받은 workspace를 이후 사용할 작업 공간으로 지정한다."""
        self._workspace = workspace


class WorkspaceEngine(BaseModule):
    """커널 수명 주기를 따르는 작업 공간 접근점."""

    def __init__(self) -> None:
        """커널에 등록할 이름과 작업 공간 관리자를 준비한다."""
        super().__init__()
        self.manager = WorkspaceManager()

    def current(self) -> Workspace:
        """현재 턴에 공유하는 작업 공간을 반환한다."""
        return self.manager.current()

    def reset(self) -> None:
        """현재 턴의 작업 영역을 초기화한다."""
        self.manager.reset()
