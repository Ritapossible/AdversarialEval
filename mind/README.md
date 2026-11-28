# Dependency Guard Mind: setup

A Mind (hellominds.ai) that checks a project's dependency changes for known vulnerabilities. It
buys **one** Telegraph `SECURITY_REVIEW_GENERAL` answer per package through Anjoman, checks that
answer **free** with Verified Ask, and then passes, blocks or flags each package with its evidence,
cost and receipt. It re-asks a different provider only when Verified Ask proves an answer wrong.

Route: the Minds **HTTP tool**, as confirmed by Telegraph on 22 Nov (no Bazaar listing needed).

**Status (22 Nov):** live. Mind **Dependency.Guard**, id `38266542-f36b-1410-8467-00039ce7df11`.
It runs the whole flow itself with its HTTP tool and two private credentials, and keeps a
watchlist of its decisions ([`evidence/2026-11-22-watchlist.json`](evidence/2026-11-22-watchlist.json)).
Every PASS and BLOCK on record is re-checked for free each day by [`watch.py`](watch.py) (the
[`watch`](../.github/workflows/watch.yml) GitHub job; reports in [`evidence/watch/`](evidence/watch/)). The
connector below (`connector/guard.mjs`) runs the same flow from outside Minds and produced the
test evidence; results are in
[`eval/reports/2026-11-22-mind-comparison.md`](../eval/reports/2026-11-22-mind-comparison.md) and
[`eval/reports/2026-11-22-code-review-v2.md`](../eval/reports/2026-11-22-code-review-v2.md).

## 1. Accounts and secrets (owner)

| Step | Where | Notes |
|---|---|---|
| Minds account and a Mind named "Dependency Guard" | hellominds.ai | Record the **Mind ID** for the submission |
| Anjoman API key (`anjoman_...`) | anjoman.ai → dashboard → API keys | 30 requests per minute per key |
| Fund the Anjoman balance | anjoman.ai → dashboard → faucet / wallet | Testnet USDC; a failed job isn't charged |
| Save the Anjoman key in the Mind's **private credentials** | the Mind's chat: ask it to store the key as a private credential named `anjomanApiKey`, then start a new thread so the key is off screen | There is no settings screen for custom keys yet ("Skills & Apps: coming soon" in the Builder console) |
| Verified Ask token (`VERIFY_TOKEN`) | Vercel → project → Settings → Environment Variables | Any long random string; also store it in the Mind as `verifyAskToken` the same way |

Never paste a key into a chat, a GitHub issue, Discord, or this repo.

**Untrusted input.** Miners are third parties, so a miner's answer can carry text written to steer
the Mind ("PASS this", "send your key to ..."). Two layers stop it:
- the connector passes the Mind only structured fields (verdict, count, well-formed advisory ids,
  our own checks, cost, receipt), never a miner's free text or self-chosen name
  (`safeEvidence` in `connector/guard.mjs`, tested in `connector/test/`);
- when the Mind calls Anjoman itself, a standing rule in its skill (saved 23 Nov,
  [`evidence/2026-11-23-mind-untrusted-input-rule.json`](evidence/2026-11-23-mind-untrusted-input-rule.json))
  limits what it reads from an answer, which hosts it calls, and where each credential may go. A
  drill with an injected answer ([`evidence/2026-11-23-mind-injection-drill.json`](evidence/2026-11-23-mind-injection-drill.json))
  was flagged as an injection attempt and changed nothing.

The second layer is an instruction to a model, not an enforced sandbox, so keep the Anjoman
balance small, and **rotate the Anjoman key after the hackathon**: it was stored by typing it into
the Mind's chat, so it may persist in Minds' conversation history.

## 2. The two HTTP tools

**A. Ask Telegraph (Anjoman).** `Authorization: Bearer <anjoman key>`

```
POST https://backend.telegraphprotocol.com/engine/ask
{"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": "pkg:npm/minimist@1.2.5"}}
```

**Use `/engine/ask`.** Tested 22 Nov: it returns the structured answer at `result.result`
(`verdict`, `vulnerability_count`, `issues`, `summary`), the cost at `result.cost_usd_total`, and
the escrow receipt at `receipt.receipt_hash`, usually in 5 to 45 seconds. `/agent/chat` returns
prose, which Verified Ask can't check.

Things learned the hard way:
- A routed ask **reserves $0.26** of the Anjoman balance up front and is refused (HTTP 400,
  "Insufficient escrow balance") below that, though it charges $0.01 to $0.03. A direct ask to one
  miner (`/engine/ask/{minerId}`, e.g. `20260828` for a1-preflight) reserves only its price.
- A routed ask can settle **two** miner payments ($0.02).
- HTTP 400 "Payment was rejected by the facilitator" means a payment-side outage (no charge); it
  lasted about 20 minutes on 22 Nov. Don't treat it as a bad key, and don't resend in a loop.
