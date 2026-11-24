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
- [x] U1 (11-24: 40 pairs, Fexx 20 + Lino 20, every shortcut judge <= 60%) Frozen test split `data/test/` by outside reviewers. **Done (Claude):** split support, `docs/REVIEWER_GUIDE.md`, CSV template, importer, `docs/OUTREACH.md`. **Open (you):** recruit 2–3 reviewers
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
- [x] M5 Rounds 2 to 4 on three different days, every reachable miner plus auto-routing (round 2 done 11-16: `eval/reports/2026-11-16-round-2.md`; round 3 done 11-21 on escrow: `eval/reports/2026-11-21-round-3.md`; round 4 and pooled 11-22: `eval/reports/2026-11-22-rounds-2-4.md`)
- [x] M6 Engineering: unit tests for grading and statistics, CI on every push, a check
      that the committed data reproduces the published numbers
- [ ] M7 Close the loop to evaluation: (a) our adapter vs the node ranking on real miner
      answers; (b) real failure answers turned into reviewed preference pairs for the pool
- [ ] M8 Report and `/progress` after each round; final `/submit` on #198 and the Anjoman form
- [x] M9 Verified Ask: buyer-side check of package answers against OSV, deps.dev and
      rubygems.org; replay over rounds 2 and 3 (`eval/reports/2026-11-22-verified-ask.md`);
      hardened for exposure (token off loopback, rate limit, atomic cache)

### Phase A: A customer-first app for Mission 10 (Apps & Agents track)

**Telegraph's feedback to another builder (Athar's Tina, which buys each question from three miners; read 22 Nov), taken as the rules for this phase:**
- Don't buy the same question from several miners by default: the user pays about 3x for what
  ranked routing is meant to deliver at 1x. Independent verification only where it is worth it.
- The goal is that the best providers get evaluated and ranked, so users don't compare answers.
- Start from one commercial mission and work backwards: the customer, their problem, the outcome
  they would pay for, the capabilities needed. Then build a complete application around it.
- Apps & Agents and Evaluators are judged separately; final submission via anjoman.ai (form not
  live yet). Evidence per track: `docs/SUBMISSION_EVIDENCE.md`.

**Customer and problem (Mission 10, routes 1 and 2).** The mission names "coding-agent
developers" whose model choices use "static benchmarks or token price, not cost per correct".
Our customer: a team whose coding agent (or CI) adds and upgrades dependencies, and that must
not ship a known-vulnerable version. The outcome they'd pay for: every dependency change gets a
security answer they can act on automatically (pass, block, or flag for a person), at a known
cost, with a receipt and the evidence.

**App: Dependency Gate.**
1. Trigger: a dependency change (a PR diff, or a manifest).
2. **One** paid `SECURITY_REVIEW_GENERAL` call per changed package, through ranked routing or the
   best-value provider from the leaderboard (1x cost).
3. **Free** check of that answer with Verified Ask (OSV, deps.dev, rubygems.org; no extra miner).
4. Action: verified "Secure" passes; verified vulnerable blocks with the advisories. Only when the
   free check proves an answer wrong, or it has no verdict, does it re-ask **one** next provider;
   if still unresolved, flag for a person. Never 3x by default.
5. Output: a PR comment or report with the decision, the evidence, cost and receipts.
6. **Leaderboard (route 1):** the benchmark becomes a small scheduled sample (not every request)
   publishing cost per verified correct answer per provider. That is the evaluation the feedback
   asks for, and it feeds provider choice. Verified outcomes are also candidate pool material for
   the Evaluators track.
7. Tests the mission requires: wrong, partial and unanswerable cases; unknown kept apart from
   incorrect (unknown package and version cases already exist).

