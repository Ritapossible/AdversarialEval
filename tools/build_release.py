#!/usr/bin/env python3
"""Build the public dataset release (GitHub release and Hugging Face).

    python tools/build_release.py [--out release/adversarialeval-security-review-v1] [--zip <path>]

Writes data/{train,validation,test}.jsonl (each row: the pair plus its metadata), README.md (the
dataset card, Hugging Face format), LICENSE, NOTICE.md and SHA256SUMS. Refuses to build if any
released row is a near-duplicate of a private pool row (tools/dedup.py; rows our rule already marks
"checked, not a duplicate" are allowed) or if a split fails to join its metadata. data/private/ is
read only for that check and never copied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from common import row_id  # noqa: E402

VERSION = "1.0"
SPLITS = [("train", "data/public/security_review.train.jsonl", "data/meta/security_review.train.meta.jsonl"),
          ("validation", "data/validation/security_review.val.jsonl", "data/meta/security_review.val.meta.jsonl"),
          ("test", "data/test/security_review.test.jsonl", "data/meta/security_review.test.meta.jsonl")]
PRIVATE = ["data/private/security_review_general.pool.jsonl", "data/private/upload_batch2.security_review_general.jsonl",
           "data/private/held_back/g_osv_pool_f8up.jsonl"]
FAMILIES = {"F0": "not labelled (independent test pairs)", "F1": "wrong advisory id", "F2": "version-range error",
            "F3": "missed critical issue", "F4": "context reversal", "F5": "overconfident \"Secure\"", "F6": "false alarm",
            "F7": "inconsistent fields", "F8": "wrong severity or class", "F9": "needless hedging", "F10": "ineffective fix"}
KEEP = ["case", "family", "format", "source_url", "verdict_chosen", "verdict_rejected", "flaw_note", "author", "reviewed"]


def private_overlap() -> list[str]:
    files = [p for p in PRIVATE if (ROOT / p).exists()]
    if not files:
        return []
    released = [s[1] for s in SPLITS]
    out = subprocess.run([sys.executable, str(ROOT / "tools/dedup.py"), *released, *files], cwd=ROOT, capture_output=True, text=True).stdout
    names = [Path(f).name for f in released]
    priv = [Path(f).name for f in files]
    return [l for l in out.splitlines() if l.startswith("ERROR") and any(n in l for n in names) and any(p in l for p in priv)]


def card(counts: dict[str, int], fams: dict[str, dict[str, int]]) -> str:
    fam_rows = "\n".join(f"| {f} | {FAMILIES[f]} | {fams['train'].get(f, 0)} | {fams['validation'].get(f, 0)} | {fams['test'].get(f, 0)} |"
                         for f in sorted(FAMILIES, key=lambda x: int(x[1:])))
    return f"""---
license: mit
language:
- en
pretty_name: AdversarialEval SECURITY_REVIEW preference pairs
size_categories:
- n<1K
task_categories:
- text-classification
tags:
- security
- preference
- reward-model
- dpo
- vulnerability
- telegraph
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.jsonl
  - split: validation
    path: data/validation.jsonl
  - split: test
    path: data/test.jsonl
---

# AdversarialEval: security review preference pairs (v{VERSION})

Pairs of answers to software security questions in which the worse answer is **plausible but wrong
in one decisive, verifiable way**: a real advisory id for the wrong package, a patched version
called vulnerable, a confident "Secure" on vulnerable code, a fix that doesn't fix. A judge that
rewards length, fluency or security keywords picks the wrong answer. A judge that checks the facts
picks the right one.

