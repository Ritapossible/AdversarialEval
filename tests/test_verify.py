#!/usr/bin/env python3
"""Offline tests for Verified Ask (verify/). No network: sources are faked.

    python tests/test_verify.py
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify import cited_ids, parse_target, verify  # noqa: E402
from verify.core import Package  # noqa: E402

JINJA = {"id": "GHSA-cpwx-vrp4-4pq7", "aliases": ["CVE-2025-27516"],
         "affected": [{"package": {"ecosystem": "PyPI", "name": "jinja2"}}]}
JINJA_OLD = {"id": "GHSA-h5c8-rqwp-cp95", "aliases": ["CVE-2024-22195"],
             "affected": [{"package": {"ecosystem": "PyPI", "name": "jinja2"}}]}
CRYPTO = {"id": "GO-2026-5932", "affected": [{"package": {"ecosystem": "Go", "name": "golang.org/x/crypto"}}]}


class Fake:
    """jinja2 3.1.5 has one advisory, 3.1.6 none, 99.0.0 doesn't exist."""
    def __init__(self, up=True):
        self.up = up

    def osv_query(self, pkg):
        if not self.up:
            return None
        return [JINJA] if (pkg.name, pkg.version) == ("jinja2", "3.1.5") else []

    def osv_vuln(self, vid):
        if not self.up:
            return None
        return {r["id"].upper(): r for r in (JINJA, JINJA_OLD, CRYPTO)}.get(vid, False)

    def version_exists(self, pkg):
        return None if not self.up else pkg.version != "99.0.0"


def ans(verdict, count, issues=(), summary=""):
    return {"verdict": verdict, "vulnerability_count": count, "issues": list(issues), "summary": summary}


def failed(v):
    return [c.name for c in v.checks if c.status == "fail"]


class Parse(unittest.TestCase):
    def test_forms(self):
        want = Package("pypi", "jinja2", "3.1.5")
        self.assertEqual(parse_target("pkg:pypi/jinja2@3.1.5"), want)
        self.assertEqual(parse_target("jinja2 3.1.5 (PyPI)"), want)
        self.assertEqual(parse_target("Is jinja2 version 3.1.5 from PyPI affected by known vulnerabilities?"), want)
        self.assertEqual(parse_target("pkg:maven/org.yaml/snakeyaml@1.9"), Package("maven", "org.yaml:snakeyaml", "1.9"))
        self.assertEqual(parse_target("pkg:golang/github.com/gin-gonic/gin@v1.5.0"), Package("golang", "github.com/gin-gonic/gin", "1.5.0"))
        self.assertEqual(parse_target("pkg:pypi/Jinja_2@1"), Package("pypi", "jinja-2", "1"))
        self.assertIsNone(parse_target("def f(x): return eval(x)"))
        self.assertIsNone(parse_target("pkg:unknowntype/x@1"))

    def test_cited_ids(self):
        ids, ph = cited_ids(ans("Insecure", 1, ["CVE‑2025‑27516 (ghsa-cpwx-vrp4-4pq7)", "CWE-79"], "see CVE-2020-..."))
        self.assertEqual(ids, ["CVE-2025-27516", "GHSA-CPWX-VRP4-4PQ7"])  # CWE is a class, not an advisory
        self.assertEqual(ph, ["CVE-2020-..."])


