# Prediction market resolution: frozen rule (28 Nov 2026)

Committed before any paid call on these markets. The only paid calls before this commit were a $0.02
preflight on a market outside the test (`bench/out/eventres-preflight/`). The commit that adds this
file is the pre-registration.

## Question

A prediction market has to settle: YES pays one side, NO pays the other. If it settles on a paid
AI answer, how often does money go to the wrong side? Does asking a second, independent provider
fix that? Or does it take checking against the official source the market names?

## Markets and truth

24 markets in `cases.json`, built by `make_cases.py`:
- 9 crypto price markets (Coinbase daily candles, UTC);
- 6 NHL games (the NHL's official API);
- 3 World Series markets (MLB's official Stats API);
- 3 earthquake markets (the USGS catalog);
- 3 that cannot be resolved: two are in the future, and one has no defined criterion.

They are chosen to test the fine print a real market depends on:
- "close above" vs "trade above";
- a win in a shootout vs a win "in regulation";
- magnitude "7.0 or greater" vs "greater than 7.0" when the largest earthquake was exactly 7.0;
- near misses of $106 and $0.11.

**Truth** is computed by code from the official source (`sources.py`) and saved with its evidence
in `cases.json`: 12 yes, 9 no, 3 unresolved. No model decides it.

## Telegraph calls (paid in devnet USDC on Solana, x402)

Intent `EVENT_OUTCOME_RESOLUTION_GENERAL`, parameter `event` set to the market's question text.
- **First answer:** Telegraph's ranked route (`/engine/v1/ask`), one call per market.
- **Second answer:** the first miner in this list whose payout address (`fee_address` in the node's
  listing) differs from the first answer's miner:
  1. `20261117` takar-outcome
  2. `4433` livecert
  3. `59003` event-poly-search

  One call per market. Miners sharing a payout address are not counted as independent (26 of the
  42 listed miners share one address; `eval/reports/raw/2026-11-28-miners-event-resolution.json`).

Spending cap: $0.75. Each answer's `outcome` field (`yes`, `no` or `unresolved`) is what counts.
An answer that is missing or unusable counts as `unresolved`.

## Arms (each settles YES, settles NO, or leaves the market unresolved)

- **A. Trust one answer.** Settle with the ranked answer's outcome.
- **B. Two independent providers.** Settle only when both answers give the same yes/no; otherwise
  leave it unresolved.
- **C. Resolution check.**
  - If the market's contract names a machine-readable source, C resolves from that source for free
    (`sources.resolve`) and settles with it, whatever Telegraph said. A disagreement is recorded as
    a dispute the check caught.
  - If the contract names no source (the World Series markets and the "crash" market), C settles
    only when both independent answers give the same yes/no and each cites at least one source URL.
    Otherwise it leaves the market unresolved for a person.

Disclosure: on markets with a machine-readable source, C reads the same official source as the truth,
so it is right by construction there, as long as its resolver is correct. What the test measures is
how often paid answers alone would settle money on the wrong side, and what C does on the markets it
cannot read for itself.

## Measures

Per arm, out of 24 markets:
- **wrong settlements:** settled YES or NO against the truth, including any settlement of a market
  whose truth is unresolved. Money goes to the wrong side.
- **correct:** matches the truth, including leaving an unresolvable market unresolved.
- **left unresolved** when the truth is yes or no. This is safe but slow, because a person has to
  decide.

Also: Wilson 95% intervals, cost reconciled on-chain with `bench/solana_reconcile.py`, and wall time.

## Limits stated in advance

- 24 markets, one day, testnet. The markets are chosen to be hard where real markets are hard.
- Miners can read public pages, including other prediction markets' own results; that is noted
  where an answer cites them.
- The NHL, MLB and USGS sources are official; Coinbase is the exchange the market names.
