#!/usr/bin/env python3
"""Build case set v2 for the paid SECURITY_REVIEW benchmark by a fixed rule (bench/RULE-v2.md).

    python bench/make_cases_v2.py        # -> bench/cases-v2.json (run once, before any round-2 call)

Selection never looks at miner answers. Package cases, per ecosystem, walking a fixed candidate list
in order and keeping the first two packages that pass:
  * "latest clean": the registry's default (latest stable) release, kept only if OSV lists 0 vulns;
  * "last affected": in the package's most recently published OSV advisory that has a fix, the
    highest affected non-prerelease version; kept only if OSV lists >= 1 vuln for it.
Code cases are hand-written twins, one vulnerable and one fixed per CWE, judged by construction.
Ground truth is frozen with the date of the OSV query; it is not refreshed between rounds.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRERELEASE = re.compile(r"(a|b|rc|alpha|beta|dev|pre|snapshot|m)\d*", re.I)

# ecosystem: (OSV name, purl type, deps.dev system or None, candidates in fixed order)
ECOSYSTEMS = {
    "PyPI": ("PyPI", "pypi", "pypi", ["jinja2", "pyyaml", "requests", "urllib3", "werkzeug", "pillow", "flask", "django"]),
    "npm": ("npm", "npm", "npm", ["lodash", "minimist", "axios", "jsonwebtoken", "express", "ws", "node-fetch", "moment"]),
    "Maven": ("Maven", "maven", "maven", ["org.apache.logging.log4j:log4j-core", "com.fasterxml.jackson.core:jackson-databind",
                                            "org.yaml:snakeyaml", "commons-io:commons-io", "org.springframework:spring-web"]),
    "Go": ("Go", "golang", "go", ["github.com/gin-gonic/gin", "golang.org/x/net", "golang.org/x/crypto",
                                   "github.com/gorilla/websocket", "google.golang.org/protobuf"]),
    "crates.io": ("crates.io", "cargo", "cargo", ["hyper", "tokio", "regex", "time", "smallvec", "h2"]),
    "RubyGems": ("RubyGems", "gem", None, ["rack", "nokogiri", "activesupport", "puma", "rails-html-sanitizer"]),
}

CODE = [  # (id, cwe, language, vulnerable snippet, fixed snippet)
    ("sqli", "CWE-89", "Python",
     "Python/Flask: cur.execute(\"SELECT * FROM users WHERE name = '\" + request.args['name'] + \"'\")",
     "Python/Flask: cur.execute(\"SELECT * FROM users WHERE name = %s\", (request.args['name'],))"),
    ("xss", "CWE-79", "JavaScript",
     "Browser JS: document.getElementById('out').innerHTML = new URLSearchParams(location.search).get('q')",
     "Browser JS: document.getElementById('out').textContent = new URLSearchParams(location.search).get('q')"),
    ("path", "CWE-22", "JavaScript",
     "Node/Express: app.get('/f', (q, r) => r.sendFile(path.join(__dirname, 'files', q.query.name)))",
     "Node/Express: app.get('/f', (q, r) => r.sendFile(path.basename(q.query.name), { root: path.join(__dirname, 'files') }))"),
    ("cmd", "CWE-78", "Python",
     "Python: subprocess.run('ping -c 1 ' + request.args['host'], shell=True)",
     "Python: subprocess.run(['ping', '-c', '1', '--', request.args['host']], shell=False)"),
    ("deser", "CWE-502", "Python",
     "Python/Flask: data = pickle.loads(base64.b64decode(request.cookies['session']))",
     "Python/Flask: data = json.loads(base64.b64decode(request.cookies['session']))"),
    ("hash", "CWE-916", "Python",
     "Python: stored = hashlib.md5(password.encode()).hexdigest()  # user password storage",
     "Python: stored = bcrypt.hashpw(password.encode(), bcrypt.gensalt())  # user password storage"),
]


def get(url: str, body: dict | None = None):
    cmd = ["curl", "-sS", "-m", "60", "--retry", "3", url]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def osv_vulns(eco: str, name: str, version: str | None = None) -> list[dict]:
    q = {"package": {"ecosystem": eco, "name": name}}
    if version:
        q["version"] = version
    vulns, token = [], None
    while True:
        d = get("https://api.osv.dev/v1/query", {**q, **({"page_token": token} if token else {})})
        vulns += d.get("vulns", [])
        token = d.get("next_page_token")
        if not token:
            return vulns


def latest(eco: str, system: str | None, name: str) -> str | None:
    if system is None:  # RubyGems
        d = get(f"https://rubygems.org/api/v1/versions/{name}/latest.json")
        return d.get("version")
    d = get(f"https://api.deps.dev/v3/systems/{system}/packages/{urllib.parse.quote(name, safe='')}")
    v = [x["versionKey"]["version"] for x in d.get("versions", []) if x.get("isDefault")]
    return v[0] if v else None


def osv_version(eco: str, v: str) -> str:
    return v[1:] if eco == "Go" and v.startswith("v") else v


def purl(ptype: str, name: str, version: str) -> str:
    if ptype == "maven":
        g, a = name.split(":")
        return f"pkg:maven/{g}/{a}@{version}"
    if ptype == "golang":
        return f"pkg:golang/{name}@{version if version.startswith('v') else 'v' + version}"
    return f"pkg:{ptype}/{name}@{version}"


def semver_key(v: str) -> tuple:
    core = v.lstrip("v").split("+")[0].split("-")[0]
    return tuple(int(p) if p.isdigit() else 0 for p in core.split("."))


def registry_versions(system: str | None, name: str) -> list[str]:
    if system is None:
        return []
    d = get(f"https://api.deps.dev/v3/systems/{system}/packages/{urllib.parse.quote(name, safe='')}")
    return [x["versionKey"]["version"] for x in d.get("versions", []) if "-" not in x["versionKey"]["version"]]


def last_affected(eco: str, system: str | None, name: str) -> tuple[str, str] | None:
    vulns = [v for v in osv_vulns(eco, name) if not v.get("withdrawn")]
    vulns.sort(key=lambda v: v.get("published", ""), reverse=True)
    releases = None
    for v in vulns:
        for aff in v.get("affected", []):
            if aff.get("package", {}).get("name", "").lower() != name.lower():
                continue
            has_fix = any("fixed" in e for r in aff.get("ranges", []) for e in r.get("events", []))
            if not has_fix:
                continue
            stable = [x for x in aff.get("versions", []) if not PRERELEASE.search(x.split("+")[0].split(".")[-1])]
            if stable:
                return stable[-1], v["id"]
            # SEMVER ranges (Go, crates.io) list no versions: take the highest registry release
            # inside the first range that has both ends
            for r in aff.get("ranges", []):
                if r.get("type") != "SEMVER":
                    continue
                intro = next((e["introduced"] for e in r["events"] if "introduced" in e), "0")
                fixed = next((e["fixed"] for e in r["events"] if "fixed" in e), None)
                if not fixed:
                    continue
                releases = releases if releases is not None else registry_versions(system, name)
                inside = [x for x in releases if semver_key(intro) <= semver_key(x) < semver_key(fixed)]
                if inside:
                    return max(inside, key=semver_key), v["id"]
    return None


def main() -> None:
    cases = []
    for label, (eco, ptype, system, candidates) in ECOSYSTEMS.items():
        kept = 0
        for name in candidates:
            if kept == 2:
                break
            try:
                cur = latest(eco, system, name)
                la = last_affected(eco, system, name)
            except Exception as e:  # network or parse failure: skip this candidate, recorded below
                print(f"skip {label} {name}: {e}")
                continue
            if not cur or not la:
                print(f"skip {label} {name}: no latest or no fixed advisory")
                continue
            clean = osv_vulns(eco, name, osv_version(eco, cur))
            hit = osv_vulns(eco, name, osv_version(eco, la[0]))
            if clean or not hit:
                print(f"skip {label} {name}: latest {cur} has {len(clean)} vulns, {la[0]} has {len(hit)}")
                continue
            kept += 1
            src = f"https://osv.dev/list?ecosystem={urllib.parse.quote(eco)}&q={urllib.parse.quote(name)}"
            cases.append({"id": f"{ptype}-{name.split('/')[-1].split(':')[-1]}-affected", "kind": "package", "ecosystem": label,
                          "target": purl(ptype, name, la[0]),
                          "truth": {"affected": True, "osv_count": len(hit), "osv_ids": sorted(x["id"] for x in hit),
                                    "selected_via": la[1], "source_url": src}})
            cases.append({"id": f"{ptype}-{name.split('/')[-1].split(':')[-1]}-latest", "kind": "package", "ecosystem": label,
                          "target": purl(ptype, name, cur),
                          "truth": {"affected": False, "osv_count": 0, "osv_ids": [], "source_url": src}})
        print(f"{label}: kept {kept}")
    for cid, cwe, lang, bad, good in CODE:
        src = f"https://cwe.mitre.org/data/definitions/{cwe.split('-')[1]}.html"
        cases.append({"id": f"code-{cid}-vulnerable", "kind": "code", "target": bad,
                      "truth": {"affected": True, "cwe": cwe, "language": lang, "source_url": src}})
        cases.append({"id": f"code-{cid}-fixed", "kind": "code", "target": good,
                      "truth": {"affected": False, "cwe": cwe, "language": lang, "source_url": src}})
    assert not osv_vulns("PyPI", "adversarialeval-no-such-package-7f3c", "1.0.0")
    cases.append({"id": "unknown-package", "kind": "unknown", "target": "pkg:pypi/adversarialeval-no-such-package-7f3c@1.0.0",
                  "truth": {"affected": None, "note": "package does not exist on PyPI"}})
    cases.append({"id": "unknown-version", "kind": "unknown", "target": "pkg:pypi/jinja2@99.0.0",
                  "truth": {"affected": None, "note": "jinja2 has no release 99.0.0"}})
    # format probe: the first four affected package cases, restated in two other common forms
    affected = [c for c in cases if c["kind"] == "package" and c["truth"]["affected"]][:4]
    for c in affected:
        m = re.match(r"pkg:([^/]+)/(.+)@(.+)$", c["target"])
        ptype, name, ver = m.groups()
        name = name.replace("/", ":") if ptype == "maven" else name
        for fid, text in (("plain", f"{name} {ver} ({c['ecosystem']})"),
                          ("question", f"Is {name} version {ver} from {c['ecosystem']} affected by known vulnerabilities?")):
            cases.append({"id": f"{c['id']}-fmt-{fid}", "kind": "format", "of": c["id"], "target": text, "truth": c["truth"]})
    for c in cases:
        assert len(c["target"].encode()) <= 256, c["id"]
    assert len({c["id"] for c in cases}) == len(cases)
    out = {"frozen_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "rule": "bench/RULE-v2.md", "cases": cases}
    (HERE / "cases-v2.json").write_text(json.dumps(out, indent=1) + "\n")
    from collections import Counter
    print(Counter(c["kind"] for c in cases), len(cases))


if __name__ == "__main__":
    main()
