# Code-review test v2: rule (frozen before any paid call)

The first code test used one-line textbook snippets, which any capable model knows by heart. This
one asks the harder question: can a reviewer tell a subtle flaw from its fix, and safe code from
code that only looks dangerous? Committed before the first paid call; the run records this file's
commit.

## Cases (`cases.json`, built by `make_cases.py`)

23 snippets, each a short multi-line function in Python, Flask or Node.js, at most 256 bytes (the
intent's limit on `target`). Every case carries its CWE, the frozen truth and the reason.

| Group | Count | Truth |
|---|---:|---|
| Vulnerable | 10 | exploitable as written |
| Fixed | 10 | the same function with the flaw removed |
| Decoy | 3 | safe as written, but looks risky (f-string SQL behind an allowlist, `shell=True` with a constant, MD5 as an HTTP ETag) |

The ten pairs: path prefix bypass (CWE-22), argument injection into `git log` (CWE-88), open
redirect through `//` (CWE-601), ReDoS (CWE-1333), prototype pollution (CWE-1321), tar extraction
outside the target (CWE-22), mass assignment (CWE-915), timing-unsafe token comparison (CWE-208),
predictable reset tokens (CWE-338), and SQL injection through `ORDER BY` (CWE-89).

**Truth checks done before freezing** (`tests/test_mind.py` repeats the cheap ones):
- Prototype pollution: the vulnerable merge pollutes `Object.prototype` when run on a
  `__proto__` payload; the fixed merge leaves it and `Object.prototype.toString` untouched.
- Tar: Python's `filter="data"` raises `OutsideDestinationError` on a `../` member.
- ReDoS: the vulnerable pattern's time grows exponentially (0.02 s at 18 characters, 1.5 s at 24);
  the fixed pattern handles 100,000 characters in about 1 ms.
- Open redirect: the fixed pattern rejects `//host`, a backslash, a tab and a full URL.
- Three draft fixes were tightened in review before freezing: the redirect fix (a tab let
  `/\t/host` through), the git fix (cloning a user URL still reached internal hosts, so the case
  became `git log` with `--end-of-options`), and the merge fix (inherited objects such as
  `toString` could still be written).

## Arms

| Arm | What is asked | Cap |
|---|---|---|
| A, Mind alone | Dependency.Guard reviews all 23 snippets itself, no tools, shuffled with seed 23 | credits only |
| B, Telegraph route, trusted | one routed `SECURITY_REVIEW_GENERAL` call per snippet (`/engine/ask`) | $0.60 |
| C, best miner by our benchmark | one direct call per snippet to a1-preflight (`/engine/ask/20260828`) | $0.30 |
| D, Mind + Telegraph | the Mind sees B's answer for each snippet as evidence it may overrule, shuffled with seed 29 | credits only |

One attempt per snippet and arm; no retries. A transient payment refusal (HTTP 400 with no
charge) counts as "not answered".

## Grading (frozen)

- Telegraph arms use the benchmark rule (`bench/benchlib.grade`, kind `code`): vulnerable is
  correct when the verdict is `Insecure` or `Needs changes` with a count of at least 1; fixed and
  decoy are correct when the verdict isn't `Insecure` and the count is 0. A missing or invalid
  verdict is "no answer".
- Mind arms answer BLOCK or PASS: BLOCK is correct for vulnerable, PASS for fixed and decoy.
- Reported per arm: correct of 23, missed flaws (vulnerable judged safe), false alarms on fixes,
  false alarms on decoys, no answer, cost and time. The decoy false alarms are also reported on
  their own, because a reviewer can reasonably raise the MD5 ETag as a style issue.

## Limits stated now

- 23 cases; differences of one or two are noise.
- Truth is by construction and review, not by a published advisory per case.
- Snippets are short functions, not whole programs: real reviews also need data-flow across files.

## Amendments

**1 (2026-11-22, after the first run, before any rerun).** During the first run (about 14:30 to
14:50 UTC) Anjoman refused payments with HTTP 400 "Payment was rejected by the facilitator",
charging nothing: all 23 routed asks (arm B) and 3 of arm C's direct asks
(token-compare-fixed, reset-token-vulnerable, reset-token-fixed) got no answer. A direct probe
at about 14:53 UTC settled normally.
- Arm B measured the outage, not the route. It is **rerun once in full**
  (`2026-11-22-codev2-routed-rerun.json`); the first record stays published as run.
- Arm C is **not** rerun: its 3 unanswered cases stay "no answer", as the rule says (one attempt,
  no retries).
- Arm D uses the rerun's answers. If the rerun is also refused, arm D uses arm C's answers and the
  report says so.
