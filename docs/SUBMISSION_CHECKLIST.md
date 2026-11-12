# Submission Checklist

The deadline is **Dec 1, 2026, 23:59 UTC**. We aim to submit on Nov 30.

## Hackathon (H2 website)

- [x] Star `telegraphprotocol/bounties` from the entrant account (rule for all tracks): done 2026-11-12
- [ ] Team, track (**Evaluators**), project name, missions (Exchange, Model Economy,
      Web3 Native & DeFi), Intents (`SECURITY_REVIEW`, `SMART_CONTRACT_AUDIT`)
- [ ] Working / reviewer link: this repo, the dataset release and the executor URL
- [ ] **A 2–5 min demo video**: the problem → the naive scorers failing → our adapter ranking
      correctly → the on-chain registration → the node's decision
- [ ] Run instructions: prerequisites, config, a sample request, the expected result, the
      network (Sepolia testnet), costs ($5 bond, gas, VM), known limitations
- [ ] Evidence:
  - [ ] registration id(s) and the `GET /api/wasm/<id>` JSON (decision, win rate, corpus version)
  - [ ] the registration tx hash on Sepolia
  - [ ] eligible pool row counts (`/api/evalpool/submissions/mine`)
  - [ ] held-out report: per-family accuracy, naive baselines, length-bias stats, probes
  - [ ] package keccak256 and sha256, and the hosted URL
- [ ] A short public summary, with links to the H2 updates (Nov 14 milestone, Nov 20 showcase)
- [ ] Showcase permissions
- [ ] Disclosure of reused components: the telegraph-wasm-baseline kit (MIT) and
      ModernBERT-base (Apache-2.0)

## Bounties

- [ ] #96 SECURITY_REVIEW: `/claim`, then `/progress` at least every 72 h, then `/submit`
      with the contributor address and registration id
- [ ] #128 SMART_CONTRACT_AUDIT: the same

## Deliverables in this repo

- [ ] `adapters/SECURITY_REVIEW.safetensors` (+ manifest)
- [ ] `data/public/*.jsonl` + datasheet (and validation, after the hackathon)
- [ ] `docs/ADVERSARIAL_CRITERIA.md` frozen
- [ ] `eval/reports/FINAL.md`
- [ ] A reproducibility check: a fresh clone → `setup_kit.sh` → `check_data.sh` → eval
      reproduces the reported numbers

## Scoring levers (out of 100; 70 to win; technical ≥ 24/35)

| Criterion | Pts | Our evidence |
|---|---|---|
| Technical quality and mainnet readiness | 35 | Canonical win, robustness probes, a reproducible pipeline |
| Commercial viability | 25 | Unblocks security miners for 3 missions; better ranking = better buyer outcomes |
| Adoption and retention | 10 | Others train on or cite our dataset; miners ranked by our adapter |
| Telegraph integration | 5 | On-chain registration, pool contributions, a live executor |
| Reproducibility and demo | 5 | Runbook, video, one-command eval |
| Growth and education | 20 | A tutorial on adversarial preference data, independent reproductions, a dataset others use |

## Fair play

- Never publish hidden evaluation material or the private pool set.
- Don't fake adoption or run collusive requests.
- Make accurate claims only: say "testnet", and report what was actually verified.
