#!/usr/bin/env python3
"""Build the Solana dependency case set from OSV and deps.dev, by a fixed rule (see RULE.md).

    python mind/solana-test/make_cases.py            # writes mind/solana-test/cases.json

For each candidate (a Solana-stack package and an affected version chosen from a known advisory):
  - the affected version must have at least one OSV advisory, and exist on the registry (deps.dev)
    unless it was withdrawn: a version the registry no longer lists but OSV does (a hijacked or
    malicious release) is kept and marked `withdrawn_from_registry`;
  - its clean twin is the package's current default release on deps.dev, which must have none;
  - a pair failing either check is dropped and listed in `dropped`, never edited.
Two versions that don't exist are added as "unknown" cases. Truth is frozen with the time it was
read; re-running later can give different truth, so the committed file is the reference.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OSV = {"npm": "npm", "cargo": "crates.io"}
DEPS = {"npm": "npm", "cargo": "cargo"}

# (purl type, package, affected version, why it's in the Solana stack)
CANDIDATES = [
    ("npm", "@solana/web3.js", "1.95.7", "Solana's JavaScript SDK; 1.95.6 and 1.95.7 were hijacked releases"),
    ("npm", "secp256k1", "4.0.3", "secp256k1 signatures, a dependency of older @solana/web3.js"),
    ("npm", "ws", "8.17.0", "WebSocket client used by Solana RPC subscriptions (rpc-websockets)"),
    ("npm", "node-fetch", "2.6.6", "HTTP client used by @solana/web3.js"),
    ("npm", "elliptic", "6.5.4", "elliptic-curve library common in wallet and Solana JS tooling"),
    ("cargo", "ed25519-dalek", "1.0.1", "Ed25519 signatures, used by Solana's Rust SDK"),
    ("cargo", "curve25519-dalek", "3.2.0", "curve arithmetic under ed25519-dalek in Solana crates"),
    ("cargo", "borsh", "0.9.3", "Borsh serialisation, Solana's account and instruction encoding"),
]
UNKNOWN = [("npm", "@solana/web3.js", "9.9.9"), ("cargo", "solana-program", "99.0.0")]


def ctx():
    c = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        c.load_verify_locations(os.environ["SSL_CERT_FILE"])
    return c


def get(url: str, body: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "adversarialeval-cases"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx()) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def osv(ptype: str, name: str, ver: str) -> list[dict]:
    return (get("https://api.osv.dev/v1/query", {"package": {"ecosystem": OSV[ptype], "name": name}, "version": ver}) or {}).get("vulns", [])


def package(ptype: str, name: str):
    return get(f"https://api.deps.dev/v3/systems/{DEPS[ptype]}/packages/{urllib.parse.quote(name, safe='')}")


def purl(ptype: str, name: str, ver: str) -> str:
    return f"pkg:{ptype}/{name}@{ver}"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cases, dropped = [], []
    for ptype, name, bad, why in CANDIDATES:
        pk = package(ptype, name)
        versions = {v["versionKey"]["version"]: v for v in (pk or {}).get("versions", [])}
        default = next((k for k, v in versions.items() if v.get("isDefault")), None)
        vb = osv(ptype, name, bad)
        withdrawn = bad not in versions
        if withdrawn and not vb:
            dropped.append({"package": name, "reason": f"{bad} not published and unknown to OSV"}); continue
        if not vb:
            dropped.append({"package": name, "reason": f"OSV lists no advisory for {bad}"}); continue
        if not default:
            dropped.append({"package": name, "reason": "no default release on deps.dev"}); continue
        vg = osv(ptype, name, default)
        if vg:
            dropped.append({"package": name, "reason": f"default release {default} still has {len(vg)} advisories"}); continue
        ids = sorted(x["id"] for x in vb)
        cases.append({"id": f"{ptype}-{name.strip('@').replace('/', '-')}-affected", "kind": "package", "ecosystem": OSV[ptype],
                      "target": purl(ptype, name, bad), "why": why, "withdrawn_from_registry": withdrawn,
                      "truth": {"affected": True, "osv_count": len(vb), "osv_ids": ids,
                                "source_url": f"https://osv.dev/vulnerability/{ids[0]}"}})
        cases.append({"id": f"{ptype}-{name.strip('@').replace('/', '-')}-latest", "kind": "package", "ecosystem": OSV[ptype],
                      "target": purl(ptype, name, default), "why": why + " (current default release)",
                      "truth": {"affected": False, "osv_count": 0, "osv_ids": [],
                                "source_url": f"https://osv.dev/list?ecosystem={urllib.parse.quote(OSV[ptype])}&q={urllib.parse.quote(name)}"}})
    for ptype, name, ver in UNKNOWN:
        pk = package(ptype, name)
        published = ver in {v["versionKey"]["version"] for v in (pk or {}).get("versions", [])}
        if published:
            dropped.append({"package": name, "reason": f"{ver} unexpectedly exists"}); continue
        cases.append({"id": f"unknown-{ptype}-{name.strip('@').replace('/', '-')}", "kind": "unknown", "ecosystem": OSV[ptype],
                      "target": purl(ptype, name, ver), "why": "version never published",
                      "truth": {"affected": None}})
    for c in cases:
        assert len(c["target"].encode()) <= 256, c["target"]
    out = {"name": "solana-dependencies-v1", "truth_read_at": now, "rule": "mind/solana-test/RULE.md",
           "cases": cases, "dropped": dropped}
    (HERE / "cases.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(cases)} cases ({sum(c['truth']['affected'] is True for c in cases)} affected, "
          f"{sum(c['truth']['affected'] is False for c in cases)} clean, {sum(c['truth']['affected'] is None for c in cases)} unknown); "
          f"dropped {len(dropped)}")
    for d in dropped:
        print("  dropped:", d)


if __name__ == "__main__":
    sys.exit(main())
