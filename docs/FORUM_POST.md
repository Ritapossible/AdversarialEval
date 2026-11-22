# Minds forum post: Dependency.Guard

Two messages (Discord allows 2,000 characters each). Post the first as the thread, the second as
a reply. Replace [VIDEO] once the demo is recorded. Check the character counts with
`python3 -c "import sys;print(len(open(sys.argv[1]).read()))"` on each part if you edit them.

## Message 1 (thread)

**Dependency.Guard: a Mind that checks security answers before it trusts them**
Mind ID: `38266542-f36b-1410-8467-00039ce7df11` · Mission 10 · Apps & Agents

**What it does:** when a project adds or upgrades a package, the Mind buys one SECURITY_REVIEW_GENERAL answer through Anjoman, checks it free against OSV, deps.dev and the registries (Verified Ask), and returns PASS, BLOCK or FLAG with the advisories, receipts and cost. It re-asks one other provider only when the check proves the first answer wrong. It keeps a watchlist and re-checks approved versions daily for free.

**Tested with and without Telegraph** (testnet, 22 Nov, frozen answer keys):
• 26 packages, 7 ecosystems, incl. 2 that don't exist. Trusting the routed answer: 11 right of the 18 it answered, 3 vulnerable versions passed, 2 fake packages called "Secure". With the check: nothing unsafe approved.
• Caught: "Secure" with 2 vulnerabilities in the same answer, advisories for the wrong package, invented CVE ids, `CVE-2023-xxxx` placeholders.
• The honest part: the Mind on its own got all 26 right by querying OSV directly. For known package vulnerabilities a free lookup is the bar, and in our paid benchmark (3,680 calls) only one miner beats it.
• Code review (12 snippets): the Mind alone 12/12; the best miner 9/12; shown that miner's answers, the Mind overruled exactly the 3 wrong ones.

So the value we can show is narrow but real: wrong paid answers never become decisions, every call has a receipt, and the benchmark says which providers are worth paying. Next: a harder code test (23 multi-line cases, pre-registered).

Video: [VIDEO]
Repo: https://github.com/Ritapossible/AdversarialEval
Report: https://github.com/Ritapossible/AdversarialEval/blob/main/eval/reports/2026-11-22-mind-comparison.md

Try it on your own packages and tell me what it gets wrong.

## Message 2 (reply: notes for other builders)

**Notes from wiring a Mind to Anjoman** (thanks @Chrysolite494 for the setup guide):
• `POST /engine/ask` with `{"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": ...}}` returns a structured verdict plus an escrow receipt, which is easier to check than `/agent/chat` prose.
• A routed ask **reserves $0.26** of your balance up front, even when it charges $0.01 to $0.03. Below $0.26 free, Anjoman refuses it with HTTP 400 "Insufficient escrow balance". Asks to one named miner (`/engine/ask/{minerId}`) reserve only its price.
• A routed ask can **pay two miners** (we saw $0.02 settled as two payments). Budget for up to 2x on the route.
• We saw short bursts of HTTP 400 "Payment was rejected by the facilitator", no charge; the same request worked minutes later. Don't treat it as a bad key.
• From Python, set a User-Agent: Cloudflare blocks the default client (error 1010).
• Minds' Cognition on the profile is the real balance; a long "Evaluating" is just slow work.
