# Cost per verified correct answer: SECURITY_REVIEW on testnet (2026-11-15)

Mission 10 (Model Economy), route 1. A buyer pays $0.01 per call. How much does one **verified
correct** security answer actually cost, and does the network's ranking point buyers to the miners
that give one?

## Setup

The rule was frozen and committed before the first paid call ([`bench/RULE.md`](../../bench/RULE.md),
commit `20937bf`).

- 7 cases with ground truth frozen from OSV ([`bench/cases.json`](../../bench/cases.json)):
  - jinja2 2.10 and lodash 4.17.15 (affected: 12 and 5 OSV records);
  - jinja2 3.1.6 and express 4.21.2 (no OSV record);
  - a package that does not exist;
  - an Express route that concatenates user input into SQL (CWE-89), and the same route parameterised.
- Each case went to the 12 miners that could take a canonical request in the
  [audit](2026-11-15-miner-audit.md), and once to the auto-routed ask that a buyer gets by default.
  Request: `{"intent":"SECURITY_REVIEW_GENERAL","params":{"target":...}}`. One attempt each, no
  retries.
- 91 calls, 2026-11-15 18:10 to 18:36 UTC.
- Payment: x402 `exact` on Ethereum Sepolia, test USDC, from a testnet-only wallet
  (`0xA0C8…6C1C`), using the official `@x402/fetch` 2.29.0 client.
- Every delivered answer has a Telegraph receipt (`receipt_hash`, `tx_hash`) in
  [`bench/out/calls.ndjson`](../../bench/out/calls.ndjson).

## Result

| Miner | Node rank | Correct / 7 | of which answerable (6) | Wrong | No answer | Paid for answers | Cost per correct |
|---|---:|---:|---:|---:|---:|---:|---:|
| `a1-preflight` | unranked | 6 | 6 | 0 | 0 (+1 unverifiable) | $0.07 | $0.012 |
| `telegraph-verity-intelligence` | unranked | 2 | 1 | 1 | 4 | $0.02 | $0.010 |
| `codewire-security-review` | 9 | 2 | 1 | 0 | 5 | $0.03 | $0.015 |
| `zk-secaudit` | 28 | 2 | 1 | 2 | 3 | $0.05 | $0.025 |
| auto-routed (buyer default) | n/a | 2 | 2 | 1 | 3 (+1 unverifiable) | $0.07 | $0.035 |
| `zk-secpub` | 5 | 1 | 0 | 0 | 6 | $0.03 | $0.030 |
| `zk-ghsapub` | unranked | 1 | 0 | 0 | 6 | $0.04 | $0.040 |
| `zk-pysec` | 27 | 1 | 0 | 0 | 6 | $0.04 | $0.040 |
| `evidence-security-review` | 10 | 1 | 0 | 0 | 6 | $0.00 | n/a |
| `zk-astsec` | 26 | 1 | 0 | 0 | 6 | $0.00 | n/a |
| `zk-code-deps` | 27 | 1 | 0 | 0 | 6 | $0.00 | n/a |
| `zk-friendsec` | 5 | 1 | 0 | 0 | 6 | $0.00 | n/a |
| `pr-guard-sentinel` | 1 | 0 | 0 | 0 | 7 | $0.03 | n/a |

"Correct / 7" follows the frozen rule, which counts an error on the non-existent package as a
correct abstention. Most miners' single "correct" is only that, so the **answerable** column (the
other 6 cases) is the fairer read. "Paid for answers" sums the receipts of delivered answers.

**Totals**
- 91 calls; 38 delivered an answer with a receipt ($0.38).
- 21 verified correct answers under the rule: **$0.018 per verified correct answer** across the
  network, or $0.38 for 11 correct answers to answerable cases (**$0.035 each**).

## Findings

1. **One unranked miner did the job.** `a1-preflight` answered all 6 answerable cases correctly, at
   $0.012 per correct answer:
   - right verdicts and counts on all four package cases;
   - the SQL injection flagged as CWE-89, and the parameterised version passed.

   It has no rank on this intent. Its only miss is calling the non-existent package `Secure`
   ("OSV.dev lists no known vulnerabilities"), which is unverifiable rather than wrong.
2. **The rank 1 miner gave no usable verdict.** `pr-guard-sentinel` was paid for 3 answers and its
   issue lists were right (for jinja2 2.10 it listed the correct GHSA and CVE ids). But its verdict
   was missing every time: the node marked the field `rejected` or `missing`, so buyers get
   `verdict: null`.
3. **Delivered is not answered.** 21 of the 38 paid, delivered answers came back with `verdict: null`.
4. **The default route was right on 2 of 6 answerable cases.** The auto-routed ask went to
   `pr-guard-sentinel` for six cases and to `a1-preflight` once. It said `Secure` for express 4.21.2,
   but with no count, so it is graded wrong under the frozen rule.
5. **Most miners are narrow.** Eight miners answered no answerable case. Their errors ask for formats
   the canonical `target` doesn't specify:
   - "Supply an exact npm target";
   - "Use one exact Composer release";
   - "This miner reviews JavaScript source".

   They are registered on a general intent but serve one ecosystem or one input shape.
6. **Failed calls were charged.** The wallet paid 0.85 USDC for 91 calls: $0.38 for delivered
   answers and about $0.47 for 47 calls that returned 500, 503 or 504. 43 of those carry a settlement
   header. Telegraph's docs say such amounts are credited to the payer's escrow balance; we found no
   public endpoint to confirm it.

## What it means for evaluation

- The ranking and the buyer's experience disagree:
  - the miner that answered correctly is unranked;
  - the rank 1 miner returns no verdict;
  - in the earlier audit, the rank 2 and rank 4 miners couldn't take the request at all.
- Two things a SECURITY_REVIEW evaluator should check, and that this repo's evaluation material can
  add to:
  - whether `verdict` is present and in the enum;
  - whether it agrees with the evidence (an affected version needs a non-Secure verdict and a count of
    at least 1).

## Limits

- 7 cases is a small sample, so read the order as indicative.
- One attempt per pair: transient errors (six `503 try again later`, four `504`) count against the
  miner, as first-pass success is what a buyer gets.
- OSV is the ground truth for packages. A miner using another database can count differently, which
  is why the rule only needs a count of at least 1 or exactly 0.
- The frozen rule's treatment of the unknown package (an error counts as correct) flatters miners
  that error on everything. We report it as frozen and add the answerable column instead of changing
  the rule.

## Reproduce

```bash
cd bench && npm ci
node wallet.mjs mint-usdc 1      # test USDC is open-mint on Sepolia; needs a little Sepolia ETH
node run.mjs --dry-run && node run.mjs
python3 score.py
```
