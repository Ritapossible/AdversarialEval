#!/usr/bin/env python3
"""Validate authored pairs and build the node / kit files from them.

Authoring files (one pair per line, rich metadata):
    data/authoring/<intent_lower>/*.jsonl          public + validation pairs (committed)
    data/private/authoring/<intent_lower>/*.jsonl  pool pairs (git-ignored, never published)

Outputs, per split:
    data/public/<stem>.train.jsonl, data/validation/<stem>.val.jsonl,
    data/private/<child>.pool.jsonl                     -> {prompt, chosen, rejected, label_kind, provenance}
    data/meta/<stem>.<split>.meta.jsonl                 -> sidecar labels joined on row_id

    python tools/build.py [--intent SECURITY_REVIEW] [--strict]

Hard errors stop the build. Warnings print; --strict turns them into errors.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ADVISORY_ID, INTENTS, ROOT, load_sources, meta_path, normalise,  # noqa: E402
                    output_path, read_jsonl, row_id, write_jsonl)

FAMILIES = {f"F{i}" for i in range(1, 11)}
VERDICTS = {"Secure", "Needs changes", "Insecure"}
FORMATS = {"prose", "bullets", "json", "mixed"}
REQUIRED = ["case", "family", "split", "prompt", "chosen", "rejected", "source_url",
            "verdict_chosen", "verdict_rejected", "format", "flaw_note", "author"]

# node limits (contribute-evaluation-data.md) and our tighter house limits (DATASET_SPEC.md)
NODE = {"prompt": (16, 16000), "chosen": (8, 32000), "rejected": (8, 32000)}
HOUSE = {"prompt": (16, 1400), "chosen": (120, 1000), "rejected": (120, 1000)}
MAX_LEN_RATIO = 1.25
CWE = re.compile(r"\bCWE-\d+\b")


def check_row(r: dict, where: str, sources: dict, errors: list, warns: list) -> None:
    for k in REQUIRED:
        if r.get(k) in (None, ""):
            errors.append(f"{where}: missing {k}")
    if errors and errors[-1].startswith(where):
        return
    if r["family"] not in FAMILIES:
        errors.append(f"{where}: family {r['family']!r} not in F1..F10")
    if r["split"] not in ("public", "validation", "private"):
        errors.append(f"{where}: bad split {r['split']!r}")
    for k in ("verdict_chosen", "verdict_rejected"):
        if r[k] not in VERDICTS:
            errors.append(f"{where}: {k} {r[k]!r} not in {sorted(VERDICTS)}")
    if r["format"] not in FORMATS:
        errors.append(f"{where}: format {r['format']!r} not in {sorted(FORMATS)}")
    if not str(r["source_url"]).startswith("https://"):
        errors.append(f"{where}: source_url must be https://")
    for k, (lo, hi) in NODE.items():
        n = len(normalise(r[k]))
        if not lo <= n <= hi:
            errors.append(f"{where}: {k} is {n} chars, node allows {lo}..{hi}")
    for k, (lo, hi) in HOUSE.items():
        n = len(normalise(r[k]))
        if not lo <= n <= hi:
            warns.append(f"{where}: {k} is {n} chars, house range {lo}..{hi}")
    a, b = len(r["chosen"]), len(r["rejected"])
    if max(a, b) / max(1, min(a, b)) > MAX_LEN_RATIO:
        warns.append(f"{where}: chosen/rejected length ratio {max(a, b) / min(a, b):.2f} > {MAX_LEN_RATIO}")
    if normalise(r["chosen"]) == normalise(r["rejected"]):
        errors.append(f"{where}: chosen == rejected")
    if "\x00" in r["prompt"] + r["chosen"] + r["rejected"]:
        errors.append(f"{where}: NUL character")

    # advisory-id discipline: real ids only, except declared F1 fabrications in `rejected`
    fab = {x.upper() for x in r.get("fabricated_ids", [])}
    mis = {x.upper() for x in r.get("misattributed_ids", [])}
    if (fab or mis) and r["family"] != "F1":
        warns.append(f"{where}: fabricated_ids/misattributed_ids on a non-F1 row")
    for side in ("prompt", "chosen", "rejected"):
        for m in ADVISORY_ID.findall(r[side]):
            mid = m.upper()
            if mid in fab or mid in mis:
                if side != "rejected":
                    errors.append(f"{where}: trap id {m} appears in {side}")
                continue
            src = sources.get(mid)
            if src is None:
                errors.append(f"{where}: {side} cites {m}, which is not in data/sources "
                              f"(add it to ids.txt, or declare it in fabricated_ids if deliberate)")
            elif src.get("withdrawn") and side == "chosen" and "withdrawn" not in r["chosen"].lower():
                errors.append(f"{where}: chosen cites withdrawn advisory {m} without saying it was withdrawn")
    for m in mis:
        if m not in r["rejected"].upper():
            warns.append(f"{where}: misattributed id {m} not found in rejected")
    for m in fab:
        if m in sources:
            errors.append(f"{where}: {m} is declared fabricated but is a real advisory")
        if m not in r["rejected"].upper():
            warns.append(f"{where}: fabricated id {m} not found in rejected")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", default="SECURITY_REVIEW", choices=sorted(INTENTS))
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    stem, _ = INTENTS[a.intent]
    sources = load_sources()

    files = sorted((ROOT / "data" / "authoring" / stem).glob("*.jsonl"))
    files += sorted((ROOT / "data" / "private" / "authoring" / stem).glob("*.jsonl"))
    if not files:
        print(f"no authoring files for {a.intent}")
        return 1

    errors, warns = [], []
    by_split: dict[str, list[dict]] = defaultdict(list)
    case_split: dict[str, set] = defaultdict(set)
    seen_prompts: dict[str, str] = {}
    for f in files:
        private_file = "private" in f.parts
        for n, r in read_jsonl(f):
            where = f"{f.relative_to(ROOT)}:{n}"
            check_row(r, where, sources, errors, warns)
            if r.get("split") == "private" and not private_file:
                errors.append(f"{where}: a private row lives in a committed file; move it to data/private/authoring/")
            if private_file and r.get("split") != "private":
                errors.append(f"{where}: rows under data/private/ must have split=private")
            key = normalise(r.get("prompt", ""))
            if key in seen_prompts:
                errors.append(f"{where}: duplicate prompt (also {seen_prompts[key]})")
            seen_prompts[key] = where
            case_split[r.get("case")].add(r.get("split"))
            src = sources.get(str(r.get("case", "")).upper())
            if src and src["split"] != r.get("split"):
                errors.append(f"{where}: case {r['case']} is assigned to split {src['split']} in sources")
            by_split[r.get("split")].append(r)
    for case, splits in case_split.items():
        if len(splits) > 1:
            errors.append(f"case {case} straddles splits {sorted(splits)}")

    for w in warns:
        print("warn:", w)
    if a.strict:
        errors += warns
    if errors:
        for e in errors:
            print("ERROR:", e)
        print(f"build: FAIL ({len(errors)} errors)")
        return 1

    for split, rows in sorted(by_split.items()):
        node_rows, meta = [], []
        for r in rows:
            node_rows.append({"prompt": r["prompt"], "chosen": r["chosen"], "rejected": r["rejected"],
                              "label_kind": "preference_pair",
                              "provenance": {"source_kind": r.get("source_kind", "advisory"),
                                             "source_url": r["source_url"]}})
            meta.append({"row_id": row_id(r["prompt"], r["chosen"], r["rejected"]),
                         **{k: v for k, v in r.items() if k not in ("prompt", "chosen", "rejected")}})
        n = write_jsonl(output_path(a.intent, split), node_rows)
        write_jsonl(meta_path(a.intent, split), meta)
        fam = Counter(r["family"] for r in rows)
        ver = Counter(r["verdict_chosen"] for r in rows)
        longer = sum(len(r["chosen"]) > len(r["rejected"]) for r in rows) / len(rows)
        print(f"{split:10} {n:4} pairs -> {output_path(a.intent, split).relative_to(ROOT)}")
        print(f"           families {dict(sorted(fam.items(), key=lambda x: int(x[0][1:])))}")
        print(f"           chosen verdicts {dict(ver)}  chosen-longer {longer:.0%}")
    print(f"build: PASS ({len(warns)} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
