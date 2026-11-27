"""대화 콘솔의 서버 설정과 실행 진입점."""

import getpass
import os
from urllib.parse import urlsplit

from lucid.log import Logger


def _prompt_server(label: str) -> str | None:
    """label을 표시해 HTTP(S) 서버 주소를 읽는다. 빈 입력은 기존 설정 유지를 뜻한다."""
    while True:
        address = input(f"{label} 주소: ").strip()
        if not address:
            return None
        try:
            parsed = urlsplit(address)
            valid = (
                parsed.scheme in {"http", "https"}
                and parsed.hostname
                and parsed.port != 0
                and not parsed.username
                and not parsed.password
                and not parsed.query
                and not parsed.fragment
                and not any(character.isspace() for character in address)
            )
        except ValueError:
            valid = False
        if valid:
            return address.rstrip("/")
        print("포트를 포함한 올바른 http:// 또는 https:// 서버 주소를 입력해 줘.")


def configure_ollama_address() -> None:
    """입력한 Ollama 주소를 현재 실행 환경에 적용한다. 빈 입력은 기존 주소를 유지한다."""
    print("Ollama 서버 주소 설정 (Enter를 누르면 기존 설정 또는 기본 주소 사용)")
    address = _prompt_server("Ollama")
    if address:
        os.environ["LUCID_OLLAMA_URL"] = address


def configure_korean_tts_address() -> None:
    """한국어 TTS 주소, 서버별 토큰, 화자 입력을 현재 실행 환경에 반영한다."""
    print("한국어 TTS 서버 설정 (Enter를 누르면 기존 설정 또는 기본 주소 사용)")
    address = _prompt_server("한국어 TTS")
    if address is None:
        return
    previous = os.environ.get("LUCID_TTS_URL") or os.environ.get(
        "LUCID_UTAUTTS_URL", ""
    )
    if address != previous.strip().rstrip("/"):
        for name in ("LUCID_TTS_TOKEN", "LUCID_UTAUTTS_TOKEN"):
            os.environ.pop(name, None)
    os.environ["LUCID_TTS_URL"] = address
    token = getpass.getpass("한국어 TTS 토큰: ").strip()
    if token:
        os.environ["LUCID_TTS_TOKEN"] = token
    os.environ["LUCID_TTS_SPEAKER"] = input("화자 이름 [Sohee]: ").strip() or "Sohee"


def main(*, debug: bool = False) -> None:
    """debug에 맞춰 로그 출력을 설정한 뒤 대화 콘솔을 실행하고 자원을 정리한다."""
    Logger.configure(debug)
    try:
        configure_ollama_address()
        configure_korean_tts_address()
    except (EOFError, KeyboardInterrupt):
        return

    # 서버 주소를 정한 후에 엔진을 가져와 시작 시 설정을 반영한다.
    from lucid.app import LucidEngine

    engine = LucidEngine()
    try:
        engine.boot()
        engine.run()
    finally:
        engine.shutdown()
