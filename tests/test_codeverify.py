#!/usr/bin/env python3
"""Offline tests for codeverify/ (no model, no installs, no network).

    python tests/test_codeverify.py
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codeverify"))
from checks import parse_requirements, third_party_imports  # noqa: E402
from generate import blocks, parse_decision  # noqa: E402
from score import wilson  # noqa: E402

F = "`" * 3


class Blocks(unittest.TestCase):
    def test_label_line_then_block(self):  # the layout Qwen's first reply used (amendment 1)
        text = f"1. {F}requirements.txt{F}\n{F}\npyyaml==6.0\n{F}\n\n2. {F}python\nimport yaml\n{F}\n"
        self.assertEqual(blocks(text), ("pyyaml==6.0", "import yaml\n"))

    def test_plain_layout_and_empty_requirements(self):
        self.assertEqual(blocks(f"{F}requirements.txt\n\n{F}\n{F}python\nx = 1\n{F}"), ("", "x = 1\n"))
        self.assertEqual(blocks(f"{F}txt\nrequests==2.32.4\n{F}\n{F}python\nimport requests\n{F}"), ("requests==2.32.4", "import requests\n"))

    def test_no_code(self):
        self.assertEqual(blocks("Sorry, I can't help with that."), ("", None))


class Parsing(unittest.TestCase):
    def test_requirements(self):
        rs = parse_requirements("PyYAML==6.0  # yaml\nrequests\n-r other.txt\nPyJWT[crypto]==2.8.0\n")
        self.assertEqual([(r["name"], r["version"], r["pinned"]) for r in rs],
                         [("pyyaml", "6.0", True), ("requests", None, False), ("pyjwt", "2.8.0", True)])

    def test_third_party_imports(self):
        code = "import os, yaml\nfrom jwt import decode\nfrom . import x\nimport xml.etree.ElementTree as ET\n"
        self.assertEqual(third_party_imports(code), ["jwt", "yaml"])

    def test_decision(self):
        self.assertEqual(parse_decision('Sure:\n{"decision": "hold", "reasons": ["x"]}')[0], "HOLD")
        self.assertEqual(parse_decision("Looks fine to me.")[0], None)

    def test_wilson(self):
        self.assertEqual(wilson(0, 0), (0.0, 0.0))
        lo, hi = wilson(31, 40)
        self.assertTrue(0.62 < lo < 0.63 and 0.87 < hi < 0.88)


class Frozen(unittest.TestCase):
    def test_tasks_tests_and_references_line_up(self):
        tasks = json.loads((ROOT / "codeverify/tasks.json").read_text())["tasks"]
        self.assertEqual(len(tasks), 12)
        for t in tasks:
            for f in (f"tests/{t['id']}_visible.py", f"tests/{t['id']}_hidden.py",
                      f"reference/{t['id']}.good.py", f"reference/{t['id']}.bad.py"):
                self.assertTrue((ROOT / "codeverify" / f).exists(), f)

    def test_reference_check_recorded(self):
        lines = (ROOT / "bench/out/codeverify/reference_check.txt").read_text().splitlines()[1:]
        good = [l for l in lines if " good: " in l]
        bad = [l for l in lines if " bad: " in l]
        self.assertEqual(len(good), 12)
        self.assertTrue(all("failed" not in l for l in good))
        self.assertTrue(all("failed" in l for l in bad))

    def test_tasks_and_tests_unchanged_since_preregistration(self):
        # hash of tasks.json, tests/ and reference/ as committed in 68c0dfa (the pre-registration)
        r = ROOT / "codeverify"
        h = hashlib.sha256()
        for f in sorted([r / "tasks.json", *r.glob("tests/*.py"), *r.glob("reference/*.py")]):
            h.update(f.relative_to(ROOT).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
        self.assertEqual(h.hexdigest(), "e7b8bc328d31ff6fccc2f5b4b6d4a021fd0f382d05ee6675509973c29bb8bba8")

class Registry(unittest.TestCase):
    """B2: only a 404 means 'not on PyPI'; rate limits and outages are retried, then the change is skipped."""

    def setUp(self):
        import checks
        self.checks = checks
        self._http, self._sleep = checks.http_json, checks.time.sleep
        checks.time.sleep = lambda s: None

    def tearDown(self):
        self.checks.http_json, self.checks.time.sleep = self._http, self._sleep

    def err(self, code):
        import urllib.error
        return urllib.error.HTTPError("https://pypi.org/x", code, "x", {}, None)

    def test_404_is_missing_and_yanked_is_flagged(self):
        def fake(url, timeout=60):
            if "nosuch" in url:
                raise self.err(404)
            return {"info": {"yanked": "old" in url, "yanked_reason": "bad build"}}
        self.checks.http_json = fake
        reqs = parse_requirements("nosuch==1.0\nold==2.0\nfine==3.0")
        probs = self.checks.registry(reqs)
        self.assertEqual(len(probs), 2)
        self.assertIn("not found on PyPI", probs[0])
        self.assertIn("yanked", probs[1])

    def test_rate_limit_is_retried_then_succeeds(self):
        calls = []
        def fake(url, timeout=60):
            calls.append(url)
            if len(calls) < 3:
                raise self.err(429)
            return {"info": {}}
        self.checks.http_json = fake
        self.assertEqual(self.checks.registry(parse_requirements("pyyaml==6.0.2")), [])
        self.assertEqual(len(calls), 3)

    def test_outage_is_not_reported_as_missing(self):
        def fake(url, timeout=60):
            raise self.err(503)
        self.checks.http_json = fake
        with self.assertRaises(self.checks.RegistryUnavailable):
            self.checks.registry(parse_requirements("pyyaml==6.0.2"))


class Isolation(unittest.TestCase):
    """S3: model-written code runs with no network, as nobody, and can't touch root's files."""

    def test_escape_attempt_is_contained(self):
        import checks
        if not checks.ISOLATED:
            self.skipTest("unshare/setpriv need root; not available on this runner")
        d = checks.scratch_dir("cv-iso-test-")
        try:
            (d / "escape.py").write_text(
                "import os, urllib.request\nr = []\n"
                "try:\n    urllib.request.urlopen('https://pypi.org', timeout=5); r.append('NET')\nexcept Exception: pass\n"
                "try:\n    open('/root/.bashrc').read(); r.append('READ_ROOT')\nexcept Exception: pass\n"
                "try:\n    open('/root/cv-pwned', 'w').write('x'); r.append('WRITE_ROOT')\nexcept Exception: pass\n"
                "print(os.getuid(), r)\n")
            (d / "escape.py").chmod(0o644)
            p = checks.run_untrusted([sys.executable, str(d / "escape.py")], cwd=d, timeout=60)
            self.assertEqual(p.stdout.strip(), "65534 []", p.stderr[-300:])
            self.assertFalse(Path("/root/cv-pwned").exists())
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
