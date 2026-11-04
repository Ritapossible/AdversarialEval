# Runbook

Every command runs from the repo root unless noted. The kit lives in
`third_party/telegraph-wasm-baseline`, pinned by `scripts/setup_kit.sh`.

```bash
export INTENT=SECURITY_REVIEW             # family prefix: train, export, register
export POOL_INTENT=SECURITY_REVIEW_GENERAL # child: eval-pool uploads
export KIT=third_party/telegraph-wasm-baseline
export NODE=https://devnode.telegraphprotocol.com
export RPC=https://ethereum-sepolia-rpc.publicnode.com
export DIAMOND=0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b
export MACHINA=0xd68305cA83C7AF42A4F720144E7416fB53F8AaF4
export USDC=0xcc194e1a843B658526D0D5C431f670028582Ae17
export ROUTER=0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E
```

Verify the addresses from the Diamond before spending: `cast call $DIAMOND "machinaToken()(address)" --rpc-url $RPC`.

## 0. Setup

```bash
bash scripts/setup_kit.sh                 # clone the kit @ pinned SHA, fetch + verify foundation.json
python -m pip install -r $KIT/requirements.txt   # install a CUDA torch first on a GPU box
```

## 1. Check data (no GPU)

```bash
bash scripts/check_data.sh data/public/security_review.train.jsonl
```

## 2. Train (GPU)

```bash
(cd $KIT && python -m float_runtime.train_adapter --intent $INTENT \
  --data ../../data/public/security_review.train.jsonl \
  --val-data ../../data/validation/security_review.val.jsonl \
  --config ../../configs/security_review.yaml \
  --out ../../runs/$INTENT)
```

Exit 0 means pass, 1 means a gate failed, 2 means an error. Read `runs/$INTENT/result.json`.

## 3. Export the delta

```bash
(cd $KIT && python -m float_runtime.export_adapter --run ../../runs/$INTENT --intent $INTENT \
  --class judgment --foundation ../../third_party/foundation/foundation.json)
```

## 4. Check and get the hash

```bash
(cd $KIT && go run ./cmd/adapterbuild lora --intent $INTENT \
  --package ../../runs/$INTENT/$INTENT.safetensors \
  --foundation ../../third_party/foundation/foundation.json)
# optional, bit-exact local scoring:
#   --foundation-onnx ../../third_party/foundation/foundation_lora_fp32.onnx \
#   --engine float_runtime/engine/foundation_engine.wasm
```

Record the `keccak256` in `MEMORY.md` → Live state.

## 5. Host the package

Commit `runs/$INTENT/$INTENT.safetensors` to a release branch, or attach it to a GitHub
Release. Then use the **immutable** URL:
`https://raw.githubusercontent.com/Ritapossible/AdversarialEval/<COMMIT_SHA>/adapters/SECURITY_REVIEW.safetensors`.
Check it with `curl -sL <url> | sha256sum`, which must equal the `sha256` from step 4.

## 6. Executor (public VM, ≥ 5 GB RAM)

```bash
bash scripts/setup_kit.sh --full          # also fetches the 599 MB ONNX, the engine and the tokenizer
export FOUNDATION_MODEL_PATH=third_party/foundation/foundation_lora_fp32.onnx
export FOUNDATION_MODEL_HASH=0a49b325304bb4cf292e683929689d0457966be264f60bfc94d0072b614bf8e6
export FOUNDATION_ENGINE_WASM_PATH=third_party/foundation/foundation_engine.wasm
export FOUNDATION_ENGINE_WASM_HASH=77643d6e1176ab8744801cef93ccb844d0136ed32b8daa865d541f37d13292de
(cd $KIT && go run ./cmd/adapterexec --package ../../runs/$INTENT/$INTENT.safetensors --listen 127.0.0.1:8080)
```

Put Caddy in front (`deploy/Caddyfile`) for TLS on a public hostname. Then pre-flight it
with the examples repo:

```bash
npm run adapter:check-executor -- --url https://<host>/ \
  --package runs/$INTENT/$INTENT.safetensors --foundation third_party/foundation/foundation.json
```

## 7. Fund the bond wallet (testnet)

```bash
cast send $USDC "mint(address,uint256)" $ADDR 10000000 --rpc-url $RPC --private-key $AUTHOR_PRIVATE_KEY
cast send $USDC "approve(address,uint256)" $ROUTER 6000000 --rpc-url $RPC --private-key $AUTHOR_PRIVATE_KEY
cast send $ROUTER "exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))" \
  "($USDC,$MACHINA,3000,$ADDR,6000000,0,0)" --rpc-url $RPC --private-key $AUTHOR_PRIVATE_KEY
cast call $DIAMOND "entityBonds()(uint64,uint64,uint256,uint256)" --rpc-url $RPC   # 3rd = adapter bond (wei)
```

## 8. Register

```bash
cast send $MACHINA "approve(address,uint256)" $DIAMOND 20000000000000000000 --rpc-url $RPC --private-key $AUTHOR_PRIVATE_KEY
# dry run (free)
cast call $DIAMOND "registerWasm(bytes32,string,string,address,string)(uint256)" \
  "$WASM_HASH" "$WASM_URL" "$INTENT" "$WASM_FEE_ADDRESS" "$WASM_RUNNABLE_URL" \
  --from $ADDR --rpc-url $RPC
# real
cast send $DIAMOND "registerWasm(bytes32,string,string,address,string)(uint256)" \
  "$WASM_HASH" "$WASM_URL" "$INTENT" "$WASM_FEE_ADDRESS" "$WASM_RUNNABLE_URL" \
  --rpc-url $RPC --private-key $AUTHOR_PRIVATE_KEY
```

Track it: `curl -s $NODE/api/wasm/<registrationId>`. This takes about 1.5 h. Paste the final
`eval` object into `eval/reports/`.

## 9. Upload eval-pool rows (private set)

```bash
bash tools/upload_pool.sh $POOL_INTENT data/private/security_review_general.pool.jsonl
curl -s "$NODE/api/evalpool/submissions/mine?submitter=$CONTRIB_ADDR&intent_id=$POOL_INTENT"
curl -s "$NODE/api/evalpool/status?intent_id=$POOL_INTENT"
```

## Rejection triage

| Reason | Fix |
|---|---|
| `ordered N of 15 public pairs correctly` | The adapter doesn't generalise to the pool. Improve the second-voice validation set and data diversity. |
| `identity echo mismatch` / `did not echo` | The executor isn't the reference `adapterexec`, or it's running the wrong package |
| `remote score mismatch` | Not bit-exact. Use the released foundation and engine with `adapterexec` only. |
| `wasm hash mismatch` | The host re-encoded the file, or the URL points at another version |
| `class_mismatch` | Re-export with `--class judgment` |
| `foundation_mismatch` / `tokenizer_mismatch` | Use the released `foundation.json` |
| `awaiting_compatible_material` | The pool has no published snapshot yet (fewer than 5 contributors). Wait. |
| `duplicate wasm hash` | Already registered. Change something, re-export, and use the new hash. |
