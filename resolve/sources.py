"""Official-source resolvers for prediction markets (no model involved).

Each resolver reads one authoritative public source and returns (outcome, evidence) where outcome is
"yes", "no" or "unresolved". The raw response is kept as evidence so a resolution can be re-checked.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from datetime import date, datetime, timedelta, timezone

UA = {"User-Agent": "adversarialeval-resolve/1.0"}


def _ctx():
    c = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        c.load_verify_locations(os.environ["SSL_CERT_FILE"])
    return c


def get(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60, context=_ctx()) as r:
        return json.loads(r.read())


def _today() -> date:
    return datetime.now(timezone.utc).date()


# ---------- Coinbase Exchange daily candles (UTC days) ----------
def coinbase_days(product: str, start: str, end: str) -> tuple[list[dict], str]:
    """Daily candles for start..end inclusive (UTC). Coinbase rows: [time, low, high, open, close, volume]."""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end) + timedelta(days=1)
    url = (f"https://api.exchange.coinbase.com/products/{product}/candles?granularity=86400"
           f"&start={s}T00:00:00Z&end={e}T00:00:00Z")
    rows = sorted(get(url))
    days = [{"day": datetime.fromtimestamp(t, timezone.utc).date().isoformat(), "low": lo, "high": hi, "open": op, "close": cl}
            for t, lo, hi, op, cl, _v in rows]
    return [d for d in days if start <= d["day"] <= end], url


def crypto(spec: dict) -> tuple[str, dict]:
    """spec: product, start, end, field (close|high|low), op (above|below), threshold, any (bool: any day in range)."""
    if date.fromisoformat(spec["end"]) >= _today():
        return "unresolved", {"why": f"the period ends {spec['end']}, which has not finished (UTC)"}
    days, url = coinbase_days(spec["product"], spec["start"], spec["end"])
    expected = (date.fromisoformat(spec["end"]) - date.fromisoformat(spec["start"])).days + 1
    if len(days) != expected:
        return "unresolved", {"why": f"Coinbase returned {len(days)} of {expected} daily candles", "url": url}
    hit = [d for d in days if (d[spec["field"]] > spec["threshold"] if spec["op"] == "above" else d[spec["field"]] < spec["threshold"])]
    return ("yes" if hit else "no"), {"url": url, "days": days, "matching_days": [d["day"] for d in hit]}


# ---------- NHL official API ----------
def nhl(spec: dict) -> tuple[str, dict]:
    """spec: date (local game date as listed by the NHL), team (abbrev), opponent (abbrev),
    test: win | win_regulation | scored | margin>=N | total>X."""
    if date.fromisoformat(spec["date"]) >= _today():
        return "unresolved", {"why": "the game date has not passed"}
    url = f"https://api-web.nhle.com/v1/score/{spec['date']}"
    games = [g for g in get(url).get("games", []) if {g["awayTeam"]["abbrev"], g["homeTeam"]["abbrev"]} == {spec["team"], spec["opponent"]}]
    if len(games) != 1 or games[0].get("gameState") not in ("OFF", "FINAL"):
        return "unresolved", {"why": f"{len(games)} final games found between {spec['team']} and {spec['opponent']}", "url": url}
    g = games[0]
    me = g["awayTeam"] if g["awayTeam"]["abbrev"] == spec["team"] else g["homeTeam"]
    op = g["homeTeam"] if me is g["awayTeam"] else g["awayTeam"]
    last = (g.get("gameOutcome") or {}).get("lastPeriodType")
    t = spec["test"]
    if t == "win":
        ok = me["score"] > op["score"]
    elif t == "win_regulation":
        ok = me["score"] > op["score"] and last == "REG"
    elif t == "scored":
        ok = me["score"] >= 1
    elif t.startswith("margin>="):
        ok = me["score"] - op["score"] >= int(t.split(">=")[1])
    elif t.startswith("total>"):
        ok = me["score"] + op["score"] > float(t.split(">")[1])
    else:
        raise ValueError(t)
    return ("yes" if ok else "no"), {"url": url, "game_id": g["id"], "score": {me["abbrev"]: me["score"], op["abbrev"]: op["score"]},
                                     "last_period": last, "start_utc": g.get("startTimeUTC")}


# ---------- MLB Stats API (official) ----------
def mlb_world_series(spec: dict) -> tuple[str, dict]:
    """spec: season, test: champion=<team name> | games>=N | won_a_game=<team name>."""
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=W&season={spec['season']}"
    games = [g for d in get(url).get("dates", []) for g in d["games"] if g["status"]["detailedState"] == "Final"]
    wins: dict[str, int] = {}
    for g in games:
        w = g["teams"]["home"] if g["teams"]["home"].get("isWinner") else g["teams"]["away"]
        wins[w["team"]["name"]] = wins.get(w["team"]["name"], 0) + 1
    champion = next((t for t, n in wins.items() if n >= 4), None)
    if champion is None:
        return "unresolved", {"why": "no team has 4 World Series wins yet", "url": url}
    t = spec["test"]
    if t.startswith("champion="):
        ok = champion == t.split("=", 1)[1]
    elif t.startswith("games>="):
        ok = len(games) >= int(t.split(">=")[1])
    elif t.startswith("won_a_game="):
        ok = wins.get(t.split("=", 1)[1], 0) >= 1
    else:
        raise ValueError(t)
    return ("yes" if ok else "no"), {"url": url, "games": len(games), "wins": wins, "champion": champion}


# ---------- USGS earthquake catalog ----------
def usgs(spec: dict) -> tuple[str, dict]:
    """spec: start, end (UTC dates, inclusive), magnitude, strict (true: greater than; false: at least)."""
    if date.fromisoformat(spec["end"]) >= _today():
        return "unresolved", {"why": "the period has not finished"}
    end_excl = (date.fromisoformat(spec["end"]) + timedelta(days=1)).isoformat()
    url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={spec['start']}"
           f"&endtime={end_excl}&minmagnitude={spec['magnitude'] - 0.5}&orderby=time-asc")
    qs = [{"id": f["id"], "mag": f["properties"]["mag"], "place": f["properties"]["place"],
           "time": datetime.fromtimestamp(f["properties"]["time"] / 1000, timezone.utc).isoformat()}
          for f in get(url)["features"]]
    hit = [q for q in qs if (q["mag"] > spec["magnitude"] if spec["strict"] else q["mag"] >= spec["magnitude"])]
    return ("yes" if hit else "no"), {"url": url, "matching": hit, "largest": max((q["mag"] for q in qs), default=None)}


RESOLVERS = {"coinbase": crypto, "nhl": nhl, "mlb_ws": mlb_world_series, "usgs": usgs}


def resolve(source: dict | None) -> tuple[str, dict]:
    """A market's machine-readable resolution source, or None when the market has none."""
    if not source:
        return "unresolved", {"why": "the market names no machine-readable resolution source"}
    return RESOLVERS[source["kind"]](source)
