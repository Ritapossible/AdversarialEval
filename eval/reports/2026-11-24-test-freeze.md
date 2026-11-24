# Test set freeze (2026-11-24), before any model is scored

Per `eval/RULE-registration.md`: the test file's SHA-256 is committed before scoring, and its rows
are never edited, added or removed after this commit.

| Item | Value |
|---|---|
| Test file | `data/test/security_review.test.jsonl` (40 pairs) |
| SHA-256 | `66b37e83df6391bb9364112e11747bad95b3afa0e32d4bda0290f5c5fc49e81b` |
| Meta file SHA-256 | `7cc55e20d0527c9f96f24b390cfbcebead13a60be9865e38d7691f3716d8f32f` |
| Authors | Fexx 20 (drafted with GPT-6, author-reviewed), Lino 20 (drafted with Grok, author-reviewed); both independent, AI-assisted under amendment 1 |
| Shortcut judges (bar: each <= 60%) | longer-wins 50%, shorter-wins 50%, prompt-overlap 49%, TF-IDF-to-prompt 48%, more-security-terms 52%, fewer-hedges 51%, more-hedges 49%, more-ids-cited 60% |

## Candidate (chosen by the rule, without looking at the test set)

- Recipe with the best two-seed validation mean on the 87 validation pairs: **cpu-v3**
  (seed 13: 74.7%, seed 7: 72.4%, mean 73.6%; cpu-v2 mean 71.8%; v4 and v5 are ablations
  trained on less data, means 67.8% and 60.9%).
- Seed with the higher validation accuracy: **seed 13** (`runs/SECURITY_REVIEW-cpu-v3-seed13`).
- Its package, exported once on 2026-11-11: `SECURITY_REVIEW.safetensors`, SHA-256 `a823b596e2a30d2ccd5627833f7bc01f53440c53d0698666d5545581a1581ecd`.

Next: score this candidate once on the frozen file; report in `eval/reports/2026-11-24-test-score.md`.
