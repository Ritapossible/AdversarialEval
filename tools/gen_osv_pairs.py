#!/usr/bin/env python3
"""Generate label-verified minimal pairs from OSV advisories (audit item U5).

Every label is computed, not written: an advisory's affected ranges (OSV, including
backport ranges) are evaluated against REAL released versions from PyPI / npm. The chosen
and rejected answers come from the same template and phrasing variant and differ only in
the decisive fact, so a judge can't separate them by style (minimal pairs).

Families produced:
  F2-in   version inside an affected range; rejected claims it is already patched
  F2-out  version at/after the fix; rejected claims it is still affected
  F1      rejected cites a real advisory id from a different package (misattribution)
  F7      rejected states the right facts but contradictory verdict / count fields
  F8      rejected downgrades a HIGH/CRITICAL advisory to low priority
Half of the F2 prompts quote the advisory's affected range ("evidence in prompt", U7), which
turns a knowledge question into an in-context version comparison a text model can learn.

Claims are scoped to the one advisory asked about; nothing says "no known vulnerabilities".
Packages that appear in validation or test cases are excluded so nothing leaks across splits.
Advisories whose OSV records disagree (see tools/verify_generated.py) are skipped.

    python tools/gen_osv_pairs.py [--max-pairs 240] [--per-package 6] [--seed 7] [--offline]

Writes data/authoring/security_review/g_osv_generated.jsonl and data/sources/ids_generated.txt
(caches: data/sources/osv/, data/sources/osv_query/, data/sources/registry/).
"""
from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ADVISORY_ID, ROOT, normalise, read_jsonl  # noqa: E402

SRC = ROOT / "data" / "sources"
OUT = ROOT / "data" / "authoring" / "security_review" / "g_osv_generated.jsonl"
IDS_OUT = SRC / "ids_generated.txt"
GENERATOR = "generator:osv-v1"

PACKAGES = {
    "PyPI": ["django", "flask", "requests", "urllib3", "jinja2", "pillow", "pyyaml", "werkzeug",
             "cryptography", "aiohttp", "tornado", "sqlalchemy", "lxml", "paramiko", "twisted",
             "gunicorn", "pyjwt", "markdown", "bleach", "mistune", "fastapi", "starlette",
             "python-multipart", "jupyter-server", "mlflow", "gradio", "transformers", "scrapy"],
    "npm": ["lodash", "express", "minimist", "ws", "node-fetch", "semver", "tar", "moment",
            "handlebars", "marked", "ejs", "undici", "socket.io", "body-parser", "path-to-regexp",
            "cookie", "send", "dompurify", "sanitize-html", "xml2js", "shell-quote", "glob-parent",
            "ansi-regex", "jquery", "underscore", "next", "vite", "webpack-dev-middleware"],
}
# Held-out packages for the generated validation set: disjoint from PACKAGES, so a model
# can't pass by memorising training advisories (audit follow-up, 2026-11-11).
PACKAGES_HOLDOUT = {
    "PyPI": ["tensorflow", "keras", "babel", "waitress", "streamlit", "langchain", "llama-index",
             "bentoml", "onnx", "sentry-sdk", "vyper", "nltk", "rsa", "ecdsa", "pycryptodome"],
    "npm": ["angular", "vue", "electron", "mongoose", "sequelize", "passport", "koa", "fastify",
            "multer", "formidable", "pug", "nunjucks", "highlight.js", "js-yaml", "fast-xml-parser"],
}
CONTEXTS = [
    "in a public REST API", "in an internal reporting job", "in our CI build image",
    "on a customer-facing web app", "in a data pipeline worker", "in a mobile backend",
    "in an admin dashboard", "in a webhook receiver", "inside a Docker image we ship to customers",
    "in a serverless function", "on a partner integration gateway", "in a CLI our support team runs",
]


