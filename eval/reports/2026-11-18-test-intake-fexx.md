# Test-set intake: Fexx, 20 pairs (2026-11-18)

**Status:** imported, **not frozen and not scored**. `eval/RULE-registration.md` needs at least
40 pairs from at least 2 independent authors before its SHA-256 freeze and the single scoring run.
This is 20 pairs from 1 author.

## Provenance (Amendment 1)

- **Author:** Fexx ([@fexx301](https://github.com/fexx301)), an independent Evaluators-track
  entrant on other intents. Delivered on Discord, 2026-11-18.
- **Drafting model:** a GPT-6 agent (OpenAI), chosen by the author because our training data was
  drafted with Claude. Every pair was read by the author before sending.
- **No access to our data:** the author states that only our rule, reviewer guide and CSV
  template were used, not our training, validation or authoring data.
- **Raw file:** [`data/reviewers/fexx-2026-11-18.csv`](../../data/reviewers/fexx-2026-11-18.csv),
  kept exactly as received.
- **Imported file:** `data/authoring/security_review/test/fexx.jsonl` →
  `data/test/security_review.test.jsonl`, with `source_kind: ai_assisted` and the drafting model
  on every row (`tools/import_reviewer_csv.py --drafted-with`).

## Checks run on import

| Check | Result |
|---|---|
| Advisory facts, re-verified on OSV by us | **All 3 correct.** lodash-es 4.17.19 is inside GHSA-p6mc-m468-83gw (lodash-es fixed in 4.17.20; lodash in 4.17.19). minimist 0.2.3 and 1.2.5 are both inside GHSA-xvch-5gv4-984h (fixed in 0.2.4 and 1.2.6). axios 1.8.1 is inside GHSA-jr5f-v2jv-69x6, GitHub severity High. |
| Advisory ids exist (`tools/check_ids.py`) | PASS. GHSA-jr5f-v2jv-69x6 was added to `data/sources/ids.txt` as `split=test`. |
| Token budget (512 per rendered row) | PASS: median 133, max 171 |
| Cross-set duplicates (train, validation, pool, test) | PASS: no test prompt is near any other set |
| Rule's shortcut judges (bar 3: each ≤ 60%) | longer 52%, shorter 48%, prompt-overlap 35%, TF-IDF 32%, security terms 50%, hedges 50%/50%, ids cited 55% |
| Kit dataset gate (informational) | FAIL on `surface_probe_acc` 0.67. A probe trained on 20 pairs has a 95% interval of about 43% to 82%, so this is re-checked at 40 pairs, not acted on. |

**Mix:**
- by verdict of the better answer: 7 Secure, 7 Insecure, 6 Needs changes;
- by kind: 3 advisory pairs and 17 code-level pairs (SQL injection, XSS, path traversal, command
  injection, SSRF, IDOR, open redirect, token generation, hard-coded credentials).

## Disclosures

- **Two of the three advisories also appear in our public training data:** GHSA-p6mc (lodash) and
  GHSA-xvch (minimist). The test pairs take different angles:
  - lodash-es vs lodash, which have different patch boundaries;
  - whether minimist 1.2.5 fixes the advisory.

  The prompts are not near-duplicates (dedup above). This will be reported next to the score.
- **We read these pairs while importing.** It does not affect the candidate: the rule fixes the
  candidate by validation accuracy, before and without the test set, and allows no tuning.
- **One tooling fix came out of this intake.** `tools/dedup.py` used `difflib`'s ratio, which is
  asymmetric, so verdicts depended on row order. It now takes the larger of the two orders, with
  a regression test. That surfaced one borderline cross-split pair (train vs pool, 0.70, a shared
  template with a different package and advisory). A person checked it, judged it not a
  duplicate, and recorded it in `data/sources/dedup_reviewed.txt`.

## Next

- A second independent author with about 20 pairs, by **Nov 26** (the rule's cutoff).
- Then record the test file's SHA-256 (`eval/reports/<date>-test-freeze.md`) and score the
  pre-chosen candidate once.
