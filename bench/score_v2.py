#!/usr/bin/env python3
"""Score benchmark rounds under rule v2 (bench/RULE-v2.md).

    python bench/score_v2.py bench/out/round-2 [bench/out/round-3 ...] [--json out.json]

Each round dir holds calls.ndjson (paid calls) and optionally osv-baseline.ndjson. Prints markdown
tables: per round, then pooled. Constant baselines are computed, not called.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchlib import (answer, bootstrap_ratio, charged, charged_onchain, grade, id_match, kendall_tau_b, percentile,  # noqa: E402
                      wilson, VERDICTS)

HERE = Path(__file__).resolve().parent
ANSWERABLE = ("package", "code")


def is_free(rec: dict) -> bool:
    """Baselines are computed or looked up, never bought."""
    mid = str(rec.get("miner_id", ""))
    return bool(rec.get("free")) or mid == "osv-baseline" or mid.startswith("always-")


def load(round_dir: Path) -> list[dict]:
    recs = []
    for name in ("calls.ndjson", "osv-baseline.ndjson"):
        p = round_dir / name
        if p.exists():
            recs += [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return recs


def constant(cases: list[dict], verdict: str, count: int, label: str) -> list[dict]:
    return [{"case": c["id"], "miner_id": label, "miner": label, "rank": None, "http": 200,
             "result": {"verdict": verdict, "vulnerability_count": count, "issues": []}} for c in cases]


def summarise(cases: dict[str, dict], recs: list[dict]) -> dict:
    by_case = {r["case"]: r for r in recs}
    ans = [c for c in cases.values() if c["kind"] in ANSWERABLE]
    grades = {c["id"]: grade(c, by_case[c["id"]]) if c["id"] in by_case else "not called" for c in cases.values()}
    k = sum(grades[c["id"]] == "correct" for c in ans)
    n = sum(grades[c["id"]] != "not called" for c in ans)
    strict = sum(grade(c, by_case[c["id"]], strict=True) == "correct" for c in ans if c["id"] in by_case)
    # bootstrap over every called case (format probes and unknowns cost money too), so the interval
    # describes the same ratio as the point estimate: all USDC charged / correct answerable answers
    called = [c for c in cases.values() if c["id"] in by_case]
    costs = [0.01 if charged(by_case[c["id"]]) else 0.0 for c in called]
    hits = [1 if c["kind"] in ANSWERABLE and grades[c["id"]] == "correct" else 0 for c in called]
    paid = sum(0.01 for r in recs if charged(r))
    paid_onchain = sum(0.01 for r in recs if not is_free(r) and charged_onchain(r))
    receipt_paid = sum(int(r["receipt"]["amount_uusdc"]) / 1e6 for r in recs if isinstance(r.get("receipt"), dict))
    delivered = [r for r in recs if r.get("http") == 200]
    valid = [r for r in delivered if (answer(r) or {}).get("verdict") in VERDICTS]
    lat = [r["duration_ms"] for r in delivered if isinstance(r.get("duration_ms"), (int, float))]
    pkg_aff = [c for c in cases.values() if c["kind"] == "package" and c["truth"]["affected"] and c["id"] in by_case]
    idm = [id_match(c, by_case[c["id"]]) for c in pkg_aff]
    unk = {c["id"]: grades[c["id"]] for c in cases.values() if c["kind"] == "unknown"}
    fmt_agree = []
    for c in cases.values():
        if c["kind"] == "format" and c["id"] in by_case and c["of"] in by_case:
            g_fmt, g_purl = grade(c, by_case[c["id"]]), grades[c["of"]]
            if g_fmt != "no answer" or g_purl != "no answer":  # two failures are not agreement
                fmt_agree.append(g_fmt == g_purl)
    cats = defaultdict(lambda: [0, 0])
    for c in ans:
        key = c["kind"] if c["kind"] == "code" else c["ecosystem"]
        cats[key][1] += 1
        cats[key][0] += grades[c["id"]] == "correct"
    return {
        "calls": len(recs), "answerable_called": n, "correct": k, "accuracy": k / n if n else None,
        "wilson95": wilson(k, n) if n else None, "correct_strict_code": strict,
        "wrong": sum(grades[c["id"]] == "wrong" for c in ans),
        "no_answer": sum(grades[c["id"]] == "no answer" for c in ans),
        "delivered": len(delivered), "valid_verdict": len(valid),
        "charged_usdc": round(paid, 4), "receipt_usdc": round(receipt_paid, 4),
        "cost_per_correct": round(paid / k, 4) if k else None,
        "charged_onchain_usdc": round(paid_onchain, 4),
        "cost_per_correct_onchain": round(paid_onchain / k, 4) if k else None,
        "cost_per_correct_ci95": bootstrap_ratio(costs, hits),
        "median_ms": statistics.median(lat) if lat else None, "p90_ms": percentile(lat, 0.9),
        "id_match": f"{sum(bool(x) for x in idm)}/{len(idm)}" if idm else None,
        "unknown": unk, "format_agreement": f"{sum(fmt_agree)}/{len(fmt_agree)}" if fmt_agree else None,
        "by_category": {k2: f"{v[0]}/{v[1]}" for k2, v in sorted(cats.items())},
        "grades": grades,
    }


def table(rows: list[tuple[str, dict, dict]]) -> str:
    out = ["| Target | Node rank | Correct / answerable | Accuracy (95% CI) | Valid verdicts / delivered / calls | Charged: headers / on-chain | Cost per correct (95% CI) | Cost per correct, on-chain | Median ms |",
           "|---|---:|---:|---|---:|---:|---|---:|---:|"]
    for name, meta, s in rows:
        acc = f"{s['accuracy']:.0%} ({s['wilson95'][0]:.0%} to {s['wilson95'][1]:.0%})" if s["accuracy"] is not None else "n/a"
        cpc = "n/a"
        if s["cost_per_correct"] is not None:
            ci = s["cost_per_correct_ci95"]
            cpc = f"${s['cost_per_correct']:.3f}" + (f" (${ci[0]:.3f} to ${ci[1]:.3f})" if ci else "")
        rank = meta.get("rank")
        out.append(f"| {name} | {rank if rank is not None else ('n/a' if meta.get('special') else 'unranked')} | "
                   f"{s['correct']}/{s['answerable_called']} | {acc} | {s['valid_verdict']}/{s['delivered']}/{s['calls']} | "
                   f"${s['charged_usdc']:.2f} / ${s['charged_onchain_usdc']:.2f} | {cpc} | "
                   f"{'$' + format(s['cost_per_correct_onchain'], '.3f') if s['cost_per_correct_onchain'] is not None else 'n/a'} | "
                   f"{int(s['median_ms']) if s['median_ms'] is not None else 'n/a'} |")
    return "\n".join(out)


def score_rounds(round_dirs: list[Path], cases_path: Path) -> dict:
    cases = {c["id"]: c for c in json.loads(cases_path.read_text())["cases"]}
    result = {"rounds": {}, "pooled": {}}
    pooled = defaultdict(list)
    meta = {}
    for rd in round_dirs:
        recs = load(rd)
        by_target = defaultdict(list)
        for r in recs:
            by_target[r["miner_id"]].append(r)
            meta.setdefault(r["miner_id"], {"name": r["miner"], "rank": r.get("rank"),
                                            "special": r["miner_id"] in ("routed", "osv-baseline")})
        round_res = {}
        for tid, rs in by_target.items():
            round_res[tid] = summarise(cases, rs)
            pooled[tid].append(round_res[tid])
        ranked = [(meta[t]["rank"], s["accuracy"]) for t, s in round_res.items()
                  if meta[t]["rank"] is not None and s["accuracy"] is not None]
        # lower rank number = better, so correlate -rank with accuracy
        tau = kendall_tau_b([-r for r, _ in ranked], [a for _, a in ranked])
        result["rounds"][rd.name] = {"targets": round_res, "kendall_tau_rank_vs_accuracy": tau, "n_ranked": len(ranked)}
    for label, verdict, count in (("always-insecure", "Insecure", 1), ("always-secure", "Secure", 0)):
        meta[label] = {"name": label, "rank": None, "special": True}
        pooled[label] = [summarise(cases, constant(list(cases.values()), verdict, count, label))]
    result["meta"] = meta
    result["pooled_raw"] = pooled
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rounds", nargs="+", type=Path)
    ap.add_argument("--cases", type=Path, default=HERE / "cases-v2.json")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    res = score_rounds(a.rounds, a.cases)
    meta = res["meta"]
    for rname, rr in res["rounds"].items():
        rows = sorted(((meta[t]["name"], meta[t], s) for t, s in rr["targets"].items()),
                      key=lambda x: (-(x[2]["accuracy"] or 0), x[2]["cost_per_correct"] or 9e9))
        tau = rr["kendall_tau_rank_vs_accuracy"]
        print(f"\n### {rname}\n\n{table(rows)}\n\nKendall's tau-b, node rank vs accuracy over {rr['n_ranked']} ranked miners: "
              f"{tau:+.2f}" if tau is not None else f"\n### {rname}\n\n{table(rows)}\n")
    if a.json:
        slim = {k: v for k, v in res.items() if k != "pooled_raw"}
        a.json.write_text(json.dumps(slim, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
