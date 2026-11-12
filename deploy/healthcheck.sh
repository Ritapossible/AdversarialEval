#!/usr/bin/env bash
# Check a PUBLIC executor exactly as a validator would: the node's own client with its SSRF
# guard ON (no WASM_REMOTE_ALLOW_PRIVATE), 15 pairs, identity echo checked. Run it from any
# machine with the repo, Go and Python (`tokenizers`), e.g. this repo's cloud session.
#   bash deploy/healthcheck.sh https://<EXEC_HOST>/ [pairs.jsonl]
set -euo pipefail
URL=${1:?usage: healthcheck.sh <https-url> [pairs.jsonl]}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DATA=${2:-$ROOT/data/validation/security_review.val.jsonl}
PKG=$ROOT/adapters/SECURITY_REVIEW.safetensors
OUT=$(mktemp -d)
case "$URL" in https://*) ;; *) echo "validators need https://"; exit 2 ;; esac
KECCAK=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['keccak256'])" "$PKG.manifest.json")
(cd "$ROOT/tools/remotecheck" && go build -o "$OUT/remotecheck" .)
python3 "$ROOT/tools/rehearse_batch.py" "$DATA" --out "$OUT/batch.json" --limit 15
"$OUT/remotecheck" --url "$URL" --batch "$OUT/batch.json" --adapter-hash "$KECCAK" \
  --foundation-json "$ROOT/third_party/foundation/foundation.json"
