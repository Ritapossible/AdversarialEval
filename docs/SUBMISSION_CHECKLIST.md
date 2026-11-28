# Submission checklist (rewritten 28 Nov 2026)

The deadline is **1 Dec 2026, 23:59 UTC**, and we aim to submit by 30 Nov. The final submission
goes through **anjoman.ai**. GitHub `/progress` and `/submit` posts are records, not the
submission. **Apps & Agents and Evaluators are judged separately.** Judge-facing summaries:
[`tracks/apps-and-agents.md`](../tracks/apps-and-agents.md) and
[`tracks/evaluators.md`](../tracks/evaluators.md). Raw evidence index:
[`SUBMISSION_EVIDENCE.md`](SUBMISSION_EVIDENCE.md).

## Both tracks

- [x] Star `telegraphprotocol/bounties` from `Ritapossible` (12 Nov)
- [x] Real Telegraph integration with genuine evidence: 164 eligible pool rows; thousands of
      paid calls with receipts; Solana x402 payments confirmed on-chain
- [x] Accurate claims, network stated (testnet / devnet everywhere); limits written in every report
- [x] Keys and private data: none committed; `data/private/` git-ignored; signing stays local
- [x] Evidence signed (333 files) and anchored on Solana devnet (`evidence/ANCHORS.json`)
- [x] Reused components disclosed: `NOTICE.md`
- [x] Licence: MIT
- [ ] Owner: fill in the Anjoman submission form(s). The text is drafted in `docs/SUBMISSION_TEXT.md`

## Apps & Agents (Dependency.Guard, Mission 10 / #198)

- [x] App listed and live on Anjoman (Dependency.Guard, Security)
- [x] Working link: https://adversarialeval.vercel.app/dependency-guard
- [x] Demo videos: Solana packages (Nov 25), Qwen code test (X post), prediction markets, the
      in-app Polymarket demo (Nov 28). Owner: post the last two and add their links to
      `tracks/apps-and-agents.md`
- [x] Run instructions and reproduce commands: `tracks/apps-and-agents.md`, `mind/README.md`
- [x] Results with and without Telegraph, each pre-registered: packages, code, Solana (x2), Qwen-Agent,
      Qwen code, prediction markets, Polymarket (direct and through the app)
- [ ] `/progress` on #198 (every 72 h until submitted), then `/submit` on #198 with the links

## Evaluators (`SECURITY_REVIEW_GENERAL`)

- [x] 164 pool rows eligible and attested (node API output committed)
- [x] Public dataset `data/public/` + `data/validation/`, taxonomy, dataset spec
- [x] Independent test scored once: 77.5% (below our 80% bar), reported as it is
- [x] Registration decided (28 Nov): **not registered**. It missed our own bar; the Evaluators
      entry is the material plus a measured adapter
- [x] Dataset release v1.0 on GitHub (https://github.com/Ritapossible/AdversarialEval/releases/tag/dataset-v1.0); zip hash matches the build
- [ ] Optional: the same release on Hugging Face

## Scoring levers (out of 100)

| Criterion | Pts | Our strongest evidence |
|---|---|---|
| Technical quality and mainnet readiness | 35 | pre-registered tests, checked decisions, reconciled payments, CI, signed and anchored evidence |
| Commercial viability | 25 | a buyer's decision with a known cost; wrong paid answers never become decisions (packages, code, markets) |
| Growth and education | 20 | public dataset and reports; posts in #showcase, the Solana and Alibaba threads; X posts |
| Adoption and retention | 10 | another team's miner tests on our public pairs; the app is listed on Anjoman |
| Telegraph integration | 5 | Anjoman, x402 on Solana, the node API, 164 pool rows |
| Reproducibility and demo | 5 | reproduce commands, offline tests, videos |
