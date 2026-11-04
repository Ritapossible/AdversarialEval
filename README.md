# AdversarialEval

**A competitive Evaluator adapter for Telegraph that prefers answers which survive
adversarial pressure over answers that are plausible but flawed.**

Telegraph Hackathon Season II · Evaluators track · Primary Intent: `SECURITY_REVIEW` ·
Stretch: `SMART_CONTRACT_AUDIT`

---

## What it is

Most answer scorers reward fluency, surface completeness or keyword overlap. AdversarialEval
is trained to do the opposite. It ranks an answer higher only when the answer stays
correct under targeted pressure: fabricated CVE ids, wrong affected-version ranges, a
missed critical finding, an overconfident "Secure", a false alarm on safe code, or a
verdict that flips once the context changes.

The project ships two things the protocol needs:

1. **An Evaluator adapter.** It's a LoRA delta and reward head on the shared ModernBERT-base
   Foundation Model, registered on-chain to challenge the current Canonical Evaluator.
2. **Adversarial preference data.** It's a public dataset of `prompt / chosen / rejected`
   pairs, plus a separate, private set contributed to the Telegraph evaluation pool.

## Why `SECURITY_REVIEW`

Live testnet, 2026-11-04:

- **Incumbent:** the Canonical Evaluator (registration #42) scored **71.43% on 21 hidden
  pairs**, just above the 70% floor. To replace it, a challenger needs about **73.4%** on
  the same sample, which is the 2-point margin.
- **Pool and miners:** the pool holds 55 rows from 6 contributors, and 26 miners serve the
  Intent.
- **Demand:** P1 bounty [#96](https://github.com/telegraphprotocol/bounties/issues/96). It's
  a mandatory Intent and sits under the Exchange, Model Economy and Web3/DeFi missions.

The full reasoning is in [`docs/RESEARCH.md`](docs/RESEARCH.md).

## Repository map

| Path | What |
|---|---|
| [`PLAN.md`](PLAN.md) | Milestones, task checklist, deadlines, risks |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Components, data flow, the scoring contract, interfaces |
| [`MEMORY.md`](MEMORY.md) | Durable project memory: facts, decisions, live state, gotchas |
| [`CLAUDE.md`](CLAUDE.md) | Working rules for AI assistants on this repo |
| [`docs/RESEARCH.md`](docs/RESEARCH.md) | Study of the kit, rules, live network and competition |
| [`docs/ADVERSARIAL_CRITERIA.md`](docs/ADVERSARIAL_CRITERIA.md) | The failure-mode taxonomy (a deliverable) |
| [`docs/DATASET_SPEC.md`](docs/DATASET_SPEC.md) | Row schema, authoring rules, splits, provenance |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Exact commands for train, export, check, host, register, upload |
| [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md) | What the hackathon and the bounty need from us |
| `data/` | `public/` (released), `validation/` (pool-like held-out), `private/` (pool set, git-ignored) |
| `configs/` | Training configs |
| `scripts/` | Setup and helper scripts |

## Quick start

```bash
bash scripts/setup_kit.sh          # clones the pinned adapter kit and fetches foundation.json
bash scripts/check_data.sh data/public/security_review.train.jsonl
```

The full pipeline is in [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

## Status

Phase 0, setup. See [`PLAN.md`](PLAN.md) for the current milestone.

## Built on

- [telegraph-wasm-baseline](https://github.com/telegraphprotocol/telegraph-wasm-baseline), the
  official adapter kit (MIT)
- [telegraph-foundation](https://github.com/telegraphprotocol/telegraph-foundation), Foundation
  Model `modernbert-base-lora16-v1` (Apache-2.0, from `answerdotai/ModernBERT-base`)

## Contributors

- **Rita** ([@Ritapossible](https://github.com/Ritapossible)): project lead
