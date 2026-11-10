#!/usr/bin/env python3
"""Prove the training tokenizer produces the node's token ids on our data.

Why this exists: at the pinned commit 8949b909, Hugging Face currently serves a
tokenizer.json for answerdotai/ModernBERT-base (sha256 9fd55248…, 2,132,967 B) that is a
different serialisation from the file the node pins (sha256 67bc76f8…, 3,583,486 B, from
the telegraph-foundation release). The kit records the downloaded file's hash at training
time and its export guard refuses any other hash, so every run trained against the live Hub
download is refused at export even though the ids are identical. The delta package never
contains a tokenizer: its metadata always carries the node's hash. A package is therefore
correct exactly when training saw the same ids the node will send.

This compares, for every rendered text in our data plus the kit's conformance vectors:
  training ids: transformers.AutoTokenizer("answerdotai/ModernBERT-base"), truncation 512
  node ids:     tokenizers.Tokenizer.from_file(third_party/foundation/tokenizer.json),
                [CLS] … [SEP], truncated to 512 keeping the closing [SEP]
Exit 0 only if every sequence matches.

    python tools/verify_tokenizer.py [files…]   (default: all built data files)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FOUNDATION, KIT, ROOT, read_jsonl, render  # noqa: E402
from token_budget import CLS, SEP, load_tokenizer  # noqa: E402

MAX = 512


def node_ids(tok, text: str) -> list[int]:
    ids = tok.encode(text).ids
    if not ids or ids[0] != CLS:
        ids = [CLS] + ids
    if ids[-1] != SEP:
        ids = ids + [SEP]
    if len(ids) > MAX:
        ids = ids[:MAX - 1] + [SEP]
    return ids


def main(argv=None) -> int:
    files = [Path(f) for f in (argv if argv is not None else sys.argv[1:])]
    if not files:
        files = [p for p in (ROOT / "data").glob("*/*.jsonl") if "meta" not in p.parts and "sources" not in p.parts]
    from transformers import AutoTokenizer
    train_tok = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
    node_tok = load_tokenizer(FOUNDATION / "tokenizer.json")

    texts = []
    for f in files:
        for _, r in read_jsonl(f):
            texts += [render(r["prompt"], r["chosen"]), render(r["prompt"], r["rejected"])]
    vec = KIT / "float_runtime" / "testdata" / "tokenizer_vectors.json"
    vectors = json.loads(vec.read_text())["vectors"] if vec.exists() else []

    bad = 0
    for t in texts:
        a = train_tok(t, truncation=True, max_length=MAX)["input_ids"]
        b = node_ids(node_tok, t)
        if list(a) != b:
            bad += 1
            if bad <= 5:
                print(f"MISMATCH on {t[:70]!r}: training {list(a)[:10]}… node {b[:10]}…")
    for v in vectors:
        a = train_tok(v["text"], add_special_tokens=v["add_special_tokens"])["input_ids"]
        if list(a) != list(v["ids"]):
            bad += 1
            print(f"MISMATCH on kit vector {v['text'][:60]!r}")
    print(f"tokenizer equivalence: {'FAIL' if bad else 'PASS'} "
          f"({len(texts)} rendered texts from {len(files)} files + {len(vectors)} kit vectors, {bad} mismatches)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
