# Run `cpu-v4-demoheld-seed13`: SECURITY_REVIEW

Date: 2026-11-12 · kit `1ed063e` · data commit `6e62e55` · extra args: `--epochs 6 --lr 0.0002 --seed 13`

Train: 240 pairs · Validation (second voice, held out by case): 87 pairs · kit gate verdict: **FAIL**

## Kit log (epochs and gates)

```
dataset gate: PASS (240 pairs)
hyperparameters: Hyperparams(max_length=512, batch_size=1, grad_accum=8, grad_checkpointing=True, lora_rank=8, lora_alpha=32, lora_dropout=0.1, epochs=6, lr=0.0002, weight_decay=0.01, eval_split=0.15, seed=13, eval_batch=4, gate_min_acc=0.65, gate_min_margin_over_baseline=0.1, early_stopping=True, es_metric='val_loss', es_patience=1, es_min_delta=0.001, loss_floor=0.0001)
epoch 0 done: train loss 0.6940
epoch 0 validation: accuracy 0.6092, loss 0.6800
epoch 1 done: train loss 0.6462
epoch 1 validation: accuracy 0.6437, loss 0.6250
epoch 2 done: train loss 0.5386
epoch 2 validation: accuracy 0.6322, loss 0.6486
epoch 3 done: train loss 0.3871
epoch 3 validation: accuracy 0.6437, loss 0.6474
  "gate_split": "validation",
  "pairwise_accuracy": 0.6437,
  "length_baseline": 0.5747,
  "beats_length_baseline": false,
  "fail_reason": "accuracy 0.6437 is below --gate-min-acc 0.65"
18:59:41 ERROR: evaluation gate FAILED: accuracy 0.6437 is below --gate-min-acc 0.65
```

## Per-family scoring (eval/score.py, PyTorch float path)

adapter: `/home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v4-demoheld-seed13/adapter`

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v4-demoheld-seed13/security_review.val.jsonl

**Pairwise accuracy: 64.4%** (87 pairs; 95% CI 53.9%–73.6%)

| source | n | accuracy |
|---|---|---|
| hand-written | 39 | 67% |
| generated minimal pairs | 48 | 62% |

| family | n | accuracy |
|---|---|---|
| F1 | 6 | 50% |
| F2 | 33 | 58% |
| F3 | 3 | 100% |
| F4 | 6 | 50% |
| F5 | 5 | 80% |
| F6 | 5 | 40% |
| F7 | 11 | 55% |
| F8 | 11 | 100% |
| F9 | 3 | 67% |
| F10 | 4 | 75% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 5 | 60% |
| F7 | 5 | 40% |
| F8 | 7 | 100% |
| F2-in | 7 | 86% |
| F2-out | 11 | 27% |
| F7 +range in prompt | 4 | 75% |
| F2-in +range in prompt | 5 | 100% |
| F2-out +range in prompt | 4 | 25% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 47 | 77% |
| rejected longer | 40 | 50% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 26 | 35% |
| Insecure | 39 | 87% |
| Needs changes | 22 | 59% |

| format | n | accuracy |
|---|---|---|
| json | 26 | 77% |
| mixed | 34 | 62% |
| prose | 21 | 62% |
| bullets | 6 | 33% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 100% (56 pairs).

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v4-demoheld-seed13/security_review.train.jsonl

**Pairwise accuracy: 74.2%** (240 pairs; 95% CI 68.3%–79.3%)

| source | n | accuracy |
|---|---|---|
| hand-written | 95 | 86% |
| generated minimal pairs | 145 | 66% |

| family | n | accuracy |
|---|---|---|
| F1 | 24 | 67% |
| F2 | 97 | 67% |
| F3 | 9 | 89% |
| F4 | 16 | 75% |
| F5 | 12 | 100% |
| F6 | 24 | 79% |
| F7 | 27 | 63% |
| F8 | 19 | 95% |
| F9 | 5 | 100% |
| F10 | 7 | 86% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 21 | 62% |
| F7 | 12 | 42% |
| F8 | 14 | 100% |
| F2-in | 19 | 74% |
| F2-out | 26 | 42% |
| F7 +range in prompt | 10 | 70% |
| F2-in +range in prompt | 26 | 85% |
| F2-out +range in prompt | 17 | 59% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 124 | 82% |
| rejected longer | 116 | 66% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 77 | 61% |
| Insecure | 98 | 91% |
| Needs changes | 65 | 65% |

| format | n | accuracy |
|---|---|---|
| json | 56 | 75% |
| mixed | 33 | 73% |
| prose | 99 | 72% |
| bullets | 52 | 79% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 99% (178 pairs).

