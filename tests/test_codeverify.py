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

if __name__ == "__main__":
    unittest.main(verbosity=1)
