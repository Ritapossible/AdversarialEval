#!/usr/bin/env bash
# Train an adapter with the unmodified kit, then score it per failure family.
#
#   bash scripts/train.sh <run-name> [extra train_adapter args...]
#   e.g. bash scripts/train.sh cpu-v1 --epochs 5 --lr 2e-4
#
# Writes runs/SECURITY_REVIEW-<run-name>/ (git-ignored) and
# eval/reports/<date>-<run-name>.md (commit it). Kit exit codes: 0 pass, 1 gate failed, 2 error.
set -uo pipefail
NAME=${1:?usage: train.sh <run-name> [train_adapter args...]}; shift
INTENT=${INTENT:-SECURITY_REVIEW}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
STEM=$(echo "$INTENT" | tr '[:upper:]' '[:lower:]')
RUN=$ROOT/runs/$INTENT-$NAME
TRAIN=$ROOT/data/public/$STEM.train.jsonl
VAL=$ROOT/data/validation/$STEM.val.jsonl
REPORT=$ROOT/eval/reports/$(date +%F)-$NAME.md
mkdir -p "$RUN"

python3 "$ROOT/tools/build.py" --intent "$INTENT" >/dev/null || { echo "build failed"; exit 1; }
cd "$ROOT/third_party/telegraph-wasm-baseline"
python3 -m float_runtime.train_adapter --intent "$INTENT" --data "$TRAIN" --val-data "$VAL" \
  --config "$ROOT/configs/$STEM.yaml" --out "$RUN" "$@" 2>&1 | tee "$RUN/train.log" \
  | grep -E "epoch .* (done|validation)|gate|accuracy|baseline|FAIL|PASS|Error"
KIT_RC=${PIPESTATUS[0]}
cd "$ROOT"
# The kit at 1ed063e crashes with NameError ('pkg') while printing its "Next" hint AFTER a
# passing gate (exit 1). Trust the verdict in result.json, not the exit code.
VERDICT=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('verdict','?'))" "$RUN/result.json" 2>/dev/null || echo "none")
[ "$VERDICT" = "PASS" ] && KIT_RC=0

{
  echo "# Run \`$NAME\`: $INTENT"
  echo
  echo "Date: $(date +%F) · kit \`$(git -C third_party/telegraph-wasm-baseline rev-parse --short HEAD)\` · data commit \`$(git rev-parse --short HEAD)\` · extra args: \`${*:-none}\`"
  echo
  echo "Train: $(grep -c . "$TRAIN") pairs · Validation (second voice, held out by case): $(grep -c . "$VAL") pairs · kit gate verdict: **$VERDICT**"
  echo
  echo "## Kit log (epochs and gates)"
  echo
  echo '```'
  grep -E "hyperparameters|epoch .* (done|validation)|gate|baseline|accuracy" "$RUN/train.log" | sed 's/^[0-9:]* INFO: //'
  echo '```'
  echo
  if [ -d "$RUN/adapter" ]; then
    echo "## Per-family scoring (eval/score.py, PyTorch float path)"
    echo
    python3 eval/score.py --adapter "$RUN/adapter" "$VAL" "$TRAIN" --probe-pad --json "$RUN/scores.json" 2>/dev/null
  else
    echo "No adapter was saved."
  fi
} > "$REPORT"
echo "report: $REPORT"
exit $KIT_RC
