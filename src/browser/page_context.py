"""The most recently user-shared browser page."""

from dataclasses import dataclass
from datetime import datetime
from threading import Lock


@dataclass(frozen=True)
class PageContext:
    title: str
    url: str
    text: str
    selection: str
    image_base64: str
    image_mime: str
    continuous: bool
    version: int
    received_at: datetime

    @property
    def has_image(self):
        return bool(self.image_base64)

    def prompt_context(self, limit=8000):
        body = self.text[:limit]
        selected = self.selection[:2000]

        return (
            f"제목: {self.title}\n"
            f"주소: {self.url}\n"
            f"사용자가 선택한 텍스트: {selected or '없음'}\n"
            f"페이지 본문 일부:\n{body or '없음'}"
        )


class PageContextStore:
    """Thread-safe storage populated only by the paired local extension."""

    def __init__(self):
        self._lock = Lock()
        self._latest = None
        self._version = 0

    def update(
        self,
        *,
        title,
        url,
        text,
        selection="",
        image_base64="",
        image_mime="image/jpeg",
        continuous=False,
    ):
        with self._lock:
            self._version += 1
            context = PageContext(
                title=str(title).strip()[:500],
                url=str(url).strip()[:2000],
                text=str(text).strip()[:16000],
                selection=str(selection).strip()[:4000],
                image_base64=str(image_base64).strip(),
                image_mime=str(image_mime).strip()[:100],
                continuous=bool(continuous),
                version=self._version,
                received_at=datetime.now(),
            )
            self._latest = context

        return context

    def latest(self):
        with self._lock:
            return self._latest

    def prompt_context(self):
        context = self.latest()
        return context.prompt_context() if context else "없음"
