#!/usr/bin/env python3
"""Score the with/without-Telegraph comparison for the Dependency Guard Mind.

    python mind/compare.py mind/evidence/<guard run>.json mind/evidence/<mind-alone>.json [--cases <case file>]

Arms, all on the same packages and graded against the benchmark's frozen truth
(bench/cases-v2.json; affected -> BLOCK is correct, clean -> PASS is correct):
  A  Mind alone: the Mind's own knowledge and web search, no Telegraph.
  B  Telegraph trusted: the first ranked answer, acted on by its verdict field
     (Secure -> PASS; Insecure or Needs changes -> BLOCK; no usable verdict -> no decision).
  C  Telegraph + Verified Ask: the connector's final decision (one re-ask only when proven wrong).
FLAG and "no decision" count as neither right nor wrong; they are reported separately.
A wrong PASS on an affected package is a "missed vulnerability", the costly error.
For a package or version that doesn't exist (benchmark "unknown" cases), FLAG or no decision is
correct and a confident PASS or BLOCK is wrong.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def truth(path: Path | None = None) -> dict[str, bool | None]:
    """True = affected, False = clean, None = the package or version doesn't exist.
    Default: the benchmark's cases (bench/cases-v2.json); or any case file with the same shape."""
    cases = json.loads((path or ROOT / "bench" / "cases-v2.json").read_text())["cases"]
    return {c["target"]: c["truth"]["affected"] for c in cases if c["kind"] in ("package", "unknown")}


def arm_b(pkg: dict) -> str | None:
    first = pkg["attempts"][0] if pkg["attempts"] else {}
    v = (first.get("result") or {}).get("verdict")
    return {"Secure": "PASS", "Insecure": "BLOCK", "Needs changes": "BLOCK"}.get(v)


def parse_alone(reply: str) -> dict[str, str]:
    text = html.unescape(re.sub(r"<[^>]+>", "\n", reply or ""))
    out = {}
    for m in re.finditer(r"(pkg:[a-z]+/\S+?@[^\s|`]+)\s*`?\s*\|\s*\**\s*(PASS|BLOCK|FLAG)\b", text):
        out.setdefault(m.group(1), m.group(2))
    return out


def score(decisions: dict[str, str | None], t: dict[str, bool], targets: list[str]) -> dict:
    s = {"correct": 0, "wrong": 0, "missed_vulnerability": 0, "false_alarm": 0, "flag_or_none": 0,
         "nonexistent_flagged": 0, "nonexistent_confident": 0}
    for x in targets:
        d = decisions.get(x)
        if t[x] is None:  # doesn't exist: the right outcome is to not decide
            if d in ("PASS", "BLOCK"):
                s["wrong"] += 1
                s["nonexistent_confident"] += 1
            else:
                s["correct"] += 1
                s["nonexistent_flagged"] += 1
            continue
        if d not in ("PASS", "BLOCK"):
            s["flag_or_none"] += 1
        elif (d == "BLOCK") == t[x]:
            s["correct"] += 1
        else:
            s["wrong"] += 1
            s["missed_vulnerability" if t[x] else "false_alarm"] += 1
    return s


def main(guard_path: str, alone_path: str | None, cases_path: str | None = None) -> None:
    t = truth(Path(cases_path) if cases_path else None)
    run = json.loads(Path(guard_path).read_text())
    alone = json.loads(Path(alone_path).read_text()) if alone_path else {"reply": None}
    targets = [p["target"] for p in run["packages"]]
    missing = [x for x in targets if x not in t]
    if missing:
        sys.exit(f"not benchmark package cases: {missing}")
    a = parse_alone(alone.get("reply") or "")
    b = {p["target"]: arm_b(p) for p in run["packages"]}
    c = {p["target"]: p["decision"] for p in run["packages"]}
    cost_b = round(sum(p["attempts"][0].get("cost_usd") or 0 for p in run["packages"] if p["attempts"]), 2)
    res = {"packages": len(targets), "affected": sum(t[x] is True for x in targets), "nonexistent": sum(t[x] is None for x in targets),
           "A_mind_alone": {**score(a, t, targets), "cost_usd": 0.0, "parsed": len(a)} if alone_path else "not run",
           "B_telegraph_trusted": {**score(b, t, targets), "cost_usd": cost_b},
           "C_telegraph_plus_verified_ask": {**score(c, t, targets), "cost_usd": run["spent_usd"]},
           "per_package": [{"target": x, "affected": t[x], "A": a.get(x), "B": b[x], "C": c[x]} for x in targets]}
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("guard_run")
    ap.add_argument("mind_alone", nargs="?")
    ap.add_argument("--cases", help="case file (default bench/cases-v2.json), e.g. mind/solana-test/cases.json")
    a = ap.parse_args()
    main(a.guard_run, a.mind_alone, a.cases)
