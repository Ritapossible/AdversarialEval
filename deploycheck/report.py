"""Readable report for a deploycheck run."""
from __future__ import annotations


def markdown(rep: dict) -> str:
    L = [f"# Pre-deployment check: {rep['scenario']}", "",
         f"{rep.get('why') or ''}", "",
         f"Run {rep['started']} to {rep['finished']} UTC at commit `{rep['repo_commit'][:7]}`. Every finding below comes "
         "from installing and running the app, OSV, the package registry, or a reviewed rule matched against the app's "
         "own source; none comes from a model's opinion.", "",
         "## Decision per candidate", "",
         "| Candidate | Decision | Imports | Serves (smoke) | Advisories (distinct) | Reachable or conditional |", "|---|---|---|---|---|---|"]
    for c in rep["candidates"]:
        live = sum(1 for vs in c["reach"].values() for v in vs if v["reach"] in ("reachable", "conditional", "unknown"))
        L.append(f"| {c['name']} | **{c['decision']}** | {'yes' if c['imports_ok'] else 'no'} | "
                 f"{'yes' if c['smoke'].get('ok') else 'no'} | {c['advisories']} | {live} |")
    for c in rep["candidates"]:
        L += ["", f"## {c['name']}", "", f"Install: `{' '.join(c['install'])}`" +
              (f", then `{' '.join(c['overrides'])}`" if c["overrides"] else "") +
              (f", then forced without dependency checks: `{' '.join(c['force'])}`" if c.get("force") else "") +
              f"; {c['packages']} packages resolved." + ("" if c["install_ok"] else " **Install failed.**"), ""]
        if c.get("pip_check") and c["pip_check"] != ["No broken requirements found."]:
            L += ["Declared-version conflicts left in this environment (`pip check`): " + "; ".join(f"`{x}`" for x in c["pip_check"][:4]), ""]
        kv = ", ".join(f"{k} {v}" for k, v in c["key_versions"].items() if v)
        L.append(f"Key versions: {kv}." if kv else "")
        if c["undeclared"]:
            L += ["", "Undeclared dependencies (imported by the app at load time, not declared by its package): " +
                  ", ".join(f"`{u['package']}`" for u in c["undeclared"]) + "."]
        if not c["imports_ok"]:
            L.append(f"\nImport fails: `{'; '.join(c['import_error'])}`")
        sm = c["smoke"]
        L.append(f"\nSmoke test: {'passed, served ' + str(sm.get('components')) + ' components over HTTP ' + str(sm.get('http')) if sm.get('ok') else 'failed: ' + str(sm.get('error'))[:240]}")
        for pkg, vs in c["reach"].items():
            if not vs:
                continue
            L += ["", f"| {pkg} advisory | Severity | Fixed in | Needs | Used by the app? | Evidence |", "|---|---|---|---|---|---|"]
            for v in vs:
                ev = "<br>".join(f"`{e}`" for e in v.get("evidence", [])[:2]) or "no match in the app's source"
                L.append(f"| [{v['id']}](https://osv.dev/vulnerability/{v['id']}) | {v.get('severity') or 'unrated'} | "
                         f"{', '.join(v.get('fixed') or []) or 'no fix listed'} | {v.get('needs') or v.get('why')} | "
                         f"**{v['reach']}**{' (' + v['condition'] + ')' if v.get('condition') and v['reach'] == 'conditional' else ''} | {ev} |")
        L += ["", "Reasons: " + ("; ".join(c["reasons"]) or "none") + "."]
    if rep.get("telegraph"):
        L += ["", "## Telegraph specialist answers (paid, checked before use)", "",
              "| Package | Miner | Answer | Verified Ask | Cost | Receipt |", "|---|---|---|---|---|---|"]
        for t in rep["telegraph"]:
            ans = t.get("answer") if isinstance(t.get("answer"), dict) else {}
            L.append(f"| `{t['target']}` | {t.get('miner') or t.get('error') or t.get('skipped')} | "
                     f"{ans.get('verdict')}, count {ans.get('vulnerability_count')} | {t['verified_ask']['label'] if 'verified_ask' in t else ''} | "
                     f"${t.get('cost_usd', 0):.2f} | `{(t.get('receipt') or '')[:18]}` |")
    return "\n".join(L) + "\n"
