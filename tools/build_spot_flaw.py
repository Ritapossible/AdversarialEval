#!/usr/bin/env python3
"""Build the "Spot the Flaw" demo page from the PUBLIC training set.

    python tools/build_spot_flaw.py [--model-scores runs/<run>/demo_scores.json ...]

--model-scores takes eval/score.py --json outputs for adapters trained WITHOUT these demo
pairs (see runs/frozen/demo_row_ids.txt). The page then shows what the adapter picked in
each training run. Never pass scores from a run that trained on the demo pairs.

Writes
  site/spot-the-flaw.html  page body (title, style, markup, script) for the claude.ai artifact
  site/index.html          the same page as a full HTML document, for GitHub Pages

Only data/public/ rows are used: validation is published after the hackathon and
data/private/ is never published (CLAUDE.md rule 1). Pairs are chosen by a fixed rule
(per family, shortest readable hand-written pairs first, then generated ones), never by
whether any model got them right. Answer positions are shuffled with a fixed seed.
The two shortcut judges are the same scorers as eval/baselines.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, row_id  # noqa: E402

TEMPLATE = ROOT / "tools" / "spot_flaw_template.html"
OUT = ROOT / "site"
SEC = re.compile(r"\b(cve|ghsa|cwe|owasp|vulnerab\w*|inject\w*|exploit\w*|critical|rce|"
                 r"xss|ssrf|traversal|insecure|attack\w*|malicious|unsafe|leak\w*)\b", re.I)
FAMILIES = {
    "F1": ("Wrong advisory id", "Cites a CVE/GHSA that doesn't exist, or a real one that belongs to a different package."),
    "F2": ("Version-range error", "Calls a patched version vulnerable, or an affected version safe."),
    "F3": ("Missed critical", "Lists real minor issues but misses the one that matters most."),
    "F4": ("Context reversal", "Applies a pattern rule while ignoring context that flips the verdict."),
    "F5": ("Overconfident \"Secure\"", "Declares vulnerable code safe, confidently."),
    "F6": ("False alarm", "Invents a vulnerability in code that is actually safe."),
    "F7": ("Inconsistent fields", "Verdict, issue count and issue list contradict each other."),
    "F8": ("Wrong severity or class", "Right bug, wrong severity or wrong vulnerability class."),
    "F9": ("Needless hedging", "Refuses to commit when the evidence is decisive."),
    "F10": ("Ineffective fix", "Recommends a fix that a simple counterexample defeats."),
}
PER_FAMILY = {"F1": 2, "F2": 2, "F3": 2, "F4": 2, "F5": 2, "F6": 2, "F7": 1, "F8": 1, "F9": 1, "F10": 2}
MAX_PROMPT, MAX_ANSWER = 700, 650

# Measured on the 87-pair validation set (eval/reports/2026-11-11-cpu-v3-seed*.md and the
# baselines in scripts/check_data.sh). Same-author data: not an independent test.
STATS = {"longer": 57, "keywords": 58, "model_lo": 72.4, "model_hi": 74.7, "n": 87}


def model_pick(run: dict, rid: str, held: set) -> str:
    if rid not in held:
        raise SystemExit(f"{rid[:12]} is not in runs/frozen/demo_row_ids.txt: refusing to show a training-set score")
    r = run.get(rid)
    if r is None:
        raise SystemExit(f"{rid[:12]}: no score in the given --model-scores file")
    return pick(r["chosen"], r["rejected"])


def pick(a: float, b: float) -> str:
    return "chosen" if a > b else "rejected" if a < b else "tie"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-scores", nargs="*", default=[])
    ap.add_argument("--model-note", default="")
    a = ap.parse_args(argv)
    held = set((ROOT / "runs" / "frozen" / "demo_row_ids.txt").read_text().split()) if a.model_scores else set()
    runs = []
    for f in a.model_scores:
        recs = {r["row_id"]: r for r in json.loads(Path(f).read_text()) if r.get("row_id")}
        runs.append(recs)
    rows = [r for _, r in read_jsonl(ROOT / "data" / "public" / "security_review.train.jsonl")]
    meta = {m["row_id"]: m for _, m in read_jsonl(ROOT / "data" / "meta" / "security_review.train.meta.jsonl")}
    by_family: dict[str, list] = {}
    for r in rows:
        m = meta[row_id(r["prompt"], r["chosen"], r["rejected"])]
        if len(r["prompt"]) > MAX_PROMPT or max(len(r["chosen"]), len(r["rejected"])) > MAX_ANSWER:
            continue
        by_family.setdefault(m["family"], []).append((r, m))
    cases = []
    for fam, n in PER_FAMILY.items():
        cands = sorted(by_family.get(fam, []),
                       key=lambda rm: (bool(rm[1].get("generator")),  # hand-written first
                                       len(rm[0]["prompt"]) + len(rm[0]["chosen"]) + len(rm[0]["rejected"])))
        seen_cases = set()
        for r, m in cands:
            if len([c for c in cases if c["family"] == fam]) >= n:
                break
            if m["case"] in seen_cases:
                continue
            seen_cases.add(m["case"])
            h = int(hashlib.sha256(m["row_id"].encode()).hexdigest(), 16)
            chosen_first = h % 2 == 0
            cases.append({
                "id": m["row_id"][:10],
                "family": fam,
                "family_name": FAMILIES[fam][0],
                "family_desc": FAMILIES[fam][1],
                "prompt": r["prompt"],
                "a": r["chosen"] if chosen_first else r["rejected"],
                "b": r["rejected"] if chosen_first else r["chosen"],
                "correct": "a" if chosen_first else "b",
                "flaw": m.get("flaw_note", ""),
                "source": m["source_url"],
                "generated": bool(m.get("generator")),
                "longer": pick(len(r["chosen"]), len(r["rejected"])),
                "keywords": pick(len(SEC.findall(r["chosen"])), len(SEC.findall(r["rejected"]))),
                "model": [model_pick(run, m["row_id"], held) for run in runs] if runs else None,
            })
    # interleave families with a fixed order so similar cases don't cluster
    cases.sort(key=lambda c: hashlib.sha256(("order" + c["id"]).encode()).hexdigest())
    payload = {"cases": cases, "stats": STATS, "families": FAMILIES,
               "model_note": a.model_note if runs else ""}
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    body = TEMPLATE.read_text().replace("__DATA__", data)
    OUT.mkdir(exist_ok=True)
    (OUT / "spot-the-flaw.html").write_text(body)
    (OUT / "index.html").write_text(
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        "</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    fams = sorted({c["family"] for c in cases}, key=lambda f: int(f[1:]))
    print(f"wrote {len(cases)} cases ({', '.join(fams)}) to site/; "
          f"longer-answer judge right on {sum(c['longer'] == 'chosen' for c in cases)}, "
          f"keyword judge right on {sum(c['keywords'] == 'chosen' for c in cases)}"
          + (f", adapter right on {[sum(c['model'][k] == 'chosen' for c in cases) for k in range(len(runs))]} per run"
             if runs else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
