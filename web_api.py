"""Small dependency-free HTTP API for the local shared-screen web client."""

from __future__ import annotations

import argparse
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from web_game import WebGameError, WebGameSession


class GameAPI:
    def __init__(self):
        self.lock = threading.RLock()
        self.session = WebGameSession()

    def dispatch(self, method, path, payload):
        with self.lock:
            if method == "GET" and path == "/api/state":
                return self.session.state()
            if method == "GET" and path == "/api/health":
                return {"ok": True}
            if method == "POST" and path == "/api/new-game":
                self.session = WebGameSession(
                    payload.get("p1_name", "Player 1"),
                    payload.get("p2_name", "Player 2"),
                    seed=payload.get("seed"),
                )
                return self.session.state()
            if method == "POST" and path == "/api/begin-step":
                return self.session.begin_step(
                    foreteller_indices=payload.get("foreteller_indices", ()),
                    barrier_indices=payload.get("barrier_indices", {}),
                )
            if method == "POST" and path == "/api/open":
                return self.session.open_card(
                    payload.get("index"),
                    discard_indices=payload.get("discard_indices", ()),
                )
            if method == "POST" and path == "/api/play-magic":
                return self.session.play_magic(payload.get("hand_index"), payload.get("choices"))
            if method == "POST" and path == "/api/activate-figure":
                return self.session.activate_figure()
            if method == "POST" and path == "/api/continue-turn":
                return self.session.continue_turn()
            raise WebGameError("unknown API route", code="not_found")


API = GameAPI()


class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    """Fail fast instead of letting two game cores share port 8000 on Windows."""

    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    server_version = "FiveByFive/0.1"

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def _handle(self, method):
        try:
            payload = self._read_json() if method == "POST" else {}
            result = API.dispatch(method, urlparse(self.path).path, payload)
            self._send_json(200, result)
        except WebGameError as error:
            status = 404 if error.code == "not_found" else 400
            self._send_json(status, {"error": str(error), "code": error.code, "details": error.details})
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            self._send_json(400, {"error": str(error), "code": "bad_request", "details": {}})
        except Exception:
            self._send_json(500, {"error": "internal server error", "code": "internal_error", "details": {}})

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise TypeError("request body must be a JSON object")
        return data

    def _send_json(self, status, body):
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _cors_headers(self):
        origin = self.headers.get("Origin", "")
        if origin in {"http://localhost:3000", "http://127.0.0.1:3000"}:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        print(f"[web-api] {self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Run the local Five by Five game API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    server = ExclusiveThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Five by Five API: http://{args.host}:{args.port}/api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
