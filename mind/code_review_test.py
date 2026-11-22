#!/usr/bin/env python3
"""Code-review comparison for the Dependency Guard Mind: buy one answer per benchmark code snippet.

    python mind/code_review_test.py --miner 20260828 --max-spend 0.15 --out mind/evidence/<file>.json
    python mind/code_review_test.py --routed ...        # the ranked route instead (needs $0.26 free)

Uses the 12 code cases in bench/cases-v2.json (6 CWEs, each vulnerable and fixed) and grades each
answer with the benchmark's frozen rule (bench/benchlib.grade). There is no free oracle for code,
so Verified Ask doesn't apply here. The Anjoman key is added by the session proxy, or taken from
ANJOMAN_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))
from benchlib import grade  # noqa: E402

ANJOMAN = "https://backend.telegraphprotocol.com"


def ask(target: str, miner: str | None) -> dict:
    url = f"{ANJOMAN}/engine/ask" + (f"/{miner}" if miner else "")
    headers = {"Content-Type": "application/json", "User-Agent": "adversarialeval-dependency-guard/0.1"}  # Cloudflare blocks the default
    if os.environ.get("ANJOMAN_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['ANJOMAN_API_KEY']}"
    req = urllib.request.Request(url, data=json.dumps({"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": target}}).encode(),
                                 headers=headers, method="POST")
    ctx = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        ctx.load_verify_locations(os.environ["SSL_CERT_FILE"])
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
            status, body = r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read() or b"{}"
        try:
            status, body = e.code, json.loads(raw)
        except json.JSONDecodeError:
            status, body = e.code, {"message": raw.decode(errors="replace")[:200]}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"http": None, "ms": int((time.time() - t0) * 1000), "result": None, "cost_usd": 0, "receipt": None, "error": str(e)[:200]}
    r = body.get("result") or {}
    return {"http": status, "ms": int((time.time() - t0) * 1000), "miner": r.get("miner_name"), "miner_id": r.get("miner_id"),
            "result": r.get("result"), "cost_usd": r.get("cost_usd_total") or r.get("cost_usd") or 0,
            "receipt": (body.get("receipt") or {}).get("receipt_hash"),
            "error": None if status == 200 else str(body.get("message") or body.get("error"))[:200]}


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--miner")
    g.add_argument("--routed", action="store_true")
    ap.add_argument("--max-spend", type=float, default=0.15)
    ap.add_argument("--cases", type=Path, help="a case file such as mind/code-test-v2/cases.json (default: the benchmark's 12 code cases)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    import hashlib
    import subprocess
    src = a.cases or ROOT / "bench" / "cases-v2.json"
    cases = [c for c in json.loads(src.read_text())["cases"] if a.cases or c["kind"] == "code"]
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    run = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "arm": "routed" if a.routed else f"miner {a.miner}",
           "rule": "bench/RULE-v2.md grading (fixed code: not Insecure and count 0)", "cases_file": str(src.relative_to(ROOT)),
           "cases_sha256": hashlib.sha256(src.read_bytes()).hexdigest(), "repo_commit": commit, "cases": []}
    spent = 0.0
    for c in cases:
        if spent + 0.02 > a.max_spend + 1e-9:
            run["cases"].append({"case": c["id"], "skipped": "spending cap"})
            continue
        r = ask(c["target"], None if a.routed else a.miner)
        spent += float(r["cost_usd"] or 0)
        g_ = grade({**c, "kind": "code"}, {"http": r["http"], "result": r["result"]})
        run["cases"].append({"case": c["id"], "group": c.get("kind", "code"), "cwe": c.get("cwe") or c["truth"].get("cwe"),
                             "vulnerable": c["truth"]["affected"], **r, "grade": g_})
        v = (r["result"] or {}).get("verdict")
        print(f"{c['id']:24} {str(v):14} {g_:10} ${r['cost_usd']} {r.get('error') or ''}")
    run["spent_usd"] = round(spent, 2)
    run["correct"] = sum(x.get("grade") == "correct" for x in run["cases"])
    a.out.write_text(json.dumps(run, indent=1) + "\n")
    print(f"correct {run['correct']}/{len(cases)}; spent ${run['spent_usd']}; saved {a.out}")


if __name__ == "__main__":
    main()
