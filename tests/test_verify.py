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


class Server(unittest.TestCase):
    def test_verify_endpoint(self):
        from verify.server import handle
        status, body = handle("/v1/verify", json.dumps({"target": "pkg:pypi/jinja2@3.1.6", "result": ans("Secure", 0)}).encode(), Fake())
        self.assertEqual((status, body["label"]), (200, "verified"))
        self.assertEqual(handle("/v1/verify", b"not json", Fake())[0], 400)
        self.assertEqual(handle("/v1/verify", json.dumps({"target": "x" * 300, "result": {}}).encode(), Fake())[0], 400)
        self.assertEqual(handle("/nope", b"{}", Fake())[0], 404)


class Replay(unittest.TestCase):
    """eval/reports/2026-11-22-verified-ask.md: re-run offline from the committed evidence cache."""

    def test_published_numbers(self):
        import subprocess
        out = ROOT / "bench" / "out" / "verify-replay"
        if not (out / "sources-cache.json").exists():
            self.skipTest("no committed replay")
        tmp = Path(__import__("tempfile").mkdtemp())
        (tmp / "sources-cache.json").write_text((out / "sources-cache.json").read_text())
        subprocess.run([sys.executable, "-m", "verify.replay", str(ROOT / "bench/out/round-2"), str(ROOT / "bench/out/round-3"),
                        "--out", str(tmp), "--offline"], cwd=ROOT, check=True, capture_output=True)
        got = json.loads((tmp / "summary.json").read_text())
        self.assertEqual(got, json.loads((out / "summary.json").read_text()))
        self.assertEqual((got["wrong"], got["wrong_contradicted"], got["correct"], got["correct_contradicted"]), (87, 61, 113, 1))


if __name__ == "__main__":
    unittest.main(verbosity=1)
