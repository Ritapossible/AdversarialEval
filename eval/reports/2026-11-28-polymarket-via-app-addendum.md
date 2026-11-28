# Addendum to `2026-11-28-polymarket-via-app.md`: what changed in the app (28 Nov)

The report above is signed and anchored on Solana, so it is left unchanged. This addendum records
what was built after it, following the Mind's suggestion in that run.

1. **Buy a paid answer only when it can count.** The connector reads each market's rules first and
   buys an answer only when the rules name a source it can check (`shouldAsk` in
   `mind/connector/markets.mjs`, commit `f241ea1`). That saves the $0.29 the Mind pointed out. The
   old behaviour is still available with `--ask-all`.
2. **Send the rules to the Mind.** Each market's resolution sentence now goes to the Mind with the
   evidence (`ruleSentence`), so it no longer has to guess how a market settles. In the run, it
   questioned whether one price could settle a range market whose rules use a single noon candle.
3. **Already in place:** a timed-out ask is counted as possibly charged, and the balance check
   catches it.

Checks: offline tests in `mind/connector/test/markets.test.mjs` (11 pass). A dry run on two
markets with no checkable source bought nothing and spent $0 (balance $4.66 before and after).
