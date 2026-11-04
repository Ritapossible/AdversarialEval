# tools/ (to build in Phase 1–2)

| Script | Purpose |
|---|---|
| `normalise.py` | NFC + whitespace collapse, the same as the node |
| `dedup.py` | Drop prompts ≥ 85% similar, within and across public/validation/private |
| `token_budget.py` | Render `### Task:\n…\n\n### Answer:\n…`; fail rows over 512 tokens |
| `split.py` | Assign each source case to exactly one split |
| `upload_pool.sh` | Sign (EIP-191 via `cast`) and POST a JSONL to `/api/evalpool/submissions` |
