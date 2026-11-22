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
      (in progress: 95 train + 39 validation as of Nov 10; see `eval/reports/`)
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

### Phase U: Audit upgrades (Nov 10–20), see `docs/AUDIT_2026-11-10.md`
- [ ] U1 Frozen test split `data/test/` by outside reviewers. **Done (Claude):** split support, `docs/REVIEWER_GUIDE.md`, CSV template, importer, `docs/OUTREACH.md`. **Open (you):** recruit 2–3 reviewers
- [ ] U2 Human-reviewed pool upload. **Done (Claude):** 91 candidates (`gen_osv_pairs.py --split private`, 17 packages disjoint from every published split, every label verified by OSV, kit gate PASS), review sheet + `tools/review_pool.py`, upload refuses unreviewed rows. **Open (you):** review `data/private/review/pool_review.csv`, then a contributor wallet
- [ ] U3 Sample and label real miner responses (blocked: funded wallet)
- [ ] U4 Seed runs + registration rule: independent-test accuracy about 80% or more (the 15-pair remote check passes only 69% of the time at 75%) (blocked for registration: wallets, VM, `/claim` #96)
- [x] Local remote-check rehearsal (`scripts/rehearse.sh`): node client, then `adapterexec`, then the real engine; identity echo and WASM-vs-PyTorch agreement verified
- [x] U5 Programmatic OSV minimal pairs: 146 pairs from 163 advisories, every label re-checked by OSV's own version query (2 ambiguous advisories excluded)
- [x] U6 Error-mining loop: `eval/errors.py` → worksheet → 11 targeted pairs (`e_targeted.jsonl`) + 12 coverage pairs (batch F). cpu-v3 showed diminishing returns (+1.7 points, noise), so single-pair mining is paused until independent data arrives
- [x] U7 Taxonomy re-scoped (`docs/ADVERSARIAL_CRITERIA.md`), with evidence-in-prompt for half of the generated F2
- [x] U8 Seed-merged LoRA via SVD: built and tested (`tools/merge_seeds.py`), negative result. The merge is worse than either seed (seeds don't share an init), so it isn't used for submission
- [ ] U9 Impact demo: incumbent vs ours on real miner responses (after U3)
- [x] U10 Four tested patches in `docs/upstream/` (filing is your call)
- [x] U11 Drop SMART_CONTRACT_AUDIT as an adapter target (material only)

### Phase 3: Integration milestone (Nov 14)
- [ ] An adapter passes the kit eval gate and our G3/G4 targets
- [ ] Export the delta → `adapterbuild lora` PASS → record the keccak256
- [ ] Executor VM up (public HTTPS, ≥ 5 GB RAM), `adapterexec` serving, passes
      `npm run adapter:check-executor`
- [ ] Milestone update posted (bounty `/progress`, H2 update). Draft ready: `docs/milestones/2026-11-14-progress.md`; needs `/claim` #96 first (you)

### Phase 4: Challenge (Nov 15–20)
- [ ] Host the `.safetensors` at an immutable URL (GitHub raw at a commit SHA, or IPFS)
- [ ] Approve the MACHINA bond, `registerWasm(...)` on prefix `SECURITY_REVIEW`
- [ ] Track the status through remote check → Stage 1 → confirmation → competition
- [ ] If rejected: read the reason, fix, re-export (a new hash) and re-register.
      Budget 3 attempts.
- [ ] Showcase demo on Nov 20

### Phase M: Mission 10 benchmark, SECURITY_REVIEW (Nov 15 to 30), claimed on #198

Question: what does a verified correct `SECURITY_REVIEW` answer cost a buyer, and does the
network's ranking point buyers to the miners that give one? Every result must be reproducible
from committed data, with uncertainty stated.

- [x] M0 Reachability audit: 12/32 miners take a canonical request (`eval/reports/2026-11-15-miner-audit.md`)
- [x] M1 Round 1 pilot: 7 cases, 91 paid calls, rule frozen first (`eval/reports/2026-11-15-paid-benchmark.md`)
- [x] M2 Pre-register rule v2 before any round-2 call: fixes the pilot's weaknesses (unknown
      cases scored separately; buyer cost includes charged failures; Wilson 95% intervals;
      rank agreement with the node)
- [x] M3 Case set v2, selected by a fixed rule from OSV and deps.dev, not by looking at answers:
      6 ecosystems x (last affected version, latest clean release); 6 CWEs x (vulnerable, fixed)
      code twins; unknown package and unknown version; a small target-format probe
- [x] M4 Free baseline: a deterministic OSV lookup at $0, the bar a paid answer has to beat
- [ ] M5 Rounds 2 to 4 on three different days, every reachable miner plus auto-routing (round 2 done 11-16: `eval/reports/2026-11-16-round-2.md`; round 3 done 11-21 on escrow: `eval/reports/2026-11-21-round-3.md`)
- [x] M6 Engineering: unit tests for grading and statistics, CI on every push, a check
      that the committed data reproduces the published numbers
- [ ] M7 Close the loop to evaluation: (a) our adapter vs the node ranking on real miner
      answers; (b) real failure answers turned into reviewed preference pairs for the pool
- [ ] M8 Report and `/progress` after each round; final `/submit` on #198 and the Anjoman form
- [x] M9 Verified Ask: buyer-side check of package answers against OSV, deps.dev and
      rubygems.org; replay over rounds 2 and 3 (`eval/reports/2026-11-22-verified-ask.md`);
      hardened for exposure (token off loopback, rate limit, atomic cache)

### Phase N: A Mind that audits dependencies with verified Telegraph answers (optional, after round 4)

Proposed by the Telegraph team in the builders channel (11-22): build a Mind (Minds by Animoca
Brands, hellominds.ai) that uses Telegraph through Anjoman for a hard multi-step job, test it
with and without Telegraph, and make a demo video. Not yet confirmed as a rewarded bounty.

**Researched 11-22 (docs only; nothing signed up for or spent):**

| Question | Finding | Source |
|---|---|---|
| What a Mind is | An agent with identity, memory and background jobs; made no-code, or from the `minds` CLI or `@animocabrands/minds-client-lib` (Node 22+) with a Builder API key | hellominds.ai/faq, build.hellominds.ai/docs |
| Custom tools (our API, an MCP server, scripts) | **Not documented.** Tools, Skills and Apps come from the curated Marketplace; Skills are built by the Mind from a chat description; external services are connected as platform apps with a key | llms.txt, docs/guides/building-skills |
| Telegraph or Anjoman inside Minds | **Not documented** on either site | both sites |
| Driving a Mind from our code | **Documented:** `minds send <alias> "..." --wait`, `minds history`, `minds events`; library `sendMessage`, `waitForReply`, `subscribeEvents`. Replies are free text | docs/get-started/cli, client-library |
| Builder access | "Unlock Builder Access" is shown with no stated requirements | docs/get-started/account-setup |
| Cost | Credits ("Cognition"): US$10 per 1,000, burned per reasoning step or tool call, rate not published; 200 free per new Mind plus a daily top-up | hellominds.ai/pricing |
| Wallet or x402 in Minds | Not a current feature (described as future) | hellominds.ai/about |
| Anjoman MCP | Local stdio (`npx -y @telegraphprotocol/telegraph-protocol-mcp`), wallet or API key; tools `telegraph_ask`, `telegraph_ask_miner`, `telegraph_find_miners`, `telegraph_ranking` and more; default limits $0.50 per ask, $5 per day | anjoman.ai/docs/using/mcp-server |
| Anjoman Skill and API | Agent Skill (SKILL.md + Node script) for command-running agents; REST at backend.telegraphprotocol.com with `anjoman_` keys, 30 requests per minute | anjoman.ai/docs/using/anjoman-skill, api-keys |

**Design, given the above.** A Mind can't call our code or the Anjoman MCP directly (as far as
the docs say), so our code orchestrates and the Mind reasons:

