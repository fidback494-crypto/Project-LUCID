"""프로젝트 내부의 허용된 텍스트 파일과 폴더 목록을 읽는다."""

import re
from pathlib import Path

from lucid.actions.models import ActionResult
from lucid.actions.tools.base import BaseTool
from lucid.settings import PROJECT_ROOT, data_directory


class FileTool(BaseTool):
    """프로젝트 내부의 허용된 텍스트 파일과 폴더 목록을 읽는다."""

    MAX_FILE_BYTES = 256_000
    MAX_LIST_ENTRIES = 100
    BLOCKED_PARTS = {
        ".git",
        ".venv",
        "venv",
        "env",
        "data",
        "private",
        "secrets",
        ".ssh",
        "credentials",
        "training",
    }
    BLOCKED_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx"}

    def __init__(self, root=None):
        """도구가 접근할 수 있는 루트 경로를 결정한다."""
        self.root = Path(root or PROJECT_ROOT).resolve()

    @property
    def name(self):
        """레지스트리에서 도구를 식별하는 이름을 반환한다."""
        return "file"

    def execute(self, command: str):
        """목록 또는 읽기 명령을 받아 허용한 파일 정보나 경로 오류를 반환한다."""
        operation, argument = self.parse_command(str(command or ""))
        if operation not in {"read", "list"}:
            return ActionResult(
                success=False,
                output="사용법: 파일 읽기 `read <프로젝트 상대경로>` 또는 목록 `list [상대경로]`",
            )

        try:
            target = self._resolve(argument or ".")
        except (OSError, ValueError) as error:
            return ActionResult(
                success=False, output=f"허용된 프로젝트 경로가 아니야: {error}"
            )

        if operation == "list":
            return self._list_directory(target)
        return self._read_file(target)

    @staticmethod
    def parse_command(command):
        """파일 명령을 읽기 또는 목록 동작과 상대 경로로 분리한다."""
        stripped = command.strip()
        explicit = re.match(r"^(read|list)(?:\s+(.+))?$", stripped, re.IGNORECASE)
        if explicit:
            return explicit.group(1).lower(), (explicit.group(2) or ".").strip().strip(
                '"'
            )

        if any(
            phrase in stripped.casefold()
            for phrase in ("파일 목록", "폴더 목록", "list files", "list folder")
        ):
            match = re.search(
                r"(?:^|\s)((?:[\w.-]+[/\\])*[a-zA-Z0-9_.-]+)(?=\s|$)", stripped
            )
            return "list", match.group(1) if match else "."

        # 자연어 문구에서는 공백 없는 파일명이나 슬래시로 구분한 경로를 찾는다.
        if any(
            word in stripped.casefold()
            for word in ("읽", "열어", "보여", "read", "open")
        ):
            match = re.search(
                r"(?:[\w.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,8}", stripped
            )
            if match:
                return "read", match.group(0)
        return "", ""

    def _resolve(self, raw_path):
        """입력 경로가 허용 범위에 있는지 검사한 뒤 절대 경로를 반환한다."""
        candidate = Path(raw_path)
        target = (
            (self.root / candidate).resolve()
            if not candidate.is_absolute()
            else candidate.resolve()
        )
        if (
            target.is_relative_to(data_directory())
            or target.name.casefold() == "browser_bridge_token.txt"
        ):
            raise ValueError("로컬 기억과 페어링 토큰은 열 수 없어")
        try:
            relative = target.relative_to(self.root)
        except ValueError as error:
            raise ValueError("경로는 프로젝트 폴더 안에 있어야 해") from error
        normalized_parts = tuple(part.casefold() for part in relative.parts)
        if any(part in self.BLOCKED_PARTS for part in normalized_parts):
            raise ValueError(
                "비밀 설정, 데이터베이스, 개인 데이터, 가상환경 경로는 읽지 않아"
            )
        if (
            target.name.casefold().startswith(".env")
            or target.suffix.casefold() in self.BLOCKED_SUFFIXES
        ):
            raise ValueError("비밀 설정 파일이나 데이터 파일은 읽지 않아")
        return target

    def _list_directory(self, target):
        """허용된 디렉터리 항목을 이름순으로 모아 도구 결과로 반환한다."""
        if not target.is_dir():
            return ActionResult(success=False, output="목록을 만들 폴더를 찾지 못했어.")
        entries = []
        for entry in target.iterdir():
            try:
                resolved = self._resolve(str(entry))
            except (OSError, ValueError):
                continue
            entries.append(resolved)
        entries.sort(key=lambda entry: (not entry.is_dir(), entry.name.casefold()))
        visible = entries[: self.MAX_LIST_ENTRIES]
        lines = [
            f"{'[폴더]' if entry.is_dir() else '[파일]'} {entry.name}"
            for entry in visible
        ]
        if len(entries) > len(visible):
            lines.append(f"… 나머지 {len(entries) - len(visible)}개 생략")
        return ActionResult(
            success=True, output="\n".join(lines) or "폴더가 비어 있어."
        )

    def _read_file(self, target):
        """허용된 텍스트 파일의 내용을 길이 제한에 맞춰 반환한다."""
        if not target.is_file():
            return ActionResult(success=False, output="읽을 파일을 찾지 못했어.")
        if target.stat().st_size > self.MAX_FILE_BYTES:
            return ActionResult(
                success=False, output="파일이 너무 커서 읽지 않았어. (최대 256KB)"
            )
        try:
            content = target.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return ActionResult(
                success=False, output="텍스트 파일이 아니거나 UTF-8로 읽을 수 없어."
            )
        if not content.strip():
            return ActionResult(success=True, output="파일은 비어 있어.")
        return ActionResult(success=True, output=content[:16_000])
