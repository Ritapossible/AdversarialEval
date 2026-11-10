#!/usr/bin/env python3
"""Score preference pairs with a trained adapter and break accuracy down.

Loads answerdotai/ModernBERT-base + the PEFT adapter the kit's train_adapter wrote
(runs/<name>/adapter, head included via modules_to_save), renders each text exactly as the
node does ("### Task:\\n{prompt}\\n\\n### Answer:\\n{answer}"), and scores every text on its
own with no padding, truncated at 512 tokens, as validators do. This is the PyTorch float
path, close to but not bit-identical with the node's WASM engine; it is for analysis, not
for the executor.

    python eval/score.py --adapter runs/SECURITY_REVIEW-cpu-v0/adapter \
        data/validation/security_review.val.jsonl [--md out.md] [--json scores.json] [--probe-pad]

--probe-pad re-scores each pair after appending neutral filler to the rejected answer until
it is ~1.5x the chosen answer's length; a robust judge keeps its preference.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from common import read_jsonl, render, row_id  # noqa: E402

BASE = "answerdotai/ModernBERT-base"
FILLER = (" Additional context: this assessment reflects the information provided in the request"
          " and the standard review checklist used for this kind of target.")


def load(adapter_dir: str):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(BASE)
    base = AutoModelForSequenceClassification.from_pretrained(
        BASE, num_labels=1, torch_dtype=torch.float32, attn_implementation="eager")
    base.config.pad_token_id = tok.pad_token_id
    model = PeftModel.from_pretrained(base, adapter_dir).eval()
    return model, tok


def scorer(model, tok, max_len: int = 512):
    import torch

    @torch.no_grad()
    def score(prompt: str, answer: str) -> float:
        enc = tok(render(prompt, answer), truncation=True, max_length=max_len, return_tensors="pt")
        return float(model(**enc).logits.squeeze())
    return score


def meta_for(data: Path) -> dict:
    stem, split = data.name.split(".")[:2]
    for c in (ROOT / "data" / "meta" / f"{stem}.{split}.meta.jsonl",
              ROOT / "data" / "private" / f"{stem.replace('_general', '')}.{split}.meta.jsonl"):
        if c.exists():
            return {m["row_id"]: m for _, m in read_jsonl(c)}
    return {}


def wilson(k: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion (ties count as half a success)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def table(title: str, groups: dict) -> list[str]:
    lines = [f"| {title} | n | accuracy |", "|---|---|---|"]
    for k in sorted(groups, key=lambda x: (len(str(x)), str(x))):
        v = groups[k]
        lines.append(f"| {k} | {len(v)} | {sum(v) / len(v):.0%} |")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="+")
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--md")
    ap.add_argument("--json")
    ap.add_argument("--probe-pad", action="store_true")
    a = ap.parse_args(argv)

    model, tok = load(a.adapter)
    score = scorer(model, tok)
    out, dump = [f"adapter: `{a.adapter}`", ""], []
    for f in a.data:
        path = Path(f)
        meta = meta_for(path)
        by = defaultdict(lambda: defaultdict(list))
        pad_kept = []
        for _, r in read_jsonl(path):
            m = meta.get(row_id(r["prompt"], r["chosen"], r["rejected"]), {})
            sc, sr = score(r["prompt"], r["chosen"]), score(r["prompt"], r["rejected"])
            ok = 1.0 if sc > sr else 0.5 if sc == sr else 0.0
            longer = "chosen longer" if len(r["chosen"]) > len(r["rejected"]) else "rejected longer"
            for dim, key in (("ALL", "ALL"), ("family", m.get("family", "?")),
                             ("format", m.get("format", "?")), ("length", longer),
                             ("chosen verdict", m.get("verdict_chosen", "?"))):
                by[dim][key].append(ok)
            rec = {"file": str(path), "row_id": m.get("row_id"), "family": m.get("family"), "chosen": sc,
                   "rejected": sr, "correct": ok}
            if a.probe_pad:
                pad = r["rejected"]
                while len(pad) < 1.5 * len(r["chosen"]):
                    pad += FILLER
                sp = score(r["prompt"], pad)
                rec["rejected_padded"] = sp
                if ok == 1.0:
                    pad_kept.append(1.0 if sc > sp else 0.0)
            dump.append(rec)
        n_all = len(by["ALL"]["ALL"])
        acc = sum(by["ALL"]["ALL"]) / n_all
        lo, hi = wilson(sum(by["ALL"]["ALL"]), n_all)
        out += [f"## {path}", "", f"**Pairwise accuracy: {acc:.1%}** ({n_all} pairs; 95% CI {lo:.1%}–{hi:.1%})", ""]
        for dim in ("family", "length", "chosen verdict", "format"):
            out += table(dim, by[dim]) + [""]
        if a.probe_pad and pad_kept:
            out += [f"Padding probe: of the pairs it got right, the adapter still prefers the chosen answer "
                    f"after the rejected one is padded to 1.5x length in {sum(pad_kept) / len(pad_kept):.0%} "
                    f"({len(pad_kept)} pairs).", ""]
    text = "\n".join(out)
    print(text)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(text + "\n")
    if a.json:
        Path(a.json).write_text(json.dumps(dump, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
