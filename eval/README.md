# eval/

| Script | Purpose |
|---|---|
| `baselines.py` | **Built.** Longer/shorter-wins, prompt overlap, TF-IDF-to-prompt, security-term density, hedge words, ids cited, per family, plus the kit's own dataset gate |
| `score.py` (todo) | Score pairs with a trained PEFT adapter + head; per-family / per-voice / per-length accuracy |
| `probes.py` (todo) | Swap invariance, paraphrased chosen, length-padded rejected, late-flaw truncation |
| `report.py` (todo) | Write `reports/YYYY-MM-DD-<run>.md` and apply the go/no-go rule |

Go/no-go for registration: validation ≥ 80%, every family ≥ 70%, longer-wins ≤ 60%,
stable across 3 seeds (±3 pts).
