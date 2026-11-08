#!/usr/bin/env python3
"""Find near-duplicate prompts within and across splits.

The node rejects a prompt that is "85% or more similar" to an existing question in the
pool. Its exact metric is not published, so this flags a pair if EITHER of two common
measures reaches the threshold on normalised prompts: difflib's sequence ratio, or the
Jaccard similarity of character 5-gram shingles. Cross-split near-duplicates are always
errors (they would leak between train and validation, or between public and pool).

    python tools/dedup.py data/public/*.jsonl data/validation/*.jsonl data/private/*.pool.jsonl
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import normalise, read_jsonl  # noqa: E402


def shingles(s: str, k: int = 5) -> set[str]:
    s = s.lower()
    return {s[i:i + k] for i in range(max(1, len(s) - k + 1))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--warn", type=float, default=0.70)
    a = ap.parse_args(argv)

    items = []
    for f in a.files:
        p = Path(f)
        if not p.exists():
            continue
        for n, r in read_jsonl(p):
            t = normalise(r["prompt"])
            items.append((f"{p.name}:{n}", p.parent.name, t, shingles(t)))

    errors = warns = 0
    for i in range(len(items)):
        wi, si, ti, shi = items[i]
        for j in range(i + 1, len(items)):
            wj, sj, tj, shj = items[j]
            jac = len(shi & shj) / max(1, len(shi | shj))
            if jac < a.warn * 0.6 and abs(len(ti) - len(tj)) > 0.5 * max(len(ti), len(tj)):
                continue  # cheap skip: clearly different
            seq = difflib.SequenceMatcher(None, ti, tj, autojunk=False).ratio()
            sim = max(jac, seq)
            cross = si != sj
            if sim >= a.threshold or (cross and sim >= a.warn):
                errors += 1
                print(f"ERROR {wi} ~ {wj}: similarity {sim:.2f}{' (cross-split)' if cross else ''}")
            elif sim >= a.warn:
                warns += 1
                print(f"warn  {wi} ~ {wj}: similarity {sim:.2f}")
    print(f"dedup: {'FAIL' if errors else 'PASS'} ({len(items)} prompts, {warns} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
