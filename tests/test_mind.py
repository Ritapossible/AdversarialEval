#!/usr/bin/env python3
"""Checks for the Dependency Guard Mind tests (mind/).

    python tests/test_mind.py
"""
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mind"))


class CodeCasesV2(unittest.TestCase):
    """mind/code-test-v2: frozen case file."""

    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((ROOT / "mind" / "code-test-v2" / "cases.json").read_text())["cases"]

    def test_shape(self):
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        kinds = [(c["kind"], c["truth"]["affected"]) for c in self.cases]
        self.assertEqual(kinds.count(("pair", True)), 10)
        self.assertEqual(kinds.count(("pair", False)), 10)
        self.assertEqual(kinds.count(("decoy", False)), 3)
        for c in self.cases:
            self.assertLessEqual(len(c["target"].encode()), 256, c["id"])  # the intent's limit
            self.assertTrue(c["rationale"] and c["cwe"].startswith("CWE-") and c["source_url"].startswith("https://cwe.mitre.org/"))
        for c in self.cases:  # every pair has both halves
            if c["kind"] == "pair":
                twin = c["id"].replace("-vulnerable", "-fixed") if c["truth"]["affected"] else c["id"].replace("-fixed", "-vulnerable")
                self.assertIn(twin, ids)

    def test_builder_reproduces_file(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mind" / "code-test-v2").mkdir(parents=True)
            subprocess.run([sys.executable, str(ROOT / "mind" / "code-test-v2" / "make_cases.py")], cwd=d, check=True, capture_output=True)
            self.assertEqual(json.loads((Path(d) / "mind/code-test-v2/cases.json").read_text())["cases"], self.cases)

    def test_regex_pair(self):
        by = {c["id"]: c for c in self.cases}
        vuln = re.search(r'r"(.+?)"', by["regex-vulnerable"]["target"]).group(1)
        fixed = re.search(r'r"(.+?)"', by["regex-fixed"]["target"]).group(1)
        t = time.time(); re.fullmatch(fixed, "a" * 100_000 + "!"); self.assertLess(time.time() - t, 0.5)
        t = time.time(); re.fullmatch(vuln, "a" * 20 + "!"); slow20 = time.time() - t
        t = time.time(); re.fullmatch(vuln, "a" * 14 + "!"); slow14 = time.time() - t
        self.assertGreater(slow20, slow14 * 4)  # grows exponentially

    def test_redirect_fix(self):
        by = {c["id"]: c for c in self.cases}
        pat = re.search(r'r"(.+?)"', by["redirect-fixed"]["target"]).group(1)
        for bad in ("//evil.example", "/\\evil.example", "/\t/evil.example", "https://evil.example"):
            self.assertIsNone(re.fullmatch(pat, bad), bad)
        self.assertIsNotNone(re.fullmatch(pat, "/account?tab=keys"))


class SolanaCases(unittest.TestCase):
    """mind/solana-test: frozen case file."""

    def test_shape(self):
        d = json.loads((ROOT / "mind" / "solana-test" / "cases.json").read_text())
        cs = d["cases"]
        self.assertEqual(len({c["id"] for c in cs}), len(cs))
        truths = [c["truth"]["affected"] for c in cs]
        self.assertEqual((truths.count(True), truths.count(False), truths.count(None)), (7, 7, 2))
        for c in cs:
            self.assertLessEqual(len(c["target"].encode()), 256)
            self.assertRegex(c["target"], r"^pkg:(npm|cargo)/.+@[^@]+$")
            if c["truth"]["affected"]:
                self.assertTrue(c["truth"]["osv_ids"])
        web3 = [c for c in cs if c["target"] == "pkg:npm/@solana/web3.js@1.95.7"]
        self.assertTrue(web3 and web3[0]["withdrawn_from_registry"])
        self.assertIn("MAL-2024-11183", web3[0]["truth"]["osv_ids"])


class Compare(unittest.TestCase):
    def test_nonexistent_scoring(self):
        from compare import score
        t = {"a": True, "b": False, "x": None}
        s = score({"a": "BLOCK", "b": "PASS", "x": "PASS"}, t, ["a", "b", "x"])
        self.assertEqual((s["correct"], s["wrong"], s["nonexistent_confident"]), (2, 1, 1))
        s = score({"a": "PASS", "b": "BLOCK", "x": "FLAG"}, t, ["a", "b", "x"])
        self.assertEqual((s["missed_vulnerability"], s["false_alarm"], s["nonexistent_flagged"]), (1, 1, 1))

    def test_unparsed_reply_is_an_error(self):
        # audit bug 9: lines that don't parse must not silently count as "no decision"
        with tempfile.TemporaryDirectory() as d:
            run = {"spent_usd": 0, "packages": [{"target": t, "decision": "PASS", "attempts": []}
                                                 for t in ("pkg:npm/minimist@1.2.8", "pkg:npm/minimist@1.2.5")]}
            (Path(d) / "run.json").write_text(json.dumps(run))
            (Path(d) / "alone.json").write_text(json.dumps({"reply": "pkg:npm/minimist@1.2.8 | PASS\nminimist 1.2.5: block it"}))
            cmd = [sys.executable, str(ROOT / "mind" / "compare.py"), str(Path(d) / "run.json"), str(Path(d) / "alone.json")]
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("1 package", p.stderr)
            p = subprocess.run(cmd + ["--allow-partial"], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)["A_mind_alone"]["unparsed"], ["pkg:npm/minimist@1.2.5"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
