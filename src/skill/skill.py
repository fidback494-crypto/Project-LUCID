


from dataclasses import dataclass


@dataclass
class Skill:

    name: str

    description: str

    trigger: list[str]

    procedure: list[str]

    success_rate: float = 1.0