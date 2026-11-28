#!/usr/bin/env python3
"""Arm C's deterministic checks and the truth for every generated change (codeverify/RULE.md).

    python codeverify/checks.py --out bench/out/codeverify [--fixes]

Writes <out>/checks.jsonl (one row per change): registry, OSV, install, undeclared imports, import,
visible tests, Bandit, and (truth only) hidden tests. Nothing here asks a model. Needs uv and a
Python 3.12 interpreter (PY312, default /usr/bin/python3.12).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from deploycheck.core import MODULE_TO_DIST, advisories, http_json  # noqa: E402

PY312 = os.environ.get("PY312", "/usr/bin/python3.12")
MODULE_TO_DIST = {**MODULE_TO_DIST, "jwt": "pyjwt", "jose": "python-jose", "Crypto": "pycryptodome",
                  "dotenv": "python-dotenv", "magic": "python-magic"}
SEV = {"MEDIUM", "HIGH"}
TEST_TIMEOUT = 120
INSTALLS: dict[str, tuple[bool, str, str]] = {}  # requirements hash -> (installed, log, last error line)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(==\s*([^\s;,]+))?", line)
        if m:
            out.append({"line": line, "name": norm(m.group(1)), "version": m.group(4), "pinned": bool(m.group(4))})
        else:
            out.append({"line": line, "name": None, "version": None, "pinned": False})
    return out


class RegistryUnavailable(RuntimeError):
    """PyPI could not be reached or kept failing: the change is not checked, rather than held."""


def pypi_info(url: str, tries: int = 4, wait: float = 2.0) -> dict | None:
    """PyPI JSON for a project or release, None if it doesn't exist (HTTP 404 only). Rate limits and
    server errors are retried with backoff; if PyPI stays unavailable, RegistryUnavailable is raised."""
    last = ""
    for attempt in range(tries):
        try:
            return http_json(url, timeout=60).get("info") or {}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = f"HTTP {e.code}"
            if e.code not in (429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = str(e)[:120]
        if attempt < tries - 1:
            time.sleep(wait * 2 ** attempt)
    raise RegistryUnavailable(f"PyPI unavailable for {url}: {last}")


def registry(reqs: list[dict]) -> list[str]:
    """Check 1: every dependency exists on PyPI (at its pinned version) and isn't yanked."""
    problems = []
    for r in reqs:
        if not r["name"]:
            problems.append(f"unparseable requirement `{r['line']}`")
            continue
        url = f"https://pypi.org/pypi/{r['name']}/{r['version']}/json" if r["pinned"] else f"https://pypi.org/pypi/{r['name']}/json"
        info = pypi_info(url)
        if info is None:
            problems.append(f"`{r['line']}` not found on PyPI (HTTP 404)")
            continue
        if r["pinned"] and info.get("yanked"):
            problems.append(f"`{r['line']}` is yanked on PyPI: {info.get('yanked_reason') or 'no reason given'}")
    return problems


