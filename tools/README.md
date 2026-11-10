# tools/

| Script | Purpose |
|---|---|
| `fetch_sources.py` | Verify every advisory in `data/sources/ids.txt` against OSV; cache raw records; write `sources.jsonl` |
| `check_ids.py` | Query OSV for every F1 trap id: `fabricated_ids` must not exist (404), `misattributed_ids` must exist (cached in `data/sources/id_checks.json`) |
| `build.py` | Validate `data/authoring/` pairs (ids, splits, enums, lengths) and write node rows + sidecar meta per split |
| `token_budget.py` | Render with the pinned tokenizer; fail texts over 512 tokens |
| `dedup.py` | Flag prompts ≥ 85% similar within a split, and ≥ 70% across splits |
| `upload_pool.sh` | Sign (EIP-191 via `cast`) and POST a `data/private/` JSONL to the eval pool; `--dry-run` shows the message |
| `common.py` | Node normalisation, row ids, render, paths |

Run everything with `bash scripts/check_data.sh`. Tests: `python tests/test_tools.py`.
