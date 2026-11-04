# eval/ (to build in Phase 1–2)

| Script | Purpose |
|---|---|
| `baselines.py` | Longer/shorter-wins, keyword overlap, security-term density, hedge words, question-blind BoW, TF-IDF-to-prompt |
| `score.py` | Score pairs with a trained PEFT adapter + head; per-family / per-voice / per-length accuracy |
| `probes.py` | Swap invariance, paraphrased chosen, length-padded rejected, late-flaw truncation |
| `report.py` | Write `reports/YYYY-MM-DD-<run>.md` and apply the go/no-go rule |

Go/no-go for registration: validation ≥ 80%, every family ≥ 70%, longer-wins ≤ 60%,
stable across 3 seeds (±3 pts).