# ---------------------------------------------------------------------------
# fetching with caches
# ---------------------------------------------------------------------------
def _get_json(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers=headers or {}, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def osv_query(eco, name, offline):
    cache = SRC / "osv_query" / f"{eco}-{name}.json"
    if cache.exists():
        ids = json.loads(cache.read_text())
    else:
        if offline:
            return []
        ids, token = [], None
        while True:
            body = {"package": {"name": name, "ecosystem": eco}}
            if token:
                body["page_token"] = token
            d = _get_json("https://api.osv.dev/v1/query", body)
            for v in d.get("vulns", []):
                (SRC / "osv_raw").mkdir(parents=True, exist_ok=True)
                p = SRC / "osv_raw" / f"{v['id']}.json"
                if not p.exists():
                    p.write_text(json.dumps(v, indent=1, sort_keys=True) + "\n")
                ids.append(v["id"])
            token = d.get("next_page_token")
            if not token:
                break
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(sorted(ids)) + "\n")
    out = []
    for i in ids:
        for d in ("osv", "osv_raw"):
            p = SRC / d / f"{i}.json"
            if p.exists():
                out.append(json.loads(p.read_text()))
                break
    return out


def registry_versions(eco, name, offline):
    cache = SRC / "registry" / f"{eco}-{name}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    if offline:
        return []
    if eco == "PyPI":
        vs = list(_get_json(f"https://pypi.org/pypi/{name}/json")["releases"])
    else:
        vs = list(_get_json(f"https://registry.npmjs.org/{name}",
                            headers={"Accept": "application/vnd.npm.install-v1+json"})["versions"])
    vs = [v for v in vs if parse(eco, v) is not None]
    vs.sort(key=lambda v: parse(eco, v))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(vs) + "\n")
    return vs


# ---------------------------------------------------------------------------
# versions and ranges
# ---------------------------------------------------------------------------
_NPM = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse(eco, v):
    """A comparable key for a STABLE release, or None (pre-releases are skipped)."""
    if eco == "npm":
        m = _NPM.match(v)
        return tuple(int(x) for x in m.groups()) if m else None
    from packaging.version import InvalidVersion, Version
    try:
        pv = Version(v)
    except InvalidVersion:
        return None
    return None if (pv.is_prerelease or pv.is_devrelease) else pv


def ranges_for(rec, eco, name):
    out = []
    for a in rec.get("affected", []):
        p = a.get("package", {})
        if p.get("ecosystem") != eco or p.get("name", "").lower() != name.lower():
            continue
        for rg in a.get("ranges", []):
            if rg.get("type") != "ECOSYSTEM":
                continue
            cur = None
            for ev in rg.get("events", []):
                if "introduced" in ev:
                    cur = {"introduced": ev["introduced"]}
                elif "fixed" in ev and cur is not None:
                    cur["fixed"] = ev["fixed"]
                    out.append(cur)
                    cur = None
                elif "last_affected" in ev and cur is not None:
                    return None  # keep it simple: only advisories with explicit fixes
            if cur is not None:
                return None  # open-ended (unfixed) range
    return out or None


def make_affected(eco, ranges):
    keyed = []
    for r in ranges:
        lo = None if r["introduced"] == "0" else parse(eco, r["introduced"])
        hi = parse(eco, r["fixed"])
        if hi is None or (r["introduced"] != "0" and lo is None):
            return None
        keyed.append((lo, hi, r))

    def affected(v):
        k = parse(eco, v)
        return any((lo is None or lo <= k) and k < hi for lo, hi, _ in keyed)

    def range_of(v):
        k = parse(eco, v)
        for lo, hi, r in keyed:
            if (lo is None or lo <= k) and k < hi:
                return r
        return None
    return affected, range_of


def ghsa_of(rec):
    if rec["id"].startswith("GHSA-"):
        return rec["id"]
    return next((a for a in rec.get("aliases", []) if a.startswith("GHSA-")), None)


def range_text(r):
    return (f"before {r['fixed']}" if r["introduced"] == "0"
            else f"{r['introduced']} up to but not including {r['fixed']}")


