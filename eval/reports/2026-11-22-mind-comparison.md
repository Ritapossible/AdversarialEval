# Dependency Guard Mind: with and without Telegraph (2026-11-22)

Telegraph asked Minds builders to test the same tasks with and without Telegraph, at comparable
budgets, and to report what actually improves. This is that test for **Dependency.Guard**
(Mind id `38266542-f36b-1410-8467-00039ce7df11`), on 12 package versions.

## Setup

- **Packages:** the first six package pairs in [`bench/cases-v2.json`](../../bench/cases-v2.json)
  (a rule fixed before running): for jinja2, pyyaml, lodash, minimist, jackson-databind and
  snakeyaml, the last affected version and the current clean release. 6 vulnerable, 6 clean.
- **Truth:** the benchmark's frozen OSV truth. BLOCK is correct for an affected version, PASS for a
  clean one. FLAG or no answer counts as neither.
- **Arms:**
  - **A, Mind alone.** One message to the Mind: use only your own knowledge and web search, no
    Telegraph, no Verified Ask, don't reuse earlier verdicts.
  - **B, Telegraph trusted.** One `SECURITY_REVIEW_GENERAL` call per package through Anjoman's
    ranked route, acted on by its `verdict` field as a buyer's code would.
  - **C, Telegraph + Verified Ask.** The same first answer, checked free against OSV and deps.dev;
    one re-ask of another provider (a1-preflight, the benchmark's most accurate) only when the
    check proves the answer wrong or it has no verdict.
- B and C come from one run (`mind/connector/guard.mjs`), so they saw the same first answers.
- **Evidence:** [`mind/evidence/2026-11-22T12-56-00-304Z.json`](../../mind/evidence/2026-11-22T12-56-00-304Z.json)
  (every answer, check and escrow receipt) and
  [`mind/evidence/2026-11-22-mind-alone.json`](../../mind/evidence/2026-11-22-mind-alone.json)
  (the message, the Mind's reply, and Verified Ask run on the Mind's own claims).
- **Reproduce the scores:** `python mind/compare.py mind/evidence/2026-11-22T12-56-00-304Z.json mind/evidence/2026-11-22-mind-alone.json`

## Result

| | A: Mind alone | B: Telegraph trusted | C: Telegraph + Verified Ask |
|---|---:|---:|---:|
| Correct decisions (of 12) | **12** | 4 (of 7 answered) | **12** |
| Missed vulnerabilities (wrong PASS) | 0 | **2** | 0 |
| False alarms (wrong BLOCK) | 0 | 1 | 0 |
| Not answered | 0 | 5 (our balance, see below) | 0 |
| Time for all 12 | 596 s (one reply) | | 316 s (sequential calls, incl. re-asks) |
| Cost | about 9 Minds credits (about $0.09) | $0.14 | $0.22 (14 Telegraph answers) |
| Every claim machine-checked | no (we checked it afterwards) | no | yes, before the decision |
| Receipt per answer | no | yes | yes |

## What we learned

**1. Trusting the ranked route as-is is the real risk.** The route answered the first 7 packages
with TxLens. It said "Secure" on vulnerable jinja2 3.1.5 and lodash 4.17.23 while its own count
said 1 and 2 vulnerabilities, and "Needs changes" with 0 vulnerabilities on clean pyyaml 6.0.3. A
buyer acting on the `verdict` field gets 4 of those 7 right and ships two known-vulnerable
versions.

The other 5 routed asks were refused by Anjoman with HTTP 400: "Insufficient escrow balance: you
have $0.19 effective, this call costs $0.26". A routed ask reserves $0.26 up front, though it
charged $0.02 here; our $0.50 test balance fell below the hold after 7 calls. So those 5 are
"not answered" because of our balance, not a network failure. Asks to a single named miner reserve
only its price, which is why the re-asks still worked. The connector now reads the balance first
and asks the fallback miner directly when it is below the hold.

**2. Verified Ask turns that into 12 of 12 at a small cost.** It caught all three
self-contradicting answers, and the five refused asks went to one other provider; one re-ask each
fixed them. That is 8 extra
calls ($0.08), and only where an answer was proven wrong, not three providers on every question.

**3. A web-searching Mind matched it on these packages.** On 12 popular packages with well-known
advisories, the Mind alone got all 12 right, citing the advisories. Running Verified Ask on its
claims: 11 of 12 verified; for jackson-databind 2.21.6 it cited `CVE-2026-110879`, which exists
in OSV only as a bare CVE record with no package, so it couldn't be confirmed.

So on familiar packages, Telegraph plus Verified Ask didn't beat the Mind on accuracy. What it
added:
- **about half the time** (316 s against 596 s);
- **every claim checked by machine before the decision**, with the failing check named; the
  Mind's claims could only be checked after the fact;
- **a receipt for every paid answer**, so the cost is auditable;
- **a structured verdict** that code can act on, instead of prose to parse.

**4. What this test doesn't show.** The packages are popular, with advisories that web search finds
easily; that favours the Mind alone. Telegraph's own advice is to try unfamiliar cases, and that
is the next test: newly published advisories, less common ecosystems, and versions that don't
exist, where search is weaker and a miner's live lookup should matter more.

## Second set: less common ecosystems and packages that don't exist

Run the same day, the set fixed before running: the six package pairs the first set didn't use
(Go: gin, x/net; Rust: hyper, tokio; Ruby: rack, nokogiri) plus the benchmark's two "unknown"
cases (a PyPI package that doesn't exist, and jinja2 99.0.0). For those two, FLAG is correct and
a confident PASS or BLOCK is wrong. Mind-alone evidence:
[`mind/evidence/2026-11-22-mind-alone-set2.json`](../../mind/evidence/2026-11-22-mind-alone-set2.json).
Evidence: [`mind/evidence/2026-11-22T13-58-35-411Z.json`](../../mind/evidence/2026-11-22T13-58-35-411Z.json).

| | A: Mind alone | B: Telegraph trusted | C: Telegraph + Verified Ask |
|---|---:|---:|---:|
| Correct decisions (of 14) | **14** | 7 | 12 |
| Missed vulnerabilities (wrong PASS) | 0 | 1 (x/net 0.61.0) | **0** |
| False alarms (wrong BLOCK) | 0 | 1 (nokogiri 1.19.7) | 0 |
| Confident answer on a package that doesn't exist | 0 (both FLAGged) | **2** ("Secure" on both) | **0** (both FLAGged) |
| FLAG, sent to a person | 0 | 1 | 2 (the two Go vulnerable versions) |
| Not answered | 0 | 3 (2 transient "payment rejected", 1 network error) | 0 |
| Time | 86 s | | about 4 min |
| Cost | about 10 Minds credits, no Telegraph fees | $0.23 | $0.33 |

- **Go is where both providers failed.** TxLens and a1-preflight both called gin 1.5.0 (8
  advisories in OSV) and x/net 0.61.0 (2) safe or gave a count of 0. Verified Ask contradicted
  both answers, so the Mind FLAGs them for a person instead of passing them. No vulnerable version
  got through; the cost is a human look at two packages.
- **Fabricated citations, caught.** TxLens's "Secure" on gin 1.12.0 cited an advisory for
  `golang.org/x/crypto` and seven CVE ids OSV doesn't know (the same list vulnrank-triage gave in
  the benchmark), and its "Insecure" on rack 2.2.9 cited placeholders such as `CVE-2023-xxxx`.
  The verdicts happened to be right; the evidence wasn't, and the re-ask gave a clean answer.
- **Non-existent packages:** the routed miner said "Secure" for a package and a version that were
  never published. Verified Ask's registry check caught both; a buyer trusting the route would
  have approved a typo-squatting-shaped name.
- **The Mind alone got all 14 right, in 86 seconds**, including both Go versions that both
  Telegraph providers got wrong. Its stated method explains it: it checked each version against
  the registries (proxy.golang.org, crates.io, rubygems.org, PyPI) and queried OSV per exact
  version. Those are the same free sources the benchmark's truth and Verified Ask use. Verified
  Ask confirmed all 12 of its decisions on existing packages.
- **An option, not taken:** when both answers are contradicted and OSV itself lists advisories,
  the free check alone could BLOCK. We kept FLAG, so a decision never rests on one source.

## What the two sets say together

For the question "does this exact package version have a known, published vulnerability?",
**a free OSV lookup is the reference, and a Mind that can call it doesn't need to pay anyone.**
That matches the benchmark: across rounds 2 to 4, only one Telegraph miner beat the free OSV
lookup on packages. Telegraph's security miners, as they answered on 22 Nov, added cost and
errors on this question; Verified Ask kept those errors from reaching a decision.

Where paid specialist answers can still earn their price, and what we test next:
- **code review**, where there is no free oracle to look up (the benchmark's code twins; a1-preflight
  got 10 of 12 in round 4); here Verified Ask has nothing to check against, which is the job of
  the evaluator model;
- **advisories too new for OSV**, and private or less-indexed ecosystems.

So the product claim we stand behind is narrow: Verified Ask stops wrong paid answers from
becoming decisions, and the benchmark shows a buyer which providers are worth paying for. We do
not claim that buying Telegraph answers beats a free lookup on known package vulnerabilities; on
22 Nov it didn't.

## Running inside the Mind (same day)

After Telegraph confirmed the route (Minds' own HTTP tool, the Anjoman key held as a private
credential), the same flow runs inside Dependency.Guard with no outside code: one routed
`/engine/ask`, then `/api/verify`, then one direct re-ask only when the check fails. Its first
in-Mind run blocked minimist 1.2.5 and lodash 4.17.23, both verified, with receipts. It now
keeps a watchlist and re-checks approved versions once a day with the free check only, buying a
fresh answer only if a PASS is contradicted (cap $0.10 a day):
[`mind/evidence/2026-11-22-watchlist.json`](../../mind/evidence/2026-11-22-watchlist.json).

Two things it found:
- Three routed asks at 13:44 to 13:45 UTC were refused with HTTP 400 "Payment was rejected by
  the facilitator" and charged nothing; the identical request settled minutes later. A transient
  payment-side failure, not a request problem.
- **A routed ask can pay two miners.** One routed call settled $0.02 as two payments (TxLens and
  a1-preflight, receipts in the watchlist). Our connector's routed calls also show $0.02. So the
  ranked route itself sometimes buys a second answer; a buyer budgeting "1x" should expect up to
  2x on the route.

## Limits

- 12 packages, one run per arm, testnet miners. No intervals are given; at this size, differences
  of one or two packages are noise.
- Arm A's cost is converted from Minds credits at the published US$10 per 1,000; arm C's figure
  doesn't include the Minds credits for the Mind's write-up (about 5 per report).
- The route changed rank 1 between our benchmark round 4 (Salence) and this run (TxLens), which
  shows how much the default route depends on the day's ranking.
