"""Minimal DuckDuckGo HTML search tool used by the rule-based web action."""

from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

from src.action.action_result import ActionResult
from src.action.tools.base_tool import BaseTool


class _SearchResultsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results = []
        self._active = None
        self._snippet_target = None
        self._capture = None
        self._capture_depth = 0

    def handle_starttag(self, tag, attrs):
        if self._capture is not None:
            self._capture_depth += 1
            return
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._active = {"title": "", "url": self._decode_url(attributes.get("href", "")), "snippet": ""}
            self._capture = "title"
            self._capture_depth = 1
        elif tag in {"a", "div", "span"} and "result__snippet" in classes:
            self._capture = "snippet"
            self._snippet_target = self.results[-1] if self.results else None
            self._capture_depth = 1

    def handle_data(self, data):
        if self._capture == "title" and self._active is not None:
            self._active[self._capture] += data
        elif self._capture == "snippet" and self._snippet_target is not None:
            self._snippet_target[self._capture] += data

    def handle_endtag(self, tag):
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
        if url.startswith("//"):
            url = "https:" + url
        parsed = urlparse(url)
        if "duckduckgo.com" in parsed.netloc:
            destination = parse_qs(parsed.query).get("uddg", [url])[0]
            return unquote(destination)
        return url


class WebTool(BaseTool):
    MAX_QUERY_LENGTH = 300

    @property
    def name(self):
        return "web"

    def execute(self, command: str):
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
            return ActionResult(success=False, output=f"웹 검색에 연결하지 못했어: {type(error).__name__}")

        results = [item for item in parser.results if item["title"].strip() and item["url"].startswith(("http://", "https://"))]
        if not results:
            return ActionResult(success=False, output="검색 결과를 읽지 못했어. 검색 사이트의 응답 형식이 바뀌었을 수 있어.")

        lines = [f"검색어: {query}"]
        for index, result in enumerate(results[:5], start=1):
            title = self._limit(result["title"], 180)
            snippet = self._limit(result["snippet"], 500)
            lines.append(f"{index}. {title}\n   {result['url']}\n   {snippet}")
        lines.append("검색 결과는 출처 후보야. 실제 사실은 연결된 출처를 확인해 답해.")
        return ActionResult(success=True, output="\n".join(lines))

    @staticmethod
    def _clean_query(command):
        query = command.strip()
        for prefix in ("/search", "웹 검색", "웹에서 검색", "인터넷 검색", "검색해줘", "검색해", "검색", "찾아줘", "찾아봐", "조사해줘"):
            if query.casefold().startswith(prefix.casefold()):
                query = query[len(prefix):].strip(" \t:：,，?？")
        for suffix in ("검색해줘", "검색해", "찾아줘", "찾아봐", "조사해줘"):
            if query.casefold().endswith(suffix.casefold()):
                query = query[:-len(suffix)].strip(" \t:：,，?？")
        return query

    @staticmethod
    def _limit(value, limit):
        text = " ".join(str(value or "").split())
        return text if len(text) <= limit else text[:limit].rstrip() + "…"
