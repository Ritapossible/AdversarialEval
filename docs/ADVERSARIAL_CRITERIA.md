# Adversarial Criteria: `SECURITY_REVIEW`

This is the definition of "good" that AdversarialEval trains toward. It's one of the
hackathon deliverables. v1 is a draft and will be frozen at the end of Phase 1.

## The Intent

A `SECURITY_REVIEW_GENERAL` request supplies a `target`: code, dependencies, endpoints,
configuration, a package or a contract. The miner answers with:

| Field | Meaning |
|---|---|
| `verdict` | `Secure` · `Needs changes` · `Insecure` |
| `vulnerability_count` | number of known vulnerabilities or weaknesses (the scored field) |
| `issues` | CVE / GHSA / CWE / OWASP ids, most serious first |
| `summary` | one or two sentences |

Scope, from bounty #96: known CVEs in dependencies, leaked credentials or secrets,
misconfiguration, and injection-prone patterns.

## What a *chosen* answer must be

1. **Correct.** The verdict, the count and every listed id are true for this exact target and
   version.
2. **Grounded.** Each finding points at the specific line, key, dependency or version that
   causes it. Each id is real and applies to the affected range.
3. **Prioritised.** The most serious issue comes first. Severity and CWE class are right.
4. **Complete on criticals.** No critical or high finding that's in scope is missing.
5. **Calibrated.** It's certain where the evidence is decisive. It states exactly what's
   missing (an unpinned version, unseen config) where it isn't, and doesn't refuse.
6. **Internally consistent.** The verdict, the count, the issues list and the summary agree.
7. **Scoped.** Claims about advisories are limited to what the prompt asks: the alert,
   advisory, package or code shown. A chosen answer never says "this version has no known
   vulnerabilities". New advisories appear all the time, so that claim goes stale and makes
   the label wrong. Say "not affected by X" or "for the code shown" instead.
8. **Actionable.** The fix actually closes the issue (upgrade target ≥ the first patched
   version; a parameterised query, not escaping).

## What a *rejected* answer must be

