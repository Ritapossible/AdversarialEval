#!/usr/bin/env python3
"""Convert an independent reviewer's CSV (templates/test_pairs_template.csv) into test-split
authoring rows (docs/REVIEWER_GUIDE.md).

    python tools/import_reviewer_csv.py reviewer.csv --author alice [--family-guess]

Writes data/authoring/security_review/test/<author>.jsonl with split=test. Reviewers don't
label families or verdicts; we parse the verdict from each answer when it is stated, and
leave family as "F0" (unclassified) for a maintainer to fill in. The build accepts F0 only
in the test split.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

VERDICT = re.compile(r"\b(Secure|Needs changes|Insecure)\b", re.I)
CANON = {"secure": "Secure", "needs changes": "Needs changes", "insecure": "Insecure"}


def verdict_of(text: str) -> str:
    m = VERDICT.search(text)
    return CANON[m.group(1).lower()] if m else "Needs changes"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--author", required=True)
    a = ap.parse_args(argv)
    author = re.sub(r"[^a-zA-Z0-9_-]", "", a.author) or "reviewer"
    out = ROOT / "data" / "authoring" / "security_review" / "test" / f"{author}.jsonl"
    rows = []
    with open(a.csv, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), 1):
            if not (r.get("prompt") or "").strip():
                continue
            fmt = "json" if r["better"].lstrip().startswith("{") else "prose"
            rows.append({
                "case": f"t-{author}-{i:03d}", "family": "F0", "split": "test", "format": fmt,
                "prompt": r["prompt"].strip(), "chosen": r["better"].strip(), "rejected": r["worse"].strip(),
                "source_url": r["source_url"].strip(), "verdict_chosen": verdict_of(r["better"]),
                "verdict_rejected": verdict_of(r["worse"]), "flaw_note": r["what_is_wrong"].strip(),
                "author": f"reviewer:{author}", "reviewed": True, "source_kind": "human",
            })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"wrote {len(rows)} test pairs -> {out.relative_to(ROOT)} (families are F0 until classified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
