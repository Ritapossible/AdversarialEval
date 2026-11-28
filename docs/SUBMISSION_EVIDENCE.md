# Submission evidence

Telegraph's guidance in #hackathon (to another builder, read 22 Nov): the final submission goes through **anjoman.ai** (the form is not
live yet). GitHub claims and `/progress` posts are not final submissions, and there is no
standalone GitHub payout. **Apps & Agents and Evaluators are judged separately**, so the evidence
for each track is kept apart here. Deadline: Dec 1, 2026, 23:59 UTC.

Every number below links to raw node API output or a committed report (CLAUDE.md rule 7).

Readable per-track summaries for judges: [`tracks/`](../tracks/README.md). This file is the
raw evidence index behind them.

## Track: Evaluators

**Intent:** `SECURITY_REVIEW_GENERAL` (testnet node `devnode.telegraphprotocol.com`)
**Contributor wallet:** `0x31Cf659edcDd1A6bF98302cbA5E7CEA8dc143095`

### Evaluation-pool material

| Batch | Uploaded | Rows | Status | Provenance | Report |
|---|---|---:|---|---|---|
| 1: flaw-family pairs (F1 to F10) | 2026-11-14 | 81 | eligible | attested | [`2026-11-14-pool-upload.md`](../eval/reports/2026-11-14-pool-upload.md) |
| 2: severity pairs (F8) | 2026-11-18 | 83 | eligible | attested | [`2026-11-18-pool-batch2.md`](../eval/reports/2026-11-18-pool-batch2.md) |
| **Total** | | **164** | **all eligible** | | |

- **Eligibility, checked 2026-11-22:** `GET /api/evalpool/submissions/mine?submitter=<wallet>&intent_id=SECURITY_REVIEW_GENERAL`
  returned `count: 164`, all `eligible`, all `attested`, rules `evalpool-quality-v1`. Raw output:
  [`eval/reports/raw/2026-11-22-evalpool-mine.json`](../eval/reports/raw/2026-11-22-evalpool-mine.json)
  (row hashes and case ids for every row).
- **Pool status, same day:** 1,379 eligible rows from 11 submitters; active snapshot
  `corpus_version e08f9e9d…efb9c`, published 2026-11-18. Raw:
  [`eval/reports/raw/2026-11-22-evalpool-status.json`](../eval/reports/raw/2026-11-22-evalpool-status.json).
- **Material links:** taxonomy [`docs/ADVERSARIAL_CRITERIA.md`](ADVERSARIAL_CRITERIA.md), dataset
  spec [`docs/DATASET_SPEC.md`](DATASET_SPEC.md), public training pairs `data/public/`, validation
  `data/validation/`. Pool rows themselves stay private (`data/private/`, git-ignored); share them
  with judges only on request.
- **Quality evidence:** every advisory fact checked against OSV; human review of every pool row;
  length gate (ratio ≤ 1.25, chosen-longer share 35 to 65%); dedup across public, validation and
  private sets (`tools/dedup.py`).

### Evaluator adapter

- **Not registered** (final decision, 28 Nov). The frozen rule
  [`eval/RULE-registration.md`](../eval/RULE-registration.md) required at least 80% on an independent
  test. The adapter scored 77.5% (31/40, Wilson 62.5 to 87.7%) on 40 pairs from 2 outside authors,
  frozen by hash ([freeze](../eval/reports/2026-11-24-test-freeze.md)) and scored once
  ([score](../eval/reports/2026-11-24-test-score.md)). Error analysis of the 9 misses:
  [`2026-11-28-test-error-analysis.md`](../eval/reports/2026-11-28-test-error-analysis.md).
- Validation results (same-author data, stated as such): [`2026-11-11-cpu-v3-seed7.md`](../eval/reports/2026-11-11-cpu-v3-seed7.md),
  [`2026-11-11-rehearsal-cpu-v3-seed13.md`](../eval/reports/2026-11-11-rehearsal-cpu-v3-seed13.md),
  [`2026-11-14-lofo.md`](../eval/reports/2026-11-14-lofo.md).

