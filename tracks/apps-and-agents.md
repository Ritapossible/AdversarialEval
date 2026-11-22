# Apps & Agents track: Dependency.Guard (Mission 10, Model Economy)

## Summary

**Dependency.Guard** is a Mind (Minds by Animoca Brands) that decides whether a project's
dependency change is safe to ship. For each package it buys **one** `SECURITY_REVIEW_GENERAL`
answer from Telegraph's ranked route through Anjoman, checks it **free** with **Verified Ask**,
re-asks one other provider only when the check proves the answer wrong, and returns **PASS, BLOCK
or FLAG** with the advisories, receipts and cost. It re-checks approved versions daily. It is
backed by a **paid benchmark** of the security miners (3,680 calls) that shows which providers
are worth paying for.

| | |
|---|---|
| Mind | Dependency.Guard, id `38266542-f36b-1410-8467-00039ce7df11` ([profile](https://hellominds.ai/profile/minds/38266542-f36b-1410-8467-00039ce7df11)) |
| Working app | https://adversarialeval.vercel.app (benchmark summary; hosted Verified Ask at `/api/verify`) |
| Mission | [#198, Mission 10, Model Economy](https://github.com/telegraphprotocol/bounties/issues/198): routes 1 (cost per verified correct answer) and 2 (procurement via ranked routing) |
| Demo video | to follow |

## Customer and problem

A team whose coding agent or CI adds and upgrades dependencies must not ship a known-vulnerable
version. It wants a decision it can act on automatically, at a known cost, with evidence. Buying
that decision from Telegraph is only useful if the answer is right, and our benchmark showed
that most paid security answers had no usable verdict and that the ranking didn't reliably
reflect accuracy.

## What was built

| Part | What it does | Where |
|---|---|---|
| **Paid market benchmark** | Same 46 cases bought from every reachable miner on three days under a pre-registered rule; payments reconciled with the chain (x402) or the node's ledger (escrow); accuracy, cost per correct answer, rank agreement, stability | [`bench/`](../bench/), [`bench/RULE-v2.md`](../bench/RULE-v2.md) |
| **Verified Ask** | Free check of a security answer: verdict vs OSV for the exact version, cited advisory ids exist and apply, version exists, fields agree. Labels: verified, contradicted, unconfirmed, invalid, unchecked | [`verify/`](../verify/), hosted at `/api/verify` (token-protected, rate-limited) |
| **Dependency.Guard Mind** | The full flow inside Minds with its HTTP tool and private credentials; daily watchlist | [`mind/README.md`](../mind/README.md), [`mind/evidence/2026-11-22-watchlist.json`](../mind/evidence/2026-11-22-watchlist.json) |
| **Connector** | The same flow from outside Minds; produced the test evidence | [`mind/connector/guard.mjs`](../mind/connector/guard.mjs) |

Spending policy, following Telegraph's guidance: one ranked answer per package, never several
providers by default; a re-ask only when the free check proves the answer wrong; caps per package,
per task and per day.

## Results (testnet, answer keys frozen before any paid call)

**Market benchmark, rounds 2 to 4** ([report](../eval/reports/2026-11-22-rounds-2-4.md))

| Finding | Result |
|---|---|
| Calls | 3,680 over three days; round-4 receipts matched the ledger to within one unmatched $0.01, reported |
| Best miner vs the free OSV lookup | a1-preflight 83% pooled (95% CI 75 to 89%) vs 67% for the free lookup; the only miner to beat it |
| Rank vs accuracy (Kendall's τ) | +0.02, −0.18, then +0.29 when a rebuilt miner reached rank 1 |
| Default route | 5, 1, then 17 of 36 correct: it follows rank 1 |

**Verified Ask, replayed over every paid answer** ([report](../eval/reports/2026-11-22-verified-ask.md)):
none of 142 wrong package answers labelled verified; 220 of 220 verified answers correct.

**With and without Telegraph** ([packages](../eval/reports/2026-11-22-mind-comparison.md),
[code](../eval/reports/2026-11-22-code-review-v2.md))

| Test | Telegraph answer trusted | Telegraph + Verified Ask (or the Mind weighing it) | Mind alone |
|---|---|---|---|
| 26 packages, 7 ecosystems, incl. 2 that don't exist | 11 right of the 18 answered; 3 vulnerable versions passed; 2 non-existent packages called "Secure" | nothing unsafe approved (24 decided right, 2 flagged for a person) | 26 of 26 (by querying OSV itself) |
| 23 subtle code functions (pre-registered) | route 13/23, best miner directly 11/23; both missed real flaws | the Mind, shown the routed answers, 23/23, overruling all 10 wrong ones | 23 of 23 |

Other findings: the same miner changed its verdict on 5 of 20 snippets asked 15 minutes apart;
a routed ask reserves $0.26 and can settle two payments; a facilitator outage refused payments
for about 20 minutes on 22 Nov.

**What we claim, and don't.** Verified Ask stops wrong paid answers from becoming decisions, and
the benchmark tells a buyer which providers are worth paying. We do not claim that buying
Telegraph security answers beats a free lookup on known package vulnerabilities; on 22 Nov it
didn't, and the Mind on its own matched every result.

## Reproduce

```bash
python bench/score_v2.py bench/out/round-2 bench/out/round-3 bench/out/round-4   # benchmark tables
python tests/test_reproduce.py                                                   # published numbers
python -m verify.replay bench/out/round-2 bench/out/round-3 bench/out/round-4 --out /tmp/replay --offline
python mind/compare.py mind/evidence/2026-11-22T12-56-00-304Z.json mind/evidence/2026-11-22-mind-alone.json
python tests/test_verify.py && python tests/test_mind.py
```

Running the paid parts needs an Anjoman API key with a funded balance; see
[`mind/README.md`](../mind/README.md).

## Limits

- Testnet, one payer, small samples (46 cases per round; 26 packages; 23 code functions).
  Intervals are wide; differences of one or two are noise.
- OSV is the reference for package truth; code truth is by construction and review.
- Package questions only for automatic checking; code answers can't be checked by a free lookup.
- In the code test, the Mind saw the functions alone before seeing them with Telegraph's answers,
  so that arm isn't independent.
