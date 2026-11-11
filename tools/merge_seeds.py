#!/usr/bin/env python3
"""Merge LoRA adapters trained with different seeds into one package (audit item U8).

For every LoRA target module the effective weight update of seed s is
    dW_s = (alpha_s / r_s) * B_s @ A_s
The merged update is dW = coef * sum_s dW_s (coef = 1/n for "mean", 1 for "sum"). It is
factored back with a truncated SVD to rank r_out (<= 16, the node's limit):
    dW ~= U_r S_r Vh_r  ->  A = Vh_r,  B = U_r S_r / (alpha_out / r_out)
With two rank-8 seeds and r_out = 16 the factorisation is exact. The reward head
(classifier weight and bias) is averaged across the seeds in both modes.

The output directory has the same layout as the kit's adapter dir (adapter_config.json,
adapter_model.safetensors, reward_head.pt), so eval/score.py and scripts/export.sh accept
it unchanged. This reads only our own trained runs.

    python tools/merge_seeds.py --out runs/SECURITY_REVIEW-cpu-v3-merged/adapter \
        runs/SECURITY_REVIEW-cpu-v3-seed7/adapter runs/SECURITY_REVIEW-cpu-v3-seed13/adapter \
        [--mode mean|sum] [--rank 16]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HEAD_KEYS = ("base_model.model.classifier.weight", "base_model.model.classifier.bias")
MAX_RANK = 16


def merge(dirs: list[Path], out: Path, mode: str, rank: int) -> dict:
    import torch
    from safetensors.torch import load_file, save_file

    if rank > MAX_RANK:
        raise SystemExit(f"rank {rank} exceeds the node limit of {MAX_RANK}")
    cfgs = [json.loads((d / "adapter_config.json").read_text()) for d in dirs]
    sds = [load_file(str(d / "adapter_model.safetensors")) for d in dirs]
    for c in cfgs[1:]:
        for k in ("target_modules", "base_model_name_or_path", "task_type"):
            norm = (lambda v: sorted(map(str, v)) if isinstance(v, list) else v)
            if norm(c[k]) != norm(cfgs[0][k]):
                raise SystemExit(f"adapters disagree on {k}")
    keys = set(sds[0])
    if any(set(sd) != keys for sd in sds[1:]):
        raise SystemExit("adapters have different tensor sets")

    coef = 1.0 / len(dirs) if mode == "mean" else 1.0
    alpha_out = cfgs[0]["lora_alpha"]
    scale_out = alpha_out / rank
    merged, kept = {}, []
    for pref in sorted({k[: -len("lora_A.weight")] for k in keys if k.endswith("lora_A.weight")}):
        dw = sum((c["lora_alpha"] / c["r"]) * sd[pref + "lora_B.weight"].double() @ sd[pref + "lora_A.weight"].double()
                 for c, sd in zip(cfgs, sds)) * coef
        U, S, Vh = torch.linalg.svd(dw, full_matrices=False)
        r = min(rank, S.numel())
        energy = float((S[:r] ** 2).sum() / (S ** 2).sum()) if float(S.sum()) else 1.0
        kept.append(energy)
        merged[pref + "lora_A.weight"] = Vh[:r].float().contiguous()
        merged[pref + "lora_B.weight"] = (U[:, :r] * S[:r] / scale_out).float().contiguous()
    for k in HEAD_KEYS:
        merged[k] = (sum(sd[k].double() for sd in sds) / len(sds)).float()
    leftover = keys - set(merged)
    if leftover:
        raise SystemExit(f"unhandled tensors: {sorted(leftover)[:5]}")

    out.mkdir(parents=True, exist_ok=True)
    save_file(merged, str(out / "adapter_model.safetensors"))
    cfg = dict(cfgs[0], r=rank, lora_alpha=alpha_out)
    (out / "adapter_config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    torch.save({"weight": merged[HEAD_KEYS[0]], "bias": merged[HEAD_KEYS[1]]}, out / "reward_head.pt")
    for extra in ("tokenizer.json", "tokenizer_config.json"):
        if (dirs[0] / extra).exists():
            shutil.copy(dirs[0] / extra, out / extra)
    info = {"sources": [str(d) for d in dirs], "mode": mode, "rank": rank, "lora_alpha": alpha_out,
            "modules": len(kept), "min_energy_kept": min(kept)}
    (out / "merge.json").write_text(json.dumps(info, indent=2) + "\n")
    return info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adapters", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=("mean", "sum"), default="mean")
    ap.add_argument("--rank", type=int, default=MAX_RANK)
    a = ap.parse_args(argv)
    if len(a.adapters) < 2:
        raise SystemExit("need at least two adapters")
    info = merge([Path(d) for d in a.adapters], Path(a.out), a.mode, a.rank)
    print(json.dumps(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
