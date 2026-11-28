"""콘솔에서 모든 모듈의 로그 시각과 수준을 같은 형식으로 표시한다."""

from datetime import datetime


class Logger:
    """콘솔 로그를 기록하는 공용 인터페이스."""

    _debug = False
    _output = staticmethod(print)

    @classmethod
    def configure(cls, debug: bool, output=None) -> None:
        """모든 스레드의 로그 수준과 출력 함수를 지정한다. 기본 출력은 콘솔이다."""
        cls._debug = debug
        cls._output = staticmethod(print if output is None else output)

    @classmethod
    def notice(cls, message: str) -> None:
        """연결 정보나 사용자 조치가 필요한 안내는 출력 모드와 관계없이 표시한다."""
        if cls._debug:
            cls._write("INFO", message)
        else:
            cls._output(message)

    @staticmethod
    def _write(level: str, message: str) -> None:
        """로그 수준과 메시지를 받아 현재 로컬 시각과 함께 한 줄을 출력한다."""
        if not Logger._debug:
            return
        Logger._output(f"[{datetime.now():%H:%M:%S}] [{level}] {message}")

    @staticmethod
    def info(message: str) -> None:
        """일반 동작을 설명하는 메시지를 출력한다."""
        Logger._write("INFO", message)

    @staticmethod
    def warning(message: str) -> None:
        """복구 가능한 문제를 설명하는 메시지를 출력한다."""
        Logger._write("WARNING", message)

    @staticmethod
    def error(message: str) -> None:
        """실패 원인을 설명하는 메시지를 출력한다."""
        Logger._write("ERROR", message)
