#!/usr/bin/env python3
"""Watch mode: re-check every PASS and BLOCK decision for free, and alert when public data changed.

    python mind/watch.py mind/evidence/2026-11-22-watchlist.json mind/evidence/2026-11-2*T*.json \
        [--out mind/evidence/watch/<date>.json] [--fail-on-alert]

Inputs: the Dependency.Guard Mind's watchlist (`entries` with `purl`, `decision`, `storedAnswer`)
and connector run files (`packages` with `decision` and `attempts`). FLAG and NOT CHECKED entries
are open questions, not decisions, so they are never watched. Only free public sources are used
(Verified Ask: OSV, deps.dev, npm, PyPI, rubygems.org); nothing is bought.

For each watched version, the stored answer is checked again against today's data:
  ALERT    a PASS whose answer is no longer verified (a new advisory, or the version was pulled):
           someone should look before the next release
  WIDENED  a BLOCK that OSV now lists more distinct advisories for (still blocked; the list grew)
  REVIEW   a BLOCK that OSV no longer lists any advisory for (withdrawn or re-scoped): a person decides
  OK       nothing changed
  UNKNOWN  a source was unavailable; try again later
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify.core import _distinct, parse_target, verify  # noqa: E402
from verify.sources import LiveSources  # noqa: E402


def watched(paths: list[Path]) -> dict[str, dict]:
    """purl -> {decision, answer, advisories, source}; the newest file wins for a purl."""
    out: dict[str, dict] = {}
    for p in sorted(paths, key=lambda x: x.name):
        d = json.loads(p.read_text())
        for e in d.get("entries", []):  # the Mind's watchlist
            if e.get("decision") in ("PASS", "BLOCK"):
                ans = e.get("storedAnswer") or {"verdict": e.get("verdict"), "vulnerability_count": e.get("vulnerabilityCount")}
                out[e["purl"]] = {"decision": e["decision"], "answer": ans, "source": p.name,
                                  "known": sorted({*(e.get("advisoryIds") or []), *(e.get("advisories") or [])})}
        for pkg in d.get("packages", []):  # connector runs
            if pkg.get("decision") in ("PASS", "BLOCK") and pkg.get("attempts"):
                last = pkg["attempts"][-1]
                ids = [c["detail"].split()[0] for c in last.get("checks", []) if c.get("name") == "citation"]
                out[pkg["target"]] = {"decision": pkg["decision"], "answer": last.get("result"), "source": p.name, "known": ids}
    return out


def recheck(items: dict[str, dict], src) -> list[dict]:
    rows = []
    for purl, w in sorted(items.items()):
        v = verify(purl, w["answer"], src)
        unavailable = any(c.status == "skip" and "unavailable" in c.detail for c in v.checks)
        if unavailable:
            status = "UNKNOWN"
        elif w["decision"] == "PASS":
            status = "OK" if v.label == "verified" else "ALERT"
        else:  # BLOCK stays blocked; report whether the advisory list grew or vanished
            pkg = parse_target(purl)
            vulns = src.osv_query(pkg) if pkg else None
            before = (w["answer"] or {}).get("vulnerability_count") or 0
            if vulns is None:
                status = "UNKNOWN"
            elif not vulns:
                status = "REVIEW"  # nothing listed any more: an advisory was withdrawn or re-scoped
            else:
                status = "WIDENED" if _distinct(vulns) > before else "OK"
        rows.append({"purl": purl, "decision": w["decision"], "status": status, "label_now": v.label,
                     "osv_ids_now": sorted(v.osv_ids), "from": w["source"],
                     "why": [f"{c.status}: {c.detail}" for c in v.checks if c.status in ("fail", "warn", "skip")]})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--fail-on-alert", action="store_true")
    a = ap.parse_args()
    items = watched(a.inputs)
    rows = recheck(items, LiveSources(max_age=600, max_entries=10_000))
    counts = {s: sum(r["status"] == s for r in rows) for s in ("ALERT", "REVIEW", "WIDENED", "OK", "UNKNOWN")}
    report = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "watched": len(rows),
              "counts": counts, "cost_usd": 0, "rows": rows}
    for r in rows:
        print(f"{r['status']:8} {r['decision']:5} {r['purl']}  ({r['label_now']}{'; ' + r['why'][0] if r['why'] else ''})")
    print(json.dumps(counts))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(report, indent=1) + "\n")
    return 1 if a.fail_on_alert and (counts["ALERT"] or counts["REVIEW"]) else 0


if __name__ == "__main__":
    sys.exit(main())
