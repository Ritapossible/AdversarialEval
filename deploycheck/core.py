"""deploycheck: an independent pre-deployment check for a Python application.

Every finding comes from execution or a public source, never from another model's opinion:
  1. install       the app exactly as a customer would, in a fresh virtualenv; record every
                   resolved package version (the real dependency tree, transitive included)
  2. declared      import the app's entry modules; any module it needs that its package doesn't
                   declare is installed and recorded (an "undeclared dependency")
  3. advisories    OSV for every resolved version (querybatch), records fetched for each hit
  4. reachability  for each advisory, does the app use the vulnerable feature? A reviewed rule
                   per advisory names the code it needs (a component, a call, a platform); the
                   app's own source is searched and the matching lines are recorded
  5. smoke         the app is built and served for real (an app-specific script); pass or fail
  6. telegraph     optional: one paid SECURITY_REVIEW answer per key package, checked by
                   Verified Ask before it counts (receipts recorded)
  7. fixes         each candidate fix (extra pins) gets its own fresh environment and steps 1 to 5
  8. decision      DEPLOY, DEPLOY WITH CONDITIONS or HOLD, with the evidence for each reason

Running an app executes its code: run this in a disposable sandbox.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify.core import verify  # noqa: E402
from verify.sources import LiveSources  # noqa: E402

OSV = "https://api.osv.dev/v1"
MODULE_TO_DIST = {"dateutil": "python-dateutil", "PIL": "pillow", "yaml": "pyyaml", "cv2": "opencv-python",
                  "bs4": "beautifulsoup4", "docx": "python-docx", "pptx": "python-pptx", "sklearn": "scikit-learn"}


def _ctx():
    c = ssl.create_default_context()
    if os.environ.get("SSL_CERT_FILE"):
        c.load_verify_locations(os.environ["SSL_CERT_FILE"])
    return c


def http_json(url: str, body: dict | None = None, timeout: int = 60, headers: dict | None = None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "adversarialeval-deploycheck/1.0",
                                          **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:
        return json.loads(r.read())


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout)


# ---------- 1-2: install, resolve, undeclared imports ----------
def make_env(where: Path, specs: list[str]) -> dict:
    if where.exists():
        shutil.rmtree(where)
    run([sys.executable, "-m", "venv", str(where)])
    pip = [str(where / "bin" / "python"), "-m", "pip", "install", "-q", "--disable-pip-version-check"]
    p = run(pip + specs)
    return {"python": str(where / "bin" / "python"), "pip": pip, "install_ok": p.returncode == 0,
            "install_log": (p.stdout + p.stderr)[-1500:]}


def freeze(env: dict) -> dict[str, str]:
    out = run([env["python"], "-m", "pip", "list", "--format=json", "--disable-pip-version-check"]).stdout
    return {x["name"].lower().replace("_", "-"): x["version"] for x in json.loads(out or "[]")
            if x["name"].lower() not in ("pip", "setuptools", "wheel")}


def undeclared_imports(env: dict, modules: list[str], max_rounds: int = 12) -> list[dict]:
    """Import the app's entry modules; install each missing module and record it."""
    found = []
    code = "import importlib,sys\nfor m in sys.argv[1:]: importlib.import_module(m)"
    for _ in range(max_rounds):
        p = run([env["python"], "-c", code, *modules], cwd=Path("/tmp"))
        m = re.search(r"No module named '([^'.]+)", p.stderr)
        if p.returncode == 0 or not m:
            break
        mod = m.group(1)
        dist = MODULE_TO_DIST.get(mod, mod)
        ok = run(env["pip"] + [dist]).returncode == 0
        found.append({"module": mod, "package": dist, "installable": ok})
        if not ok:
            break
    final = run([env["python"], "-c", code, *modules], cwd=Path("/tmp"))
    return found, final.returncode == 0, final.stderr.strip().splitlines()[-1:] if final.returncode else []


# ---------- 3: advisories ----------
def advisories(pkgs: dict[str, str]) -> dict[str, list[dict]]:
    names = sorted(pkgs)
    queries = [{"package": {"ecosystem": "PyPI", "name": n}, "version": pkgs[n]} for n in names]
    hits: dict[str, list[str]] = {}
    for i in range(0, len(queries), 500):
        res = http_json(f"{OSV}/querybatch", {"queries": queries[i:i + 500]})["results"]
        for n, r in zip(names[i:i + 500], res):
            if r.get("vulns"):
                hits[n] = [v["id"] for v in r["vulns"]]
    out = {}
    for n, ids in hits.items():
        recs = [http_json(f"{OSV}/vulns/{vid}") for vid in ids]
        out[n] = _dedupe(recs)
    return out


