#!/usr/bin/env python3
"""Offline tests for resolve/ (no network, no payments).

    python tests/test_resolve.py
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resolve"))
from run import cites, outcome, wilson  # noqa: E402
from sources import resolve  # noqa: E402


class Frozen(unittest.TestCase):
    def test_cases_unchanged_since_preregistration(self):
        self.assertEqual(hashlib.sha256((ROOT / "resolve/cases.json").read_bytes()).hexdigest(),
                         "08b415b313202218e64d5e041f9b66c0b08ee09c397b809b9cd42b1895ffb3ac")

    def test_truth_mix_and_evidence(self):
        ms = json.loads((ROOT / "resolve/cases.json").read_text())["markets"]
        self.assertEqual(len(ms), 24)
        self.assertEqual([sum(m["truth"] == k for m in ms) for k in ("yes", "no", "unresolved")], [12, 9, 3])
        for m in ms:
            if m["truth"] != "unresolved":
                self.assertIn("url", m["truth_evidence"], m["id"])  # every settled truth names its source


class FrozenPolymarket(unittest.TestCase):
    def test_polymarket_cases_unchanged_since_preregistration(self):
        self.assertEqual(hashlib.sha256((ROOT / "resolve/polymarket_cases.json").read_bytes()).hexdigest(),
                         "e2e5ed3bb2209be661ac450aed3f9f832ff6a3ec5fd6f4e481dd22af9dcc1602")

    def test_selection_shape(self):
        ms = json.loads((ROOT / "resolve/polymarket_cases.json").read_text())["markets"]
        self.assertEqual(len(ms), 24)
        self.assertEqual(sorted({m["category"] for m in ms}), ["crypto", "politics", "sports", "world"])
        self.assertEqual(sum(m["truth"] == "yes" for m in ms), 9)
        self.assertTrue(all(bool(m["contract"]) == (m["category"] == "crypto") for m in ms))


class Parsing(unittest.TestCase):
    def test_outcome(self):
        self.assertEqual(outcome({"result": {"outcome": "YES"}}), "yes")
        self.assertEqual(outcome({"result": {"outcome": None, "resolved_yes": False}}), "no")
        self.assertEqual(outcome({"result": None, "error": "fetch failed"}), "unresolved")
        self.assertEqual(outcome(None), "unresolved")

    def test_cites(self):
        self.assertTrue(cites({"result": {"sources": ["https://www.espn.com/x"]}}))
        self.assertFalse(cites({"result": {"sources": None}}))
        self.assertFalse(cites({"result": {"sources": ["ESPN"]}}))

    def test_no_contract_is_unresolved(self):
        self.assertEqual(resolve(None)[0], "unresolved")

    def test_wilson(self):
        self.assertEqual(wilson(0, 0), [0.0, 0.0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
