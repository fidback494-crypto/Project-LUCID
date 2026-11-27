"""분할과 학습에 공통으로 사용하는 대화 데이터 검증."""

import json
from pathlib import Path

# 실행 시 인지 응답 스키마와 동일한 유니코드 문자 수 한도다.
_MAX_TARGET_LENGTH = {"reply": 500, "experience": 60, "meaning": 100}


def read_examples(path: Path) -> list[dict]:
    """path의 JSONL을 검증하고 입력 순서대로 대화 행 목록을 반환한다."""
    examples = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {error}"
                ) from error
            validate_row(row, path, line_number)
            examples.append(row)
    if len(examples) < 2:
        raise ValueError("At least two reviewed examples are needed to create a split.")
    return examples


def validate_messages(messages, allowed_roles, label) -> None:
    """메시지 목록의 역할·본문을 검사하고 오류가 있으면 label을 포함한 예외를 낸다."""
    if not isinstance(messages, list) or not messages:
        raise ValueError(f"{label} must be a non-empty message array.")
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError(f"{label} contains a non-object message.")
        if message.get("role") not in allowed_roles:
            raise ValueError(f"{label} contains an unsupported role.")
        if (
            not isinstance(message.get("content"), str)
            or not message["content"].strip()
        ):
            raise ValueError(f"{label} contains an empty or non-text message.")


def validate_row(row, path, line_number) -> None:
    """한 행의 메시지 역할과 응답 필드·길이를 검사하고 오류에 파일 위치를 붙인다."""
    location = f"{path}:{line_number}"
    if not isinstance(row, dict):
        raise ValueError(f"{location}: each JSONL row must be an object.")
    validate_messages(
        row.get("prompt"), {"system", "user", "assistant"}, f"{location} prompt"
    )
    validate_messages(row.get("completion"), {"assistant"}, f"{location} completion")
    if row["prompt"][-1].get("role") != "user":
        raise ValueError(f"{location}: prompt must end with the current user message.")
    if len(row["completion"]) != 1:
        raise ValueError(
            f"{location}: completion must contain exactly one assistant message."
        )
    try:
        target = json.loads(row["completion"][0]["content"])
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{location}: assistant completion must contain JSON."
        ) from error
    required = {"reply", "intent", "experience", "meaning", "speech_style"}
    if not isinstance(target, dict) or set(target) != required:
        raise ValueError(
            f"{location}: completion JSON keys must be exactly {sorted(required)}."
        )
    if not all(
        isinstance(target[key], str) and target[key].strip() for key in required
    ):
        raise ValueError(f"{location}: every completion value must be non-empty text.")
    for field, limit in _MAX_TARGET_LENGTH.items():
        if len(target[field]) > limit:
            raise ValueError(f"{location}: {field} exceeds {limit} characters.")
    if target["intent"] not in {
        "question",
        "greeting",
        "conversation",
        "request",
        "emotion",
        "exit",
    }:
        raise ValueError(f"{location}: intent is outside the response schema.")
    if target["speech_style"] not in {
        "neutral",
        "warm",
        "curious",
        "cheerful",
        "playful",
        "soothing",
        "concerned",
        "serious",
        "shy",
    }:
        raise ValueError(f"{location}: speech_style is outside the response schema.")
