# Real Polymarket markets through the app: Anjoman + the Dependency.Guard Mind (2026-11-28)

The same 24 real, resolved Polymarket markets as `2026-11-28-polymarket-resolution.md`, run the
way the listed app runs:
- each Telegraph answer paid through **Anjoman**;
- a free check against the source each market's rules name;
- a decision;
- the settlement report written by the **Dependency.Guard Mind**
  (`38266542-f36b-1410-8467-00039ce7df11`).

**Rule:** pre-registered in `resolve/RULE-app.md` (`0ea3567`), with one amendment before the run
(`c5f8a99`: the cap was raised to $1.00 after the first asks cost $0.02 to $0.04 each). **Run:**
`mind/evidence/2026-11-28T10-41-49-223Z.markets.json` (every ask, check, decision, receipt, and the
message sent to the Mind with its reply). **Truth:** Polymarket's final resolution.

## Result

| | Count | Against Polymarket's resolution |
|---|---|---|
| SETTLE NO, from Binance 1-minute candles (the crypto markets) | 6 | **6 correct** |
| SETTLE YES or NO from a paid answer alone | 0 | never allowed by the rule |
| HOLD for a person (no machine-readable source in the rules) | 18 | not settled |
| **Wrong settlements** | **0** | |

**Telegraph's paid answers through Anjoman gave an outcome for 1 of 24 markets.** All answers came
from LiveCert:
- 16 answered "unresolved";
- 7 timed out (HTTP 504);
- 1 answered "no" for "Will Manchester United win on 2026-11-08?", which was correct. The app still
  held that market, because a single paid answer isn't a source.

## The Mind's report (excerpt; the full reply is in the run file)

The Mind kept to the evidence: six SETTLE NO, eighteen HOLD, "I won't settle a market from a paid
answer, cited or not." It checked each number against its question, not just the label. It flagged
the two thin crypto calls for a person:
- "window low 62,006, $6 above the strike";
- "closest print 59,958, $42 below the floor".

It also made one recommendation we accept:

> $0.29 of the $0.44 went to markets whose rules name no machine-readable source. Under your own
> rule those answers can't settle anything, so that money bought nothing usable... the gate belongs
> on "does this market name a checkable source", not on the price of the answer.

One point where the Mind lacked context: it asked whether "BTC between $60,000 and $62,000 on
November 27" could be settled from one price. The market's rules resolve on the close of the single
1-minute candle at 12:00 ET, so one price does settle it. We sent the Mind the evidence, not the
rules text; the next version sends each market's resolution sentence too.

## Cost, reconciled with the Anjoman balance

| | USD |
|---|---|
| 17 answers with receipts | $0.44 |
| 7 asks that timed out (504), with no answer and no cost reported, but charged | $0.17 |
| **This run** | **$0.61** |
| Before the run: the 2 discarded paid asks (amendment) and one $0.01 test ask | $0.06 |

The escrow balance went from $5.33 to $4.66 ($0.67 unbilled), which matches the table exactly.

**Finding:** through Anjoman, a routed ask that times out can still be charged with no answer
delivered. Each answer cost $0.02 to $0.04, against $0.01 per call paid directly on Solana.

## What changes in the app (built after this run, 28 Nov)

1. **Done:** the connector reads each market's rules first and buys a paid answer only when the rules
   name a source it can check (`shouldAsk` in `mind/connector/markets.mjs`). That saves the $0.29
   the Mind pointed out. The old behaviour is still available with `--ask-all`.
2. **Done:** each market's resolution sentence now goes to the Mind with the evidence (`ruleSentence`).
3. **Already in place:** a timed-out ask is counted as possibly charged, and the balance check
   catches it.

Offline tests: `mind/connector/test/markets.test.mjs`. A dry run on two markets with no checkable
source bought nothing and spent $0.