# ---------------------------------------------------------------------------
# rendering: one template + phrasing variant per pair, shared by chosen and rejected
# ---------------------------------------------------------------------------
def verdict_for(sev, affected):
    if not affected:
        return "Secure"
    return "Insecure" if sev in ("HIGH", "CRITICAL") else "Needs changes"


def render_answer(fmt, verdict, count, issues, sentences):
    body = " ".join(sentences)
    if fmt == "json":
        return json.dumps({"verdict": verdict, "vulnerability_count": count, "issues": issues,
                           "summary": body}, ensure_ascii=False)
    if fmt == "bullets":
        lines = [f"- Verdict: {verdict}", f"- vulnerability_count: {count}"]
        if issues:
            lines.append("- Issues: " + "; ".join(issues))
        return "\n".join(lines + [f"- {s}" for s in sentences])
    if fmt == "terse":
        head = f"VERDICT={verdict} COUNT={count}"
        return head + ("\n" + "; ".join(issues) if issues else "") + "\n" + body.lower()
    return f"Verdict: {verdict}. vulnerability_count: {count}. " + (
        ("Issues: " + "; ".join(issues) + ". ") if issues else "") + body


def prompt_for(kind, rng, pkg, v, gid, cve, summary, eco, r_ev, ctx):
    ref = f"{gid}" + (f" ({cve})" if cve and rng.random() < 0.5 else "")
    mgr = "requirements.txt" if eco == "PyPI" else "package-lock.json"
    pin = f"{pkg}=={v}" if eco == "PyPI" else f"{pkg}@{v}"
    evidence = ""
    if r_ev:
        evidence = " " + rng.choice([
            f"The advisory text says versions {range_text(r_ev)} are affected.",
            f"Per the GHSA page, affected versions: {range_text(r_ev)}.",
            f"(Scanner detail: vulnerable range is {range_text(r_ev)}.)",
            f"Advisory excerpt: \"affects {pkg} {range_text(r_ev)}\".",
            f"The vendor lists {range_text(r_ev)} as vulnerable.",
        ])
    if kind == "F1":
        opts = [f"For our audit ticket: which GitHub advisory covers \"{summary}\" in {pkg}? We run {pin} {ctx}.",
                f"Need the advisory id for the {pkg} issue \"{summary}\" (we pin {pin} {ctx}). Which GHSA is it, and what's the fix version?",
                f"Compliance wants the exact GHSA id for {pkg}: \"{summary}\". Our {mgr} has {pin}; the service runs {ctx}."]
    elif kind == "F8":
        opts = [f"Risk register entry: {pin} {ctx} is flagged by {ref} (\"{summary}\"). What priority should it get?",
                f"How serious is {ref} for {pin} {ctx}? Advisory title: \"{summary}\". We need a severity for the weekly report.",
                f"Triage {ref} (\"{summary}\") against {pin}, deployed {ctx}. Severity and priority please."]
    else:
        opts = [f"Dependabot raised {ref} (\"{summary}\") on {pin} {ctx}.{evidence} Is the alert valid?",
                f"Our scanner flags {pin} {ctx} for {ref}: \"{summary}\".{evidence} True positive or not?",
                f"Do we need to patch {pkg} for {ref}? {mgr} pins {pin}, used {ctx}.{evidence}",
                f"Security check before release: {pin} {ctx}. Is it affected by {ref} (\"{summary}\")?{evidence}"]
    return rng.choice(opts)


