# Code-review test v2: subtle flaws, fixes and decoys (2026-11-22)

The first code test used one-line textbook snippets. This one, pre-registered in
[`mind/code-test-v2/RULE.md`](../../mind/code-test-v2/RULE.md) (commit `8f853b1`, before any paid
call), uses 23 short multi-line functions: 10 with a subtle exploitable flaw, the 10 fixed
versions, and 3 decoys that are safe but look risky. Truth was checked by running the code where
possible; three draft fixes were tightened in review before freezing.

## Result

| Arm | Correct (of 23) | Missed flaws | False alarms on fixes | False alarms on decoys | No answer | Cost |
|---|---:|---:|---:|---:|---:|---:|
| A: Mind alone | **23** | 0 | 0 | 0 | 0 | about 5 Minds credits |
| B: Telegraph route, first run | 0 | 0 | 0 | 0 | 23 (payment outage) | $0 |
| B: Telegraph route, rerun (amendment 1) | 13 | **1** | 6 | 3 | 0 | $0.24 |
| C: a1-preflight, asked directly | 11 | **2** | 4 | 3 | 3 (payment outage) | $0.20 |
| D: Mind, shown B's rerun answers | **23** | 0 | 0 | 0 | 0 | about 5 Minds credits |

Evidence in [`mind/evidence/`](../../mind/evidence/): `2026-11-22-codev2-*.json`, with the
shuffle maps for the Mind arms. Telegraph arms graded with the benchmark rule
(`bench/benchlib.grade`); the counts above were cross-checked against it.

## What happened

**1. A payment outage, and how it was handled.** From about 14:30 to 14:50 UTC Anjoman refused
payments ("Payment was rejected by the facilitator", HTTP 400, no charge): all 23 routed asks and
3 of the direct ones. Amendment 1, committed before any rerun, reran the routed arm once and left
the direct arm's 3 refusals as "no answer". Both routed records are published.

**2. The route sent everything to one miner, and it changed its mind.** In the rerun every
routed ask went to a1-preflight, the miner arm C asked directly 15 minutes earlier. On the 20
snippets answered both times, it gave a different verdict on 5: the vulnerable open redirect went
from Secure to Insecure, the fixed regex from Insecure to Secure, and three fixes moved between
Secure, Needs changes and Insecure. Same miner, same input, different answer.

**3. Telegraph's answers erred on the safe side, mostly.** Both Telegraph arms flagged most
fixes and all three decoys (10 and 9 false alarms in the two arms), and still missed real flaws:
the path-prefix bypass (`startswith` on a path without a separator, both arms) and the `//`
open redirect (arm C). A missed traversal is the costlier error.

**4. The Mind got all 23 right, alone and with Telegraph's answers.** With the routed answers
as evidence it overruled 10 of them: 9 false alarms on safe code and the 1 missed traversal, with
a reason for each, and agreed with the other 13.

## Caveats

- **Arm D is not independent of arm A.** The Mind saw the same 23 functions (in another order)
  in arm A minutes earlier, and said so in its reply. Arm D shows it isn't misled by wrong paid
  answers; it doesn't show what Telegraph's answers would add to a Mind seeing the code for the
  first time. A clean test would use a second Mind, or a fresh set.
- The Mind's own tally said "nine BLOCK, fourteen PASS" while it answered BLOCK ten times; the
  per-line answers are what we score.
- 23 cases. Truth is by construction and review, not by a published advisory per case. The
  snippets are short functions; whole-program review, with data flow across files, is harder.

## What it adds to the earlier tests

Across four tests on 22 Nov (known vulnerabilities in seven ecosystems, packages that don't
exist, textbook code, and these subtler functions), the Mind on its own was never beaten by a
Telegraph answer, and Telegraph's security answers were least reliable on the safe side: fixes,
decoys and clean versions. What paying added was a second, receipted opinion that a careful
reviewer could weigh, and which our checks and the Mind overruled when it was wrong.
