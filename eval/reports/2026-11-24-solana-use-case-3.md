# Solana use case 3: verified intelligence for Solana agents, paid on Solana (2026-11-24)

Telegraph's Solana use case 3, Verified Intelligence Economy (Telegraph x Pay.sh): an agent buys
specialist intelligence, chosen by independent evaluation rather than by an API listing, pays for
it on Solana, and is compared with a frontier model and with direct paid API selection on
correctness, cost, latency and task fulfilment.

Pre-registered at commit `ee02304` (18:11:25 UTC): rule `mind/solana-test-v2/RULE.md`, cases
`mind/solana-test-v2/cases.json` (built by `make_cases.py`), runner `bench/solana_run.mjs`. The paid
run started after that commit and records it in `bench/out/solana-v2/decisions.json`.

## The task

An agent is approving dependencies for a Solana project: PASS (install), BLOCK (malicious or
vulnerable) or FLAG (can't be confirmed). 21 cases, chosen by rule and harder than our first Solana
set (where every arm got every real version right):

| Type | n | Cases |
|---|---|---|
| malicious | 4 | `solana-web3.js`, `solana-web3`, `solana-transaction-toolkit`, `solana-stable-web-huks`: look-alikes of Solana packages that were real malware (OSV `MAL-`), since removed from npm |
| withdrawn | 1 | `@solana/web3.js` 1.95.6, the other hijacked release (key theft) |
| latest | 2 | `bigint-buffer` 1.1.5, `elliptic` 6.6.1: the newest release is still affected |
| recent | 4 | `anchor-lang`, `tokio`, `rustls`, `ws`: advisories published May to Oct 2026 |
| clean | 7 | current releases with no advisory (incl. the recent cases' clean twins) |
| unknown | 3 | `solana-web3-js`, `solana-spl-token`, `solana-keypair`: names never published |

## Payment on Solana (checked on-chain)

Every Telegraph call was paid per request in Circle's devnet USDC with x402 v2 "exact" on Solana
devnet, the payment protocol Pay.sh uses, from wallet `AeM9DFuWEN5jpCL4BA3q9byjCsEwyXeWWmV6kx1C6NtE`
to the node's Solana payee `G53EbeTZ…8bix`; the facilitator paid the network fees.
`bench/solana_reconcile.py` fetched every transaction from Solana devnet:

| | |
|---|---|
| Calls | 57 (21 listing, 21 ranked, 15 re-asks) |
| Confirmed Solana payments | 55, each 0.01 USDC, all succeeded (54 recorded by the run + 1 that settled while its answer was lost in transit, found on-chain and charged to its arm) |
| Unpaid failures | 2 (the request failed before payment) |
| Total | **0.55 USDC** (plus 0.03 for the preflight) |
| Wallet | 20.00 from the faucet, 19.42 after: matches 0.55 + 0.03 to the cent |

Each answer also carries Telegraph's own receipt (`x-telegraph-receipt`) naming the Solana payer and
`rail: x402`. Signatures, slots and amounts: `bench/out/solana-v2/onchain.json`; any one can be
opened at `https://explorer.solana.com/tx/<signature>?cluster=devnet`.

Preflight (before the run, on `minimist@1.2.8`, outside the 21 cases): listing, ranked and re-ask
paths each paid and confirmed on-chain (`bench/out/solana-v2-preflight/`).

## Result

| Arm | Correct (of 21) | 95% Wilson | Malware or hijacked release approved | Missed vulnerabilities | False alarms | Never-published name decided | Paid on Solana | Median latency per package |
|---|---|---|---|---|---|---|---|---|
| B. First provider in the listing (TxLens), trusted | 8 | 21 to 59% | 2 | 4 | 2 | 3 of 3 | $0.20 | 9.2 s |
| C. Telegraph's ranked route, trusted | 6 | 14 to 50% | **5** | 8 | 2 | 3 of 3 | $0.21 | 8.3 s |
| **D. Ranked + Verified Ask (Dependency.Guard)** | **20** | **77 to 99%** | **0** | **0** | **0** | **0** | **$0.35** | 14.0 s |
| A. Frontier model alone (the Mind, own knowledge and search) | 21 | 85 to 100% | 0 | 0 | 0 | 0 | $0 (Minds credits) | 81 s for all 21 |

Task fulfilled (all 21 right): only A. D's one miss is a FLAG, not a wrong approval: on
`solana-transaction-toolkit` (malware) the ranked answer said "Secure", Verified Ask contradicted it
(OSV lists MAL-2025-41), and the one allowed re-ask failed in transit before payment, so D sent the
package to a person instead of guessing. Graded strictly, that is "no decision".

Cost per correct decision: D $0.0175, B $0.025, C $0.035.

## What the paid answers got wrong

- **The ranked route followed one provider.** 19 of 21 questions went to the same miner (LiveCert),
  which answered "Secure" on all 4 malware look-alikes, on the hijacked `@solana/web3.js` 1.95.6,
  on 3 of the 4 recent advisories and on all 3 names that were never published. Trusting it, an
  agent would have installed key-stealing malware 5 times out of 5.
- **Listing order is not quality.** The first listed provider was right 8 times, also approved 2
  malware packages, and gave confident BLOCKs on names that don't exist.
- **Verified Ask turned the same paid answers into safe decisions**: of the 21 ranked answers it
  verified 6, contradicted 13 and found 2 unusable. The 15 re-asks of the benchmark's best miner
  gave 11 verified decisions (8 BLOCK, 3 PASS); the other 4 became FLAG (the 3 never-published
  names, correctly, and one malware package). Every malware package and hijacked release ended
  BLOCK or FLAG; no clean package was blocked.

## What this says

- Paying for intelligence on Solana works per request today: 55 independent payments, every one
  confirmed on-chain and matched to an answer and a Telegraph receipt.
- Choosing a provider by listing order, or trusting the ranked route blindly, is unsafe on hard
  cases: 6 to 8 of 21 right, with malware approved.
- An independent free check plus one evaluated re-ask fixes that: 20 of 21 right, nothing unsafe
  approved, for $0.35 and about 14 s per package.
- The frontier model alone (Dependency.Guard with its own web search) got all 21 right, as on our
  earlier sets. Its answers carry no receipts or independent check; the product's value is that
  every decision is evidence-backed and paid answers are never trusted unchecked. We don't claim
  the paid route beats a strong model with search on known advisories.

## Limits

- 21 cases; one or two differences are noise (see the intervals).
- OSV is the truth; clean versions are clean as of 24 Nov.
- Testnet: devnet USDC and testnet miners; one run per arm; routing changes daily.
- Arm B's rule ("first listed") is one reasonable listing choice, not the only one.
- Pay.sh's own CLI keeps keys in the OS keychain and documents no devnet mode, so the run pays with
  the x402 Solana client (`@x402/svm`), the same protocol, from a burner devnet wallet.

## Reproduce

```bash
SSL_CERT_FILE=... python mind/solana-test-v2/make_cases.py        # truth changes over time; the committed file is the reference
node bench/solana_run.mjs --cases mind/solana-test-v2/cases.json --out bench/out/solana-v2 --max-spend 1.00
python bench/solana_reconcile.py bench/out/solana-v2              # every payment checked on Solana devnet
python mind/solana-test-v2/score.py bench/out/solana-v2 mind/evidence/2026-11-24-solana-v2-mind-alone.json
```
