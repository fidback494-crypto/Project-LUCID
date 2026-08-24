from dataclasses import dataclass


@dataclass
class ActionResult:

    success: bool

    output: str