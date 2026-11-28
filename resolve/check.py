#!/usr/bin/env python3
"""Free resolution check for one market, as JSON (used by mind/connector/markets.mjs).

    python resolve/check.py --cases resolve/polymarket_cases.json --id pm-6891215

Prints {"id", "contract", "source_outcome", "evidence"}: the outcome read from the source the market's
contract names (Binance, Coinbase, NHL, MLB, USGS), or "unresolved" when the contract names none.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from polymarket import binance  # noqa: E402
from sources import RESOLVERS, resolve  # noqa: E402

RESOLVERS["binance"] = binance

ap = argparse.ArgumentParser()
ap.add_argument("--cases", type=Path, required=True)
ap.add_argument("--id", required=True)
a = ap.parse_args()
m = next(x for x in json.loads(a.cases.read_text())["markets"] if x["id"] == a.id)
out, ev = resolve(m["contract"])
ev = {k: v for k, v in ev.items() if k not in ("days",)}  # keep the evidence short
print(json.dumps({"id": m["id"], "contract": m["contract"], "source_outcome": out, "evidence": ev}))
