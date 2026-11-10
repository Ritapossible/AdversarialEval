#!/usr/bin/env python3
"""Verify the F1 trap ids in authoring files against OSV.

- `fabricated_ids` must NOT exist on OSV (HTTP 404). A "made-up" id that turns out to be a
  real advisory for some other package is a misattribution, not a fabrication, and the
  label metadata would be wrong.
- `misattributed_ids` MUST exist on OSV (HTTP 200): a real id cited for the wrong package.

Results are cached in data/sources/id_checks.json so the check runs offline afterwards.

    python tools/check_ids.py [--offline]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_jsonl  # noqa: E402

CACHE = ROOT / "data" / "sources" / "id_checks.json"


def exists(vid: str, cache: dict, offline: bool) -> bool:
    if vid in cache:
        return cache[vid]["exists"]
    if offline:
        raise SystemExit(f"{vid}: not in {CACHE.name} and --offline given")
    try:
        with urllib.request.urlopen("https://api.osv.dev/v1/vulns/" + vid, timeout=30) as r:
            rec = json.load(r)
        cache[vid] = {"exists": True, "summary": (rec.get("summary") or rec.get("details", ""))[:160]}
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        cache[vid] = {"exists": False}
    return cache[vid]["exists"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    files = sorted((ROOT / "data" / "authoring").rglob("*.jsonl"))
    files += sorted((ROOT / "data" / "private" / "authoring").rglob("*.jsonl"))
    errors = checked = 0
    for f in files:
        for n, r in read_jsonl(f):
            where = f"{f.relative_to(ROOT)}:{n}"
            for vid in r.get("fabricated_ids", []):
                checked += 1
                if exists(vid.upper(), cache, a.offline):
                    errors += 1
                    print(f"ERROR {where}: 'fabricated' {vid} is a real advisory "
                          f"({cache[vid.upper()].get('summary', '')[:80]!r}); move it to misattributed_ids")
            for vid in r.get("misattributed_ids", []):
                checked += 1
                if not exists(vid.upper(), cache, a.offline):
                    errors += 1
                    print(f"ERROR {where}: 'misattributed' {vid} does not exist on OSV; it is a fabrication")
    CACHE.write_text(json.dumps(dict(sorted(cache.items())), indent=1) + "\n")
    print(f"id check: {'FAIL' if errors else 'PASS'} ({checked} trap ids)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
