#!/usr/bin/env python3
"""Real Polymarket markets: frozen selection, truth = Polymarket's final resolution, Binance resolver.

    python resolve/polymarket.py select     # writes resolve/polymarket_cases.json (run once, before any paid call)

Selection rule (resolve/RULE-polymarket.md): Gamma API, closed markets ending 2026-11-01..2026-11-28 UTC,
first 2,100 by volume (the API's paging limit), Yes/No outcomes, UMA status "resolved", final prices
exactly 1/0; at most one market per event (the highest-volume one); categories by fixed patterns below;
the top 6 by volume in each of crypto, sports, politics, world.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sources import get  # noqa: E402

ET = ZoneInfo("America/New_York")
GAMMA = ("https://gamma-api.polymarket.com/markets?closed=true&limit=100&offset={off}&order=volumeNum&ascending=false"
         "&end_date_min=2026-11-01T00:00:00Z&end_date_max=2026-11-28T00:00:00Z")
CATS = [("crypto", r"\b(bitcoin|ethereum|solana|xrp)\b"),
        ("politics", r"\b(election|senate|house|governor|midterm|party|mayor|referendum|ballot|congress)\b"),
        ("sports", r"( win on 20\d\d-| vs\.? |\bNFL\b|\bNBA\b|\bNHL\b|\bMLB\b|\bUFC\b|Exact Score|O/U|Spread|Map \d|BO\d|\bLoL\b|Counter-Strike|Dota)")]
PER_CATEGORY = 6


def category(q: str) -> str:
    return next((c for c, pat in CATS if re.search(pat, q, re.I)), "world")


# ---------- Binance 1-minute candles (the source Polymarket's crypto rules name) ----------
def binance_minutes(symbol: str, start: datetime, end: datetime) -> list[list]:
    """1m klines [open_time, open, high, low, close, ...] with open_time in [start, end], from Binance's public data mirror."""
    out, t = [], int(start.timestamp() * 1000)
    stop = int(end.timestamp() * 1000)
    while t <= stop:
        rows = get(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=1m&startTime={t}&endTime={stop}&limit=1000")
        if not rows:
            break
        out += rows
        t = rows[-1][0] + 60_000
    return out


def binance(spec: dict) -> tuple[str, dict]:
    """spec: symbol, start_et, end_et (ISO local ET times, inclusive minutes), test: high>=X | low<=X | close_at_between=A,B."""
    start = datetime.fromisoformat(spec["start_et"]).replace(tzinfo=ET)
    end = datetime.fromisoformat(spec["end_et"]).replace(tzinfo=ET)
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={spec['symbol']}&interval=1m"
    if end >= datetime.now(timezone.utc):
        return "unresolved", {"why": "window has not finished"}
    t = spec["test"]
    if t.startswith("close_at_between="):
        a, b = map(float, t.split("=")[1].split(","))
        minute = end  # the 1m candle that closes at `end_et` opened one minute earlier
        rows = binance_minutes(spec["symbol"], minute - timedelta(minutes=1), minute - timedelta(minutes=1))
        if not rows:
            return "unresolved", {"why": "no candle", "url": url}
        close = float(rows[0][4])
        return ("yes" if a <= close < b else "no"), {"url": url, "close": close, "candle_open_utc": datetime.fromtimestamp(rows[0][0] / 1000, timezone.utc).isoformat()}
    rows = binance_minutes(spec["symbol"], start, end)
    expected = int((end - start).total_seconds() // 60) + 1
    if len(rows) < expected * 0.99:
        return "unresolved", {"why": f"only {len(rows)} of {expected} minutes returned", "url": url}
    if t.startswith("high>="):
        x = float(t.split(">=")[1]); best = max(float(r[2]) for r in rows); ok = best >= x
    elif t.startswith("low<="):
        x = float(t.split("<=")[1]); best = min(float(r[3]) for r in rows); ok = best <= x
    else:
        raise ValueError(t)
    return ("yes" if ok else "no"), {"url": url, "minutes": len(rows), "extreme": best}


# Machine-readable contracts transcribed by hand from each crypto market's published rules, before any paid call.
CONTRACTS = {
    "7203506": {"kind": "binance", "symbol": "BTCUSDT", "start_et": "2026-11-27T12:00", "end_et": "2026-11-27T12:00", "test": "close_at_between=60000,62000"},
    "5170735": {"kind": "binance", "symbol": "BTCUSDT", "start_et": "2026-10-01T00:00", "end_et": "2026-10-31T23:59", "test": "high>=87500"},
    "5170791": {"kind": "binance", "symbol": "ETHUSDT", "start_et": "2026-10-01T00:00", "end_et": "2026-10-31T23:59", "test": "low<=2100"},
    "6891215": {"kind": "binance", "symbol": "BTCUSDT", "start_et": "2026-11-09T00:00", "end_et": "2026-11-15T23:59", "test": "low<=62000"},
    "5170814": {"kind": "binance", "symbol": "XRPUSDT", "start_et": "2026-10-01T00:00", "end_et": "2026-10-31T23:59", "test": "high>=4.00"},
    "6563869": {"kind": "binance", "symbol": "BTCUSDT", "start_et": "2026-11-02T00:00", "end_et": "2026-11-08T23:59", "test": "low<=72000"},
}


def select() -> None:
    allm = []
    for off in range(0, 3000, 100):
        try:
            page = get(GAMMA.format(off=off))
        except urllib.error.HTTPError:
            break  # the API stops paging at offset 2,100
        allm += page
        if len(page) < 100:
            break
    ok = [m for m in allm if m.get("umaResolutionStatus") == "resolved" and json.loads(m.get("outcomes") or "[]") == ["Yes", "No"]
          and json.loads(m.get("outcomePrices") or "[]") in (["1", "0"], ["0", "1"])]
    seen, pick = set(), {c: [] for c in ("crypto", "sports", "politics", "world")}
    for m in ok:  # sorted by volume, highest first
        ev = ((m.get("events") or [{}])[0]).get("id")
        if ev in seen:
            continue
        c = category(m["question"])
        if len(pick[c]) < PER_CATEGORY:
            pick[c].append(m)
            seen.add(ev)
    markets = []
    for c, ms in pick.items():
        for m in ms:
            truth = "yes" if json.loads(m["outcomePrices"])[0] == "1" else "no"
            markets.append({"id": f"pm-{m['id']}", "polymarket_id": m["id"], "slug": m.get("slug"), "category": c,
                            "event": f"{m['question']} (Polymarket market; resolves per its published rules)",
                            "question": m["question"], "rules": m.get("description"), "resolution_source": m.get("resolutionSource"),
                            "end_date": m.get("endDate"), "volume_usd": round(float(m.get("volumeNum") or 0)),
                            "contract": CONTRACTS.get(m["id"]), "truth": truth,
                            "truth_evidence": {"source": "Polymarket final resolution (UMA)", "outcomePrices": m["outcomePrices"],
                                               "umaResolutionStatus": m["umaResolutionStatus"], "closedTime": m.get("closedTime"),
                                               "url": f"https://polymarket.com/market/{m.get('slug')}"}})
    body = {"made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "listed": len(allm), "eligible": len(ok), "markets": markets}
    (HERE / "polymarket_cases.json").write_text(json.dumps(body, indent=1) + "\n")
    for m in markets:
        print(f"{m['category']:9} {m['truth']:4} {'contract' if m['contract'] else '        '} {m['question'][:80]}")
    print(len(markets), "markets;", len(ok), "eligible of", len(allm))


if __name__ == "__main__":
    select()
