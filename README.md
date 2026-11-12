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
   Foundation Model, to be registered on the Telegraph **testnet** (Sepolia) to challenge the
   current Canonical Evaluator. **Not registered yet**: see Status.
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
| [`site/`](site/) | "Spot the Flaw" demo page (built by `tools/build_spot_flaw.py` from public data; deployed to GitHub Pages) |
| [`docs/ACTION_PLAN.md`](docs/ACTION_PLAN.md) | Step-by-step for the project lead: bounty, reviewers, pool review, wallets, VM, registration |
| [`docs/AUDIT_2026-11-10.md`](docs/AUDIT_2026-11-10.md) | Senior-engineer audit and the upgrade plan (U1–U11) |
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
bash scripts/setup_kit.sh --tokenizer   # pinned kit, foundation.json and the node's tokenizer
bash scripts/check_data.sh              # full data check
```

The full pipeline is in [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

## Status

Updated 2026-11-12. All numbers are on **our own validation set** (87 pairs, same author as
the training data), reported over two training seeds, so they are not an independent test.

- Best recipe (cpu-v3, 264 training pairs): **72.4% / 74.7%** pairwise accuracy (two seeds);
  naive scorers ≤ 58%. The package passes the node's Stage 1 check locally, and a local
  rehearsal of the node's remote check (kit executor + real WASM engine) agrees with our
  PyTorch scoring on every pair. Reports: [`eval/reports/`](eval/reports/).
- **Network actions so far:** none on chain. Nothing is registered and no pool rows are
  uploaded yet (testnet; waiting on reviewed rows and a wallet). Bounty #96 is claimed with
  progress posted.
- Next: an independent test set from outside reviewers, the reviewed pool upload, then a
  registration decision. See [`docs/ACTION_PLAN.md`](docs/ACTION_PLAN.md).

```bash
pip install numpy tokenizers
bash scripts/check_data.sh      # build, token budget, near-duplicates, baselines, kit gate
python tests/test_tools.py
```

## Built on

Full list with licenses, data attribution (GitHub Advisory Database, CC BY 4.0) and the AI-assistance disclosure: [`NOTICE.md`](NOTICE.md).

- [telegraph-wasm-baseline](https://github.com/telegraphprotocol/telegraph-wasm-baseline), the
  official adapter kit (MIT)
- [telegraph-foundation](https://github.com/telegraphprotocol/telegraph-foundation), Foundation
  Model `modernbert-base-lora16-v1` (Apache-2.0, from `answerdotai/ModernBERT-base`)

## Contributors

- **Rita** ([@Ritapossible](https://github.com/Ritapossible)): project lead
