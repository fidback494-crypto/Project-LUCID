"""브라우저가 사용자의 선택에 따라 공유한 페이지와 화면을 받는다."""

from lucid.browser.bridge import BrowserBridge
from lucid.browser.context import PageContextStore

__all__ = ["BrowserBridge", "PageContextStore"]
