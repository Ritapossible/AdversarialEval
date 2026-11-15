# Benchmark rule (frozen before the first paid call)

Mission 10 (Model Economy), route 1: **cost per verified correct answer** on `SECURITY_REVIEW_GENERAL`,
testnet. This rule is committed before any paid request is made and is not changed afterwards;
any later change is a dated amendment below.

## Set

- Cases: the 7 in `cases.json`, with ground truth frozen from OSV (`make_cases.py`):
  - 2 affected package versions, 2 versions with no OSV record;
  - 1 package that does not exist;
  - 2 code snippets: SQL built by string concatenation, and the same query parameterised.
- Each case goes to:
  - every miner that took a canonical request in the 2026-11-15 audit (12), by `POST /engine/v1/ask/{minerId}`;
  - once to the auto-routed `POST /engine/v1/ask`, which is what a buyer gets by default.
- Request: `{"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": <case target>}}`. One
  attempt per pair, no retries, so first-pass success is measured as it is.
- Payment: x402 `exact` on Ethereum Sepolia (test USDC), from a fresh testnet-only wallet. Hard cap:
  91 paid calls ($0.91 at $0.01 each).

## Scoring (per answer)

The answer is the delivered `result` (`verdict`, `vulnerability_count`, `issues`).

| Case | Verified correct when |
|---|---|
| affected (package or code) | `verdict` is `Insecure` or `Needs changes` **and** `vulnerability_count` ≥ 1 |
| not affected (package or code) | `verdict` is `Secure` **and** `vulnerability_count` = 0 |
| unknown package | the miner abstains or errors, or says it can't find the package. A confident `Secure` with 0 is **unverifiable**, not correct. Listing vulnerabilities is **wrong**. |

Each result is one of: **correct**, **wrong**, **no answer**, or **unverifiable**.
- **No answer:** a non-200 response, a timeout, or a missing or invalid `verdict`.
- **Unverifiable:** only for the unknown package, as defined above.

Secondary, reported but not part of "correct":
- whether `vulnerability_count` equals the OSV count, for package cases;
- whether `issues` contains at least one OSV id or an alias of one.

## Measures

- **Cost per verified correct answer:** USDC actually paid to that miner (from receipts) ÷ correct
  answers. Shown as "n/a" with 0 correct.
- **First-pass success:** share of the 7 calls that returned a delivered answer.
- **Latency:** median and max `duration_ms` (7 calls is too few for a real p95).
- **Comparison with the network:** the node's rank for each miner next to its correct count, and the
  auto-routed answer per case.
- **Baselines:**
  - always "Insecure" with count 1;
  - always "Secure" with count 0.

  On this set each baseline scores 3 of 7 (the unknown case counts against both).

## Limits stated up front

- 7 cases is a small sample: a ranking of miners from it is indicative, not conclusive.
- OSV is the ground truth for packages. A miner using another database may count differently, which
  is why the count only has to be ≥ 1 or 0.
- The code cases are judged by construction (CWE-89), not by an external record.
