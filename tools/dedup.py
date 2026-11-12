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

    # Exact speedups (same verdicts and numbers as comparing every pair in full):
    # - SequenceMatcher caches its index of the SECOND sequence, so the outer loop fixes
    #   seq2 = items[j] and the inner loop varies seq1 = items[i] (i < j): the same (a, b)
    #   order as before, so ratio() is unchanged;
    # - real_quick_ratio() and quick_ratio() are upper bounds of ratio(): when the larger of
    #   them and the Jaccard score is below the warning level, the pair can't be flagged.
    found = []
    sm = difflib.SequenceMatcher(None, autojunk=False)
    for j in range(len(items)):
        wj, sj, tj, shj = items[j]
        sm.set_seq2(tj)
        for i in range(j):
            wi, si, ti, shi = items[i]
            jac = len(shi & shj) / max(1, len(shi | shj))
            sm.set_seq1(ti)
            if jac < a.warn and (sm.real_quick_ratio() < a.warn or sm.quick_ratio() < a.warn):
                continue
            sim = max(jac, sm.ratio())
            cross = si != sj
            if sim >= a.threshold or (cross and sim >= a.warn):
                found.append((i, j, "ERROR", f"ERROR {wi} ~ {wj}: similarity {sim:.2f}{' (cross-split)' if cross else ''}"))
            elif sim >= a.warn:
                found.append((i, j, "warn", f"warn  {wi} ~ {wj}: similarity {sim:.2f}"))
    found.sort()
    for *_, line in found:
        print(line)
    errors = sum(k == "ERROR" for _, _, k, _ in found)
    warns = len(found) - errors
    print(f"dedup: {'FAIL' if errors else 'PASS'} ({len(items)} prompts, {warns} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
