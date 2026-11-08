#!/usr/bin/env python3
"""Fail any pair whose rendered text exceeds the node's 512-token window.

Uses the pinned ModernBERT tokenizer.json (sha256 67bc76f8…c456), the same one validators
use, and the node's render: "### Task:\\n{prompt}\\n\\n### Answer:\\n{answer}" with
[CLS] … [SEP]. Fetch it with: bash scripts/setup_kit.sh --tokenizer

    python tools/token_budget.py data/public/security_review.train.jsonl [--max 512]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FOUNDATION, read_jsonl, render  # noqa: E402

TOKENIZER_SHA = "67bc76f8b9386efba1a761c1c8e5ad439fd0eaf1c2826e9dd1a205c7af4dc456"
CLS, SEP = 50281, 50282


def load_tokenizer(path: Path):
    from tokenizers import Tokenizer
    if hashlib.sha256(path.read_bytes()).hexdigest() != TOKENIZER_SHA:
        raise SystemExit(f"{path}: sha256 differs from the node's pinned tokenizer")
    return Tokenizer.from_file(str(path))


def count(tok, text: str) -> int:
    ids = tok.encode(text).ids
    if not ids or ids[0] != CLS:
        ids = [CLS] + ids
    if ids[-1] != SEP:
        ids = ids + [SEP]
    return len(ids)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--max", type=int, default=512)
    ap.add_argument("--warn", type=int, default=460, help="warn above this (keeps headroom)")
    ap.add_argument("--tokenizer", default=str(FOUNDATION / "tokenizer.json"))
    a = ap.parse_args(argv)
    tok = load_tokenizer(Path(a.tokenizer))
    bad = 0
    for f in a.files:
        lens = []
        for n, r in read_jsonl(Path(f)):
            for side in ("chosen", "rejected"):
                t = count(tok, render(r["prompt"], r[side]))
                lens.append(t)
                if t > a.max:
                    bad += 1
                    print(f"ERROR {f}:{n} {side}: {t} tokens > {a.max} (the node truncates the end)")
                elif t > a.warn:
                    print(f"warn  {f}:{n} {side}: {t} tokens (> {a.warn})")
        if lens:
            lens.sort()
            print(f"{f}: {len(lens)} texts, tokens median {lens[len(lens) // 2]}, "
                  f"p95 {lens[int(len(lens) * .95) - 1]}, max {lens[-1]}")
    print(f"token budget: {'FAIL' if bad else 'PASS'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