def build_pair(kind, rng, ctx_facts):
    f = ctx_facts
    fmt = rng.choice(["prose", "prose", "bullets", "json", "terse"])
    var = rng.randrange(3)
    issue = f"{f['gid']}" + (f" / {f['cve']}" if f["cve"] else "") + f" ({f['sev'].lower()})"

    def affected_sents(v, r):
        return [[f"{f['pkg']} {v} is inside the affected range ({range_text(r)}), so this applies.",
                 f"Upgrade to {r['fixed']} or later."],
                [f"The advisory affects {f['pkg']} {range_text(r)}; {v} falls in that range.",
                 f"The first fixed release on this line is {r['fixed']}."],
                [f"Affected: {v} is below the fix ({r['fixed']}) and at or above where the bug was introduced.",
                 f"Move to {f['pkg']} {r['fixed']}+."]][var]

    def patched_sents(v, fixed_claim):
        return [[f"{f['pkg']} {v} is not in the affected range; the fix shipped in {fixed_claim}.",
                 f"This alert does not apply to {v}."],
                [f"The issue was fixed in {fixed_claim}, and {v} is at or after that release.",
                 "Dismiss this alert as not applicable."],
                [f"Not affected: {v} already contains the fix from {fixed_claim}.",
                 "No upgrade is needed for this advisory."]][var]

    if kind == "F2-in":
        v, r, wrong = f["v_in"], f["r_in"], f["wrong_fix_le"]
        vc = verdict_for(f["sev"], True)
        chosen = render_answer(fmt, vc, 1, [issue], affected_sents(v, r))
        rejected = render_answer(fmt, "Secure", 0, [], patched_sents(v, wrong))
        return fmt, f["v_in"], chosen, rejected, vc, "Secure", f"claims {v} is patched (fix '{wrong}'); real fix {r['fixed']}"
    if kind == "F2-out":
        v, r, wrong = f["v_out"], f["r_fixed"], f["wrong_fix_gt"]
        wrong_r = {"introduced": r["introduced"], "fixed": wrong}
        vr = verdict_for(f["sev"], True)
        chosen = render_answer(fmt, "Secure", 0, [], patched_sents(v, r["fixed"]))
        rejected = render_answer(fmt, vr, 1, [issue], affected_sents(v, wrong_r))
        return fmt, v, chosen, rejected, "Secure", vr, f"claims {v} is still affected (fix '{wrong}'); real fix {r['fixed']}"
    if kind == "F7":
        v, r = f["v_in"], f["r_in"]
        vc = verdict_for(f["sev"], True)
        chosen = render_answer(fmt, vc, 1, [issue], affected_sents(v, r))
        bad_v, bad_c = rng.choice([("Secure", 1), (vc, 0), ("Secure", 0)])
        rejected = render_answer(fmt, bad_v, bad_c, [issue], affected_sents(v, r))
        return fmt, v, chosen, rejected, vc, bad_v, f"same facts but fields contradict (verdict {bad_v}, count {bad_c})"
    if kind == "F8":
        v, r = f["v_in"], f["r_in"]
        vc = verdict_for(f["sev"], True)
        sev_words = {"CRITICAL": "critical", "HIGH": "high"}[f["sev"]]
        s_ok = [f"Severity: {sev_words} per the advisory; treat as a priority fix.", *affected_sents(v, r)]
        s_bad = ["Severity: low; schedule it with routine maintenance.", *affected_sents(v, r)]
        issue_low = issue.replace(f"({f['sev'].lower()})", "(low)")
        chosen = render_answer(fmt, vc, 1, [issue], s_ok)
        rejected = render_answer(fmt, "Needs changes", 1, [issue_low], s_bad)
        return fmt, v, chosen, rejected, vc, "Needs changes", f"downgrades a {sev_words} advisory to low"
    if kind == "F1":
        v, r, other = f["v_in"], f["r_in"], f["distractor"]
        vc = verdict_for(f["sev"], True)
        # symmetric with the chosen issue: the distractor's own GHSA (and its own CVE, when it has one)
        wrong_issue = f"{other['gid']}" + (f" / {other['cve']}" if other["cve"] else "") + f" ({f['sev'].lower()})"
        chosen = render_answer(fmt, vc, 1, [issue], affected_sents(v, r))
        rejected = render_answer(fmt, vc, 1, [wrong_issue], affected_sents(v, r))
        return fmt, v, chosen, rejected, vc, vc, f"cites {other['gid']} ({other['pkg']}), a real advisory for a different package"
    raise ValueError(kind)