def third_party_imports(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            mods.add(n.module.split(".")[0])
    return sorted(m for m in mods if m not in sys.stdlib_module_names and m != "solution")


def sh(cmd: list[str], cwd: Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(cmd, 124, e.stdout or "", f"timed out after {timeout}s")


# Code written by a model runs with no network, as the unprivileged `nobody` user (so it can't read
# keys or write outside its temp folder), and under memory, CPU, file-size and open-file limits.
ISOLATE = ["unshare", "-n", "--", "setpriv", "--reuid=65534", "--regid=65534", "--clear-groups", "--",
           "prlimit", "--as=4000000000", "--cpu=300", "--fsize=104857600", "--nofile=512", "--"]


CA_DIR = Path("/tmp/codeverify-ca")


def _readable_ca() -> list[str]:
    """Code may build an HTTPS context at import time; give it a readable copy of the host's CA bundle
    (public certificates) so it fails for real reasons, not for a permission on root's files."""
    env = []
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        src = os.environ.get(var)
        if src and Path(src).is_file():
            CA_DIR.mkdir(exist_ok=True)
            CA_DIR.chmod(0o755)
            dst = CA_DIR / f"{var.lower()}.pem"
            shutil.copyfile(src, dst)
            dst.chmod(0o644)
            env.append(f"{var}={dst}")
    return ["env", "HOME=/tmp", *env]


ISOLATE = ISOLATE + _readable_ca()


def isolation_available() -> bool:
    try:
        return subprocess.run(ISOLATE + ["true"], capture_output=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


ISOLATED = isolation_available()


def run_untrusted(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    """Run model-written code isolated when the host allows it; the result row records which."""
    return sh((ISOLATE + cmd) if ISOLATED else cmd, cwd=cwd, timeout=timeout)


def scratch_dir(prefix: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=prefix, dir="/tmp"))
    d.chmod(0o755)  # readable by the unprivileged user; only root can write here
    return d


def pytest(env_py: str, work: Path, test_file: Path) -> dict:
    d = scratch_dir("cv-test-")
    try:
        shutil.copy(work / "solution.py", d / "solution.py")
        shutil.copy(test_file, d / "test_it.py")
        p = run_untrusted([env_py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_it.py"], cwd=d, timeout=TEST_TIMEOUT)
        lines = (p.stdout + p.stderr).strip().splitlines()
        failed = [l.split(" - ")[0].replace("FAILED ", "").replace("ERROR ", "") for l in lines if l.startswith(("FAILED", "ERROR"))]
        return {"ok": p.returncode == 0, "summary": lines[-1] if lines else "", "failed": failed[:10]}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def bandit(tools_py: str, work: Path) -> list[dict]:
    p = sh([tools_py, "-m", "bandit", "-q", "-f", "json", str(work / "solution.py")], timeout=120)
    try:
        res = json.loads(p.stdout).get("results", [])
    except json.JSONDecodeError:
        return [{"test_id": "bandit-error", "issue_text": (p.stderr or p.stdout)[-200:], "issue_severity": "HIGH",
                 "issue_confidence": "HIGH", "line_number": 0}]
    return [{k: r[k] for k in ("test_id", "issue_text", "issue_severity", "issue_confidence", "line_number")} for r in res]


def check_change(work: Path, venvs: Path, tools_py: str, hidden: Path, visible: Path) -> dict:
    req_text = (work / "requirements.txt").read_text() if (work / "requirements.txt").exists() else ""
    reqs = parse_requirements(req_text)
    has_solution = (work / "solution.py").exists()
    r = {"requirements": [x["line"] for x in reqs], "has_solution": has_solution,
         "isolation": "no network, user nobody, resource limits" if ISOLATED else "none (unshare/setpriv unavailable)"}
    reasons: list[str] = []

    r["registry"] = registry(reqs)
    reasons += r["registry"]

    pins = {x["name"]: x["version"] for x in reqs if x["name"] and x["pinned"]}
    adv = advisories(pins) if pins else {}
    r["osv"] = {n: [{"id": v["id"], "severity": v.get("severity"), "fixed": v.get("fixed")} for v in vs] for n, vs in adv.items()}
    for n, vs in r["osv"].items():
        reasons.append(f"{n}=={pins[n]} has {len(vs)} OSV advisories ({', '.join(v['id'] for v in vs[:3])}{'…' if len(vs) > 3 else ''})")

    # One environment per distinct requirements set, shared by the changes that declare it. Safe to
    # share: model-written code runs as `nobody` and can't modify a root-owned environment.
    specs = [x["line"] for x in reqs if x["name"]]
    key = hashlib.sha256("\n".join(sorted(specs)).encode()).hexdigest()[:16]
    env = venvs / f"env-{key}"
    py = str(env / "bin" / "python")
    if key not in INSTALLS:
        if env.exists():
            shutil.rmtree(env)
        sh(["uv", "venv", "-q", "-p", PY312, str(env)])
        p = sh(["uv", "pip", "install", "-q", "-p", py, "pytest==8.3.5", *specs], timeout=900)
        INSTALLS[key] = (p.returncode == 0, (p.stdout + p.stderr)[-800:], (p.stderr.strip().splitlines() or ["?"])[-1][:200])
    ok, log, last = INSTALLS[key]
    r["install_ok"] = ok
    if not ok:
        r["install_log"] = log
        reasons.append("requirements don't install in a fresh Python 3.12 environment: " + last)

    if not has_solution:
        reasons.append("no solution.py was produced")
        r.update(undeclared=[], import_ok=False, visible=None, hidden=None, bandit=[])
    else:
        code = (work / "solution.py").read_text()
        declared = {x["name"] for x in reqs if x["name"]}
        r["undeclared"] = [m for m in third_party_imports(code) if norm(MODULE_TO_DIST.get(m, m)) not in declared]
        for m in r["undeclared"]:
            reasons.append(f"solution.py imports `{m}` but requirements.txt doesn't declare it")
        if r["install_ok"]:
            d = scratch_dir("cv-imp-")
            shutil.copy(work / "solution.py", d / "solution.py")
            ip = run_untrusted([py, "-c", "import solution"], cwd=d, timeout=60)
            shutil.rmtree(d, ignore_errors=True)
            r["import_ok"] = ip.returncode == 0
            if not r["import_ok"]:
                r["import_error"] = (ip.stderr.strip().splitlines() or ["?"])[-1][:300]
                reasons.append(f"solution.py doesn't import: {r['import_error']}")
            r["visible"] = pytest(py, work, visible)
            r["hidden"] = pytest(py, work, hidden)
        else:
            r.update(import_ok=False, visible={"ok": False, "summary": "not run (install failed)", "failed": []},
                     hidden={"ok": False, "summary": "not run (install failed)", "failed": []})
        if r["visible"] and not r["visible"]["ok"] and r["install_ok"]:
            reasons.append("visible tests fail: " + (", ".join(r["visible"]["failed"][:3]) or r["visible"]["summary"]))
        r["bandit"] = bandit(tools_py, work)
    flagged = [b for b in r["bandit"] if b["issue_severity"] in SEV and b["issue_confidence"] in SEV]
    for b in flagged:
        reasons.append(f"Bandit {b['test_id']} (severity {b['issue_severity']}) line {b['line_number']}: {b['issue_text']}")

    # Arm C's deterministic part (check 8, verified Telegraph answers, is added by score.py)
    r["c_reasons"] = reasons
    r["c_decision"] = "HOLD" if reasons else "DEPLOY"
    # Truth: no solution, checks 1-5, or any visible or hidden test failing
    truth_fail = []
    if not has_solution:
        truth_fail.append("no solution")
    truth_fail += r["registry"] + [f"OSV advisory for {n}" for n in r["osv"]]
    if not r["install_ok"]:
        truth_fail.append("install failed")
    truth_fail += [f"undeclared import {m}" for m in r.get("undeclared", [])]
    if has_solution and not r["import_ok"]:
        truth_fail.append("import failed")
    for k in ("visible", "hidden"):
        if has_solution and r[k] and not r[k]["ok"]:
            truth_fail.append(f"{k} tests: " + (", ".join(r[k]["failed"][:4]) or r[k]["summary"]))
    r["truth"] = "HOLD" if truth_fail else "DEPLOY"
    r["truth_reasons"] = truth_fail
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "bench/out/codeverify")
    ap.add_argument("--fixes", action="store_true", help="check the fix round instead of the original changes")
    a = ap.parse_args()
    out = a.out.resolve()
    src, dst = (out / "fixes", out / "fix_checks.jsonl") if a.fixes else (out / "changes", out / "checks.jsonl")
    have = {(x["task"], x["seed"]) for x in map(json.loads, dst.read_text().splitlines())} if dst.exists() else set()
    work_root = scratch_dir("cv-envs-")
    tools = work_root / "tools"
    sh(["uv", "venv", "-q", "-p", PY312, str(tools)])
    sh(["uv", "pip", "install", "-q", "-p", str(tools / "bin/python"), "bandit==1.8.3"])
    bver = sh([str(tools / "bin/python"), "-m", "bandit", "--version"]).stdout.split("\n")[0]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    for tdir in sorted(p for p in src.iterdir() if p.is_dir()):
        for sdir in sorted(p for p in tdir.iterdir() if p.is_dir()):
            seed = int(sdir.name[1:])
            if (tdir.name, seed) in have:
                continue
            try:
                res = check_change(sdir, work_root, str(tools / "bin/python"), HERE / "tests" / f"{tdir.name}_hidden.py",
                                   HERE / "tests" / f"{tdir.name}_visible.py")
            except RegistryUnavailable as e:  # not recorded, so a re-run checks it again
                print(f"{tdir.name} s{seed}: SKIPPED, {e}", flush=True)
                continue
            row = {"task": tdir.name, "seed": seed, "at": now(), "repo_commit": commit, "bandit_version": bver, **res}
            with dst.open("a") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"{tdir.name} s{seed}: C={res['c_decision']} truth={res['truth']}  {'; '.join(res['truth_reasons'])[:140]}", flush=True)
    shutil.rmtree(work_root, ignore_errors=True)


if __name__ == "__main__":
    main()
