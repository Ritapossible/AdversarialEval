# Plan

Deadline: **Dec 1, 2026, 23:59 UTC**. Checkpoints: **Nov 14** (integration milestone),
**Nov 20** (community showcase). Today: Nov 4.

## Goal and definition of done

| # | Outcome | Measured by |
|---|---|---|
| G1 | The adapter registers and challenges the `SECURITY_REVIEW` Canonical Evaluator | A registration id, and the `GET /api/wasm/<id>` decision |
| G2 | The adapter beats the incumbent on hidden verification | `eval.candidate_win_rate` ≥ incumbent + 0.02, and ≥ 0.70 |
| G3 | It prefers the chosen answer on held-out pairs, including pool-like pairs we didn't write | ≥ 80% on `data/validation/`, ≥ 70% on every failure family |
| G4 | The data defeats naive scorers | Longer-wins, keyword overlap and question-blind BoW each ≤ 60% |
| G5 | The material is accepted into the pool | Our private rows are `eligible`, and `eligible_submitters` counts us |
| G6 | The evidence is public and reproducible | Released dataset, write-up and run instructions; a third party can rerun the eval |
| S1 | Stretch: first material on `SMART_CONTRACT_AUDIT` | Rows `eligible`; the adapter registered if the pool reaches 5 contributors |

Kit-enforced minimums, which are already gates: dataset gate PASS; held-out ≥ 65% and ≥ +10
points over longer-wins; remote check ≥ 70% on 15 public pairs.

## Phases

### Phase 0: Setup (Nov 4–5)
- [x] Study the kit, rules, live network and competition → `docs/RESEARCH.md`
- [x] Repo scaffold: plan, memory, architecture, specs
- [x] `scripts/setup_kit.sh`: pin kit commit `1ed063e`, fetch and verify `foundation.json`
- [ ] Create two wallets: (a) eval-pool contributor key, (b) adapter-bond / fee wallet. Get
      Sepolia ETH and about 6 MACHINA.
- [ ] `/claim` on bounty #96 (SECURITY_REVIEW). Consider #128 (SMART_CONTRACT_AUDIT).
- [ ] Ask the organizers the open questions in `MEMORY.md` §Open questions (Discord)

### Phase 1: Criteria and seed data (Nov 5–8)
- [ ] Freeze the taxonomy v1 in `docs/ADVERSARIAL_CRITERIA.md` (F1–F10)
- [x] Source list of real advisories: GHSA, NVD, OSV, CWE pages, about 150 distinct
      package/version cases
- [ ] Author 10 seed pairs per family (100 total) following `docs/DATASET_SPEC.md`
      (in progress: 59 train + 14 validation as of Nov 8; see `eval/reports/2026-11-08-seed-v0.md`)
- [ ] Human review pass on seed pairs (`reviewed: true`)
- [x] `scripts/check_data.sh` passes the kit dataset gate
- [x] Naive-baseline harness (`eval/baselines.py`): longer-wins, shorter-wins, keyword overlap
      with the prompt, question-blind BoW, TF-IDF cosine to prompt. Report per family.

### Phase 2: Scale and validate (Nov 8–13)
- [ ] Grow to about 400 public train pairs and about 150 private pool pairs, in disjoint
      sets with no near-duplicate prompts across them
- [ ] Build `data/validation/`, about 80 pool-style pairs written in a *different voice*:
      other formats, terse and verbose answers, JSON-shaped miner responses, a second author
- [ ] First training run (GPU). Record per-family accuracy and length-bias stats in
      `eval/reports/`
- [ ] Robustness probes: answer-order swap, paraphrase of the chosen answer, padding the
      rejected answer to match length, truncation at 512 tokens
- [ ] Upload the private pool set (signed) → confirm the rows are `eligible`

### Phase 3: Integration milestone (Nov 14)
- [ ] An adapter passes the kit eval gate and our G3/G4 targets
- [ ] Export the delta → `adapterbuild lora` PASS → record the keccak256
- [ ] Executor VM up (public HTTPS, ≥ 5 GB RAM), `adapterexec` serving, passes
      `npm run adapter:check-executor`
- [ ] Milestone update posted (bounty `/progress`, H2 update)

### Phase 4: Challenge (Nov 15–20)
- [ ] Host the `.safetensors` at an immutable URL (GitHub raw at a commit SHA, or IPFS)
- [ ] Approve the MACHINA bond, `registerWasm(...)` on prefix `SECURITY_REVIEW`
- [ ] Track the status through remote check → Stage 1 → confirmation → competition
- [ ] If rejected: read the reason, fix, re-export (a new hash) and re-register.
      Budget 3 attempts.
- [ ] Showcase demo on Nov 20

### Phase 5: Stretch and polish (Nov 21–30)
- [ ] `SMART_CONTRACT_AUDIT_GENERAL`: 60+ private pool pairs uploaded. Register an adapter if
      the pool reaches 5 contributors.
- [ ] Publish the dataset (GitHub release and Hugging Face) with a datasheet
- [ ] Write-up: adversarial criteria, results, ablations, how to reproduce
- [ ] Tutorial or blog post for growth points (reproductions and integrations count; stars don't)
- [ ] 2–5 min demo video

### Phase 6: Submit (by Nov 30, a day early)
- [ ] Everything in `docs/SUBMISSION_CHECKLIST.md`
- [ ] `/submit` on the bounty issues with the contributor address and registration id

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| The adapter learns our authoring style and fails the remote check on others' pairs (this happened to 3 recent challengers: 13%, 53%, 53%) | **High** | A pool-style validation set from a second voice; vary formats; mix in broader security preference data; per-family monitoring |
| The hidden sample is small (about 21 pairs), so one pair ≈ 4.8 points | High | Aim well above the bar (≥ 80% on validation); register only once validation is stable across seeds |
| Publishing the dataset leaks hidden testing-half rows | Medium | Keep the public and pool sets strictly disjoint, and confirm with the organizers |
| Flaw truncated past 512 tokens | Medium | Length-check every row; put the flaw early; keep the snippets short |
| The executor isn't bit-exact or the VM goes down | Medium | Use the reference `adapterexec` only; a systemd service; health check; keep it up until Active |
| The incumbent is replaced by someone else first, which raises the bar | Medium | Watch `/api/wasm?resolve=SECURITY_REVIEW`; register as early as quality allows |
| `SMART_CONTRACT_AUDIT` never reaches 5 contributors | High | Treat it as material-only coverage; still counts as "valuable new coverage" |
| Rows rejected as near-duplicates (≥ 85% prompt similarity) | Medium | Dedup locally with the same normalisation before upload |

## Cadence

- Bounty `/progress` comment at least every 72 h (the claim lapses otherwise)
- Update `MEMORY.md` → *Live state* after every network action
- Commit each training run's report to `eval/reports/<date>-<run>.md`
