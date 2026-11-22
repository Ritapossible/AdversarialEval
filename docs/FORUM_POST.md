# Minds channel progress post: Dependency.Guard (asking for feedback)

Three messages; Discord allows 2,000 characters each. Post message 1 as the thread or first
message, then 2 and 3 as replies. No video yet (planned for 23 Nov). Every number below comes from
the committed reports: `eval/reports/2026-11-22-mind-comparison.md` and
`eval/reports/2026-11-22-code-review-v2.md`.

## Message 1: what it is

**Dependency.Guard: a Mind that checks security answers before it trusts them**
Mind ID: `38266542-f36b-1410-8467-00039ce7df11` · Mission 10 (Model Economy) · Apps & Agents
Thanks @Chrysolite494 for the setup guide, it's what got the HTTP route working.

**The job:** a coding team adds or upgrades a dependency. The Mind has to say PASS, BLOCK or FLAG for each package, with evidence and cost, and keep watching afterwards.

**How it works inside Minds:**
1. For each package it buys **one** `SECURITY_REVIEW_GENERAL` answer from Telegraph's ranked route through Anjoman (HTTP tool, key in private credentials).
2. It checks that answer **for free** with Verified Ask, our open checker: does the verdict match OSV for that exact version, do the cited advisory ids exist and apply, does the version even exist?
3. If the check proves the answer wrong, it asks **one** other provider. Never three by default.
4. It reports one line per package with the advisories, every receipt and the total cost.
5. It keeps a watchlist and re-checks approved versions every day for free; it only buys a new answer if something changes, capped at $0.10 a day.

Everything is open source with receipts: https://github.com/Ritapossible/AdversarialEval

## Message 2: what the tests found

**Tested with and without Telegraph** (testnet, 22 Nov, answer keys frozen before any paid call):

**Packages** (26 versions, 7 ecosystems, incl. 2 that don't exist)
• Trusting the routed answer: 11 right of the 18 it answered, 3 vulnerable versions passed, 2 non-existent packages called "Secure".
• With the free check: nothing unsafe approved. It caught "Secure" alongside a count of 2 vulnerabilities, advisories for the wrong package, invented CVE ids and `CVE-2023-xxxx` placeholders.
• The Mind on its own: 26 of 26, by querying OSV directly.

**Code review** (23 subtle functions: 10 flaws, their fixes, 3 safe decoys, pre-registered)
• Mind alone: 23/23. Telegraph's route: 13/23. Best miner by our benchmark, asked directly: 11/23. Both missed real flaws and flagged most of the safe code.
• Shown the route's answers, the Mind overruled all 10 wrong ones.
• The same miner gave a different verdict on 5 of 20 snippets, asked 15 minutes apart.

**My honest read:** for known package vulnerabilities a free OSV lookup is the bar (in our 3,680-call benchmark only one miner beats it). What paying added was a receipted second opinion; the value we can show is that wrong paid answers never became decisions.

## Message 3: feedback I'd love

1. **Is "check before trusting" the right shape** for a Mind on Telegraph, given the results? Or would you rather see it lean on Telegraph more and verify less?
2. **Where should a specialist beat a careful Mind?** I'd like a fair test where paid answers can win: very new advisories, private ecosystems, whole-file code review? Suggestions welcome.
3. **Builders:** if your Mind takes security or package answers from Telegraph, would you try Verified Ask on them? It's free; I'll help you wire it in.
4. **Telegraph team:** the facilitator refused all payments for ~20 min today (about 14:30 to 14:50 UTC, HTTP 400, no charge). Is that known? Also, routed asks reserve $0.26 and sometimes settle two payments; is that intended?

Reports: https://github.com/Ritapossible/AdversarialEval/tree/main/eval/reports
Demo video coming tomorrow. Tell me what it gets wrong!
