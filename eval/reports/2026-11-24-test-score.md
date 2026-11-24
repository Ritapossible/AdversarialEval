# Independent test result (2026-11-24): 77.5%, do not register

Scored once, as `eval/RULE-registration.md` requires, after the test file was frozen
(`eval/reports/2026-11-24-test-freeze.md`, SHA-256 `66b37e83df6391bb9364112e11747bad95b3afa0e32d4bda0290f5c5fc49e81b`).

## Config

| Item | Value |
|---|---|
| Candidate | `runs/SECURITY_REVIEW-cpu-v3-seed13` (chosen by the rule: best two-seed validation mean, higher-validation seed) |
| Recipe | LoRA rank 8, lr 2e-4, 6 epochs, 264 training pairs, unmodified official kit, seed 13 |
| Scorer | `python eval/score.py --adapter runs/SECURITY_REVIEW-cpu-v3-seed13/adapter data/test/security_review.test.jsonl` (PyTorch path, each text rendered as the node does, 512-token truncation) |
| Test set | 40 pairs, 2 independent authors (Fexx 20, Lino 20), both AI-assisted and author-reviewed (amendment 1) |
| Raw scores | `eval/reports/raw/2026-11-24-test-scores.json` |

## Result

| Set | Correct | Accuracy | 95% Wilson |
|---|---|---|---|
| **All 40** | **31** | **77.5%** | **62.5% to 87.7%** |
| Fexx (drafted with GPT-6) | 17 of 20 | 85.0% | 64.0% to 94.8% |
| Lino (drafted with Grok) | 14 of 20 | 70.0% | 48.1% to 85.5% |

| Chosen verdict | n | Accuracy |
|---|---|---|
| Secure | 15 | 73% |
| Insecure | 13 | 92% |
| Needs changes | 12 | 67% |

| Length | n | Accuracy |
|---|---|---|
| better answer longer | 19 | 79% |
| worse answer longer | 21 | 76% |

| Format | n | Accuracy |
|---|---|---|
| JSON | 5 | 100% |
| prose | 35 | 74% |

(`score.py` prints every row as "hand-written"; in fact all 40 are AI-assisted and author-reviewed.
No test pair is human-written, so amendment 1's separate human-written bar has nothing to apply to.)

## Baselines on the same 40 pairs

| Judge | Accuracy |
|---|---|
| **Adapter (cpu-v3 seed 13)** | **77.5%** |
| more advisory ids cited | 60% |
| more security terms | 52% |
| fewer hedges | 51% |
| longer answer | 50% |
| shorter answer | 50% |
| prompt overlap | 49% |
| TF-IDF to prompt | 48% |

The adapter beats the strongest shortcut judge by 17.5 points, and it holds when the worse
answer is the longer one (76%), so it isn't reading length. Its validation accuracy was 74.7%;
the independent result is consistent with it.

## Decision (frozen bar)

| Condition | Needed | Got | |
|---|---|---|---|
| 1. Test accuracy | >= 80% | 77.5% | fail |
| 2. Wilson lower bound | >= 65% | 62.5% | fail |
| 3. Every shortcut judge | <= 60% | max 60% | pass |
| 4. Rehearsal (15 pairs) | all agree | not run (1 and 2 already fail) | |

**DO NOT REGISTER.** As the rule says, the entry is the evaluation material (164 pool rows,
eligible on the live network) plus this result, reported as a measured limit. No retraining,
tuning or seed swap follows from this score.

## What it says

- The adapter judges independent security reviews well above chance and above every shortcut
  (77.5% vs at most 60%), on writing it never saw, from two outside authors and two different
  drafting models.
- It is weakest where the right answer is "Secure" or "Needs changes" (73% and 67%) and on
  prose answers (74%), and strongest on clear "Insecure" cases (92%).
- At a true 77.5%, the node's first check (11 of 15 right) would pass about 3 times in 4; the rule's
  80% bar was set so that a registration attempt is likely to succeed, and this falls just short.

## Limits

- 40 pairs: the interval is wide (62.5% to 87.7%).
- All test pairs are AI-assisted; none is fully hand-written.
- PyTorch scoring path; the node runs the WASM engine (they agreed on 87 of 87 validation pairs
  in the 11 Nov rehearsal).
