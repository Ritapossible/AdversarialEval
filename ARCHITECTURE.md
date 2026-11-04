# Architecture

```
 ┌────────────────────────────┐   real advisories (GHSA / NVD / OSV / CWE)
 │ 1. Source corpus           │◄─ provenance URL kept per case
 └─────────────┬──────────────┘
               ▼
 ┌────────────────────────────┐   taxonomy F1–F10 (docs/ADVERSARIAL_CRITERIA.md)
 │ 2. Pair authoring          │   chosen = grounded, calibrated
 │    prompt / chosen /       │   rejected = plausible, similar length, one targeted flaw
 │    rejected + metadata     │
 └─────────────┬──────────────┘
               ▼
 ┌────────────────────────────┐   normalise → dedup (85% prompt similarity) → length/token
 │ 3. Data QA + splitter      │   check (≤512) → kit dataset gate → naive-baseline report
 └──────┬──────────┬──────────┘
        │          │                               (strictly disjoint sets)
        ▼          ▼                 ▼
  data/public/   data/validation/   data/private/  ──► 7. Eval-pool upload (signed EIP-191)
  (train, released) (pool-style,    (never published)     POST /api/evalpool/submissions
                     held out)
        │          │
        ▼          ▼
 ┌────────────────────────────┐   telegraph-wasm-baseline float_runtime/train_adapter.py
 │ 4. Training                │   ModernBERT-base + PEFT LoRA (r≤16, Wqkv/Wo/Wi)
 │                            │   + 1-logit head, Bradley–Terry loss
 └─────────────┬──────────────┘
               ▼
 ┌────────────────────────────┐   eval/: per-family accuracy, length bias, swap/paraphrase/
 │ 5. Evaluation harness      │   padding/truncation probes, naive baselines, seeds
 └─────────────┬──────────────┘   → eval/reports/*.md  (go/no-go for registration)
               ▼
 ┌────────────────────────────┐   export_adapter.py → SECURITY_REVIEW.safetensors (6.8 MB)
 │ 6. Package + check         │   adapterbuild lora → keccak256 + manifest
 └─────────────┬──────────────┘
               ▼
 ┌────────────────────────────┐   immutable https/ipfs URL (wasmUrl)
 │ 8. Host + executor         │   cmd/adapterexec behind TLS on a public VM (wasmRunnableUrl)
 └─────────────┬──────────────┘
               ▼
 ┌────────────────────────────┐   registerWasm(keccak256, wasmUrl, "SECURITY_REVIEW",
 │ 9. On-chain registration   │                feeAddress, wasmRunnableUrl) + $5 MACHINA bond
 └─────────────┬──────────────┘
               ▼
 ┌────────────────────────────┐   remote check (15 public pairs ≥70%) → download + Stage 1
 │ 10. Telegraph node         │   → bit-exact confirmation → hidden competition
 │     (validators)           │   (≥70%, ≥ incumbent + 2 pts) → Canonical
 └────────────────────────────┘
```

## Components

### 1. Source corpus (`data/sources/`)
A list of real, citable cases: an advisory id, package, ecosystem, affected and patched
ranges, CWE, severity, and URL. Every pair is anchored to one or more sources so the
`chosen` answer is verifiably correct and the row gets `attested` provenance.
CSV/JSONL: `sources.jsonl`.

### 2. Pair authoring (`data/*/*.jsonl`)
One row per question. The schema is in `docs/DATASET_SPEC.md`. Fields the node reads:
`prompt`, `chosen`, `rejected`, `label_kind`, `provenance`. We also keep a sidecar with
`family`, `subfamily`, `source_ids`, `author` and `voice` (`meta/*.jsonl`, joined on row
hash). The sidecar never ships inside uploaded rows.

### 3. Data QA (`tools/`)
- `normalise.py`: Unicode NFC and whitespace collapse, the same as the node
- `dedup.py`: drops prompts ≥ 85% similar, within and **across** public/private/validation
- `token_budget.py`: renders `### Task:\n{prompt}\n\n### Answer:\n{answer}` with the pinned
  tokenizer. It fails any row over 512 tokens, or any row whose flaw marker sits past the cut.
- `split.py`: assigns each source case to exactly one of public, private or validation, so
  near-twins can't straddle splits
- the kit's `--check-data` dataset gate

### 4. Training (kit, unmodified)
`python -m float_runtime.train_adapter --intent SECURITY_REVIEW --data … --val-data …`
with `configs/security_review.yaml`. We don't fork the kit. Keeping it unmodified means our
package is exactly what the node expects.

### 5. Evaluation harness (`eval/`)
- `baselines.py`: longer-wins, shorter-wins, prompt keyword overlap, question-blind BoW,
  TF-IDF-to-prompt
