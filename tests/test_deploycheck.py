#!/usr/bin/env python3
"""Offline tests for deploycheck/ (no installs, no network).

    python tests/test_deploycheck.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from deploycheck.core import _dedupe, decide, reachability  # noqa: E402


def rec(i, aliases=(), sev="HIGH", fixed="2.0"):
    return {"id": i, "aliases": list(aliases), "summary": f"{i} summary", "database_specific": {"severity": sev},
            "affected": [{"ranges": [{"events": [{"introduced": "0"}, {"fixed": fixed}]}]}]}


class Dedupe(unittest.TestCase):
    def test_aliases_merge_and_ghsa_wins(self):
        out = _dedupe([rec("PYSEC-2026-1", ["GHSA-aaaa-bbbb-cccc"]), rec("GHSA-aaaa-bbbb-cccc", ["PYSEC-2026-1"]), rec("GHSA-dddd-ffff-gggg")])
        self.assertEqual([g["id"] for g in out], ["GHSA-aaaa-bbbb-cccc", "GHSA-dddd-ffff-gggg"])
        self.assertEqual(out[0]["aliases"], ["PYSEC-2026-1"])
        self.assertEqual(out[0]["fixed"], ["2.0"])


class Reachability(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app = Path(self.tmp.name) / "app"
        app.mkdir()
        (app / "ui.py").write_text("import gradio as gr\nwith gr.Blocks() as demo:\n    gr.Audio()\ndemo.launch()\n")
        self.src = app

    def tearDown(self):
        self.tmp.cleanup()

    def test_used_not_used_conditional_default_unknown(self):
        rules = {"GHSA-used": {"needs": "audio", "uses": ["gr\\.Audio\\b"]},
                 "GHSA-unused": {"needs": "file explorer", "uses": ["FileExplorer"]},
                 "GHSA-cond": {"needs": "serving", "uses": ["\\.launch\\("], "condition": "Windows"}}
        vs = [{"id": i, "aliases": [], "severity": "HIGH"} for i in ("GHSA-used", "GHSA-unused", "GHSA-cond", "GHSA-other")]
        got = {v["id"]: v["reach"] for v in reachability(vs, rules, self.src)}
        self.assertEqual(got, {"GHSA-used": "reachable", "GHSA-unused": "not used", "GHSA-cond": "conditional", "GHSA-other": "unknown"})
        got = {v["id"]: v["reach"] for v in reachability(vs[3:], {"_default": {"needs": "x", "uses": ["launch"]}}, self.src)}
        self.assertEqual(got, {"GHSA-other": "reachable"})  # a package-wide rule covers advisories without their own
        ev = reachability(vs[:1], rules, self.src)[0]["evidence"]
        self.assertTrue(ev and "ui.py:3" in ev[0])  # evidence names the file and line

    def test_alias_matches_rule(self):
        vs = [{"id": "PYSEC-1", "aliases": ["GHSA-used"], "severity": "LOW"}]
        self.assertEqual(reachability(vs, {"GHSA-used": {"needs": "audio", "uses": ["Audio"]}}, self.src)[0]["reach"], "reachable")


class Decide(unittest.TestCase):
    def base(self, **kw):
        c = {"install_ok": True, "imports_ok": True, "import_error": [], "undeclared": [], "smoke": {"ok": True}, "reach": {}}
        c.update(kw)
        return c

    def test_clean_deploys(self):
        self.assertEqual(decide(self.base())[0], "DEPLOY")

    def test_hold_reasons(self):
        self.assertEqual(decide(self.base(imports_ok=False, import_error=["No module named x"]))[0], "HOLD")
        self.assertEqual(decide(self.base(undeclared=[{"package": "numpy"}]))[0], "HOLD")
        self.assertEqual(decide(self.base(smoke={"ok": False, "error": "boom"}))[0], "HOLD")
        high = {"p": [{"id": "G", "severity": "HIGH", "reach": "reachable"}]}
        self.assertEqual(decide(self.base(reach=high))[0], "HOLD")
        unknown_critical = {"p": [{"id": "G", "severity": "CRITICAL", "reach": "unknown"}]}
        self.assertEqual(decide(self.base(reach=unknown_critical))[0], "HOLD")  # unknown is never treated as safe

    def test_conditions(self):
        cond = {"p": [{"id": "G", "severity": "HIGH", "reach": "conditional", "condition": "Windows"}]}
        d, why = decide(self.base(reach=cond))
        self.assertEqual(d, "DEPLOY WITH CONDITIONS")
        self.assertIn("only when Windows", why[0])
        self.assertEqual(decide(self.base(reach={"p": [{"id": "G", "severity": "HIGH", "reach": "not used"}]}))[0], "DEPLOY")
        d, why = decide(self.base(force=["pillow==13"], pip_check=["gradio 5 has requirement pillow<12, but you have pillow 13."]))
        self.assertEqual(d, "DEPLOY WITH CONDITIONS")  # forced out-of-range versions are never a plain DEPLOY
        self.assertIn("pillow<12", why[0])


class Scenario(unittest.TestCase):
    def test_qwen_agent_scenario_and_rules(self):
        sc = json.loads((ROOT / "deploycheck/scenarios/qwen_agent.json").read_text())
        self.assertTrue((ROOT / sc["smoke"]).exists())
        rules = json.loads((ROOT / sc["reach_rules"]).read_text())
        for pkg, rs in rules.items():
            if pkg.startswith("_"):
                continue
            for k, r in rs.items():
                self.assertTrue(r["needs"] and r["uses"], f"{pkg} {k}")

    def test_published_run(self):
        rep = json.loads((ROOT / "bench/out/deploycheck-qwen-agent/report.json").read_text())
        d = {c["name"].split(":")[0]: c["decision"] for c in rep["candidates"]}
        self.assertEqual(d["as shipped"], "HOLD")
        self.assertEqual(d["fix 5"], "DEPLOY WITH CONDITIONS")
        shipped = rep["candidates"][0]
        self.assertFalse(shipped["imports_ok"])
        self.assertEqual([u["package"] for u in shipped["undeclared"]], ["soundfile"])
        self.assertTrue(all(t["verified_ask"]["label"] == "verified" for t in rep["telegraph"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
