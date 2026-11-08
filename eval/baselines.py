#!/usr/bin/env python3
"""Naive scorers the data must defeat, overall and per failure family.

Each scorer picks one answer of a pair without understanding it. Pairwise accuracy
(ties = 0.5) near 50% means the scorer has no shortcut; near 100% means the data has a
tell. Also runs the kit's own dataset gate (unique negatives, length shortcut, leakage,
question-blind bag-of-words probe) so the numbers match what train_adapter enforces.

    python eval/baselines.py data/public/security_review.train.jsonl [--meta …] [--md out.md]
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from common import KIT, read_jsonl, row_id  # noqa: E402

TOK = re.compile(r"[a-z0-9']+")
SEC = re.compile(r"\b(cve|ghsa|cwe|owasp|vulnerab\w*|inject\w*|exploit\w*|critical|rce|"
                 r"xss|ssrf|traversal|insecure|attack\w*|malicious|unsafe|leak\w*)\b", re.I)
HEDGE = re.compile(r"\b(may|might|could|possibly|potentially|likely|unclear|unknown|cannot|"
                   r"can't|not enough|depends|appears|seems|recommend verifying|unverified)\b", re.I)


def toks(s: str) -> list[str]:
    return TOK.findall(s.lower())


def pick(a: float, b: float) -> float:
    return 1.0 if a > b else 0.0 if a < b else 0.5


def tfidf_factory(rows):
    df, n = Counter(), 0
    for r in rows:
        for t in (r["prompt"], r["chosen"], r["rejected"]):
            df.update(set(toks(t)))
            n += 1

    def vec(s):
        c = Counter(toks(s))
        v = {w: k * math.log((1 + n) / (1 + df[w])) for w, k in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}

    def cos(a, b):
        va, vb = vec(a), vec(b)
        return sum(x * vb.get(w, 0.0) for w, x in va.items())
    return cos


def scorers(rows):
    cos = tfidf_factory(rows)

    def overlap(p, a):
        sp, sa = set(toks(p)), set(toks(a))
        return len(sp & sa) / max(1, len(sa))

    return {
        "longer-wins": lambda r: pick(len(r["chosen"]), len(r["rejected"])),
        "shorter-wins": lambda r: pick(-len(r["chosen"]), -len(r["rejected"])),
        "prompt-overlap": lambda r: pick(overlap(r["prompt"], r["chosen"]), overlap(r["prompt"], r["rejected"])),
        "tfidf-to-prompt": lambda r: pick(cos(r["prompt"], r["chosen"]), cos(r["prompt"], r["rejected"])),
        "more-security-terms": lambda r: pick(len(SEC.findall(r["chosen"])), len(SEC.findall(r["rejected"]))),
        "fewer-hedges": lambda r: pick(-len(HEDGE.findall(r["chosen"])), -len(HEDGE.findall(r["rejected"]))),
        "more-hedges": lambda r: pick(len(HEDGE.findall(r["chosen"])), len(HEDGE.findall(r["rejected"]))),
        "more-ids-cited": lambda r: pick(len(re.findall(r"CVE-|GHSA-|CWE-", r["chosen"])),
                                         len(re.findall(r"CVE-|GHSA-|CWE-", r["rejected"]))),
    }


def kit_gate(rows):
    sys.path.insert(0, str(KIT))
    try:
        from float_runtime.train_adapter import Hyperparams, gate_dataset
    except Exception as e:  # kit missing or import error
        return {"error": f"kit import failed: {e}"}
    return gate_dataset([{"prompt": r["prompt"], "chosen": r["chosen"], "rejected": r["rejected"],
                          "margin": 0.0} for r in rows], Hyperparams())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--meta", help="sidecar meta jsonl (default: guessed from data path)")
    ap.add_argument("--md", help="also write a markdown table here")
    ap.add_argument("--max-acc", type=float, default=0.60, help="target ceiling for every naive scorer")
    a = ap.parse_args(argv)

    rows = [r for _, r in read_jsonl(Path(a.data))]
    meta_file = Path(a.meta) if a.meta else None
    if meta_file is None:
        p = Path(a.data)
        stem, split = p.name.split(".")[0], p.name.split(".")[1]
        cand = [ROOT / "data" / "meta" / f"{stem}.{split}.meta.jsonl",
                ROOT / "data" / "private" / f"{stem.replace('_general', '')}.{split}.meta.jsonl"]
        meta_file = next((c for c in cand if c.exists()), None)
    fam = {}
    if meta_file and meta_file.exists():
        fam = {m["row_id"]: m.get("family", "?") for _, m in read_jsonl(meta_file)}
    for r in rows:
        r["_family"] = fam.get(row_id(r["prompt"], r["chosen"], r["rejected"]), "?")

    sc = scorers(rows)
    families = sorted({r["_family"] for r in rows}, key=lambda f: (len(f), f))
    table = {}
    for name, fn in sc.items():
        per = defaultdict(list)
        for r in rows:
            v = fn(r)
            per["ALL"].append(v)
            per[r["_family"]].append(v)
        table[name] = {k: sum(v) / len(v) for k, v in per.items()}

    cols = ["ALL"] + families
    counts = Counter(r["_family"] for r in rows)
    lines = [f"| scorer | " + " | ".join(f"{c} (n={len(rows) if c == 'ALL' else counts[c]})" for c in cols) + " |",
             "|---|" + "---|" * len(cols)]
    worst = 0.0
    for name, accs in table.items():
        worst = max(worst, accs["ALL"])
        lines.append(f"| {name} | " + " | ".join(f"{accs.get(c, float('nan')):.0%}" for c in cols) + " |")

    gate = kit_gate(rows)
    out = [f"naive baselines on {a.data} ({len(rows)} pairs)", "", *lines, ""]
    if "error" in gate:
        out.append(f"kit dataset gate: {gate['error']}")
    else:
        out.append(f"kit dataset gate: {'PASS' if gate['ok'] else 'FAIL'}  {gate['metrics']}")
        out += [f"  x {f}" for f in gate["failures"]]
    verdict = worst <= a.max_acc
    out.append(f"strongest naive scorer overall: {worst:.0%} "
               f"({'within' if verdict else 'ABOVE'} the {a.max_acc:.0%} target)")
    print("\n".join(out))
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text("\n".join(out) + "\n")
    return 0 if verdict and gate.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
