# Run `cpu-v5-lofo-F4F6-seed7`: SECURITY_REVIEW

Date: 2026-11-14 · kit `1ed063e` · data commit `09428ae` · extra args: `--epochs 6 --lr 0.0002 --seed 7`

Train: 218 pairs · Validation (second voice, held out by case): 87 pairs · kit gate verdict: **FAIL**

## Kit log (epochs and gates)

```
dataset gate: PASS (218 pairs)
hyperparameters: Hyperparams(max_length=512, batch_size=1, grad_accum=8, grad_checkpointing=True, lora_rank=8, lora_alpha=32, lora_dropout=0.1, epochs=6, lr=0.0002, weight_decay=0.01, eval_split=0.15, seed=7, eval_batch=4, gate_min_acc=0.65, gate_min_margin_over_baseline=0.1, early_stopping=True, es_metric='val_loss', es_patience=1, es_min_delta=0.001, loss_floor=0.0001)
epoch 0 done: train loss 0.6800
epoch 0 validation: accuracy 0.5517, loss 0.6962
epoch 1 done: train loss 0.5966
epoch 1 validation: accuracy 0.5862, loss 0.6648
epoch 2 done: train loss 0.5380
epoch 2 validation: accuracy 0.6322, loss 0.6372
epoch 3 done: train loss 0.4864
epoch 3 validation: accuracy 0.6207, loss 0.6590
epoch 4 done: train loss 0.4391
epoch 4 validation: accuracy 0.6207, loss 0.6888
  "gate_split": "validation",
  "pairwise_accuracy": 0.6322,
  "length_baseline": 0.5747,
  "beats_length_baseline": false,
  "fail_reason": "accuracy 0.6322 is below --gate-min-acc 0.65"
12:16:30 ERROR: evaluation gate FAILED: accuracy 0.6322 is below --gate-min-acc 0.65
```

## Per-family scoring (eval/score.py, PyTorch float path)

adapter: `/home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v5-lofo-F4F6-seed7/adapter`

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v5-lofo-F4F6-seed7/security_review.val.jsonl

**Pairwise accuracy: 63.2%** (87 pairs; 95% CI 52.7%–72.6%)

| source | n | accuracy |
|---|---|---|
| hand-written | 39 | 59% |
| generated minimal pairs | 48 | 67% |

| family | n | accuracy |
|---|---|---|
| F1 | 6 | 100% |
| F2 | 33 | 48% |
| F3 | 3 | 67% |
| F4 | 6 | 50% |
| F5 | 5 | 80% |
| F6 | 5 | 20% |
| F7 | 11 | 64% |
| F8 | 11 | 91% |
| F9 | 3 | 100% |
| F10 | 4 | 75% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 5 | 100% |
| F7 | 5 | 40% |
| F8 | 7 | 100% |
| F2-in | 7 | 43% |
| F2-out | 11 | 55% |
| F7 +range in prompt | 4 | 100% |
| F2-in +range in prompt | 5 | 20% |
| F2-out +range in prompt | 4 | 100% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 47 | 66% |
| rejected longer | 40 | 60% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 26 | 46% |
| Insecure | 39 | 79% |
| Needs changes | 22 | 55% |

| format | n | accuracy |
|---|---|---|
| json | 26 | 58% |
| mixed | 34 | 74% |
| prose | 21 | 48% |
| bullets | 6 | 83% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 100% (55 pairs).

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v5-lofo-F4F6-seed7/security_review.train.jsonl

**Pairwise accuracy: 76.6%** (218 pairs; 95% CI 70.6%–81.7%)

| source | n | accuracy |
|---|---|---|
| hand-written | 72 | 92% |
| generated minimal pairs | 146 | 69% |

| family | n | accuracy |
|---|---|---|
| F1 | 28 | 61% |
| F2 | 100 | 70% |
| F3 | 11 | 100% |
| F5 | 15 | 100% |
| F7 | 28 | 68% |
| F8 | 20 | 95% |
| F9 | 6 | 100% |
| F10 | 10 | 100% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 22 | 59% |
| F7 | 12 | 58% |
| F8 | 14 | 100% |
| F2-in | 19 | 47% |
| F2-out | 26 | 81% |
| F7 +range in prompt | 10 | 80% |
| F2-in +range in prompt | 26 | 62% |
| F2-out +range in prompt | 17 | 76% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 112 | 70% |
| rejected longer | 106 | 84% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 51 | 78% |
| Insecure | 103 | 90% |
| Needs changes | 64 | 53% |

| format | n | accuracy |
|---|---|---|
| json | 52 | 73% |
| mixed | 32 | 62% |
| prose | 86 | 83% |
| bullets | 48 | 79% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 100% (167 pairs).

