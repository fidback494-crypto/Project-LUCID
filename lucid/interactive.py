"""데스크톱 창과 로컬 웹 화면에서 공통으로 사용하는 대화 엔진 작업자."""

import os
from functools import partial
from io import StringIO

from lucid.cli import apply_tts_settings
from lucid.log import Logger


def _publish(events, channel, *values, sep=" ", end="\n", flush=False):
    """print 형식으로 전달된 출력을 한 문자열로 합쳐 UI 이벤트로 보낸다."""
    text = StringIO()
    print(*values, sep=sep, end=end, file=text, flush=flush)
    events.put((channel, text.getvalue()))


def run_engine(settings, debug, commands, events, stopping, engine_factory=None):
    """서버 설정으로 엔진 하나를 열어 대화·명령을 순서대로 처리하고 종료 시 자원을 닫는다."""
    engine = None
    try:
        if stopping.is_set():
            return
        ollama, tts, token, speaker = settings
        os.environ["LUCID_OLLAMA_URL"] = ollama
        apply_tts_settings(tts, token, speaker)
        Logger.configure(debug, output=partial(_publish, events, "log"))
        if engine_factory is None:
            from lucid.app import LucidEngine

            engine_factory = LucidEngine
        engine = engine_factory(output=partial(_publish, events, "output"))
        if stopping.is_set():
            return
        engine.boot()
        if not stopping.is_set():
            events.put(("ready", ""))
        while not stopping.is_set():
            command = commands.get()
            if command is None or stopping.is_set():
                break
            try:
                if not engine.handle_input(command):
                    events.put(("quit", ""))
                    break
            except Exception as error:
                events.put(("output", f"입력을 처리하지 못했어. {error}\n"))
            events.put(("ready", ""))
    except Exception as error:
        events.put(("failed", f"{type(error).__name__}: {error}"))
    finally:
        if engine is not None:
            try:
                engine.shutdown()
            except Exception as error:
                events.put(("log", f"종료 중 오류: {error}\n"))
