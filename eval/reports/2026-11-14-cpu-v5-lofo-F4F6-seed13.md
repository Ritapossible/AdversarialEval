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

