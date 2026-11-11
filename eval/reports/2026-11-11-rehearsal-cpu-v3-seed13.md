# Remote-check rehearsal `cpu-v3-seed13`: SECURITY_REVIEW

Date: 2026-11-11 · package `0xd70b3b618492b695cabce36c238685026fc5782f0c26395d2d3056a4bfe7df1a`
(6,776,908 bytes, rank 8, class judgment; **not registered**) · foundation `0a49b325…f8e6`,
engine `77643d6e…92de`, tokenizer `67bc76f8…c456` (all hash-checked by `setup_kit.sh --full`).

Path: `tools/rehearse_batch.py` (node render + pinned tokenizer.json) → `tools/remotecheck`
(the node's own `pkg/wasm/remote` client, 15 pairs = 30 texts per request, score identity
sent and checked) → kit `adapterexec` on 127.0.0.1 (the real foundation graph and WASM
engine) → back. Data: the 87 frozen validation pairs. These are **our** pairs, not the
other contributors' pairs the node draws, so this is a plumbing and fidelity test, not a
forecast.

## Results

| Request | Pairs | Correct | Node verdict for that draw | Time |
|---|---|---|---|---|
| 1 | 1–15 | 11/15 (73.3%) | pass | 2m21s |
| 2 | 16–30 | 10/15 (66.7%) | **fail** | 2m27s |
| 3 | 31–45 | 10/15 (66.7%) | **fail** | 2m26s |
| 4 | 46–60 | 12/15 (80.0%) | pass | 2m21s |
| 5 | 61–75 | 11/15 (73.3%) | pass | 1m58s |
| 6 | 76–87 | 11/12 (91.7%) | pass | 1m57s |
| **All** | 87 | **65/87 (74.7%)** | | about 13.5 min |

- **Identity echo:** every reply echoed the foundation, adapter and tokenizer hashes. A
  request carrying a wrong adapter hash was rejected with `identity echo mismatch`, exactly
  as the node does.
- **Engine fidelity:** WASM and PyTorch (`eval/score.py`) order all **87/87** pairs the same
  way, and the maximum absolute score difference is 8.4e-5. The 74.7% here equals the
  PyTorch validation number, so the analyses in `eval/reports/` hold on the node's engine.
- **Latency:** about 2.3 min per 30-text request on this container's CPU, well inside the
  node's 30-minute budget.

## The finding that matters: 15 pairs is a coin flip at our accuracy

The same adapter passes four draws and fails two. That isn't a bug; it's the binomial. The
node needs 11 of 15 correct:

| True accuracy | P(pass one 15-pair remote check) |
|---|---|
| 65% | 35% |
| 70% | 52% |
| 75% | 69% |
| 80% | 84% |
| 85% | 94% |

So the registration bar is now about **80% on independent data** (MEMORY Decisions
11-11), and whether the bond survives a remote-check rejection is an open question for the
organizers.
