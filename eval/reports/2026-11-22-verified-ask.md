# Verified Ask: checking paid security answers before a buyer trusts them (2026-11-22)

The benchmark ([round 2](2026-11-16-round-2.md), [round 3](2026-11-21-round-3.md),
[rounds 2 to 4](2026-11-22-rounds-2-4.md)) showed that buyers of `SECURITY_REVIEW_GENERAL` answers
can't rely on what a miner returns: most delivered answers have no usable verdict, and in two of
three rounds the top-ranked miner scored 0/36. Verified Ask is the buyer-side fix. It checks every answer against free public data
at the moment the buyer receives it, and returns one label the buyer's code can act on.

This report replays it over the 3,680 calls already bought in rounds 2, 3 and 4 (updated after
round 4; the first version covered rounds 2 and 3). **No new calls were made and nothing was spent.**

## What it checks

For a package question (a purl such as `pkg:npm/minimist@1.2.5`, or the same in plain text):

| Check | Source | Fails when |
|---|---|---|
| fields | the answer itself | the verdict and `vulnerability_count` contradict each other |
| exists | deps.dev, rubygems.org | the package version was never published |
| verdict | OSV query for that exact version | "Secure" while OSV lists advisories, or "vulnerable" while it lists none |
| citations | OSV record for each cited id | a cited id doesn't exist, is about another package, or doesn't affect this version, or is a placeholder like `CVE-2020-...` |

Labels: **verified** (every check ran and passed), **contradicted** (a check failed),
**unconfirmed** (nothing failed, but something couldn't be confirmed: a missing count, or a CVE
that OSV doesn't carry), **invalid** (no usable verdict), and **unchecked** (code: facts can't
settle it).

Code snippets are labelled unchecked on purpose. That is where our evaluator model belongs (next
step), not a lookup.

## Result

- **Replay:** `python -m verify.replay bench/out/round-2 bench/out/round-3 bench/out/round-4 --out bench/out/verify-replay`
- **Data:** [`bench/out/verify-replay/`](../../bench/out/verify-replay/): a label and its checks for
  every call, the summary, and every OSV, deps.dev and rubygems.org response used (2.2 MB), so
  `--offline` reproduces it exactly. `tests/test_verify.py` does that in CI.

### Package answers with a verdict, against the benchmark's frozen grades

| Benchmark grade | Answers | verified | unconfirmed | contradicted |
|---|---:|---:|---:|---:|
| correct | 222 | **220** | 0 | 2 |
| wrong | 142 | **0** | 50 | 92 |

Per round (correct verified / wrong verified): round 2 43 / 0, round 3 69 / 0, round 4 108 / 0.

- **No wrong answer was labelled verified, in any round, and every verified answer was correct
  (220 of 220).**
- 92 of the 142 wrong answers were contradicted outright. The other 50 had the right direction but
  were missing a `vulnerability_count` or cited a CVE that OSV can't tie to a package; the verifier
  says unconfirmed and names what it couldn't confirm.
- The two correct answers that were contradicted are real catches, not false alarms. Both are
  vulnrank-triage on gin 1.5.0 (rounds 3 and 4): right verdict, but it cites `GO-2026-5932`, an
  advisory about `golang.org/x/crypto`. The benchmark's grade doesn't check citations.

### What the extra checks found

| Failed check | Answers |
|---|---:|
| verdict disagrees with OSV | 85 |
| fields contradict each other | 40 |
| version was never published | 8 |
| bad citation (placeholder, wrong package) | 7 answers, 7 citations |

- Bad citations came from two miners: txlens (3 answers, placeholder ids such as `CVE-2020-...`)
  and vulnrank-triage (4 answers, advisories about other packages).
- The unpublished-version check catches 8 confident answers about a package or version that does
  not exist. Four were "Secure, 0 vulnerabilities" in round 2 (a1-preflight and the default route).
  The benchmark could only call these "confident clean".

### What a buyer gets

- Of 1,049 delivered answers to package questions, **677 (65%) had no usable verdict**. A buyer's
  code should reject those, and the label says so.
- Of the rest, 220 come back verified, 102 contradicted with the reason, and 50 unconfirmed.

## Correction (22 Nov, after round 4)

The first count treated a cited CVE whose OSV record names no package (a bare record imported
from NVD) as "about another package", a failure. OSV can't confirm or refute such a citation, so
it is now a warning. Effect: 3 wrong answers move from contradicted to unconfirmed, and txlens's
bad citations drop from 9 answers to 3 (the 6 were real CVEs, not wrong-package claims). The
headline is unchanged: no wrong answer was labelled verified. Regression test in
`tests/test_verify.py`.

## Limits

- **Partly circular on the verdict check.** The benchmark's package truth also comes from OSV
  (frozen when the cases were built), so agreement on the verdict is expected. What this shows is
  that the check works at answer time, for free, with live data, and that OSV didn't drift between
  case build and replay. The existence, citation and field checks are independent of the grades.
- **OSV is the reference.** A miner that finds a real issue OSV doesn't know yet would be marked
  contradicted on the verdict, with the reason shown. A CVE missing from OSV is only a warning.
- **Packages only.** Code answers are unchecked until the evaluator model is wired in.
- 364 graded answers from three rounds; testnet miners.

## Using it

```
python -m verify.server --port 8402
curl -s localhost:8402/v1/verify -d '{"target":"pkg:npm/minimist@1.2.5",
  "result":{"verdict":"Secure","vulnerability_count":0,"issues":[]}}'
# -> {"label":"contradicted", ... "says 'Secure', but OSV lists 1 advisory: GHSA-xvch-5gv4-984h"}
```

Standard library only, no key, no account. A buyer calls a miner as usual, then posts the target
and the miner's `result` before acting on it.

## Next

1. Route code answers to the evaluator model, with calibrated confidence and an "unsure" option.
2. A paying proxy (`/v1/ask`) that calls a miner, verifies, and returns both. Escrow already bills
   only delivered answers, which makes this cheap.
3. Run it on round 4 and publish labels per miner alongside the benchmark.
