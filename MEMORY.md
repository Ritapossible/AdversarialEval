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
| Bounty claims | **#96 closed "not planned" 11-15** by maintainer muhammadtalha198: Season II bounties moved to 15 mission issues; #96 claims/progress/submissions stay on record; contributors re-`/claim` on a mission issue (SECURITY_REVIEW is a core intent of #189 Exchange, #198 Model Economy, #202 Web3 & DeFi) and link #96 in the first update. Mission rules: non-exclusive claims, `/progress` every 72 h or the claim is released, `/submit` on GitHub plus the official Anjoman form. Showcase Nov 20; final deadline **Dec 1 23:59 UTC**. Our earlier #96 claim (11-12) and progress (11-12, 11-15) remain on #96 | 11-15 |
| Mission #198 (11-15) | Claimed #198 Model Economy 11-15 (bot confirmed, progress recorded; next `/progress` due by 11-18 ~18:15 local). Miner audit (`tools/miner_audit.py`, report `eval/reports/2026-11-15-miner-audit.md`): **12/32** SECURITY_REVIEW_GENERAL miners take the canonical `target` request (402, $0.01/call); 20 return `no_compatible_miner`, incl. rank 2 (secrev-ghsa, 0.9719), rank 4, rank 7. Paid step (cost per verified correct answer) needs a funded payer | 11-15 |
| Paid benchmark (11-15) | 91 x402 calls (Sepolia test USDC, burner 0xA0C8…6C1C, key at ~/.adversarialeval/burner.key, outside repo) under frozen `bench/RULE.md`: 38 delivered with receipts ($0.38), 21 verified correct ($0.018 each; 11 on answerable cases, $0.035 each). a1-preflight (unranked) 6/6 answerable; rank 1 pr-guard-sentinel 0/7 (verdict null). 21/38 delivered answers had verdict null; ~$0.47 charged on 47 failed calls (docs: credited to escrow; unverified). Report `eval/reports/2026-11-15-paid-benchmark.md`. User accidentally sent 1 USDT (0xFB12…b0C1, 18 dec) to the burner; return to 0x31cf…3095 pending user OK | 11-15 |
| Grok audit (11-16) | Verified: length ratio >1.25 in 59% train / 48% val (hand-written) but 0% in pool (batch 2 max 1.07, chosen-longer 51%); longer-wins 55-58% < 60% gate. 8 short rows fail `build.py --strict` (style floor; CI does not use --strict; kept as deliberate terse wrong answers). source_kind absent only on never-uploaded public rows. Action: upload_pool.sh now refuses any pool row with ratio > 1.25 or chosen-longer share outside 35-65% | 11-16 |
| Pool batch 2 (11-16) | User reviewed severity pairs: 83 approved (code applied as Ritapossible); 1 undecided (448c4c529b69, LiteLLM GHSA-wpfp-gwwc-vwq6) left out. File data/private/upload_batch2.security_review_general.{jsonl,txt,json} (83 rows) sent to user. Pool before upload: 332 eligible, 10 submitters | 11-16 |
| Pool batch 2 uploaded (11-18) | 83 rows admitted (API: admitted 83, no new rejections); eligible pending next snapshot (active snapshot still 11-14, 332 rows; epoch reset to 9 after migration). Report eval/reports/2026-11-18-pool-batch2.md | 11-18 |
| Test intake (11-18) | Fexx: 20 AI-assisted (GPT-6) pairs, author-reviewed; imported to data/test (source_kind ai_assisted); 3 advisory facts re-verified on OSV; shortcut judges <= 55%; kit surface probe 0.67 on n=20 (noise). Need a 2nd author (>= 20 pairs) by Nov 26 to reach 40/2 for freeze + single scoring. dedup.py made order-independent; 1 reviewed pair in data/sources/dedup_reviewed.txt | 11-18 |
| Mind comparison (11-22) | 12 benchmark packages (first 6 pairs). A Mind alone (web search): 12/12, 596 s, ~9 credits; its claims 11/12 verified by Verified Ask (1 bare CVE). B Telegraph trusted: route answered 7 (TxLens), 4 right, 2 missed vulnerabilities ('Secure' with count 1-2), 1 false alarm; 5 routed asks refused HTTP 400 'Insufficient escrow balance ... costs $0.26' (routed ask holds $0.26 up front; our $0.50 balance fell below). C Telegraph + Verified Ask + one re-ask: 12/12, $0.22, 316 s. Honest takeaway: on popular packages a web-searching Mind matches; Telegraph+VA adds speed, receipts, structured verdicts and checks before acting; next test unfamiliar cases. Verified Ask fix: bare CVE records (no package) now warn not fail; replay: wrong contradicted 95->92, unconfirmed 47->50, txlens bad citations 9->3; headline unchanged. Report eval/reports/2026-11-22-mind-comparison.md. Anjoman effective balance $0.19 | 11-22 |
| Dependency Guard live (11-22) | Mind Dependency.Guard id 38266542-f36b-1410-8467-00039ce7df11. Minds Builder console: 'Skills & Apps' coming soon, so no custom key store for Anjoman; route = our connector (mind/connector/guard.mjs) drives the Mind via Builder API (api.build.hellominds.ai, X-Api-Key) and calls Anjoman (backend.telegraphprotocol.com /engine/ask, Bearer). Both keys saved as network secrets on the 'Full' environment (proxy-injected; run node with NODE_USE_ENV_PROXY=1 NODE_EXTRA_CA_CERTS=/root/.ccr/ca-bundle.crt). /engine/ask returns structured result + escrow receipt in ~5-30 s, $0.01-0.02. Run 1 ($0.04): 1.2.5 BLOCK; on 1.2.8 rank 1 Salence said 'Needs changes' with count 0, Verified Ask contradicted, re-ask a1-preflight -> Secure verified -> PASS. Run 2 with the Mind ($0.04): both verified first time; the Mind replied with decisions, receipts, caveats (PASS is per version, not a floor). Anjoman balance started at $0.50 | 11-22 |
| Adoption evidence (11-22) | Femtech-web (#198, Miners/Providers track) runs Salence (registration 6157, routing ID 905227 = our round-4 rank 1): their /progress says "80.6% correct on 264 held-out AdversarialEval questions" (our 264 public training pairs used as their test set). Cite as independent use. Our round 4: Salence flags every vulnerable case but returns verdict null on clean/fixed cases. Bot note: our 11-22 /progress with '/progress' alone on line 1 got no bot reply; a second post with text on the same line was recorded within a minute. Always put text on the /progress line | 11-22 |
| Round 4 + pooled (11-22) | Round 4 escrow, 1,518 calls, 634 delivered (225 valid verdicts), receipts 6,340,000 vs ledger delta 6,350,000: one $0.01 unmatched (likely a 'fetch failed' call billed after the connection dropped; unconfirmed). tau +0.29 over 32 ranked (rounds: +0.02, -0.18, +0.29). New rank 1 'salence' = same id 905227 as evidence-security-review (0/36 twice), now 17/36: flags all vulnerable cases but returns verdict null on every clean/fixed case. Route -> rank 1 every round (5, 1, 17 of 36). a1-preflight 27/31/32 (rank 7, unranked, 3), pooled 90/108 83% (75-89%) vs free OSV 72/108 67%. Cost per correct all targets: $0.100 (x402), $0.083, $0.059 (escrow). Verified Ask rounds 2-4: 0 of 142 wrong verified, 220/220 verified correct. Scorer fix: failed client calls lacked `rail`, now filled per round; runner records it. Report eval/reports/2026-11-22-rounds-2-4.md. Escrow available 15.72 test USDC | 11-22 |
| Minds integration tips (11-22) | From Chrysolite494's Supplier Detective update: Minds can't load the Telegraph MCP; use an Anjoman API key with Minds' HTTP tool, key in the Mind's private key store (never in the skill). Minds cuts calls at 60 s (504) while Anjoman jobs can take ~2 min: find the job with GET /agent/spend, then poll GET /agent/jobs/{id}. Our Mind (Dependency.Guard, created 11-22) can probe endpoints but says it cannot register custom apps; Mind Connections lists only built-in apps (Browser Use, Browserbase, Linear, Superior Trade, Tavily, Vercel). Open: where the HTTP tool and private key store are | 11-22 |
| Verified Ask hosted (11-22) | Live at https://adversarialeval.vercel.app/api/verify (Vercel Python function, generated copy of verify/ via tools/sync_site_api.py, CI check). Refuses all POSTs (503) until VERIFY_TOKEN is set in Vercel env; then bearer token required; per-instance rate limit; citation lookups parallel, capped 25; ~1 s live. Open question for the Mind: does Anjoman /agent/chat return the structured miner result or prose (else use /engine/ask) | 11-22 |
| Minds HTTP route (11-22) | Telegraph: Minds connect to Anjoman via the Minds HTTP tool: POST backend.telegraphprotocol.com/agent/chat (stream:false), API key in Minds private credentials, funded Anjoman balance; poll GET /agent/jobs/{id} after Minds timeouts; GET /agent/spend. One builder already has it working. Telegraph asks all builders for Mind IDs, working app links and demo videos (Chrysolite494 already shared Supplier.Detective + a Vercel app). Our design: Mind -> Anjoman (one ask per package) -> hosted Verified Ask -> pass/block/flag | 11-22 |
| Minds forum (11-22) | Telegraph opened a Discord forum to coordinate Minds built on Anjoman (API, MCP or Skill). Listed: an investigating Mind, a supplier/business-ops Mind with a reviewer Mind, RugReceipt (token risk, alerts), Ballast (Bitcoin mining ops), an investigator+reviewer for supplier/invoice evidence. None covers security. They ask builders to collaborate, help with integration and test each other's Minds (adoption evidence). Drafted an intro post for the user | 11-22 |
| Telegraph feedback to another builder (read 11-22) | Given by the Telegraph team to Athar (@atharhive) about his app Tina, which buys every question from three miners; not addressed to us, but it states what they reward. Don't buy the same question from several miners by default (3x cost vs 1x ranked routing); the goal is ranked providers so users don't compare. Start from one of the 15 commercial missions and work backwards (customer, problem, paid outcome, capabilities) and build a complete app. Final submission via anjoman.ai (form not live); GitHub claims and progress are not submissions; no standalone GitHub payout; Apps & Agents and Evaluators judged separately: keep intent details, material links, IDs, eligibility evidence. Done: docs/SUBMISSION_EVIDENCE.md (164/164 eligible, raw API 11-22). Plan: Phase A Dependency Gate for Mission 10 routes 1-2 (one paid call + free Verified Ask; re-ask only when proven wrong); Mind demoted to optional front end. Apps rubric: technical 35 (min 24), commercial 25, growth 20, adoption 10, integration 5, reproducibility 5 | 11-22 |
| Minds research (11-22) | Telegraph proposed building a Mind (hellominds.ai, Animoca) on Anjoman. Docs: no documented custom tools, MCP or HTTP for Minds; no Telegraph/Anjoman integration documented on either site; a Mind CAN be driven from code (`minds` CLI, `@animocabrands/minds-client-lib`), replies free text; Cognition US$10/1,000, rate per step unpublished. Anjoman MCP is local stdio (npx), API keys at backend.telegraphprotocol.com (30 rpm). Plan: Phase N in PLAN.md (our orchestrator + Verified Ask, Mind writes the report; 3-arm test). Gated after round 4 and the test set; first ask Telegraph how they connected Anjoman to a Mind and whether it is rewarded | 11-22 |
| Grok audit 3 (11-22) | Checked against the repo. Verified Ask findings valid and fixed: VERIFY_TOKEN required off loopback (refuses to start otherwise), per-IP rate limit (429), upstream cap 8, atomic cache writes, optional strict_count (count must equal OSV records or alias-merged distinct count), verify/README.md for scope. Replay numbers unchanged. Repeated items (length ratio 156/264 train, 42/87 val; 8 short rows under --strict) are the same as the 11-16 audit: direction is balanced (chosen longer 137/264, 47/87), longer-wins 54-57% < 60% gate, pool and test (20 pairs, max ratio 1.25) are length-gated; CI does not use --strict | 11-22 |
| Verified Ask (11-22) | New `verify/` module: checks SECURITY_REVIEW answers against OSV + deps.dev + rubygems.org (fields, exists, verdict, citations) -> verified/contradicted/unconfirmed/invalid/unchecked; HTTP API `python -m verify.server`. Replay over rounds 2-3 (no spend): 113 correct -> 112 verified + 1 contradicted (real bad citation); 87 wrong -> 0 verified, 61 contradicted, 26 unconfirmed (missing count). 371/577 delivered package answers had no usable verdict. Evidence cache committed; tests/test_verify.py in CI. Report eval/reports/2026-11-22-verified-ask.md. Next: code answers -> evaluator model; paying /v1/ask proxy | 11-22 |
| Round 3 (11-21) | Escrow rail, 1564 calls (46 cases x 33 miners + routed). 591 delivered, 591 receipts = 5,910,000 uUSDC = ledger charged+unbilled delta (20,000 -> 5,930,000): exact match, no failure billed. a1-preflight 31/36 (unranked; code flipped from mostly Secure to mostly Insecure), OSV free 24/36, rank 1 secrev-nvd-kw 0/36, routed 1/36 (43/46 to rank 1), tau -0.18 over 27. Scorer fix: rank now per round. Report eval/reports/2026-11-21-round-3.md. Escrow available 22.07 test USDC. Round 4 scheduled 11-22 08:10 UTC | 11-21 |
| Status (11-20) | All 164 of our pool rows eligible (API submissions/mine); pool 1379 eligible, 11 submitters, snapshot 11-18 15:49. Payments: node now offers exact only on Base Sepolia (Circle USDC 0x036C…) + Solana, and escrow on Eth Sepolia; benchmark needs Base Sepolia USDC or escrow support. Next /progress due ~11-21 09:45 local | 11-20 |
| Round 2 (11-16) | 598 calls, rule v2. a1-preflight 27/36 (75%, rank 7) but `Secure` on 10/12 code; free OSV 24/36; routed 5/36 (all to rank 1 pr-guard); ranks 1-3 at 0/6/3%; Kendall tau +0.02. On-chain: 560 transfers = $5.60 (only the 38 pre-payment 503s unpaid); 123 timeouts charged with no header; 246 charged miner errors; 72 delivered null verdicts. Rule v2 amendment 1: on-chain charged measure + bootstrap scope fix. Report `eval/reports/2026-11-16-round-2.md`. Rounds 3-4 scheduled 11-17/18 07:00 UTC | 11-16 |
| Network change (11-17) | Registry 2171 -> 1118 (07:00 UTC) -> 1515 (15:00); SECURITY_REVIEW_GENERAL listed 32 -> 8 -> 24 (17 reachable). x402 Sepolia asset changed: open-mint test USDC 0xcc19… -> Circle USDC 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238, payTo new 0x72a70e94… (LedgerFacet escrow). Round 3 attempt void (client refused to pay, nothing charged); kept in bench/out/round-3-void-payment-migration; rule v2 amendment 2. Burner holds 9.55 old test USDC (now useless for payments) and 0 Circle USDC: needs Circle Sepolia USDC (faucet.circle.com) to continue | 11-17 |
| Public posts (11-12) | Discord #showcase thread "AdversarialEval" (tag Evaluators): intro + progress + reviewer request; bounties repo starred; the 3 organizer questions (open questions 5–7) posted, awaiting answers | 11-12 |
| Demo page (11-12) | "Spot the Flaw": 17 public-train pairs across F1–F10; shortcut judges 8/17 (longer), 5/17 (keywords). Adapter choices come from **cpu-v4-demoheld** (trained without the 17 + 7 same-advisory twins): 13/17 and 11/17 (10 right in both runs, 3 wrong in both). Preview https://claude.ai/artifact/H5j9paVdwFQSJhnvxepd12 (private). Public: https://adversarialeval.vercel.app (Vercel, root dir `site`, deploys on push; checked HTTP 200 on 11-15). Pages workflow removed 11-15 | 11-12 |
| cpu-v4-demoheld (11-12) | 240 pairs: val 71.3% / 64.4% (mean 67.9% vs cpu-v3 73.6%); dropping 24 mostly hand-written pairs cost ~6 points, hand-written val 81% → 70.5%. Report `eval/reports/2026-11-12-demoheld.md` | 11-12 |
| Polarity check (11-15) | `eval/score.py` now flags an F2-in vs F2-out gap > 20 points. cpu-v1-seed7: 100% vs 0% (original shortcut). cpu-v3 seeds: 42% vs 67% and 42% vs 80%, so the current models **over-correct towards "patched"** on version pairs (small n, same direction in both seeds). Version reasoning stays a stated limit | 11-15 |
| Held-out families (11-14) | cpu-v5-lofo (no F4/F6 in training, 218 pairs): unseen F4+F6 (57 pairs) **36.8% / 38.6%**; F6 false alarm 23–26% (below chance: learns "alarmist answer wins"); val "Secure" verdicts 46%/19%. Validation accuracy holds only for trained families. Report `eval/reports/2026-11-14-lofo.md` | 11-14 |
| Severity pairs fixed (11-15) | New pool kind `F8-any`: answers identical except the severity claim and the words that depend on it (issue tag, verdict); the wrong level is drawn from the true-severity distribution (either direction); length direction balanced at the end. 84 pairs: longer-wins 50%, TF-IDF-to-prompt 50%, keywords 55%, kit gate PASS (Fexx's 'identical except one claim' advice plus our distribution/direction fixes). Awaiting human review (review page: only undecided rows), then a second upload | 11-15 |
| CVE_LOOKUP_CVSS truth source (11-15) | **Built, tested, not deployed yet** (`truth-sources/cve-cvss/`): Vercel function `/api/cvss?cve_id=` reads NVD's own record from the CIRCL mirror of the NVD feed (20/20, ~0.45 s) with NVD API fallback (NVD alone failed 11/20 even with retries); rule: NVD Primary v3.1 → v3.0 → CNA (Secondary) v3.1 → v3.0 → v4.0, v2 never; mirror vs NVD identical on 18/18; live local run 19×200 (~120 ms), 1×404 (v2-only), bad id 400. Own endpoint, so no duplicate_case. Next: user deploys on Vercel (root `truth-sources/cve-cvss`), `make_item.py <url>` writes items.txt, user uploads under CVE_LOOKUP_CVSS | 11-15 |
| Fexx repos studied (11-15) | fexx301/oathcast (Season I winner: deployed miner + paid app path, receipts, release evidence) and oathcast-telegraph-s2 (S2: material + **truth sources** for WFV, sanctions and macro; a 2.5 KB Rust **comparator** registered on-chain, reg 223; LoRA adapters that **did not ship**, published as negative results with frozen rules). They **withhold their material generators** (publishing them would expose hidden-pool questions); ours is public, with the pool package list private. Future pool batches should use templates not in the public repo. Opportunity: `CVE_LOOKUP_CVSS` is **deterministic** (21 miners, 61 eligible rows from 8 contributors), so a keyless truth source (e.g. NVD CVSS) is valid evaluation material, and "one is enough for an intent to be scored" | 11-15 |
| Peer findings (11-14, Fexx in #showcase, also an Evaluators entrant) | (1) hold out whole failure types/formats, not just pairs: their adapter did 94% on trained error kinds vs 61% on unseen; we're running a leave-F4+F6-out test (cpu-v5-lofo). (2) report numeric families separately (we do: F2 by kind). (3) flipped negatives must flip every dependent word; our generated F2/F8 do. (4) balance, don't ban (as we did for length). (5) kit PR #5 (theirs) fixes the legacy full-wasm export with missing weights and adds `--class` (same as our patch 0002, so no duplicate filing). Our packages: 177/178 tensors non-zero (only head.bias is 0, expected under a pairwise loss) | 11-14 |
| Telegraph team guidance (11-13) | "Sign up on anjoman.ai and that's it, you're already in" (that is the hackathon registration). They "especially need evaluation material … independently sourced … from multiple contributors", even on claimed Intents; flow: `/claim` the bounty, follow its requirements, submit material at anjoman.ai/dashboard/eval. Bounty #96 Part 1: worse answers "believable but wrong, about as long as the better one, and different every time"; rows must end `eligible`; source links per row. Part 2: adapter live on SECURITY_REVIEW. Issue closes only when both parts are maintainer-verified | 11-13 |
| Anjoman dashboard, seen (11-13) | Signed up; wallet connected on Sepolia (address shown in the dashboard). Faucet: 1 test USDC / 24 h (first claim 11-13); USDC buys the $5 MACHINA bond at registration, so collect about 6–7 USDC (claim daily). Gas: email accounts sponsored, wallet accounts need Sepolia ETH. Evaluators page: *Contribute evaluation material* (tick intents, Upload a file JSONL or Add a pair, Sign and upload, browser-signed); adapter flow *Link & hash* → *Structural checks* → *Publish*. My registrations has Miners / Evaluation WASMs tabs. No Solana anywhere | 11-13 |
| Anjoman dashboard (11-13) | anjoman.ai/dashboard/eval is the official web UI for the SAME Evaluators track (the H2 Build page links the track to it): publish an adapter or contribute evaluation data; sign-in gated. The dashboard also has Wallet, Faucet (testnet tokens) and My registrations. Not yet explored behind sign-in. A Telegraph reply to a miner author says test tokens come from that faucet | 11-13 |
| #96 our /submit (11-15) | Posted `/submit` for the evaluation-material part (81 eligible, attested; contributor 0x31Cf…3095); bot: "Submission from @Ritapossible moved to review". Adapter part continues under `eval/RULE-registration.md`. zkasuran meanwhile uploaded 676 more pairs (166 eligible, 501 quarantined `rate_limited`); hidden-sample draws are even across contributors, so volume doesn't buy share | 11-15 |
| Licence (11-15) | MIT for our code/docs/pairs (owner's decision); third-party data keeps CC BY 4.0 / NVD notices in `NOTICE.md` | 11-15 |
| #96 thread intel (11-15) | zkasuran (0xDB6c… contributor, 0x8b22… miner, discloses both) posted `/submit` for the evaluation-material part: 114 pairs eligible in the active snapshot; bot moved the issue to `status:review`. Adapter part still open for everyone | 11-15 |
| #96 thread intel (11-12) | another contributor (0xDB6c…) reports 114 rows admitted to the pool (127 quarantined rate_limited, 7 near_duplicate) from 248 programmatic Composer/FriendsOfPHP questions, `source_kind` "api", per-row source URL | 11-12 |
| Dataset | 59 public train + 14 validation pairs (Claude drafts, unreviewed); 26 OSV-verified sources | 11-08 |
| Data check | kit dataset gate PASS on train; naive scorers ≤ 58% overall; per-family tells remain (report 11-08) | 11-08 |
| Our pool rows (SECURITY_REVIEW_GENERAL) | **81 eligible (11-15), all attested**, in the active snapshot (332 rows / 10 submitters, published 11-14 21:45Z). Was: 81 admitted (uploaded 11-14 via the dashboard, wallet 0x31Cf...3095; node API verified, `eval/reports/2026-11-14-pool-upload.md`). Pool: 10 submitters; active snapshot 199 rows from 9. Re-check for `eligible` after the rollover | 11-14 |
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
| Pool candidates (11-14) | **81 pairs** (F2 63, F7 10, F1 8; 19 packages), all length-matched (≤ 1.25×, random direction), labels OSV-verified, kit gate PASS, strongest naive scorer 54%. **Severity (F8) pairs held back** in `data/private/held_back/`: downgrade-only F8 let a keyword judge win 11/11; adding inflation pairs (F8-up) fixed that, but TF-IDF-to-prompt still won ~91–96% (the wrong severity word is rarer in the corpus). **81/81 human-reviewed and approved by Ritapossible (11-14)**; **uploaded 11-14: 81 admitted, attested** | 11-14 |
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
| 11-15 | Rule amendment 1 (before any test data): independent AI-assisted pairs count if the author is outside the project, names the drafting model, reviews every pair, and facts are GHSA/OSV-checked; reported separately by author and by AI-assisted vs human-written; bar on the pooled set | Fexx offered AI-drafted, fact-checked pairs and asked whether they count |
| 11-15 | Registration decision follows `eval/RULE-registration.md`, frozen before any test pair exists: test ≥ 40 pairs / ≥ 2 reviewers, hashed before scoring, scored once; candidate chosen on validation; REGISTER only if acc ≥ 80%, Wilson lower ≥ 65%, every shortcut judge ≤ 60%, rehearsal clean | Learned from a Season I winner (fexx301): frozen rules + outcome tables make results verifiable and stop goalpost-moving |
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
