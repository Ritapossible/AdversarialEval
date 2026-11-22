# Submission evidence

Telegraph's guidance (22 Nov): the final submission goes through **anjoman.ai** (the form is not
live yet). GitHub claims and `/progress` posts are not final submissions, and there is no
standalone GitHub payout. **Apps & Agents and Evaluators are judged separately**, so the evidence
for each track is kept apart here. Deadline: Dec 1, 2026, 23:59 UTC.

Every number below links to raw node API output or a committed report (CLAUDE.md rule 7).

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

- **Not registered yet.** Registration waits on the independent test set under the frozen rule
  [`eval/RULE-registration.md`](../eval/RULE-registration.md) (≥ 40 pairs from ≥ 2 outside authors;
  20 pairs from one author so far: [`2026-11-18-test-intake-fexx.md`](../eval/reports/2026-11-18-test-intake-fexx.md)).
- When registered, add: registration id, `GET /api/wasm/<id>` JSON, the Sepolia tx hash, package
  keccak256 and sha256, and the hosted executor URL.
- Validation results so far (same-author data, stated as such): [`2026-11-11-cpu-v3-seed7.md`](../eval/reports/2026-11-11-cpu-v3-seed7.md),
  [`2026-11-11-rehearsal-cpu-v3-seed13.md`](../eval/reports/2026-11-11-rehearsal-cpu-v3-seed13.md),
  [`2026-11-14-lofo.md`](../eval/reports/2026-11-14-lofo.md).

## Track: Apps & Agents

**Mission:** 10, Model Economy ([#198](https://github.com/telegraphprotocol/bounties/issues/198)), claimed 2026-11-15.
**Route:** 1, cost per verified correct answer (plus route 2, procurement via ranked routing, in progress).

| Evidence | Where |
|---|---|
| Pre-registered rule, with dated amendments | [`bench/RULE-v2.md`](../bench/RULE-v2.md) |
| Reachability audits (which miners take a canonical request) | [`2026-11-15-miner-audit.md`](../eval/reports/2026-11-15-miner-audit.md), `bench/out/round-*/audit.json` |
| Round 1 pilot, 91 paid calls | [`2026-11-15-paid-benchmark.md`](../eval/reports/2026-11-15-paid-benchmark.md) |
| Round 2, 598 paid calls (x402), reconciled with 560 on-chain transfers | [`2026-11-16-round-2.md`](../eval/reports/2026-11-16-round-2.md), `bench/out/round-2/onchain-payments.json` |
| Round 3, 1,564 calls (escrow), 591 receipts = ledger change | [`2026-11-21-round-3.md`](../eval/reports/2026-11-21-round-3.md), `bench/out/round-3/ledger-*.json` |
| Round 4 and the pooled report | pending (Nov 22) |
| Verified Ask, replay over 2,162 paid answers | [`2026-11-22-verified-ask.md`](../eval/reports/2026-11-22-verified-ask.md), [`verify/`](../verify/) |
| Receipts per call | `bench/out/round-*/calls.ndjson` (`receipt`, `escrow_receipt`) |
| Unknown vs incorrect (required by the mission) | unknown-package and unknown-version cases; graded `abstained` / `confident clean` / `invented` |
| Payer wallet (testnet only) | `0xA0C8…6C1C` (full address in the round reports) |
| Reproducibility | `python tests/test_reproduce.py`, `python tests/test_verify.py`, CI on every push |

**Still needed for this track:** a runnable app for a named customer (see `PLAN.md`, Phase A),
a demo video, and adoption evidence (another builder or user running it).

## Shared

- Demo site: https://adversarialeval.vercel.app
- Repository: https://github.com/Ritapossible/AdversarialEval
- Reused components and data licences: [`NOTICE.md`](../NOTICE.md)
- Progress history: #96 (Nov 12, 15), #198 (from Nov 15), Discord #showcase thread
