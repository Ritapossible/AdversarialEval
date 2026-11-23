# Solana use case 3: what we will build (plan only, not started)

Source: Telegraph's post "Solana Institutional AI & Commercial Use Cases" (Discord showcase, 23 Nov
2026), use case 3, **Verified Intelligence Economy (Telegraph x Pay.sh)**:

> Enable Solana agents to purchase competing specialist intelligence selected through independent
> performance evaluation, rather than choosing providers solely from API listings. Combine
> Telegraph's ranking, verification and intelligent recovery capabilities with Solana's Pay.sh
> payment and API ecosystem.
>
> Demonstration: an agent completing difficult tasks through independently evaluated specialists,
> compared against a frontier model and direct paid API selection. Measure correctness, costs,
> latency and actual task fulfillment.

Status: **planned, nothing built for it yet.** Facts about Pay.sh below are open questions until we
have read its documentation; nothing here claims how Pay.sh works.

## Why this use case, not the other four

| # | Use case | Fit for us |
|---|---|---|
| 1 | Institutional settlement assurance | Needs counterparty, contract and compliance data we don't have |
| 2 | Tokenized-asset intelligence | Needs issuer and legal evidence; a new project |
| **3** | **Verified Intelligence Economy** | **What we already do: evaluated provider choice, free verification, recovery, receipts, comparisons** |
| 4 | Trade and autonomous commerce | Needs supplier and shipment data; a new project |
| 5 | Confidential institutional AI | Needs Solana Confidential Compute; a new stack |

The post allows building on an existing project. Use case 3 lets us reuse the benchmark, Verified
Ask, the Mind and the connector, and add the missing Solana parts.

## The product

**Dependency.Guard for Solana agents: a paid "is this package version safe to ship?" check that
an agent buys on Solana.**

An agent (a coding agent, a wallet team's CI, a Solana program's build pipeline) sends a lockfile
or a list of package versions and pays per check on Solana. For each version the product:

1. **Selects** the specialist by independent evaluation: Telegraph's ranked route, informed by our
   paid benchmark of every reachable security miner (not the first provider in a listing).
2. **Buys one answer** from Telegraph (`SECURITY_REVIEW_GENERAL`), with a receipt.
3. **Verifies it for free** with Verified Ask (OSV, deps.dev, npm, PyPI, rubygems.org).
4. **Recovers**: if the answer is proven wrong or unusable, asks one other evaluated provider once.
5. **Decides** PASS, BLOCK or FLAG, with advisories, receipts, cost and latency, and keeps every
   PASS and BLOCK on the daily watch list.

What each part maps to in the post: ranking = step 1, verification = step 3, intelligent recovery =
step 4, Pay.sh payment and API ecosystem = how the agent buys the check (and, if the node allows,
how we pay Telegraph).

## Who pays and why (to write up as S9)

- **Buyers:** teams shipping Solana agents, wallets and dApps; AI coding agents that add or upgrade
  dependencies; audit firms and CI providers serving Solana projects.
- **Why:** a single bad version can drain keys. `@solana/web3.js` 1.95.6 and 1.95.7 (Dec 2024) were
  hijacked releases that stole private keys (GHSA-jcxm-7wvp-g6p5, CVE-2024-54134, MAL-2024-11183).
  A wrong PASS costs far more than a check.
- **Price:** set from measured cost: about $0.01 to $0.02 per Telegraph answer today, Verified Ask
  free, a re-ask only when needed. The write-up compares price per check with the cost of a wrong
  PASS and with a person reviewing upgrades.
- **Recurring demand:** every lockfile change, plus the daily watch, creates repeat purchases for
  the best-evaluated specialists, which is the "recurring demand for specialist providers" the post
  asks for.

## The demonstration (pre-registered, as before)