1. Input: a dependency list (`package.json`, `requirements.txt`), 20 to 50 packages.
2. Our orchestrator asks Telegraph miners per package (Anjoman API key or our escrow runner),
   runs each answer through Verified Ask, and re-asks another miner (picked from benchmark data)
   when an answer is contradicted or has no verdict.
3. It sends the Mind the evidence (labels, cited advisories, OSV ids) with `minds send`; the Mind
   writes the audit report and explains what is uncertain. Code questions stay "unchecked".
4. The with/without test, scored on our benchmark cases with frozen truth:
   (a) the Mind alone, (b) the Mind with Telegraph answers trusted as given, (c) the Mind with
   Telegraph answers plus Verified Ask. Report accuracy, completeness, cost and time per arm.
5. Demo video: a request, providers answering, one caught (for example an advisory about
   another package), a re-ask, and the report with its evidence.

- [ ] N0 Ask the Telegraph team: how did they connect Anjoman to a Mind (a Marketplace app, the
      Skill?), is this rewarded, and what are the Builder access rules
- [ ] N1 Builder account and API key; one Mind; check that `minds send --wait` works and what a
      reply costs in Cognition
- [ ] N2 Orchestrator (`mind/`): dependency list in, Telegraph asks plus Verified Ask, evidence
      to the Mind, report out. Spend caps on both Telegraph and Cognition
- [ ] N3 Three-arm test on the benchmark package cases; report in `eval/reports/`
- [ ] N4 Demo video (2 to 4 min)

**Gates:** don't start before round 4 and its pooled report are committed, and don't let it take
time from the independent test set (deadline Nov 26). Stop at N1 if a Mind can't be reached from
code, or if Cognition per task makes the test unaffordable.

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

## Your next steps

See [`docs/ACTION_PLAN.md`](docs/ACTION_PLAN.md) (detailed, ordered, with done-criteria).

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