### Dataset release

- **v1.0:** 264 train, 87 validation and 40 independent test pairs, with a dataset card and checksums.
  - [GitHub release](https://github.com/Ritapossible/AdversarialEval/releases/tag/dataset-v1.0)
    (zip sha256 `d1159220a141611b…`);
  - [Hugging Face](https://huggingface.co/datasets/Ritapossible/adversarialeval-security-review)
    (loads with `load_dataset`, and every row id matches the GitHub release);
  - source: [`release/`](../release/adversarialeval-security-review-v1/), built by
    `tools/build_release.py`, which refuses to build if any row overlaps the private pool.

## Track: Apps & Agents

**Mission:** 10, Model Economy ([#198](https://github.com/telegraphprotocol/bounties/issues/198)), claimed 2026-11-15.
**Route:** 1, cost per verified correct answer, and route 2, procurement via ranked routing (which answers are worth paying for).

| Evidence | Where |
|---|---|
| Pre-registered rule, with dated amendments | [`bench/RULE-v2.md`](../bench/RULE-v2.md) |
| Reachability audits (which miners take a canonical request) | [`2026-11-15-miner-audit.md`](../eval/reports/2026-11-15-miner-audit.md), `bench/out/round-*/audit.json` |
| Round 1 pilot, 91 paid calls | [`2026-11-15-paid-benchmark.md`](../eval/reports/2026-11-15-paid-benchmark.md) |
| Round 2, 598 paid calls (x402), reconciled with 560 on-chain transfers | [`2026-11-16-round-2.md`](../eval/reports/2026-11-16-round-2.md), `bench/out/round-2/onchain-payments.json` |
| Round 3, 1,564 calls (escrow), 591 receipts = ledger change | [`2026-11-21-round-3.md`](../eval/reports/2026-11-21-round-3.md), `bench/out/round-3/ledger-*.json` |
| Round 4 (1,518 calls, escrow) and the pooled report, rounds 2 to 4 | [`2026-11-22-rounds-2-4.md`](../eval/reports/2026-11-22-rounds-2-4.md), `bench/out/round-4/ledger-*.json`, `bench/out/pooled-score.md` |
| Verified Ask, replay over 3,680 paid calls (rounds 2 to 4) | [`2026-11-22-verified-ask.md`](../eval/reports/2026-11-22-verified-ask.md), [`verify/`](../verify/) |
| Receipts per call | `bench/out/round-*/calls.ndjson` (`receipt`, `escrow_receipt`) |
| Unknown vs incorrect (required by the mission) | unknown-package and unknown-version cases; graded `abstained` / `confident clean` / `invented` |
| Payer wallet (testnet only) | `0xA0C8…6C1C` (full address in the round reports) |
| Reproducibility | `python tests/test_reproduce.py`, `python tests/test_verify.py`, CI on every push |

**Independent use of our material:** Femtech-web's miner Salence (Miners/Providers track, routing
ID 905227) reports "80.6% correct on 264 held-out AdversarialEval questions" in its #198
`/progress` (22 Nov), i.e. our public training pairs used as another builder's test set.

**The app:** Dependency.Guard, a Mind on Minds by Animoca (id `38266542-f36b-1410-8467-00039ce7df11`),
listed and live on Anjoman (Security). Demo videos: https://adversarialeval.vercel.app/videos

| Test (each rule frozen before the first paid call) | Payment | Evidence |
|---|---|---|
| Dependency.Guard with and without Telegraph: 26 packages, 23 code functions, 16 Solana versions | Anjoman | [`2026-11-22-mind-comparison.md`](../eval/reports/2026-11-22-mind-comparison.md), [`2026-11-22-code-review-v2.md`](../eval/reports/2026-11-22-code-review-v2.md), [`2026-11-23-solana-dependencies.md`](../eval/reports/2026-11-23-solana-dependencies.md), `mind/evidence/` |
| Solana use case 3: 21 hard cases | x402 on Solana devnet, 55 payments on-chain | [`2026-11-24-solana-use-case-3.md`](../eval/reports/2026-11-24-solana-use-case-3.md), `bench/out/solana-v2/` (`calls.ndjson`, `onchain.json`) |
| Provider independence by payout address | free (node listing) | [`2026-11-24-provider-independence.md`](../eval/reports/2026-11-24-provider-independence.md), `eval/reports/raw/2026-11-24-miners-security-review.json` |
| Qwen-Agent pre-deployment check | Anjoman, 4 answers | [`2026-11-25-qwen-agent-predeploy.md`](../eval/reports/2026-11-25-qwen-agent-predeploy.md), `bench/out/deploycheck-qwen-agent/` |
| Qwen alone vs Qwen + Telegraph: 36 changes | x402 on Solana, 45 payments on-chain | [`2026-11-28-qwen-code-verification.md`](../eval/reports/2026-11-28-qwen-code-verification.md), `codeverify/` (rule, tasks, tests), `bench/out/codeverify/` |
| Prediction markets we wrote: 24 | x402 on Solana, 48 + 2 preflight on-chain | [`2026-11-28-prediction-market-resolution.md`](../eval/reports/2026-11-28-prediction-market-resolution.md), `resolve/cases.json`, `bench/out/eventres/` |
| Real Polymarket markets: 24 | x402 on Solana, 48 on-chain | [`2026-11-28-polymarket-resolution.md`](../eval/reports/2026-11-28-polymarket-resolution.md), `resolve/polymarket_cases.json`, `bench/out/eventres-polymarket/` |
| The same Polymarket markets through the app (Anjoman + the Mind) | Anjoman, reconciled with the escrow balance | [`2026-11-28-polymarket-via-app.md`](../eval/reports/2026-11-28-polymarket-via-app.md) and [addendum](../eval/reports/2026-11-28-polymarket-via-app-addendum.md), `mind/evidence/2026-11-28T10-41-49-223Z.markets.json` |

**Pre-registration, checked against times the author can't set.** Each rule's freeze commit
comes before the first payment of its run. Payment times are Solana block times (`onchain.json`)
or Anjoman's own timestamps. Push times are also recorded server-side in the repository's
[activity log](https://github.com/Ritapossible/AdversarialEval/activity).

| Run | Freeze commit (UTC) | First payment (UTC, server-side) |
|---|---|---|
| Solana use case 3 | `ee02304` 24 Nov 18:11:25 | 24 Nov 18:24:48 (Solana block time) |
| Qwen code test | `68c0dfa` 28 Nov 07:30:22 (amendment `7647c69` 07:33:25) | 28 Nov 08:11:01 (Solana block time) |
| Prediction markets we wrote | `ca0fa48` 28 Nov 09:14:37 | 28 Nov 09:14:46 (Solana block time) |
| Real Polymarket markets | `47a2aa8` 28 Nov 10:02:02 | 28 Nov 10:02:13 (Solana block time) |
| Polymarket through the app | `0ea3567` 28 Nov 10:32:44 (amendment `c5f8a99` 10:41:41) | 28 Nov 10:41:49 (run start; Anjoman receipts in the run file) |

**Evidence integrity:** 338 evidence files are listed in [`evidence/MANIFEST.json`](../evidence/MANIFEST.json)
and signed with Ed25519. The manifest's hash is anchored on Solana devnet
([`evidence/ANCHORS.json`](../evidence/ANCHORS.json)). Anyone can check both with
`node tools/evidence_manifest.mjs verify` and `node tools/anchor_evidence.mjs verify`, and CI
checks the signature on every push.

## Shared

- Demo site: https://adversarialeval.vercel.app
- Repository: https://github.com/Ritapossible/AdversarialEval
- Reused components and data licences: [`NOTICE.md`](../NOTICE.md)
- Progress history: #96 (Nov 12, 15), #198 (from Nov 15), Discord #showcase thread
