# Registration rule: frozen before any test data exists

Committed 2026-11-15, before `data/test/` holds a single pair. Changing this file after the
test set arrives voids the rule. Any later edit must be a new, dated section that says why,
and it never applies to a test set already scored. Method borrowed from a Season I winner's
practice (fexx301/oathcast-telegraph-s2: "frozen rule, written and committed before any run").

## Question
Should we register an AdversarialEval adapter on SECURITY_REVIEW (testnet), given that the
node's first check scores 15 public pairs from other contributors and needs 11 right?

## Test set (independent, frozen once, scored once)
- Pairs written by people outside this project, following `docs/REVIEWER_GUIDE.md`,
  imported with `tools/import_reviewer_csv.py` into `data/test/`.
- Minimum: **40 pairs from at least 2 reviewers**. Fewer means no decision, and the entry
  stays "evaluation material".
- Before any model is scored on it, the test file's SHA-256 is recorded in a commit
  (`eval/reports/<date>-test-freeze.md`). Rows are never edited, added or removed after that.

## Candidate (chosen without looking at the test set)
- The recipe of the best two-seed validation mean at freeze time (currently cpu-v3: rank 8,
  lr 2e-4, 6 epochs, 264 training pairs).
- Of its two seeds, the one with the higher **validation** accuracy. Its package is exported
  once, and those exact bytes are the ones scored, rehearsed and registered.
- No retraining, tuning or seed swapping after the test set is scored.

## Measurements (all reported, whatever the outcome)
- Pairwise accuracy on the test set with its 95% Wilson interval, plus per family and per
  answer verdict.
- The shortcut judges on the same pairs: longer-wins, shorter-wins, prompt-overlap,
  TF-IDF-to-prompt, security-keyword count (`eval/baselines.py`).
- The remote-check rehearsal on 15 test pairs (`scripts/rehearse.sh`), with the identity
  echo and WASM-vs-PyTorch agreement.

## Bar (frozen)
**REGISTER** only if all of these hold:
1. test accuracy **≥ 80%**,
2. its 95% Wilson lower bound **≥ 65%**,
3. every shortcut judge on the test set **≤ 60%** (otherwise the set can't separate checking
   from plausibility, and we publish it as a limit, not a result),
4. the rehearsal echoes the identity and agrees with PyTorch on pair order for all 15.

Otherwise **DO NOT REGISTER**. The entry is evaluation material (the uploaded pool rows)
plus the published negative result, reported with the measured numbers.

Why 80%: at a true 80%, a 15-pair check passes about 84% of the time; at 75%, about 69%
(binomial, `eval/reports/2026-11-11-rehearsal-cpu-v3-seed13.md`). The bond is never
slashed (docs), so a miss costs gas, time and a two-day bond lock-up, not money.

## Outcome table
| Result | Action |
|---|---|
| REGISTER | export once → host the bytes at a commit URL → executor VM + `deploy/healthcheck.sh` → `registerWasm` → track `GET /api/wasm/<id>` → report |
| DO NOT REGISTER | no registration; the write-up reports the test result, unseen-type accuracy and shortcut judges as a measured limit |
| No test set by Nov 26 | no registration; same write-up, with "independent test pending" stated plainly |
