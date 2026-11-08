#!/usr/bin/env bash
# The full data check: build -> token budget -> near-duplicates -> naive baselines + kit gate.
#   bash scripts/check_data.sh [INTENT]        (default SECURITY_REVIEW)
# Needs: numpy, tokenizers  (pip install numpy tokenizers)
set -uo pipefail
INTENT=${1:-SECURITY_REVIEW}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
[ -d third_party/telegraph-wasm-baseline ] || bash scripts/setup_kit.sh
[ -f third_party/foundation/tokenizer.json ] || bash scripts/setup_kit.sh --tokenizer
STEM=$(echo "$INTENT" | tr '[:upper:]' '[:lower:]')
rc=0
echo "== build";        python3 tools/build.py --intent "$INTENT" || exit 1
FILES=$(ls data/public/$STEM.train.jsonl data/validation/$STEM.val.jsonl data/private/${STEM}_general.pool.jsonl 2>/dev/null)
echo "== token budget"; python3 tools/token_budget.py $FILES || rc=1
echo "== dedup";        python3 tools/dedup.py $FILES || rc=1
for f in $FILES; do
  echo "== baselines: $f"
  if [[ "$f" == data/validation/* ]]; then
    # the kit gate governs training data; validation is reported, not gated
    python3 eval/baselines.py "$f" || echo "(validation: reported only, not gated)"
  else
    python3 eval/baselines.py "$f" || rc=1
  fi
done
echo; [ $rc -eq 0 ] && echo "check_data: PASS" || echo "check_data: FAIL"
exit $rc
