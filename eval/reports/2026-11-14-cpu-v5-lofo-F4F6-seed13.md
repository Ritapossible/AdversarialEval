# Run `cpu-v5-lofo-F4F6-seed13`: SECURITY_REVIEW

Date: 2026-11-14 · kit `1ed063e` · data commit `09428ae` · extra args: `--epochs 6 --lr 0.0002 --seed 13`

Train: 218 pairs · Validation (second voice, held out by case): 87 pairs · kit gate verdict: **FAIL**

## Kit log (epochs and gates)

```
dataset gate: PASS (218 pairs)
hyperparameters: Hyperparams(max_length=512, batch_size=1, grad_accum=8, grad_checkpointing=True, lora_rank=8, lora_alpha=32, lora_dropout=0.1, epochs=6, lr=0.0002, weight_decay=0.01, eval_split=0.15, seed=13, eval_batch=4, gate_min_acc=0.65, gate_min_margin_over_baseline=0.1, early_stopping=True, es_metric='val_loss', es_patience=1, es_min_delta=0.001, loss_floor=0.0001)
epoch 0 done: train loss 0.6905
epoch 0 validation: accuracy 0.5747, loss 0.6828
epoch 1 done: train loss 0.5986
epoch 1 validation: accuracy 0.5862, loss 0.6768
epoch 2 done: train loss 0.4233
epoch 2 validation: accuracy 0.5977, loss 0.7560
epoch 3 done: train loss 0.3273
epoch 3 validation: accuracy 0.6667, loss 0.8265
  "gate_split": "validation",
  "pairwise_accuracy": 0.5862,
  "length_baseline": 0.5747,
  "beats_length_baseline": false,
  "fail_reason": "accuracy 0.5862 is below --gate-min-acc 0.65"
12:39:08 ERROR: evaluation gate FAILED: accuracy 0.5862 is below --gate-min-acc 0.65
```

## Per-family scoring (eval/score.py, PyTorch float path)

adapter: `/home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v5-lofo-F4F6-seed13/adapter`

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v5-lofo-F4F6-seed13/security_review.val.jsonl

**Pairwise accuracy: 58.6%** (87 pairs; 95% CI 48.1%–68.4%)

| source | n | accuracy |
|---|---|---|
| hand-written | 39 | 54% |
| generated minimal pairs | 48 | 62% |

| family | n | accuracy |
|---|---|---|
| F1 | 6 | 83% |
| F2 | 33 | 52% |
| F3 | 3 | 67% |
| F4 | 6 | 33% |
| F5 | 5 | 60% |
| F6 | 5 | 20% |
| F7 | 11 | 55% |
| F8 | 11 | 91% |
| F9 | 3 | 100% |
| F10 | 4 | 50% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 5 | 80% |
| F7 | 5 | 40% |
| F8 | 7 | 100% |
| F2-in | 7 | 71% |
| F2-out | 11 | 36% |
| F7 +range in prompt | 4 | 75% |
| F2-in +range in prompt | 5 | 100% |
| F2-out +range in prompt | 4 | 0% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 47 | 74% |
| rejected longer | 40 | 40% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 26 | 19% |
| Insecure | 39 | 79% |
| Needs changes | 22 | 68% |

| format | n | accuracy |
|---|---|---|
| json | 26 | 58% |
| mixed | 34 | 62% |
| prose | 21 | 62% |
| bullets | 6 | 33% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 100% (51 pairs).

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v5-lofo-F4F6-seed13/security_review.train.jsonl

**Pairwise accuracy: 80.7%** (218 pairs; 95% CI 75.0%–85.4%)

| source | n | accuracy |
|---|---|---|
| hand-written | 72 | 97% |
| generated minimal pairs | 146 | 73% |

| family | n | accuracy |
|---|---|---|
| F1 | 28 | 82% |
| F2 | 100 | 73% |
| F3 | 11 | 100% |
| F5 | 15 | 100% |
| F7 | 28 | 68% |
| F8 | 20 | 95% |
| F9 | 6 | 100% |
| F10 | 10 | 100% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 22 | 77% |
| F7 | 12 | 58% |
| F8 | 14 | 100% |
| F2-in | 19 | 63% |
| F2-out | 26 | 65% |
| F7 +range in prompt | 10 | 60% |
| F2-in +range in prompt | 26 | 73% |
| F2-out +range in prompt | 17 | 82% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 112 | 79% |
| rejected longer | 106 | 83% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 51 | 75% |
| Insecure | 103 | 94% |
| Needs changes | 64 | 64% |

| format | n | accuracy |
|---|---|---|
| json | 52 | 81% |
| mixed | 32 | 69% |
| prose | 86 | 81% |
| bullets | 48 | 88% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 99% (176 pairs).

