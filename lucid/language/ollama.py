"""Ollama의 단일 응답 HTTP API와 요청 시간 통계를 관리한다."""

import os
from time import monotonic

import requests

from lucid.core.kernel import BaseModule
from lucid.log import Logger
from lucid.settings import (
    DEFAULT_KEEP_ALIVE,
    DEFAULT_OLLAMA_URL,
    DEFAULT_WARMUP_TIMEOUT,
    MODEL_NAME,
)


class OllamaClient:
    """환경 변수에서 모델과 서버 주소를 읽어 HTTP 세션을 재사용한다."""

    def __init__(self):
        """환경 설정을 읽고 서버와 통신할 세션을 준비한다."""
        self.base_url = (
            os.getenv("LUCID_OLLAMA_URL", "").strip().rstrip("/") or DEFAULT_OLLAMA_URL
        )
        self.api_url = f"{self.base_url}/api/chat"
        self.generate_url = f"{self.base_url}/api/generate"
        self.timeout = self._read_timeout("LUCID_OLLAMA_TIMEOUT", 300)
        self.warmup_timeout = self._read_timeout(
            "LUCID_OLLAMA_WARMUP_TIMEOUT", DEFAULT_WARMUP_TIMEOUT
        )
        self.keep_alive = (
            os.getenv("LUCID_OLLAMA_KEEP_ALIVE", "").strip() or DEFAULT_KEEP_ALIVE
        )
        self.model = os.getenv("LUCID_OLLAMA_MODEL", "").strip() or MODEL_NAME
        self.session = requests.Session()
        self.last_metrics = {}

    @staticmethod
    def _read_timeout(variable, default):
        """환경 변수에서 5~3,600초의 응답 대기 시간을 읽고 잘못된 입력에는 기본값을 쓴다."""
        try:
            return max(5, min(int(os.getenv(variable, default)), 3600))
        except ValueError:
            return default

    def close(self):
        """재사용 중이던 HTTP 연결을 닫는다."""
        self.session.close()

    def _post(self, url, payload, timeout, label):
        """모델과 유지 시간을 붙여 전송하고 응답 객체와 요청 통계를 얻는다."""
        started_at = monotonic()
        self.last_metrics = {}
        try:
            response = self.session.post(
                url,
                json={
                    "model": self.model,
                    "stream": False,
                    "keep_alive": self.keep_alive,
                    **payload,
                    "options": {"num_ctx": 4096, **payload.get("options", {})},
                },
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Ollama 응답이 JSON 객체가 아닙니다.")
            self._record_metrics(data, monotonic() - started_at, label)
            return data
        except Exception:
            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }
            raise

    def preload(self, timeout=None):
        """대화·화면용 모델을 미리 불러온다. timeout은 예열 응답을 기다리는 초 단위 시간이다."""
        read_timeout = self.warmup_timeout if timeout is None else timeout
        try:
            result = self._post(
                self.generate_url,
                {"prompt": ""},
                (5, read_timeout),
                "warmup",
            )
            if result.get("done") is not True:
                self.last_metrics["error"] = True
                raise ValueError("모델 로드가 완료되지 않았어.")
        except (requests.RequestException, ValueError, TypeError) as error:
            Logger.warning(f"[Ollama] Model warmup skipped ({type(error).__name__})")
            return False
        Logger.info(f"[Ollama] Model warmup completed: {self.model}")
        return True

    def _record_metrics(self, data, request_wall_seconds, label="generate"):
        """서버의 나노초 단위 통계와 실제 요청 시간을 초 단위로 기록한다."""

        def seconds(field):
            """응답의 나노초 값을 초로 환산하며, 값이 없거나 숫자가 아니면 0을 쓴다."""
            try:
                return float(data.get(field) or 0) / 1_000_000_000
            except (TypeError, ValueError):
                return 0.0

        eval_count = int(data.get("eval_count") or 0)
        eval_seconds = seconds("eval_duration")
        self.last_metrics = {
            "request_wall_seconds": request_wall_seconds,
            "total_seconds": seconds("total_duration"),
            "load_seconds": seconds("load_duration"),
            "prompt_seconds": seconds("prompt_eval_duration"),
            "generation_seconds": eval_seconds,
            "prompt_tokens": int(data.get("prompt_eval_count") or 0),
            "output_tokens": eval_count,
            "tokens_per_second": (
                eval_count / eval_seconds if eval_seconds > 0 else 0.0
            ),
        }
        metrics = self.last_metrics
        Logger.info(
            f"[Ollama Timing] {label} wall={metrics['request_wall_seconds']:.3f}s "
            f"load={metrics['load_seconds']:.3f}s "
            f"prompt={metrics['prompt_seconds']:.3f}s "
            f"generate={metrics['generation_seconds']:.3f}s "
            f"tokens={metrics['prompt_tokens']}+{metrics['output_tokens']} "
            f"speed={metrics['tokens_per_second']:.1f} tok/s"
        )

    def check_connection(self):
        """모델 목록 API에 연결할 수 있으면 True를 반환한다."""
        try:
            self.session.get(f"{self.base_url}/api/tags", timeout=10).raise_for_status()
            return True
        except Exception as error:
            Logger.error(f"[Ollama] Connection Error : {error}")
            return False

    def chat(self, messages, think=False, options=None, response_format=None):
        """역할별 메시지와 선택적 생성 설정을 보내 답변 문자열을 반환한다."""
        payload = {"messages": messages}
        if think:
            payload["think"] = True
        return self._generate_text(
            self.api_url, payload, options, response_format, "chat"
        )

    def generate(self, messages, options=None, response_format=None):
        """문자열은 생성 API로, 역할별 메시지는 대화 API로 보내 답변을 반환한다."""
        if not isinstance(messages, str):
            return self.chat(messages, options=options, response_format=response_format)
        return self._generate_text(
            self.generate_url,
            {"prompt": messages},
            options,
            response_format,
            "generate",
        )

    def _generate_text(self, url, payload, options, response_format, label):
        """주어진 엔드포인트로 생성 요청을 보내 답변이나 연결 실패 안내를 반환한다."""
        if options:
            payload["options"] = options
        if response_format is not None:
            payload["format"] = response_format

        try:
            data = self._post(url, payload, (5, self.timeout), label)
            text = (
                data.get("message", {}).get("content")
                if label == "chat"
                else data.get("response")
            )
            if not text:
                Logger.warning("[Ollama] Empty response")
                return ""
            return text.strip()
        except requests.Timeout:
            Logger.error(f"[Ollama] {label} timeout")
            return "미안해. 응답 시간이 너무 오래 걸렸어."
        except requests.ConnectionError:
            Logger.error("[Ollama] Failed to connect to the configured server")
            return "미안해. 현재 AI 서버에 연결할 수 없어."
        except Exception as error:
            self.last_metrics["error"] = True
            Logger.error(f"[Ollama] {label} Error : {error}")
            return "미안해. AI 처리 중 문제가 발생했어."


class OllamaModule(BaseModule):
    """커널에 등록되는 모델 엔진마다 HTTP 클라이언트의 수명을 관리한다."""

    def __init__(self):
        """엔진 전용 Ollama 세션을 준비해 여러 턴에 걸쳐 재사용한다."""
        super().__init__()
        self.client = OllamaClient()

    def stop(self) -> None:
        """이 엔진이 소유한 HTTP 세션을 닫고 종료를 기록한다."""
        self.client.close()
        super().stop()