class Labels(unittest.TestCase):
    def test_verified(self):
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, ["CVE-2025-27516"]), Fake())
        self.assertEqual(v.label, "verified")
        v = verify("pkg:pypi/jinja2@3.1.6", ans("Secure", 0), Fake())
        self.assertEqual(v.label, "verified")

    def test_count_mismatch_is_info_only(self):
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 3), Fake())
        self.assertEqual(v.label, "verified")
        self.assertIn("info", [c.status for c in v.checks])

    def test_missed_and_false_alarm(self):
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Secure", 0), Fake())
        self.assertEqual((v.label, failed(v)), ("contradicted", ["verdict"]))
        v = verify("pkg:pypi/jinja2@3.1.6", ans("Insecure", 1), Fake())
        self.assertEqual((v.label, failed(v)), ("contradicted", ["verdict"]))

    def test_fields_disagree(self):
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 0), Fake())
        self.assertIn("fields", failed(v))
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", None), Fake())
        self.assertEqual(v.label, "unconfirmed")

    def test_citations(self):
        f = Fake()
        # invented id in a namespace OSV mirrors fully
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, ["GHSA-2222-3333-4444"]), f)
        self.assertEqual((v.label, failed(v)), ("contradicted", ["citation"]))
        # real advisory, other package
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, ["GO-2026-5932"]), f)
        self.assertIn("not jinja2", [c.detail for c in v.checks if c.status == "fail"][0])
        # real advisory, right package, wrong version
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, ["GHSA-h5c8-rqwp-cp95"]), f)
        self.assertIn("not version 3.1.5", [c.detail for c in v.checks if c.status == "fail"][0])
        # unknown CVE: OSV lacks some CVEs, so only a warning
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, ["CVE-2026-99999"]), f)
        self.assertEqual(v.label, "unconfirmed")
        # placeholder
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, [], "a flaw (CVE-2020-...)"), f)
        self.assertEqual(v.label, "contradicted")

    def test_unpublished_version(self):
        v = verify("pkg:pypi/jinja2@99.0.0", ans("Secure", 0), Fake())
        self.assertEqual((v.label, failed(v)), ("contradicted", ["exists"]))

    def test_invalid_and_unchecked(self):
        self.assertEqual(verify("pkg:pypi/jinja2@3.1.5", ans(None, 2, ["CVE-2025-27516"]), Fake()).label, "invalid")
        self.assertEqual(verify("pkg:pypi/jinja2@3.1.5", None, Fake()).label, "invalid")
        self.assertEqual(verify("query = 'SELECT ' + x", ans("Insecure", 1), Fake()).label, "unchecked")

    def test_sources_down_never_verifies(self):
        v = verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1, ["CVE-2025-27516"]), Fake(up=False))
        self.assertEqual(v.label, "unconfirmed")


class StrictCount(unittest.TestCase):
    def test_strict_count(self):
        twins = [JINJA, {"id": "PYSEC-2026-1471", "aliases": ["CVE-2025-27516"],
                         "affected": [{"package": {"ecosystem": "PyPI", "name": "jinja2"}}]}]
        f = Fake()
        f.osv_query = lambda pkg: twins
        # two OSV records for one vulnerability: 1 and 2 are both right
        self.assertEqual(verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 1), f, strict_count=True).label, "verified")
        self.assertEqual(verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 2), f, strict_count=True).label, "verified")
        self.assertEqual(verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 5), f, strict_count=True).label, "unconfirmed")
        self.assertEqual(verify("pkg:pypi/jinja2@3.1.5", ans("Insecure", 5), f).label, "verified")  # default: info only


