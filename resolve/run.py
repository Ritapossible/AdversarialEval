#!/usr/bin/env python3
"""Run and score the prediction-market test (resolve/RULE.md).

    python resolve/run.py jobs1     # ranked-route jobs                   -> <out>/jobs1.json
    node bench/telegraph_jobs.mjs --jobs <out>/jobs1.json --out <out> --max-spend 0.75
    python resolve/run.py jobs2     # second, independent provider jobs   -> <out>/jobs2.json
    node bench/telegraph_jobs.mjs --jobs <out>/jobs2.json --out <out> --max-spend 0.75
    python resolve/run.py score     # arms A, B, C against the truth      -> <out>/score.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from sources import UA, resolve  # noqa: E402

INTENT = "EVENT_OUTCOME_RESOLUTION_GENERAL"
SECOND = ["20261117", "4433", "59003"]  # fixed order (rule)


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if not n:
        return [0.0, 0.0]
    p, d = k / n, 1 + z * z / n
    c, h = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def fee_addresses(out: Path) -> dict[str, str]:
    f = out / "miners.json"
    if not f.exists():
        req = urllib.request.Request("https://devnode.telegraphprotocol.com/api/miners", headers=UA)
        ms = json.loads(urllib.request.urlopen(req, timeout=120).read())
        f.write_text(json.dumps({str(m["id"]): (m.get("fee_address") or "").lower() for m in ms}, indent=0) + "\n")
    return json.loads(f.read_text())


def outcome(rec: dict | None) -> str:
    r = (rec or {}).get("result") or {}
    o = str(r.get("outcome") or "").lower()
    if o in ("yes", "no", "unresolved"):
        return o
    if r.get("resolved_yes") in (True, False):
        return "yes" if r["resolved_yes"] else "no"
    return "unresolved"


def cites(rec: dict | None) -> bool:
    s = ((rec or {}).get("result") or {}).get("sources") or []
    return any(isinstance(x, str) and x.startswith("http") for x in s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["jobs1", "jobs2", "score"])
    ap.add_argument("--out", type=Path, default=ROOT / "bench/out/eventres")
    a = ap.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    markets = json.loads((HERE / "cases.json").read_text())["markets"]
    calls = {c["key"]: c for c in load(out / "calls.ndjson")}

    if a.cmd == "jobs1":
        js = [{"key": f"ranked|{m['id']}", "intent": INTENT, "params": {"event": m["event"]}} for m in markets]
        (out / "jobs1.json").write_text(json.dumps({"jobs": js}, indent=1) + "\n")
        print(len(js), "ranked jobs")
        return

    fees = fee_addresses(out)
    if a.cmd == "jobs2":
        js = []
        for m in markets:
            first = calls.get(f"ranked|{m['id']}") or {}
            first_fee = fees.get(str(first.get("miner_id")), "?")
            pick = next(x for x in SECOND if fees.get(x) and fees[x] != first_fee)
            js.append({"key": f"second|{m['id']}", "intent": INTENT, "params": {"event": m["event"]}, "miner": pick,
                       "first_miner": first.get("miner_id"), "first_fee": first_fee})
        (out / "jobs2.json").write_text(json.dumps({"jobs": js}, indent=1) + "\n")
        print(len(js), "second-provider jobs")
        return

    rows = []
    for m in markets:
        r1, r2 = calls.get(f"ranked|{m['id']}"), calls.get(f"second|{m['id']}")
        o1, o2 = outcome(r1), outcome(r2)
        A = o1 if o1 in ("yes", "no") else "unresolved"
        B = o1 if o1 == o2 and o1 in ("yes", "no") else "unresolved"
        if m["contract"]:
            C, ev = resolve(m["contract"])
            c_how = "official source in the contract"
        else:
            agree = o1 == o2 and o1 in ("yes", "no") and cites(r1) and cites(r2)
            C, ev = (o1 if agree else "unresolved"), {}
            c_how = "two independent answers agree, each citing a source" if agree else "left for a person"
        rows.append({"id": m["id"], "kind": m["kind"], "truth": m["truth"], "A": A, "B": B, "C": C, "C_how": c_how,
                     "C_caught_dispute": bool(m["contract"]) and o1 in ("yes", "no") and o1 != C,
                     "first": {"miner": (r1 or {}).get("miner"), "miner_id": (r1 or {}).get("miner_id"), "outcome": o1,
                               "sources": ((r1 or {}).get("result") or {}).get("sources"), "error": (r1 or {}).get("error")},
                     "second": {"miner": (r2 or {}).get("miner"), "miner_id": (r2 or {}).get("miner_id"), "outcome": o2,
                                "sources": ((r2 or {}).get("result") or {}).get("sources"), "error": (r2 or {}).get("error")}})
    n = len(rows)
    summary = {"markets": n, "truth": {k: sum(r["truth"] == k for r in rows) for k in ("yes", "no", "unresolved")}}
    for arm in "ABC":
        wrong = sum(r[arm] in ("yes", "no") and r[arm] != r["truth"] for r in rows)
        ok = sum(r[arm] == r["truth"] for r in rows)
        summary[arm] = {"correct": ok, "wilson": wilson(ok, n), "wrong_settlements": wrong,
                        "left_unresolved_when_resolvable": sum(r[arm] == "unresolved" and r["truth"] != "unresolved" for r in rows)}
    summary["C"]["disputes_caught"] = sum(r["C_caught_dispute"] for r in rows)
    paid = [c for c in calls.values() if c.get("paid")]
    summary["telegraph"] = {"calls": len(calls), "paid": len(paid), "usd": round(0.01 * len(paid), 2),
                            "median_wall_s": sorted(c["wall_ms"] for c in paid)[len(paid) // 2] / 1000 if paid else None,
                            "first_answer_miners": sorted({str(r["first"]["miner"]) for r in rows})}
    (out / "score.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
