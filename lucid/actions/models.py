"""도구로 전달할 명령과 도구의 실행 결과를 정의한다."""

from dataclasses import dataclass


@dataclass
class Action:
    """도구 이름, 명령과 실행 필요 여부를 담는다."""

    tool: str = "none"
    command: str = ""
    need_action: bool = False


@dataclass
class ActionResult:
    """실행 성공 여부와 사용자 또는 모델에게 전달할 내용을 담는다."""

    success: bool
    output: str