- `score.py`: loads the PEFT adapter and head, scores rendered texts, and gives pairwise accuracy
  per family, per voice and per length bucket
- `probes.py`: four robustness probes. A/B swap invariance; paraphrased chosen answer;
  rejected answer padded to equal length; flaw moved late, as a truncation sanity check
- `report.py`: writes `eval/reports/<date>-<run>.md`. **Registration is go only if** validation
  ≥ 80%, every family ≥ 70%, longer-wins ≤ 60%, and the result is stable across 3 seeds (±3 pts)

### 6. Package and check (kit)
`export_adapter.py` → `adapterbuild lora` (the node's own Stage 1 parser). Optionally score
locally on the real foundation ONNX and engine.

### 7. Eval-pool uploader (`tools/upload_pool.sh`)
Builds the 5-line message (`Telegraph eval-pool submission v1`, `intent_id`, `body_sha256`,
`nonce`, `chain_id`), signs it with `cast wallet sign`, and POSTs with `--data-binary`.
Then it polls `/api/evalpool/submissions/mine` until the rows are `eligible`.

### 8. Host and executor (`deploy/`)
- The package goes to an immutable URL: GitHub raw pinned to a commit SHA, or IPFS
- The VM runs `adapterexec` (Go 1.25+), plus the foundation ONNX, engine and
  `SECURITY_REVIEW.safetensors`
- Caddy gives automatic TLS and a reverse proxy. A systemd unit restarts it.
- Public IP only: no redirects, no private ranges

### 9. Registration
`registerWasm(bytes32 wasmHash, string wasmUrl, string intent, address feeAddress, string wasmRunnableUrl)`
on the Diamond contract (Sepolia), after approving the MACHINA bond (`entityBonds()`).
Addresses are in the Telegraph docs (`protocol/addresses-and-params.md`).

## The scoring contract we must satisfy

| | |
|---|---|
| Foundation | `modernbert-base-lora16-v1`, sha256 `0a49b325…f8e6` |
| Engine | sha256 `77643d6e…92de` |
| Tokenizer | sha256 `67bc76f8…c456`, `[CLS]`=50281, `[SEP]`=50282 |
| Input | `### Task:\n{prompt}\n\n### Answer:\n{answer}`, ≤ 512 tokens, no padding |
| Output | One f32 reward logit (higher = better). The executor returns its bit pattern as a u32. |
| Package | safetensors, metadata `format_version=1`, `abi=lora-v1`, `class=judgment`, `intent=SECURITY_REVIEW`, rank ≤ 16, 178 F32 tensors |
| Executor request | `POST {batch:[{tokens:[…]}], foundation_hash, adapter_hash, tokenizer_hash, input_root}`, ≤ 100 items |
| Executor reply | `{results:[{score:u32}], foundation_hash, adapter_hash, tokenizer_hash}`, ≤ 64 KiB, echoing what was run |

## What a `SECURITY_REVIEW` answer looks like

The miner response schema: `verdict` ∈ {Secure, Needs changes, Insecure},
`vulnerability_count` (scored), `issues` (CVE/GHSA/CWE/OWASP, most serious first), and
`summary`. Our `chosen` and `rejected` answers are written in this shape, as prose,
JSON-like or mixed, so the adapter judges real miner output, not essays.

## Directory layout

```
.
├── README.md  PLAN.md  ARCHITECTURE.md  MEMORY.md  CLAUDE.md
├── docs/        RESEARCH, ADVERSARIAL_CRITERIA, DATASET_SPEC, RUNBOOK, SUBMISSION_CHECKLIST
├── configs/     training configs
├── data/
│   ├── sources/     real advisory cases (provenance)
│   ├── public/      released training pairs
│   ├── validation/  pool-style held-out pairs (released after the hackathon)
│   ├── private/     eval-pool upload set — git-ignored, never published
│   └── meta/        sidecar labels (family, voice, source ids)
├── tools/       normalise, dedup, token budget, split, upload
├── eval/        baselines, scoring, probes, reports/
├── deploy/      Caddyfile, systemd unit, executor notes
├── scripts/     setup_kit.sh, check_data.sh
└── third_party/ (git-ignored) pinned kit checkout + foundation files
```

## Design decisions

The rationale is logged in `MEMORY.md` → Decisions.

- **The kit stays unmodified.** That matches the node's expectations bit for bit and
  removes a whole class of rejections.
- **Disjoint public/private sets.** Releasing data can't leak the hidden testing half.
- **Splits are made per source case, not per row.** It stops near-twins inflating validation.
- **The validation set is written in a second voice.** It approximates the remote check and
  the hidden sample, which draw across contributors.
- **Pairs are written in the miner response shape.** The adapter scores miner output, so it
  trains on that.
