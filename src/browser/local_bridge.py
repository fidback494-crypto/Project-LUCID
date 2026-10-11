"""A token-protected localhost endpoint for the LUCID browser extension."""

import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.utils import Logger


class BrowserBridge:
    """Receives page snapshots from a browser extension on this computer only."""

    def __init__(self, store):
        self.store = store
        self.port = int(os.getenv("LUCID_BROWSER_PORT", "8765"))
        self.token = self._load_token()
        self._server = None
        self._thread = None

    @staticmethod
    def _data_directory():
        root = Path(__file__).resolve().parents[2]
        directory = Path(os.getenv("LUCID_DATA_DIR", root / "data"))
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _load_token(self):
        configured = os.getenv("LUCID_BROWSER_TOKEN", "").strip()

        if configured:
            return configured

        token_file = self._data_directory() / "browser_bridge_token.txt"

        if token_file.exists():
            return token_file.read_text(encoding="utf-8").strip()

        token = secrets.token_urlsafe(24)
        token_file.write_text(token, encoding="utf-8")
        return token

    def start(self):
        if self._server is not None:
            return

        bridge = self

        class RequestHandler(BaseHTTPRequestHandler):
            def _headers(self, status=200):
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_OPTIONS(self):
                self._headers()

            def do_POST(self):
                if self.path != "/context":
                    self._headers(404)
                    self.wfile.write(b'{"error":"not found"}')
                    return

                try:
                    length = int(self.headers.get("Content-Length", "0"))

                    if length <= 0 or length > 25000:
                        raise ValueError("invalid payload size")

                    payload = json.loads(self.rfile.read(length))

                    if not secrets.compare_digest(
                        str(payload.get("token", "")), bridge.token
                    ):
                        self._headers(403)
                        self.wfile.write(b'{"error":"invalid token"}')
                        return

                    context = bridge.store.update(
                        title=payload.get("title", ""),
                        url=payload.get("url", ""),
                        text=payload.get("text", ""),
                        selection=payload.get("selection", ""),
                    )
                    Logger.info(
                        f"[Browser] Page shared: {context.title or context.url}"
                    )
                    self._headers()
                    self.wfile.write(b'{"ok":true}')

                except (ValueError, json.JSONDecodeError):
                    self._headers(400)
                    self.wfile.write(b'{"error":"invalid request"}')

            def log_message(self, _format, *_args):
                # Browser requests are reported through LUCID's logger instead.
                return

        try:
            self._server = ThreadingHTTPServer(
                ("127.0.0.1", self.port),
                RequestHandler,
            )
        except OSError as error:
            Logger.warning(
                f"[Browser] Local bridge could not start on port {self.port}: {error}"
            )
            return

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="LUCIDBrowserBridge",
            daemon=True,
        )
        self._thread.start()
        Logger.info(f"[Browser] Local bridge started: 127.0.0.1:{self.port}")
        Logger.info(f"[Browser] Pair token: {self.token}")

    def stop(self):
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        Logger.info("[Browser] Local bridge stopped")
