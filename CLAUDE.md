# Working rules for AI assistants

Read `MEMORY.md` first: it holds the verified facts, live state and decisions. `PLAN.md` holds
the current phase. Update `MEMORY.md` → *Live state* and *Decisions* whenever you learn or
change something durable.

## Hard rules

1. **Never commit or publish `data/private/`.** It's the eval-pool upload set. It's
   git-ignored, so keep it that way. Public, validation and private sets must stay disjoint.
   Run `tools/dedup.py` across all three before any upload or release.
2. **Never request, infer, scrape or use** unpublished evaluator weights, hidden evaluation
   rows or private node diagnostics. Use only the public kit, the public base model, and data
   we're entitled to use.
3. **Never commit secrets:** private keys, `.env`, RPC keys. Signing happens locally with
   `cast`.
4. **Don't modify the vendored kit.** Train and export with
   `third_party/telegraph-wasm-baseline` at the pinned commit.
5. Every pair must cite at least one real, public `source_url` (GHSA/NVD/OSV/CWE/vendor
   advisory). Don't invent advisory ids, **except in a `rejected` answer as a deliberate F1
   flaw**, and record that in the sidecar meta.
6. Every rendered row (`### Task:\n…\n\n### Answer:\n…`) must fit in 512 tokens, with the
   decisive flaw well inside that window.
7. Don't claim network results you haven't verified with the node API. Paste the API output
   into `eval/reports/` or `MEMORY.md`.

## Conventions

- JSONL, UTF-8, one row per line, no trailing whitespace. File names are
  `<intent_lower>.<split>.jsonl`.
- Reports go in `eval/reports/YYYY-MM-DD-<run>.md` with the config, seeds, per-family accuracy
  and baselines.
- Commit messages are imperative and say what changed and why.
