#!/usr/bin/env python3
"""Audit which miners on an intent can take a canonical request, next to their ranking.

    python tools/miner_audit.py                       # SECURITY_REVIEW_GENERAL, three target kinds
    python tools/miner_audit.py --out eval/reports/raw/2026-11-15-miner-audit.json

For every miner the node lists on the intent, this sends the intent's canonical request
(`{"intent": ..., "params": {"target": ...}}`) to `POST /engine/v1/ask/{minerId}` WITHOUT a
payment. The node validates and maps params before it asks for payment, so the answer is
free and tells us whether a buyer could reach that miner at all:

    402  payment required: the node can map the request onto the miner (callable)
    503  no_compatible_miner: the miner's API has no field for a required param
    422  the node predicts the call would fail (not charged)

No wallet, key or payment is involved. Ranks and scores come from the public `GET /api/miners`.
Requests are sequential with a pause, so this is light on the node.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

NODE = "https://devnode.telegraphprotocol.com"
TARGETS = {
    # one realistic target of each kind the intent's description names
    "package": "pypi:jinja2@2.10",
    "advisory": "CVE-2021-44228",
    "code": "app.get('/u', (req, res) => db.query(\"SELECT * FROM users WHERE id = \" + req.query.id))",
}


def curl_json(url: str, body: dict | None = None, timeout: int = 60) -> tuple[str, dict | list | str]:
    with tempfile.NamedTemporaryFile() as out:
        cmd = ["curl", "-sS", "-m", str(timeout), "-o", out.name, "-w", "%{http_code}", url]
        if body is not None:
            cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(body)]
        code = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
        raw = Path(out.name).read_text(errors="replace")
    try:
        return code, json.loads(raw)
    except json.JSONDecodeError:
        return code, raw[:300]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", default="SECURITY_REVIEW_GENERAL")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--pause", type=float, default=1.5)
    a = ap.parse_args()

    code, intent = curl_json(f"{NODE}/engine/v1/intents/{a.intent}")
    if code != "200":
        sys.exit(f"intent lookup failed: HTTP {code} {intent}")
    _, all_miners = curl_json(f"{NODE}/api/miners", timeout=120)
    by_id = {str(m["id"]): m for m in all_miners} if isinstance(all_miners, list) else {}

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for m in intent["miners"]:
        full = by_id.get(str(m["id"]), {})
        score = next((s for s in reversed(full.get("scores") or []) if s.get("intent_id") == a.intent), {})
        schema = full.get("input_schema")
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError:
                schema = {}
        row = {"id": str(m["id"]), "slug": m["slug"], "rank": score.get("rank"), "score": score.get("score"),
               "scored_epoch": score.get("epoch_id"), "operator": (full.get("wallet_address") or "")[:10],
               "input_params": sorted(((schema or {}).get("properties") or {}).keys()), "probes": {}}
        for kind, target in TARGETS.items():
            c, b = curl_json(f"{NODE}/engine/v1/ask/{m['id']}", {"intent": a.intent, "params": {"target": target}})
            price = None
            if isinstance(b, dict):
                price = next((x.get("price") for x in b.get("accepts") or [] if x.get("price")), None)
            row["probes"][kind] = {"http": c, "error": b.get("error") if isinstance(b, dict) else None,
                                   "message": (b.get("message") or "")[:200] if isinstance(b, dict) else str(b)[:200],
                                   "price": price}
            time.sleep(a.pause)
        row["callable"] = [k for k, p in row["probes"].items() if p["http"] == "402"]
        rows.append(row)
        print(f"{row['slug']:32} rank={row['rank']!s:>4} callable={','.join(row['callable']) or '-'}", flush=True)

    result = {"node": NODE, "intent": a.intent, "started_utc": started,
              "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "targets": TARGETS, "miners": rows}
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(result, indent=1) + "\n")
        print(f"wrote {a.out}")
    n = len(rows)
    callable_any = sum(bool(r["callable"]) for r in rows)
    print(f"{callable_any}/{n} miners callable with a canonical request")
    return 0


if __name__ == "__main__":
    sys.exit(main())
