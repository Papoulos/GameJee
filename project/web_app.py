from __future__ import annotations

import importlib
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from import_content import import_content

HOST = "0.0.0.0"
PORT = 8000
PROJECT_ROOT = Path(__file__).resolve().parent


def build_orchestrator():
    """Import orchestrator safely to provide actionable diagnostics on broken local merges."""
    try:
        main_module = importlib.import_module("main")
    except (IndentationError, SyntaxError) as exc:
        print("Failed to import main.py (syntax/indentation error).")
        print(f"Details: {exc}")
        print("Run from project/: python3 -m py_compile main.py")
        print("If it fails, resolve merge markers or re-sync main.py from GitHub.")
        sys.exit(1)
    except ModuleNotFoundError as exc:
        print(f"Module import error: {exc}")
        print("Run this script from the project/ directory: python3 web_app.py")
        sys.exit(1)

    return main_module.Orchestrator(PROJECT_ROOT)


class WebHandler(BaseHTTPRequestHandler):
    orchestrator = build_orchestrator()
    index_path = PROJECT_ROOT / "web" / "index.html"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON body.") from exc

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
        if self.path == "/api/action":
            self._handle_action()
            return
        if self.path == "/api/import":
            self._handle_import()
            return
        self.send_error(404, "Not found")

    def _handle_action(self) -> None:
        try:
            data = self._read_json_body()
        except ValueError as exc:
            self._send_json({"status": "error", "message": str(exc)}, status=400)
            return

        action = str(data.get("action", ""))
        confirm_reset = bool(data.get("confirm_reset", False))
        result = self.orchestrator.handle_action(action, confirm_reset=confirm_reset)
        self._send_json(result)

    def _handle_import(self) -> None:
        try:
            data = self._read_json_body()
        except ValueError as exc:
            self._send_json({"status": "error", "message": str(exc)}, status=400)
            return

        content_type = str(data.get("type", "")).strip().lower()
        source = str(data.get("source", "")).strip()
        title = str(data.get("title", "")).strip() or None

        if content_type not in {"rules", "scenario"}:
            self._send_json({"status": "error", "message": "Le type doit être 'rules' ou 'scenario'."}, status=400)
            return
        if not source:
            self._send_json({"status": "error", "message": "Le chemin du document est requis."}, status=400)
            return

        try:
            source_path = Path(source).expanduser().resolve()
            if not source_path.exists():
                raise FileNotFoundError(f"Source introuvable: {source_path}")
            # Ensure runtime state exists before import (bootstraps from template when missing).
            self.orchestrator.memory.load()
            cached_path = import_content(PROJECT_ROOT, source_path, content_type, title)
        except Exception as exc:  # noqa: BLE001 - user-facing API needs message
            self._send_json({"status": "error", "message": str(exc)}, status=400)
            return

        self._send_json(
            {
                "status": "ok",
                "message": f"Document importé ({content_type}) : {cached_path}",
                "cached_text": str(cached_path),
            }
        )


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), WebHandler)
    print(f"Web UI available on http://{HOST}:{PORT}")
    server.serve_forever()
