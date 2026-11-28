# Apps & Agents track: Dependency.Guard (Mission 10, Model Economy)

## Summary

**Dependency.Guard** is a Mind (Minds by Animoca Brands) that decides whether a project's
dependency change is safe to ship. For each package it buys **one** `SECURITY_REVIEW_GENERAL`
answer from Telegraph's ranked route through Anjoman, checks it **free** with **Verified Ask**,
re-asks one other provider only when the check proves the answer wrong, and returns **PASS, BLOCK
or FLAG** with the advisories, receipts and cost. Every PASS and BLOCK is re-checked for free each
day ([`mind/watch.py`](../mind/watch.py), run by the [`watch`](../.github/workflows/watch.yml) job). It is
backed by a **paid benchmark** of the security miners (3,680 calls) that shows which providers
are worth paying for.

The same check-before-trust design was then applied, each time under a pre-registered rule, to:
- **code written by Qwen** (Alibaba item 4);
- **a pre-deployment check of Qwen-Agent**;
- **prediction market settlement:** 24 test markets, then 24 real Polymarket markets, paid both
  directly on Solana and through the app (Anjoman + the Mind).

All 333 evidence files are signed, and their hash is anchored on Solana devnet.

| | |
|---|---|
| Mind | Dependency.Guard, id `38266542-f36b-1410-8467-00039ce7df11` ([profile](https://hellominds.ai/profile/minds/38266542-f36b-1410-8467-00039ce7df11)) |
| Working app | https://adversarialeval.vercel.app/dependency-guard (decisions with their evidence and Solana payments; hosted Verified Ask at `/api/verify`) |
| Mission | [#198, Mission 10, Model Economy](https://github.com/telegraphprotocol/bounties/issues/198): routes 1 (cost per verified correct answer) and 2 (procurement via ranked routing) |
| Listed on Anjoman | Dependency.Guard, category Security, status Live (28 Nov) |
| Demo videos | Prediction markets: https://x.com/RitaCryptoTips/status/2126711423908614492 · Qwen code test: https://x.com/RitaCryptoTips/status/2126612379286786350 · In-app Polymarket demo and Solana packages: `[add links]` |
| Evidence anchor | [Solana devnet memo](https://explorer.solana.com/tx/2J9e6xD5v2Wnn17Qd9BCiRgqiVTEzhXzYhwb11e8B32gsXUtJCVZUCunE3Fmh4K9EQpQxm65R5TJMaVzRNoZMPu7?cluster=devnet) holding the SHA-256 of the signed manifest of 333 files; `node tools/anchor_evidence.mjs verify` |

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
| **Dependency.Guard Mind** | The full flow inside Minds with its HTTP tool and private credentials; a watchlist of its decisions, re-checked free each day; a standing rule that miner output is untrusted data ([drill](../mind/evidence/2026-11-23-mind-injection-drill.json)) | [`mind/README.md`](../mind/README.md), [`mind/evidence/2026-11-22-watchlist.json`](../mind/evidence/2026-11-22-watchlist.json), [`mind/evidence/watch/`](../mind/evidence/watch/) |
| **Connector** | The same flow from outside Minds; produced the test evidence. Reads lockfiles, reserves the worst-case price against its cap, logs every paid attempt as it returns, reconciles with the balance, and passes the Mind only structured fields | [`mind/connector/guard.mjs`](../mind/connector/guard.mjs) |

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
[code](../eval/reports/2026-11-22-code-review-v2.md),
[Solana](../eval/reports/2026-11-23-solana-dependencies.md),
[Solana use case 3, paid on Solana](../eval/reports/2026-11-24-solana-use-case-3.md))

| Test | Telegraph answer trusted | Telegraph + Verified Ask (or the Mind weighing it) | Mind alone |
|---|---|---|---|
| 26 packages, 7 ecosystems, incl. 2 that don't exist | 11 right of the 18 answered; 3 vulnerable versions passed; 2 non-existent packages called "Secure" | nothing unsafe approved (24 decided right, 2 flagged for a person) | 26 of 26 (by querying OSV itself) |
| 23 subtle code functions (pre-registered) | route 13/23, best miner directly 11/23; both missed real flaws | the Mind, shown the routed answers, 23/23, overruling all 10 wrong ones | 23 of 23 |
| 16 Solana stack versions (pre-registered), incl. the hijacked `@solana/web3.js` 1.95.7 and 2 that don't exist | 14/16: all 7 bad versions blocked, but both non-existent versions given a confident verdict | 16/16 for $0.22; both non-existent versions flagged | 16 of 16 |
| 21 hard Solana cases, every call paid in USDC on Solana devnet (pre-registered) | ranked route 6/21, approving malware 5 times; first-listed provider 8/21 | 20/21 for $0.35, nothing unsafe approved (1 malware package flagged for a person) | 21 of 21 |

**Beyond packages (25 to 28 Nov, each rule frozen before any paid call)**

| Test | Paid answers trusted | With the check | Report |
|---|---|---|---|
| Qwen-Agent 0.0.34, Alibaba's agent framework: is it safe to deploy? | 4 paid answers, all verified, but blind to the real exposure | **HOLD as shipped:** it doesn't import after the documented install, and Pillow has 5 critical advisories reachable through image decoding. A tested fix serves the UI with 2 conditional advisories left | [report](../eval/reports/2026-11-25-qwen-agent-predeploy.md) |
| 36 changes written by Qwen2.5-Coder for 12 tasks (30 should not ship) | Qwen reviewing itself: 6/36 right, approved all 36; Telegraph answers trusted: 14/36 | **27/36**, no good change blocked; caught a non-existent pin and PyJWT with 14 advisories that the paid answer called "Secure"; all three arms missed 9 | [report](../eval/reports/2026-11-28-qwen-code-verification.md) |
| 24 prediction markets we wrote (Coinbase, NHL, MLB, USGS), paid on Solana | one answer: 3 settled on the wrong side; two independent providers agreeing: 1 wrong | **0 wrong**, 21/24 right | [report](../eval/reports/2026-11-28-prediction-market-resolution.md) |
| 24 real Polymarket markets ($180M traded), paid on Solana | 0 wrong, but the ranked route settled only 6 | **0 wrong**; all 6 crypto markets settled from Binance 1-minute candles, matching Polymarket (one by $6) | [report](../eval/reports/2026-11-28-polymarket-resolution.md) |
| The same 24 Polymarket markets **through the app** (Anjoman + the Mind) | paid answers gave an outcome for 1 of 24; 7 timed-out asks were charged | **0 wrong**: 6 settled from Binance, 18 held for a person; the Mind's report kept to the evidence | [report](../eval/reports/2026-11-28-polymarket-via-app.md), [addendum](../eval/reports/2026-11-28-polymarket-via-app-addendum.md) |

Other findings: the same miner changed its verdict on 5 of 20 snippets asked 15 minutes apart;
a routed ask reserves $0.26 and can settle two payments; a facilitator outage refused payments
for about 20 minutes on 22 Nov.

**What we claim, and don't.** Checking paid answers before acting stops wrong ones from becoming
decisions, whether a package verdict, a code review or a market settlement, and the benchmark
tells a buyer which providers are worth paying. We do not claim that buying
Telegraph security answers beats a free lookup on known package vulnerabilities; on 22 and 23 Nov
it didn't, and the Mind on its own matched every result. On markets whose rules name a
machine-readable source, the check reads the same source as the truth, so it is right there by
construction. The finding is how often paid answers alone would have settled money wrongly.

## Reproduce

```bash
python bench/score_v2.py bench/out/round-2 bench/out/round-3 bench/out/round-4   # benchmark tables
python tests/test_reproduce.py                                                   # published numbers
python -m verify.replay bench/out/round-2 bench/out/round-3 bench/out/round-4 --out /tmp/replay --offline
python mind/compare.py mind/evidence/2026-11-22T12-56-00-304Z.json mind/evidence/2026-11-22-mind-alone.json
python tests/test_verify.py && python tests/test_mind.py
```

Running the paid parts needs an Anjoman API key with a funded balance; see
[`mind/README.md`](../mind/README.md). The newer tests reproduce with:

```bash
python tests/test_codeverify.py && python tests/test_resolve.py      # frozen tasks and markets, offline
python codeverify/score.py score && python resolve/run.py score       # Qwen and market scores from saved answers
NODE_PATH=bench/node_modules node tools/anchor_evidence.mjs verify    # evidence anchor on Solana
NODE_USE_ENV_PROXY=1 node mind/connector/markets.mjs --mind <id> --cases resolve/polymarket_cases.json   # paid, through the app
```

## Limits

- Testnet, one payer, small samples (46 cases per round; 26 packages; 23 code functions).
  Intervals are wide; differences of one or two are noise.
- OSV is the reference for package truth; code truth is by construction and review.
- Package questions only for automatic checking; code answers can't be checked by a free lookup.
- In the code test, the Mind saw the functions alone before seeing them with Telegraph's answers,
  so that arm isn't independent.
