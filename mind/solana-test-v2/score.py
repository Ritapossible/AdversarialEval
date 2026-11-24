#!/usr/bin/env python3
"""Score the Solana use case 3 test (four arms), as frozen in RULE.md.

    python mind/solana-test-v2/score.py bench/out/solana-v2 mind/evidence/<mind-alone>.json [--md out.md]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import statistics
import sys
from math import sqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERDICT = {"Secure": "PASS", "Insecure": "BLOCK", "Needs changes": "BLOCK"}


def wilson(k: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(100 * (c - h) / d, 1), round(100 * (c + h) / d, 1))


def parse_alone(reply: str) -> dict[str, str]:
    text = html.unescape(re.sub(r"<[^>]+>", "\n", reply or ""))
    out = {}
    for m in re.finditer(r"(pkg:[a-z]+/\S+?@[^\s|`]+)\s*`?\s*\|\s*\**\s*(PASS|BLOCK|FLAG)\b", text):
        out.setdefault(m.group(1), m.group(2))
    return out


def grade(decisions: dict[str, str | None], cases: list[dict]) -> dict:
    s = {"correct": 0, "missed_vulnerability": 0, "false_alarm": 0, "unknown_decided": 0, "no_decision": 0}
    for c in cases:
        d, t = decisions.get(c["target"]), c["truth"]["affected"]
        if t is None:
            if d in ("PASS", "BLOCK"):
                s["unknown_decided"] += 1
            else:
                s["correct"] += 1
        elif d not in ("PASS", "BLOCK"):
            s["no_decision"] += 1
        elif (d == "BLOCK") == t:
            s["correct"] += 1
        else:
            s["missed_vulnerability" if t else "false_alarm"] += 1
    n = len(cases)
    s["accuracy_pct"] = round(100 * s["correct"] / n, 1)
    s["wilson_95"] = wilson(s["correct"], n)
    s["task_fulfilled"] = s["correct"] == n
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("mind_alone", type=Path, nargs="?")
    ap.add_argument("--cases", type=Path, default=HERE / "cases.json")
    a = ap.parse_args()
    cases = json.loads(a.cases.read_text())["cases"]
    calls = [json.loads(l) for l in (a.run / "calls.ndjson").read_text().splitlines() if l.strip()]
    dec = json.loads((a.run / "decisions.json").read_text())
    onchain = json.loads((a.run / "onchain.json").read_text()) if (a.run / "onchain.json").exists() else None
    by = {(c["case"], c["arm"]): c for c in calls}
    id2t = {c["id"]: c["target"] for c in cases}

    arms = {}
    def trusted(cid: str, arm: str) -> str | None:
        r = (by.get((cid, arm)) or {}).get("result")
        return VERDICT.get(r.get("verdict")) if isinstance(r, dict) else None

    arms["B_listing"] = {id2t[cid]: trusted(cid, "listing") for cid in id2t}
    arms["C_ranked"] = {id2t[cid]: trusted(cid, "ranked") for cid in id2t}
    arms["D_verified"] = {d["target"]: d["verified_decision"] for d in dec["decisions"]}
    if a.mind_alone:
        alone = parse_alone(json.loads(a.mind_alone.read_text()).get("reply") or "")
        missing = [t for t in id2t.values() if t not in alone]
        if missing:
            sys.exit(f"Mind-alone reply has no decision line for {len(missing)}: {missing[:4]}")
        arms["A_frontier_alone"] = alone

    paid_tx = {}
    if onchain:
        for r in onchain["rows"]:
            if r.get("onchain") == "success":
                paid_tx[(r["case"], r["arm"])] = r["usdc_paid"]
        for u in onchain["summary"].get("unrecorded_payments", []):  # paid, but the answer was lost
            k = tuple(u["nearest_call"].split("|"))
            paid_tx[k] = paid_tx.get(k, 0) + u["usdc_paid"]

    def arm_calls(names):
        return [c for c in calls if c["arm"] in names]

    report = {"cases": len(cases), "affected": sum(c["truth"]["affected"] is True for c in cases),
              "clean": sum(c["truth"]["affected"] is False for c in cases),
              "unknown": sum(c["truth"]["affected"] is None for c in cases), "arms": {}}
    for name, d in arms.items():
        g = grade(d, cases)
        if name == "B_listing":
            cs = arm_calls({"listing"})
        elif name == "C_ranked":
            cs = arm_calls({"ranked"})
        elif name == "D_verified":
            cs = arm_calls({"ranked", "reask"})
        else:
            cs = []
        if cs:
            g["calls"] = len(cs)
            g["usdc_paid_onchain"] = round(sum(paid_tx.get((c["case"], c["arm"]), 0) for c in cs), 4) if onchain else None
            per_case = {}
            for c in cs:
                per_case[c["case"]] = per_case.get(c["case"], 0) + (c.get("wall_ms") or 0)
            g["latency_s_median_per_case"] = round(statistics.median(per_case.values()) / 1000, 1)
            g["latency_s_total"] = round(sum(per_case.values()) / 1000, 1)
        report["arms"][name] = g
    report["per_case"] = [{"type": c["type"], "target": c["target"], "truth": c["truth"]["affected"],
                           **{k: v.get(c["target"]) for k, v in arms.items()}} for c in cases]
    if onchain:
        report["onchain"] = onchain["summary"]
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