# ---------------------------------------------------------------------------
def shingles(s, k=5):
    s = s.lower()
    return {s[i:i + k] for i in range(max(1, len(s) - k + 1))}


def too_similar(t, sh, pool, threshold=0.80, exhaustive=False):
    """Jaccard of 5-gram shingles, then difflib's ratio (dedup.py uses the max of both).
    Templated prompts can share structure with little word overlap, so `exhaustive` always
    runs difflib (used for held-out generation, where cross-split similarity is an error)."""
    for t2, sh2 in pool:
        jac = len(sh & sh2) / max(1, len(sh | sh2))
        if jac >= threshold:
            return True
        if (exhaustive or jac > 0.40) and difflib.SequenceMatcher(None, t, t2, autojunk=False).ratio() >= threshold:
            return True
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pairs", type=int, default=240)
    ap.add_argument("--per-package", type=int, default=6)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--split", choices=["public", "validation"], default="public",
                    help="validation = held-out minimal pairs from PACKAGES_HOLDOUT")
    a = ap.parse_args(argv)
    holdout = a.split == "validation"
    packages = PACKAGES_HOLDOUT if holdout else PACKAGES
    out_path = OUT.with_name("g_osv_generated_val.jsonl") if holdout else OUT
    ids_out = IDS_OUT.with_name("ids_generated_val.txt") if holdout else IDS_OUT
    # cross-split prompts must stay below dedup.py's 0.70 cross-split error threshold
    sim_threshold = 0.66 if holdout else 0.80
    rng = random.Random(a.seed)

    # packages used by validation/test cases are off limits
    excluded = set()
    for _, s in read_jsonl(SRC / "sources.jsonl"):
        if (s["split"] == "public") == holdout:  # holdout: avoid train packages; train: avoid held-out ones
            excluded |= {p["name"].lower() for p in s["packages"] if p.get("name")}
    if holdout:
        excluded |= {n.lower() for names in PACKAGES.values() for n in names}
    existing = []
    for f in sorted((ROOT / "data" / "authoring").rglob("*.jsonl")):
        if f == out_path:
            continue
        for _, r in read_jsonl(f):
            t = normalise(r["prompt"])
            existing.append((t, shingles(t)))

    amb_file = SRC / "ambiguous_advisories.txt"
    ambiguous = set(amb_file.read_text().split()) if amb_file.exists() else set()
    candidates, gid_pkg = [], {}
    for eco, names in packages.items():
        for name in names:
            if name.lower() in excluded:
                print(f"skip {name}: used in a validation/test case")
                continue
            try:
                recs = osv_query(eco, name, a.offline)
                versions = registry_versions(eco, name, a.offline)
            except Exception as e:  # noqa: BLE001 - one package failing must not stop the run
                print(f"skip {name}: {e}")
                continue
            for rec in recs:
                gid = ghsa_of(rec)
                sev = (rec.get("database_specific") or {}).get("severity")
                if gid in ambiguous:
                    continue  # OSV records for this advisory disagree on the affected range
                if not gid or rec.get("withdrawn") or sev not in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
                    continue
                rngs = ranges_for(rec, eco, name)
                fns = make_affected(eco, rngs) if rngs else None
                if not fns:
                    continue
                affected, range_of = fns
                v_in = next((v for v in reversed(versions) if affected(v)), None)
                if not v_in:
                    continue
                r_in = range_of(v_in)
                after = [v for v in versions if parse(eco, v) >= parse(eco, r_in["fixed"]) and not affected(v)]
                v_out = after[0] if after else None
                before = [v for v in versions if parse(eco, v) < parse(eco, v_in)]
                wrong_le = before[-1] if before else None
                wrong_gt = next((v for v in versions if v_out and parse(eco, v) > parse(eco, v_out)), None)
                summary = (rec.get("summary") or "").strip().rstrip(".")
                if not summary or len(summary) > 140:
                    continue
                if ADVISORY_ID.search(summary):
                    continue  # the title cites another advisory (e.g. "bypass of CVE-…"): ambiguous ids

                cve = next((x for x in rec.get("aliases", []) if x.startswith("CVE-")), None)
                gid_pkg[gid] = name
                candidates.append({"gid": gid, "cve": cve, "sev": sev, "summary": summary, "pkg": name, "eco": eco,
                                   "v_in": v_in, "r_in": r_in, "v_out": v_out, "r_fixed": r_in,
                                   "wrong_fix_le": wrong_le, "wrong_fix_gt": wrong_gt, "url": f"https://github.com/advisories/{gid}"})

    rng.shuffle(candidates)
    rows, per_pkg, used_ids = [], {}, set()
    pool = list(existing)
    kinds_cycle = ["F2-in", "F2-out", "F7", "F1", "F8", "F2-in", "F2-out"]
    k_i = 0
    for c in candidates:
        if len(rows) >= a.max_pairs:
            break
        if per_pkg.get(c["pkg"], 0) >= a.per_package:
            continue
        for _ in range(len(kinds_cycle)):
            kind = kinds_cycle[k_i % len(kinds_cycle)]
            k_i += 1
            if kind == "F2-in" and not c["wrong_fix_le"]:
                continue
            if kind == "F2-out" and not (c["v_out"] and c["wrong_fix_gt"]):
                continue
            if kind == "F8" and c["sev"] not in ("HIGH", "CRITICAL"):
                continue
            if kind == "F1":
                others = [o for o in candidates if o["pkg"] != c["pkg"] and o["eco"] == c["eco"]]
                if not others:
                    continue
                c = {**c, "distractor": rng.choice(others)}
            break
        else:
            continue
        evidence = c["r_in"] if kind in ("F2-in", "F2-out", "F7") and rng.random() < 0.5 else None
        v_prompt = c["v_out"] if kind == "F2-out" else c["v_in"]
        prompt = prompt_for("F1" if kind == "F1" else "F8" if kind == "F8" else "F2", rng, c["pkg"], v_prompt,
                            c["gid"], c["cve"], c["summary"], c["eco"], evidence, rng.choice(CONTEXTS))
        t = normalise(prompt)
        sh = shingles(t)
        if too_similar(t, sh, pool, sim_threshold, exhaustive=holdout):
            continue
        fmt, _, chosen, rejected, vc, vr, note = build_pair(kind, rng, c)
        row = {"case": c["gid"], "family": kind.split("-")[0], "split": a.split, "format": "mixed" if fmt == "terse" else fmt,
               "prompt": prompt, "chosen": chosen, "rejected": rejected, "source_url": c["url"],
               "verdict_chosen": vc, "verdict_rejected": vr, "flaw_note": note, "author": GENERATOR,
               "reviewed": False, "source_kind": "advisory", "voice": "generated-minimal",
               "generator": {"kind": kind, "package": c["pkg"], "ecosystem": c["eco"], "version": v_prompt,
                             "evidence_in_prompt": bool(evidence)}}
        if kind == "F1":
            row["misattributed_ids"] = [c["distractor"]["gid"]] + ([c["distractor"]["cve"]] if c["distractor"]["cve"] else [])
            used_ids.add(c["distractor"]["gid"])
        rows.append(row)
        used_ids.add(c["gid"])
        per_pkg[c["pkg"]] = per_pkg.get(c["pkg"], 0) + 1
        pool.append((t, sh))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    hand = {line.split()[0] for line in (SRC / "ids.txt").read_text().splitlines()
            if line.strip() and not line.startswith("#")}
    ids_out.write_text(f"# generated by tools/gen_osv_pairs.py; all split={a.split}\n" +
                       "".join(f"{i} split={a.split}\n" for i in sorted(used_ids - hand)))
    kinds = {}
    for r in rows:
        kinds[r["generator"]["kind"]] = kinds.get(r["generator"]["kind"], 0) + 1
    print(f"wrote {len(rows)} pairs -> {out_path.relative_to(ROOT)}  kinds {kinds}  "
          f"packages {len(per_pkg)}  advisories {len(used_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
