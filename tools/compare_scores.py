#!/usr/bin/env python3
"""Compare WASM-engine scores (tools/remotecheck --out) with PyTorch scores (eval/score.py --json).

    python tools/compare_scores.py runs/<run>/rehearsal/wasm_scores.json runs/<run>/scores.json

Reports pair-ordering agreement and the largest absolute score difference. Agreement
on every pair means the PyTorch analysis in eval/reports transfers to the node's engine.
"""
from __future__ import annotations

import json
import sys


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        raise SystemExit(__doc__)
    wasm = json.load(open(argv[0]))
    torch_scores = {r["row_id"]: r for r in json.load(open(argv[1]))}
    agree = n = 0
    max_diff = 0.0
    flips = []
    for r in wasm:
        q = torch_scores.get(r["row_id"])
        if q is None:
            continue
        n += 1
        same = (r["chosen"] > r["rejected"]) == (q["chosen"] > q["rejected"])
        agree += same
        if not same:
            flips.append(r["row_id"][:12])
        max_diff = max(max_diff, abs(r["chosen"] - q["chosen"]), abs(r["rejected"] - q["rejected"]))
    if not n:
        raise SystemExit("no overlapping rows")
    print(f"WASM vs PyTorch: ordering agrees on {agree}/{n} pairs; max |score diff| {max_diff:.2e}"
          + (f"; flipped: {', '.join(flips)}" if flips else ""))
    return 0 if agree == n else 1


if __name__ == "__main__":
    sys.exit(main())
