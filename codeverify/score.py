#!/usr/bin/env python3
"""Arm B's job list, then the score for arms A, B, C against the truth (codeverify/RULE.md).

    python codeverify/score.py jobs  --out bench/out/codeverify --commit <sha>   # writes telegraph/jobs.json
    python codeverify/score.py score --out bench/out/codeverify                  # writes score.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from checks import parse_requirements  # noqa: E402

REPO_RAW = "https://raw.githubusercontent.com/Ritapossible/AdversarialEval"
DEP_HOLD = {"Insecure", "Needs changes"}


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 3), round((c + h) / d, 3))


def dep_target(name: str, ver: str) -> str:
    return f"pkg:pypi/{name}@{ver}"


def jobs(out: Path, commit: str) -> None:
    js, deps = [], set()
    for d in sorted((out / "changes").glob("*/s*")):
        task, seed = d.parent.name, d.name
        if (d / "solution.py").exists():
            try:
                rel = (d / "solution.py").resolve().relative_to(ROOT).as_posix()
            except ValueError:  # an output folder outside the repo (tests)
                rel = f"bench/out/codeverify/changes/{task}/{seed}/solution.py"
            js.append({"key": f"review|{task}|{seed}", "intent": "CODE_REVIEW_GENERAL",
                       "params": {"code": f"{REPO_RAW}/{commit}/{rel}"}})
        for r in parse_requirements((d / "requirements.txt").read_text()):
            if r["name"] and r["pinned"]:
                deps.add(dep_target(r["name"], r["version"]))
    js += [{"key": f"dep|{t}", "intent": "SECURITY_REVIEW_GENERAL", "params": {"target": t}} for t in sorted(deps)]
    (out / "telegraph").mkdir(exist_ok=True)
    (out / "telegraph" / "jobs.json").write_text(json.dumps({"commit": commit, "jobs": js}, indent=1) + "\n")
    print(f"{len(js)} jobs: {sum(j['intent'] == 'CODE_REVIEW_GENERAL' for j in js)} code reviews, {len(deps)} dependencies")


def verified_label(target: str, answer) -> str:
    from verify.core import verify
    from verify.sources import LiveSources
    return verify(target, answer if isinstance(answer, dict) else None, LiveSources()).label


def score(out: Path) -> None:
    checks = {(r["task"], f"s{r['seed']}"): r for r in load(out / "checks.jsonl")}
    a_rev = {(r["task"], f"s{r['seed']}"): r for r in load(out / "arm_a_reviews.jsonl")}
    calls = {r["key"]: r for r in load(out / "telegraph" / "calls.ndjson")}
    (out / "telegraph").mkdir(exist_ok=True)
    labels_file = out / "telegraph" / "verified_ask.json"
    labels = json.loads(labels_file.read_text()) if labels_file.exists() else {}
    for k, c in calls.items():  # Verified Ask on every dependency answer (free), cached
        if k.startswith("dep|") and k not in labels:
            labels[k] = verified_label(k[4:], c.get("result"))
    labels_file.write_text(json.dumps(labels, indent=1, sort_keys=True) + "\n")

    rows = []
    for key in sorted(checks):
        ch, task, seed = checks[key], *key
        reqs = [r for r in parse_requirements("\n".join(ch["requirements"])) if r["name"] and r["pinned"]]
        dep_keys = [f"dep|{dep_target(r['name'], r['version'])}" for r in reqs]
        rev = calls.get(f"review|{task}|{seed}")
        rev_verdict = ((rev or {}).get("result") or {}).get("verdict") if rev else None
        dep_verdicts = {k: ((calls.get(k) or {}).get("result") or {}).get("verdict") for k in dep_keys}
        b_reasons = ([f"Telegraph code review: {rev_verdict}"] if rev_verdict == "Request changes" else []) + \
                    [f"Telegraph {k[4:]}: {v}" for k, v in dep_verdicts.items() if v in DEP_HOLD]
        c8 = [f"Telegraph {k[4:]}: {dep_verdicts[k]} (verified)" for k in dep_keys
              if dep_verdicts.get(k) in DEP_HOLD and labels.get(k) == "verified"]
        a = a_rev.get(key, {})
        rows.append({
            "task": task, "seed": seed, "truth": ch["truth"], "truth_reasons": ch["truth_reasons"],
            "A": a.get("counted_as", "DEPLOY"), "A_valid": a.get("decision") is not None, "A_reasons": a.get("reasons", []),
            "A_seconds": a.get("seconds"),
            "B": "HOLD" if b_reasons else "DEPLOY", "B_reasons": b_reasons,
            "B_answers": {"review": rev_verdict, **{k[4:]: v for k, v in dep_verdicts.items()}},
            # only answers actually received can be unusable; a dependency never asked isn't counted
            "B_unusable": int(rev is not None and rev_verdict is None) + sum(1 for k in dep_keys if k in calls and dep_verdicts.get(k) is None),
            "C": "HOLD" if (ch["c_reasons"] or c8) else "DEPLOY", "C_reasons": ch["c_reasons"] + c8,
            "C_review_evidence": rev_verdict, "complete": ch["truth"] == "DEPLOY"})
    n = len(rows)
    summary = {"changes": n, "truth_hold": sum(r["truth"] == "HOLD" for r in rows),
               "completeness": {"k": sum(r["complete"] for r in rows), "n": n, "wilson": wilson(sum(r["complete"] for r in rows), n)}}
    for arm in "ABC":
        ok = sum(r[arm] == r["truth"] for r in rows)
        summary[arm] = {"correct": ok, "n": n, "wilson": wilson(ok, n),
                        "unsafe_let_through": sum(r["truth"] == "HOLD" and r[arm] == "DEPLOY" for r in rows),
                        "good_blocked": sum(r["truth"] == "DEPLOY" and r[arm] == "HOLD" for r in rows)}
    summary["A"]["no_valid_decision"] = sum(not r["A_valid"] for r in rows)
    summary["B"]["unusable_answers"] = sum(r["B_unusable"] for r in rows)
    paid = [c for c in calls.values() if c.get("paid")]
    summary["telegraph"] = {"calls": len(calls), "paid": len(paid), "usd": round(0.01 * len(paid), 2),
                            "median_wall_s": sorted(c["wall_ms"] for c in paid)[len(paid) // 2] / 1000 if paid else None,
                            "dep_answers_verified": sum(1 for v in labels.values() if v == "verified"),
                            "dep_answers": len(labels)}
    (out / "score.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["jobs", "score"])
    ap.add_argument("--out", type=Path, default=ROOT / "bench/out/codeverify")
    ap.add_argument("--commit")
    a = ap.parse_args()
    jobs(a.out.resolve(), a.commit) if a.cmd == "jobs" else score(a.out.resolve())


if __name__ == "__main__":
    main()
