#!/usr/bin/env python3
"""Independently verify every generated pair's label with OSV's own version matching.

tools/gen_osv_pairs.py computes "is version V affected by advisory A" itself. This check
does not trust that code: for each generated row it asks OSV directly
(POST /v1/query {package, version}), which returns the advisories OSV considers to affect
exactly that version, and compares:

  F2-in, F7, F8, F1  -> the row claims V IS affected  -> A must be in OSV's answer
  F2-out             -> the row claims V is NOT affected -> A must be absent

Answers are cached in data/sources/osv_version/ so the check reruns offline.

    python tools/verify_generated.py [--offline]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_jsonl  # noqa: E402

GEN = ROOT / "data" / "authoring" / "security_review" / "g_osv_generated.jsonl"
CACHE = ROOT / "data" / "sources" / "osv_version"
AMBIGUOUS = ROOT / "data" / "sources" / "ambiguous_advisories.txt"


def affecting(eco: str, name: str, version: str, offline: bool) -> set[str]:
    p = CACHE / f"{eco}-{name}-{version}.json"
    if p.exists():
        return set(json.loads(p.read_text()))
    if offline:
        raise SystemExit(f"{p.name} not cached and --offline given")
    ids, token = set(), None
    while True:
        body = {"package": {"name": name, "ecosystem": eco}, "version": version}
        if token:
            body["page_token"] = token
        req = urllib.request.Request("https://api.osv.dev/v1/query", data=json.dumps(body).encode(), method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        for v in d.get("vulns", []):
            ids.add(v["id"])
            ids.update(v.get("aliases", []))
        token = d.get("next_page_token")
        if not token:
            break
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(ids)) + "\n")
    return ids


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--record-ambiguous", action="store_true",
                    help=f"append mislabelled advisory ids to {AMBIGUOUS.name}; gen_osv_pairs.py then skips them")
    a = ap.parse_args(argv)
    if not GEN.exists():
        print("no generated pairs")
        return 0
    bad = n = 0
    ambiguous = set()
    for line, r in read_jsonl(GEN):
        g = r["generator"]
        ids = affecting(g["ecosystem"], g["package"], g["version"], a.offline)
        claims_affected = g["kind"] != "F2-out"
        is_affected = r["case"] in ids
        n += 1
        if claims_affected != is_affected:
            bad += 1
            ambiguous.add(r["case"])
            print(f"MISLABEL {GEN.name}:{line} {r['case']} {g['package']} {g['version']} kind {g['kind']}: "
                  f"row says {'affected' if claims_affected else 'not affected'}, OSV says "
                  f"{'affected' if is_affected else 'not affected'}")
    if a.record_ambiguous and ambiguous:
        old = set(AMBIGUOUS.read_text().split()) if AMBIGUOUS.exists() else set()
        AMBIGUOUS.write_text("".join(f"{i}\n" for i in sorted(old | ambiguous)))
        print(f"recorded {len(ambiguous)} ambiguous advisories in {AMBIGUOUS.relative_to(ROOT)}")
    print(f"generated labels vs OSV version query: {'FAIL' if bad else 'PASS'} ({n} rows, {bad} mislabels)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
