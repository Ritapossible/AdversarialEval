# AI-assisted test pairs from defiplusacademy (not independent)

21 SECURITY_REVIEW test pairs written by defiplusacademy (GitHub: defiplusacademy24-art), drafted with
Claude. **They are not part of the independent test set** and must never be counted toward the
registration rule's "40 pairs from at least 2 outside reviewers".

## Files
- `defiplusacademy.author.jsonl`: authoring rows, labelled `author: author:defiplusacademy`,
  `independent: false`, `source_kind: ai_assisted`, `reviewed: false`.
- `defiplusacademy_author_pairs.csv`: the same pairs in the reviewer-template columns, for reading
  and editing in a spreadsheet.

## Where to put them
Commit the JSONL as `data/authoring/security_review/author_test/defiplusacademy.jsonl`.

- **Not** under `data/authoring/security_review/test/`: `tools/build.py` merges every file in
  that folder into `data/test/`, the independent set.
- **Don't** run `tools/import_reviewer_csv.py` on the CSV: it writes into `test/` and labels the
  rows `reviewer:<handle>`.

Score them separately and report the result under its own heading ("author-written,
AI-assisted"):

    python eval/score.py --adapter <frozen adapter> \
        data/authoring/security_review/author_test/defiplusacademy.jsonl --md eval/reports/<date>-author-pairs.md

## Mix
- 8 where the right verdict is Secure (the worse answer raises a false alarm)
- 7 obvious-but-easy-to-miss bugs
- 6 subtle errors: wrong version range, wrong fixed version, a malicious release treated as
  ReDoS, a fix that doesn't fix, a verdict that contradicts its own count
- Formats: prose, bullets, scanner output, JSON. The worse answer is longer in 10 of 21 pairs.

## Checks already run
- Every CVE/GHSA id and affected/fixed version checked against OSV on 22 Nov 2026
  (CVE-2024-3094, GHSA-f82v-jwr5-mffw, GHSA-pjwm-rvh2-c87w, GHSA-5h86-8mv2-jq9f).
- None of the cited ids appears in `data/authoring/` (training, validation or the existing test file).
- Shortcut judges (`eval/baselines.py`): longer-wins 52%, shorter-wins 48%, prompt-overlap 43%,
  TF-IDF 57%, more-security-terms 55%, hedges 43/57%, more-ids-cited 50%. All within the 60% bar.
- Every prompt is under 1,200 characters (longest: 394).

## Before you use them
Read every pair yourself. Change `reviewed` to `true` only for pairs you have checked, and
delete any pair you aren't sure about ("when in doubt, leave the pair out").

## Intake checks (22 Nov 2026, in this repo)
- Converted from the CSV to `defiplusacademy.jsonl` (21 rows): `split: author_test`,
  `independent: false`, `reviewed: false`, `source_kind: ai_assisted`. The build reads only the
  top-level authoring files and `test/`, so these rows reach neither training nor the
  independent test set.
- Advisories re-checked against OSV: CVE-2024-3094 (alias GHSA-rxwq-x6h5-x525),
  GHSA-f82v-jwr5-mffw (CVE-2025-29927; next 14.2.24 affected, 14.2.25 not),
  GHSA-pjwm-rvh2-c87w (alias CVE-2021-4229, which has no standalone OSV record; ua-parser-js
  0.7.29 affected, 0.7.30 not), GHSA-5h86-8mv2-jq9f (CVE-2024-23334; aiohttp 3.9.1 affected,
  3.9.2 not).
- Token budget (`tools/token_budget.py`): PASS, max 232 of 512 tokens.
- Near-duplicates (`tools/dedup.py` against public, validation, test and the pool): none.
- Shortcut judges (`eval/baselines.py`): strongest 57%, within the 60% bar. The kit's dataset gate
  flags a reused rejected answer at 4.8% (one row of 21 is already over its 2% line) and a
  bag-of-words probe at 66.7% (limit 65%); both are small-sample effects and the gate is meant
  for training sets, so they are recorded, not acted on.
- Reviewed (24 Nov 2026): the maintainer read all 21 pairs; every row now has `reviewed: true`.
  They stay `independent: false` and `ai_assisted`, so they still never count toward the
  independent test set (40 pairs from 2 authors).
