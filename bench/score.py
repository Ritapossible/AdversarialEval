#!/usr/bin/env python3
"""Score bench/out/calls.ndjson under the frozen rule in bench/RULE.md.

    python bench/score.py            # prints the leaderboard as markdown, writes bench/out/scored.json
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = {c["id"]: c for c in json.loads((HERE / "cases.json").read_text())["cases"]}
OK_VERDICTS = {"Secure", "Needs changes", "Insecure"}
ABSTAIN_WORDS = ("not found", "no such", "does not exist", "doesn't exist", "unknown package", "could not find",
                 "cannot find", "can't find", "no package", "not exist", "unable to find", "no record")


def grade(rec: dict) -> str:
    case = CASES[rec["case"]]
    res = rec.get("result") if rec.get("http") == 200 else None
    affected = case["truth"]["affected"]
    if affected is None:  # unknown package
        if not res:
            return "correct"  # abstained / errored
        text = json.dumps(res).lower()
        if any(w in text for w in ABSTAIN_WORDS):
            return "correct"
        verdict, count = res.get("verdict"), res.get("vulnerability_count")
        if (count or 0) >= 1 or res.get("issues"):
            return "wrong"
        if verdict == "Secure":
            return "unverifiable"
        return "no answer" if verdict not in OK_VERDICTS else "wrong"
    if not res:
        return "no answer"
    verdict, count = res.get("verdict"), res.get("vulnerability_count")
    if verdict not in OK_VERDICTS:
        return "no answer"
    if affected:
        return "correct" if verdict in ("Insecure", "Needs changes") and isinstance(count, (int, float)) and count >= 1 else "wrong"
    return "correct" if verdict == "Secure" and count == 0 else "wrong"


def main() -> None:
    recs = [json.loads(l) for l in (HERE / "out" / "calls.ndjson").read_text().splitlines() if l.strip()]
    by = defaultdict(list)
    for r in recs:
        r["grade"] = grade(r)
        by[(r["miner_id"], r["miner"], r["rank"])].append(r)
    rows = []
    for (mid, slug, rank), rs in by.items():
        paid = sum(int(r["receipt"]["amount_uusdc"]) for r in rs if isinstance(r.get("receipt"), dict)) / 1e6
        correct = sum(r["grade"] == "correct" for r in rs)
        delivered = sum(r.get("http") == 200 for r in rs)
        lat = [r["duration_ms"] for r in rs if r.get("http") == 200 and r.get("duration_ms") is not None]
        rows.append({"miner_id": mid, "miner": slug, "rank": rank, "calls": len(rs), "delivered": delivered,
                     "correct": correct, "wrong": sum(r["grade"] == "wrong" for r in rs),
                     "no_answer": sum(r["grade"] == "no answer" for r in rs),
                     "unverifiable": sum(r["grade"] == "unverifiable" for r in rs), "paid_usdc": round(paid, 4),
                     "cost_per_correct": round(paid / correct, 4) if correct else None,
                     "median_ms": int(statistics.median(lat)) if lat else None, "max_ms": max(lat) if lat else None,
                     "per_case": {r["case"]: r["grade"] for r in rs}})
    rows.sort(key=lambda x: (-x["correct"], x["cost_per_correct"] or 9e9, x["miner"]))
    (HERE / "out" / "scored.json").write_text(json.dumps({"rows": rows, "calls": recs}, indent=1) + "\n")
    print("| Miner | Node rank | Correct / 7 | Wrong | No answer | Paid (USDC) | Cost per correct | Median ms |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for x in rows:
        cpc = f"${x['cost_per_correct']:.3f}" if x["cost_per_correct"] else "n/a"
        print(f"| `{x['miner']}` | {x['rank'] if x['rank'] is not None else 'n/a'} | {x['correct']} | {x['wrong']} | "
              f"{x['no_answer']}{' (+' + str(x['unverifiable']) + ' unverifiable)' if x['unverifiable'] else ''} | "
              f"{x['paid_usdc']:.2f} | {cpc} | {x['median_ms'] if x['median_ms'] is not None else 'n/a'} |")
    total_paid = sum(x["paid_usdc"] for x in rows)
    total_correct = sum(x["correct"] for x in rows)
    print(f"\nTotal: {len(recs)} calls, {total_paid:.2f} USDC paid, {total_correct} verified correct answers"
          f" (${total_paid / total_correct:.3f} per correct answer overall)" if total_correct else "")


if __name__ == "__main__":
    main()
