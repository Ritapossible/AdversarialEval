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


class Round2(unittest.TestCase):
    """eval/reports/2026-11-16-round-2.md (rule bench/RULE-v2.md, amendment 1)."""

    @classmethod
    def setUpClass(cls):
        from score_v2 import score_rounds
        cls.res = score_rounds([ROOT / "bench" / "out" / "round-2"], ROOT / "bench" / "cases-v2.json")
        cls.t = cls.res["rounds"]["round-2"]["targets"]
        from benchlib import answer, charged_onchain, VERDICTS
        cls.calls = [json.loads(l) for l in (ROOT / "bench" / "out" / "round-2" / "calls.ndjson").read_text().splitlines() if l.strip()]
        cls.answer, cls.charged_onchain, cls.VERDICTS = staticmethod(answer), staticmethod(charged_onchain), VERDICTS

    def test_headline(self):
        self.assertEqual(len(self.calls), 598)
        a1 = self.t["20260828"]
        self.assertEqual((a1["correct"], a1["answerable_called"]), (27, 36))
        self.assertEqual(self.t["osv-baseline"]["correct"], 24)
        self.assertEqual(self.t["routed"]["correct"], 5)
        self.assertEqual(self.t["731001"]["correct"], 0)  # rank 1
        self.assertAlmostEqual(self.res["rounds"]["round-2"]["kendall_tau_rank_vs_accuracy"], 0.02, places=2)

    def test_onchain_reconciliation(self):
        onchain = json.loads((ROOT / "bench" / "out" / "round-2" / "onchain-payments.json").read_text())
        self.assertEqual(onchain["transfers"], 560)
        self.assertEqual(sum(self.charged_onchain(c) for c in self.calls), 560)
        total = sum(v["charged_onchain_usdc"] for v in self.t.values())
        self.assertAlmostEqual(total, 5.60, places=2)

    def test_charged_breakdown(self):
        ch = [c for c in self.calls if self.charged_onchain(c)]
        valid = sum(c.get("http") == 200 and (self.answer(c) or {}).get("verdict") in self.VERDICTS for c in ch)
        null = sum(c.get("http") == 200 and (self.answer(c) or {}).get("verdict") not in self.VERDICTS for c in ch)
        err = sum(c.get("http") == 500 for c in ch)
        timeout = sum(c.get("http") in (504, None) for c in ch)
        self.assertEqual((valid, null, err, timeout), (119, 72, 246, 123))

    def test_a1_code_says_secure(self):
        a1 = [c for c in self.calls if c["miner"] == "a1-preflight" and c["case"].startswith("code-")]
        self.assertEqual(sum((c.get("result") or {}).get("verdict") == "Secure" for c in a1), 10)
        self.assertEqual(self.t["20260828"]["by_category"]["code"], "6/12")


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
