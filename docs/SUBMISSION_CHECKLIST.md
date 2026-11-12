# Submission Checklist

The deadline is **Dec 1, 2026, 23:59 UTC**. We aim to submit on Nov 30. Last checked against
the official rules (anjoman.ai/dashboard/hackathon/season-2/rules) on 2026-11-12; see
"Rules compliance" at the end.

## Hackathon (H2 website)

- [x] Star `telegraphprotocol/bounties` from the entrant account (rule for all tracks): done 2026-11-12
- [ ] **A real Telegraph integration with genuine evidence** (required for every entry). The
      minimum is reviewed pool rows uploaded to `SECURITY_REVIEW_GENERAL` and shown eligible by
      the node API; registration adds more. **Not done yet: this is the biggest gap.**
- [ ] Project details incl. the GitHub username that starred the bounties repo (`Ritapossible`)
- [ ] Team, track (**Evaluators**), project name, missions (Exchange, Model Economy,
      Web3 Native & DeFi), Intent `SECURITY_REVIEW` only
      (`SMART_CONTRACT_AUDIT` was dropped on 11-10, decision U11)
- [ ] Working / reviewer link: this repo, the dataset release and the executor URL
- [ ] **A 2–5 min demo video**: the problem → the naive scorers failing → our adapter ranking
      correctly → the on-chain registration → the node's decision
- [ ] Run instructions (fields the rules name): prerequisites, a sample request, the expected
      result, the network (Sepolia testnet), spending limits / costs ($5 bond, never slashed;
      gas; VM), known limitations
- [ ] Evidence:
  - [ ] registration id(s) and the `GET /api/wasm/<id>` JSON (decision, win rate, corpus version)
  - [ ] the registration tx hash on Sepolia
  - [ ] eligible pool row counts (`/api/evalpool/submissions/mine`)
  - [ ] held-out report: per-family accuracy, naive baselines, length-bias stats, probes
  - [ ] package keccak256 and sha256, and the hosted URL
- [ ] Evidence: the Spot the Flaw demo link, with the held-out adapter results (`eval/reports/2026-11-12-demoheld.md`)
- [ ] Sensitive material (pool rows, keys) shared privately with judges only if they ask; never public
- [ ] A short public summary, with links to the original updates (Nov 12 `/progress` on #96,
      the Discord #showcase thread, the Nov 20 showcase) and any tutorial
- [ ] Showcase permissions
- [x] Disclosure of reused components: `NOTICE.md` (kit, foundation, ModernBERT, libraries,
      GitHub Advisory Database data under CC BY 4.0, AI assistance)

## Bounties

- [ ] #96 SECURITY_REVIEW: `/claim`, then `/progress` at least every 72 h, then `/submit`
      with the contributor address and registration id
- [x] #96 claimed 2026-11-12, first `/progress` posted (next due by Nov 15 ~13:57)
- ~~#128 SMART_CONTRACT_AUDIT~~ dropped (U11)

## Deliverables in this repo

- [ ] `adapters/SECURITY_REVIEW.safetensors` (+ manifest)
- [ ] `data/public/*.jsonl` + `data/validation/*.jsonl` (already public) + datasheet
- [ ] A LICENSE for our own code and data (owner's choice; the data must keep the CC BY 4.0
      attribution in `NOTICE.md`)
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

## Rules compliance (checked 2026-11-12)

| Rule | Status |
|---|---|
| Something working (a valid Evaluator contribution) | Partly: dataset, demo and adapter work; nothing on the network yet |
| Real Telegraph integration with genuine evidence | **Open**: needs the pool upload and/or registration on testnet |
| Repeatable results with clear instructions | Mostly: RUNBOOK + scripts; write the submission run-instructions block |
| Safe handling of keys, private data, confidential evaluation material | OK: no secrets or pool rows ever committed (history checked); signing stays local; never read hidden rows |
| Accurate claims, network stated | Fixed 11-12: README said "registered on-chain" and quoted an old single-seed 76.9%; now says not registered, testnet, two-seed validation numbers |
| Star the bounties repo | Done (Ritapossible) |
| Disclose major reused components | Done: `NOTICE.md` |
| H2 activity inside the event period | OK: repo started Nov 4; all network activity is still to come |
| Promotional posts disclose participation and prize incentive | OK on Discord and #96; reviewer outreach now says it's a prize-eligible hackathon entry |
| No fake adoption, collusion, star or repost incentives | OK: none; reviewers get credit only, for writing test pairs, not for engagement |
| Copied work presented as independent | Watch: the test set must come from genuinely independent reviewers |
| No disclosure of protected material | OK: only public kit, public data and the node's public APIs used |
| Third-party licenses respected | Fixed 11-12: CC BY 4.0 attribution for the cached advisory records added |
