# Solana use case 3 test: rule (frozen before any paid call)

Telegraph's Solana use case 3, Verified Intelligence Economy (Telegraph x Pay.sh): an agent buys
specialist intelligence chosen by independent evaluation, paid on Solana, compared with a frontier
model and with direct paid API selection, measuring correctness, cost, latency and task fulfilment.
Plan: `docs/SOLANA_USE_CASE_3.md`. This file, `cases.json` and the runner are committed before the
first paid call; every run records the commit it ran on.

## The task

An agent is about to approve dependencies for a Solana project. For each package version it must
decide PASS (safe to install), BLOCK (known malicious or vulnerable) or FLAG (can't be confirmed,
e.g. the version was never published). **Task fulfilled** = every case gets a correct decision.

## Cases (`cases.json`, built by `make_cases.py`; truth read 2026-11-24, see the file)

21 cases chosen by rule, harder than the first Solana set (where every arm got every real version
right):

| Type | n | What makes it hard |
|---|---|---|
| malicious | 4 | look-alikes of Solana packages that were real malware (OSV `MAL-`), since removed from npm |
| withdrawn | 1 | `@solana/web3.js` 1.95.6, the other hijacked release |
| latest | 2 | the newest release is still affected (`bigint-buffer`, `elliptic`), where "latest = safe" fails |
| recent | 4 | advisories published May to Oct 2026, likely after a frontier model's training data |
| clean | 7 | current releases with no advisory, including the clean twins of the recent cases |
| unknown | 3 | plausible Solana package names that were never published |

Truth: affected (BLOCK correct), clean (PASS correct), unknown (FLAG or no decision correct; a
confident PASS or BLOCK is wrong). OSV, deps.dev and npm's registry history are the sources.

## Arms

| Arm | Provider choice | Payment | Verification |
|---|---|---|---|
| A. Frontier model alone | none: the Dependency.Guard Mind, told not to use Telegraph, Anjoman, Verified Ask or its watchlist | Minds credits | none |
| B. Direct paid API selection | the first miner in the node's public listing for `SECURITY_REVIEW_GENERAL` (`/api/miners`, read 2026-11-24): **TxLens, id 9002**, asked directly | x402 on Solana devnet, $0.01 | none, verdict trusted |
| C. Evaluated specialist | Telegraph's ranked route (`/engine/v1/ask`) | x402 on Solana devnet, $0.01 | none, verdict trusted |
| D. Our product | C's answer | as C, plus at most one re-ask | Verified Ask; one re-ask of the benchmark's best miner (a1-preflight, id 20260828) only if proven wrong or unusable |

B, C and D run in one pass of `bench/solana_run.mjs`. Every Telegraph call is paid in Circle's
devnet USDC with x402 v2 "exact" on Solana devnet, the payment protocol Pay.sh uses; each call's
Solana transaction signature is recorded and checked on-chain with `bench/solana_reconcile.py`.
Cap: $1.00. One attempt per case and arm; a refused or failed call counts as no answer.

## Grading (frozen)

`mind/solana-test-v2/score.py`: correct, missed vulnerabilities (PASS on affected), false alarms
(BLOCK on clean), unknown versions decided confidently, no answer, task fulfilled (all 21 correct),
cost (on-chain), latency (median and total per arm), each with Wilson 95% intervals where it is a
rate. Arm B and C act on the answer's `verdict` (Secure = PASS; Insecure or Needs changes = BLOCK;
anything else = no decision).

## Limits stated now

- 21 cases; differences of one or two are noise.
- OSV is the truth; clean versions are clean as of the read time.
- Testnet; routing and miners change daily; one run per arm.
- Arm B's rule ("first listed") is one reasonable way an agent picks from a listing, not the only one.
- Pay.sh's own CLI keeps keys in the OS keychain and documents no devnet mode, so the run pays with
  the x402 Solana client directly (`@x402/svm`), the same protocol, from a burner devnet wallet.