- **Plausible.** It's written in the same register, shape and length as a good miner answer
  (within ±25% of the chosen answer's characters). Most rows have a single decisive flaw.
- **One targeted failure mode.** Each one comes from the families below.
- **Not stylistically marked.** Rejected answers don't share a tone, template, length or
  vocabulary that a question-blind model could learn. The kit enforces this at ≤ 65%; we
  aim for ≤ 60%.

## Failure-mode families

| ID | Family | Rejected answer does | Chosen answer does | Example target |
|---|---|---|---|---|
| **F1** | Fabricated or misattributed id | Cites a CVE/GHSA that doesn't exist, or a real id for a different package, ecosystem or version line | Cites the correct advisory, or says no known advisory applies | `lodash@4.17.20` |
| **F2** | Version-range error | Flags a patched version as vulnerable, or calls an in-range version safe | Compares the pinned version to the affected and patched ranges explicitly | `requests==2.31.0` vs `<2.32.0` advisory |
| **F3** | Missed critical | Lists real minor issues, misses the hard-coded secret, SQLi, SSRF or RCE | Leads with the critical; the count includes it | Flask app with `debug=True` and an AWS key in source |
| **F4** | **Contextual reversal** | Applies a pattern rule while ignoring context that flips it (input already validated, test-only file, dev-dependency, unreachable path, constant argument), or the reverse | Verdict follows the context | `subprocess.run(cmd, shell=True)` where `cmd` is a literal |
| **F5** | Overconfident "Secure" | "No issues found", stated confidently, on vulnerable code | `Needs changes` / `Insecure` with evidence | JWT verified with `algorithms=["none"]` allowed |
| **F6** | False alarm / over-flagging | Invents a vuln in safe code (a parameterised query flagged as SQLi; `secrets.token_hex` flagged as weak RNG) | `Secure`, and says why the suspicious-looking pattern is safe | `cursor.execute("… WHERE id = %s", (uid,))` |
| **F7** | Field inconsistency | Verdict, count and issues disagree (`Insecure` with count 0; three issues, count 5) | Consistent fields | any |
| **F8** | Wrong class or severity | Right bug, wrong CWE or OWASP class, or critical reported as low | Correct mapping and ordering | reflected XSS labelled CSRF |
| **F9** | Unwarranted hedging | Refuses to commit, or says "might be vulnerable, consult an expert", when the evidence is decisive | Commits; hedges only on genuinely missing information | known-vulnerable pinned version |
| **F10** | Ineffective fix | Recommends a mitigation that fails a specific counterexample (blacklist filtering, upgrading to a still-affected version, client-side checks) | A fix that closes the issue | path traversal "fixed" by stripping `../` once |

### What a text-only judge can and can't learn (re-scoped 2026-11-10, audit U7)

The judge is ModernBERT-base: 150M parameters, text only, with no advisory database and no
tool use. Being honest about what it can learn shapes both the training emphasis and the
claims we make.

| Family | Learnable from the text alone? | How we use it |
|---|---|---|
| F3 missed critical, F4 context reversal, F6 false alarm, F9 hedging, F10 ineffective fix | **Yes.** The evidence is in the prompt and the answer: code, context, the reasoning. | Training emphasis. Most hand-written pairs go here. |
| F7 field inconsistency | **Yes.** It's internal to the answer. | Training: generated minimal pairs plus hand-written ones. |
| F2 version range | **Only if the prompt carries the range.** Otherwise it's memorisation. | Half of the generated F2 prompts quote the advisory range ("evidence in prompt"), making it an in-context version comparison. The rest test memorised advisories and stay mainly as pool material. |
| F1 wrong advisory id | **Mostly no.** Checking that an id matches a package needs the database. | Mainly evaluation material for the pool. We claim robustness here only where the answer is internally inconsistent (e.g. the id's package doesn't match the prompt). |
| F8 severity | **Partly.** Impact language ("RCE", "unauthenticated") is visible; exact CVSS isn't. | Training with severity framed by impact, not by score. |

**What we claim in the write-up:** robustness to *reasoning* failures (missed criticals,
context, false alarms, hedging, broken fixes, inconsistency) and to *checkable* factual
errors (version vs a quoted range). We don't claim the adapter can verify arbitrary CVE
ids or version ranges from memory.

### Balancing rules

- **Families:** about 10% each. F4 and F6 get about 15% each, because they're the
  "looks right / looks wrong" inversions that defeat surface heuristics.
- **Verdicts:** across all chosen answers, roughly ⅓ `Secure`, ⅓ `Needs changes`,
  ⅓ `Insecure`. Otherwise "Insecure wins" becomes a shortcut.
- **Citations:** about 30% of chosen answers carry no ids, because none apply. About 30% of
  rejected answers carry real-looking ids. Then "has a CVE" isn't a signal.
- **Hedging:** hedging language appears in both chosen (F-calibrated) and rejected (F9)
  answers.
- **Length:** in about 50% of pairs the rejected answer is the longer one.
- **Format:** a mix of prose, bullet lists and JSON-shaped responses
  (`{"verdict": …, "vulnerability_count": …, "issues": […], "summary": …}`), on both sides.
- **Pairing twins:** where possible, author the F4 and F6 twins from the same base snippet.
  One variant is vulnerable and one is safe, so only the reasoning separates them.

## Naive scorers this data must defeat

Reported per family in `eval/reports/`. Target ≤ 60% overall for each:

| Scorer | Rule |
|---|---|
| Longer-wins / shorter-wins | Pick by character length |
| Keyword overlap | Pick the answer that shares more tokens with the prompt |
| Security-term density | Pick the answer with more CVE / CWE / "vulnerab*" / "inject*" tokens |
| Confidence words | Pick the answer with fewer (or more) hedge words |
| Question-blind BoW | Logistic regression on answer words only (the kit's surface probe) |
| TF-IDF to prompt | Pick the answer with the higher cosine similarity to the prompt |

## Second Intent (stretch): `SMART_CONTRACT_AUDIT`

The same structure applies, with families adapted to Solidity and EVM: reentrancy that the
check-effects-interactions order already prevents (F4); `onlyOwner` present but the owner is
a renounced zero address (F4); unchecked arithmetic in ≥ 0.8 versus `unchecked {}` blocks
(F2/F6); `tx.origin` auth missed (F3); fabricated SWC ids (F1); a proxy-initialiser
front-run missed (F3). Detailed in Phase 5.