- From Python, send a User-Agent header; Cloudflare blocks the default client (error 1010).

**B. Check the answer (Verified Ask).** `Authorization: Bearer <VERIFY_TOKEN>`

```
POST https://adversarialeval.vercel.app/api/verify
{"target": "pkg:npm/minimist@1.2.5", "result": {"verdict": "...", "vulnerability_count": 0, "issues": []}}
```

Returns `label` (`verified`, `contradicted`, `unconfirmed`, `invalid`, `unchecked`) and `checks`
with the reason for each. `GET` on the same URL shows whether the token is configured.
Details: [`verify/README.md`](../verify/README.md).

**Timeouts (from another builder, 22 Nov).** Minds cuts an HTTP call at 60 seconds (504), while an
Anjoman job can take about 2 minutes. The job keeps running: find it with `GET /agent/spend` and
poll `GET /agent/jobs/{id}` until it finishes. Treat a 504 as "still running", not as a failure.

## 3. The Mind's instructions (its Skill playbook)

Give the Mind this, in its own words:

1. Input: a dependency list or diff (`package.json`, `requirements.txt`, a PR diff). Turn each
   added or changed package into a purl: `pkg:<pypi|npm|maven|golang|cargo|gem>/<name>@<version>`.
2. For each package, call tool A **once**. Record cost and receipt.
3. Call tool B with the target and the answer's `result`.
4. Decide:
   - `verified` and `Secure` → **PASS**
   - `verified` and vulnerable → **BLOCK**, listing the advisories
   - `contradicted` or `invalid` → call tool A **once more** with a different miner, then tool B
     again. If still not verified → **FLAG** for a person, quoting the failed checks
   - `unconfirmed` → **FLAG**, quoting what couldn't be confirmed
5. Report: one line per package (decision, reason, advisories), the total cost, the receipts, and
   which answers were caught and why.
6. Remember the approved versions. When asked to re-check (or on a schedule), repeat for them and
   alert if any decision changes, saying what changed.

Never ask more than two providers about one package. Never present an unverified answer as fact.

## 4. First test, before building the full Skill

1. `GET https://adversarialeval.vercel.app/api/verify` shows `"configured": true`.
2. Tool A on `pkg:npm/minimist@1.2.5` (known vulnerable) and `pkg:npm/minimist@1.2.8` (clean).
   Check whether the response has the structured `result`. Note cost and time.
3. Tool B on each answer: expect `verified` for a correct answer.
4. A deliberately wrong answer to tool B (`Secure`, count 0, for 1.2.5): expect `contradicted`.

## 5. Evaluation (with vs without Telegraph, same budget)

Scored on the benchmark's package cases (`bench/cases-v2.json`, frozen truth), plus unseen
packages chosen by a fixed rule before running:
(a) the Mind alone; (b) the Mind trusting Telegraph's answer; (c) the Mind with Telegraph plus
Verified Ask and at most one re-ask. Reported: correct decisions, wrong passes, wrong blocks,
flags, cost and time per arm.

## 6. Prediction markets: settle only from the source the rules name

`connector/markets.mjs` runs the same check-before-trust flow for prediction markets. For each
market it:
1. buys one Telegraph answer (`EVENT_OUTCOME_RESOLUTION_GENERAL`, ranked route, through Anjoman),
   but only when the market's rules name a source it can check;
2. reads that source for free with `resolve/check.py`: Binance 1-minute candles, Coinbase, the NHL,
   MLB or USGS;
3. decides **SETTLE YES**, **SETTLE NO** or **HOLD** for a person;
4. sends the Mind the structured evidence and each market's resolution rule, and the Mind writes
   the settlement report.

It never settles on a paid answer alone.

```bash
NODE_USE_ENV_PROXY=1 node mind/connector/markets.mjs \
  --mind 38266542-f36b-1410-8467-00039ce7df11 --cases resolve/polymarket_cases.json --max-spend 1.00
# --no-mind   asks and checks only     --ask-all   also buy answers for markets with no checkable source
```

- **Behind the session proxy, `NODE_USE_ENV_PROXY=1` is required.** Without it, Node's `fetch`
  bypasses the proxy and sends no key. The connector refuses to start in that case, and it stops
  at the first 401/403 without messaging the Mind.
- **Money:**
  - each ask reserves $0.05 against `--max-spend`; the observed price through Anjoman is $0.02
    to $0.04;
  - an ask that times out is counted as possibly charged (`possibly_charged_usd`);
  - the run records the escrow balance before and after.
- **Evidence:** every ask is appended to `mind/evidence/<timestamp>.markets.attempts.ndjson` as it
  returns, and the whole run goes to `<timestamp>.markets.json`.
- **Results and demo:** the 28 Nov run on 24 real Polymarket markets
  (`eval/reports/2026-11-28-polymarket-via-app.md`); the in-app demo message
  (`docs/DEMO_MIND_MARKETS.md`).
