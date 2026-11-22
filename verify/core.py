"""Verified Ask: check a SECURITY_REVIEW answer against public facts before a buyer trusts it.

Pure logic, no I/O. Network lookups come in through a `Sources` object (see verify/sources.py),
so every check is testable offline.

A package answer is checked on four points:
  1. fields:    the verdict, the count and the issue list agree with each other
  2. exists:    the package version is published (deps.dev or rubygems.org)
  3. verdict:   "vulnerable" or "clean" agrees with what OSV lists for that exact version
  4. citations: every advisory id the answer cites exists and applies to this package and version

Each check returns pass, fail, warn, skip or info (info never changes the label). The label is:
  contradicted  any check failed: public data says the answer is wrong
  verified      every check that ran passed, and the verdict and existence checks both ran
  unconfirmed   nothing failed, but something could not be confirmed (a warning or a skipped check)
  invalid       no usable verdict, so a buyer's machine has nothing to act on
  unchecked     not a package question (code, free text we can't parse): facts can't settle it
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Protocol

VERDICTS = {"Secure", "Needs changes", "Insecure"}
VULNERABLE = {"Insecure", "Needs changes"}

# purl type -> OSV ecosystem
ECOSYSTEMS = {"pypi": "PyPI", "npm": "npm", "maven": "Maven", "golang": "Go", "cargo": "crates.io", "gem": "RubyGems"}
_ECO_WORDS = {"pypi": "pypi", "npm": "npm", "maven": "maven", "go": "golang", "golang": "golang",
              "crates.io": "cargo", "cargo": "cargo", "rubygems": "gem", "gem": "gem"}

# Advisory namespaces OSV mirrors in full: an id from one of these that OSV doesn't know is
# almost certainly invented. CVEs are different: OSV doesn't carry every CVE, so a missing CVE is
# only a warning.
_FULL_MIRRORS = ("GHSA", "PYSEC", "GO", "RUSTSEC", "RUBYSEC", "OSV", "MAL")
_ID = re.compile(r"\b(GHSA(?:-[23456789cfghjmpqrvwx]{4}){3}|CVE-\d{4}-\d{4,}|PYSEC-\d{4}-\d+|GO-\d{4}-\d{4,}"
                 r"|RUSTSEC-\d{4}-\d{4}|MAL-\d{4}-\d+)\b", re.I)
_PLACEHOLDER = re.compile(r"\b(?:CVE|GHSA)-\d{0,4}-?(?:\.\.\.|x{3,}|X{3,}|…)", re.I)
_DASHES = str.maketrans({c: "-" for c in "‐‑‒–—−"})


@dataclass(frozen=True)
class Package:
    purl_type: str  # pypi, npm, maven, golang, cargo, gem
    name: str       # OSV spelling: maven uses group:artifact
    version: str    # OSV spelling: Go without the leading v

    @property
    def ecosystem(self) -> str:
        return ECOSYSTEMS[self.purl_type]


@dataclass
class Check:
    name: str
    status: str  # pass | fail | warn | skip | info
    detail: str


@dataclass
class Verdict:
    label: str
    target: str
    package: dict | None
    checks: list[Check] = field(default_factory=list)
    osv_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class Sources(Protocol):
    def osv_query(self, pkg: Package) -> list[dict] | None: ...       # vulns for this version; None = unavailable
    def osv_vuln(self, vid: str) -> dict | None | bool: ...           # the record; False = 404; None = unavailable
    def version_exists(self, pkg: Package) -> bool | None: ...         # None = can't tell


def parse_target(target: str) -> Package | None:
    """A purl (pkg:npm/lodash@4.17.21), "lodash 4.17.21 (npm)", or "Is lodash version 4.17.21 from npm ...?"."""
    t = target.strip()
    m = re.match(r"^pkg:([a-z]+)/(.+)@([^@\s]+)$", t)
    if m and m.group(1) in ECOSYSTEMS:
        ptype, name, ver = m.groups()
        return _norm(ptype, name, ver)
    m = re.match(r"^([\w.\-/:@]+)\s+v?([\w.\-+]+)\s+\(([\w.]+)\)$", t)
    if m and m.group(3).lower() in _ECO_WORDS:
        return _norm(_ECO_WORDS[m.group(3).lower()], m.group(1), m.group(2))
    m = re.search(r"\b([\w.\-/:@]+)\s+version\s+v?([\w.\-+]+)\s+from\s+([\w.]+)\b", t, re.I)
    if m and m.group(3).lower() in _ECO_WORDS:
        return _norm(_ECO_WORDS[m.group(3).lower()], m.group(1), m.group(2))
    return None


def _norm(ptype: str, name: str, ver: str) -> Package:
    if ptype == "maven":
        name = name.replace("/", ":")
    if ptype == "golang" and ver.startswith("v"):
        ver = ver[1:]
    if ptype == "pypi":
        name = re.sub(r"[-_.]+", "-", name).lower()
    return Package(ptype, name, ver)


def cited_ids(result: dict) -> tuple[list[str], list[str]]:
    """Advisory ids cited in issues and summary (deduplicated, upper case), and placeholder ids like CVE-2020-...."""
    text = " ".join(map(str, result.get("issues") or [])) + " " + str(result.get("summary") or "")
    text = text.translate(_DASHES)
    ids = list(dict.fromkeys(m.upper() for m in _ID.findall(text)))
    return ids, list(dict.fromkeys(_PLACEHOLDER.findall(text)))


def _n(n: int) -> str:
    return f"{n} advisory" if n == 1 else f"{n} advisories"


def _count(result: dict):
    c = result.get("vulnerability_count")
    return c if isinstance(c, (int, float)) and not isinstance(c, bool) else None


def _applies(record: dict, pkg: Package) -> bool:
    """Does the OSV record name this package? (Version is settled by the version query.)"""
    for a in record.get("affected", []):
        p = a.get("package", {})
        name = p.get("name", "")
        if pkg.purl_type == "pypi":
            name = re.sub(r"[-_.]+", "-", name).lower()
        if p.get("ecosystem") == pkg.ecosystem and name == pkg.name:
            return True
    return False


def verify(target: str, result: dict | None, src: Sources) -> Verdict:
    pkg = parse_target(target)
    v = Verdict(label="unchecked", target=target, package=asdict(pkg) if pkg else None)
    if not isinstance(result, dict) or result.get("verdict") not in VERDICTS:
        v.label = "invalid"
        v.checks.append(Check("fields", "fail", f"no usable verdict ({(result or {}).get('verdict')!r})"))
        return v
    if pkg is None:
        v.checks.append(Check("scope", "skip", "not a package question; facts can't settle it"))
        return v

    verdict, count = result["verdict"], _count(result)
    says_vulnerable = verdict in VULNERABLE

    # 1. fields agree
    if count is None:
        v.checks.append(Check("fields", "warn", "vulnerability_count is missing or not a number"))
    elif says_vulnerable and count == 0:
        v.checks.append(Check("fields", "fail", f"verdict {verdict!r} but vulnerability_count is 0"))
    elif not says_vulnerable and count > 0:
        v.checks.append(Check("fields", "fail", f"verdict 'Secure' but vulnerability_count is {count}"))
    else:
        v.checks.append(Check("fields", "pass", "verdict and count agree"))

    # 2. the version exists
    exists = src.version_exists(pkg)
    if exists is False:
        v.checks.append(Check("exists", "fail", f"{pkg.name} {pkg.version} is not published on {pkg.ecosystem}"))
    elif exists is None:
        v.checks.append(Check("exists", "skip", "registry lookup unavailable"))
    else:
        v.checks.append(Check("exists", "pass", f"{pkg.name} {pkg.version} is published"))

    # 3. verdict vs OSV for this exact version
    vulns = src.osv_query(pkg)
    known: set[str] = set()
    if vulns is None:
        v.checks.append(Check("verdict", "skip", "OSV unavailable"))
    else:
        for x in vulns:
            known.add(x["id"].upper())
            known |= {a.upper() for a in x.get("aliases", [])}
        v.osv_ids = sorted(x["id"] for x in vulns)
        n = len(vulns)
        if exists is False:
            v.checks.append(Check("verdict", "skip", "version not published, so OSV's empty answer means nothing"))
        elif says_vulnerable and n == 0:
            v.checks.append(Check("verdict", "fail", f"says {verdict!r}, but OSV lists no advisory for this version"))
        elif not says_vulnerable and n > 0:
            v.checks.append(Check("verdict", "fail", f"says 'Secure', but OSV lists {_n(n)}: {', '.join(v.osv_ids[:5])}"))
        else:
            v.checks.append(Check("verdict", "pass", f"OSV lists {_n(n)} for this version"))
        if count is not None and n and says_vulnerable and count != n:
            v.checks.append(Check("count", "info", f"count {count}, OSV lists {n} records (aliases may be counted once)"))

    # 4. every cited advisory id is real and about this package and version
    ids, placeholders = cited_ids(result)
    for p in placeholders:
        v.checks.append(Check("citation", "fail", f"placeholder id {p!r} instead of a real advisory"))
    for vid in ids:
        if vid in known:
            v.checks.append(Check("citation", "pass", f"{vid} affects this version"))
            continue
        rec = src.osv_vuln(vid)
        if rec is None:
            v.checks.append(Check("citation", "skip", f"{vid}: OSV unavailable"))
        elif rec is False:
            full = vid.split("-")[0] in _FULL_MIRRORS
            v.checks.append(Check("citation", "fail" if full else "warn",
                                  f"{vid} does not exist in OSV" + ("" if full else " (OSV doesn't carry every CVE)")))
        elif not _applies(rec, pkg):
            names = sorted({f"{a.get('package', {}).get('ecosystem')}/{a.get('package', {}).get('name')}"
                            for a in rec.get("affected", [])})[:3]
            v.checks.append(Check("citation", "fail", f"{vid} is about {', '.join(names) or 'another product'}, not {pkg.name}"))
        elif vulns is not None:
            v.checks.append(Check("citation", "fail", f"{vid} is about {pkg.name}, but not version {pkg.version}"))
        else:
            v.checks.append(Check("citation", "skip", f"{vid} names {pkg.name}; version not checked (OSV query unavailable)"))

    st = [c.status for c in v.checks]
    ran = {c.name for c in v.checks if c.status == "pass"}
    if "fail" in st:
        v.label = "contradicted"
    elif "warn" in st or "skip" in st or not {"verdict", "exists"} <= ran:
        v.label = "unconfirmed"
    else:
        v.label = "verified"
    return v
