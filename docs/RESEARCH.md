# Research: study brief

Researched 2026-11-04 from the official kit (`telegraphprotocol/telegraph-wasm-baseline`),
`telegraph-docs`, `telegraph-foundation`, the bounty board, the Season II rules page, and the
live testnet node (`devnode.telegraphprotocol.com`, epoch ~2011).

## 1. The live facts that should drive scope

| Intent (pool lives on `_GENERAL` child) | Class | Miners | Pool rows / contributors | Canonical evaluator | Bounty |
|---|---|---|---|---|---|
| **SECURITY_REVIEW** | judgment | 26 | 55 / 6 | #42, **71.43% on 21 pairs** (floor 70%) | #96, P1, mandatory Intent |
| SMART_CONTRACT_AUDIT | judgment | 15 | **0 / 0** | none | #128, P2, unclaimed |
| VULNERABILITY_TRIAGE | judgment | 36 | 316 / 7 | #37, 83.33% on 30 | #89, P1, in review |
| SANCTIONS_SCREENING_MATCH | judgment | 16 | 485 / 8 | none (both deregistered) | #78, P1, in review |
| CODE_REVIEW | judgment | 14 | 70 / 10 | #27, 91.30% on 23 | — |
| MEDIA_FORENSIC_VERIFY / DEEPFAKE_DETECTION | judgment | 13 / 12 | 0 / 0 | none | — |

**Recommendation: primary = `SECURITY_REVIEW`, stretch = `SMART_CONTRACT_AUDIT`.**

- SECURITY_REVIEW has the weakest incumbent of any security Intent: 71.43% means we
  need about **≥73.4% on the same hidden sample** (2-point replacement margin). It also has
  the most miner activity, a thin pool, a P1 bounty, and three missions behind it
  (Exchange, Model Economy, Web3/DeFi). The incumbent author `0x3035…` seeded
  first-canonical adapters on about 10 Intents on Nov 1, so these are generic baselines,
  not tuned ones.
- SMART_CONTRACT_AUDIT is greenfield: no material and no evaluator. A pool is used only
  after **5 distinct contributors**, so an adapter there will sit in
  `awaiting_compatible_material` until others contribute. Be a first contributor of
  material; register the adapter if the pool fills before Dec 1.
- Sanctions already has 485 rows, so our marginal value is lower. Media forensics answers
  are about images, which a text-only ModernBERT can't see, so skip it.

### SECURITY_REVIEW answer schema (what miners return, what we score)

- request: `target` (code, package, contract or site)
- `verdict` ∈ {Secure, Needs changes, Insecure}: processed
- `vulnerability_count`: **scored** number
- `issues`: CVE / GHSA / CWE / OWASP ids, most serious first (off-chain)
- `summary`: 1–2 sentences (off-chain)

Bounty #96 scope: find known CVEs, leaked credentials, misconfiguration and
injection-prone patterns in supplied code, dependencies, endpoints or config.

## 2. How scoring works (the parts that constrain the design)

- **Input the model sees:** `### Task:\n{prompt}\n\n### Answer:\n{answer}`, tokenized with the
  ModernBERT tokenizer, **truncated at 512 tokens** (closing `[SEP]` kept). The prompt and
  the answer share that budget. **The flaw that makes a rejected answer wrong must sit
  inside those 512 tokens**, ideally early. Keep the code snippets in prompts compact.
- **Output:** one reward logit. Pairwise ordering is all that matters.
- **Adapter:** plain PEFT LoRA on `answerdotai/ModernBERT-base`, r ≤ 16, targets ⊂
  {`Wqkv`,`Wo`,`Wi`}, a single alpha (no DoRA or rsLoRA), plus a 768→1 head. 178 F32 tensors,
  6.8 MB at r=8. The `.wasm` wording in the bounty text is outdated: since Oct 30 the
  format is a safetensors delta only.

### Gates, in order

