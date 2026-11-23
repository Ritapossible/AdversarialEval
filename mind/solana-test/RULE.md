# Solana dependency test: rule (frozen before any paid call)

For Telegraph's Solana call (idea 1, verified intelligence for Solana AI agents): does
Dependency.Guard keep a Solana agent or app from shipping a known-bad dependency, with and
without Telegraph? Committed before the first paid call; each run records this file's commit.

## Cases (`cases.json`, built by `make_cases.py`; truth read 2026-11-23 07:41 UTC)

The Solana stack and what it pulls in: `@solana/web3.js` and its signature, HTTP and websocket
dependencies on npm (`secp256k1`, `ws`, `node-fetch`), and the crates Solana programs and SDKs
rely on (`ed25519-dalek`, `curve25519-dalek`, `borsh`).

Selection rule, applied by the script, not by hand:
- each candidate names a package and an affected version taken from a known advisory;
- the affected version must have at least one OSV advisory, and exist on the registry, unless the
  registry withdrew it (then it is kept and marked `withdrawn_from_registry`);
- its clean twin is the package's current default release on deps.dev, which must have none;
- a pair failing a check is dropped and listed in `dropped` (here: `elliptic`, whose current
  release 6.6.1 still has an advisory);
- two versions that were never published are added as "unknown" cases.

Result: 16 cases, 7 affected, 7 clean, 2 unknown. The key case is `@solana/web3.js` 1.95.7, one of
two hijacked releases that stole private keys (GHSA-jcxm-7wvp-g6p5, CVE-2024-54134,
MAL-2024-11183), since withdrawn from npm.

## Arms (as in `eval/reports/2026-11-22-mind-comparison.md`)

| Arm | What decides |
|---|---|
| A, Mind alone | Dependency.Guard, own knowledge and web search, no Telegraph, no Verified Ask |
| B, Telegraph trusted | the first routed `SECURITY_REVIEW_GENERAL` answer, acted on by its `verdict` |
| C, Telegraph + Verified Ask | `mind/connector/guard.mjs`: one routed ask, the free check, one re-ask only if proven wrong |

B and C come from one connector run. Cap: $0.40. One attempt per case and arm; a payment refusal
counts as "not answered".

## Grading (frozen)

`mind/compare.py`: BLOCK is correct for an affected version (withdrawn or not), PASS for a clean
one, and FLAG or no decision for a version that was never published; a confident PASS or BLOCK on
an unknown version is wrong. Reported: correct, missed vulnerabilities, false alarms, unknown
versions approved, no answer, cost, time.

## Change made before freezing

Building the set exposed that Verified Ask treated a withdrawn malicious version as "never
published". It now treats a version the registry no longer has, but OSV lists advisories for, as
real and known-bad (`tests/test_verify.py`, `test_withdrawn_malicious_version`); the replay of the
3,680 benchmark calls is unchanged by this.

## Limits stated now

- 16 cases; differences of one or two are noise.
- OSV is the truth source; the clean versions are only clean as of the read time.
- Testnet routing and miners change daily.
