# Dataset Specification

## Files

| Path | Split | Published? | Uploaded to pool? |
|---|---|---|---|
| `data/public/security_review.train.jsonl` | training | **yes** (GitHub + HF) | **never** |
| `data/validation/security_review.val.jsonl` | held-out, pool-style, second voice | after the hackathon | never |
| `data/private/security_review_general.pool.jsonl` | eval-pool contribution | **never** (git-ignored) | yes |
| `data/meta/*.jsonl` | sidecar labels for every row above | yes (public/validation only) | no |
| `data/sources/sources.jsonl` | real advisory cases | yes | no |

**The three sets are disjoint per source case.** One advisory or snippet family belongs to
exactly one split. Prompts must also be < 85% similar across splits, which is the node's
near-duplicate rule.

## Row schema (what's trained on and uploaded)

```json
{
  "prompt": "Security review this requirements.txt for a public Flask API:\nflask==2.3.3\nrequests==2.31.0\npyyaml==5.3.1",
  "chosen": "Verdict: Insecure. vulnerability_count: 2. Issues: CVE-2020-14343 (PyYAML < 5.4, arbitrary code execution via full_load/FullLoader) — critical; GHSA-9wx4-h78v-vm56 / CVE-2024-35195 (requests < 2.32.0, verify=False persists across a Session) — moderate. Flask 2.3.3 is past the CVE-2023-30861 fix (2.3.2). Fix: pyyaml>=5.4 and use safe_load; requests>=2.32.0.",
  "rejected": "Verdict: Needs changes. vulnerability_count: 1. Issues: CVE-2023-30861 (Flask session cookie disclosure behind a caching proxy) — moderate. PyYAML 5.3.1 and requests 2.31.0 are stable releases with no outstanding advisories. Fix: upgrade Flask to 3.0 and set Vary: Cookie.",
  "label_kind": "preference_pair",
  "provenance": {"source_kind": "human", "source_url": "https://github.com/advisories/GHSA-8q59-q68h-6hv4"}
}
```

| Field | Rule |
|---|---|
| `prompt` | 16–16,000 chars (node). Ours: ≤ 1,200 chars, realistic, states the target and any context that matters. |
| `chosen` / `rejected` | 8–32,000 chars (node). Ours: 150–900 chars each, within ±25% of each other. In the miner response shape. |
| `label_kind` | always `preference_pair` |
| `provenance.source_kind` | `human` for human-authored or human-verified rows. Never `llm`, `synthetic`, `generated` or `model`: those values force `unverified`. (Disclose AI assistance honestly; see open question 5 in `MEMORY.md`.) |
| `provenance.source_url` | **required.** A public `https://` advisory, NVD, OSV, CWE or vendor page that verifies the chosen answer. |
| `margin` | optional, training only. Leave unset (0) in v1. |

**The token budget:** `### Task:\n{prompt}\n\n### Answer:\n{answer}` ≤ 512 ModernBERT tokens
for *both* answers. The decisive flaw must appear in the first ~70% of the answer.

## Sidecar meta (`data/meta/<file>.meta.jsonl`)

Joined on `row_id = sha256(normalised prompt + "\x00" + normalised chosen + "\x00" + normalised rejected)`.

```json
{"row_id": "…", "family": "F2", "subfamily": "patched-flagged+missed-critical", "source_ids": ["GHSA-8q59-q68h-6hv4"],
 "verdict_chosen": "Insecure", "verdict_rejected": "Needs changes", "format": "prose",
 "author": "A", "voice": "primary", "flaw_note": "flags patched flask 2.3.3; calls pyyaml 5.3.1 (<5.4) and requests 2.31.0 (<2.32.0) safe"}
```

## Source case (`data/sources/sources.jsonl`)

```json
{"case_id": "pyyaml-cve-2020-14343", "ids": ["CVE-2020-14343", "GHSA-8q59-q68h-6hv4"], "ecosystem": "pypi",
 "package": "pyyaml", "affected": "<5.4", "patched": "5.4", "cwe": ["CWE-20"], "severity": "critical",
 "urls": ["https://nvd.nist.gov/vuln/detail/CVE-2020-14343"], "split": "public"}
```

## Authoring format (`data/authoring/<intent>/*.jsonl`)

Pairs are written in one rich format. `tools/build.py` validates them and writes the
node/kit files and the sidecar meta above. Private pool pairs live in
`data/private/authoring/<intent>/` (git-ignored).

```json
{"case": "GHSA-8q59-q68h-6hv4", "family": "F2", "split": "public", "format": "prose",
 "prompt": "…", "chosen": "…", "rejected": "…", "source_url": "https://github.com/advisories/GHSA-8q59-q68h-6hv4",
 "verdict_chosen": "Secure", "verdict_rejected": "Insecure",
 "flaw_note": "claims the fix landed in 6.0; it landed in 5.4", "fabricated_ids": [],
 "author": "claude-draft", "reviewed": false}
```

`case` is either an advisory id from `data/sources/ids.txt` or a `code-…` / `v-code-…` id for
a code-pattern case. All rows of a case must share one split, and an advisory case's split is
set in `ids.txt`.

What `build.py` enforces, as hard errors:
- **Required fields and enums:** families F1–F10, the three verdicts, and the formats.
- **Length limits:** the node's limits, plus `https://` source URLs.
- **One split per case:** a case can't straddle splits. Private rows must sit under
  `data/private/`.
- **Advisory ids are verified:** every CVE/GHSA id in a prompt or answer must exist in
  `data/sources/sources.jsonl` (verified via OSV).
- **Trap ids are declared:** an F1 trap id may appear only in `rejected`. If it doesn't
  exist anywhere, list it in `fabricated_ids`. If it's a real advisory for a different
  package or issue, list it in `misattributed_ids`. `tools/check_ids.py` checks both against
  OSV. Random-looking ids are often real: `CVE-2020-28471` (properties-reader) and
  `GHSA-7fh5-64p2-3v2j` (PostCSS) were both "invented" before the check caught them.
- **Withdrawn advisories:** one may appear in `chosen` only if the answer says it was
  withdrawn.

Warnings: the house length ranges, and a chosen/rejected length ratio over 1.25.

## Provenance and review status

The seed pairs (Nov 2026) are **drafted by Claude** (`author: claude-draft`) from verified
OSV and CWE sources, with `reviewed: false`. They're fine for the public training set as
they are. **Before any row goes into the pool set, a human checks it and sets
`reviewed: true`.** Its `source_kind` is then chosen honestly (see open question 5 in
`MEMORY.md`). Never label AI-drafted, unreviewed text as `human`.

## Authoring workflow

1. Pick a source case and verify it on NVD or GHSA (affected range, patched version, CWE).
2. Write the `prompt` (the target, plus any context that matters).
3. Write the `chosen` answer and check every claim against the source.
4. Pick a family. Write the `rejected` answer by changing **one** decisive thing, then
   rebalance its length, format and tone to match the chosen answer.
5. A second person reviews: is the chosen answer correct? Is the rejected answer
   *plausibly* wrong and *really* wrong?
6. Run `scripts/check_data.sh`, which runs the normalise, dedup, token budget, kit gate and
   baselines.

## Validation set (second voice)

- About 80 pairs, written by a different author or with a different style guide: terse
  one-liners, verbose reports, raw JSON, non-native phrasing.
- It covers all families, with source cases not used in train.
- It approximates the remote check and the hidden sample, which draw evenly across
  pool contributors.

## Release

- License: CC-BY-4.0 for the data, decided in Phase 5. Source links stay attached.
- A datasheet: motivation, composition, families, collection process, known limitations,
  and intended use.