- [ ] A0 Confirm the fit with Telegraph in one line (customer, route, 1x design) before building
- [ ] A1 `gate/`: manifest diff in, one paid call per package, Verified Ask, decision, receipt out;
      spend caps; CLI first, then a GitHub Action. **Calls go through Anjoman's existing
      integration, not our own payment code** (Telegraph: "use our existing Anjoman integrations
      rather than rebuilding the intelligence layer"): `POST backend.telegraphprotocol.com/engine/ask`
      with `intent: SECURITY_REVIEW_GENERAL`, `params: {target}` and an `anjoman_` API key, or the
      Skill's `auto --intent ... --params ...`. Both report cost and a receipt. The key is entered
      through the session's credential form, never in chat or the repo. `bench/run.mjs` (escrow)
      stays for the benchmark only.
- [ ] A2 Measure against the benchmark cases: decisions correct, blocked wrongly, flagged, cost
      per decision, versus (a) trusting ranked routing alone, (b) the free OSV lookup alone
- [ ] A3 Scheduled leaderboard from a small sample; public page on the site
- [ ] A4 One outside user or builder runs it (adoption counts for 10 of the 100 points)
- [ ] A5 Demo video, docs, submission via anjoman.ai

## Nov 24 checklist

Owner: edit the Apps submission's live link to adversarialeval.vercel.app/#apps; chase the second
independent test author (20 pairs by Nov 25, cutoff Nov 26); say which defiplusacademy pairs were
read; post `/progress` on #198 by Nov 25; post in the Solana thread; faucet top-up; Qwen API key
if the Qwen demo goes ahead.
Claude: run Dependency.Guard on real packages (receipts to `mind/evidence/`); draft `/progress`;
on the owner's go: Qwen demo prep (find a real Qwen-based app), Pay.sh docs (S5), the 8 short rows,
the Solana clip (S3).

Improvements to our own build (when the owner says go):
- Site: a plain "What we don't claim" section (testnet, small samples, the Mind's rule is not a sandbox).
- Site: adoption evidence (another team's miner trained on our public pairs and reports its score).
- Site: one evidence row per Dependency.Guard decision (package, verdict, advisory link, receipt).
- Benchmark: how many independent providers sit behind the miners we paid (distinct pay-to
  addresses in our own payment records); free, from data we already have.
- Solana run: add named frontier models answering alone, reported as right / wrong / couldn't tell.
- Sign each run file so a changed result fails verification (fits the Solana decision receipt).

### Phase S: Dependency.Guard for Solana builders (after the video; before or instead of Phase P)

**Why.** Telegraph's Solana announcement (23 Nov) asks for verified intelligence that Solana
agents and apps can buy, using real Solana data, paid Telegraph requests, hard test cases and a
comparison with frontier models, as working applications rather than concepts. Our strongest fit
is idea 1 (verified intelligence for Solana AI agents), done by extending what already works
instead of starting a new project.

**What we found (23 Nov).** The relevant intents exist but are not Solana-specific:
VALIDATOR_PERFORMANCE_VERIFY_GENERAL takes an Ethereum beacon-chain validator index;
CRYPTO_TRANSFER_VERIFY_GENERAL (24 miners) has no request or response format yet ("not ready"
on-chain); only two or three miners mention Solana. A real Solana case is in OSV:
`@solana/web3.js` 1.95.6 and 1.95.7 were hijacked releases with key-stealing malware
(GHSA-jcxm-7wvp-g6p5, CVE-2024-54134, MAL-2024-11183); 1.95.8 is clean.

**Scope (about one day).**
1. A Solana dependency case set, fixed by rule before any call, truth from OSV and frozen: the
   Solana stack on npm and crates.io (`@solana/web3.js` malicious and clean versions, wallet and
   SPL libraries, Anchor and the Rust crates Solana programs depend on, such as ed25519 and
   curve25519 implementations), affected and clean versions, plus one non-existent version.
2. The same three arms as the main comparison: Telegraph's routed answer trusted, Telegraph plus
   Verified Ask, and the Mind alone; the Mind runs the in-Minds flow on a sample for the demo.
3. Optional: pay through the node's Solana devnet USDC rail (x402 exact) for a Solana-settled
   variant; today the Mind pays through Anjoman's escrow on Ethereum Sepolia.
4. Post in the Solana thread: which idea, intents, data sources, results and limits.

- [x] S1 Solana case set and rule, committed before calls
- [x] S2 Three-arm run; report (`eval/reports/2026-11-23-solana-dependencies.md`)
- [ ] S3 Demo clip and post in the Solana thread
- [ ] S4 (optional) Solana devnet USDC payment path

**Update (23 Nov, second announcement: five priority use cases).** Telegraph now names five Solana
use cases and wants 3 to 5 working applications with real Solana functionality, paid Telegraph
requests, independent verification, measurable results against frontier models, commercial value,
demo video and X post. Ours maps to **use case 3, Verified Intelligence Economy (Telegraph x
Pay.sh)**: agents buy specialist intelligence chosen by independent evaluation instead of by API
listing, compared against a frontier model and direct paid API selection, measuring correctness,
cost, latency and task fulfilment. What we already have for it: the paid market benchmark (listing
order vs evaluated choice: the default route 21% vs the best miner 83%, pooled), Verified Ask as
independent verification, and three-arm tests with receipts. Full plan (product, buyers, four
arms, hard cases, Solana payment, deliverables, order of work): `docs/SOLANA_USE_CASE_3.md`.
Not started; gaps, in order:

- [ ] S5 Read the use-case post and Pay.sh's docs; confirm what "Telegraph x Pay.sh" needs (no claims
      about Pay.sh until read)
- [ ] S6 Pay on Solana: one paid Telegraph request settled in Solana devnet USDC (node's x402 Solana
      rail, or Pay.sh), with the receipt checked on-chain (absorbs S4)
- [ ] S7 A fourth arm, "direct paid API selection": the provider an agent would pick from a listing,
      next to the evaluated choice, the frontier model alone, and evaluated + Verified Ask
- [ ] S8 Harder Solana cases, where the frontier model alone is not already perfect (the 16-case set
      was easy: every arm got every real version right)
- [ ] S9 Commercial case in one page: who pays (teams shipping Solana agents and wallets), for what,
      and the price per check against the cost of a wrong PASS

### Phase P: CODE_PATCH_VERIFY (after the video, the test set and the submission are safe)

**Why.** Telegraph's 22 Nov announcement asks for specialist intelligence where frontier models
fail: live data and independently verifiable findings. Our own results show SECURITY_REVIEW for
known CVEs is not that (a Mind with a free OSV lookup matched every paid answer). Whether a given
commit or pull request passed CI *is*: a model can't know it, and the CI provider's API can prove
it. Mission 10, area 1 of the announcement (CODE_PATCH_VERIFY, REGRESSION_VERIFY).

**What the network looks like (checked 22 Nov).** The intent is `CODE_PATCH_VERIFY_GENERAL`
(request `patch`: repository and commit, PR or CI run, at most 256 bytes; response `conclusion`
from success/failure/cancelled/skipped/neutral/timed_out/pending, `passed` (scored), and off-chain
`commit` and `pipeline`). It has **23 miners** (the parent `CODE_PATCH_VERIFY` shows 0, which
misled our first read) and an active evaluator adapter (registration 155). Most miners are generic
wrappers whose compatibility note says their endpoint has no field for `patch`; a few are serious
(zk-patchproof: GitHub, GitLab, CircleCI and Actions, with evidence digests; zk-runpin, zk-patchci,
zk-code-ci, a1-preflight). Same shape as the SECURITY_REVIEW market we benchmarked.

**Order, cheapest evidence first:**
1. **Benchmark the market (route 1, our method on a second intent).** A case set fixed by rule
   before any call, with truth read from the providers' APIs and frozen: public commits and PRs
   whose CI finished with success, failure, cancelled or skipped; one still running (pending);
   a commit with no CI; a commit that doesn't exist; a malformed request. Audit which miners take
   a canonical request (free), then one paid call per case and miner. Report accuracy, cost per
   correct answer, and which miners confuse "pending" or "no CI" with "passed".
   Budget: about 12 cases x the callable miners (likely 5 to 8) x $0.01 = $0.60 to $1.00.
2. **"Verified Ask for CI".** Extend Verified Ask to check a CODE_PATCH_VERIFY answer against
   the provider's API (does the commit exist, does `conclusion` match the check runs, is `passed`
   consistent with `conclusion`). Free for the buyer, like the package check. Lets the
   Dependency.Guard Mind also confirm that the PR applying an upgrade passed CI.
3. **Evaluation material (Evaluators track, another intent).** Pairs where the worse answer is
   plausible but wrong in one verifiable way: "success" while a required check failed, the merge
   commit's result reported for the PR head, "pending" reported as passed, `passed: true` with
   `conclusion: failure`. Same verification and length gates as the security pool.
4. **A miner, only if steps 1 and 2 show a gap the existing miners leave.** Then its pitch is
   measured, not claimed. Registration facts gathered 22 Nov: current Diamond
   0x72a70e949362670Bf8bceAd24eFC5b8f950aa08b (the 0x3624... one is retired; example scripts
   still point at it); `registerMiner(yamlUrl, sha256(yaml), feeAddress, minPriceUsdc >= 10000,
   intents)`; bond to be confirmed with `minerBondParams()` (docs conflict: MACHINA vs USDC vs 0);
   permissionless, activation about 10 to 15 minutes; 7-day grace period with a 5% traffic share.
   Hosting: a Vercel function next to Verified Ask, with a read-only GitHub token (unauthenticated
   GitHub allows only 60 requests per hour per IP).

- [ ] P1 Case set and rule for CODE_PATCH_VERIFY (truth from GitHub, GitLab and CircleCI APIs), committed before calls
- [ ] P2 Free audit of the 23 miners; paid round; report
- [ ] P3 Verified Ask for CI answers; wire into the Mind
- [ ] P4 Evaluation pairs for CODE_PATCH_VERIFY_GENERAL
- [ ] P5 Decide on a miner from P2/P3 evidence

**Gates:** after the demo video and the second test-set author (Nov 26). Stop at P2 if no
miner takes canonical requests (then the gap is integration, not intelligence, and a miner is
the right move after all).

### Phase N: A Mind front end for the Dependency Gate (optional, after Phase A works)

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

**Telegraph's guidance (Ahmed Ali, #hackathon, 11-19; screenshots from the user, 11-22).** What
the team wants to see in a Mind:
- it spots wrong or conflicting provider answers, investigates them with **different
  specialists** and **independent truth sources**, asks for what is missing, and **revises its
  conclusion** when the evidence changes;
- **persistence:** it remembers earlier findings, watches for changes, and sends a **proactive
  alert** explaining why its assessment changed;
- ideally **two Minds**: one investigates, one independently reviews the findings;
- the same cases **with and without Telegraph at a comparable budget**: errors caught, recovery,
  completeness, cost; also **unseen cases**; easy for another builder to reproduce;
- the whole run **recorded inside Minds** (setup, requests, evidence, costs, results). Video,
  repo and findings posted in #hackathon and on X, tagging `@telegraphprotoc`, `@ysiu`,
  `@marcmcg` and Minds;
- the recommended route is the **Anjoman Skill**, used with a high budget.

Other builders took finance and crypto Minds (supplier checks, counterparty checks, token risk).
None does security, so a dependency-security Mind is distinct. Two of them asked whether Minds
accept a Skill or a remote MCP URL; no answer was visible in the screenshots, which matches the gap
in the Minds docs.

**Design, given the above.** The docs don't show a way for a Mind to call our code or the Anjoman
MCP directly, so until Telegraph says otherwise, our code orchestrates and the Mind reasons:

1. **Investigator Mind.** Input: a dependency list (`package.json`, `requirements.txt`), 20 to 50
   packages. Our orchestrator asks Telegraph miners per package (Anjoman Skill or API key, or our
   escrow runner), **one call per package by default**, and runs each answer through Verified Ask
   (free). Only when the free check proves an answer wrong, or it has no verdict, does it re-ask one
   **different** miner (picked from benchmark reliability), within a set budget. The Mind gets the evidence with `minds send`, writes the
   audit, and says what is still uncertain. Code questions stay "unchecked".
2. **Reviewer Mind.** Gets the investigator's findings and the raw evidence, re-checks every
   claim against Verified Ask, and approves or disputes each finding.
3. **Watch mode.** The audit is remembered. A daily job re-queries OSV for the watched versions;
   when a new advisory appears (or a provider's answer changes), the investigator re-investigates
   and the Mind sends an alert saying what changed and why the assessment moved.
4. **Test, same cases and comparable budget:** (a) the Mind alone, (b) the Mind with Telegraph
   answers trusted as given, (c) the Mind with Telegraph, Verified Ask and re-asking. Scored on
   the benchmark's frozen package cases, plus unseen packages chosen by a fixed rule before
   running. Report errors caught, errors recovered, completeness, cost and time per arm.
5. **Demo video**, recorded inside Minds: a request, providers answering, one caught (for example
   an advisory about another package), a re-ask, the reviewer's check, the report with evidence,
   then a later alert.

- Checked 11-22: the Anjoman MCP is local stdio only (no HTTP transport); the integrations page
  lists Claude Desktop, Cursor, VS Code, Claude Code, Continue, Goose, Hermes, OpenClaw,
  LangChain, ElizaOS and "any MCP client", but not Minds. So driving the Mind from our code is
  still the documented-safe route. Telegraph also floated a general-purpose Mind; not for us
  (focus on security depth).
- **Unblocked 11-22 (Telegraph, Minds forum):** a Mind can use its **HTTP tool** with an Anjoman
  API key kept in Minds private credentials: `POST https://backend.telegraphprotocol.com/agent/chat`
  with `stream: false`; long jobs continue after a Minds timeout, so poll `GET /agent/jobs/{id}`;
  `GET /agent/spend` lists recent jobs. The Anjoman account needs a funded balance. A custom Mind
  Skill can be built around this; no need to wait for the Bazaar listing. Telegraph now asks every
  builder for **Mind IDs, working app links and demo videos**.
- **New design:** the whole flow runs inside the Mind. The Mind calls Anjoman (one
  SECURITY_REVIEW_GENERAL ask per package) and then a **hosted Verified Ask** endpoint (our Vercel
  site, token-protected) to check each answer; it re-asks only when the check proves the answer
  wrong, then passes, blocks or flags with cost and receipts. Phase A's Dependency Gate and this
  Mind share the same logic; the Mind is the customer-facing front end.
- [x] N0 Ask the Telegraph team (now in the Minds forum): can a Mind load the Anjoman Skill (or a remote MCP URL), or
      does it need an outside orchestrator? Is this rewarded? What do Builder access rules require?
- [x] N1a Host Verified Ask as a token-protected endpoint on the Vercel site (`site/api/verify.py`; live 11-22; VERIFY_TOKEN set, GET shows `configured:true`, POST needs the token). Setup guide: `mind/README.md`
- [x] N1 (user) Minds account and a Mind (Dependency.Guard, id 38266542-f36b-1410-8467-00039ce7df11); Anjoman API key in Minds private credentials; funded Anjoman balance; check that `minds send --wait` works and what a
      reply costs in Cognition
- [x] N2 Orchestrator (`mind/connector/guard.mjs`, 11-22; first end-to-end run with the Mind in `mind/evidence/`): dependency list in, Telegraph asks plus Verified Ask, evidence
      to the Mind, report out. Spend caps on both Telegraph and Cognition
- [x] N3 Watch mode (11-23): `mind/watch.py` re-checks every PASS and BLOCK for free; the daily `watch` GitHub job fails on an alert
- [x] N4 Three-arm tests: packages, code v2, Solana (`eval/reports/2026-11-22-mind-comparison.md`, `2026-11-22-code-review-v2.md`, `2026-11-23-solana-dependencies.md`)
- [x] N5 Demo video, repo and findings posted (11-23)

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
