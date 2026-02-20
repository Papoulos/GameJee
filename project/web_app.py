from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from main import Orchestrator

HOST = "0.0.0.0"
PORT = 8000


class WebHandler(BaseHTTPRequestHandler):
    orchestrator = Orchestrator(Path(__file__).resolve().parent)
    index_path = Path(__file__).resolve().parent / "web" / "index.html"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self.send_error(404, "Not found")
            return
        html = self.index_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/action":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"status": "error", "message": "Invalid JSON body."}, status=400)
            return

        action = str(data.get("action", ""))
        confirm_reset = bool(data.get("confirm_reset", False))
        result = self.orchestrator.handle_action(action, confirm_reset=confirm_reset)
        self._send_json(result)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), WebHandler)
    print(f"Web UI available on http://{HOST}:{PORT}")
    server.serve_forever()
