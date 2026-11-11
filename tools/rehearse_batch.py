#!/usr/bin/env python3
"""Tokenise preference pairs exactly as a validator does, for a local remote-check rehearsal.

Renders "### Task:\\n{prompt}\\n\\n### Answer:\\n{answer}" and encodes it with the node's
pinned tokenizer.json (third_party/foundation, sha256 67bc76f8…), special tokens included,
truncated to 512 tokens. Writes one JSON file that tools/remotecheck sends to an executor.

    python tools/rehearse_batch.py data/validation/security_review.val.jsonl \
        --out runs/rehearsal/batch.json [--limit 15]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, render, row_id  # noqa: E402

TOKENIZER = ROOT / "third_party" / "foundation" / "tokenizer.json"
TOKENIZER_SHA = "67bc76f8b9386efba1a761c1c8e5ad439fd0eaf1c2826e9dd1a205c7af4dc456"
MAX_TOKENS = 512


def main(argv=None) -> int:
    from tokenizers import Tokenizer

    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    if hashlib.sha256(TOKENIZER.read_bytes()).hexdigest() != TOKENIZER_SHA:
        raise SystemExit(f"{TOKENIZER} is not the node's tokenizer; run scripts/setup_kit.sh --tokenizer")
    tok = Tokenizer.from_file(str(TOKENIZER))
    tok.no_padding()
    tok.enable_truncation(MAX_TOKENS)
    pairs, truncated = [], 0
    for _, r in read_jsonl(Path(a.data)):
        ids = []
        for ans in (r["chosen"], r["rejected"]):
            enc = tok.encode(render(r["prompt"], ans))
            truncated += bool(enc.overflowing)
            ids.append(enc.ids)
        pairs.append({"row_id": row_id(r["prompt"], r["chosen"], r["rejected"]), "chosen": ids[0], "rejected": ids[1]})
        if a.limit and len(pairs) >= a.limit:
            break
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"source": a.data, "pairs": pairs}) + "\n")
    print(f"wrote {len(pairs)} pairs to {a.out}; {truncated} texts truncated at {MAX_TOKENS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
