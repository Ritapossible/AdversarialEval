#!/usr/bin/env bash
# Run the kit's dataset gate on a pairs file (needs only numpy).
#   bash scripts/check_data.sh data/public/security_review.train.jsonl [INTENT]
set -euo pipefail
DATA=$(realpath "${1:?usage: check_data.sh <pairs.jsonl> [INTENT]}")
INTENT=${2:-SECURITY_REVIEW}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
KIT=$ROOT/third_party/telegraph-wasm-baseline
[ -d "$KIT" ] || bash "$ROOT/scripts/setup_kit.sh"
cd "$KIT"
python -m float_runtime.train_adapter --intent "$INTENT" --data "$DATA" --out "$ROOT/runs/$INTENT" --check-data
