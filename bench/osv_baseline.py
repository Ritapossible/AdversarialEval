#!/usr/bin/env python3
"""Free baseline for rule v2: answer each package case from OSV alone, at $0.

    python bench/osv_baseline.py bench/cases-v2.json bench/out/round-2/osv-baseline.ndjson

Writes records in the same shape as bench/run.mjs (miner "osv-baseline", no payment), so the
scorer treats it like any other target. Code and format-probe cases get no answer (abstain):
a dependency lookup has nothing to say about a code snippet or free text.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone

ECO = {"pypi": "PyPI", "npm": "npm", "maven": "Maven", "golang": "Go", "cargo": "crates.io", "gem": "RubyGems"}


def osv(eco: str, name: str, version: str) -> list[dict] | None:
    out = subprocess.run(["curl", "-sS", "-m", "60", "--retry", "3", "https://api.osv.dev/v1/query", "-d",
                          json.dumps({"package": {"ecosystem": eco, "name": name}, "version": version})],
                         capture_output=True, text=True)
    try:
        return json.loads(out.stdout).get("vulns", [])
    except json.JSONDecodeError:
        return None


def main(cases_path: str, out_path: str) -> None:
    cases = json.load(open(cases_path))["cases"]
    with open(out_path, "w") as f:
        for c in cases:
            rec = {"case": c["id"], "miner_id": "osv-baseline", "miner": "osv-baseline (free)", "rank": None,
                   "target": c["target"], "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "http": None}
            m = re.match(r"pkg:([^/]+)/(.+)@(.+)$", c["target"])
            if m and m.group(1) in ECO:
                ptype, name, ver = m.groups()
                name = name.replace("/", ":") if ptype == "maven" else name
                ver = ver[1:] if ptype == "golang" and ver.startswith("v") else ver
                v = osv(ECO[ptype], name, ver)
                if v is not None:
                    ids = sorted(x["id"] for x in v)
                    rec.update(http=200, result={"verdict": "Insecure" if ids else "Secure",
                                                 "vulnerability_count": len(ids), "issues": ids,
                                                 "summary": f"OSV lists {len(ids)} advisories for {name} {ver}."})
            f.write(json.dumps(rec) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
