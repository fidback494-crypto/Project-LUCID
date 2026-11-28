"""대화·화면·클릭과 예열이 한 Ollama 모델을 쓰는지 로컬 HTTP로 검증한다."""

import json
import os
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from threading import Thread
from unittest.mock import patch
from urllib.request import Request, urlopen

from requests import HTTPError

from lucid.browser import BrowserBridge, PageContextStore
from lucid.cognition.engine import CognitiveEngine
from lucid.language.ollama import OllamaClient
from lucid.vision import VisionClient


class _OllamaHandler(BaseHTTPRequestHandler):
    """요청을 기록하고 예열, 대화, 화면 분석에 해당하는 짧은 응답을 돌려준다."""

    def do_POST(self):
        """서버에 실제로 도착한 요청 경로와 본문을 보관한다."""
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.calls.append((self.path, body))
        if self.server.fail:
            self.send_error(503)
            return
        if self.path == "/api/generate":
            result = {"done": True, "done_reason": "load", "response": ""}
        elif "format" in body:
            result = {"message": {"content": '{"target":1}'}}
        else:
            result = {"message": {"content": "한국어 응답"}}
        raw = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        """테스트 출력에서 HTTP 접근 로그를 생략한다."""


@contextmanager
def _model_server():
    """임의의 루프백 포트에서 Ollama 대역을 열어 두고 검사 후 닫는다."""
    with ThreadingHTTPServer(("127.0.0.1", 0), _OllamaHandler) as server:
        server.calls = []
        server.fail = False
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
        thread.start()
        try:
            yield server, f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


class ModelConfigTests(unittest.TestCase):
    """새 모델 설정과 이전 비전 전용 설정이 공존하는 환경도 검사한다."""

    def test_defaults_and_blank_values(self):
        """별도 비전 설정만 있거나 공용 설정이 비면 두 클라이언트 모두 같은 기본값을 쓴다."""
        env = {
            "LUCID_OLLAMA_URL": " ",
            "LUCID_OLLAMA_MODEL": " ",
            "LUCID_OLLAMA_WARMUP_TIMEOUT": "invalid",
            "LUCID_VISION_URL": "http://vision.invalid",
            "LUCID_VISION_MODEL": "old-vision",
        }
        with patch.dict(os.environ, env, clear=True):
            for cls in (OllamaClient, VisionClient):
                with self.subTest(client=cls.__name__):
                    client = cls()
                    self.addCleanup(client.close)
                    self.assertEqual(client.base_url, "http://127.0.0.1:11434")
                    self.assertEqual(client.model, "gemma3:12b")
                    self.assertEqual(client.warmup_timeout, 180)
                    self.assertEqual(client.keep_alive, "10m")

    def test_one_model_for_chat_screen_click_and_warmup(self):
        """예열, 대화, 관찰과 확장의 클릭 요청이 모두 같은 모델·서버로 전달된다."""
        with (
            _model_server() as (server, url),
            tempfile.TemporaryDirectory() as data_dir,
        ):
            env = {
                "LUCID_OLLAMA_URL": url + "/",
                "LUCID_OLLAMA_MODEL": "fixture:multimodal",
                "LUCID_OLLAMA_WARMUP_TIMEOUT": "240",
                "LUCID_OLLAMA_TIMEOUT": "370",
                "LUCID_OLLAMA_KEEP_ALIVE": "25m",
                "LUCID_VISION_URL": "http://127.0.0.1:1",
                "LUCID_VISION_MODEL": "obsolete",
                "LUCID_VISION_TIMEOUT": "17",
                "LUCID_BROWSER_TOKEN": "fixture-token",
                "LUCID_DATA_DIR": data_dir,
                "NO_PROXY": "127.0.0.1",
            }
            with patch.dict(os.environ, env, clear=True):
                cognition = CognitiveEngine()
                vision = VisionClient()
                self.addCleanup(cognition.stop)
                self.addCleanup(vision.close)
                with patch.object(
                    cognition.client.session,
                    "post",
                    wraps=cognition.client.session.post,
                ) as post:
                    cognition.start()
                    self.assertEqual(post.call_args.kwargs["timeout"], (5, 240))
                    reply = cognition.client.chat([{"role": "user", "content": "안녕"}])
                    self.assertEqual(reply, "한국어 응답")
                    self.assertEqual(post.call_args.kwargs["timeout"], (5, 370))

                # 1×1 PNG. 실제 화면 내용이나 개인 데이터 없이 이미지 요청을 검증한다.
                sample_image = (
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
                    "/x8AAwMCAO+jWZkAAAAASUVORK5CYII="
                )
                self.assertEqual(
                    vision.observe(sample_image, "무엇이 보여?"), "한국어 응답"
                )
                bridge = BrowserBridge(PageContextStore())
                bridge.port = 0
                with redirect_stdout(StringIO()):
                    bridge.start()
                try:
                    request = Request(
                        f"http://127.0.0.1:{bridge._server.server_port}/click-target",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(
                            {
                                "token": bridge.token,
                                "image_base64": sample_image,
                                "instruction": "확인 버튼",
                                "candidates": ["확인"],
                            }
                        ).encode("utf-8"),
                    )
                    with urlopen(request, timeout=5) as response:
                        self.assertEqual(json.load(response), {"target": 1})
                finally:
                    bridge.stop()
                self.assertEqual(
                    [path for path, _ in server.calls],
                    ["/api/generate", "/api/chat", "/api/chat", "/api/chat"],
                )
                for _, payload in server.calls:
                    self.assertEqual(payload["model"], "fixture:multimodal")
                    self.assertEqual(payload["keep_alive"], "25m")
                    self.assertEqual(payload["options"]["num_ctx"], 4096)
                for _, payload in server.calls[-2:]:
                    self.assertEqual(payload["messages"][-1]["images"], [sample_image])

    def test_unavailable_model(self):
        """서버 오류가 나면 예열 실패, 빈 화면 관찰, 클릭 선택 실패로 전달된다."""
        with (
            _model_server() as (server, url),
            patch.dict(
                os.environ,
                {"LUCID_OLLAMA_URL": url, "NO_PROXY": "127.0.0.1"},
                clear=True,
            ),
        ):
            server.fail = True
            client = VisionClient()
            self.addCleanup(client.close)
            self.assertFalse(client.preload())
            self.assertEqual(client.observe("c2NyZWVu", "장면"), "")
            with self.assertRaises(HTTPError):
                client.select_click_target(
                    "c2NyZWVu", "확인", [{"번호": 1, "이름": "확인"}]
                )
