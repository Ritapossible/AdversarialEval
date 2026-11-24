# Solana dependency test: Dependency.Guard with and without Telegraph (2026-11-23)

Rule, cases and grading were frozen before any paid call: `mind/solana-test/RULE.md` (commit
`58b54d2`), `mind/solana-test/cases.json` (truth read from OSV and the registries 07:41 UTC).
Scored with `python3 mind/compare.py mind/evidence/2026-11-23T10-45-39-006Z.json
mind/evidence/2026-11-23-solana-mind-alone.json --cases mind/solana-test/cases.json`.

## Setup

- 16 cases from the Solana stack: `@solana/web3.js`, `secp256k1`, `ws`, `node-fetch` on npm;
  `ed25519-dalek`, `curve25519-dalek`, `borsh` on crates.io. 7 affected versions, their 7 current
  clean releases, 2 versions that were never published (`@solana/web3.js` 9.9.9,
  `solana-program` 99.0.0).
- The key case: `@solana/web3.js` 1.95.7, a hijacked release that stole private keys
  (GHSA-jcxm-7wvp-g6p5, CVE-2024-54134, MAL-2024-11183), since withdrawn from npm.
- Arm A: Dependency.Guard in Minds, told not to use Telegraph, Anjoman, Verified Ask or its
  watchlist, only its own knowledge and web search (its reply says it read registry and advisory
  data itself, as in the earlier package sets). Sent 10:45:41 UTC, shuffled order (seed 31,
  `mind/evidence/2026-11-23-solana-mind-alone.order.json`), full reply 10:47:02 UTC.
- Arms B and C: one run of `mind/connector/guard.mjs --no-mind --max-spend 0.40`, started 10:45:39
  UTC, intent `SECURITY_REVIEW_GENERAL`, routed by Anjoman. B acts on the first answer's verdict;
  C is the connector's decision after Verified Ask (one re-ask only when proven wrong).

## Result

| Arm | Correct (of 16) | Missed vulnerabilities | False alarms | Unknown versions approved | Time | Cost |
|---|---|---|---|---|---|---|
| A: Mind alone | **16** | 0 | 0 | 0 | 81 s | Minds credits, $0 USDC |
| B: Telegraph trusted | 14 | 0 | 0 | **2** | 341 s (16 asks) | $0.21 |
| C: Telegraph + Verified Ask | **16** | 0 | 0 | 0 | 350 s (17 asks) | $0.22 |

All three arms blocked all 7 affected versions, including the withdrawn `@solana/web3.js` 1.95.7,
and passed all 7 clean releases. The difference is in the two versions that don't exist:

| Case | B: first paid answer | What Verified Ask found | C |
|---|---|---|---|
| `@solana/web3.js` 9.9.9 | TxLens: **Secure**, "no publicly disclosed vulnerabilities … follows standard cryptographic practices" | not published on npm: contradicted; re-asked PREFLIGHT, which said no such release and gave no verdict | FLAG |
| `solana-program` 99.0.0 | PREFLIGHT: **Insecure**, 3 issues (CWE-284, CWE-190, CWE-20), while its own summary says "no 99.0.0 release" | not published on crates.io: contradicted | FLAG |

Without the check, an agent acting on Telegraph's verdict would have approved a version that
doesn't exist (a typo or a planted name) and blocked another on invented issues.

On 1.95.7 the first answer (PREFLIGHT) was Insecure with all three advisory ids; Verified Ask
confirmed each id against OSV and, with the fix made before freezing, treated the withdrawn
version as real and known-bad.

## Payments (checked)

17 asks, 17 receipts in the run file. 12 asks cost $0.01, 5 cost $0.02 (the routed ask settled two
payments, as seen before). Total $0.22. Anjoman `/engine/escrow/balance` after the run:

```
{"effectiveBalance":"0.45","escrowBalance":"0.67","agentDebt":"0"}
```

$0.67 before, $0.45 after: matches the $0.22 the connector recorded.

## What this says

- On well-known Solana advisories, Telegraph's answers were right on every real version, and so
  was the Mind alone. The hijacked web3.js release is widely documented, so a frontier model
  knowing it is expected.
- Trusting Telegraph's verdict blindly fails where it failed before: versions that don't exist get
  confident verdicts (2 of 2 here). Verified Ask caught both for free and turned them into FLAG.
- The Mind alone matched the best paid arm again, as on the earlier package sets. The value
  Telegraph plus Verified Ask adds is a receipt-backed, independently checked decision, not
  better accuracy on this set.

## Re-check before reporting (24 Nov)

- **Pre-registration holds.** The rule and cases were committed at 07:42:19 UTC (`58b54d2`), three
  hours before the first paid call (10:45:39 UTC), and neither file has changed since. The run
  file itself doesn't name that commit (the rule asked it to); from now on the connector records
  its repository commit in every run file.
- **The fixed Verified Ask gives the same labels.** After this run, an audit tightened how Verified
  Ask treats versions missing from the registry (`docs/AUDIT_2026-11-23.md`, bug 1). All 17 stored
  answers were checked again with the fixed code on 24 Nov: 0 labels changed, so B, C and the
  payments stand as reported.
- **Scoring is strict.** `compare.py` now refuses a Mind reply it can't fully parse; all 16 lines of
  arm A parse, and the scores are unchanged (16, 14, 16).
- **The clean and affected versions still hold.** The daily free watch re-checked all 14 decided
  versions on 23 Nov (`mind/evidence/watch/2026-11-23.json`): all still verified.
- **Intervals** (Wilson, 95%): 16 of 16 is 81% to 100%; 14 of 16 is 64% to 97%. They overlap: on
  this set the difference between B and C is the 2 versions that don't exist, not a measured gap
  in accuracy.

## Limits

- 16 cases; one or two differences are noise.
- OSV is the truth; the clean releases are clean as of 07:41 UTC on 23 Nov.
- One run per arm; routing and miners change daily (15 of 16 first answers came from PREFLIGHT).
- No Solana-specific intent exists; this uses `SECURITY_REVIEW_GENERAL` on Solana dependencies.
  Payments were on the existing rail, not Solana devnet USDC (Phase S4, optional).
