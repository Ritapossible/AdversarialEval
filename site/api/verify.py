"""Verified Ask as a Vercel serverless function: POST /api/verify.

Same contract as `python -m verify.server` (see verify/README.md):
    POST /api/verify  Authorization: Bearer <VERIFY_TOKEN>
         {"target": "pkg:npm/minimist@1.2.5", "result": {<miner result>}, "strict_count": false}
    GET  /api/verify  -> {"ok": true, "configured": <bool>}

It refuses every POST until VERIFY_TOKEN is set in the Vercel project's environment variables,
so a fresh deploy is never an open proxy. Rate limiting is per function instance (best effort).
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify.server import CACHE_MAX_AGE, MAX_BODY, RateLimiter, authorized, client_ip, handle  # noqa: E402
from _verify.sources import LiveSources  # noqa: E402

SRC = LiveSources(None, timeout=6, max_age=CACHE_MAX_AGE, max_entries=5_000)
LIMITER = RateLimiter(int(os.environ.get("VERIFY_RATE_PER_MIN", "60")))


class handler(BaseHTTPRequestHandler):  # Vercel's Python runtime looks for this name
    def _send(self, status: int, obj: dict) -> None:
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, {"ok": True, "service": "verified-ask", "configured": bool(os.environ.get("VERIFY_TOKEN"))})

    def do_POST(self):
        token = os.environ.get("VERIFY_TOKEN")
        if not token:
            return self._send(503, {"error": "not configured: set VERIFY_TOKEN in the deployment"})
        client = client_ip(self.headers, self.client_address[0])
        if not LIMITER.allow(client):  # before the token check, so guessing is limited too
            return self._send(429, {"error": "rate limit exceeded"})
        if not authorized(self.headers.get("Authorization"), token):
            return self._send(401, {"error": "missing or wrong bearer token"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"error": "bad Content-Length"})
        if n > MAX_BODY or n < 0:
            return self._send(413, {"error": "body too large"})
        status, obj = handle("/v1/verify", self.rfile.read(n), SRC)
        self._send(status, obj)

    def log_message(self, *args):  # keep request bodies out of logs
        pass