**Task:** an agent is asked to approve a Solana project's dependency upgrade. "Task fulfilled"
means every package gets a correct, usable decision (PASS on safe, BLOCK on affected, FLAG on a
version that doesn't exist) within the time limit.

**Four arms, same cases, same day:**

| Arm | How the provider is chosen | Verification |
|---|---|---|
| A. Frontier model alone | none (the Dependency.Guard Mind, no Telegraph) | none |
| B. Direct paid API selection | the provider an agent would pick from a listing (rule fixed in advance, e.g. first or cheapest listed for the intent) | none |
| C. Evaluated specialist | Telegraph's ranked route, answer trusted | none |
| D. **Our product** | evaluated specialist | Verified Ask + one recovery re-ask |

**Measured:** correctness, missed vulnerabilities (wrong PASS), false alarms, confident answers on
versions that don't exist, cost (receipts reconciled with the balance), latency per package and
per task, task fulfilment rate.

**Hard cases (new set, built by rule and frozen before any call).** Our first Solana set was easy:
every arm got every real version right. The new set targets what frontier models and listings get
wrong:
- malicious and typosquat npm packages aimed at Solana developers (OSV `MAL-` records whose
  package names reference Solana, wallets or keys);
- withdrawn and yanked versions (npm unpublished, crates.io yanked);
- versions that never existed, including near-miss names;
- advisories published after the frontier model's training cutoff;
- packages whose latest release is still affected;
- transitive dependencies pulled in by a real Solana project's lockfile.

Truth from OSV and the registries, read at a recorded time; selection rule and grading committed
before the first paid call (as in `mind/solana-test/RULE.md`).

## Solana functionality (S6, the biggest gap)

All our payments so far settle on Ethereum Sepolia (Anjoman escrow). For this use case:
1. **The agent pays us on Solana** (devnet USDC) through Pay.sh, if Pay.sh supports this for an
   API like ours; otherwise through x402 on Solana. Each paid check returns its Solana transaction
   signature.
2. **We pay Telegraph on Solana** if the node's Solana rail accepts our requests (the node has
   offered exact payment on Solana since 20 Nov; to confirm for `SECURITY_REVIEW_GENERAL`).
3. **Optional: a decision receipt on Solana**, a memo transaction holding the hash of the decision
   and its Telegraph receipts, so anyone can check later that a decision was made before a release.

Every payment is reconciled on-chain (signatures checked with a Solana RPC), as the benchmark did
on Ethereum.

## Evaluator side (the post says evaluators are essential)

- Publish the provider evaluation behind step 1: per-miner accuracy, cost per correct answer and
  stability on the Solana cases (extends `bench/`).
- Contribute the hard Solana cases as evaluation pairs to the `SECURITY_REVIEW_GENERAL` pool, kept
  disjoint from public and validation data (CLAUDE.md rule 1).

## Deliverables (what we will show)

- Live: the paid check endpoint (Solana payment) and the Dependency.Guard Mind.
- GitHub: code, the frozen case set, rule, every receipt and Solana signature, the report.
- Report: four-arm results with confidence intervals; what the frontier model and listing choice
  got wrong; cost and latency.
- Commercial one-pager (S9).
- Demo video (about 2 minutes) and an X post; a post in the Solana thread with what we are taking
  on and what we need.

## Order of work (when we start)

| Step | Plan item | Done when |
|---|---|---|
| 1 | S5 Read Pay.sh docs and the node's Solana rail | We know how an agent pays an API on Solana and whether Telegraph requests can settle there |
| 2 | S8 Hard Solana case set | Rule, cases and truth committed before any paid call |
| 3 | S6 Solana payment path | One paid check bought on Solana devnet, signature verified on-chain |
| 4 | S7 Arm B rule fixed | Listing-based choice written down before the run |
| 5 | Four-arm run and report | Receipts and signatures reconciled; report in `eval/reports/` |
| 6 | S9 Commercial one-pager | Buyers, price, cost of a wrong PASS |
| 7 | Demo video, X post, Solana thread post | Before the Dec 1 submission |

Budget: the run costs cents of test USDC per case and arm (about $1 to $2 in total at today's
prices); Minds credits for arm A.

## Questions to settle first

- How does Pay.sh let an agent pay for an API (protocol, devnet support, listing)? Do we list our
  check there, or does the agent pay through x402 directly?
- Can a `SECURITY_REVIEW_GENERAL` request to the Telegraph node settle on Solana devnet today?
- What counts as "direct paid API selection" for the judges: a listing on Pay.sh, Anjoman's miner
  list, or both? (Ask in the Solana thread.)
- Is a decision receipt on Solana valued, or is the payment signature enough?

## What we will not claim

- Nothing about Pay.sh until its documentation or a working call confirms it.
- No "better than frontier models" unless the frozen hard set shows it; on the first two package
  sets, the Mind alone matched the best paid arm, and the report will say so if that repeats.
- Testnet only; small samples are reported with intervals and read as such.
