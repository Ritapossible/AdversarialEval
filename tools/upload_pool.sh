#!/usr/bin/env bash
# Sign and upload a JSONL file of rows to a Telegraph node's evaluation pool.
#
#   CONTRIBUTOR_PRIVATE_KEY=0x... bash tools/upload_pool.sh SECURITY_REVIEW_GENERAL data/private/security_review_general.pool.jsonl
#   bash tools/upload_pool.sh --dry-run SECURITY_REVIEW_GENERAL <file>     # show what would be signed; no key needed
#
# Protocol (docs: scoring/contribute-evaluation-data.md): EIP-191 personal_sign over exactly
#   Telegraph eval-pool submission v1\nintent_id: <I>\nbody_sha256: <hex>\nnonce: <N>\nchain_id: <C>
# with no trailing newline; POST the exact bytes with --data-binary (never -d, which strips newlines).
# Env: NODE (default testnet devnode), CHAIN_ID (default 11155111 Sepolia). Needs: foundry `cast`, curl, openssl.
set -euo pipefail

DRY=0
if [ "${1:-}" = "--dry-run" ]; then DRY=1; shift; fi
INTENT=${1:?usage: upload_pool.sh [--dry-run] <INTENT_ID> <file.jsonl>}
FILE=${2:?usage: upload_pool.sh [--dry-run] <INTENT_ID> <file.jsonl>}
NODE=${NODE:-https://devnode.telegraphprotocol.com}
CHAIN_ID=${CHAIN_ID:-11155111}
ROOT=$(cd "$(dirname "$0")/.." && pwd)

[ -f "$FILE" ] || { echo "no such file: $FILE" >&2; exit 2; }

# refuse files that are not the private pool set, so public/validation rows are never uploaded by mistake
case "$(realpath "$FILE")" in
  "$ROOT"/data/private/*) ;;
  *) echo "refusing: only files under data/private/ may be uploaded (public and validation sets must stay out of the pool)" >&2; exit 2 ;;
esac

# body checks the node would otherwise reject per row
python3 - "$FILE" "$INTENT" <<'PY'
import json, sys
path, intent = sys.argv[1], sys.argv[2]
raw = open(path, "rb").read()
if len(raw) > 32 * 1024 * 1024: sys.exit("body over 32 MB: split the file on whole lines")
bad = 0
for n, line in enumerate(raw.decode("utf-8").splitlines(), 1):
    if not line.strip(): continue
    r = json.loads(line)
    if len(line.encode()) > 64 * 1024: print(f"row {n}: over 64 KiB"); bad += 1
    if r.get("intent_id") not in (None, intent): print(f"row {n}: intent_id mismatch"); bad += 1
    if r.get("label_kind", "preference_pair") != "preference_pair": print(f"row {n}: unexpected label_kind"); bad += 1
    if (r.get("provenance") or {}).get("source_kind") in ("llm", "synthetic", "generated", "model"):
        print(f"row {n}: note: source_kind forces provenance 'unverified'")
if bad: sys.exit(f"{bad} rows would be rejected")
PY

BODY_SHA=$(sha256sum "$FILE" | cut -d' ' -f1)
NONCE=$(openssl rand -hex 16)
MSG=$(printf 'Telegraph eval-pool submission v1\nintent_id: %s\nbody_sha256: %s\nnonce: %s\nchain_id: %s' \
  "$INTENT" "$BODY_SHA" "$NONCE" "$CHAIN_ID")

if [ $DRY -eq 1 ]; then
  echo "rows: $(grep -c . "$FILE")  node: $NODE"
  echo "--- message to sign ---"; printf '%s\n' "$MSG"; echo "-----------------------"
  exit 0
fi

: "${CONTRIBUTOR_PRIVATE_KEY:?set CONTRIBUTOR_PRIVATE_KEY (never commit it)}"
ADDR=$(cast wallet address --private-key "$CONTRIBUTOR_PRIVATE_KEY")
SIG=$(cast wallet sign --private-key "$CONTRIBUTOR_PRIVATE_KEY" "$MSG")

echo "uploading $(grep -c . "$FILE") rows to $INTENT as $ADDR"
curl -sS -X POST "$NODE/api/evalpool/submissions?intent_id=$INTENT&submitter=$ADDR" \
  -H "Content-Type: application/x-ndjson" \
  -H "X-Evalpool-Signature: $SIG" \
  -H "X-Evalpool-Nonce: $NONCE" \
  --data-binary @"$FILE"
echo
echo "check rows:  curl -s \"$NODE/api/evalpool/submissions/mine?submitter=$ADDR&intent_id=$INTENT\""
echo "pool status: curl -s \"$NODE/api/evalpool/status?intent_id=$INTENT\""
