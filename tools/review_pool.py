#!/usr/bin/env python3
"""Human review round trip for the eval-pool candidates (audit item U2).

    python tools/review_pool.py export   # -> data/private/review/pool_review.csv
    (a person opens the CSV, reads each pair and its source, fills `decision` and `notes`)
    python tools/review_pool.py apply    # writes decisions back into the authoring files
    python tools/review_pool.py status

`decision` is one of:
  approve  the chosen answer is correct, the rejected one is wrong for the stated reason,
           and the source supports it -> the row gets reviewed: true and a reviewer stamp
  reject   anything else -> the row moves to data/private/review/rejected.jsonl and is
           never uploaded
  (blank)  not reviewed yet -> stays reviewed: false

The reviewer is a human; `apply` refuses decisions without a reviewer name in --reviewer.
Everything here lives under data/private/ (git-ignored). tools/upload_pool.sh refuses to
upload a pool file that contains any row whose meta does not say reviewed: true.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_jsonl, row_id  # noqa: E402

AUTHORING = ROOT / "data" / "private" / "authoring"
REVIEW = ROOT / "data" / "private" / "review"
SHEET = REVIEW / "pool_review.csv"
REJECTED = REVIEW / "rejected.jsonl"
COLUMNS = ["row_id", "file", "line", "family", "kind", "source_url", "label_checked_by",
           "prompt", "chosen", "rejected", "flaw_note", "decision", "notes"]


def rows():
    for f in sorted(AUTHORING.rglob("*.jsonl")):
        for n, r in read_jsonl(f):
            yield f, n, r


def export(_a) -> int:
    REVIEW.mkdir(parents=True, exist_ok=True)
    old = {}
    if SHEET.exists():
        with SHEET.open(newline="") as fh:
            old = {r["row_id"]: r for r in csv.DictReader(fh)}
    out = []
    for f, n, r in rows():
        rid = row_id(r["prompt"], r["chosen"], r["rejected"])
        g = r.get("generator") or {}
        prev = old.get(rid, {})
        out.append({"row_id": rid, "file": str(f.relative_to(ROOT)), "line": n, "family": r["family"],
                    "kind": g.get("kind", ""), "source_url": r["source_url"],
                    "label_checked_by": "OSV version query (tools/verify_generated.py)" if g else "",
                    "prompt": r["prompt"], "chosen": r["chosen"], "rejected": r["rejected"],
                    "flaw_note": r.get("flaw_note", ""),
                    "decision": prev.get("decision", "approve" if r.get("reviewed") else ""),
                    "notes": prev.get("notes", "")})
    with SHEET.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} rows to {SHEET.relative_to(ROOT)} (decisions kept from any earlier sheet)")
    return 0


def apply(a) -> int:
    if not a.reviewer.strip():
        raise SystemExit("--reviewer NAME is required: only a person may mark rows reviewed")
    with SHEET.open(newline="") as fh:
        decisions = {r["row_id"]: (r["decision"].strip().lower(), r["notes"].strip()) for r in csv.DictReader(fh)}
    bad = {d for d, _ in decisions.values()} - {"", "approve", "reject"}
    if bad:
        raise SystemExit(f"unknown decisions {sorted(bad)}; use approve, reject or leave blank")
    counts = {"approve": 0, "reject": 0, "": 0}
    rejected = []
    for f in sorted(AUTHORING.rglob("*.jsonl")):
        kept = []
        for _, r in read_jsonl(f):
            d, notes = decisions.get(row_id(r["prompt"], r["chosen"], r["rejected"]), ("", ""))
            counts[d] += 1
            if d == "reject":
                rejected.append({**r, "review": {"by": a.reviewer, "on": str(date.today()), "notes": notes}})
                continue
            if d == "approve":
                r = {**r, "reviewed": True, "review": {"by": a.reviewer, "on": str(date.today()), "notes": notes}}
            kept.append(r)
        f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept))
    if rejected:
        REVIEW.mkdir(parents=True, exist_ok=True)
        with REJECTED.open("a") as fh:
            fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rejected)
    print(f"approved {counts['approve']}, rejected {counts['reject']}, unreviewed {counts['']}. "
          "Now rerun scripts/check_data.sh (rebuilds the pool file).")
    return 0


def status(_a) -> int:
    total = reviewed = 0
    for _, _, r in rows():
        total += 1
        reviewed += bool(r.get("reviewed"))
    print(f"pool candidates: {total}, reviewed: {reviewed}, unreviewed: {total - reviewed}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export").set_defaults(fn=export)
    p = sub.add_parser("apply")
    p.add_argument("--reviewer", required=True)
    p.set_defaults(fn=apply)
    sub.add_parser("status").set_defaults(fn=status)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
