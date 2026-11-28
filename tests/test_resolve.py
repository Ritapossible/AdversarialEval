#!/usr/bin/env python3
"""Offline tests for resolve/ (no network, no payments).

    python tests/test_resolve.py
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resolve"))
from run import cites, outcome, wilson  # noqa: E402
from sources import RESOLVERS, resolve  # noqa: E402
from polymarket import binance  # noqa: E402

RESOLVERS["binance"] = binance


class Frozen(unittest.TestCase):
    def test_cases_unchanged_since_preregistration(self):
        self.assertEqual(hashlib.sha256((ROOT / "resolve/cases.json").read_bytes()).hexdigest(),
                         "08b415b313202218e64d5e041f9b66c0b08ee09c397b809b9cd42b1895ffb3ac")

    def test_truth_mix_and_evidence(self):
        ms = json.loads((ROOT / "resolve/cases.json").read_text())["markets"]
        self.assertEqual(len(ms), 24)
        self.assertEqual([sum(m["truth"] == k for m in ms) for k in ("yes", "no", "unresolved")], [12, 9, 3])
        for m in ms:
            if m["truth"] != "unresolved":
                self.assertIn("url", m["truth_evidence"], m["id"])  # every settled truth names its source


class FrozenPolymarket(unittest.TestCase):
    def test_polymarket_cases_unchanged_since_preregistration(self):
        self.assertEqual(hashlib.sha256((ROOT / "resolve/polymarket_cases.json").read_bytes()).hexdigest(),
                         "e2e5ed3bb2209be661ac450aed3f9f832ff6a3ec5fd6f4e481dd22af9dcc1602")

    def test_selection_shape(self):
        ms = json.loads((ROOT / "resolve/polymarket_cases.json").read_text())["markets"]
        self.assertEqual(len(ms), 24)
        self.assertEqual(sorted({m["category"] for m in ms}), ["crypto", "politics", "sports", "world"])
        self.assertEqual(sum(m["truth"] == "yes" for m in ms), 9)
        self.assertTrue(all(bool(m["contract"]) == (m["category"] == "crypto") for m in ms))


class Parsing(unittest.TestCase):
    def test_outcome(self):
        self.assertEqual(outcome({"result": {"outcome": "YES"}}), "yes")
        self.assertEqual(outcome({"result": {"outcome": None, "resolved_yes": False}}), "no")
        self.assertEqual(outcome({"result": None, "error": "fetch failed"}), "unresolved")
        self.assertEqual(outcome(None), "unresolved")

    def test_cites(self):
        self.assertTrue(cites({"result": {"sources": ["https://www.espn.com/x"]}}))
        self.assertFalse(cites({"result": {"sources": None}}))
        self.assertFalse(cites({"result": {"sources": ["ESPN"]}}))

    def test_no_contract_is_unresolved(self):
        self.assertEqual(resolve(None)[0], "unresolved")

    def test_wilson(self):
        self.assertEqual(wilson(0, 0), [0.0, 0.0])


class Resolvers(unittest.TestCase):
    """Resolver logic on saved-shape responses (no network): the edge cases that decided real markets."""

    def setUp(self):
        import polymarket
        import sources
        self.sources, self.polymarket = sources, polymarket
        self._get_s, self._get_p = sources.get, polymarket.get

    def tearDown(self):
        self.sources.get, self.polymarket.get = self._get_s, self._get_p

    def test_coinbase_close_vs_trade(self):
        from datetime import datetime, timezone
        t = int(datetime(2026, 11, 4, tzinfo=timezone.utc).timestamp())
        self.sources.get = lambda url: [[t, 75600.64, 81130.79, 77336.0, 80428.31, 1.0]]
        spec = {"kind": "coinbase", "product": "BTC-USD", "start": "2026-11-04", "end": "2026-11-04", "threshold": 81000}
        self.assertEqual(resolve({**spec, "field": "close", "op": "above"})[0], "no")   # closed below
        self.assertEqual(resolve({**spec, "field": "high", "op": "above"})[0], "yes")   # traded above
        self.sources.get = lambda url: []                                             # a missing day
        self.assertEqual(resolve({**spec, "field": "close", "op": "above"})[0], "unresolved")

    def test_future_period_is_unresolved(self):
        spec = {"kind": "coinbase", "product": "BTC-USD", "start": "2099-12-31", "end": "2099-12-31", "field": "close", "op": "above", "threshold": 1}
        self.assertEqual(resolve(spec)[0], "unresolved")

    def test_nhl_shootout_is_not_a_regulation_win(self):
        game = {"games": [{"id": 1, "gameState": "OFF", "awayTeam": {"abbrev": "EDM", "score": 4}, "homeTeam": {"abbrev": "STL", "score": 5},
                           "gameOutcome": {"lastPeriodType": "SO"}, "startTimeUTC": "2026-11-23T00:00:00Z"}]}
        self.sources.get = lambda url: game
        spec = {"kind": "nhl", "date": "2026-11-22", "team": "STL", "opponent": "EDM"}
        self.assertEqual(resolve({**spec, "test": "win"})[0], "yes")
        self.assertEqual(resolve({**spec, "test": "win_regulation"})[0], "no")
        self.assertEqual(resolve({**spec, "test": "total>8.5"})[0], "yes")
        self.assertEqual(resolve({**spec, "test": "margin>=2"})[0], "no")

    def test_usgs_exactly_seven(self):
        q = {"features": [{"id": "us1", "properties": {"mag": 7.0, "place": "x", "time": 1792680820289}}]}
        self.sources.get = lambda url: q
        spec = {"kind": "usgs", "start": "2026-10-15", "end": "2026-10-31", "magnitude": 7.0}
        self.assertEqual(resolve({**spec, "strict": False})[0], "yes")   # 7.0 or greater
        self.assertEqual(resolve({**spec, "strict": True})[0], "no")     # greater than 7.0

    def test_mlb_world_series(self):
        def g(home_wins):
            return {"status": {"detailedState": "Final"}, "teams": {"home": {"team": {"name": "Brewers"}, "isWinner": home_wins},
                                                                     "away": {"team": {"name": "Rays"}, "isWinner": not home_wins}}}
        self.sources.get = lambda url: {"dates": [{"games": [g(True), g(True), g(True), g(False), g(True)]}]}
        spec = {"kind": "mlb_ws", "season": 2026}
        self.assertEqual(resolve({**spec, "test": "champion=Brewers"})[0], "yes")
        self.assertEqual(resolve({**spec, "test": "games>=6"})[0], "no")
        self.assertEqual(resolve({**spec, "test": "won_a_game=Rays"})[0], "yes")

    def _binance(self, lows=None, close_at=None):
        """Fake Binance 1m klines for the requested window; low and close set per minute timestamp."""
        import re as _re
        def get(url):
            st = int(_re.search(r"startTime=(\d+)", url).group(1)); en = int(_re.search(r"endTime=(\d+)", url).group(1))
            rows, t = [], st
            while t <= en and len(rows) < 1000:
                low = (lows or {}).get(t, 70000.0)
                close = (close_at or {}).get(t, 61000.0)
                rows.append([t, "0", "75000", str(low), str(close)])
                t += 60_000
            return rows
        self.polymarket.get = get

    def test_binance_low_window_in_new_york_time(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
        inside = int(datetime(2026, 11, 15, 23, 59, tzinfo=et).timestamp() * 1000)   # last minute of the window
        outside = int(datetime(2026, 11, 16, 0, 0, tzinfo=et).timestamp() * 1000)    # one minute after it
        spec = {"kind": "binance", "symbol": "BTCUSDT", "start_et": "2026-11-15T23:50", "end_et": "2026-11-15T23:59", "test": "low<=62000"}
        self._binance(lows={outside: 61000.0})
        self.assertEqual(resolve(spec)[0], "no")      # a dip just after the ET window doesn't count
        self._binance(lows={inside: 62000.0})
        self.assertEqual(resolve(spec)[0], "yes")     # exactly on the line counts ("equal to or lower")
        self._binance(lows={inside: 62006.0})
        self.assertEqual(resolve(spec)[0], "no")      # the real $6 near miss

    def test_binance_noon_close_bracket(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        noon_candle = int(datetime(2026, 11, 27, 11, 59, tzinfo=ZoneInfo("America/New_York")).timestamp() * 1000)
        spec = {"kind": "binance", "symbol": "BTCUSDT", "start_et": "2026-11-27T12:00", "end_et": "2026-11-27T12:00", "test": "close_at_between=60000,62000"}
        for close, want in ((59958.0, "no"), (60000.0, "yes"), (61999.99, "yes"), (62000.0, "no")):  # 62,000 belongs to the next bracket
            self._binance(close_at={noon_candle: close})
            self.assertEqual(resolve(spec)[0], want, close)


if __name__ == "__main__":
    unittest.main(verbosity=1)
