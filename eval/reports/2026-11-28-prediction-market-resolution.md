# Settling prediction markets on paid AI answers: a checked test, paid on Solana (2026-11-28)

The Solana use case Telegraph asked for: resolving prediction markets with Telegraph's
`EVENT_OUTCOME_RESOLUTION_GENERAL` intent. A market has to settle, YES paying one side and NO the
other. How often would a paid answer send the money to the wrong side? Does a second, independent
provider fix it? Or does it take checking the official source the market names?

**Pre-registered** in `resolve/RULE.md`, committed in `ca0fa48` before any paid call on these
markets. The only earlier calls were a 2-call preflight on a market outside the test. Data is in
`bench/out/eventres/`; markets, truth and its evidence are in `resolve/cases.json`.

**Markets.** 24 already-settled or not-yet-settleable markets:
- 9 crypto prices (Coinbase daily candles, UTC);
- 6 NHL games (the NHL's official API);
- 3 World Series (MLB's official Stats API);
- 3 earthquakes (USGS);
- 3 that can't be settled: two future events, and one with no defined criterion.

They're chosen where real markets are hard:
- "close above" vs "trade above";
- a shootout win vs a win "in regulation";
- magnitude "7.0 or greater" vs "greater than 7.0" when the largest earthquake was exactly 7.0;
- near misses of $106 and $0.11.

**Truth** was computed by code from those official sources and saved with the raw data: 12 YES,
9 NO, 3 not settleable.

## Result

| Arm | Settles on | Correct (of 24) | Wilson 95% | **Wrong settlements** | Left for a person |
|---|---|---|---|---|---|
| A. Trust one answer | Telegraph's ranked answer | 9 | 21–57% | **3** | 12 |
| B. Two independent providers | both answers agree (different payout addresses) | 6 | 12–45% | **1** | 17 |
| C. Resolution check | the official source named in the contract; otherwise two agreeing answers that each cite a source | **21** | 69–96% | **0** | 3 |

- **Each provider on its own was wrong in 1 of every 3 markets it settled.** The ranked route
  (every answer from LiveCert) settled 9 and got 3 wrong. The independent provider (Takar Outcome
  Resolver) also settled 9 and got 3 wrong.
- **Agreement isn't proof.** Both providers said St. Louis beat Edmonton **in regulation**. They
  won in a shootout. Arm B settled that market wrongly.
- **The check never settled against the official source.** It overruled 2 paid answers the source
  contradicts (St. Louis "in regulation" and Pittsburgh "scored"). It left the 3 World Series
  markets for a person because no two cited answers agreed. It left all 3 unsettleable markets
  unsettled.

## The wrong answers, with the source that settles them

| Market | Truth (official source) | Telegraph answers |
|---|---|---|
| Did St. Louis beat Edmonton **in regulation** on Nov 22? | **NO**: 5-4 in a shootout ([NHL](https://api-web.nhle.com/v1/score/2026-11-22), last period `SO`) | LiveCert **yes**; Takar **yes** (citing ESPN) |
| Did Pittsburgh score at least one goal vs Dallas on Nov 22? | **NO**: lost 0-1 ([NHL](https://api-web.nhle.com/v1/score/2026-11-22)) | LiveCert **yes**; Takar unresolved |
| Did the Rays win at least one game of the 2026 World Series? | **YES**: won game 4, 4-3 ([MLB](https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=W&season=2026)) | LiveCert **no**; Takar unresolved |
| Did BTC **trade** above $81,000 at any time on Nov 4? | **YES**: high $81,130.79, close $80,428.31 (Coinbase) | LiveCert unresolved; Takar **no** |
| Did BTC **trade** below $56,000 at any time on Nov 21? | **YES**: low $55,106, close $60,086 (Coinbase) | LiveCert unresolved; Takar **no** |

The Bitcoin errors are the close-vs-trade trap. On both days the price crossed the line during the
day but closed on the other side, and Takar answered as if the question were about the close.

## What else we found

- **LiveCert answered all 24 with no sources and no winner field.** An outcome you can't trace is
  hard to accept for a payout.
- **Takar's "sources" for crypto markets are links to other Telegraph answers** (`/engine/v1/signal/…`),
  not to Coinbase. A different payout address doesn't guarantee independent evidence: one provider's
  answer can be built on another's.
- **The crypto markets were the weakest.** LiveCert left all 9 unresolved. Takar settled 5, all
  NO, and 2 of those were wrong. Neither provider settled any of the 5 crypto markets whose truth is
  YES. Each market names its exact source (Coinbase BTC-USD daily candle, UTC), and one free API
  call settles it, which is what arm C does.
- **On independence:** 42 miners are listed for this intent, behind 10 payout addresses, and one
  address runs 26 of them (several of those read Polymarket's and Kalshi's own results, which is
  circular when the job is resolving a market).

## Cost and latency

All 48 calls were paid in devnet USDC on Solana (x402) and all 48 are confirmed on-chain: **$0.48**
(`onchain.json`), plus $0.02 for the preflight. Nothing was paid without a recorded answer.

| | A | B | C |
|---|---|---|---|
| Paid calls per market | 1 | 2 | 1 or 2 (2 only when the contract names no source) |
| Median wait for a paid answer | 14 s | 20 s for the second | about 1 s for the free source read |

## Limits (stated in advance)

- 24 markets, one day, testnet; the markets are chosen to be hard.
- On markets whose contract names a machine-readable source, C reads the same official source as
  the truth, so it is right there by construction, as long as its resolver is correct. What this
  measures is how often paid answers alone would settle money wrongly. C's own judgment is tested
  only on the 5 markets whose contract names no source; it settled none of them wrongly and left the
  3 resolvable ones for a person.
- Results are for the two providers that answered (the ranked route sent every question to
  LiveCert). Other miners may do better.

## Reproduce

```
python resolve/make_cases.py            # truth from official sources (already frozen in cases.json)
python resolve/run.py jobs1 && node bench/telegraph_jobs.mjs --jobs bench/out/eventres/jobs1.json --out bench/out/eventres
python resolve/run.py jobs2 && node bench/telegraph_jobs.mjs --jobs bench/out/eventres/jobs2.json --out bench/out/eventres
python bench/solana_reconcile.py bench/out/eventres
python resolve/run.py score
```
