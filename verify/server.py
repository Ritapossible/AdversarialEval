#!/usr/bin/env python3
"""Verified Ask HTTP API (standard library only).

    VERIFY_TOKEN=<secret> python -m verify.server [--host 127.0.0.1] [--port 8402] [--cache verify-cache.json]

    POST /v1/verify  {"target": "pkg:npm/lodash@4.17.23", "result": {<the miner's SECURITY_REVIEW result>},
                      "strict_count": false}
      -> {"label": "verified" | "contradicted" | "unconfirmed" | "invalid" | "unchecked", "checks": [...], ...}
    GET  /healthz

A buyer (person or agent) calls a miner as usual, then posts the target and the miner's `result`
here before acting on it. Only public data is consulted (OSV, deps.dev, rubygems.org).

Exposure rules (it makes outbound calls for its callers, so it must not become an open proxy):
- Bound to anything other than loopback, it refuses to start unless VERIFY_TOKEN is set; every
  request must then send `Authorization: Bearer <token>`.
- Each client address gets --rate requests per minute (default 60), counted before the token check
  so guessing is limited too; beyond that, 429.
- A connection that stalls for 15 s is dropped, and at most --max-threads requests run at once
  (others get 503), so slow clients can't exhaust the server.
- Upstream calls are capped at 8 at once. Answers are cached for an hour (a new advisory shows up
  within that), at most 20,000 entries.
"""
from __future__ import annotations

import argparse
import hmac
import ipaddress
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core import verify
from .sources import LiveSources

MAX_BODY = 64 * 1024
MAX_TARGET = 256  # the intent's own limit on `target`
CACHE_MAX_AGE = 3600  # seconds; fresh enough for a daily watch, light on OSV
CACHE_MAX_ENTRIES = 20_000
SOCKET_TIMEOUT = 15


def handle(path: str, body: bytes, src) -> tuple[int, dict]:
    if path != "/v1/verify":
        return 404, {"error": "not found"}
    try:
        req = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 400, {"error": "body must be JSON"}
    if not isinstance(req, dict):
        return 400, {"error": "body must be a JSON object"}
    target, result = req.get("target"), req.get("result")
    if not isinstance(target, str) or not target or len(target.encode()) > MAX_TARGET:
        return 400, {"error": f"target must be a non-empty string of at most {MAX_TARGET} bytes"}
    strict = req.get("strict_count", False)
    if not isinstance(strict, bool):
        return 400, {"error": "strict_count must be true or false"}
    return 200, verify(target, result if isinstance(result, dict) else None, src, strict_count=strict).to_dict()


def authorized(header: str | None, token: str | None) -> bool:
    if not token:
        return True
    want = f"Bearer {token}"
    return isinstance(header, str) and hmac.compare_digest(header.encode(), want.encode())


class RateLimiter:
    """Fixed one-minute window per client address."""

    def __init__(self, per_minute: int):
        self.per_minute, self.hits, self.lock = per_minute, {}, threading.Lock()

    def allow(self, client: str, now: float | None = None) -> bool:
        window = int((now if now is not None else time.time()) // 60)
        with self.lock:
            w, n = self.hits.get(client, (window, 0))
            if w != window:
                w, n = window, 0
            if n >= self.per_minute:
                return False
            self.hits[client] = (w, n + 1)
            if len(self.hits) > 10_000:  # forget old windows
                self.hits = {k: v for k, v in self.hits.items() if v[0] == window}
            return True


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8402)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--rate", type=int, default=60, help="requests per minute per client address")
    ap.add_argument("--max-threads", type=int, default=32, help="requests handled at once")
    a = ap.parse_args()
    token = os.environ.get("VERIFY_TOKEN") or None
    if not is_loopback(a.host) and not token:
        raise SystemExit(f"refusing to listen on {a.host} without VERIFY_TOKEN: it would be an open proxy to OSV and deps.dev")
    src = LiveSources(a.cache, max_age=CACHE_MAX_AGE, max_entries=CACHE_MAX_ENTRIES)
    slots = threading.BoundedSemaphore(a.max_threads)
    limiter = RateLimiter(a.rate)
    last_save = [time.time()]

    class H(BaseHTTPRequestHandler):
        timeout = SOCKET_TIMEOUT  # applied to the socket: a stalled client is dropped

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
            if not slots.acquire(blocking=False):
                return self._send(503, {"error": "busy, try again"})
            try:
                self._post()
            finally:
                slots.release()

        def _post(self):
            if not limiter.allow(self.client_address[0]):
                return self._send(429, {"error": f"over {a.rate} requests per minute"})
            if not authorized(self.headers.get("Authorization"), token):
                return self._send(401, {"error": "missing or wrong bearer token"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._send(400, {"error": "bad Content-Length"})
            if n > MAX_BODY or n < 0:
                return self._send(413, {"error": "body too large"})
            try:
                body = self.rfile.read(n)
            except TimeoutError:
                return self._send(408, {"error": "body not received in time"})
            status, obj = handle(self.path, body, src)
            self._send(status, obj)
            if a.cache and time.time() - last_save[0] > 30:  # the cache is MBs: save at most twice a minute
                last_save[0] = time.time()
                src.save()

    print(f"Verified Ask on http://{a.host}:{a.port}/v1/verify" + (" (token required)" if token else ""))
    try:
        ThreadingHTTPServer((a.host, a.port), H).serve_forever()
    finally:
        if a.cache:
            src.save()


if __name__ == "__main__":
    main()
