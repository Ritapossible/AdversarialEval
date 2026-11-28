#!/usr/bin/env bash
# Run every step of .github/workflows/ci.yml locally, with the same Python (3.11), before pushing.
#   bash scripts/ci_local.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-$(command -v python3.11 || echo python3)}
step() { printf '%-55s' "$1"; shift; if out=$("$@" 2>&1); then echo PASS; else echo FAIL; echo "$out" | tail -15; exit 1; fi; }
privacy() {
  if git ls-files | grep -E '^data/private/|\.key$|(^|/)\.env$' | grep -vx 'data/private/README.md'; then return 1; fi
  if git grep -nIE '0x[0-9a-fA-F]{64}\b' -- ':!*.ndjson' ':!*.json' ':!*.md' ':!*.lock' ':!package-lock.json' | grep -v 'public-constant'; then return 1; fi
  if git grep -nIE -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' -e 'anjoman_[A-Za-z0-9_-]{16,}' \
       -e '"(private_?key|privateKey|secret|api_?key|apiKey|builderApiKey)"[[:space:]]*:[[:space:]]*"[^"]{8,}"' \
       -e '(sk|ghp|gho|xox[bp])[-_][A-Za-z0-9]{20,}' -- ':!data/sources/osv/*'; then return 1; fi
}
quiet() { "$@" 2>&1 | grep -v -E "distutils-precedence|_distutils_hack|Remainder of file|frozen site|addpackage|<module>|Error processing line|^\s*$" ; return "${PIPESTATUS[0]}"; }
step "privacy guard" privacy
for t in test_tools test_bench test_reproduce test_verify test_mind test_deploycheck test_codeverify test_resolve; do step "tests/$t.py ($($PY -V 2>&1))" quiet "$PY" "tests/$t.py"; done
step "truth source tests" node --test truth-sources/cve-cvss/test/*.test.js
step "website built from its sources" quiet "$PY" tools/build_site.py --check
step "signed evidence unchanged" node tools/evidence_manifest.mjs verify
step "Mind connector tests" node --test mind/connector/test/*.test.mjs
echo "all CI steps pass locally"
