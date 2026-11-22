#!/usr/bin/env python3
"""Replay Verified Ask over benchmark answers we already paid for. No new calls, no spending.

    python -m verify.replay bench/out/round-2 bench/out/round-3 --out bench/out/verify-replay [--offline]

For every call it writes the label and checks (labels.ndjson), and compares labels with the
benchmark's frozen grades (bench/RULE-v2.md) in summary.json. OSV, deps.dev and rubygems.org
responses are cached in <out>/sources-cache.json; --offline re-runs from that cache alone.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))
from benchlib import answer, grade  # noqa: E402

from .core import verify  # noqa: E402
from .sources import LiveSources  # noqa: E402

FREE = ("osv-baseline",)


def load_calls(rounds: list[Path]) -> list[dict]:
    out = []
    for rd in rounds:
        for line in (rd / "calls.ndjson").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["miner_id"] not in FREE:
                    r["round"] = rd.name
                    out.append(r)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rounds", nargs="+", type=Path)
    ap.add_argument("--cases", type=Path, default=ROOT / "bench" / "cases-v2.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    cases = {c["id"]: c for c in json.loads(a.cases.read_text())["cases"]}
    src = LiveSources(a.out / "sources-cache.json", offline=a.offline)
    calls = load_calls(a.rounds)

    def one(r):
        res = answer(r)
        v = verify(r["target"], res, src)
        c = cases[r["case"]]
        g = grade(c, r) if c["kind"] != "format" else grade({**c, "kind": "package"}, r)
        return {"round": r["round"], "case": r["case"], "kind": c["kind"], "miner": r["miner"], "miner_id": r["miner_id"],
                "http": r.get("http"), "grade": g, "label": v.label,
                "checks": [{"name": x.name, "status": x.status, "detail": x.detail} for x in v.checks]}

    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(one, calls))
    src.save()
    with open(a.out / "labels.ndjson", "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    delivered = [x for x in rows if x["http"] == 200]
    pkg = [x for x in delivered if x["kind"] in ("package", "format", "unknown")]
    valid_pkg = [x for x in pkg if x["label"] != "invalid"]
    graded = [x for x in valid_pkg if x["kind"] in ("package", "format")]
    wrong = [x for x in graded if x["grade"] == "wrong"]
    right = [x for x in graded if x["grade"] == "correct"]
    fails = Counter()
    for x in valid_pkg:
        for c in x["checks"]:
            if c["status"] == "fail":
                fails[c["name"]] += 1
    cite_fail_by_miner = defaultdict(int)
    answers_with_bad_citation = 0
    for x in valid_pkg:
        bad = [c for c in x["checks"] if c["name"] == "citation" and c["status"] == "fail"]
        if bad:
            answers_with_bad_citation += 1
            cite_fail_by_miner[x["miner"]] += 1
    summary = {
        "rounds": [r.name for r in a.rounds],
        "calls": len(rows), "delivered": len(delivered),
        "labels_all_delivered": dict(Counter(x["label"] for x in delivered)),
        "package_questions_delivered": len(pkg),
        "labels_package_delivered": dict(Counter(x["label"] for x in pkg)),
        "graded_package_answers_with_verdict": len(graded),
        "wrong": len(wrong), "wrong_contradicted": sum(x["label"] == "contradicted" for x in wrong),
        "wrong_labels": dict(Counter(x["label"] for x in wrong)),
        "correct": len(right), "correct_contradicted": sum(x["label"] == "contradicted" for x in right),
        "correct_labels": dict(Counter(x["label"] for x in right)),
        "failed_checks": dict(fails),
        "answers_with_bad_citation": answers_with_bad_citation,
        "bad_citation_by_miner": dict(sorted(cite_fail_by_miner.items(), key=lambda kv: -kv[1])),
        "unknown_cases": dict(Counter(f"{x['grade']} -> {x['label']}" for x in pkg if x["kind"] == "unknown")),
        "code_labels": dict(Counter(x["label"] for x in delivered if x["kind"] == "code")),
    }
    (a.out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
