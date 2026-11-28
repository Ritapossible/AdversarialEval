"""Dependency.Guard as a Vercel serverless function: POST /api/guard.

    POST /api/guard  Authorization: Bearer <GUARD_TOKEN>   {"target": "pkg:npm/minimist@1.2.5"}
      -> {"decision": "PASS"|"BLOCK"|"FLAG", "reason", "check", "answer": {verdict, vulnerability_count,
          advisory_ids}, "osv_ids", "cost_usd", "receipt", "provider"}
    GET  /api/guard  -> {"ok": true, "configured": <bool>}

The Anjoman key lives only in this deployment's environment (ANJOMAN_API_KEY), so the Mind never
holds it, and the reply carries no miner free text. It refuses every POST until both GUARD_TOKEN and
ANJOMAN_API_KEY are set. One paid ask per request; GUARD_MAX_USD_PER_DAY caps spend per instance
(default $0.50), and the Anjoman balance is the hard cap.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify.guard import Budget, guard  # noqa: E402
from _verify.server import CACHE_MAX_AGE, MAX_BODY, RateLimiter, authorized, client_ip  # noqa: E402
from _verify.sources import LiveSources  # noqa: E402

SRC = LiveSources(None, timeout=6, max_age=CACHE_MAX_AGE, max_entries=5_000)
LIMITER = RateLimiter(int(os.environ.get("GUARD_RATE_PER_MIN", "10")))
BUDGET = Budget(float(os.environ.get("GUARD_MAX_USD_PER_DAY", "0.50")))


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
        self._send(200, {"ok": True, "service": "dependency-guard",
                         "configured": bool(os.environ.get("GUARD_TOKEN") and os.environ.get("ANJOMAN_API_KEY"))})

    def do_POST(self):
        token, key = os.environ.get("GUARD_TOKEN"), os.environ.get("ANJOMAN_API_KEY")
        if not token or not key:
            return self._send(503, {"error": "not configured: set GUARD_TOKEN and ANJOMAN_API_KEY in the deployment"})
        if not LIMITER.allow(client_ip(self.headers, self.client_address[0])):
            return self._send(429, {"error": "rate limit exceeded"})
        if not authorized(self.headers.get("Authorization"), token):
            return self._send(401, {"error": "missing or wrong bearer token"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"error": "bad Content-Length"})
        if n > MAX_BODY or n < 0:
            return self._send(413, {"error": "body too large"})
        status, obj = guard(self.rfile.read(n), SRC, BUDGET, key=key)
        self._send(status, obj)

    def log_message(self, *args):  # keep request bodies out of logs
        pass
