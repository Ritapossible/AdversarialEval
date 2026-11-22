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


class Round3(unittest.TestCase):
    """eval/reports/2026-11-21-round-3.md (rule v2, amendment 4: escrow rail)."""

    @classmethod
    def setUpClass(cls):
        from score_v2 import score_rounds
        d = ROOT / "bench" / "out"
        cls.res = score_rounds([d / "round-2", d / "round-3"], ROOT / "bench" / "cases-v2.json")
        cls.t = cls.res["rounds"]["round-3"]["targets"]
        cls.calls = [json.loads(l) for l in (d / "round-3" / "calls.ndjson").read_text().splitlines() if l.strip()]
        cls.before = json.loads((d / "round-3" / "ledger-before.json").read_text())
        cls.after = json.loads((d / "round-3" / "ledger-after.json").read_text())

    def test_headline(self):
        self.assertEqual(len(self.calls), 1564)
        a1 = self.t["20260828"]
        self.assertEqual((a1["correct"], a1["by_category"]["code"]), (31, "9/12"))
        self.assertIsNone(a1["rank"])  # unranked at round 3's start
        self.assertEqual(self.t["osv-baseline"]["correct"], 24)
        self.assertEqual(self.t["routed"]["correct"], 1)
        self.assertEqual(self.t["77007"]["rank"], 1)
        self.assertEqual(self.t["77007"]["correct"], 0)

    def test_rank_is_per_round(self):
        # scored together with round 2, round 3 must still use its own ranks
        self.assertEqual(self.res["rounds"]["round-2"]["targets"]["20260828"]["rank"], 7)
        self.assertEqual(self.res["rounds"]["round-3"]["n_ranked"], 27)
        self.assertAlmostEqual(self.res["rounds"]["round-3"]["kendall_tau_rank_vs_accuracy"], -0.18, places=2)

    def test_escrow_reconciliation(self):
        receipts = sum(int(c["escrow_receipt"]["amount_uusdc"]) for c in self.calls if isinstance(c.get("escrow_receipt"), dict))
        delivered = sum(c.get("http") == 200 for c in self.calls)
        billed = [c for c in self.calls if isinstance(c.get("escrow_receipt"), dict)]
        self.assertEqual((len(billed), delivered, receipts), (591, 591, 5_910_000))
        self.assertTrue(all(c.get("http") == 200 for c in billed))  # no failure was billed
        delta = (int(self.after["charged"]) + int(self.after["unbilled"])) - (int(self.before["charged"]) + int(self.before["unbilled"]))
        self.assertEqual(delta, receipts)


class Round4Pooled(unittest.TestCase):
    """eval/reports/2026-11-22-rounds-2-4.md."""

    @classmethod
    def setUpClass(cls):
        from score_v2 import score_rounds
        d = ROOT / "bench" / "out"
        cls.res = score_rounds([d / "round-2", d / "round-3", d / "round-4"], ROOT / "bench" / "cases-v2.json")
        cls.R = cls.res["rounds"]
        cls.calls = [json.loads(l) for l in (d / "round-4" / "calls.ndjson").read_text().splitlines() if l.strip()]
        cls.before = json.loads((d / "round-4" / "ledger-before.json").read_text())
        cls.after = json.loads((d / "round-4" / "ledger-after.json").read_text())

    def test_round4_headline(self):
        t = self.R["round-4"]["targets"]
        self.assertEqual(len(self.calls), 1518)
        self.assertEqual((t["20260828"]["correct"], t["20260828"]["rank"]), (32, 3))
        self.assertEqual((t["905227"]["correct"], t["905227"]["rank"]), (17, 1))  # salence, ex evidence-security-review
        self.assertEqual(t["routed"]["correct"], 17)
        self.assertEqual(t["osv-baseline"]["correct"], 24)
        self.assertEqual(self.R["round-4"]["n_ranked"], 32)
        self.assertAlmostEqual(self.R["round-4"]["kendall_tau_rank_vs_accuracy"], 0.29, places=2)

    def test_round4_reconciliation(self):
        billed = [c for c in self.calls if isinstance(c.get("escrow_receipt"), dict)]
        receipts = sum(int(c["escrow_receipt"]["amount_uusdc"]) for c in billed)
        self.assertEqual((len(billed), receipts), (634, 6_340_000))
        self.assertTrue(all(c.get("http") == 200 for c in billed))
        delta = (int(self.after["charged"]) + int(self.after["unbilled"])) - (int(self.before["charged"]) + int(self.before["unbilled"]))
        self.assertEqual(delta - receipts, 10_000)  # one unmatched charge, reported
        self.assertEqual(sum(c.get("http") is None for c in self.calls), 3)

    def test_pooled_stability(self):
        a1 = [self.R[r]["targets"]["20260828"]["correct"] for r in self.R]
        self.assertEqual(a1, [27, 31, 32])
        self.assertEqual([self.R[r]["targets"]["905227"]["correct"] for r in self.R], [0, 0, 17])
        self.assertEqual([self.R[r]["targets"]["routed"]["correct"] for r in self.R], [5, 1, 17])
        common = set.intersection(*[set(self.R[r]["targets"]) for r in self.R])
        self.assertEqual(len(common) - 2, 13 - 2)  # 13 incl. the route and the free baseline

    def test_cost_per_rail(self):
        def tot(r, key):
            return round(sum(v[key] for k, v in self.R[r]["targets"].items() if k != "osv-baseline"), 2)
        self.assertEqual([tot(r, "charged_onchain_usdc") for r in self.R], [5.60, 5.91, 6.34])
        self.assertEqual([sum(v["correct"] for k, v in self.R[r]["targets"].items() if k != "osv-baseline") for r in self.R], [56, 71, 107])


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
