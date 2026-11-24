#!/usr/bin/env python3
"""Check every Solana payment of a run against Solana devnet itself.

    SSL_CERT_FILE=... python bench/solana_reconcile.py bench/out/solana-v2 [--rpc https://api.devnet.solana.com]

For each call in <run>/calls.ndjson with a transaction signature, fetch the transaction from the
RPC and confirm: it succeeded, it moved devnet USDC (mint 4zMMC9…ncDU) out of the payer, and how
much. Writes <run>/onchain.json and prints totals. A call marked paid without a confirmed
transaction, or a confirmed transaction the run didn't record, is reported.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import time
import urllib.request
from pathlib import Path

USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"


def rpc(url: str, method: str, params: list):
    ctx = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        ctx.load_verify_locations(os.environ["SSL_CERT_FILE"])
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(5):
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                out = json.loads(r.read())
            if "error" in out and out["error"].get("code") == 429:
                raise RuntimeError("rate limited")
            return out.get("result")
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def usdc_moves(tx: dict, payer: str) -> dict:
    meta = tx.get("meta") or {}
    def bal(xs):
        return {(b["owner"], b["mint"]): int(b["uiTokenAmount"]["amount"]) for b in xs or []}
    pre, post = bal(meta.get("preTokenBalances")), bal(meta.get("postTokenBalances"))
    keys = set(pre) | set(post)
    deltas = {k[0]: post.get(k, 0) - pre.get(k, 0) for k in keys if k[1] == USDC}
    return {"payer_delta_micro": deltas.get(payer, 0),
            "receivers": {o: d for o, d in deltas.items() if d > 0}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--rpc", default="https://api.devnet.solana.com")
    a = ap.parse_args()
    calls = [json.loads(l) for l in (a.run / "calls.ndjson").read_text().splitlines() if l.strip()]
    payer = json.loads((a.run / "decisions.json").read_text())["payer"]
    rows, total = [], 0
    for c in calls:
        sig = c.get("solana_tx")
        if not sig:
            rows.append({"case": c["case"], "arm": c["arm"], "paid_in_run": c.get("paid"), "tx": None, "onchain": "no signature"})
            continue
        tx = rpc(a.rpc, "getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}])
        if not tx:
            rows.append({"case": c["case"], "arm": c["arm"], "tx": sig, "onchain": "not found"}); continue
        ok = (tx.get("meta") or {}).get("err") is None
        mv = usdc_moves(tx, payer)
        paid = -mv["payer_delta_micro"] if ok else 0
        total += paid
        rows.append({"case": c["case"], "arm": c["arm"], "tx": sig, "slot": tx.get("slot"), "block_time": tx.get("blockTime"),
                     "onchain": "success" if ok else f"failed: {tx['meta']['err']}", "usdc_paid": paid / 1e6,
                     "receivers": {k: v / 1e6 for k, v in mv["receivers"].items()}})
    summary = {"payer": payer, "network": "solana-devnet", "calls": len(calls),
               "with_signature": sum(1 for r in rows if r.get("tx")),
               "confirmed_success": sum(1 for r in rows if r.get("onchain") == "success"),
               "usdc_paid_onchain": round(total / 1e6, 6),
               "paid_in_run_without_tx": [f"{r['case']}|{r['arm']}" for r in rows if r.get("paid_in_run") and not r.get("tx")],
               "explorer": "https://explorer.solana.com/tx/<signature>?cluster=devnet"}
    (a.run / "onchain.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
