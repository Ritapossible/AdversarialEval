"""Run a deploycheck scenario and write report.json and report.md.

    SSL_CERT_FILE=... python -m deploycheck deploycheck/scenarios/qwen_agent.json --out bench/out/deploycheck-qwen-agent \
        [--work /tmp/deploycheck] [--telegraph --max-spend 0.10]
"""
import argparse
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

from .core import ISOLATION, ROOT, check_candidate, telegraph
from .report import markdown


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--work", type=Path, default=Path("/tmp/deploycheck"))
    ap.add_argument("--keep-work", action="store_true", help="keep the installed environments (about 4 GB) after the run")
    ap.add_argument("--telegraph", action="store_true", help="buy one SECURITY_REVIEW answer per telegraph_targets entry")
    ap.add_argument("--max-spend", type=float, default=0.10)
    ap.add_argument("--reuse-telegraph", type=Path, help="reuse the paid answers in an earlier report.json instead of buying again")
    a = ap.parse_args()
    sc = json.loads(a.scenario.read_text())
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    cands = []
    for c in sc["candidates"]:
        print(f"checking: {c['name']}", flush=True)
        r = check_candidate(c, sc, a.work, probe_undeclared=c.get("probe_undeclared", False))
        print(f"  -> {r['decision']}: {'; '.join(r['reasons'])[:200]}", flush=True)
        cands.append(r)
    if a.reuse_telegraph:
        tg = json.loads(a.reuse_telegraph.read_text())["telegraph"]
    else:
        tg = telegraph(sc.get("telegraph_targets", []), a.max_spend) if a.telegraph else []
    rep = {"scenario": sc["name"], "why": sc.get("why"), "started": started,
           "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "repo_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
           "isolation": ISOLATION, "candidates": cands, "telegraph": tg}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report.json").write_text(json.dumps(rep, indent=1, default=list) + "\n")
    (a.out / "report.md").write_text(markdown(rep))
    print(f"wrote {a.out}/report.json and report.md")
    if not a.keep_work:  # each candidate's environment is a full install; don't leave gigabytes behind
        shutil.rmtree(a.work, ignore_errors=True)


if __name__ == "__main__":
    main()
