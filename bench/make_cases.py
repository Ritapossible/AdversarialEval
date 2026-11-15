#!/usr/bin/env python3
"""Freeze the benchmark cases with OSV ground truth (run once, before any paid call).

    python bench/make_cases.py   # -> bench/cases.json
"""
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKGS = [  # (purl target, OSV ecosystem, name, version)
    ("pkg:pypi/jinja2@2.10", "PyPI", "jinja2", "2.10"),
    ("pkg:npm/lodash@4.17.15", "npm", "lodash", "4.17.15"),
    ("pkg:pypi/jinja2@3.1.6", "PyPI", "jinja2", "3.1.6"),
    ("pkg:npm/express@4.21.2", "npm", "express", "4.21.2"),
]


def osv(eco, name, ver):
    out = subprocess.run(["curl", "-sS", "-m", "60", "https://api.osv.dev/v1/query", "-d",
                          json.dumps({"package": {"ecosystem": eco, "name": name}, "version": ver})],
                         capture_output=True, text=True, check=True).stdout
    return sorted(v["id"] for v in json.loads(out).get("vulns", []))


cases = []
for target, eco, name, ver in PKGS:
    ids = osv(eco, name, ver)
    cases.append({"id": f"{name}-{ver}", "kind": "package", "target": target,
                  "truth": {"affected": bool(ids), "osv_count": len(ids), "osv_ids": ids,
                            "source_url": f"https://osv.dev/list?ecosystem={eco}&q={name}"}})
unknown = "pkg:pypi/adversarialeval-no-such-package-7f3c@1.0.0"
assert not osv("PyPI", "adversarialeval-no-such-package-7f3c", "1.0.0")
cases.append({"id": "unknown-package", "kind": "unknown", "target": unknown,
              "truth": {"affected": None, "note": "package does not exist on PyPI; nothing to verify"}})
cases.append({"id": "code-sqli", "kind": "code",
              "target": "Node/Express: app.get('/u', (req, res) => db.query(\"SELECT * FROM users WHERE id = \" + req.query.id))",
              "truth": {"affected": True, "cwe": "CWE-89", "source_url": "https://cwe.mitre.org/data/definitions/89.html",
                        "note": "user input concatenated into SQL"}})
cases.append({"id": "code-param", "kind": "code",
              "target": "Node/Express: app.get('/u', (req, res) => db.query('SELECT * FROM users WHERE id = $1', [req.query.id]))",
              "truth": {"affected": False, "cwe": "CWE-89", "source_url": "https://cwe.mitre.org/data/definitions/89.html",
                        "note": "parameterised query; no injection"}})
for c in cases:
    assert len(c["target"].encode()) <= 256, c["id"]
Path(HERE / "cases.json").write_text(json.dumps({"frozen_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                 "cases": cases}, indent=1) + "\n")
print("\n".join(f"{c['id']:18} {c['truth'].get('affected')} {c['truth'].get('osv_count', '')}" for c in cases))
