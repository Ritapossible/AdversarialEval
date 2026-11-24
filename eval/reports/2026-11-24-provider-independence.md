# How many independent providers sit behind the security miners? (2026-11-24)

Telegraph's marketplace lists many miners for `SECURITY_REVIEW_GENERAL`. A buyer comparing
"competing providers" should know how many operators are really competing. The node's public
listing (`/api/miners?intent=SECURITY_REVIEW_GENERAL`) publishes each miner's `wallet_address` and
`fee_address`; miners paid to the same address are counted as one provider.

Method: `python tools/provider_independence.py --snapshot eval/reports/raw/2026-11-24-miners-security-review.json`
(snapshot read 2026-11-24T19:45:32+00:00; re-run offline with `--offline`).

## Result

| | |
|---|---|
| Miners listed for the intent | **37** |
| Distinct payout (fee) addresses | **13** (wallet addresses: 13) |
| Miners behind the two largest addresses | **18 + 8 = 26** (70% of the listing) |
| Providers with a single miner | 11 |

The two largest groups are families of thin wrappers over public sources: one address pays
18 miners named `secrev-*` (CIRCL, deps.dev, GHSA, NVD variants), the other 8
named `zk-*` or `codewire-*`.

## What our paid runs actually bought

Miners that answered in each of our paid runs, mapped to today's listing:

| Run | Miners that answered | Distinct providers |
|---|---|---|
| round-2 | 12 | 5 |
| round-3 | 33 | 10 |
| round-3-void-payment-migration | 17 | 8 |
| round-4 | 32 | 9 |
| solana-v2 | 4 | 4 |

In round 4, 32 "competing" miners came from 9 payout identities. In the Solana use case 3 run the
ranked route sent 19 of 21 questions to a single miner.

## Why it matters

- Ranking and routing treat each miner as an independent provider; when one operator runs 18 of
  them, a buyer's "second opinion" can come from the same source, and agreement between miners
  says less than it seems.
- For evaluators: independence should be measured by operator, not by miner count, before
  agreement or diversity is used as evidence.

## Limits

- Addresses are an upper bound on independence: one operator can use several addresses, and the
  listing can change. Two addresses never prove two teams.
- Our earlier rounds are mapped with today's listing; a miner's address may have changed since.
- Public listing data only; no private node data is used.
