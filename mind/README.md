# Dependency Guard Mind: setup

A Mind (hellominds.ai) that checks a project's dependency changes for known vulnerabilities. It
buys **one** Telegraph `SECURITY_REVIEW_GENERAL` answer per package through Anjoman, checks that
answer **free** with Verified Ask, and then passes, blocks or flags each package with its evidence,
cost and receipt. It re-asks a different provider only when Verified Ask proves an answer wrong.

Route: the Minds **HTTP tool**, as confirmed by Telegraph on 22 Nov (no Bazaar listing needed).

## 1. Accounts and secrets (owner)

| Step | Where | Notes |
|---|---|---|
| Minds account and a Mind named "Dependency Guard" | hellominds.ai | Record the **Mind ID** for the submission |
| Anjoman API key (`anjoman_...`) | anjoman.ai → dashboard → API keys | 30 requests per minute per key |
| Fund the Anjoman balance | anjoman.ai → dashboard → faucet / wallet | Testnet USDC; a failed job isn't charged |
| Save the Anjoman key in the Mind's **private credentials** | Minds | Never in chat, the repo, or a prompt |
| Verified Ask token (`VERIFY_TOKEN`) | Vercel → project → Settings → Environment Variables | Any long random string; also save it in the Mind's private credentials |

Never paste a key into a chat, a GitHub issue, Discord, or this repo.

## 2. The two HTTP tools

**A. Ask Telegraph (Anjoman).** `Authorization: Bearer <anjoman key>`

```
POST https://backend.telegraphprotocol.com/engine/ask
{"intent": "SECURITY_REVIEW_GENERAL", "params": {"target": "pkg:npm/minimist@1.2.5"}}
```

`/engine/ask` is listed as returning the miner's result and a receipt. `/agent/chat` (with
`"stream": false`, and `intent` + `params`) returns `answer`, `status`, `costUsd` and a `jobId`;
for long jobs, poll `GET /agent/jobs/{id}`. **First test (step 4) decides which one we use:**
Verified Ask needs the structured `result` (`verdict`, `vulnerability_count`, `issues`), not prose.

**B. Check the answer (Verified Ask).** `Authorization: Bearer <VERIFY_TOKEN>`

```
POST https://adversarialeval.vercel.app/api/verify
{"target": "pkg:npm/minimist@1.2.5", "result": {"verdict": "...", "vulnerability_count": 0, "issues": []}}
```

Returns `label` (`verified`, `contradicted`, `unconfirmed`, `invalid`, `unchecked`) and `checks`
with the reason for each. `GET` on the same URL shows whether the token is configured.
Details: [`verify/README.md`](../verify/README.md).

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
