# Run `cpu-v4-demoheld-seed7`: SECURITY_REVIEW

Date: 2026-11-12 · kit `1ed063e` · data commit `6e62e55` · extra args: `--epochs 6 --lr 0.0002 --seed 7`

Train: 240 pairs · Validation (second voice, held out by case): 87 pairs · kit gate verdict: **PASS**

## Kit log (epochs and gates)

```
dataset gate: PASS (240 pairs)
hyperparameters: Hyperparams(max_length=512, batch_size=1, grad_accum=8, grad_checkpointing=True, lora_rank=8, lora_alpha=32, lora_dropout=0.1, epochs=6, lr=0.0002, weight_decay=0.01, eval_split=0.15, seed=7, eval_batch=4, gate_min_acc=0.65, gate_min_margin_over_baseline=0.1, early_stopping=True, es_metric='val_loss', es_patience=1, es_min_delta=0.001, loss_floor=0.0001)
epoch 0 done: train loss 0.6846
epoch 0 validation: accuracy 0.5977, loss 0.6740
epoch 1 done: train loss 0.6377
epoch 1 validation: accuracy 0.5862, loss 0.6740
epoch 2 done: train loss 0.5322
epoch 2 validation: accuracy 0.6322, loss 0.6679
epoch 3 done: train loss 0.4231
epoch 3 validation: accuracy 0.7011, loss 0.6220
epoch 4 done: train loss 0.3048
epoch 4 validation: accuracy 0.7126, loss 0.5863
epoch 5 done: train loss 0.1978
epoch 5 validation: accuracy 0.6667, loss 0.7331
  "gate_split": "validation",
  "pairwise_accuracy": 0.7126,
  "length_baseline": 0.5747,
  "beats_length_baseline": true,
  File "/home/user/adversarialeval/third_party/telegraph-wasm-baseline/float_runtime/train_adapter.py", line 844, in <module>
  File "/home/user/adversarialeval/third_party/telegraph-wasm-baseline/float_runtime/train_adapter.py", line 838, in main
```

## Per-family scoring (eval/score.py, PyTorch float path)

adapter: `/home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v4-demoheld-seed7/adapter`

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v4-demoheld-seed7/security_review.val.jsonl

**Pairwise accuracy: 71.3%** (87 pairs; 95% CI 61.0%–79.7%)

| source | n | accuracy |
|---|---|---|
| hand-written | 39 | 74% |
| generated minimal pairs | 48 | 69% |

| family | n | accuracy |
|---|---|---|
| F1 | 6 | 33% |
| F2 | 33 | 70% |
| F3 | 3 | 100% |
| F4 | 6 | 67% |
| F5 | 5 | 80% |
| F6 | 5 | 60% |
| F7 | 11 | 64% |
| F8 | 11 | 91% |
| F9 | 3 | 100% |
| F10 | 4 | 75% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 5 | 40% |
| F7 | 5 | 40% |
| F8 | 7 | 100% |
| F2-in | 7 | 57% |
| F2-out | 11 | 73% |
| F7 +range in prompt | 4 | 75% |
| F2-in +range in prompt | 5 | 80% |
| F2-out +range in prompt | 4 | 75% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 47 | 74% |
| rejected longer | 40 | 68% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 26 | 65% |
| Insecure | 39 | 82% |
| Needs changes | 22 | 59% |

| format | n | accuracy |
|---|---|---|
| json | 26 | 73% |
| mixed | 34 | 76% |
| prose | 21 | 62% |
| bullets | 6 | 67% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 100% (62 pairs).

## /home/user/adversarialeval/runs/SECURITY_REVIEW-cpu-v4-demoheld-seed7/security_review.train.jsonl

**Pairwise accuracy: 92.5%** (240 pairs; 95% CI 88.5%–95.2%)

| source | n | accuracy |
|---|---|---|
| hand-written | 95 | 99% |
| generated minimal pairs | 145 | 88% |

| family | n | accuracy |
|---|---|---|
| F1 | 24 | 75% |
| F2 | 97 | 93% |
| F3 | 9 | 100% |
| F4 | 16 | 100% |
| F5 | 12 | 100% |
| F6 | 24 | 100% |
| F7 | 27 | 81% |
| F8 | 19 | 100% |
| F9 | 5 | 100% |
| F10 | 7 | 100% |

| generated kind | n | accuracy |
|---|---|---|
| F1 | 21 | 71% |
| F7 | 12 | 83% |
| F8 | 14 | 100% |
| F2-in | 19 | 84% |
| F2-out | 26 | 92% |
| F7 +range in prompt | 10 | 70% |
| F2-in +range in prompt | 26 | 100% |
| F2-out +range in prompt | 17 | 94% |

| length | n | accuracy |
|---|---|---|
| chosen longer | 124 | 89% |
| rejected longer | 116 | 97% |

| chosen verdict | n | accuracy |
|---|---|---|
| Secure | 77 | 95% |
| Insecure | 98 | 96% |
| Needs changes | 65 | 85% |

| format | n | accuracy |
|---|---|---|
| json | 56 | 93% |
| mixed | 33 | 85% |
| prose | 99 | 94% |
| bullets | 52 | 94% |

Padding probe: of the pairs it got right, the adapter still prefers the chosen answer after the rejected one is padded to 1.5x length in 100% (222 pairs).

