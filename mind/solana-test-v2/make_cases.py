#!/usr/bin/env python3
"""Build the hard Solana case set (use case 3) from OSV, deps.dev and the npm registry, by a fixed
rule (see RULE.md). Nothing is picked by hand after looking at any answer.

    SSL_CERT_FILE=... python mind/solana-test-v2/make_cases.py   # writes mind/solana-test-v2/cases.json

Case types (each kept only if the check in brackets passes; failures are listed in `dropped`):
  malicious   look-alike npm packages aimed at Solana developers [an OSV MAL- record names the
              package; the version is the newest one npm's history says was published, other than
              its "0.0.1-security" placeholder]
  withdrawn   @solana/web3.js 1.95.6, the other hijacked release [OSV lists it; npm's history has it]
  latest      a Solana-stack dependency whose current default release is still affected
              [OSV lists an advisory for the default release on deps.dev]
  recent      a Solana-stack dependency with an advisory published on or after 2026-05-01: the newest
              published version that the most recent such advisory affects [OSV confirms it]
  clean       current default releases with no OSV advisory [OSV lists none]
  unknown     plausible Solana names that were never published [npm 404 and no OSV record]
Truth is frozen with the time it was read; the committed file is the reference.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ECO = {"npm": ("npm", "npm"), "cargo": ("crates.io", "cargo")}
RECENT_SINCE = "2026-05-01"

MALICIOUS = ["solana-web3.js", "solana-web3", "solana-transaction-toolkit", "solana-stable-web-huks"]
WITHDRAWN = [("npm", "@solana/web3.js", "1.95.6")]
LATEST = [("npm", "bigint-buffer", "big-integer buffer conversion under @solana/buffer-layout-utils (SPL token tooling)"),
          ("npm", "elliptic", "elliptic-curve library common in wallet and Solana JS tooling")]
RECENT = [("cargo", "anchor-lang", "Anchor, the main framework for Solana programs"),
          ("cargo", "tokio", "async runtime under the Solana Rust client and validator tooling"),
          ("cargo", "rustls", "TLS for Solana Rust RPC clients"),
          ("npm", "ws", "WebSocket client used by Solana RPC subscriptions")]
CLEAN = [("npm", "@solana/web3.js"), ("npm", "@coral-xyz/anchor"), ("npm", "bs58")]
UNKNOWN = ["solana-web3-js", "solana-spl-token", "solana-keypair"]


def ctx():
    c = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        c.load_verify_locations(os.environ["SSL_CERT_FILE"])
    return c


def get(url: str, body: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "adversarialeval-cases"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx()) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def osv(ptype: str, name: str, ver: str | None = None) -> list[dict]:
    body = {"package": {"ecosystem": ECO[ptype][0], "name": name}, **({"version": ver} if ver else {})}
    return (get("https://api.osv.dev/v1/query", body) or {}).get("vulns", [])


def deps(ptype: str, name: str):
    return get(f"https://api.deps.dev/v3/systems/{ECO[ptype][1]}/packages/{urllib.parse.quote(name, safe='')}") or {}


def default_version(pk: dict) -> str | None:
    return next((v["versionKey"]["version"] for v in pk.get("versions", []) if v.get("isDefault")), None)


def npm_history(name: str) -> dict:
    d = get(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}") or {}
    return {k: v for k, v in (d.get("time") or {}).items() if k not in ("created", "modified")}


def purl(ptype: str, name: str, ver: str) -> str:
    return f"pkg:{ptype}/{name}@{ver}"


def slug(s: str) -> str:
    return s.strip("@").replace("/", "-").replace(".", "_")


def case(kind, ptype, name, ver, why, affected, ids=(), **extra):
    ids = sorted(ids)
    src = (f"https://osv.dev/vulnerability/{ids[0]}" if ids else
           f"https://osv.dev/list?ecosystem={urllib.parse.quote(ECO[ptype][0])}&q={urllib.parse.quote(name)}")
    return {"id": f"{kind}-{ptype}-{slug(name)}", "kind": "unknown" if affected is None else "package", "type": kind,
            "ecosystem": ECO[ptype][0], "target": purl(ptype, name, ver), "why": why,
            "truth": {"affected": affected, "osv_ids": list(ids), "source_url": src}, **extra}


def main() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cases, dropped = [], []

    for name in MALICIOUS:
        mal = [v["id"] for v in osv("npm", name) if v["id"].startswith("MAL-")]
        hist = [v for v, t in sorted(npm_history(name).items(), key=lambda kv: kv[1]) if v != "0.0.1-security"]
        if not mal or not hist:
            dropped.append({"package": name, "reason": "no MAL record" if not mal else "no published version in npm history"}); continue
        ver = hist[-1]
        hit = [v["id"] for v in osv("npm", name, ver)]
        if not any(i.startswith("MAL-") for i in hit):
            dropped.append({"package": name, "reason": f"OSV doesn't list {ver} as malicious"}); continue
        cases.append(case("malicious", "npm", name, ver, "look-alike of a Solana package; known malware", True, hit,
                          withdrawn_from_registry=True))

    for ptype, name, ver in WITHDRAWN:
        hit = [v["id"] for v in osv(ptype, name, ver)]
        if not hit or ver not in npm_history(name):
            dropped.append({"package": name, "reason": f"{ver}: no OSV record or not in npm history"}); continue
        cases.append(case("withdrawn", ptype, name, ver, "the other hijacked @solana/web3.js release", True, hit,
                          withdrawn_from_registry=True))

    for ptype, name, why in LATEST:
        d = default_version(deps(ptype, name))
        hit = [v["id"] for v in osv(ptype, name, d)] if d else []
        if not hit:
            dropped.append({"package": name, "reason": f"default release {d} has no advisory"}); continue
        cases.append(case("latest", ptype, name, d, why + " (current default release, still affected)", True, hit))

    for ptype, name, why in RECENT:
        pk = deps(ptype, name)
        recent = sorted((v for v in osv(ptype, name) if v.get("published", "") >= RECENT_SINCE),
                        key=lambda v: v["published"])
        if not recent:
            dropped.append({"package": name, "reason": f"no advisory published since {RECENT_SINCE}"}); continue
        adv = recent[-1]
        versions = sorted(pk.get("versions", []), key=lambda v: v.get("publishedAt", ""), reverse=True)
        chosen = None
        for v in versions[:80]:
            ver = v["versionKey"]["version"]
            if any(x["id"] == adv["id"] for x in osv(ptype, name, ver)):
                chosen = ver
                break
        if not chosen:
            dropped.append({"package": name, "reason": f"no published version found affected by {adv['id']}"}); continue
        hit = [v["id"] for v in osv(ptype, name, chosen)]
        cases.append(case("recent", ptype, name, chosen, f"{why}; advisory {adv['id']} published {adv['published'][:10]}",
                          True, hit, recent_advisory=adv["id"], recent_published=adv["published"][:10]))
        d = default_version(pk)
        if d and not osv(ptype, name, d):
            cases.append(case("clean", ptype, name, d, why + " (current default release)", False))
        else:
            dropped.append({"package": name, "reason": f"clean twin: default release {d} has advisories"})

    for ptype, name in CLEAN:
        d = default_version(deps(ptype, name))
        if d and not osv(ptype, name, d):
            cases.append(case("clean", ptype, name, d, "core Solana package (current default release)", False))
        else:
            dropped.append({"package": name, "reason": f"default release {d} has advisories"})

    for name in UNKNOWN:
        if get(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}") is None and not osv("npm", name):
            cases.append(case("unknown", "npm", name, "1.0.0", "plausible Solana package name that was never published", None))
        else:
            dropped.append({"package": name, "reason": "exists on npm or OSV"})

    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), ids
    for c in cases:
        assert len(c["target"].encode()) <= 256, c["target"]
    out = {"name": "solana-dependencies-v2-hard", "truth_read_at": now, "rule": "mind/solana-test-v2/RULE.md",
           "cases": cases, "dropped": dropped}
    (HERE / "cases.json").write_text(json.dumps(out, indent=1) + "\n")
    t = [c["truth"]["affected"] for c in cases]
    print(f"{len(cases)} cases ({t.count(True)} affected, {t.count(False)} clean, {t.count(None)} unknown); dropped {len(dropped)}")
    for c in cases:
        print(f"  {c['type']:9} {c['target']:52} {c['truth']['osv_ids'][:3]}")
    for d in dropped:
        print("  dropped:", d)


if __name__ == "__main__":
    sys.exit(main())
