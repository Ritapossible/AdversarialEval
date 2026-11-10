#!/usr/bin/env python3
"""Build data/sources/sources.jsonl from real advisories, verified against OSV.

Every fact a `chosen` answer states about a package advisory (id, aliases, affected
ranges, first patched version, CWE, severity) must come from this file, and this file
comes from https://api.osv.dev. Raw OSV records are cached in data/sources/osv/ so the
dataset can be re-verified offline and diffed when an advisory changes.

    python tools/fetch_sources.py                 # fetch every id in data/sources/ids.txt
    python tools/fetch_sources.py --offline       # rebuild from the cache only

ids.txt: one advisory id per line (GHSA-… preferred), `#` comments allowed, plus an
optional ` split=<public|validation|private>` and ` case=<case_id>` after the id.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "sources"
OSV = "https://api.osv.dev/v1/vulns/"


def fetch(vid: str, offline: bool) -> dict:
    cache = SRC / "osv" / f"{vid}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    raw = SRC / "osv_raw" / f"{vid}.json"
    if raw.exists():  # cached by the generator's package queries (git-ignored)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(raw.read_text())
        return json.loads(raw.read_text())
    if offline:
        raise SystemExit(f"{vid}: not cached and --offline given")
    with urllib.request.urlopen(OSV + vid, timeout=30) as r:
        rec = json.load(r)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    return rec


def ranges(affected: dict) -> list[dict]:
    out = []
    for rg in affected.get("ranges", []):
        if rg.get("type") not in ("ECOSYSTEM", "SEMVER"):
            continue
        cur: dict = {}
        for ev in rg.get("events", []):
            if "introduced" in ev:
                cur = {"introduced": ev["introduced"]}
            elif "fixed" in ev:
                cur["fixed"] = ev["fixed"]
                out.append(cur)
                cur = {}
            elif "last_affected" in ev:
                cur["last_affected"] = ev["last_affected"]
                out.append(cur)
                cur = {}
        if cur:
            out.append(cur)  # open-ended: no fix
    return out


def summarise(rec: dict, split: str, case: str | None) -> dict:
    db = rec.get("database_specific") or {}
    pkgs = []
    for a in rec.get("affected", []):
        p = a.get("package", {})
        pkgs.append({"ecosystem": p.get("ecosystem"), "name": p.get("name"), "ranges": ranges(a)})
    cves = [x for x in rec.get("aliases", []) if x.startswith("CVE-")]
    return {
        "case_id": case or rec["id"],
        "id": rec["id"],
        "cves": cves,
        "summary": rec.get("summary", ""),
        "packages": pkgs,
        "cwe": db.get("cwe_ids", []),
        "severity": db.get("severity"),
        "withdrawn": rec.get("withdrawn"),
        "url": f"https://github.com/advisories/{rec['id']}" if rec["id"].startswith("GHSA-")
               else f"https://osv.dev/vulnerability/{rec['id']}",
        "split": split,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="+", default=[str(SRC / "ids.txt"), str(SRC / "ids_generated.txt")],
                    help="id files (hand-picked ids.txt, then generator output); missing files are skipped")
    ap.add_argument("--out", default=str(SRC / "sources.jsonl"))
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)

    rows, seen = [], set()
    lines = []
    for idf in a.ids:
        if Path(idf).exists():
            lines += Path(idf).read_text().splitlines()
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        vid, opts = parts[0], dict(p.split("=", 1) for p in parts[1:])
        if vid in seen:
            raise SystemExit(f"duplicate id {vid}")
        seen.add(vid)
        rec = fetch(vid, a.offline)
        s = summarise(rec, opts.get("split", "public"), opts.get("case"))
        if s["withdrawn"]:
            print(f"! {vid} is WITHDRAWN ({s['withdrawn']}) — usable only as an F1 trap", file=sys.stderr)
        rows.append(s)
    Path(a.out).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"wrote {len(rows)} sources -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
