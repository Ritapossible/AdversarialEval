#!/usr/bin/env python3
"""Verified Ask HTTP API (standard library only).

    python -m verify.server [--port 8402] [--cache verify-cache.json]

    POST /v1/verify  {"target": "pkg:npm/lodash@4.17.23", "result": {<the miner's SECURITY_REVIEW result>}}
      -> {"label": "verified" | "contradicted" | "unconfirmed" | "invalid" | "unchecked", "checks": [...], ...}
    GET  /healthz

A buyer (person or agent) calls a miner as usual, then posts the target and the miner's `result`
here before acting on it. Only public data is consulted (OSV, deps.dev, rubygems.org).
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core import verify
from .sources import LiveSources

MAX_BODY = 64 * 1024
MAX_TARGET = 256  # the intent's own limit on `target`


def handle(path: str, body: bytes, src) -> tuple[int, dict]:
    if path != "/v1/verify":
        return 404, {"error": "not found"}
    try:
        req = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 400, {"error": "body must be JSON"}
    target, result = (req.get("target"), req.get("result")) if isinstance(req, dict) else (None, None)
    if not isinstance(target, str) or not target or len(target.encode()) > MAX_TARGET:
        return 400, {"error": f"target must be a non-empty string of at most {MAX_TARGET} bytes"}
    return 200, verify(target, result if isinstance(result, dict) else None, src).to_dict()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8402)
    ap.add_argument("--cache", type=Path)
    a = ap.parse_args()
    src = LiveSources(a.cache)

    class H(BaseHTTPRequestHandler):
        def _send(self, status: int, obj: dict) -> None:
            data = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._send(200, {"ok": True}) if self.path == "/healthz" else self._send(404, {"error": "not found"})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self._send(413, {"error": "body too large"})
            status, obj = handle(self.path, self.rfile.read(n), src)
            self._send(status, obj)
            if a.cache:
                src.save()

    print(f"Verified Ask on http://{a.host}:{a.port}/v1/verify")
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()


if __name__ == "__main__":
    main()
