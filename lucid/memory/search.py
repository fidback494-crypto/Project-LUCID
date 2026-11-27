"""한국어 질문과 관련된 활성 장기 기억을 찾는다."""

import re

from lucid.log import Logger

STOPWORDS = frozenset(
    "그 그런 그리고 기억나 기억해 나 나는 난 내 너 네 들려줘 말해 무엇 뭐 뭐야 알려 어떤 어떻게 없어 이 인가 있어 저 저는 저런 전 정말 제 좀 지금 해 해줘 했어".split()
)
PARTICLES = tuple(
    "까지 보다 부터 에게 에서 으로 처럼 한테 가 과 까 는 도 를 만 야 에 와 요 은 을 의 이 죠".split()
)


def query_terms(query):
    """검색 범위가 다른 저장소들이 같은 규칙으로 한국어 조사와 불용어를 처리하도록 한다."""
    terms = []
    for token in re.findall(r"[0-9a-z가-힣]+", str(query).casefold()):
        if token in STOPWORDS:
            continue
        for particle in PARTICLES:
            if len(token) > len(particle) + 1 and token.endswith(particle):
                token = token[: -len(particle)]
                break
        if token and token not in STOPWORDS:
            terms.append(token)
    return list(dict.fromkeys(terms))[:20]


class MemorySearch:
    """활성 기억을 검색어 관련성 순으로 읽는다."""

    STOPWORDS = STOPWORDS
    PARTICLES = PARTICLES

    def __init__(self, long_memory):
        """검색 대상인 장기 기억 저장소를 연결한다."""
        self.memory = long_memory

    def search(self, observation):
        """관찰이나 질문에서 검색어를 추출해 관련 사실의 본문을 최대 다섯 건 반환한다."""
        text = (
            observation.content if hasattr(observation, "content") else str(observation)
        )
        keywords = self._keywords(text)
        results = self.memory.search_records(keywords, limit=5)

        Logger.info(f"[MemorySearch] {len(results)} Memories Found")
        return [record["content"] for record in results]

    @classmethod
    def _keywords(cls, text):
        """질문에서 조사를 제거하고 관계 키를 포함한 중복 없는 검색어를 반환한다."""
        keywords = []
        for term in query_terms(text):
            keywords.append(term)
            if term.startswith("좋아"):
                keywords.extend(("likes", "좋아한다"))
            elif term.startswith("싫어"):
                keywords.extend(("dislikes", "싫어한다"))
            elif term.startswith("이름"):
                keywords.append("name")
        return list(dict.fromkeys(keywords))[:20]
