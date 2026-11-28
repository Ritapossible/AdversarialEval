# Settling real Polymarket markets with checked Telegraph answers (2026-11-28)

The follow-up to `2026-11-28-prediction-market-resolution.md`: the same test on **24 real,
already-resolved Polymarket markets**, picked by a fixed rule.

- **Rule:** pre-registered in `resolve/RULE-polymarket.md`, committed in `47a2aa8` before any paid
  call.
- **Markets:** `resolve/polymarket_cases.json`.
- **Data:** `bench/out/eventres-polymarket/`.

**Selection.** From Polymarket's public API, we took the 636 November markets that were Yes/No and
finally resolved (out of the 2,100 highest-volume closed markets). We kept one market per event, then
the top 6 by volume in each of crypto, sports, politics and world events. The 24 markets traded
**$180M** in total.

**Truth** is Polymarket's own final resolution (the UMA oracle outcome): 9 YES, 15 NO.

## Result

| Arm | Settled | Correct | Wrong settlements | Left for a person (volume) |
|---|---|---|---|---|
| A. Trust one answer (Telegraph's ranked route) | 6 | 6 | 0 | 18 markets ($156M) |
| B. Two independent providers agree | 1 | 1 | 0 | 23 |
| C. Resolution check | 6 | 6 | 0 | 18 markets ($174M) |

- **No answer settled a market on the wrong side.** On real markets the providers mostly declined
  to answer.
- **Telegraph's ranked route** (every answer from LiveCert) settled 6 of 24, with no sources cited.
- **The independent provider** (Takar) settled 1 of 24.
- **None of the 6 midterm election markets was settled by any paid answer,** although those results
  are public. Those markets traded $112M.
- **The check settled all 6 crypto markets correctly** by reading Binance 1-minute candles over the
  exact ET window each market's rules name. That's an independent recomputation, and it agreed
  with Polymarket every time, including two near misses:
  - **"Will Bitcoin dip to $62,000 November 9-15?":** NO. The lowest Binance price in the window was
    **$62,006**, $6 above the line. Reading the wrong exchange or time zone gives the wrong answer:
    Coinbase's UTC daily low on 15 Nov was $61,946.
  - **"Will Bitcoin be between $60,000 and $62,000 on November 27?":** NO. The noon-ET candle closed
    at **$59,958**.
  - Telegraph's answers settled only 1 of these 6 crypto markets.
- **The two methods settled different markets.** The ranked answer's 6 were 1 crypto, 3 sports and
  2 world. The check's 6 were all crypto. Neither covered politics.

## Read with the written-market test

On the 24 markets we wrote, with harder fine print, the same providers answered more often and got
1 in 3 of their settlements wrong. On these real markets they answered less and got none wrong.
Together:
- **Paid answers alone are either missing or, on fine print, unreliable.** Neither is enough to move
  money.
- **Reading the source the market's rules name is what settles markets correctly** when that source
  is machine-readable: crypto prices, official league and agency data.
- **For the rest** (elections, world events), the providers in this test did not give cited answers
  that agree, so the check leaves those markets for a person rather than guess.

## Cost

All 48 calls were paid in devnet USDC on Solana (x402) and all 48 are confirmed on-chain: **$0.48**.

## Limits

- 24 markets, picked by volume, one day, testnet.
- Results are for the two providers that answered; the ranked route sent every question to one
  miner.
- C's crypto contracts were transcribed by hand from each market's published rules before any paid
  call (`resolve/polymarket.py`).
- Truth is Polymarket's resolution. Binance agreed with it on all 6 crypto markets.
