# Submission text (draft, 28 Nov 2026)

Ready to paste into the Anjoman submission form. Adjust the fields to the form's real ones. Every
number links to a committed report. Owner: fill in the links marked `[add]`.

---

## Apps & Agents track

**Project name:** Dependency.Guard (by AdversarialEval)

**Team:** Rita (RitaCryptoTips, GitHub `Ritapossible`)

**Track / mission:** Apps & Agents · Mission 10, Model Economy (bounty #198)

**One line:** A Mind on Minds by Animoca that buys answers from Telegraph and checks them against
public sources before anything is shipped, paid or settled.

**Problem.** Agents and teams now buy answers (is this package safe, is this code ready, which
side of this market won) and act on them automatically. Our paid tests show those answers are
often missing, and sometimes confidently wrong:
- the default route got 5, 1 and 17 of 36 security questions right in three rounds;
- a ranked answer approved malware 5 times in 21 Solana cases;
- each market-resolution provider alone settled 1 in 3 of its markets on the wrong side.

**What it does.** For each question it:
1. buys one Telegraph answer through Anjoman (no 3x buying by default);
2. checks it free against the public source that settles it (OSV and registries for packages, a
   real install and tests for code, the source a market's rules name for markets);
3. decides PASS / BLOCK / FLAG for packages, or SETTLE / HOLD for markets, with the receipts and
   cost.

It never acts on a paid answer it hasn't checked.

**Results (testnet, every rule frozen before the first paid call):**

| Test | Paid answer trusted | With Dependency.Guard's check |
|---|---|---|
| 21 hard Solana dependency cases, paid in USDC on Solana | 6/21, approved malware 5 times | 20/21, nothing unsafe approved, $0.35 |
| 36 changes written by Qwen (30 should not ship) | 14/36 (Qwen reviewing itself: 6/36) | 27/36, no good change blocked |
| Qwen-Agent pre-deployment check | 4 answers, all verified, but blind to the real exposure | HOLD as shipped; a tested fix found |
| 24 prediction markets we wrote, paid on Solana | 3 settled on the wrong side (two agreeing providers: 1) | 0 wrong, 21/24 right |
| 24 real Polymarket markets through the app (Anjoman + the Mind) | an outcome for 1 of 24 | 0 wrong: 6 settled from Binance, 18 held for a person |

Benchmark behind it: 3,680 paid calls to the security miners. The best miner was right 83% of the
time, against 67% for a free lookup; the default route followed rank 1.

**Telegraph integration:**
- Anjoman (`/engine/ask`, escrow), with receipts on every answer;
- x402 payments on Solana devnet (USDC), all confirmed on-chain;
- the node's public miner listings, used to check provider independence by payout address;
- the hosted Verified Ask (`/api/verify`).

**Links:**
- App: Dependency.Guard on Minds, https://hellominds.ai/profile/minds/38266542-f36b-1410-8467-00039ce7df11
- Website: https://adversarialeval.vercel.app/dependency-guard
- Repo: https://github.com/Ritapossible/AdversarialEval
- Track summary: https://github.com/Ritapossible/AdversarialEval/blob/main/tracks/apps-and-agents.md
- Demo videos: in-app Polymarket demo `[add]` · Qwen code test https://x.com/RitaCryptoTips/status/2126612379286786350 · prediction markets https://x.com/RitaCryptoTips/status/2126711423908614492 · Solana packages `[add]`
- Evidence anchor (Solana devnet): https://explorer.solana.com/tx/2J9e6xD5v2Wnn17Qd9BCiRgqiVTEzhXzYhwb11e8B32gsXUtJCVZUCunE3Fmh4K9EQpQxm65R5TJMaVzRNoZMPu7?cluster=devnet

**How to run it:**
- **Prerequisites:** Node 20+, Python 3.11+, an Anjoman API key with a funded testnet balance
  (each answer costs $0.01 to $0.04), and a Minds Builder key for the Mind step.
- **Sample request:**

  ```
  node mind/connector/guard.mjs --mind <mindId> pkg:npm/minimist@1.2.5
  ```

  Expected result: BLOCK, with the advisory ids, the receipt and the cost.
- **Markets:**

  ```
  node mind/connector/markets.mjs --mind <mindId> --cases resolve/polymarket_cases.json
  ```

- **Network:** testnet (Telegraph devnode, Solana devnet). **Spending limits:** a `--max-spend`
  cap on every run.
- **Offline checks:** `bash scripts/ci_local.sh`.

**Known limits:**
- Testnet and small samples, so intervals are wide.
- For known package vulnerabilities, a free OSV lookup matched the paid answers. The value is that
  wrong paid answers never become decisions.
- On markets that name a machine-readable source, the check reads the same source as the truth.
- Through Anjoman, timed-out asks were still charged ($0.17 in one run). This is reported.

---

## Evaluators track

**Project name:** AdversarialEval, evaluation material for `SECURITY_REVIEW_GENERAL`

**Track:** Evaluators · intent `SECURITY_REVIEW`

**One line:** Pairs in which the worse security answer is plausible but wrong in one decisive,
verifiable way, so a scorer can't win by rewarding length or keywords.

**Contribution:**
- 164 attested pairs, all eligible in the live evaluation pool (contributor
  `0x31Cf659edcDd1A6bF98302cbA5E7CEA8dc143095`; node API output committed);
- a ten-family failure taxonomy;
- 264 public training and 87 validation pairs, every advisory fact checked against OSV;
- an adapter trained with the unmodified official kit.

**Results:**
- Shortcut judges (length, keywords) score at most 58 to 60% on this material.
- The adapter scored 77.5% (31 of 40) on an independent test of 40 pairs from 2 outside authors,
  frozen by hash and scored once. That is below our own pre-registered 80% bar, and we report it
  as it is.
- `[Registration: owner decision; fill in the registration id and transaction if registered.]`

**Adoption:** another team's miner on #198 reports its accuracy on our 264 public pairs.

**Links:**
- Repo: https://github.com/Ritapossible/AdversarialEval
- Track summary: https://github.com/Ritapossible/AdversarialEval/blob/main/tracks/evaluators.md
- Evidence index: https://github.com/Ritapossible/AdversarialEval/blob/main/docs/SUBMISSION_EVIDENCE.md

**Known limits:** the validation pairs share an author with the training pairs, and failure types
absent from training are not learned (37 to 39% when held out).
