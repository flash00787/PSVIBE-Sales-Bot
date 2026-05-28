#!/usr/bin/env python3
"""Health-check HTTP server (stdlib only — no Flask dependency).

Serves a lightweight /health endpoint with uptime, status, and version.
Runs in a background daemon thread so it never blocks the main bot loop.
"""
import os
import sys
import json
import time
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

_log = logging.getLogger(__name__)
_START_TIME = time.time()
_HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8080"))


def _uptime_seconds() -> float:
    return time.time() - _START_TIME


def _uptime_str() -> str:
    s = int(_uptime_seconds())
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal request handler — only GET /health returns JSON; rest → 404."""

    def log_message(self, fmt, *args):
        pass  # suppress default stderr logging

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health", "/healthz", "/"):
            self._send_json(200, {
                "status": "ok",
                "service": "psvibe-sales-bot",
                "version": "2026.05.05-r1",
                "uptime_seconds": round(_uptime_seconds(), 1),
                "uptime_human": _uptime_str(),
            })
        else:
            self._send_json(404, {"error": "not found"})

    def do_HEAD(self):
        if self.path in ("/health", "/healthz", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def keep_alive():
    """Start the health-check HTTP server in a daemon thread."""
    try:
        server = HTTPServer(("0.0.0.0", _HEALTH_PORT), HealthHandler)
        server.allow_reuse_address = True
        t = threading.Thread(target=server.serve_forever, daemon=True, name="health-server")
        t.start()
        _log.info("Health server started on port %d", _HEALTH_PORT)
    except Exception as exc:
        _log.exception("Health server failed to start: %s", exc)
        raise
