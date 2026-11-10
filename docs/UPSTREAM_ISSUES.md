# Kit issues found while building AdversarialEval

These are drafts to file on
[telegraphprotocol/telegraph-wasm-baseline](https://github.com/telegraphprotocol/telegraph-wasm-baseline).
All were reproduced on 2026-11-10 at kit commit `1ed063e` (Python 3.13, torch 2.15.0+cpu,
transformers 5.22.2, peft 0.21.2, safetensors 0.8.0, Go 1.25.7). None of them affects what
the node accepts, but each one blocks or misleads an adapter author. **Not filed yet:**
the project lead decides.

---

## 1. `train_adapter`: NameError after a passing gate, so a PASS exits 1

`float_runtime/train_adapter.py` line 838 prints the next-step hint using `{pkg}`. The variable
in scope is `deltapkg`.

```
"verdict": "PASS",
...
  File ".../train_adapter.py", line 838, in main
    f"  go run ./cmd/adapterbuild lora --intent {args.intent} --package {pkg} "
NameError: name 'pkg' is not defined
```

`result.json` and the adapter are already written, but the process exits **1**. The README
documents 1 as "the data check or the test failed", so scripts that trust the exit code
treat a passing run as a failure. **Fix:** `{pkg}` → `{deltapkg}`.

## 2. `export_adapter` refuses every run trained on today's Hugging Face tokenizer download

At the pinned commit `8949b909ec900327062f0ebf497f51aef5e6f0c8`, Hugging Face serves a
`tokenizer.json` with sha256 `9fd55248…74b7b1` (2,132,967 B, from a plain `curl` of
`resolve/8949b909…/tokenizer.json`). The node pins `67bc76f8…dc456` (3,583,486 B, the
telegraph-foundation release file). The two files are different serialisations: the
`model` section is laid out differently, and `padding`/`truncation` are null in the Hub file.
They produce **identical ids**: the kit's own 88 conformance vectors pass, and we checked
268 rendered texts with zero mismatches (`tools/verify_tokenizer.py`).

`foundation_record()` hashes the downloaded Hub file into `result.json`, and
`export_adapter` then refuses the run:

```
ERROR: the run's tokenizer 9fd55248d51d33976b324fc11592e28071da7d41e0e9401dfb7082e30574b7b1 is not the node's 67bc76f8b9386efba1a761c1c8e5ad439fd0eaf1c2826e9dd1a205c7af4dc456
```

Recent transformers versions also re-save `adapter/tokenizer.json` as a third serialisation
(`3703d011…`), which trips the second check in `export_adapter`.

**Suggested fix:** compare token ids (the conformance vectors), not file bytes. Or train with
the pinned `tokenizer.json` from the foundation release.
**Our workaround:** `scripts/export.sh` proves id-equivalence first, then exports with
`--adapter` from a staged copy without the re-saved tokenizer files.

## 3. Offline `adapterbuild lora` demands `hybrid` for judgment intents

`pkg/scoring/catalog.ClassOf` falls back to the compiled-in `judgmentOrHybrid` map. That
map can't tell the two classes apart, so it reports `hybrid` ("the conservative
answer"). Offline, `ResolveClass` therefore refuses a correct judgment package:

```
adapterbuild lora: FAILED: adapterbuild lora: Stage 1: class_mismatch: class "judgment", the intent needs "hybrid"
```

The live node classifies SECURITY_REVIEW as **judgment** (`GET /engine/v1/intents/SECURITY_REVIEW`),
and rejects hybrid packages for judgment intents. Registration #62 (EMAIL_SECURITY) was
rejected that way: `class_mismatch: class "hybrid", the intent needs "judgment"`. An
author who follows the offline tool's advice gets rejected on chain.

**Suggested fix:** ship the judgment/hybrid split in the compiled catalog, or let
`adapterbuild` read the class from a node (`--node URL`).
**Our workaround:** `tools/stage1check` (in this repo) calls the kit's
`adapterbuild.CheckLoRA` unchanged, after `catalog.UseClasses` with the class the live node reports.

## 4. Export is not reproducible: the metadata key order is random

With safetensors 0.8.0, `save()` and `save_file()` serialise `__metadata__` in a random key
order on every call. Exporting the same adapter twice gives identical tensors, offsets
and metadata values, but different bytes:

```
11c362d3…565f  exp1.safetensors      metadata order: format_version, intent, foundation_hash, …
3ea56cb5…6cca  exp2.safetensors      metadata order: class, tokenizer_hash, intent, …
```

As a result:
- The sha256 that `export_adapter` logs is computed from a separate in-memory `save()`, so it
  never matches the file it wrote. The README says the registered hash is "the hash of the
  file export_adapter wrote", which is true, but the log line contradicts it.
- Nobody can rebuild a registered package from its adapter and get the same keccak256.

**Suggested fix:** write the header JSON yourself with sorted keys, or hash the file after
`save_file`.

## 5. Docs: `--class` for the export command

`train_adapter`'s next-step hint prints `--class <judgment|hybrid>`, and the offline catalog
(issue 3) points authors to the wrong one. The docs could say plainly: read the class from
`GET /engine/v1/intents/<INTENT>` on the node.
