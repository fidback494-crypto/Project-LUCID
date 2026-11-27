from dataclasses import dataclass


@dataclass
class Skill:
    """기술의 이름, 설명, 실행 조건·절차 및 성공률."""

    name: str

    description: str

    trigger: list[str]

    procedure: list[str]

    success_rate: float = 1.0
