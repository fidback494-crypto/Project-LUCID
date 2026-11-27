"""Qwen3-TTS 서버에 한국어 음성을 요청하고 Windows에서 WAV를 재생한다."""

import os
import re
import sys
from queue import Empty, Full, Queue
from threading import Event, Thread

import requests

from lucid.log import Logger


class KoreanTTSClient:
    """사용자 응답과 말투를 받아 재생할 문장 하나를 대기열에 보관한다."""

    STYLE_INSTRUCTIONS = {
        "neutral": "",
        "warm": "따뜻하고 다정한 느낌으로, 편안한 억양으로 말해.",
        "curious": "호기심이 살짝 느껴지도록 밝고 자연스럽게 말해.",
        "cheerful": "기분 좋고 생기 있는 목소리로 말해.",
        "playful": "장난기가 은근히 묻어나도록 가볍게 말해.",
        "soothing": "상대를 안심시키듯 부드럽고 차분하게 말해.",
        "concerned": "걱정하는 마음이 느껴지되 차분하고 다정하게 말해.",
        "serious": "또렷하고 침착한 어조로 말해.",
        "shy": "조금 수줍고 조심스러운 느낌으로 말해.",
    }

    def __init__(self):
        """환경 변수에서 서버 주소와 화자를 읽고 합성 요청 대기열을 준비한다."""
        configured_url = os.getenv("LUCID_TTS_URL") or os.getenv("LUCID_UTAUTTS_URL")
        self.explicit_server = bool(configured_url and configured_url.strip())
        self.base_url = (configured_url or "http://127.0.0.1:8000").strip().rstrip("/")
        self.token = (
            os.getenv("LUCID_TTS_TOKEN") or os.getenv("LUCID_UTAUTTS_TOKEN") or ""
        ).strip()
        self.speaker = os.getenv("LUCID_TTS_SPEAKER", "Sohee").strip() or "Sohee"
        self.timeout = self._read_timeout()
        self.session = requests.Session()
        self.available = False
        self._speech_queue = Queue(maxsize=1)
        self._speech_stop = Event()
        self._speech_thread = None

    @staticmethod
    def _read_timeout():
        """설정된 응답 제한 시간을 10~600초 범위의 정수로 반환한다."""
        try:
            return max(10, min(int(os.getenv("LUCID_TTS_TIMEOUT", "180")), 600))
        except ValueError:
            return 180

    def start(self):
        """재생 환경과 서버 상태를 확인하고 요청을 받을 준비가 되면 True를 반환한다."""
        if sys.platform != "win32":
            self._report_unavailable(
                "음성 재생은 Windows에서 지원합니다. 텍스트로 대화합니다."
            )
            return False
        if self._speech_thread is not None and self._speech_thread.is_alive():
            return self.available
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=(3, 10),
            )
            response.raise_for_status()
            health = response.json()
            if not isinstance(health, dict):
                raise ValueError("health response must be a JSON object")
        except (requests.RequestException, ValueError) as error:
            self._report_unavailable(
                "음성 서버에 연결하지 못했습니다. 텍스트로 대화합니다."
            )
            Logger.info(f"[Voice] {type(error).__name__}")
            return False

        if health.get("engine") != "qwen3-tts" or health.get("language") != "Korean":
            self._report_unavailable(
                "음성 서버가 한국어 Qwen3-TTS를 지원하는지 확인해 주세요."
            )
            return False
        if not self.token:
            Logger.notice("음성을 사용하려면 한국어 TTS 토큰을 설정해 주세요.")
            return False

        self.available = True
        self._start_speech_worker()
        Logger.info(f"[Voice] Korean TTS ready: {self.speaker}")
        return True

    def _report_unavailable(self, message: str) -> None:
        """음성 서버를 직접 설정한 사용자에게 텍스트 모드로 전환한 이유를 알린다."""
        if self.explicit_server:
            Logger.notice(message)
        else:
            Logger.info(f"[Voice] {message}")

    def _start_speech_worker(self):
        """대기 음성을 재생할 작업 스레드 하나를 시작한다."""
        if self._speech_thread is not None and self._speech_thread.is_alive():
            return
        self._speech_stop.clear()
        self._speech_thread = Thread(
            target=self._run_speech_queue,
            name="LUCIDKoreanSpeech",
            daemon=True,
        )
        self._speech_thread.start()

    def _run_speech_queue(self):
        """대기 문장을 차례로 재생하고 종료 신호를 받으면 HTTP 세션을 닫는다."""
        while not self._speech_stop.is_set():
            try:
                text, style = self._speech_queue.get(timeout=0.25)
            except Empty:
                continue
            try:
                if not self._speech_stop.is_set():
                    self.speak(text, style=style)
            finally:
                self._speech_queue.task_done()
        self.session.close()

    def speak_async(self, text, style="neutral"):
        """문장과 말투를 대기열에 넣는다. 이미 대기 중인 문장을 대체하며, 등록에 성공하면 True를 반환한다."""
        if (
            not self.available
            or self._speech_thread is None
            or not self._speech_thread.is_alive()
            or sys.platform != "win32"
            or not text
            or not str(text).strip()
        ):
            return False

        item = (str(text).strip(), style)
        try:
            self._speech_queue.put_nowait(item)
            return True
        except Full:
            pass

        try:
            self._speech_queue.get_nowait()
            self._speech_queue.task_done()
        except Empty:
            pass

        try:
            self._speech_queue.put_nowait(item)
            return True
        except Full:
            return False

    def stop(self):
        """대기 음성을 비우고, 합성 중이면 응답이 도착해도 다음 재생을 생략한다."""
        self.available = False
        self._speech_stop.set()
        while True:
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except Empty:
                break

        if self._speech_thread is not None:
            self._speech_thread.join(timeout=1)
        else:
            self.session.close()

    def speak(self, text, style="neutral"):
        """문장을 지정한 말투로 합성해 재생하고 모든 조각이 재생되면 True를 반환한다."""
        if not self.available or not text or not text.strip():
            return False
        if sys.platform != "win32":
            Logger.warning("[Voice] Automatic WAV playback is currently Windows-only.")
            return False

        try:
            import winsound

            instruction = self.STYLE_INSTRUCTIONS.get(style, "")
            language = "Korean" if re.search(r"[\uac00-\ud7a3]", text) else "Auto"
            headers = {"Authorization": f"Bearer {self.token}"}
            for chunk in self._split_text(text.strip()):
                if self._speech_stop.is_set():
                    return False
                response = self.session.post(
                    f"{self.base_url}/api/synthesize/audio",
                    headers=headers,
                    json={
                        "text": chunk,
                        "language": language,
                        "speaker": self.speaker,
                        "speech_style": style,
                        "instruct": instruction,
                    },
                    timeout=(5, self.timeout),
                )
                response.raise_for_status()
                if not response.headers.get("Content-Type", "").startswith("audio/wav"):
                    Logger.warning("[Voice] Korean TTS returned a non-WAV response.")
                    return False
                if self._speech_stop.is_set():
                    return False
                winsound.PlaySound(response.content, winsound.SND_MEMORY)
            return True
        except requests.RequestException as error:
            Logger.warning(
                f"[Voice] Korean speech generation failed: {type(error).__name__}"
            )
        except Exception as error:
            Logger.warning(f"[Voice] Audio playback failed: {error}")
        return False

    @staticmethod
    def _split_text(text, max_chars=240):
        """문장 경계와 글자 수 상한에 맞춰 전송할 문자열 목록을 반환한다."""
        sentences = re.split(r"(?<=[.!?。！？])\s*", text)
        chunks = []
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(
                    sentence[index : index + max_chars]
                    for index in range(0, len(sentence), max_chars)
                )
                continue
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks


# 기존 통합 코드가 쓰던 클래스 이름을 유지한다.
UtauTTSClient = KoreanTTSClient
