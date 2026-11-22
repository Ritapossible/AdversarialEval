# Demo video script: Dependency Guard Mind (about 3 minutes)

For Telegraph's Minds challenge (Apps & Agents track, Mission 10). Recorded on a phone: screen
recording of the Minds app, the site and GitHub, with a voice-over. Read the voice-over lines as
written or in your own words; the times are a guide.

## Before recording

- **Anjoman balance at least $0.40.** A routed ask needs $0.26 free at the moment it is made
  (claim the faucet first; today's balance is about $0.27).
- **Mind credits.** The profile's Cognition figure is what counts (520 on 22 Nov); a report uses
  about 5 and a long web-search task about 10. Replies can take a few minutes; that is normal.
- **Hide secrets.** Never show the Anjoman key, the Verified Ask token, your email, or the
  message where the keys were stored (that thread was closed; record in a new one).
- Open in tabs: the Minds app (Dependency.Guard, a fresh thread), https://adversarialeval.vercel.app,
  and the comparison report on GitHub
  (eval/reports/2026-11-22-mind-comparison.md).
- Do one dry run first. Live answers change with the day's ranking, so the exact miner names may
  differ from this script; say what the screen shows.

## Scene 1. The problem (0:00 to 0:25)

**Screen:** the site's "What a paid answer is worth" section.

> "AI agents now buy security answers from Telegraph's network. But are those answers right?
> I paid for 3,680 of them. The top-ranked miner scored zero out of 36 in two of three rounds,
> and the most common answer had no usable verdict at all. So I built a Mind that checks before
> it trusts."

## Scene 2. Meet Dependency.Guard (0:25 to 0:45)

**Screen:** the Mind's profile (name, Online), then its chat.

> "This is Dependency.Guard, a Mind on Minds by Animoca. It connects to Telegraph through Anjoman
> with the Mind's own HTTP tool. The API key sits in the Mind's private credentials, so it never
> appears in the chat. Setup took one message."

## Scene 3. The request (0:45 to 1:30)

**Screen:** type in a fresh thread:

```
Run Dependency Check on pkg:npm/minimist@1.2.5, pkg:npm/minimist@1.2.8 and pkg:pypi/jinja2@99.0.0
```

While it works:

> "For each package, it buys one answer from Telegraph's ranked route, about one cent. Then it
> checks that answer for free against OSV, deps.dev and the package registries: is the verdict
> right, do the cited advisories exist and apply, does this version even exist? Only if the check
> proves the answer wrong does it ask one other provider. Never three by default."

**Screen:** the reply. Point at each line.

> "minimist 1.2.5: blocked, with the advisory, CVE-2021-44906, verified. 1.2.8: passed, verified.
> And jinja2 99.0.0: that version was never published. Telegraph's ranked answer called it
> Secure. The check caught it, and the Mind flagged it for a person instead of approving a
> package that doesn't exist. Every paid call has a receipt, and here's the total cost."

(If the live run gives a different catch, describe that one. If nothing is caught live, cut to
Scene 4's evidence instead.)

## Scene 4. Catching a wrong answer (1:30 to 2:00)

**Screen:** GitHub, `mind/evidence/` run files or the comparison report, scrolled to the examples.

> "Here are catches from earlier runs. The rank-one miner said 'Needs changes' with zero
> vulnerabilities on a clean package. Another said 'Secure' while listing two vulnerabilities on
> lodash 4.17.23. One cited an advisory about a different package and seven CVE numbers that don't
> exist. Each time, the check caught it, one other provider was asked, and the decision was
> corrected."

## Scene 5. With and without Telegraph (2:00 to 2:30)

**Screen:** the comparison report's two result tables.

> "Telegraph asked us to test with and without it. On 26 packages, trusting the ranked answer
> as-is got 11 of the 18 it answered right, missed three vulnerable versions and approved two
> packages that don't exist. With the free check, nothing unsafe was approved. And the honest
> part: the Mind on its own, looking up OSV directly, got all 26 right. For known package
> vulnerabilities, a free lookup is the bar, and our benchmark shows only one paid miner beats
> it. So the check matters: it stops wrong paid answers from becoming decisions. Code review,
> where there's nothing free to look up, is where we test next."

## Scene 6. It keeps watching (2:30 to 2:45)

**Screen:** the watchlist (mind/evidence/2026-11-22-watchlist.json) or ask the Mind "What are you
watching?"

> "It remembers every version it approved or blocked, and re-checks them every day for free. Only
> if a new advisory hits an approved version does it buy a fresh answer and alert me."

## Scene 7. Limits and links (2:45 to 3:00)

**Screen:** the repo README.

> "Limits: package questions only for now; code review needs our evaluator model next. Testnet,
> small samples, and OSV is the reference. Everything is open source with receipts, so you can
> reproduce it. Repo and site in the description. Thanks to Telegraph, Anjoman and Minds."

## Post

Share the video, the repo and the comparison report in the Minds forum and on X, tagging
`@telegraphprotoc`, `@ysiu`, `@marcmcg` and Minds, with the Mind ID
`38266542-f36b-1410-8467-00039ce7df11`, and invite others to run their own packages through it.
