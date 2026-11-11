#!/usr/bin/env bash
# Local dress rehearsal of the node's remote check for an exported run.
#
#   bash scripts/rehearse.sh <run-name> [pairs.jsonl] [--limit N]
#   e.g. bash scripts/rehearse.sh cpu-v3-seed13
#
# 1. starts the kit's reference executor (adapterexec) on the run's exported package, on the
#    real foundation graph and engine (needs scripts/setup_kit.sh --full, 599 MB),
# 2. tokenises the pairs as a validator does (tools/rehearse_batch.py),
# 3. sends them with the node's own client (tools/remotecheck → pkg/wasm/remote) in requests
#    of 15 pairs with the score identity, and reports the per-request verdict,
# 4. compares every WASM score with the PyTorch path (eval/score.py's scores.json).
#
# This proves the package, executor and identity echo work and that our PyTorch numbers
# transfer to the node's engine. It is NOT the node's result: the node uses other
# contributors' public pairs. Expect about 2.5 min per 15 pairs on this CPU.
set -euo pipefail
NAME=${1:?usage: rehearse.sh <run-name> [pairs.jsonl] [--limit N]}; shift
INTENT=${INTENT:-SECURITY_REVIEW}
STEM=$(echo "$INTENT" | tr '[:upper:]' '[:lower:]')
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN=$ROOT/runs/$INTENT-$NAME
F=$ROOT/third_party/foundation
DATA=$RUN/$STEM.val.jsonl
if [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; then DATA=$1; shift; fi
PKG=$RUN/$INTENT.safetensors
OUT=$RUN/rehearsal
PORT=${PORT:-8088}
[ -f "$PKG" ] || { echo "no package; run scripts/export.sh $NAME first"; exit 2; }
[ -f "$F/foundation_lora_fp32.onnx" ] || { echo "no foundation graph; run scripts/setup_kit.sh --full"; exit 2; }
mkdir -p "$OUT" "$ROOT/runs/bin"

(cd "$ROOT/third_party/telegraph-wasm-baseline" && go build -o "$ROOT/runs/bin/adapterexec" ./cmd/adapterexec)
(cd "$ROOT/tools/remotecheck" && go build -o "$ROOT/runs/bin/remotecheck" .)
KECCAK=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['keccak256'])" "$PKG.manifest.json")

FOUNDATION_MODEL_PATH=$F/foundation_lora_fp32.onnx \
FOUNDATION_MODEL_HASH=$(python3 -c "import json;print(json.load(open('$F/foundation.json'))['foundation_hash'])") \
FOUNDATION_ENGINE_WASM_PATH=$F/foundation_engine.wasm \
FOUNDATION_ENGINE_WASM_HASH=$(awk '/foundation_engine.wasm/{print $1}' "$F/SHA256SUMS") \
  "$ROOT/runs/bin/adapterexec" --package "$PKG" --listen 127.0.0.1:$PORT > "$OUT/adapterexec.log" 2>&1 &
EXEC=$!
trap 'kill $EXEC 2>/dev/null' EXIT
for _ in $(seq 120); do grep -q listening "$OUT/adapterexec.log" && break; sleep 1; done
grep -q listening "$OUT/adapterexec.log" || { cat "$OUT/adapterexec.log"; exit 1; }

python3 "$ROOT/tools/rehearse_batch.py" "$DATA" --out "$OUT/batch.json" "$@"
WASM_REMOTE_ALLOW_PRIVATE=true "$ROOT/runs/bin/remotecheck" --url http://127.0.0.1:$PORT \
  --batch "$OUT/batch.json" --adapter-hash "$KECCAK" --foundation-json "$F/foundation.json" \
  --out "$OUT/wasm_scores.json" | tee "$OUT/remotecheck.txt"
[ -f "$RUN/scores.json" ] && python3 "$ROOT/tools/compare_scores.py" "$OUT/wasm_scores.json" "$RUN/scores.json" | tee -a "$OUT/remotecheck.txt"
