# Project Memory

The durable record of what we know, what we decided and why, and where things stand.
**Update it after every network action, decision or surprise.** Newest entries go first
within each section.

---

## Live state

| Item | Value | As of |
|---|---|---|
| Our contributor address | _not created_ | |
| Our bond / fee address | _not created_ | |
| Bounty claims | **#96 claimed 11-12** by Ritapossible (bot confirmed; unfunded issue, prizes per H2 rules). First `/progress` posted 11-12 ~13:57 local (bot: "Progress recorded"); **next due by 11-15 ~13:57**, then every ≤ 72 h. Also claimed by zkasuran (0x8b22…, discloses running a miner on this intent) | 11-12 |
| Public posts (11-12) | Discord #showcase thread "AdversarialEval" (tag Evaluators): intro + progress + reviewer request; bounties repo starred; the 3 organizer questions (open questions 5–7) posted, awaiting answers | 11-12 |
| Demo page (11-12) | "Spot the Flaw": 17 public-train pairs across F1–F10; shortcut judges 8/17 (longer), 5/17 (keywords). Adapter choices come from **cpu-v4-demoheld** (trained without the 17 + 7 same-advisory twins): 13/17 and 11/17 (10 right in both runs, 3 wrong in both). Preview https://claude.ai/artifact/H5j9paVdwFQSJhnvxepd12 (private). Public hosting: GitHub Pages workflow ready, or Vercel (root dir `site`), user's choice | 11-12 |
| cpu-v4-demoheld (11-12) | 240 pairs: val 71.3% / 64.4% (mean 67.9% vs cpu-v3 73.6%); dropping 24 mostly hand-written pairs cost ~6 points, hand-written val 81% → 70.5%. Report `eval/reports/2026-11-12-demoheld.md` | 11-12 |
| Telegraph team guidance (11-13) | "Sign up on anjoman.ai and that's it, you're already in" (that is the hackathon registration). They "especially need evaluation material … independently sourced … from multiple contributors", even on claimed Intents; flow: `/claim` the bounty, follow its requirements, submit material at anjoman.ai/dashboard/eval. Bounty #96 Part 1: worse answers "believable but wrong, about as long as the better one, and different every time"; rows must end `eligible`; source links per row. Part 2: adapter live on SECURITY_REVIEW. Issue closes only when both parts are maintainer-verified | 11-13 |
| Anjoman dashboard (11-13) | anjoman.ai/dashboard/eval is the official web UI for the SAME Evaluators track (the H2 Build page links the track to it): publish an adapter or contribute evaluation data; sign-in gated. The dashboard also has Wallet, Faucet (testnet tokens) and My registrations. Not yet explored behind sign-in. A Telegraph reply to a miner author says test tokens come from that faucet | 11-13 |
| #96 thread intel (11-12) | another contributor (0xDB6c…) reports 114 rows admitted to the pool (127 quarantined rate_limited, 7 near_duplicate) from 248 programmatic Composer/FriendsOfPHP questions, `source_kind` "api", per-row source URL | 11-12 |
| Dataset | 59 public train + 14 validation pairs (Claude drafts, unreviewed); 26 OSV-verified sources | 11-08 |
| Data check | kit dataset gate PASS on train; naive scorers ≤ 58% overall; per-family tells remain (report 11-08) | 11-08 |
| Our pool rows (SECURITY_REVIEW_GENERAL) | 0 | 11-04 |
| Our registrations | none | 11-04 |
| Executor URL | _not deployed_ | |
| Dataset (11-10) | train 252 pairs (95 hand + 146 OSV-generated + 11 targeted), validation 39, test 0 (awaiting reviewers); every naive scorer ≤ 54% | 11-10 |
| Validation (11-11) | 87 pairs: 39 hand-written second voice + 48 held-out generated minimal pairs (13 packages disjoint from training) | 11-11 |
| Seed variance (11-11) | cpu-v1 config: seed 13 = 76.9%, seed 7 = 87.2% on the 39 hand-written pairs, about 10 points apart | 11-11 |
| **Polarity shortcut** (11-11) | the 95-pair model scores F2-in 100% / F2-out 0% on minimal pairs (train and held-out alike). It prefers the "vulnerable" answer and hasn't learned version comparison. Hand-written validation hid it | 11-11 |
| cpu-v2 two seeds (11-11) | 252 pairs: seed 7 = 74.7%, seed 13 = 69.0% on val 87 (mean about 72%). Shortcut break replicates (F2-out 64% both); version reasoning doesn't (F2 52% on seed 13; range-in-prompt 8/9 vs 4/9) | 11-11 |
| cpu-v3 two seeds (11-11) | 264 pairs (+12 batch-F coverage): seed 7 = 72.4%, seed 13 = 74.7% on val 87 (mean 73.6%, +1.7 vs cpu-v2, inside seed noise). Lower CIs 62–65%. Batch F's own targets (Java deserialisation, defusedxml) still wrong on both seeds; no shortcut regression (F2-out 73% / F2-in 42%) | 11-11 |
| Seed merge U8 (11-11) | exact rank-16 merge of cpu-v3 seeds = 70.1% (mean) / 67.8% (sum), worse than either seed; seeds are orthogonal (head cos 0.01, LoRA cos ≈ 0). Score ensemble 75.9% but not deployable. Merged package passes Stage 1 (not registered). Report `eval/reports/2026-11-11-merge-cpu-v3.md` | 11-11 |
| Remote-check rehearsal (11-11) | cpu-v3-seed13 package (`0xd70b3b61…df1a`, not registered) via the node's own client → local adapterexec → real engine: echo OK, wrong hash rejected, WASM = PyTorch order on 87/87 pairs (max diff 8.4e-5), 74.7%; 15-pair draws passed 4 of 6. Report `eval/reports/2026-11-11-rehearsal-cpu-v3-seed13.md` | 11-11 |
| Pool candidates (11-13) | **86 pairs** (regenerated 11-13 to meet bounty #96's "about as long as the better one": every pair within 1.25× length, median 1.02, and a random choice of which side is longer, so longer-wins is 53%), 17 packages (list in `data/private/pool_packages.json`), labels OSV-verified, kit gate PASS, naive ≤ 55%; 0 reviewed | 11-13 |
| Best run | cpu-v1 (rank 8, lr 2e-4, epoch 3 of 6): **76.9% on 39 validation pairs**, 97.9% train; weakest on Secure verdicts (55%) and F5/F6 (60%). Validation picked the epoch, so it's optimistic; a clean test split is needed | 11-10 |
| Latest adapter keccak256 | cpu-v0 smoke package `0x1a4e6750…45dd` (passes node Stage 1 locally; NOT registered; 61.5% on validation, below the 70% floor) | 11-10 |

### Network snapshot, update 11-10

SECURITY_REVIEW: canonical still #42 (71.43%). The pool is now 85 rows from 8 contributors, with 32 miners. Challenger #216 (0x8b22…, Nov 6) was rejected at the remote check: 8/15 (53.3%).

### Network snapshot (testnet `devnode.telegraphprotocol.com`, epoch ≈ 2011)

| Intent | Canonical | Score | Pool rows / contributors | Miners |
|---|---|---|---|---|
| SECURITY_REVIEW | #42 (0x3035…1bc0) | 71.43% / 21 pairs | 55 / 6 | 26 |
| SMART_CONTRACT_AUDIT | none | — | 0 / 0 | 15 |
| VULNERABILITY_TRIAGE | #37 (0x3035…) | 83.33% / 30 | 316 / 7 | 36 |
| SANCTIONS_SCREENING_MATCH | none | — | 485 / 8 | 16 |
| CODE_REVIEW | #27 (0x3035…) | 91.30% / 23 | 70 / 10 | 14 |

Refresh commands:
```bash
N=https://devnode.telegraphprotocol.com
curl -s "$N/api/wasm?resolve=SECURITY_REVIEW"
curl -s "$N/api/evalpool/status?intent_id=SECURITY_REVIEW_GENERAL"
curl -s "$N/engine/v1/intents/SECURITY_REVIEW"
```

---

## Durable facts (verified 2026-11-04)

### Protocol and format
- Since **2026-10-30** an adapter is a **safetensors delta** (LoRA plus reward head), never a
  full `.wasm`. The bounty issue text still says ".wasm", which is outdated.
- The Foundation is `modernbert-base-lora16-v1`, foundation sha256 `0a49b325304bb4cf292e683929689d0457966be264f60bfc94d0072b614bf8e6`,
  engine `77643d6e1176ab8744801cef93ccb844d0136ed32b8daa865d541f37d13292de`, tokenizer
  `67bc76f8b9386efba1a761c1c8e5ad439fd0eaf1c2826e9dd1a205c7af4dc456`, foundation.json
  `f7de64b999acd3f735118fbe5999abf251fdf188f9797e3a4e36c54ee9e4dbbe`.
- The kit is `telegraphprotocol/telegraph-wasm-baseline` @ `1ed063e2f0066cfaf0e124d66ec6a17b7a6121fd` (Nov 1).
- Rendered input: `### Task:\n{prompt}\n\n### Answer:\n{answer}`, **max 512 tokens**.
- LoRA: plain PEFT, r ≤ 16, targets ⊂ {Wqkv, Wo, Wi}, one alpha, no DoRA or rsLoRA. Defaults
  r=8, α=32, lr 1e-4, 3 epochs, grad-accum 16. The loss is Bradley–Terry.
- Intent pools live on the **`_GENERAL` child** (e.g. `SECURITY_REVIEW_GENERAL`). Register the
  adapter on the **family prefix** (`SECURITY_REVIEW`).
- `SECURITY_REVIEW` class = **judgment**. `SMART_CONTRACT_AUDIT_GENERAL` = judgment.

### Gates
- Kit dataset gate: ≥ 80% unique rejected; no single rejected answer > 2%; chosen == rejected ≤ 1%;
  longer/shorter-wins ≤ 65%; question-blind BoW ≤ 65%; held-out leakage ≤ 10%.
- Kit eval gate: held-out ≥ 65% and ≥ +10 points over longer-wins.
- Node: a remote check on **15 public pairs (all contributors)** ≥ 70% → hash → Stage 1 →
  bit-exact confirmation → hidden split ≥ 70% (≥ 60% per child) **and ≥ incumbent + 2 points**.
- Remote check failures retry at most 3 times; the budget is 30 min. Replies ≤ 64 KiB; no redirects;
  private IPs are refused.

### Eval pool
- The pool is used only after **≥ 5 distinct contributors**. Samples draw *evenly across
  contributors*.
- Provenance: an `http(s)` `source_url` → `attested`. `source_kind` ∈ {llm, synthetic,
  generated, model} → always `unverified`.
- Prompt 16–16k chars, answers 8–32k chars. A prompt ≥ 85% similar to an existing one is
  rejected. 5,000 rows a day per contributor per Intent. Once the pool reaches 200 rows,
  no contributor may hold more than 50%.
- Rows go to a hidden **testing** half or a miner-visible **ranking** half. We don't choose
  which. Frozen at each epoch rollover (testnet epoch ≈ 1 h).
- Testnet chain id `11155111` (Sepolia). Upload with `curl --data-binary`, never `-d`.

### Hackathon
- Evaluators prizes: 4 × $300 delivery, $500 / $300 excellence. A team can win one of each.
- Delivery tie-break: **proven measurement improvement or valuable new coverage**, then
  validity score.
- Judging out of 100 (70 to win; technical ≥ 24/35): Technical 35, Commercial 25,
  Growth/education 20, Adoption 10, Integration 5, Reproducibility 5. Stars and likes score 0.
- Submission: team, track, missions/Intents, a working link, a 2–5 min demo, run
  instructions, evidence, a public summary, and showcase permissions.
- Dates: Nov 14 milestone, Nov 20 showcase, **Dec 1 23:59 UTC deadline**, judging Dec 2–8,
  results from Dec 9 (72 h to appeal).

### Competition intel
- 0x3035… seeded about 10 first-Canonical adapters on Nov 1. They're generic baselines.
- 0x8b22… (zkasuran) challengers all failed the **remote check**: CODE_REVIEW 13.3%,
  EMAIL_SECURITY 53.3%, THREAT_INTELLIGENCE 53.3%. Another was rejected for
  `class_mismatch` (it exported `hybrid` for a judgment Intent).
- Bounty #96 claimant Iniwura (FALSUM) submitted 20 pairs and **no adapter**. Their LoRA
  failed "contextual reversal" tests (0/2).

---

## Decisions

| Date | Decision | Why |
|---|---|---|
| 11-04 | Primary Intent `SECURITY_REVIEW`, stretch `SMART_CONTRACT_AUDIT` | The weakest security incumbent (71.43%), the most miners, a P1 bounty. SCA is greenfield coverage. |
| 11-04 | Drop media forensics / deepfake | Text-only foundation; those answers are about images |
| 11-04 | Public and pool datasets strictly disjoint | Don't leak hidden testing-half rows |
| 11-04 | Don't fork the kit; train with it unmodified | Bit-exact node compatibility |
| 11-04 | Validation set in a second "voice" | The remote check and hidden sample draw from other contributors; an in-style validation set overstates accuracy |
| 11-12 | External review (Grok) triaged: polarity shortcut and U1 structure were already done (stale snapshot); length "bias" rejected after measurement (59% of train pairs exceed 1.25, but split 72 chosen-longer / 84 rejected-longer; longer-wins 55%; padding probe 100%), so per-pair ratio warnings became a per-split summary; accepted: OSV range unit tests, an exact 2x dedup speedup | Verify claims against the repo before acting on them |
| 11-12 | Rules audit against the official H2 rules: fixed README overclaims ("registered on-chain", stale single-seed 76.9%), added `NOTICE.md` (CC BY 4.0 attribution for cached GHSA records, reused components, AI assistance), disclosed hackathon/prize in the outreach text, corrected the validation-publication line. Biggest open requirement: a real Telegraph integration with genuine evidence (pool upload/registration) | `docs/SUBMISSION_CHECKLIST.md` → Rules compliance |
| 11-12 | Registration-risk update: a failed registration costs gas, about 1.5 h, a new package hash, and the $5 bond locked until deregister + 2 days. It is never slashed (docs). The ~80% independent-test bar stays because the remote check needs 11/15 and the competition needs incumbent + 2 points, but money is no longer the reason. After any rejection: `deregisterEntity(id, 2)`, then `withdrawMinerBond()` after 2 days | Verified in the official docs, not taken from a second AI's summary |
| 11-11 | Registration bar raised: register only when independent-test accuracy is about **80% or more** (and the lower CI bound is above 70%), not "lower bound above 72%" | The remote check draws only 15 pairs and needs 11 right. P(pass) is 52% at a true 70%, 69% at 75%, 84% at 80% and 94% at 85% (binomial). The local rehearsal showed the same adapter passing and failing different 15-pair draws |
| 11-11 | Pool candidates are generated from a third, disjoint package set; their output, ids and caches live only under `data/private/`; upload requires a human `approve` per row | Which advisories sit in the hidden pool must not leak through committed caches; the spec forbids uploading unreviewed rows |
| 11-11 | No seed-merged submission (U8 closed, negative). Choose the submitted seed by a pre-fixed rule on the independent test split | Different kit seeds give different inits, so weight averaging lands between basins; a shared-init soup would need a kit change |
| 11-11 | Stop hand-writing single targeted pairs; next gains come from independent data (U1–U3) and variance reduction (U8) | cpu-v3: 12 targeted pairs gave +1.7 points (noise) and didn't fix their own target concepts |
| 11-11 | Don't claim version-range robustness. F2 is a shortcut breaker and pool material, not a capability claim | The range-in-prompt effect didn't replicate across seeds |
| 11-11 | Report every training result as a mean over at least 2 seeds | Seeds differ by 6–10 points on the same data |
| 11-11 | Every run is also scored on held-out generated minimal pairs, reported by source and pair kind | Hand-written validation hid a 0%/100% polarity shortcut |
| 11-10 | Audit adopted (`docs/AUDIT_2026-11-10.md`): independent evidence first, programmatic OSV minimal pairs, error-mining loop, honest taxonomy scope | The best number so far is self-graded; competitors keep dying at the remote check from distribution shift |
| 11-10 | SMART_CONTRACT_AUDIT dropped as an adapter target (material only) | Depth on one Intent beats breadth |
| 11-10 | Add a separate test split before any registration decision | Validation is used for early stopping and tuning, so it's no longer an unbiased estimate |
| 11-10 | Training on CPU in this container is viable (about 7–13 min per run) | A GPU isn't needed at this data size |
| 11-08 | Chosen answers make scoped claims only ("not affected by X"), never "no known vulnerabilities" | Absolute claims go stale as new advisories land, which silently flips labels |
| 11-08 | Every advisory fact comes from OSV (`tools/fetch_sources.py`), and `build.py` rejects unverified ids | Two of our own id comments were wrong on the first fetch (GHSA-h75v… is Jinja2, not vm2) |
| 11-08 | The kit gate governs train and pool sets; validation is reported only | The kit gate's repeat check is meaningless below about 50 rows |
| 11-04 | Contextual reversal (F4) is a core family | It's a documented failure of another contributor's LoRA, and likely the incumbent's too |

---

## Open questions (ask the organizers)

1. May we publish rows we also uploaded to the pool, or must the public set be disjoint?
   We assume disjoint.
2. Does the remote check sample only the ranking half, or any public pairs?
3. Does a testnet Canonical slot carry over to mainnet, or is it re-run there?
4. The incumbents use `http://…sslip.io` URLs, but the docs require `https://`. Which is enforced?
5. Is AI-assisted authoring fine if every row cites a real `source_url`, and what `source_kind`
   should it carry? (Our pool candidates are *programmatic*: OSV facts, labels checked by
   OSV's version query, templated text. We currently send `advisory`.) **Docs (verified
   11-12):** an `http(s)` `source_url` makes a row `attested` unless `source_kind` is `llm`,
   `synthetic`, `generated` or `model`; no list of recommended values (the sample uses
   `human`). So `advisory` + GHSA URL is attested. Another #96 contributor uses `api`.
   Still asked on Discord whether the team prefers a value.
6. ~~Ranking half readable?~~ **Answered (docs, verified 11-12): no.** "Rows are never shown
   back. The endpoints on this page return counts, states and row identities, never row
   content." Testing half: "Nobody outside the validators"; ranking half: "Miners, since they
   have to answer it." (anjoman.ai/docs/scoring/contribute-evaluation-data; docs.telegraphprotocol.com redirects there)
7. ~~Bond lost on rejection?~~ **Answered (docs, verified 11-12): never slashed.** "The bond is
   returned in full when you deregister and is never slashed." Deregister with
   `deregisterEntity(registrationId, 2)` from the registering address, then "withdraw it after
   2 days with `withdrawMinerBond()`". The docs don't say whether a *rejected* registration
   auto-releases it, so plan to call deregister after any rejection (anjoman.ai/docs/scoring/build-a-scoring-module).

---

## Gotchas

- OSV ids are **case-sensitive** (`GHSA-` + lowercase). Uppercased GHSA lookups always 404, which once made unverified "fabricated" ids look verified. Many CVEs exist only as aliases (e.g. CVE-2023-6014), so check aliases too.
- OSV records can disagree with their own aliases on affected ranges (jinja2 GHSA-fqh9: fixed 2.7.2 vs PYSEC-2014-82: 2.7.3). Generated labels must pass `tools/verify_generated.py`; ambiguous advisories go in `data/sources/ambiguous_advisories.txt`.
- Don't edit `scripts/train.sh` while a run is executing it: bash reads scripts incrementally.
- `train.sh` rebuilds the train file at start, so pin `TRAIN=` for controlled comparisons (seed studies).

- **Kit bugs at `1ed063e`** (see `docs/UPSTREAM_ISSUES.md`):
  - (1) `train_adapter` exits 1 after a PASS (NameError `pkg`). Read `result.json`'s verdict instead.
  - (2) `export_adapter` refuses runs trained on today's HF tokenizer download (same ids, different bytes). Use `scripts/export.sh`.
  - (3) Offline `adapterbuild` says SECURITY_REVIEW needs "hybrid". The node says **judgment**. Use `tools/stage1check`.
  - (4) Export is non-deterministic (random metadata key order), so export once and archive the exact file.

- **`data/private/` is git-ignored, so it is lost when the cloud container is reclaimed.** Keep
  the pool set somewhere durable outside git (a local machine or a private repo) before
  authoring it here.
- Seed pairs are `claude-draft`, `reviewed: false`. A human must review them before pool
  upload, and they must never be labelled `source_kind: human` unreviewed.
- First seed batch: chosen-longer was 100% until the rejected answers were rebalanced. Check
  length per family, not just overall.

- `curl -d` strips newlines → `signer_mismatch`. Always use `--data-binary @file`.
- Export with `--class judgment` (a `hybrid` export on a judgment Intent → `class_mismatch`).
- Re-registering the same hash reverts (`duplicate wasm hash`). Every change needs a new export.
- A host that re-encodes files breaks the keccak256. Use GitHub raw at a commit SHA, or IPFS.
- If training used `--max-length < 512`, export with the same `--max-tokens`.
- Only the reference `adapterexec` gives bit-exact scores. Native ONNX Runtime doesn't.
- Bounty claims lapse without a `/progress` comment every 72 h.