Built for the `SECURITY_REVIEW` intent on [Telegraph](https://telegraphprotocol.com), Season II.
Project: https://github.com/Ritapossible/AdversarialEval

## Splits

| Split | Pairs | Who wrote them | Review |
|---|---:|---|---|
| train | {counts['train']} | generated from OSV records (`generator:osv-v1`) and drafted with an AI assistant (`claude-draft`) | every advisory fact machine-checked against OSV; not individually human-reviewed |
| validation | {counts['validation']} | the same, in a second voice (`claude-draft-voice2`) | as train |
| test | {counts['test']} | two independent outside authors, Fexx (drafted with GPT-6) and Lino (drafted with Grok) | each author read and revised every pair |

The splits are disjoint (near-duplicate check across all of them), and none of them overlaps
the private material uploaded to Telegraph's evaluation pool, which is not part of this release.

## Fields

| Field | Meaning |
|---|---|
| `id` | SHA-256 row id over prompt, chosen and rejected |
| `prompt` | the question (often with code or a dependency pin) |
| `chosen` | the better answer |
| `rejected` | the worse answer: plausible, wrong in one decisive way |
| `family` | the failure family of the rejected answer (table below) |
| `flaw_note` | what exactly is wrong with the rejected answer |
| `source_url` | the public source that settles it (GitHub advisory, NVD, CWE or vendor docs) |
| `verdict_chosen`, `verdict_rejected` | the verdict each answer gives (Secure, Insecure, Needs changes, ...) |
| `case`, `format`, `author`, `reviewed`, `label_kind`, `provenance` | provenance details |

Rendered for a reward model as `### Task:\\n{{prompt}}\\n\\n### Answer:\\n{{answer}}`. Every row fits in 512
tokens, with the decisive flaw early.

## Failure families

| Family | Meaning | Train | Validation | Test |
|---|---|---:|---:|---:|
{fam_rows}

## Baselines

- **Shortcut judges** (longer answer, shorter answer, more advisory ids, security keywords): at
  most 58% on validation and 60% on test.
- **An adapter trained on the train split** with Telegraph's official kit: 72 to 75% on
  validation and **77.5%** (31/40, 95% CI 62.5 to 87.7%) on the independent test. Details are in
  the project's reports.

## Intended use

Training and evaluating reward models, judges and evaluators for security answers, and checking
that a judge isn't rewarding length or keywords. It is not a vulnerability database: check facts
against the cited source before relying on them.

## Limitations

- **Small:** {sum(counts.values())} pairs.
- **One author style:** train and validation share it, so validation overstates accuracy on other
  authors' material.
- **Mostly machine-checked:** the train and validation pairs are drafted with an AI assistant or
  generated, then checked against OSV by script, not read row by row by a person. The test pairs
  are AI-assisted drafts revised by their human authors.
- **Coverage:** advisory facts are as of November 2026; later advisories can change what is
  vulnerable.

## Licence and attribution

The pairs are released under the MIT licence. The advisory facts they state come from the
**GitHub Advisory Database** (CC BY 4.0, © GitHub, Inc. and contributors,
https://github.com/github/advisory-database) and the PyPA Advisory Database (CC BY 4.0), through
[OSV](https://osv.dev). Keep that attribution when you reuse them. Thanks to Fexx and Lino for
the independent test pairs.

## Citation

```
@misc{{adversarialeval2026,
  title  = {{AdversarialEval: security review preference pairs}},
  author = {{Rita (Ritapossible)}},
  year   = {{2026}},
  url    = {{https://github.com/Ritapossible/AdversarialEval}}
}}
```
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "release" / "adversarialeval-security-review-v1")
    ap.add_argument("--zip", type=Path)
    a = ap.parse_args()
    bad = private_overlap()
    if bad:
        sys.exit("refusing to build: released rows overlap private pool rows:\n" + "\n".join(bad))
    out = a.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    counts, fams = {}, {}
    for name, data, meta in SPLITS:
        m = {x["row_id"]: x for x in map(json.loads, (ROOT / meta).read_text().splitlines())}
        rows = []
        for r in map(json.loads, (ROOT / data).read_text().splitlines()):
            rid = row_id(r["prompt"], r["chosen"], r["rejected"])
            if rid not in m:
                sys.exit(f"{name}: a row has no metadata ({rid[:12]})")
            mm = m[rid]
            rows.append({"id": rid, "prompt": r["prompt"], "chosen": r["chosen"], "rejected": r["rejected"],
                         **{k: mm.get(k) for k in KEEP}, "label_kind": r.get("label_kind"), "provenance": r.get("provenance")})
        (out / "data" / f"{name}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
        counts[name] = len(rows)
        fams[name] = {}
        for x in rows:
            fams[name][x["family"]] = fams[name].get(x["family"], 0) + 1
    (out / "README.md").write_text(card(counts, fams))
    shutil.copy(ROOT / "LICENSE", out / "LICENSE")
    notice = (ROOT / "NOTICE.md").read_text()
    (out / "NOTICE.md").write_text(notice[: notice.index("## NVD data")].rstrip() + "\n")
    sums = []
    for f in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        sums.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(out).as_posix()}")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    if a.zip:
        a.zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(a.zip, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(p for p in out.rglob("*") if p.is_file()):
                z.write(f, f"{out.name}/{f.relative_to(out).as_posix()}")
    print(json.dumps({"out": str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out), "counts": counts,
                      "zip": str(a.zip) if a.zip else None}))


if __name__ == "__main__":
    main()
