"""DuckDuckGo의 HTML 응답에서 검색 결과와 출처를 추출한다."""

from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import requests

from lucid.actions.models import ActionResult
from lucid.actions.tools.base import BaseTool


class _SearchResultsParser(HTMLParser):
    """DuckDuckGo의 HTML 응답에서 검색 결과와 출처를 추출한다."""

    def __init__(self):
        """제목과 본문을 추적할 파서 상태와 결과 목록을 초기화한다."""
        super().__init__(convert_charrefs=True)
        self.results = []
        self._active = None
        self._snippet_target = None
        self._capture = None
        self._capture_depth = 0

    def handle_starttag(self, tag, attrs):
        """여는 태그와 속성에서 결과 제목이나 설명 수집을 시작한다."""
        if self._capture is not None:
            self._capture_depth += 1
            return
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._active = {
                "title": "",
                "url": self._decode_url(attributes.get("href", "")),
                "snippet": "",
            }
            self._capture = "title"
            self._capture_depth = 1
        elif tag in {"a", "div", "span"} and "result__snippet" in classes:
            self._capture = "snippet"
            self._snippet_target = self.results[-1] if self.results else None
            self._capture_depth = 1

    def handle_data(self, data):
        """현재 수집 중인 제목이나 설명에 텍스트를 추가한다."""
        if self._capture == "title" and self._active is not None:
            self._active[self._capture] += data
        elif self._capture == "snippet" and self._snippet_target is not None:
            self._snippet_target[self._capture] += data

    def handle_endtag(self, tag):
        """닫는 태그를 처리하고 완성된 제목과 링크를 결과 목록에 기록한다."""
        if self._capture is None:
            return
        self._capture_depth -= 1
        if self._capture_depth > 0:
            return
        if self._capture == "title" and self._active is not None:
            self._capture = None
            self.results.append(self._active)
            self._snippet_target = self._active
            self._active = None
        else:
            self._capture = None
            self._snippet_target = None

    @staticmethod
    def _decode_url(url):
        """검색 서비스의 리디렉션 링크에서 실제 목적지 URL을 반환한다."""
        if url.startswith("//"):
            url = "https:" + url
        parsed = urlparse(url)
        if "duckduckgo.com" in parsed.netloc:
            destination = parse_qs(parsed.query).get("uddg", [url])[0]
            return unquote(destination)
        return url


class WebTool(BaseTool):
    """DuckDuckGo의 HTML 응답에서 검색 결과와 출처를 추출한다."""

    MAX_QUERY_LENGTH = 300

    @property
    def name(self):
        """레지스트리에서 도구를 식별하는 이름을 반환한다."""
        return "web"

    def execute(self, command: str):
        """검색 명령에서 질의를 추출하고 제목·링크·요약을 최대 다섯 건 반환한다."""
        query = self._clean_query(str(command or ""))
        if not query:
            return ActionResult(success=False, output="검색어를 입력해 줘.")
        if len(query) > self.MAX_QUERY_LENGTH:
            query = query[: self.MAX_QUERY_LENGTH]

        try:
            response = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Project-LUCID/1.0 (web search)"},
                timeout=(4, 12),
            )
            response.raise_for_status()
            parser = _SearchResultsParser()
            parser.feed(response.text)
        except requests.RequestException as error:
            return ActionResult(
                success=False,
                output=f"웹 검색에 연결하지 못했어: {type(error).__name__}",
            )

        results = [
            item
            for item in parser.results
            if item["title"].strip() and item["url"].startswith(("http://", "https://"))
        ]
        if not results:
            return ActionResult(
                success=False,
                output="검색 결과를 읽지 못했어. 검색 사이트의 응답 형식이 바뀌었을 수 있어.",
            )

        lines = [f"검색어: {query}"]
        for index, result in enumerate(results[:5], start=1):
            title = self._limit(result["title"], 180)
            snippet = self._limit(result["snippet"], 500)
            lines.append(f"{index}. {title}\n   {result['url']}\n   {snippet}")
        lines.append("검색 결과는 출처 후보야. 실제 사실은 연결된 출처를 확인해 답해.")
        return ActionResult(success=True, output="\n".join(lines))

    @staticmethod
    def _clean_query(command):
        """입력에서 검색을 지시하는 표현을 제거한 검색어를 반환한다."""
        query = command.strip()
        for prefix in (
            "/search",
            "웹 검색",
            "웹에서 검색",
            "인터넷 검색",
            "검색해줘",
            "검색해",
            "검색",
            "찾아줘",
            "찾아봐",
            "조사해줘",
        ):
            if query.casefold().startswith(prefix.casefold()):
                query = query[len(prefix) :].strip(" \t:：,，?？")
        for suffix in ("검색해줘", "검색해", "찾아줘", "찾아봐", "조사해줘"):
            if query.casefold().endswith(suffix.casefold()):
                query = query[: -len(suffix)].strip(" \t:：,，?？")
        return query

    @staticmethod
    def _limit(value, limit):
        """문자열의 공백을 정리하고 길이 제한을 적용한다."""
        text = " ".join(str(value or "").split())
        return text if len(text) <= limit else text[:limit].rstrip() + "…"
