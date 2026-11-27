"""브라우저가 공유한 마지막 웹페이지와 화면을 메모리에 보관한다."""

from dataclasses import dataclass, replace
from datetime import datetime
from threading import Lock


@dataclass(frozen=True)
class PageContext:
    """사용자가 공유한 페이지 또는 캡처 한 장의 내용과 수신 시각."""

    title: str
    url: str
    text: str
    selection: str
    image_base64: str
    image_mime: str
    continuous: bool
    version: int
    received_at: datetime
    session_id: str = ""

    @property
    def has_image(self):
        """화면 이미지가 포함됐으면 True를 반환한다."""
        return bool(self.image_base64)

    def prompt_context(self, limit=8000):
        """모델에 전달할 제목·주소·선택 영역과 limit자 이하의 본문을 반환한다."""
        return (
            f"제목: {self.title}\n"
            f"주소: {self.url}\n"
            f"사용자가 선택한 텍스트: {self.selection[:2000] or '없음'}\n"
            f"페이지 본문 일부:\n{self.text[:limit] or '없음'}"
        )


class PageContextStore:
    """페이지 공유와 화면 공유를 서로 덮어쓰지 않도록 보관한다."""

    def __init__(self):
        """빈 저장소를 만들고 페이지·화면 갱신에 공유할 잠금을 준비한다."""
        self._lock = Lock()
        self._page = None
        self._screen = None
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
        session_id="",
    ):
        """확장에서 받은 내용을 최신 페이지나 화면으로 저장하고 해당 스냅샷을 반환한다."""
        with self._lock:
            self._version += 1
            if continuous and not session_id:
                # 이전 확장은 세션 번호를 생략한다. 중지 후 도착한 프레임은 새 세션이다.
                if self._screen is not None and self._screen.continuous:
                    session_id = self._screen.session_id
                else:
                    session_id = str(self._version)
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
                session_id=session_id,
            )
            if context.has_image:
                self._screen = context
            else:
                self._page = context
            self._latest = context
            return context

    def latest(self):
        """형식에 관계없이 마지막으로 받은 스냅샷을 반환한다."""
        with self._lock:
            return self._latest

    def latest_page(self):
        """마지막으로 공유한 웹페이지나 None을 반환한다."""
        with self._lock:
            return self._page

    def latest_screen(self):
        """마지막으로 공유한 화면이나 None을 반환한다."""
        with self._lock:
            return self._screen

    def stop_continuous(self, session_id=""):
        """같은 세션의 연속 관찰을 종료하고 마지막 화면과 원래 수신 시각을 보존한다."""
        with self._lock:
            screen = self._screen
            if screen is None or not screen.continuous:
                return screen
            if session_id and screen.session_id != session_id:
                return screen
            self._version += 1
            self._screen = replace(screen, continuous=False, version=self._version)
            if self._latest is screen:
                self._latest = self._screen
            return self._screen

    def prompt_context(self):
        """공유한 페이지의 프롬프트를 반환하고, 공유 기록이 없으면 '없음'을 반환한다."""
        page = self.latest_page()
        return page.prompt_context() if page else "없음"
