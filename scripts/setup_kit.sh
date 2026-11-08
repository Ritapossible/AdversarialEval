#!/usr/bin/env bash
# Clone the official adapter kit at a pinned commit and fetch the released Foundation files.
#   bash scripts/setup_kit.sh          # kit + foundation.json (enough to train, export, check)
#   bash scripts/setup_kit.sh --tokenizer  # + pinned tokenizer.json (3.5 MB, for tools/token_budget.py)
#   bash scripts/setup_kit.sh --full   # + 599 MB ONNX, engine, tokenizer (executor / local scoring)
set -euo pipefail
KIT_SHA=1ed063e2f0066cfaf0e124d66ec6a17b7a6121fd
TAG=modernbert-base-lora16-v1
BASE=https://github.com/telegraphprotocol/telegraph-foundation/releases/download/$TAG
ROOT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$ROOT/third_party/foundation"

if [ ! -d "$ROOT/third_party/telegraph-wasm-baseline/.git" ]; then
  git clone https://github.com/telegraphprotocol/telegraph-wasm-baseline "$ROOT/third_party/telegraph-wasm-baseline"
fi
git -C "$ROOT/third_party/telegraph-wasm-baseline" fetch -q origin "$KIT_SHA" 2>/dev/null || true
git -C "$ROOT/third_party/telegraph-wasm-baseline" checkout -q "$KIT_SHA"
echo "kit pinned at $KIT_SHA"

cd "$ROOT/third_party/foundation"
files="foundation.json SHA256SUMS"
[ "${1:-}" = "--tokenizer" ] && files="$files tokenizer.json"
[ "${1:-}" = "--full" ] && files="$files foundation_lora_fp32.onnx foundation_engine.wasm tokenizer.json"
for f in $files; do [ -f "$f" ] || curl -fL --retry 3 -sS -O "$BASE/$f"; done
if command -v sha256sum >/dev/null; then sha256sum -c --ignore-missing SHA256SUMS; else shasum -a 256 -c --ignore-missing SHA256SUMS; fi
