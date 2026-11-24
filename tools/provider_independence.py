#!/usr/bin/env python3
"""How many independent providers sit behind the miners listed for an intent?

    SSL_CERT_FILE=... python tools/provider_independence.py [--intent SECURITY_REVIEW_GENERAL] \
        [--snapshot eval/reports/raw/<date>-miners.json] [--offline]

Reads the node's public listing (/api/miners?intent=...), saves it as a dated snapshot, and groups
miners by the payout identity the listing itself publishes: `wallet_address` and `fee_address`.
Miners paid to the same address are counted as one provider. Also counts the miners each of our
paid runs actually used (bench/out/*/calls.ndjson), so "competing providers" can be read as
"competing operators". Public data only.

Caveat (stated in every report): one operator can use several addresses, so this is an upper
bound on independence; two addresses never prove two teams.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = "https://devnode.telegraphprotocol.com"


def fetch(intent: str) -> list[dict]:
    ctx = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        ctx.load_verify_locations(os.environ["SSL_CERT_FILE"])
    req = urllib.request.Request(f"{NODE}/api/miners?intent={urllib.parse.quote(intent)}",
                                 headers={"User-Agent": "adversarialeval-independence"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.loads(r.read())


def slim(m: dict) -> dict:
    keep = ("id", "slug", "name", "wallet_address", "fee_address", "base_url", "activation_status",
            "min_price_usdc", "registered_at", "total_requests_served")
    return {k: m.get(k) for k in keep}


def paid_miners() -> dict[str, set[str]]:
    """miner ids our runs got answers from, per run directory."""
    out: dict[str, set[str]] = {}
    for f in sorted((ROOT / "bench" / "out").glob("*/calls.ndjson")):
        ids = set()
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            mid = r.get("routed_miner") or r.get("miner_id") or r.get("miner_asked")
            if mid and str(mid) not in ("routed", "osv-baseline"):
                ids.add(str(mid))
        if ids:
            out[f.parent.name] = ids
    return out


def analyse(listing: list[dict]) -> dict:
    by_id = {str(m["id"]): m for m in listing}
    owner = {mid: (m.get("fee_address") or m.get("wallet_address") or f"none:{mid}").lower() for mid, m in by_id.items()}
    groups = collections.defaultdict(list)
    for mid, addr in owner.items():
        groups[addr].append(mid)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    wallets = {(m.get("wallet_address") or "").lower() for m in listing}
    runs = {}
    for run, ids in paid_miners().items():
        known = [i for i in ids if i in owner]
        runs[run] = {"miners_answering": len(ids), "in_listing": len(known),
                     "distinct_providers": len({owner[i] for i in known})}
    return {
        "miners_listed": len(listing),
        "distinct_fee_addresses": len(groups),
        "distinct_wallet_addresses": len(wallets),
        "largest_groups": [{"address": a, "miners": len(ids),
                            "slugs": sorted(by_id[i]["slug"] for i in ids)} for a, ids in ranked[:5]],
        "share_in_two_largest": round(sum(len(ids) for _, ids in ranked[:2]) / max(1, len(listing)), 3),
        "single_miner_providers": sum(1 for _, ids in ranked if len(ids) == 1),
        "our_runs": runs,
        "caveat": "addresses are an upper bound on independence: one operator can use several addresses",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", default="SECURITY_REVIEW_GENERAL")
    ap.add_argument("--snapshot", type=Path)
    ap.add_argument("--offline", action="store_true", help="read --snapshot instead of the node")
    a = ap.parse_args()
    if a.offline:
        snap = json.loads(a.snapshot.read_text())
        listing = snap["miners"]
    else:
        listing = [slim(m) for m in fetch(a.intent)]
        snap = {"read_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "source": f"{NODE}/api/miners?intent={a.intent}", "intent": a.intent, "miners": listing}
        if a.snapshot:
            a.snapshot.parent.mkdir(parents=True, exist_ok=True)
            a.snapshot.write_text(json.dumps(snap, indent=1) + "\n")
    out = {"intent": a.intent, "read_at": snap.get("read_at"), **analyse(listing)}
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
