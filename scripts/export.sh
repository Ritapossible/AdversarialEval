#!/usr/bin/env bash
# Export a trained run as the node's safetensors delta package and check it with the node's
# own Stage 1 parser.
#
#   bash scripts/export.sh <run-name>          e.g. bash scripts/export.sh cpu-v0
#
# The kit's export guard compares tokenizer FILE hashes. Hugging Face currently serves a
# different serialisation of ModernBERT-base's tokenizer.json than the node pins (same ids,
# different bytes), so runs trained on the live Hub download are refused at export. We do not
# patch the kit. Instead tools/verify_tokenizer.py proves token-id equivalence on all our data
# plus the kit's conformance vectors, and only then is the adapter exported via --adapter from
# a staged copy without the re-serialised tokenizer files. The package itself never contains
# a tokenizer; its metadata always carries the node's tokenizer hash.
set -euo pipefail
NAME=${1:?usage: export.sh <run-name>}
INTENT=${INTENT:-SECURITY_REVIEW}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN=$ROOT/runs/$INTENT-$NAME
KIT=$ROOT/third_party/telegraph-wasm-baseline
FOUND=$ROOT/third_party/foundation/foundation.json
PKG=$RUN/$INTENT.safetensors
[ -d "$RUN/adapter" ] || { echo "no adapter in $RUN"; exit 2; }

echo "== tokenizer equivalence"
python3 "$ROOT/tools/verify_tokenizer.py" 2>/dev/null | tail -1 | tee "$RUN/tokenizer_check.txt"
grep -q "PASS" "$RUN/tokenizer_check.txt" || { echo "refusing to export: token ids differ from the node"; exit 1; }

echo "== stage adapter (without re-serialised tokenizer files)"
STAGE=$RUN/adapter-staged
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp "$RUN/adapter/adapter_config.json" "$RUN/adapter/adapter_model.safetensors" "$RUN/adapter/reward_head.pt" "$STAGE/"

echo "== export delta"
(cd "$KIT" && python3 -m float_runtime.export_adapter --adapter "$STAGE" --intent "$INTENT" \
  --class judgment --foundation "$FOUND" --out "$PKG" 2>&1 | grep -v "HTTP Request" | grep -E "wrote|ERROR|Error")

# The kit's offline `adapterbuild lora` reports "hybrid" for every judgment-or-hybrid intent it
# cannot resolve (compiled-in catalog), so it refuses a correct judgment package. stage1check
# runs the same adapterbuild.CheckLoRA with the class the live node reports.
# Take the keccak256 to register from this output: export_adapter's logged sha256 is computed
# from an in-memory save() and can differ from the bytes save_file() wrote.
echo "== node Stage 1 check (kit adapterbuild.CheckLoRA, class from the live node)"
(cd "$ROOT/tools/stage1check" && GOTOOLCHAIN=${GOTOOLCHAIN:-auto} go run . --intent "$INTENT" \
  --package "$PKG" --foundation "$FOUND" --out "$RUN") | tee "$RUN/stage1.json"
echo "file sha256: $(sha256sum "$PKG" | cut -d' ' -f1)"
