"""Live public sources for Verified Ask: OSV, deps.dev and rubygems.org. All free, no key.

Every response is cached, keyed by request. A replay keeps the cache forever in a JSON file so it
can be re-run offline with exactly the same evidence (pass `offline=True`). A live service passes
`max_age` and `max_entries`, so answers are refreshed (a new advisory shows up within `max_age`)
and memory stays bounded. Network errors return None ("unavailable"), never a guess.
"""
from __future__ import annotations

import json
import os
import ssl
import tempfile
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .core import Package

OSV = "https://api.osv.dev/v1"
DEPS_DEV = "https://api.deps.dev/v3/systems"
_DEPS_SYSTEM = {"pypi": "pypi", "npm": "npm", "maven": "maven", "golang": "go", "cargo": "cargo"}


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ca = os.environ.get("SSL_CERT_FILE")
    if ca and Path(ca).exists():
        ctx.load_verify_locations(ca)
    return ctx


class LiveSources:
    def __init__(self, cache_path: Path | None = None, offline: bool = False, timeout: float = 30, max_upstream: int = 8,
                 max_age: float | None = None, max_entries: int | None = None):
        self.cache_path, self.offline, self.timeout = cache_path, offline, timeout
        self.max_age, self.max_entries = max_age, max_entries
        self.cache: dict[str, dict] = json.loads(cache_path.read_text()) if cache_path and cache_path.exists() else {}
        self._lock = threading.Lock()
        self._upstream = threading.BoundedSemaphore(max_upstream)  # never more than this many calls to OSV etc. at once
        self._ctx = _ssl_context()

    def save(self) -> None:
        """Atomic: write a temp file next to the cache, then rename over it, so a crash can't corrupt it."""
        if not self.cache_path:
            return
        with self._lock:
            data = json.dumps(self.cache, indent=0, sort_keys=True) + "\n"
        fd, tmp = tempfile.mkstemp(dir=self.cache_path.parent, prefix=self.cache_path.name + ".")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(data)
            os.replace(tmp, self.cache_path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def _get(self, url: str, body: dict | None = None, reduce=None, tag: str = "") -> tuple[int, object] | None:
        """(status, parsed JSON) or None when unavailable. 404 is an answer, not an error.
        reduce: keep only what the caller needs from a large body (it is what gets cached)."""
        key = tag + url + (" " + json.dumps(body, sort_keys=True) if body else "")
        with self._lock:
            c = self.cache.get(key)
            if c is not None and (self.max_age is None or time.time() - c.get("at", 0) <= self.max_age):
                return c["status"], c["json"]
        if self.offline:
            return None
        req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                     headers={"Content-Type": "application/json", "User-Agent": "verified-ask/0.1"})
        try:
            with self._upstream, urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as r:
                data = json.loads(r.read() or b"null")
                out = (r.status, reduce(data) if reduce else data)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                return None
            out = (404, None)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None
        with self._lock:
            entry = {"status": out[0], "json": out[1]}
            if self.max_age is not None:
                entry["at"] = time.time()
            self.cache.pop(key, None)
            self.cache[key] = entry  # dicts keep insertion order: oldest first
            if self.max_entries is not None:
                while len(self.cache) > self.max_entries:
                    self.cache.pop(next(iter(self.cache)))
        return out

    def osv_query(self, pkg: Package) -> list[dict] | None:
        body: dict = {"package": {"ecosystem": pkg.ecosystem, "name": pkg.name}, "version": pkg.version}
        vulns: list[dict] = []
        for _ in range(20):  # OSV pages long answers; follow next_page_token
            r = self._get(f"{OSV}/query", body)
            if r is None or r[0] != 200:
                return None
            vulns += (r[1] or {}).get("vulns", [])
            token = (r[1] or {}).get("next_page_token")
            if not token:
                return vulns
            body = {**body, "page_token": token}
        return None  # unreasonably many pages: don't guess

    def osv_vuln(self, vid: str) -> dict | None | bool:
        r = self._get(f"{OSV}/vulns/{urllib.parse.quote(vid)}")
        if r is None:
            return None
        return False if r[0] == 404 else r[1]

    def version_exists(self, pkg: Package) -> bool | None:
        if pkg.purl_type == "gem":
            r = self._get(f"https://rubygems.org/api/v1/versions/{urllib.parse.quote(pkg.name)}.json")
            if r is None:
                return None
            return r[0] == 200 and any(x.get("number") == pkg.version for x in r[1] or [])
        system = _DEPS_SYSTEM.get(pkg.purl_type)
        if not system:
            return None
        ver = "v" + pkg.version if pkg.purl_type == "golang" else pkg.version
        r = self._get(f"{DEPS_DEV}/{system}/packages/{urllib.parse.quote(pkg.name, safe='')}/versions/{urllib.parse.quote(ver, safe='')}")
        if r is None:
            return None
        if r[0] == 200:
            return True
        if pkg.purl_type == "pypi":  # "2.0" and "2.0.0" are the same PyPI version; deps.dev wants the exact spelling
            want = _pep440_key(pkg.version)
            p = self._get(f"https://pypi.org/pypi/{urllib.parse.quote(pkg.name)}/json", tag="pypi-releases ",
                          reduce=lambda d: sorted((d or {}).get("releases", {})))
            if p is None:
                return None
            return p[0] == 200 and any(_pep440_key(x) == want for x in p[1] or [])
        return False

    def was_published(self, pkg: Package) -> bool | None:
        """Was this version ever published, even if withdrawn since? Only npm keeps that history
        (its `time` field keeps unpublished versions). Elsewhere: None, can't tell."""
        if pkg.purl_type != "npm":
            return None
        r = self._get(f"https://registry.npmjs.org/{urllib.parse.quote(pkg.name, safe='@')}", tag="npm-history ",
                      reduce=lambda d: sorted(k for k in ((d or {}).get("time") or {}) if k not in ("created", "modified")))
        if r is None:
            return None
        return r[0] == 200 and pkg.version in (r[1] or [])


def _pep440_key(v: str) -> str:
    """Enough of PEP 440 normalisation to match spellings: case, a leading v, trailing .0 in the release."""
    v = v.strip().lower().lstrip("v")
    m = re.match(r"^(\d+(?:\.\d+)*)(.*)$", v)
    if not m:
        return v
    parts = m.group(1).split(".")
    while len(parts) > 1 and int(parts[-1]) == 0:
        parts.pop()
    return ".".join(str(int(x)) for x in parts) + m.group(2)
