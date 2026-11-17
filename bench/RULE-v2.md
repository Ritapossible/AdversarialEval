# Benchmark rule v2 (pre-registered before any round-2 call)

Round 1 (`RULE.md`, 7 cases) was a pilot. This rule replaces it for rounds 2 and later. It is
committed before the first round-2 call; any change afterwards is a dated amendment at the end,
and the pre-change numbers stay published.

## Question

On `SECURITY_REVIEW_GENERAL` (testnet), what does a **verified correct** answer cost a buyer, per
miner and on the default route? Does the node's ranking order miners the way verified correctness
does?

## Cases (`cases-v2.json`, built by `make_cases_v2.py`)

Selection follows a fixed rule; no miner answer is looked at. Ground truth is frozen at build time.

| Kind | Count | Ground truth |
|---|---:|---|
| package, last affected | 12 | 6 ecosystems (PyPI, npm, Maven, Go, crates.io, RubyGems) × 2 packages. The highest affected stable version in the package's newest fixed OSV advisory. OSV lists ≥ 1 vuln. |
| package, latest clean | 12 | The same packages' default (latest stable) release. OSV lists 0 vulns. |
| code, vulnerable | 6 | One snippet per CWE: 89, 79, 22, 78, 502, 916. Judged by construction. |
| code, fixed | 6 | The same snippets with the flaw fixed. |
| unknown | 2 | A package that does not exist, and a version that does not exist. |
| format probe | 8 | The first 4 affected package cases restated twice: as plain text, and as a question. |

## Calls

- **Targets:**
  - every miner that takes a canonical request at the start of the round, re-checked with
    `tools/miner_audit.py` and recorded;
  - the auto-routed ask.
- **Request:** `{"intent":"SECURITY_REVIEW_GENERAL","params":{"target": ...}}`.
- **One attempt per (case, target), no retries.** A restart never repays a recorded pair.
- **Rounds:** 2, 3 and 4, on three different UTC days. Each round re-sends the same cases.
- **Payment:** x402 `exact`, Ethereum Sepolia test USDC, from a testnet-only wallet. Cap per
  round: (cases × targets) calls.

## Grading (frozen)

The answer is the delivered `result`. Its fields are `verdict` (one of `Secure`, `Needs changes`,
`Insecure`), `vulnerability_count` and `issues`.

| Case | Correct when | Wrong when |
|---|---|---|
| affected | the verdict is `Insecure` or `Needs changes`, **and** the count is ≥ 1 | any other valid verdict, or a count of 0 |
| clean package | the verdict is `Secure` **and** the count is 0 | `Insecure` / `Needs changes`, or a count of ≥ 1 |
| fixed code | the verdict is not `Insecure` **and** the count is 0 (also reported strict: `Secure` only) | `Insecure`, or a count of ≥ 1 |
| unknown | not graded for correctness. Reported as `abstained` (an error, or the miner says the package or version is unknown), `confident clean` (`Secure` with 0), or `invented` (any vulnerability listed) | |

**No answer:** a non-200 response, a timeout, or a missing or invalid `verdict`, whatever the
other fields say. The intent's `verdict` is the field a buyer's machine acts on.

Secondary measures, reported but not counted as correct:
- **ID match:** on affected package cases, at least one OSV id or alias appears in `issues`.
- **Count match:** on package cases, `vulnerability_count` equals the OSV count.

## Measures (per target, per round, and pooled over rounds)

- **Accuracy** on the 36 answerable cases (packages and code; format probes reported separately),
  with a Wilson 95% interval.
- **Buyer cost per verified correct answer** = USDC charged ÷ correct answers.
  - Charged = delivered answers with a receipt, **plus** calls whose response carries a successful
    settlement (`PAYMENT-RESPONSE`) without delivery.
  - The receipt-only cost is reported too.
  - A 95% interval from 10,000 bootstrap resamples of cases.
- **Delivery:** the share of calls that returned 200, and the share of those with a valid
  `verdict`.
- **Latency:** median and 90th percentile `duration_ms` of delivered answers.
- **Rank agreement:** Kendall's τ between the node's rank (at the round's start) and accuracy, over
  ranked miners.
- **Stability:** for each miner, the spread of accuracy across rounds.
- **Format sensitivity:** for each miner, agreement between the purl form and the two restated
  forms.

## Baselines

- **Free OSV lookup:** `bench/osv_baseline.py`, a deterministic script on package cases. It
  answers `Insecure` / count when OSV lists vulns, `Secure` / 0 when it lists none, and abstains on
  code. It costs $0, so it is the bar a paid answer has to beat on packages.
- **Constant answers:** always `Insecure` with count 1, and always `Secure` with count 0.

## Limits stated now

- 36 answerable cases give intervals about ±15 points at mid accuracy. Read differences inside the
  intervals as ties.
- Code ground truth is by construction. A reviewer may reasonably flag extra concerns on a fixed
  snippet, which the "fixed code" rule partly allows for.
- Testnet only, test USDC, a single payer wallet.

## Amendments

**1 (2026-11-16, after round 2).** Two corrections, both decided before round 3.

- **Charges that left no trace in the response.** The pre-registered charge measure (receipts plus
  settlement headers) under-counts. On-chain, the payer made 560 transfers of $0.01 during round 2
  for 598 calls. The 38 calls refused before payment (`503 could not route`) are the only unpaid ones;
  timeouts (`504`, or no response within 90 s) were charged without any header saying so.
  - From round 2 on, both measures are reported: the pre-registered one, and the
    **on-chain-reconciled** one (every call except a 503 is charged).
  - The reconciliation is checked by counting the payer's USDC `Transfer` events for each round.
- **Bootstrap scope.** Implementing the interval exposed a bug: it resampled only the 36 answerable
  cases, while the cost in the ratio covers all 46 called cases. That put some point estimates
  outside their own intervals. The interval now resamples all called cases, matching the ratio
  defined above, with a regression test in `tests/test_bench.py`.
- **Wilson bounds** are clamped to [0, 1]. Floating-point rounding had printed `-0%`.

**2 (2026-11-17, before any valid round-3 call).** Telegraph changed its payment layer between
rounds. The Sepolia asset moved from the open-mint test USDC (`0xcc19…Ae17`) to Circle's USDC
(`0x1c7D…7238`), paid to a new contract (`0x72a7…a08b`).
- The first round-3 attempt (15:06 UTC) reached no miner. Our client, pinned to the old asset,
  refused to pay on 794 calls, and nothing was charged.
- That attempt is **void**, kept in `bench/out/round-3-void-payment-migration/`, and not scored.
- The runner now pays in whichever of the two Sepolia USDC assets the node offers, with the same
  $0.02 per-payment cap.
- Round 3 is re-run once the payer holds the new asset. Rounds stay on different UTC days, so round 4
  moves to the next free day if needed.
