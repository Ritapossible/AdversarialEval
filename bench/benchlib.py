"""Grading and statistics for benchmark rule v2 (bench/RULE-v2.md). Pure functions, no I/O."""
from __future__ import annotations

import math
import random
from typing import Iterable, Sequence

VERDICTS = {"Secure", "Needs changes", "Insecure"}
ABSTAIN_WORDS = ("not found", "no such", "does not exist", "doesn't exist", "unknown package", "unknown version",
                 "could not find", "cannot find", "can't find", "no package", "not exist", "unable to find",
                 "no record", "no release", "not a valid", "invalid version", "not published")


def answer(rec: dict) -> dict | None:
    """The delivered result, or None when nothing usable was delivered."""
    return rec.get("result") if rec.get("http") == 200 and isinstance(rec.get("result"), dict) else None


def charged(rec: dict) -> bool:
    """True when the call cost the buyer: a delivery receipt, or a successful settlement without one."""
    if isinstance(rec.get("receipt"), dict) or isinstance(rec.get("escrow_receipt"), dict):
        return True
    pr = rec.get("payment_response")
    return isinstance(pr, dict) and bool(pr.get("success"))


def charged_onchain(rec: dict) -> bool:
    """Reconciled with the payer's on-chain USDC transfers (rule v2, amendment 1): every call was
    paid except those the node refused before payment (HTTP 503, could not route)."""
    if rec.get("rail") == "escrow":  # escrow bills delivered answers only (amendment 4): its receipt is the charge
        return isinstance(rec.get("escrow_receipt"), dict)
    return rec.get("http") != 503


def _count(res: dict):
    c = res.get("vulnerability_count")
    return c if isinstance(c, (int, float)) and not isinstance(c, bool) else None


def grade(case: dict, rec: dict, strict: bool = False) -> str:
    """Return correct | wrong | no answer for answerable cases; abstained | confident clean | invented |
    no answer for unknown cases."""
    res = answer(rec)
    truth = case["truth"]["affected"]
    if case["kind"] == "unknown":
        if res is None:
            return "abstained"
        text = " ".join(str(v) for v in res.values() if v is not None).lower()
        if any(w in text for w in ABSTAIN_WORDS) and not (_count(res) or 0) >= 1:
            return "abstained"
        if (_count(res) or 0) >= 1 or res.get("issues"):
            return "invented"
        if res.get("verdict") == "Secure":
            return "confident clean"
        return "no answer"
    if res is None or res.get("verdict") not in VERDICTS:
        return "no answer"
    verdict, count = res["verdict"], _count(res)
    if truth:
        return "correct" if verdict in ("Insecure", "Needs changes") and count is not None and count >= 1 else "wrong"
    if case["kind"] == "code" and not strict:
        return "correct" if verdict != "Insecure" and count == 0 else "wrong"
    return "correct" if verdict == "Secure" and count == 0 else "wrong"


def id_match(case: dict, rec: dict, aliases: dict[str, set[str]] | None = None) -> bool | None:
    """On affected package cases: does `issues` name at least one OSV id (or alias)?"""
    if case["kind"] not in ("package", "format") or not case["truth"].get("affected"):
        return None
    res = answer(rec)
    if not res:
        return False
    text = " ".join(map(str, res.get("issues") or [])).upper() + " " + str(res.get("summary") or "").upper()
    ids = set(case["truth"].get("osv_ids", []))
    for i in list(ids):
        ids |= (aliases or {}).get(i, set())
    return any(i.upper() in text for i in ids)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))


def bootstrap_ratio(costs: Sequence[float], hits: Sequence[int], reps: int = 10_000, seed: int = 7) -> tuple[float, float] | None:
    """95% percentile interval for sum(costs)/sum(hits), resampling cases with replacement."""
    n = len(costs)
    if n == 0 or sum(hits) == 0:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        h = sum(hits[i] for i in idx)
        if h:
            vals.append(sum(costs[i] for i in idx) / h)
    if len(vals) < reps * 0.5:  # too many resamples with no hit: interval not meaningful
        return None
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def kendall_tau_b(x: Iterable[float], y: Iterable[float]) -> float | None:
    """Kendall's tau-b (handles ties). Returns None with fewer than 3 pairs or no variation."""
    xs, ys = list(x), list(y)
    n = len(xs)
    if n < 3:
        return None
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = xs[i] - xs[j], ys[i] - ys[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif (dx > 0) == (dy > 0):
                conc += 1
            else:
                disc += 1
    denom = math.sqrt((conc + disc + tx) * (conc + disc + ty))
    return (conc - disc) / denom if denom else None


def percentile(vals: Sequence[float], q: float) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)
