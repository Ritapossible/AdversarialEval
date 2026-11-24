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

## Amendment 1 (2026-11-15, before any test pair exists)

An independent reviewer (Fexx, another Evaluators-track entrant on different Intents) offered
pairs **drafted with an AI agent** (not the model that drafted our training data), with every
advisory id and affected version checked on GHSA/OSV and anything uncertain left out.

Change: the test set may include **AI-assisted pairs from independent authors**, provided that:
1. the author is outside this project and hasn't seen our training or validation data;
2. the author names the drafting model and personally reviews every pair before sending;
3. advisory facts are checked against GHSA/OSV (we re-run `tools/check_ids.py` and the token
   budget on import).

Each author's pairs, and AI-assisted vs human-written pairs, are **reported separately** as
well as pooled. The bar is applied to the **pooled** test set, with the minimums unchanged
(≥ 40 pairs, ≥ 2 independent authors). If the pooled set passes but the human-written part
alone falls below 80% (with at least 15 such pairs), the write-up says so prominently.
Nothing else in this rule changes.

## Owner decision (2026-11-24, after the test set was scored)

The frozen bar was applied as written: the test scored 77.5% (Wilson lower bound 62.5%), below
the 80% / 65% bar, so **the rule's outcome is DO NOT REGISTER**
(`eval/reports/2026-11-24-test-score.md`). This section does not change that outcome or the bar,
and the bar is not lowered retroactively.

The project owner has decided to **register the adapter anyway**, as an explicit override of the
rule's recommendation, for these reasons:
- the bar was our own, stricter than the network's: the node itself decides by its remote check
  (11 of 15 public pairs) and its competition, which judge the adapter independently of us;
- a failed attempt costs gas, about 1.5 hours and a bond locked for 2 days, and the bond is never
  slashed (docs, verified 11-12);
- at a true 77.5%, the remote check passes about 3 times in 4 (binomial, 11 of 15).

Every place that reports the adapter says this plainly: "independent test 77.5%, below our
pre-registered 80% bar; registered by the owner's decision, not because it passed." Nothing is
retrained, tuned or re-selected: the candidate stays cpu-v3 seed 13 and its 11 Nov package bytes.

