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

None yet.
