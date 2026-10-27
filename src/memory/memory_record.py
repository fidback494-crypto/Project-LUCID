"""
Project LUCID

Artificial Mind Project

Module : Memory Record

Creator : 시드
"""

from dataclasses import dataclass
import re
import unicodedata


@dataclass
class MemoryRecord:

    category: str

    content: str

    importance: float

    timestamp: str = ""

    subject: str = "user"

    predicate: str = ""

    value: str = ""

    confidence: float = 0.8

    source: str = "user_explicit"

    def __post_init__(self):
        if not self.predicate:
            self.predicate = "fact" if self.category == "user" else self.category

        if not self.value:
            self.value = self.content

        self.importance = min(1.0, max(0.0, float(self.importance)))
        self.confidence = min(1.0, max(0.0, float(self.confidence)))


def normalize_memory_value(value):
    """Normalize value text for reliable deduplication and memory keys."""

    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return " ".join(normalized.split()).strip(" .,!?:;。！？、")


def memory_key(subject, predicate, value):
    """Build a stable identity for a fact; singular facts share one key."""

    subject = normalize_memory_value(subject)
    predicate = normalize_memory_value(predicate)

    if predicate in {"name", "age", "birth_date", "location"}:
        return f"{subject}:{predicate}"

    return f"{subject}:{predicate}:{normalize_memory_value(value)}"


def infer_legacy_memory(category, content):
    """Map old category/content memories into the normalized schema."""

    text = str(content or "").strip()
    name_prefix = "사용자의 이름은 "

    if text.startswith(name_prefix):
        value = text[len(name_prefix):].strip()
        value = re.sub(r"[.!?。！？]+$", "", value).strip()
        value = re.sub(r"(?:이야|야|이에요|예요|입니다)$", "", value).strip()
        return "user", "name", value

    if category == "preference":
        match = re.search(
            r"(?:사용자는\s*)?(?:(?:나는|난|저는|전)\s*)?"
            r"(.+?)(?:을|를)\s*좋아해요?[.!?。！？]*$",
            text,
        )

        if match:
            return "user", "likes", match.group(1).strip()

        return "user", "preference", text

    return "user", "fact", text
