#!/usr/bin/env python3
"""Build the frozen prediction-market test: 24 markets, truth from official sources, evidence saved.

    python resolve/make_cases.py      # writes resolve/cases.json (run once, before any paid call)

Each market has:
- event: the question as a market would state it (what the miners are asked)
- contract: the machine-readable resolution source a market contract carries, or null
- truth: computed by resolve/sources.py from the official source (for no-contract markets too), never by a model
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sources import resolve  # noqa: E402

CB = "according to the Coinbase {p} daily candle (UTC)"


def coin(i, text, product, start, end, field, op, thr, kind):
    return {"id": i, "kind": kind, "event": text,
            "contract": {"kind": "coinbase", "product": product, "start": start, "end": end, "field": field, "op": op, "threshold": thr}}


MARKETS = [
    coin("btc-close-above-80k-nov04", f"Did Bitcoin close above $80,000 on November 4, 2026, {CB.format(p='BTC-USD')}?", "BTC-USD", "2026-11-04", "2026-11-04", "close", "above", 80000, "close vs trade"),
    coin("btc-close-above-81k-nov04", f"Did Bitcoin close above $81,000 on November 4, 2026, {CB.format(p='BTC-USD')}?", "BTC-USD", "2026-11-04", "2026-11-04", "close", "above", 81000, "close vs trade: traded above, closed below"),
    coin("btc-trade-above-81k-nov04", f"Did Bitcoin trade above $81,000 at any time on November 4, 2026, {CB.format(p='BTC-USD')}?", "BTC-USD", "2026-11-04", "2026-11-04", "high", "above", 81000, "close vs trade"),
    coin("btc-close-below-60k-nov21", f"Did Bitcoin close below $60,000 on November 21, 2026, {CB.format(p='BTC-USD')}?", "BTC-USD", "2026-11-21", "2026-11-21", "close", "below", 60000, "close vs trade: traded far below, closed $86 above"),
    coin("btc-trade-below-56k-nov21", f"Did Bitcoin trade below $56,000 at any time on November 21, 2026, {CB.format(p='BTC-USD')}?", "BTC-USD", "2026-11-21", "2026-11-21", "low", "below", 56000, "close vs trade"),
    coin("btc-trade-below-55k-nov", f"Did Bitcoin trade below $55,000 at any time between November 1 and November 27, 2026, according to Coinbase BTC-USD daily candles (UTC)?", "BTC-USD", "2026-11-01", "2026-11-27", "low", "below", 55000, "near miss: low was $55,106"),
    coin("eth-close-above-1800-nov23", f"Did Ether close above $1,800 on November 23, 2026, {CB.format(p='ETH-USD')}?", "ETH-USD", "2026-11-23", "2026-11-23", "close", "above", 1800, "close vs trade: traded above, closed below"),
    coin("sol-close-above-75-nov17", f"Did Solana (SOL) close above $75 on November 17, 2026, {CB.format(p='SOL-USD')}?", "SOL-USD", "2026-11-17", "2026-11-17", "close", "above", 75, "near miss: closed at $75.11"),
    coin("eth-close-below-1700-nov27", f"Did Ether close below $1,700 on November 27, 2026, {CB.format(p='ETH-USD')}?", "ETH-USD", "2026-11-27", "2026-11-27", "close", "below", 1700, "plain"),
    {"id": "nhl-stl-beat-edm-nov22", "kind": "shootout win counts as a win",
     "event": "Did the St. Louis Blues beat the Edmonton Oilers in their NHL game on November 22, 2026?",
     "contract": {"kind": "nhl", "date": "2026-11-22", "team": "STL", "opponent": "EDM", "test": "win"}},
    {"id": "nhl-stl-beat-edm-reg-nov22", "kind": "regulation only: the win came in a shootout",
     "event": "Did the St. Louis Blues beat the Edmonton Oilers in regulation time in their NHL game on November 22, 2026?",
     "contract": {"kind": "nhl", "date": "2026-11-22", "team": "STL", "opponent": "EDM", "test": "win_regulation"}},
    {"id": "nhl-pit-scored-nov22", "kind": "shutout",
     "event": "Did the Pittsburgh Penguins score at least one goal against the Dallas Stars in their NHL game on November 22, 2026?",
     "contract": {"kind": "nhl", "date": "2026-11-22", "team": "PIT", "opponent": "DAL", "test": "scored"}},
    {"id": "nhl-mtl-beat-car-nov19", "kind": "overtime win counts as a win",
     "event": "Did the Montreal Canadiens beat the Carolina Hurricanes in their NHL game on November 19, 2026?",
     "contract": {"kind": "nhl", "date": "2026-11-19", "team": "MTL", "opponent": "CAR", "test": "win"}},
    {"id": "nhl-bos-margin3-nov18", "kind": "margin",
     "event": "Did the Boston Bruins beat the Detroit Red Wings by 3 or more goals in their NHL game on November 18, 2026?",
     "contract": {"kind": "nhl", "date": "2026-11-18", "team": "BOS", "opponent": "DET", "test": "margin>=3"}},
    {"id": "nhl-buf-tbl-over65-nov22", "kind": "total",
     "event": "Were more than 6.5 total goals scored in the NHL game between the Buffalo Sabres and the Tampa Bay Lightning on November 22, 2026?",
     "contract": {"kind": "nhl", "date": "2026-11-22", "team": "BUF", "opponent": "TBL", "test": "total>6.5"}},
    {"id": "mlb-ws-2026-brewers", "kind": "no machine-readable source in the contract",
     "event": "Did the Milwaukee Brewers win the 2026 World Series?", "contract": None,
     "truth_source": {"kind": "mlb_ws", "season": 2026, "test": "champion=Milwaukee Brewers"}},
    {"id": "mlb-ws-2026-six-games", "kind": "no machine-readable source in the contract",
     "event": "Did the 2026 World Series last at least six games?", "contract": None,
     "truth_source": {"kind": "mlb_ws", "season": 2026, "test": "games>=6"}},
    {"id": "mlb-ws-2026-rays-won-a-game", "kind": "no machine-readable source in the contract",
     "event": "Did the Tampa Bay Rays win at least one game in the 2026 World Series?", "contract": None,
     "truth_source": {"kind": "mlb_ws", "season": 2026, "test": "won_a_game=Tampa Bay Rays"}},
    {"id": "usgs-m7-oct15-31", "kind": "threshold edge: exactly 7.0 counts",
     "event": "Was there an earthquake of magnitude 7.0 or greater anywhere in the world between October 15 and October 31, 2026 (UTC), according to the USGS?",
     "contract": {"kind": "usgs", "start": "2026-10-15", "end": "2026-10-31", "magnitude": 7.0, "strict": False}},
    {"id": "usgs-over7-oct15-31", "kind": "threshold edge: exactly 7.0 does not count",
     "event": "Was there an earthquake of magnitude greater than 7.0 anywhere in the world between October 15 and October 31, 2026 (UTC), according to the USGS?",
     "contract": {"kind": "usgs", "start": "2026-10-15", "end": "2026-10-31", "magnitude": 7.0, "strict": True}},
    {"id": "usgs-m7-nov1-27", "kind": "none happened",
     "event": "Was there an earthquake of magnitude 7.0 or greater anywhere in the world between November 1 and November 27, 2026 (UTC), according to the USGS?",
     "contract": {"kind": "usgs", "start": "2026-11-01", "end": "2026-11-27", "magnitude": 7.0, "strict": False}},
    coin("btc-close-above-70k-dec31", f"Will Bitcoin close above $70,000 on December 31, 2026, {CB.format(p='BTC-USD')}?", "BTC-USD", "2026-12-31", "2026-12-31", "close", "above", 70000, "not yet resolvable: future date"),
    {"id": "mlb-ws-2027-seven-games", "kind": "not yet resolvable: future event",
     "event": "Will the 2027 World Series go to seven games?", "contract": None,
     "truth_source": {"kind": "mlb_ws", "season": 2027, "test": "games>=7"}},
    {"id": "btc-crash-nov", "kind": "not resolvable: no defined criterion",
     "event": "Did Bitcoin crash in November 2026?", "contract": None, "truth_source": None},
]


def main() -> None:
    out = []
    for m in MARKETS:
        src = m.get("truth_source", m["contract"]) if "truth_source" in m else m["contract"]
        truth, ev = resolve(src)
        out.append({**m, "truth": truth, "truth_evidence": ev})
        print(f"{m['id']:32} {truth:10} {m['kind']}")
    body = {"made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "markets": out}
    (HERE / "cases.json").write_text(json.dumps(body, indent=1) + "\n")
    print(len(out), "markets")


if __name__ == "__main__":
    main()
