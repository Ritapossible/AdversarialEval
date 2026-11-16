#!/usr/bin/env python3
"""Published numbers must follow from the committed raw data.

    python tests/test_reproduce.py

Re-scores every committed benchmark round and checks the figures quoted in eval/reports/.
Add a check here whenever a report quotes a new number.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))


class Round1(unittest.TestCase):
    """eval/reports/2026-11-15-paid-benchmark.md (rule bench/RULE.md)."""

    def test_totals(self):
        out = subprocess.run([sys.executable, str(ROOT / "bench" / "score.py")], capture_output=True, text=True, check=True).stdout
        self.assertIn("Total: 91 calls, 0.38 USDC paid, 21 verified correct answers ($0.018 per correct answer overall)", out)
        rows = {r["miner"]: r for r in json.loads((ROOT / "bench" / "out" / "scored.json").read_text())["rows"]}
        self.assertEqual(rows["a1-preflight"]["correct"], 6)
        self.assertEqual(rows["pr-guard-sentinel"]["correct"], 0)
        self.assertEqual(rows["pr-guard-sentinel"]["rank"], 1)

    def test_null_verdicts(self):
        calls = [json.loads(l) for l in (ROOT / "bench" / "out" / "calls.ndjson").read_text().splitlines() if l.strip()]
        delivered = [c for c in calls if c.get("http") == 200]
        self.assertEqual(len(delivered), 38)
        self.assertEqual(sum((c.get("result") or {}).get("verdict") is None for c in delivered), 21)


class Audit(unittest.TestCase):
    """eval/reports/2026-11-15-miner-audit.md."""

    def test_reachable(self):
        a = json.loads((ROOT / "eval" / "reports" / "raw" / "2026-11-15-miner-audit.json").read_text())
        self.assertEqual(len(a["miners"]), 32)
        self.assertEqual(sum(bool(m["callable"]) for m in a["miners"]), 12)
        unreachable_top = sorted(m["rank"] for m in a["miners"] if not m["callable"] and m["rank"] and m["rank"] <= 7)
        self.assertEqual(unreachable_top, [2, 4, 7])


if __name__ == "__main__":
    unittest.main(verbosity=1)
