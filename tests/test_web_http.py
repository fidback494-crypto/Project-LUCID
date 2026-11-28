"""실제 루프백 HTTP 연결로 웹 화면, 대화 API, 요청 검사를 확인한다."""

import json
import unittest
from http.client import HTTPConnection
from threading import Thread
from unittest.mock import Mock

from lucid.web import ChatServer


class WebHTTPTests(unittest.TestCase):
    """독립적인 엔진 대역을 사용해 HTTP 응답을 검사한다."""

    def setUp(self):
        """빈 포트에 서버를 시작하고 테스트 종료 시 소켓을 해제한다."""
        self.session = Mock()
        self.server = ChatServer(0, self.session)
        self.addCleanup(self.server.server_close)
        thread = Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}
        )
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None, headers=None):
        """요청 하나를 전송하고 상태 코드, 응답 헤더, UTF-8 본문을 반환한다."""
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, response.headers, response.read().decode()
        finally:
            conn.close()

    def test_html_and_local_assets(self):
        """별도 설치 없이 대화 HTML과 그 페이지에 연결된 스크립트와 스타일을 제공한다."""
        code, headers, html = self.request("GET", "/")
        self.assertEqual(code, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for resource, mime in (("/style.css", "text/css"), ("/app.js", "javascript")):
            with self.subTest(resource=resource):
                self.assertIn(resource, html)
                code, headers, source = self.request("GET", resource)
                self.assertEqual(code, 200)
                self.assertIn(mime, headers["Content-Type"])
                self.assertTrue(source.strip())
        self.assertEqual(self.request("GET", "/main.py")[0], 404)

    def test_state_and_submission(self):
        """조회 커서를 전달하고 한 번만 수락된 메시지에 202를 반환한다."""
        self.session.snapshot.return_value = {
            "events": [],
            "cursor": 3,
            "status": "ready",
        }
        code, headers, body = self.request("GET", "/api/state?after=3")
        self.assertEqual(code, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(body)["cursor"], 3)
        self.session.snapshot.assert_called_once_with(3)
        headers = {
            "Content-Type": "application/json",
            "X-Lucid-Client": "web",
            "Origin": f"http://127.0.0.1:{self.server.server_port}",
        }
        message = json.dumps({"text": "  안녕  "})
        self.session.submit.return_value = True
        self.assertEqual(self.request("POST", "/api/message", message, headers)[0], 202)
        self.session.submit.assert_called_once_with("안녕")
        self.session.submit.return_value = False
        self.assertEqual(self.request("POST", "/api/message", message, headers)[0], 409)

    def test_invalid_requests_do_not_enqueue_messages(self):
        """다른 출처, 누락된 전용 헤더, 잘못된 입력은 엔진에 전달하지 않는다."""
        valid = {"Content-Type": "application/json", "X-Lucid-Client": "web"}
        payload = json.dumps({"text": "test"})
        for headers, body, status in (
            ({**valid, "Origin": "https://other.example"}, payload, 403),
            ({"Content-Type": "application/json"}, payload, 403),
            ({**valid, "Content-Type": "text/plain"}, payload, 415),
            (valid, "{}", 400),
            (valid, "{", 400),
            (valid, json.dumps({"text": "x" * 8001}), 400),
        ):
            with self.subTest(status=status, headers=headers):
                self.assertEqual(
                    self.request("POST", "/api/message", body, headers)[0], status
                )
        self.session.submit.assert_not_called()
        self.assertEqual(
            self.request("GET", "/api/state", headers={"Host": "other.example"})[0], 403
        )
        self.assertEqual(self.request("GET", "/api/state?after=invalid")[0], 400)