class Hardening(unittest.TestCase):
    def test_token(self):
        from verify.server import authorized
        self.assertTrue(authorized(None, None))
        self.assertTrue(authorized("Bearer s3cret", "s3cret"))
        self.assertFalse(authorized("Bearer wrong", "s3cret"))
        self.assertFalse(authorized(None, "s3cret"))

    def test_rate_limit(self):
        from verify.server import RateLimiter
        r = RateLimiter(2)
        self.assertEqual([r.allow("a", 0), r.allow("a", 1), r.allow("a", 2), r.allow("b", 2)], [True, True, False, True])
        self.assertTrue(r.allow("a", 61))  # next minute

    def test_public_bind_needs_token(self):
        import os
        import subprocess
        env = {k: v for k, v in os.environ.items() if k != "VERIFY_TOKEN"}
        p = subprocess.run([sys.executable, "-m", "verify.server", "--host", "0.0.0.0", "--port", "0"],
                           cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("refusing", p.stderr)

    def test_atomic_cache(self):
        import tempfile
        from verify.sources import LiveSources
        d = Path(tempfile.mkdtemp())
        s = LiveSources(d / "c.json", offline=True)
        s.cache["k"] = {"status": 200, "json": [1]}
        s.save()
        self.assertEqual(json.loads((d / "c.json").read_text())["k"]["json"], [1])
        self.assertEqual([p.name for p in d.iterdir()], ["c.json"])  # no temp file left behind


class Server(unittest.TestCase):
    def test_verify_endpoint(self):
        from verify.server import handle
        status, body = handle("/v1/verify", json.dumps({"target": "pkg:pypi/jinja2@3.1.6", "result": ans("Secure", 0)}).encode(), Fake())
        self.assertEqual((status, body["label"]), (200, "verified"))
        self.assertEqual(handle("/v1/verify", b"not json", Fake())[0], 400)
        self.assertEqual(handle("/v1/verify", json.dumps({"target": "x" * 300, "result": {}}).encode(), Fake())[0], 400)
        self.assertEqual(handle("/nope", b"{}", Fake())[0], 404)
        self.assertEqual(handle("/v1/verify", b"[1]", Fake())[0], 400)
        self.assertEqual(handle("/v1/verify", json.dumps({"target": "pkg:pypi/jinja2@3.1.6", "strict_count": "yes"}).encode(), Fake())[0], 400)


class VercelFunction(unittest.TestCase):
    """site/api/verify.py: the hosted endpoint the Mind calls."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        import os
        import threading
        from http.server import ThreadingHTTPServer
        spec = importlib.util.spec_from_file_location("site_verify", ROOT / "site" / "api" / "verify.py")
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)
        cls.mod.SRC = Fake()  # offline
        cls.os = os
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/api/verify"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def call(self, body=None, token=None):
        import urllib.error
        import urllib.request
        h = {"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})}
        req = urllib.request.Request(self.url, data=None if body is None else json.dumps(body).encode(), headers=h)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_refuses_until_configured_then_needs_token(self):
        body = {"target": "pkg:pypi/jinja2@3.1.6", "result": ans("Secure", 0)}
        self.os.environ.pop("VERIFY_TOKEN", None)
        self.assertEqual(self.call(body)[0], 503)
        self.assertEqual(self.call()[1]["configured"], False)  # GET
        self.os.environ["VERIFY_TOKEN"] = "t"
        try:
            self.assertEqual(self.call(body)[0], 401)
            self.assertEqual(self.call(body, "wrong")[0], 401)
            status, out = self.call(body, "t")
            self.assertEqual((status, out["label"]), (200, "verified"))
        finally:
            self.os.environ.pop("VERIFY_TOKEN", None)

    def test_copy_in_sync(self):
        import subprocess
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_site_api.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


class Replay(unittest.TestCase):
    """eval/reports/2026-11-22-verified-ask.md (rounds 2 to 4): re-run offline from the committed evidence cache."""

    def test_published_numbers(self):
        import subprocess
        out = ROOT / "bench" / "out" / "verify-replay"
        if not (out / "sources-cache.json").exists():
            self.skipTest("no committed replay")
        tmp = Path(__import__("tempfile").mkdtemp())
        (tmp / "sources-cache.json").write_text((out / "sources-cache.json").read_text())
        subprocess.run([sys.executable, "-m", "verify.replay", str(ROOT / "bench/out/round-2"), str(ROOT / "bench/out/round-3"),
                        str(ROOT / "bench/out/round-4"), "--out", str(tmp), "--offline"], cwd=ROOT, check=True, capture_output=True)
        got = json.loads((tmp / "summary.json").read_text())
        self.assertEqual(got, json.loads((out / "summary.json").read_text()))
        self.assertEqual((got["wrong"], got["wrong_contradicted"], got["correct"], got["correct_contradicted"]), (142, 95, 222, 2))
        self.assertEqual(got["wrong_labels"].get("verified", 0), 0)  # the headline claim


if __name__ == "__main__":
    unittest.main(verbosity=1)