def _dedupe(recs: list[dict]) -> list[dict]:
    """One entry per vulnerability: GHSA preferred, aliases merged."""
    groups: list[dict] = []
    for r in sorted(recs, key=lambda x: (not x["id"].startswith("GHSA"), x["id"])):
        ids = {r["id"], *r.get("aliases", [])}
        if any(ids & g["ids"] for g in groups):
            next(g for g in groups if ids & g["ids"])["ids"] |= ids
            continue
        fixed = sorted({e["fixed"] for a in r.get("affected", []) for rg in a.get("ranges", []) for e in rg.get("events", []) if "fixed" in e})
        groups.append({"id": r["id"], "ids": ids, "summary": (r.get("summary") or r.get("details") or "")[:160],
                       "severity": (r.get("database_specific") or {}).get("severity"), "fixed": fixed})
    for g in groups:
        g["aliases"] = sorted(g.pop("ids") - {g["id"]})
    return groups


# ---------- 4: reachability ----------
def reachability(vulns: list[dict], rules: dict, source_dir: Path) -> list[dict]:
    files = [p for p in source_dir.rglob("*.py")]
    texts = {p: p.read_text(errors="ignore") for p in files}
    out = []
    for v in vulns:
        rule = next((rules[i] for i in [v["id"], *v["aliases"]] if i in rules), rules.get("_default"))
        if rule is None:
            out.append({**v, "reach": "unknown", "why": "no reviewed rule for this advisory", "evidence": []})
            continue
        ev = []
        for pat in rule.get("uses", []):
            rx = re.compile(pat)
            for p, t in texts.items():
                for i, line in enumerate(t.splitlines(), 1):
                    if rx.search(line):
                        ev.append(f"{p.relative_to(source_dir.parent)}:{i}: {line.strip()[:100]}")
        used = bool(ev)
        reach = ("conditional" if rule.get("condition") else "reachable") if used else "not used"
        out.append({**v, "reach": reach, "needs": rule["needs"], "condition": rule.get("condition"),
                    "why": rule["needs"] + (f"; only when {rule['condition']}" if used and rule.get("condition") else ""),
                    "evidence": ev[:4]})
    return out


# ---------- 5: smoke ----------
def smoke(env: dict, script: Path) -> dict:
    p = run([env["python"], str(script)], cwd=Path("/tmp"), timeout=600)
    line = (p.stdout.strip().splitlines() or ["{}"])[-1]
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {"ok": False, "error": (p.stderr or p.stdout)[-400:]}


# ---------- 6: telegraph ----------
def telegraph(targets: list[str], max_spend: float) -> list[dict]:
    """One paid SECURITY_REVIEW_GENERAL answer per target via Anjoman (key added by the session proxy,
    or $ANJOMAN_API_KEY), each checked by Verified Ask before it counts."""
    hdr = {"Authorization": f"Bearer {os.environ['ANJOMAN_API_KEY']}"} if os.environ.get("ANJOMAN_API_KEY") else {}
    src, out, spent = LiveSources(), [], 0.0
    for t in targets:
        if spent + 0.02 > max_spend + 1e-9:
            out.append({"target": t, "skipped": "spending cap"}); continue
        t0 = time.time()
        try:
            body = http_json("https://backend.telegraphprotocol.com/engine/ask",
                             {"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": t}}, timeout=120, headers=hdr)
            r = body.get("result") or {}
            ans, cost = r.get("result"), float(r.get("cost_usd_total") or r.get("cost_usd") or 0)
            rec = {"target": t, "miner": r.get("miner_name"), "answer": ans, "cost_usd": cost,
                   "receipt": (body.get("receipt") or {}).get("receipt_hash"), "seconds": round(time.time() - t0, 1)}
        except Exception as e:
            rec = {"target": t, "error": str(e)[:200], "cost_usd": 0, "seconds": round(time.time() - t0, 1)}
        spent += rec.get("cost_usd") or 0
        v = verify(t, rec.get("answer") if isinstance(rec.get("answer"), dict) else None, src)
        rec["verified_ask"] = {"label": v.label, "notes": [f"{c.status}: {c.detail}" for c in v.checks if c.status != "pass"][:4]}
        out.append(rec)
    return out


