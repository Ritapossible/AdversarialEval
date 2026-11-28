# Real Polymarket markets: frozen rule (28 Nov 2026)

Committed before any paid call on these markets. It is the same test as `RULE.md`, run on 24 real,
already-resolved Polymarket markets instead of markets we wrote.

## Markets (selected by rule, `polymarket.py`)

- **Source:** Polymarket's public Gamma API.
- **Pool:** closed markets ending 1 to 28 Nov 2026 (UTC), the first 2,100 by volume (the API's
  paging limit).
- **Eligible:** Yes/No outcomes, UMA status `resolved`, final prices exactly 1/0. That leaves 636.
- **One per event:** at most one market per event, the highest-volume one.
- **Categories** use fixed patterns: crypto, politics, sports, and world (everything else).
- **Picked:** the top 6 by volume in each category, 24 markets in all (9 YES, 15 NO). All four
  groups have 6.

`polymarket_cases.json` holds each market's question, full rules, end date and volume.

## Truth

**Polymarket's final resolution** (the UMA oracle outcome, final prices 1/0), saved with its
evidence. We do not re-decide what Polymarket settled.

## Telegraph calls, arms and measures

These are the same as `RULE.md`:
- intent `EVENT_OUTCOME_RESOLUTION_GENERAL`, with `event` set to the question plus
  " (Polymarket market; resolves per its published rules)";
- the first answer from the ranked route;
- the second from the first of `20261117`, `4433`, `59003` whose payout address differs from the
  first answer's miner;
- paid in devnet USDC on Solana; spending cap $0.75.

The arms:
- **A.** Trust the ranked answer.
- **B.** Settle only when two independent answers agree.
- **C. Resolution check.**
  - **Crypto markets:** C resolves from Binance 1-minute candles over the exact ET window the
    rules name. The contracts were transcribed by hand from each market's published rules and are
    in `polymarket.py`. This is an independent recomputation, not the truth's own data, so C can
    disagree with Polymarket.
  - **Every other market:** C settles only when both independent answers agree on yes/no and each
    cites at least one source URL. Otherwise the market is left for a person.

## Things to watch, stated in advance

- **Circularity:** these markets are already resolved on Polymarket's public pages, so a provider
  can copy Polymarket's own result. We record when an answer cites Polymarket. An answer that
  copies Polymarket is no help in settling a Polymarket market before Polymarket does.
- **Near misses:** two crypto markets are decided by $6 (the lowest BTC price was $62,006 against a
  $62,000 line) and $42 (a $59,958 close against a $60,000 to $62,000 range). A check on the wrong
  exchange or time zone gets them wrong: Coinbase's UTC daily low on 15 Nov was $61,946.
- 24 markets, one day, testnet.
