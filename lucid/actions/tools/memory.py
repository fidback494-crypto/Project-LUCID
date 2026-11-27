"""사용자가 명시적으로 요청한 활성 기억을 조회한다."""

import re

from lucid.actions.models import ActionResult
from lucid.actions.tools.base import BaseTool
from lucid.memory.search import MemorySearch


class MemoryTool(BaseTool):
    """전체 목록과 특정 기억 검색을 구분한다."""

    _LIST = re.compile(
        r"(?:내가? |네가? |너의 |저장된 )?(?:장기 ?)?(?:기억|메모리)(?:을|를|들| 목록| 전체| 전부)*"
        r"\s*(?:보여\s*줘|알려\s*줘|보여\s*주세요|보기)|"
        r"(?:나에 대해 )?(?:뭘|무엇을) 기억하고 있(?:어|니|나요)"
    )
    _SEARCH = re.compile(
        r"(?:내 |저장된 )?(?:장기 ?)?(?:기억|메모리)에서\s+(.+?)\s*"
        r"(?:찾아\s*줘|검색해\s*줘|찾아봐|알려\s*줘)"
    )

    def __init__(self, long_memory):
        """검색과 목록 조회에 사용할 장기 기억 저장소를 보관한다."""
        self.long_memory = long_memory

    @property
    def name(self):
        """레지스트리에서 도구를 식별하는 이름을 반환한다."""
        return "memory"

    @classmethod
    def parse_query(cls, command):
        """전체 목록이면 빈 문자열, 검색이면 검색어, 해당하지 않으면 None을 반환한다."""
        text = str(command or "").strip().rstrip(".!?？").strip()
        if cls._LIST.fullmatch(text):
            return ""
        match = cls._SEARCH.fullmatch(text)
        return match.group(1) if match else None

    def execute(self, command: str):
        """목록 또는 검색 명령을 실행해 일치한 기억을 반환한다."""
        query = self.parse_query(command)
        if query is None:
            return ActionResult(False, "기억 목록이나 찾고 싶은 기억을 지정해 줘.")
        try:
            if query:
                contents = MemorySearch(self.long_memory).search(query)
                return ActionResult(
                    True, "\n".join(contents) or "일치하는 기억이 없어."
                )
            lines = [
                f"#{memory['id']} [{memory['predicate']}] {memory['content']} "
                f"(신뢰도 {memory['confidence']:.2f})"
                for memory in self.long_memory.all()
            ]
            return ActionResult(True, "\n".join(lines) or "기억이 비어있다.")
        except Exception as error:
            return ActionResult(False, str(error))
