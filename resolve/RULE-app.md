# Polymarket markets through the app (Dependency.Guard + Anjoman): frozen rule (28 Nov 2026)

Committed before any paid call in this run. These are the same 24 real Polymarket markets as
`RULE-polymarket.md` (`polymarket_cases.json`, truth = Polymarket's final resolution). This time
they are run the way the listed app runs: paid through **Anjoman**, with the decision report written
by the **Dependency.Guard Mind** (`38266542-f36b-1410-8467-00039ce7df11`).

## Route

`mind/connector/markets.mjs`:
1. **One paid answer per market:** `EVENT_OUTCOME_RESOLUTION_GENERAL` from Telegraph's ranked route
   through Anjoman (`/engine/ask`), with the market's question text. No second miner is bought.
2. **A free check** (`resolve/check.py`) against the source the market's rules name. For the 6
   crypto markets that is Binance 1-minute candles; the other 18 name no machine-readable source.
3. **A decision:**
   - **SETTLE YES or SETTLE NO** from the named source. A paid answer that disagrees is overruled
     and recorded as a dispute caught.
   - **HOLD for a person** when the rules name no machine-readable source; the paid answer is kept
     as a lead.
   - **Never settle on a paid answer alone.**
4. **The Mind gets structured evidence only** (outcome, whether sources were cited, our check, cost)
   and replies with the settlement report. Miners' free text is never passed on.

## Measures

- The connector's decisions against the truth: wrong settlements (the headline), correct
  settlements, and markets held for a person.
- The paid answers alone against the truth, with how often they gave an outcome at all.
- Whether the Mind's report keeps to the evidence. Any overrule it proposes is recorded word for
  word.
- Spend: from the Anjoman receipts and the change in the escrow balance. Spending cap: $0.40.

## Limits

- 24 markets, one day, testnet.
- Anjoman's ranked route may send these questions to different miners than the Solana run did.

## Amendment 1 (28 Nov, after the first paid asks, before any decision was scored)

1. **The first two attempts failed with 401 and cost nothing.** I started the connector without
   `NODE_USE_ENV_PROXY=1`, so Node's `fetch` bypassed the session proxy and sent the asks without
   the Anjoman key.
2. **The cap was too low for this route.** The third attempt worked, but through Anjoman each
   routed ask cost $0.02 to $0.03, not the $0.01 we paid per call directly on Solana. At that
   price the $0.40 cap would stop after about 16 of the 24 markets.
3. **What I did:** stopped after 2 paid asks ($0.05). All three attempts are kept in
   `mind/evidence/aborted/`.
4. **The change:** the spending cap is now **$1.00**, and the run restarts from the first market.
   Nothing else changes. The 2 discarded paid asks are reported with the costs.
