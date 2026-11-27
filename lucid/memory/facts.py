"""사용자 사실을 표현하고 대화나 이전 스키마에서 사실을 추출한다."""

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class MemoryRecord:
    """출처와 신뢰도를 함께 기록한 사용자 사실 한 건."""

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
        """누락된 관계·값을 채우고 중요도와 신뢰도를 0~1로 제한한다."""
        if not self.predicate:
            self.predicate = "fact" if self.category == "user" else self.category

        if not self.value:
            self.value = self.content

        self.importance = min(1.0, max(0.0, float(self.importance)))
        self.confidence = min(1.0, max(0.0, float(self.confidence)))


def normalize_memory_value(value):
    """문자열의 유니코드·대소문자·공백을 정규화한 비교용 값을 반환한다."""
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return " ".join(normalized.split()).strip(" .,!?:;。！？、")


def memory_key(subject, predicate, value):
    """주체와 관계로 식별 키를 만든다. 이름 같은 단일 값은 바뀌어도 키를 유지한다."""
    subject = normalize_memory_value(subject)
    predicate = normalize_memory_value(predicate)

    if predicate in {"name", "age", "birth_date", "location"}:
        return f"{subject}:{predicate}"

    return f"{subject}:{predicate}:{normalize_memory_value(value)}"


def infer_legacy_memory(category, content):
    """이전 기억의 종류와 본문을 읽어 주체·관계·값 튜플을 반환한다."""
    text = str(content or "").strip()
    name_prefix = "사용자의 이름은 "

    if text.startswith(name_prefix):
        value = text[len(name_prefix) :].strip()
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


class MemoryExtractor:
    """사용자가 직접 밝힌 이름과 취향만 장기 기억 후보로 만든다."""

    _NAME = re.compile(
        r"(?:내|제)\s*이름\s*(?:은|이)\s*"
        r"(.+?)(?:이야|야|이에요|예요|입니다)?"
    )
    _PREFERENCE = re.compile(
        r"(?:(?:나는|난|저는|전)\s*)?(.+?)\s*(을|를)\s*"
        r"(좋아해|좋아해요|좋아합니다|싫어해|싫어해요|싫어합니다)"
    )

    def extract(self, observation):
        """발화에서 명시적인 자기 진술을 찾고, 질문이나 추측이면 None을 반환한다."""
        text = observation.content.strip()
        if not text or any(mark in text for mark in ("?", "？")):
            return None

        text = text.rstrip(".!。！").strip()
        name_match = self._NAME.fullmatch(text)
        if name_match:
            name = name_match.group(1).strip()
            if not name or not all(ch.isalpha() or ch in " .’'-" for ch in name):
                return None
            if re.search(
                r"(?:뭐|무엇|누구|기억해|기억나|알려|몰라|모르겠|아니[야라]|맞지|맞아|어떻|일까|인가|였지|이지)$|^(?:뭐|무엇|누구)",
                name,
            ):
                return None
            return MemoryRecord(
                category="user",
                content=f"사용자의 이름은 {name}",
                importance=0.98,
                subject="user",
                predicate="name",
                value=name,
                confidence=0.99,
                source="user_explicit",
            )

        preference = self._PREFERENCE.fullmatch(text)
        if not preference:
            return None
        value, particle, sentiment = preference.groups()
        value = value.strip()
        if not value or re.search(r"(?:^|\s)\S+(?:은|는|이|가)\s", value):
            return None
        dislikes = sentiment.startswith("싫어")
        verb = "싫어한다" if dislikes else "좋아한다"
        return MemoryRecord(
            category="preference",
            content=f"사용자는 {value}{particle} {verb}",
            importance=0.82,
            subject="user",
            predicate="dislikes" if dislikes else "likes",
            value=value,
            confidence=0.9,
            source="user_explicit",
        )
