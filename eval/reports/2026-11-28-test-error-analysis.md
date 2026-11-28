# Error analysis: the 9 independent-test pairs the adapter got wrong (2026-11-28)

The adapter (cpu-v3 seed 13) scored 31 of 40 (77.5%) on the independent test set, frozen by hash
and scored once on 24 Nov (`2026-11-24-test-score.md`). This note reads the 9 misses from the saved
scores (`eval/reports/raw/2026-11-24-test-scores.json`), joined to the pairs and their metadata by
row id. No model is re-run, and nothing is retrained or re-scored, so the result stays 77.5%.

| Pair | What the better answer knows | Kind of error | Score margin (chosen − rejected) |
|---|---|---|---:|
| t-fexx-007 | Flask templates autoescape HTML by default | false alarm on safe code | −0.63 |
| t-lino-001 | bound SQL parameters are data, not SQL | false alarm on safe code | −1.41 |
| t-lino-002 | JSX text interpolation auto-escapes | false alarm on safe code | −0.74 |
| t-lino-014 | Jinja2 with autoescape escapes HTML | false alarm on safe code | −3.29 |
| t-fexx-006 | the "fix" version 1.2.5 is still inside the affected 1.x range | version-range fact | −0.89 |
| t-lino-013 | the advisory lists every version before 4.19.2 as affected | version-range fact | −2.22 |
| t-lino-003 | the GHSA fix covers malformed URLs only; direct absolute URLs still redirect | incomplete fix | −1.46 |
| t-fexx-015 | a string-prefix check doesn't prove a resolved path is inside the directory | incomplete fix | −1.30 |
| t-lino-007 | it is SQL injection, not XSS | wrong vulnerability class | −1.14 |

## What the misses show

1. **False alarms on safe code are the largest group: 4 of 9.** In each case the worse answer calls
   framework-protected code "Insecure". This is the false-alarm family (F6). The held-out-family
   test on 14 Nov already showed it barely transfers (37 to 39% when held out), and the training
   set has only 26 such pairs. The adapter leans toward the more alarming answer when safety comes
   from a framework default.
2. **Version facts: 2 of 9.** The adapter can't read version ranges from the advisory itself; it
   learned them only through the training pairs' wording.
3. **Incomplete fixes and misclassification: 3 of 9.**
4. **A length effect in two misses, not overall.** The worse answer was longer in 5 misses, but
   by less than 20 characters in 3 of them. Only t-lino-002 (281 vs 108 characters) and
   t-lino-014 (234 vs 79) show a long, alarming worse answer winning, and both are false alarms. In
   the other 4 misses the worse answer was shorter. The shortcut judges stayed at or below 60% on
   this set.
5. **All 9 misses are prose answers**, and 0 of the 5 JSON-formatted pairs were missed. 35 of the
   40 pairs are prose, so this is not significant evidence of a format effect.
6. **By author:** Fexx 3 misses of 20, Lino 6 of 20. 3 of Lino's 6 misses are framework-default false
   alarms (t-lino-001, 002 and 014), against 1 of Fexx's 3.

## What would help (not done; the test stays frozen and scored once)

- More false-alarm pairs on framework defaults (template autoescaping, ORM and driver parameter
  binding, React/JSX escaping), written by authors other than ours, in a new training set.
- Pairs that make the model read an affected range from the cited advisory text.
- A new independent test set, from new authors, before any future registration decision.