1. **Kit dataset gate** (`train_adapter --check-data`, offline):
   - ≥ 80% unique `rejected` answers; no single `rejected` answer in > 2% of pairs; ≤ 1% where
     chosen == rejected
   - "pick the longer answer" (or the shorter one) right ≤ 65%
   - **a question-blind bag-of-words model right ≤ 65%** (this catches style tells)
   - ≤ 10% leakage of held-out rejected answers into training
2. **Kit eval gate:** ≥ 65% held-out accuracy and ≥ 10 points over "pick longer".
3. **Node remote check:** 15 **public pool pairs from all contributors**, ≥ 70% correct at
   our executor. Echoed hashes must match.
4. **Download + Stage 1** (hash, format) → **bit-exact confirmation** by the validator.
5. **Hidden competition:** ≥ 70% (≥ 60% per family child), and ≥ incumbent + 2 points.
   **Sampling draws evenly across contributors.**

**The real risk is point 3 and point 5, not the training script.** The hidden sample and
the remote check use *other people's* pairs, not ours. The last three challengers on
similar Intents (`0x8b22…`, regs #130, #131, #26) **all died at the remote check (13%, 53%,
53%)**. They overfit their own data style. The adapter has to learn the security judgment
itself, not our authoring style. Implications:
- Hold out a validation set built to look like the pool (different author voice, different
  formats, short and long answers), not a random 15% of our own pairs.
- Mix our adversarial pairs with broader security preference data we're entitled to use,
  so the model doesn't key on our phrasing.
- Don't make "hedging" or "has a citation" a free signal. Include rejected answers that
  over-hedge when the evidence is clear, and chosen answers with no ids when none apply.
- The other #96 contributor (Iniwura / FALSUM, 20 pairs) reports that their LoRA failed
  "contextual reversal" tests: the same code with context that flips the verdict. That's
  a failure mode the incumbent probably has too. Make it a core family.

## 3. Evaluation pool rules (for the dataset deliverable)

- JSONL rows: `prompt`, `chosen`, `rejected`, optional `label_kind: preference_pair`,
  `provenance: {source_kind, source_url}`. One upload per Intent, signed with EIP-191
  (`POST /api/evalpool/submissions`). No fee.
- Lengths: prompt 16–16k chars; answers 8–32k chars. Prompts that are **≥ 85% similar** to
  an existing question are rejected, so vary the questions, not just the answers.
- Provenance: an `http(s)` `source_url` → `attested`. A `source_kind` of llm, synthetic,
  generated or model → always `unverified`. **Cite real GHSA/NVD/CWE pages per row.**
- Each row lands in a hidden **testing** half or a miner-visible **ranking** half.
  You don't choose which. Frozen at each epoch rollover.
- Limits: 5,000 rows a day per contributor per Intent; once the pool reaches 200 rows,
  one contributor holds at most 50%.

**⚠ Conflict with "public dataset" deliverable.** The rules forbid publishing hidden
evaluation material, and the bounty doc says "not a public dump of hidden test cases".
If we upload a row *and* publish it, any row that lands in the testing half is leaked.
**Plan: two disjoint sets.** (a) A **public release set**: published on GitHub/HF and
used for training, never uploaded. (b) A **pool set**: uploaded and never published
(only counts and hashes shown). Confirm with the organizers on Discord.

## 4. Draft adversarial taxonomy for SECURITY_REVIEW

Each family has a rejected answer that is *plausible and about as long as the chosen one*:

| # | Failure mode in the rejected answer | Chosen answer does |
|---|---|---|
| F1 | **Fabricated id**: non-existent CVE/GHSA, or a real id for the wrong package or version | cites the correct advisory, or says none is known |
| F2 | **Version-range error**: flags a patched version as vulnerable, or misses that the version is in range | checks the pinned version against the affected range |
| F3 | **Missed critical**: lists low-severity findings, misses the hard-coded secret, SQLi or SSRF | puts the critical first, with the count right |
| F4 | **Contextual reversal**: same snippet, but the context (sanitized input, test-only code, unreachable path, dev-only dep) flips the verdict | verdict fits the context |
| F5 | **Overconfident Secure**: "no issues" with confident language on vulnerable code | Needs changes / Insecure with evidence |
| F6 | **False alarm / over-flagging**: invents a vuln in safe code (e.g., parameterized query flagged as SQLi) | Secure, with the reason it's safe |
| F7 | **Count/verdict inconsistency**: says Insecure with count 0, or lists 3 issues with count 5 | consistent fields |
| F8 | **Wrong CWE/severity mapping**: right bug, wrong class or severity (XSS called CSRF; critical called low) | correct mapping |
| F9 | **Unwarranted hedging**: refuses to commit when the evidence is decisive | commits; hedges only where the evidence is incomplete |
| F10 | **Fix that doesn't fix**: recommends a mitigation that fails a specific counterexample | a fix that actually closes it |

Target: about 300–500 public training pairs plus about 100–200 private pool pairs across
F1–F10, balanced so no family or style dominates. Every row needs a `source_url`.
Report naive baselines (longer-wins, keyword overlap, BoW question-blind, and if possible
the incumbent's ordering via the public pairs) per family. That's the "naive scorers fail"
evidence.

## 5. What it costs and needs

- GPU for training (one Colab/A10-class card is plenty for ModernBERT-base).
- **A public HTTPS VM with ≥ 5 GB RAM** that stays up during the check, running
  `cmd/adapterexec` (Go 1.25+). It runs about 13–14 s per 512-token text on CPU, about 7 min
  for the remote check. A home laptop doesn't work (private IPs are refused).
- About 5.3 MACHINA for the $5 adapter bond (refunded on deregistration), plus Sepolia ETH.
- An Ethereum key for signing pool uploads (a separate key from the bond wallet is fine).
- Registration to decision: up to about 1.5 h on testnet (mostly waiting for the epoch).

## 6. How this maps to judging and prizes

- Evaluators track: 4 × $300 delivery + $500 / $300 excellence. A team can win one of each.
- **Delivery tie-break = "proven measurement improvement or valuable new coverage"**.
  Displacing the SECURITY_REVIEW incumbent is the improvement, and first material on
  SMART_CONTRACT_AUDIT is the new coverage. The two Intents cover both halves.
- Score: Technical 35 (needs ≥ 24), Commercial 25, Growth/education 20, Adoption 10,
  Integration 5, Reproducibility 5. **70 to win.** Growth points need verifiable
  reproductions or integrations, not stars. A reproducible tutorial and a public dataset
  others train on directly earn the 20.
- Submission: a 2–5 min demo, run instructions, evidence (registration id,
  `GET /api/wasm/<id>` decision, eligible row counts), and a public summary.
- Dates: **Nov 14** integration milestone · **Nov 20** showcase · **Dec 1 23:59 UTC** deadline.
- Bounty etiquette: `/claim` on #96 (and #128), `/progress` every ≤ 72 h, `/submit` with the
  contributor address or registration id.

## 7. Suggested milestones

1. **By Nov 7:** repo scaffold, pinned kit plus `foundation.json`, taxonomy and authoring
   guide, first 60 pairs, `--check-data` PASS, naive-baseline harness.
2. **By Nov 14 (milestone):** about 250 pairs, first LoRA trained, pool-like validation set,
   per-family accuracy report; claim #96/#128; first pool upload (private set) → `eligible`.
3. **By Nov 20 (showcase):** executor VM live and passing `adapter:check-executor`;
   registered on SECURITY_REVIEW; challenge result recorded.
4. **By Dec 1:** iterate if the challenge fails (new package = new hash), publish the
   dataset with a write-up, demo video, and SMART_CONTRACT_AUDIT material and adapter.

## 8. Open questions for the organizers

- Is publishing our *own* uploaded pool rows allowed, or must the public set be disjoint?
  We assume disjoint.
- Does the remote-check sample come from the ranking half only? It's described as "public".
- Are mainnet evaluator rewards tied to the testnet canonical slot, or re-run on mainnet?
- The incumbents serve `http://…sslip.io`, but the docs say `https://`. Which is enforced?