# ---------- 8: decision ----------
def decide(c: dict) -> tuple[str, list[str]]:
    reasons, hold, cond = [], False, False
    if not c["install_ok"]:
        hold = True; reasons.append("install failed")
    if not c["imports_ok"]:
        hold = True; reasons.append("the app does not import: " + "; ".join(c["import_error"])[:160])
    if c.get("undeclared"):
        hold = True; reasons.append("needs packages it doesn't declare: " + ", ".join(u["package"] for u in c["undeclared"]))
    if c["imports_ok"] and not c["smoke"].get("ok"):
        hold = True; reasons.append(f"the app fails its build-and-serve test: {c['smoke'].get('error', 'no result')[:160]}")
    if c.get("force"):
        cond = True; reasons.append("runs versions outside a library's declared range (" + ", ".join(c["force"]) + "): "
                                    + "; ".join(x for x in c.get("pip_check", []) if "has requirement" in x or "requires" in x)[:200])
    for pkg, vs in c["reach"].items():
        for v in vs:
            sev = (v.get("severity") or "unrated").upper()
            if v["reach"] in ("reachable", "unknown") and sev in ("HIGH", "CRITICAL"):
                hold = True; reasons.append(f"{pkg}: {v['id']} ({sev}) {v['reach']}")
            elif v["reach"] == "conditional":
                cond = True; reasons.append(f"{pkg}: {v['id']} ({sev}) only when {v['condition']}")
            elif v["reach"] in ("reachable", "unknown"):
                cond = True; reasons.append(f"{pkg}: {v['id']} ({sev}) {v['reach']}")
    return ("HOLD" if hold else "DEPLOY WITH CONDITIONS" if cond else "DEPLOY"), reasons


def import_check(env: dict, modules: list[str]) -> tuple[bool, list[str]]:
    code = "import importlib,sys\nfor m in sys.argv[1:]: importlib.import_module(m)"
    p = run([env["python"], "-c", code, *modules], cwd=Path("/tmp"))
    return p.returncode == 0, (p.stderr.strip().splitlines()[-1:] if p.returncode else [])


def check_candidate(cand: dict, scenario: dict, work: Path, probe_undeclared: bool = False) -> dict:
    """cand: {"name", "install": [specs], "overrides": [specs installed after, e.g. a newer pin]}"""
    env = make_env(work / re.sub(r"[^a-z0-9]+", "-", cand["name"].lower()).strip("-"), cand["install"])
    if env["install_ok"] and cand.get("overrides"):
        p = run(env["pip"] + cand["overrides"])
        env["install_ok"] = p.returncode == 0
        env["install_log"] += (p.stdout + p.stderr)[-800:]
    if env["install_ok"] and cand.get("force"):  # versions installed against a library's declared range (--no-deps)
        p = run(env["pip"] + ["--no-deps"] + cand["force"])
        env["install_ok"] = p.returncode == 0
        env["install_log"] += (p.stdout + p.stderr)[-800:]
    imports_ok, import_err = import_check(env, scenario["entry_modules"]) if env["install_ok"] else (False, ["install failed"])
    undeclared = []
    if probe_undeclared and not imports_ok:  # list them in a separate sandbox, leaving this one as installed
        probe = make_env(work / "probe-undeclared", cand["install"])
        undeclared, _, _ = undeclared_imports(probe, scenario["entry_modules"])
    pkgs = freeze(env)
    vulns = advisories(pkgs)
    loc = run([env["python"], "-c", f"import importlib.util,os;s=importlib.util.find_spec('{scenario['source_module']}');print(os.path.dirname(s.origin) if s else '')"]).stdout.strip()
    rules = json.loads((ROOT / scenario["reach_rules"]).read_text()) if scenario.get("reach_rules") else {}
    reach = {p: reachability(vs, rules.get(p, {}), Path(loc)) for p, vs in vulns.items()} if loc else {}
    sm = smoke(env, ROOT / scenario["smoke"]) if imports_ok else {"ok": False, "error": "not run: the app does not import"}
    broken = run([env["python"], "-m", "pip", "check", "--disable-pip-version-check"]).stdout.strip().splitlines()
    c = {"name": cand["name"], "install": cand["install"], "overrides": cand.get("overrides", []), "force": cand.get("force", []),
         "pip_check": broken, "install_log": env["install_log"][-600:] if not env["install_ok"] else "", "install_ok": env["install_ok"],
         "packages": len(pkgs), "key_versions": {k: pkgs.get(k) for k in scenario.get("key_packages", [])},
         "imports_ok": imports_ok, "import_error": import_err, "undeclared": undeclared, "smoke": sm, "reach": reach,
         "advisories": sum(len(v) for v in vulns.values())}
    c["decision"], c["reasons"] = decide(c)
    return c
