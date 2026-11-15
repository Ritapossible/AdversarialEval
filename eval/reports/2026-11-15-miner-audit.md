# Who can actually answer a SECURITY_REVIEW request? (2026-11-15)

Mission 10 (Model Economy), route 1, step 0: before measuring **cost per verified correct
answer**, check which ranked miners a buyer can reach with the intent's own request.

## Method

- Intent `SECURITY_REVIEW_GENERAL` on testnet (`devnode.telegraphprotocol.com`). Its canonical
  request has one required param, `target` ("Code, package, contract or site to review").
- For each of the 32 miners the node lists, send
  `POST /engine/v1/ask/{minerId}` with `{"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": ...}}`
  and **no payment**, once for each of three targets: a package (`pypi:jinja2@2.10`), an advisory id
  (`CVE-2021-44228`) and a code snippet.
- The node maps params onto the miner's API **before** asking for payment, so the answer is free:
  `402` (with a price) means the request can reach the miner; `503 no_compatible_miner` means the
  miner's API has no field for `target`.
- Ranks and scores: public `GET /api/miners`, latest score per miner for this intent.
- Run 2026-11-15 17:23 to 17:27 UTC, sequential, 1.5 s apart. Tool: `tools/miner_audit.py`.
  Raw output: [`raw/2026-11-15-miner-audit.json`](raw/2026-11-15-miner-audit.json).

## Result

**12 of 32 miners can take the canonical request (all at $0.01 per call). 20 cannot**: the node
answers `no_compatible_miner: /query has no field for required param(s) target` before any payment.

Three of the seven best-ranked miners are in the 20:

- rank 2, score **0.9719**: `secrev-ghsa`, whose only input is `per_page`
- rank 4, score 0.7711: `secrev-circl-last`, input `n`
- rank 7, score 0.1238: `secrev-nvd-kw`, inputs `keywordSearch`, `resultsPerPage`

Their APIs list recent advisories; none takes the code, package or site the buyer asks about.

| Rank | Score | Miner | Takes `target`? | Miner's own input fields |
|---:|---:|---|---|---|
| 1 | 0.9836 | `pr-guard-sentinel` | yes (package, advisory) | `code`, `diff`, `ecosystem`, `name` |
| 2 | 0.9719 | `secrev-ghsa` | **no** | `per_page` |
| 4 | 0.7711 | `secrev-circl-last` | **no** | `n` |
| 5 | 0.9807 | `zk-friendsec` | yes (package, advisory, code) | `target` |
| 5 | 0.9976 | `zk-secpub` | yes (package, advisory, code) | `target` |
| 7 | 0.1238 | `secrev-nvd-kw` | **no** | `keywordSearch`, `resultsPerPage` |
| 9 | 0 | `codewire-security-review` | yes (package, advisory) | `code`, `question`, `source` |
| 10 | 0 | `evidence-security-review` | yes (package, advisory, code) | `target` |
| 11 | 0 | `secrev-circl-browse` | **no** | `vendor` |
| 12 | 0 | `secrev-deps` | **no** | `pkg`, `ver` |
| 13 | 0 | `secrev-depsdev` | **no** | `pkg`, `system`, `ver` |
| 14 | 0 | `secrev-depsdev-cargo` | **no** | `pkg`, `system`, `ver` |
| 15 | 0 | `secrev-depsdev-maven` | **no** | `pkg`, `system`, `ver` |
| 16 | 0 | `secrev-depsdev-pypi` | **no** | `pkg`, `system`, `ver` |
| 17 | 0 | `secrev-ghsa-npm` | **no** | `ecosystem`, `per_page` |
| 18 | 0 | `secrev-ghsa-pip` | **no** | `ecosystem`, `per_page` |
| 19 | 0 | `secrev-nvd` | **no** | `cveId` |
| 20 | 0 | `secrev-osv-cve` | **no** | `cve_id` |
| 21 | 0 | `secrev-osv-ghsa` | **no** | `ghsa_id` |
| 22 | 0 | `secrev-osv-id` | **no** | `id` |
| 23 | 0 | `secrev-osv-log4j` | **no** | `id` |
| 24 | 0 | `secrev-pypi` | **no** | `pkg`, `ver` |
| 25 | 0 | `secrev-pypi-django` | **no** | `pkg`, `ver` |
| 26 | 0 | `zk-astsec` | yes (package, advisory, code) | `target` |
| 27 | 0 | `zk-code-deps` | yes (package, advisory, code) | `target` |
| 27 | 0 | `zk-pysec` | yes (package, advisory, code) | `target` |
| 28 | 0 | `zk-secaudit` | yes (package, advisory, code) | `target` |
| n/a | n/a | `a1-preflight` | yes (package, advisory, code) | `address`, `asset`, `block`, `chain` |
| n/a | n/a | `chainsight-oracle` | **no** | `address`, `base`, `chain`, `hash` |
| n/a | n/a | `telegraph-verity-intelligence` | yes (package, advisory, code) | `address`, `block`, `change`, `claim` |
| n/a | n/a | `txlens` | **no** | `address`, `amount`, `block`, `card_number` |
| n/a | n/a | `zk-ghsapub` | yes (package, advisory, code) | `target` |

Notes:
- Two callable miners returned a transient `503 could not route this question now` for the code
  target only; they took the other two targets.
- Operators (by payout wallet): 18 of the 20 non-callable miners share one wallet; 8 of the 12
  callable miners share another, whose operator discloses running them. Five more miners have one
  wallet each.

## What this means

- **For buyers:** under the canonical request, the realistic choice is the 12 miners that can take
  the request, not the 32 listed. The rank and score don't show which ones those are.
- **For evaluation:** a ranking that scores miners no canonical request can reach is measuring
  something other than the answers buyers get. Two cheap fixes:
  - exclude, or flag in the ranking, miners that fail the node's own param mapping for the intent;
  - score through the same request path buyers use.
- **Limits:**
  - This is one snapshot. Ranks move each epoch.
  - The auto-routed ask with a plain-language `query` may map differently; this audit covers only
    the canonical `intent` + `params` path.
  - A `402` shows the request can reach the miner, not that its answer is right.

## Next (paid step)

Fixed, disclosed set of `target`s with ground truth from OSV:
- affected versions, patched versions, advisory ids;
- unanswerable cases: unknown package, malformed target.

Plan:
- Call each of the 12 callable miners directly at $0.01 per call.
- Check `verdict` and `vulnerability_count` against OSV.
- Report:
  - cost per verified correct answer;
  - first-pass success rate;
  - p95 latency;
  - how that order compares with the node's ranking.
- Shortcut baselines: always "Insecure", always "Secure".
