#!/usr/bin/env python3
"""Unit tests for the benchmark's grading and statistics (bench/benchlib.py, rule v2).

    python tests/test_bench.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bench"))
from benchlib import bootstrap_ratio, charged, charged_onchain, grade, id_match, kendall_tau_b, percentile, wilson  # noqa: E402

AFF = {"id": "a", "kind": "package", "truth": {"affected": True, "osv_ids": ["GHSA-aaaa-bbbb-cccc"]}}
CLEAN = {"id": "c", "kind": "package", "truth": {"affected": False}}
CODE_FIXED = {"id": "f", "kind": "code", "truth": {"affected": False}}
UNK = {"id": "u", "kind": "unknown", "truth": {"affected": None}}


def rec(verdict=None, count=None, issues=None, http=200, summary=None):
    return {"http": http, "result": {"verdict": verdict, "vulnerability_count": count, "issues": issues, "summary": summary}}


class Grade(unittest.TestCase):
    def test_affected(self):
        self.assertEqual(grade(AFF, rec("Insecure", 2)), "correct")
        self.assertEqual(grade(AFF, rec("Needs changes", 1)), "correct")
        self.assertEqual(grade(AFF, rec("Insecure", 0)), "wrong")
        self.assertEqual(grade(AFF, rec("Secure", 0)), "wrong")

    def test_missing_or_invalid_verdict_is_no_answer(self):
        self.assertEqual(grade(AFF, rec(None, 6, ["GHSA-aaaa-bbbb-cccc"])), "no answer")
        self.assertEqual(grade(AFF, rec("vulnerable", 6)), "no answer")
        self.assertEqual(grade(AFF, rec("Insecure", 2, http=500)), "no answer")
        self.assertEqual(grade(AFF, {"http": None, "error": "timeout"}), "no answer")

    def test_count_must_be_a_number(self):
        self.assertEqual(grade(AFF, rec("Insecure", None)), "wrong")
        self.assertEqual(grade(AFF, rec("Insecure", True)), "wrong")
        self.assertEqual(grade(CLEAN, rec("Secure", None)), "wrong")

    def test_clean_package(self):
        self.assertEqual(grade(CLEAN, rec("Secure", 0)), "correct")
        self.assertEqual(grade(CLEAN, rec("Needs changes", 0)), "wrong")
        self.assertEqual(grade(CLEAN, rec("Secure", 1)), "wrong")

    def test_fixed_code_lenient_and_strict(self):
        self.assertEqual(grade(CODE_FIXED, rec("Needs changes", 0)), "correct")
        self.assertEqual(grade(CODE_FIXED, rec("Needs changes", 0), strict=True), "wrong")
        self.assertEqual(grade(CODE_FIXED, rec("Insecure", 0)), "wrong")

    def test_unknown(self):
        self.assertEqual(grade(UNK, {"http": 500, "error": "x"}), "abstained")
        self.assertEqual(grade(UNK, rec("Secure", 0, summary="package not found")), "abstained")
        self.assertEqual(grade(UNK, rec("Secure", 0)), "confident clean")
        self.assertEqual(grade(UNK, rec("Insecure", 3, ["CVE-2020-1"])), "invented")


class ScoreV2(unittest.TestCase):
    def test_point_estimate_inside_interval(self):
        from score_v2 import summarise
        cases = {f"p{i}": {"id": f"p{i}", "kind": "package", "ecosystem": "npm", "truth": {"affected": True}} for i in range(10)}
        cases.update({f"f{i}": {"id": f"f{i}", "kind": "format", "of": "p0", "truth": {"affected": True}} for i in range(5)})
        paid = {"receipt": {"amount_uusdc": "10000"}}
        recs = [dict(rec("Insecure", 1), case=f"p{i}", **paid) if i < 6 else dict(rec(None, 1), case=f"p{i}", **paid) for i in range(10)]
        recs += [dict(rec("Insecure", 1), case=f"f{i}", **paid) for i in range(5)]
        s = summarise(cases, recs)
        self.assertAlmostEqual(s["cost_per_correct"], 0.15 / 6, places=4)
        lo, hi = s["cost_per_correct_ci95"]
        self.assertLessEqual(lo, s["cost_per_correct"])
        self.assertGreaterEqual(hi, s["cost_per_correct"])


class RailFill(unittest.TestCase):
    def test_failed_escrow_call_is_not_charged(self):
        import json, tempfile
        from score_v2 import load
        d = Path(tempfile.mkdtemp())
        rows = [{"case": "a", "miner_id": "m", "http": 200, "rail": "escrow", "escrow_receipt": {"amount_uusdc": "10000"}},
                {"case": "b", "miner_id": "m", "http": None, "error": "fetch failed"}]
        (d / "calls.ndjson").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        recs = load(d)
        self.assertEqual(recs[1]["rail"], "escrow")
        self.assertFalse(charged_onchain(recs[1]))


class Measures(unittest.TestCase):
    def test_charged(self):
        self.assertTrue(charged({"receipt": {"amount_uusdc": "10000"}}))
        self.assertTrue(charged({"payment_response": {"success": True}}))
        self.assertFalse(charged({"payment_response": {"success": False}}))
        self.assertFalse(charged({"http": 503}))
        self.assertTrue(charged_onchain({"http": 504}))
        self.assertTrue(charged_onchain({"http": None}))
        self.assertFalse(charged_onchain({"http": 503}))
        # escrow rail (amendment 4): only a delivered answer with a receipt is billed
        self.assertTrue(charged({"escrow_receipt": {"amount_uusdc": "10000"}}))
        self.assertTrue(charged_onchain({"rail": "escrow", "http": 200, "escrow_receipt": {"amount_uusdc": "10000"}}))
        self.assertFalse(charged_onchain({"rail": "escrow", "http": 504}))

    def test_id_match(self):
        self.assertTrue(id_match(AFF, rec("Insecure", 1, ["ghsa-aaaa-bbbb-cccc"])))
        self.assertFalse(id_match(AFF, rec("Insecure", 1, ["CVE-2000-0001"])))
        self.assertTrue(id_match(AFF, rec("Insecure", 1, ["CVE-2000-0001"]), {"GHSA-aaaa-bbbb-cccc": {"CVE-2000-0001"}}))
        self.assertIsNone(id_match(CLEAN, rec("Secure", 0)))

    def test_wilson(self):
        lo, hi = wilson(18, 36)
        self.assertAlmostEqual(lo, 0.3447, places=3)  # hand-checked: p=.5, n=36, z=1.96
        self.assertAlmostEqual(hi, 0.6553, places=3)
        self.assertEqual(wilson(0, 0), (0.0, 1.0))
        self.assertGreater(wilson(0, 10)[1], 0)
        self.assertEqual(wilson(0, 36)[0], 0.0)  # never prints as -0%
        self.assertEqual(wilson(36, 36)[1], 1.0)

    def test_bootstrap(self):
        ci = bootstrap_ratio([0.01] * 20, [1] * 10 + [0] * 10)
        self.assertLess(ci[0], 0.02)
        self.assertGreater(ci[1], 0.02)
        self.assertIsNone(bootstrap_ratio([0.01] * 5, [0] * 5))

    def test_kendall(self):
        self.assertAlmostEqual(kendall_tau_b([1, 2, 3, 4], [1, 2, 3, 4]), 1.0)
        self.assertAlmostEqual(kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(kendall_tau_b([1, 2], [1, 2]))
        self.assertIsNone(kendall_tau_b([1, 1, 1], [2, 2, 2]))

    def test_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.5), 3)
        self.assertIsNone(percentile([], 0.9))


if __name__ == "__main__":
    unittest.main(verbosity=1)
