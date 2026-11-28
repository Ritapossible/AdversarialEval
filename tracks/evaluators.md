# Evaluators track: AdversarialEval for `SECURITY_REVIEW_GENERAL`

## Summary

Evaluation material in which every worse answer is **plausible but wrong in one decisive,
verifiable way**, contributed to Telegraph's evaluation pool for `SECURITY_REVIEW_GENERAL`, plus
an Evaluator adapter trained and measured on it. **164 attested pairs are eligible in the live
pool.** On an independent test set (40 pairs from 2 outside authors, scored once under a rule fixed
before any test data existed) the adapter scores **77.5%**, against at most 60% for every
shortcut judge. That is just under our own 80% bar, so the rule says do not register, and the adapter is **not
registered** (owner's final decision, 28 Nov).

## The problem

On Telegraph, an Evaluator decides which miner answers win. For security reviews, the dangerous
answers are the plausible ones: an advisory id for the wrong package, a patched version called
vulnerable, a confident "Secure" on vulnerable code, a fix that doesn't fix. Judges that reward
length, fluency or security keywords pick them. On our material those shortcut judges score about
50%, and the canonical evaluator for this intent scored 71.43% on its hidden sample
(15 of 21, 10 Nov 2026).

## What was built

| Part | Where |
|---|---|
| Ten-family failure taxonomy: F1 wrong advisory id, F2 version-range error, F3 missed critical, F4 context reversal, F5 overconfident "Secure", F6 false alarm, F7 inconsistent fields, F8 wrong severity or class, F9 needless hedging, F10 ineffective fix | [`docs/ADVERSARIAL_CRITERIA.md`](../docs/ADVERSARIAL_CRITERIA.md) |
| Public training and validation pairs: 264 + 87, with sidecar metadata | `data/public/`, `data/validation/`, `data/meta/` |
| Dataset release v1.0: train, validation and the 40 independent test pairs, with a dataset card and checksums | [Hugging Face](https://huggingface.co/datasets/Ritapossible/adversarialeval-security-review), [GitHub release](https://github.com/Ritapossible/AdversarialEval/releases/tag/dataset-v1.0), [`release/`](../release/adversarialeval-security-review-v1/) |
| Generators and checks: OSV-verified minimal pairs, id checks, label checks, token budget, near-duplicate detection, shortcut judges, the kit's dataset gate | `tools/`, `eval/baselines.py`, `scripts/check_data.sh` |
| Pool material (private; never published) | `data/private/` (git-ignored) |
| Adapter: LoRA and reward head on Telegraph's ModernBERT-base foundation, trained with the unmodified official kit | `scripts/train.sh`, `scripts/export.sh` |
| Frozen registration rule | [`eval/RULE-registration.md`](../eval/RULE-registration.md) |

Quality gates applied to every pool pair: every advisory fact checked against OSV, human review,
length ratio at most 1.25 with the chosen answer longer in 35 to 65% of rows, and
deduplication across public, validation, test and pool sets.

## Results

**Pool contribution (testnet, contributor wallet `0x31Cf659edcDd1A6bF98302cbA5E7CEA8dc143095`)**

| Batch | Uploaded | Rows | Status | Report |
|---|---|---:|---|---|
| Flaw families F1 to F10 | 14 Nov 2026 | 81 | eligible, attested | [`2026-11-14-pool-upload.md`](../eval/reports/2026-11-14-pool-upload.md) |
| Severity pairs (F8) | 18 Nov 2026 | 83 | eligible, attested | [`2026-11-18-pool-batch2.md`](../eval/reports/2026-11-18-pool-batch2.md) |
| **Total** | | **164** | **all eligible** | raw node API output, 22 Nov: [`2026-11-22-evalpool-mine.json`](../eval/reports/raw/2026-11-22-evalpool-mine.json) |

**Adapter (same-author validation data; the registration decision uses the independent test)**

| Measure | Result | Report |
|---|---|---|
| Pairwise accuracy, 87 validation pairs, two seeds | 72.4% and 74.7% | [`2026-11-11-cpu-v3-seed7.md`](../eval/reports/2026-11-11-cpu-v3-seed7.md) |
| Strongest shortcut judge on the same pairs | at most 58% | `scripts/check_data.sh` |
| Whole failure types held out from training | 37 to 39%: not learned without examples | [`2026-11-14-lofo.md`](../eval/reports/2026-11-14-lofo.md) |
| Local rehearsal of the node's remote check (kit executor, WASM engine, the node's client) | WASM and PyTorch agree on 87 of 87 pairs | [`2026-11-11-rehearsal-cpu-v3-seed13.md`](../eval/reports/2026-11-11-rehearsal-cpu-v3-seed13.md) |
| A shortcut found and removed | an early model preferred any "vulnerable" answer (100% vs 0% on version pairs); balanced minimal pairs fixed it | [`2026-11-10-cpu-v1-seed7.md`](../eval/reports/2026-11-10-cpu-v1-seed7.md) |

**Adoption:** another team's miner on #198 (Femtech-web, running Salence) reports "80.6% correct on
264 held-out AdversarialEval questions", using our public training pairs as its test set
(MEMORY, 22 Nov). That is independent use of the material we published.

## Independent test and registration

- **Rule** ([`eval/RULE-registration.md`](../eval/RULE-registration.md)): at least 40 pairs from
  at least 2 independent outside authors, frozen by hash before scoring and scored once. Register
  only if accuracy is at least 80%, the Wilson lower bound at least 65%, and every shortcut judge
  at most 60%. Amendment 1 allows AI-assisted pairs from independent authors, reported
  separately.
- **Collected:** 20 pairs from Fexx (GPT-6) and 20 from Lino (Grok), both author-reviewed
  ([Fexx intake](../eval/reports/2026-11-18-test-intake-fexx.md)); frozen by hash on 24 Nov
  ([freeze](../eval/reports/2026-11-24-test-freeze.md)).
- **Result** ([report](../eval/reports/2026-11-24-test-score.md)): 31 of 40, **77.5%** (95% CI
  62.5 to 87.7%); Fexx 85%, Lino 70%; strongest shortcut judge 60%. Bar: 80% and a lower bound of
  65%, so the rule says **do not register**. An override to register anyway was considered on 24
  Nov and withdrawn on 28 Nov: **not registered**. The bar is not lowered, and no retraining follows
  from the score.
- **Separate, not independent:** 21 author-written, AI-assisted pairs from defiplusacademy, kept
  out of the test set and to be reported under their own heading
  ([intake notes](../data/authoring/security_review/author_test/README.md)).

## Reproduce

```bash
bash scripts/setup_kit.sh --tokenizer
pip install -r third_party/telegraph-wasm-baseline/requirements.txt
bash scripts/check_data.sh                                     # every data check and shortcut judge
python tests/test_tools.py
bash scripts/train.sh cpu-v3 --epochs 6 --lr 0.0002 --seed 7   # about 40 minutes on CPU
```

## Limits

- Validation pairs share an author with the training pairs, so they overstate real accuracy.
- Failure types absent from training are not learned (37 to 39% held out).
- Independent test 77.5%, below our 80% bar; the adapter is not registered.
