"""
Project LUCID

Artificial Mind Project

Module : Experience

Creator : 시드
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Experience:

    event: str

    result: str

    confidence: float

    timestamp: str = datetime.now().isoformat()