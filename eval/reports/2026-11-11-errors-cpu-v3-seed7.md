# Error worksheet: `runs/SECURITY_REVIEW-cpu-v3-seed7/scores.json` on `runs/SECURITY_REVIEW-cpu-v3-seed7/security_review.val.jsonl`

24 of 87 pairs ranked wrong. Write **new** training pairs that target each failure; never copy these pairs into training.

| family | wrong / total |
|---|---|
| F1 | 0 / 6 |
| F2 | 15 / 33 |
| F3 | 0 / 3 |
| F4 | 1 / 6 |
| F5 | 1 / 5 |
| F6 | 1 / 5 |
| F7 | 4 / 11 |
| F8 | 0 / 11 |
| F9 | 0 / 3 |
| F10 | 2 / 4 |

## F2: write the same version-range mistake on a different advisory; quote the range in the prompt for half of them

### `GHSA-qr82-2c78-4m8h`: margin -2.652 (chosen − rejected)

**Flaw:** claims 2.5.1 is still affected (fix '2.5.2'); real fix 2.5.1

**Prompt:**

```
Security check before release: tensorflow==2.5.1 in a CLI our support team runs. Is it affected by GHSA-qr82-2c78-4m8h ("Reference binding to nullptr in map operations")?
```

**Chosen (should win):**

```
VERDICT=Secure COUNT=0
not affected: 2.5.1 already contains the fix from 2.5.1. no upgrade is needed for this advisory.
```

**Rejected (won instead):**

```
VERDICT=Insecure COUNT=1
GHSA-qr82-2c78-4m8h / CVE-2021-37671 (high)
affected: 2.5.1 is below the fix (2.5.2) and at or above where the bug was introduced. move to tensorflow 2.5.2+.
```

### `GHSA-m8wh-29wm-52mv`: margin -1.336 (chosen − rejected)

**Flaw:** claims 3.14.1 is patched (fix '3.14.0'); real fix 3.15.0

**Prompt:**

```
Do we need to patch keras for GHSA-m8wh-29wm-52mv (CVE-2026-9335)? requirements.txt pins keras==3.14.1, used in a serverless function. Per the GHSA page, affected versions: 3.13.0 up to but not including 3.15.0.
```

**Chosen (should win):**

```
Verdict: Needs changes. vulnerability_count: 1. Issues: GHSA-m8wh-29wm-52mv / CVE-2026-9335 (moderate). keras 3.14.1 is inside the affected range (3.13.0 up to but not including 3.15.0), so this applies. Upgrade to 3.15.0 or later.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 0. keras 3.14.1 is not in the affected range; the fix shipped in 3.14.0. This alert does not apply to 3.14.1.
```

### `GHSA-ppx5-q359-pvwj`: margin -0.960 (chosen − rejected)

**Flaw:** claims 0.3.10 is patched (fix '0.3.9'); real fix 0.4.0

**Prompt:**

```
Security check before release: vyper==0.3.10 on a partner integration gateway. Is it affected by GHSA-ppx5-q359-pvwj ("vyper's range(start, start + N) reverts for negative numbers")?
```

**Chosen (should win):**

```
Verdict: Needs changes. vulnerability_count: 1. Issues: GHSA-ppx5-q359-pvwj / CVE-2024-32481 (moderate). Affected: 0.3.10 is below the fix (0.4.0) and at or above where the bug was introduced. Move to vyper 0.4.0+.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 0. Not affected: 0.3.10 already contains the fix from 0.3.9. No upgrade is needed for this advisory.
```

### `GHSA-fgv4-6jr3-jgfw`: margin -0.915 (chosen − rejected)

**Flaw:** claims 1.4.38 is still affected (fix '1.4.39'); real fix 1.4.38

**Prompt:**

```
Our scanner flags bentoml==1.4.38 in a CLI our support team runs for GHSA-fgv4-6jr3-jgfw: "BentoML: Command Injection in cloud deployment setup script". True positive or not?
```

**Chosen (should win):**

```
Verdict: Secure. vulnerability_count: 0. Not affected: 1.4.38 already contains the fix from 1.4.38. No upgrade is needed for this advisory.
```

**Rejected (won instead):**

```
Verdict: Insecure. vulnerability_count: 1. Issues: GHSA-fgv4-6jr3-jgfw / CVE-2026-35043 (high). Affected: 1.4.38 is below the fix (1.4.39) and at or above where the bug was introduced. Move to bentoml 1.4.39+.
```

### `GHSA-968f-66r5-5v74`: margin -0.583 (chosen − rejected)

**Flaw:** claims 1.4.1 is patched (fix '1.4.0'); real fix 1.4.2

**Prompt:**

```
Security check before release: waitress==1.4.1 on a partner integration gateway. Is it affected by GHSA-968f-66r5-5v74 (CVE-2019-16789) ("HTTP Request Smuggling in Waitress: Invalid whitespace characters in headers (Follow-up)")? Per the GHSA page, affected versions: before 1.4.2.
```

**Chosen (should win):**

```
VERDICT=Needs changes COUNT=1
GHSA-968f-66r5-5v74 / CVE-2019-16789 (moderate)
waitress 1.4.1 is inside the affected range (before 1.4.2), so this applies. upgrade to 1.4.2 or later.
```

**Rejected (won instead):**

```
VERDICT=Secure COUNT=0
waitress 1.4.1 is not in the affected range; the fix shipped in 1.4.0. this alert does not apply to 1.4.1.
```

### `GHSA-x99w-6fgc-pmfw`: margin -0.532 (chosen − rejected)

**Flaw:** claims 3.10.2 is patched (fix '3.10.1'); real fix 3.10.3

**Prompt:**

```
Security check before release: nltk==3.10.2 in a mobile backend. Is it affected by GHSA-x99w-6fgc-pmfw (CVE-2026-79657) ("NLTK: Allowlisted pickle loaders still permit code execution in current source")? (Scanner detail: vulnerable range is before 3.10.3.)
```

**Chosen (should win):**

```
Verdict: Insecure. vulnerability_count: 1. Issues: GHSA-x99w-6fgc-pmfw / CVE-2026-79657 (critical). nltk 3.10.2 is inside the affected range (before 3.10.3), so this applies. Upgrade to 3.10.3 or later.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 0. nltk 3.10.2 is not in the affected range; the fix shipped in 3.10.1. This alert does not apply to 3.10.2.
```

### `GHSA-9298-4cf8-g4wj`: margin -0.429 (chosen − rejected)

**Flaw:** claims 3.0.1 is still affected (fix '3.0.2'); real fix 3.0.1

**Prompt:**

```
Our scanner flags waitress==3.0.1 on a partner integration gateway for GHSA-9298-4cf8-g4wj (CVE-2024-49768): "Waitress has request processing race condition in HTTP pipelining with invalid first request". True positive or not?
```

**Chosen (should win):**

```
- Verdict: Secure
- vulnerability_count: 0
- waitress 3.0.1 is not in the affected range; the fix shipped in 3.0.1.
- This alert does not apply to 3.0.1.
```

**Rejected (won instead):**

```
- Verdict: Insecure
- vulnerability_count: 1
- Issues: GHSA-9298-4cf8-g4wj / CVE-2024-49768 (critical)
- waitress 3.0.1 is inside the affected range (2.0.0 up to but not including 3.0.2), so this applies.
- Upgrade to 3.0.2 or later.
```

### `GHSA-4f3f-g24h-fr8m`: margin -0.248 (chosen − rejected)

**Flaw:** claims 3.13.2 is still affected (fix '3.14.0'); real fix 3.13.2

**Prompt:**

```
Dependabot raised GHSA-4f3f-g24h-fr8m (CVE-2026-1462) ("Keras has an untrusted deserialization vulnerability") on keras==3.13.2 inside a Docker image we ship to customers. Is the alert valid?
```

**Chosen (should win):**

```
- Verdict: Secure
- vulnerability_count: 0
- Not affected: 3.13.2 already contains the fix from 3.13.2.
- No upgrade is needed for this advisory.
```

**Rejected (won instead):**

```
- Verdict: Insecure
- vulnerability_count: 1
- Issues: GHSA-4f3f-g24h-fr8m / CVE-2026-1462 (high)
- Affected: 3.13.2 is below the fix (3.14.0) and at or above where the bug was introduced.
- Move to keras 3.14.0+.
```

### `GHSA-mq26-g339-26xf`: margin -0.225 (chosen − rejected)

**Flaw:** says the Mercurial issue was fixed in pip 24.0; it was fixed in 23.3

**Prompt:**

```
we do install from hg+https URLs in one build. pip is 23.3.1. still exposed to the Mercurial revision injection?
```

**Chosen (should win):**

```
VERDICT=Secure COUNT=0 (for CVE-2023-5752)
fixed in pip 23.3, so 23.3.1 is outside the range even for hg+ installs. keep the hg revisions pinned to commit hashes.
```

**Rejected (won instead):**

```
VERDICT=Insecure COUNT=1
CVE-2023-5752 / GHSA-mq26-g339-26xf: pip only fixed the Mercurial revision injection in 24.0. 23.3.1 still lets an hg+https revision pass --config options to hg clone, so upgrade pip to 24.0 before the next build.
```

### `GHSA-m5ff-3wj3-8ph4`: margin -0.189 (chosen − rejected)

**Flaw:** claims 1.4.0 is patched (fix '1.3.1'); real fix 1.4.1

**Prompt:**

```
Dependabot raised GHSA-m5ff-3wj3-8ph4 ("HTTP Request Smuggling: Invalid whitespace characters in headers in Waitress") on waitress==1.4.0 in a mobile backend. The advisory text says versions before 1.4.1 are affected. Is the alert valid?
```

**Chosen (should win):**

```
Verdict: Insecure. vulnerability_count: 1. Issues: GHSA-m5ff-3wj3-8ph4 (high). waitress 1.4.0 is inside the affected range (before 1.4.1), so this applies. Upgrade to 1.4.1 or later.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 0. waitress 1.4.0 is not in the affected range; the fix shipped in 1.3.1. This alert does not apply to 1.4.0.
```

### `GHSA-9c47-m6qq-7p4h`: margin -0.168 (chosen − rejected)

**Flaw:** says only json5 2.x is affected; 1.x before 1.0.2 is affected too

**Prompt:**

```
babel toolchain pulls json5 1.0.1 (via tsconfig-paths) and our dev server parses user-uploaded .json5 project files with it. affected?
```

**Chosen (should win):**

```
VERDICT=Needs changes COUNT=1
yes. CVE-2022-46175 covers json5 <1.0.2 as well as 2.0.0 to <2.2.2. with user-uploaded files, __proto__ keys can set the parsed object's prototype. upgrade to 1.0.2+.
```

**Rejected (won instead):**

```
VERDICT=Secure COUNT=0
CVE-2022-46175 / GHSA-9c47-m6qq-7p4h only affects the json5 2.x parser (2.0.0 to <2.2.2); the 1.x line used by tsconfig-paths never had the __proto__ handling bug, so json5 1.0.1 parsing user-uploaded .json5 files is fine.
```

### `GHSA-6643-h7h5-x9wh`: margin -0.106 (chosen − rejected)

**Flaw:** claims 0.0.247 is still affected (fix '0.0.248'); real fix 0.0.247

**Prompt:**

```
Our scanner flags langchain==0.0.247 in a webhook receiver for GHSA-6643-h7h5-x9wh: "Langchain vulnerable to arbitrary code execution". True positive or not?
```

**Chosen (should win):**

```
{"verdict": "Secure", "vulnerability_count": 0, "issues": [], "summary": "The issue was fixed in 0.0.247, and 0.0.247 is at or after that release. Dismiss this alert as not applicable."}
```

**Rejected (won instead):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["GHSA-6643-h7h5-x9wh / CVE-2023-34541 (critical)"], "summary": "The advisory affects langchain before 0.0.248; 0.0.247 falls in that range. The first fixed release on this line is 0.0.248."}
```

### `GHSA-qx2g-xrx7-vfh8`: margin -0.105 (chosen − rejected)

**Flaw:** claims 3.10.0 is patched (fix '3.9.4'); real fix 3.10.1

**Prompt:**

```
Dependabot raised GHSA-qx2g-xrx7-vfh8 ("NLTK TweetTokenizer vulnerable to denial of service through catastrophic regex backtracking") on nltk==3.10.0 in a data pipeline worker. Is the alert valid?
```

**Chosen (should win):**

```
VERDICT=Insecure COUNT=1
GHSA-qx2g-xrx7-vfh8 / CVE-2026-72818 (high)
nltk 3.10.0 is inside the affected range (before 3.10.1), so this applies. upgrade to 3.10.1 or later.
```

**Rejected (won instead):**

```
VERDICT=Secure COUNT=0
nltk 3.10.0 is not in the affected range; the fix shipped in 3.9.4. this alert does not apply to 3.10.0.
```

### `GHSA-655w-fm8m-m478`: margin -0.061 (chosen − rejected)

**Flaw:** claims 0.0.316 is patched (fix '0.0.315'); real fix 0.0.317

**Prompt:**

```
Our scanner flags langchain==0.0.316 in a public REST API for GHSA-655w-fm8m-m478 (CVE-2023-46229): "LangChain Server Side Request Forgery vulnerability". True positive or not?
```

**Chosen (should win):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["GHSA-655w-fm8m-m478 / CVE-2023-46229 (high)"], "summary": "The advisory affects langchain before 0.0.317; 0.0.316 falls in that range. The first fixed release on this line is 0.0.317."}
```

**Rejected (won instead):**

```
{"verdict": "Secure", "vulnerability_count": 0, "issues": [], "summary": "The issue was fixed in 0.0.315, and 0.0.316 is at or after that release. Dismiss this alert as not applicable."}
```

### `GHSA-8hc4-vh64-cxmj`: margin -0.038 (chosen − rejected)

**Flaw:** says only versions before 1.3.2 are affected; the range is 1.3.2 to <1.7.4

**Prompt:**

```
node backend, axios 1.7.2, baseURL http://inventory.internal
const r = await api.get('/' + req.params.sku)
sku is user input. issue?
```

**Chosen (should win):**

```
VERDICT=Insecure COUNT=1
CVE-2024-39338 / GHSA-8hc4-vh64-cxmj (CWE-918): axios 1.3.2 to <1.7.4 can treat a path-relative URL as protocol-relative. a sku of /attacker.example/x makes the path //attacker.example/x, so the request leaves your network. upgrade to 1.7.4 and validate sku as [A-Za-z0-9-]+.
```

**Rejected (won instead):**

```
VERDICT=Secure COUNT=0
the axios path-relative SSRF (CVE-2024-39338) only affected axios before 1.3.2; 1.7.2 resolves '/' + req.params.sku against baseURL http://inventory.internal. no change; maybe trim whitespace in sku.
```

## F4: write a new snippet where one line of context flips the verdict, plus its twin without that line

### `v-code-csrf-bearer-api`: margin -1.535 (chosen − rejected)

**Flaw:** flags CSRF on an API that authenticates only with a bearer header, never cookies

**Prompt:**

```
django rest api, auth only via Authorization: Bearer <token> header (no session or cookie auth enabled). we exempted the API from CSRF middleware. problem? json.
```

**Chosen (should win):**

```
{"verdict": "Secure", "vulnerability_count": 0, "issues": [], "summary": "CSRF needs credentials the browser attaches automatically. a bearer token in a header is not sent cross-site by the browser, so the exemption is fine. keep SessionAuthentication disabled for these views."}
```

**Rejected (won instead):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["CWE-352 CSRF"], "summary": "exempting the django rest api from CSRF middleware lets other sites submit requests. remove the exemption."}
```

## F5: write vulnerable code with a confident, short 'Secure' answer, in another language or framework

### `v-code-java-objectinputstream`: margin -1.566 (chosen − rejected)

**Flaw:** clears native Java deserialization of network input

**Prompt:**

```
java service on port 9000:

ObjectInputStream in = new ObjectInputStream(socket.getInputStream());
Command cmd = (Command) in.readObject();

safe? port is reachable from the office LAN.
```

**Chosen (should win):**

```
VERDICT=Insecure COUNT=1
CWE-502: readObject on network bytes deserialises before the cast, so gadget chains on the classpath can execute code. anyone on the LAN can reach it. use a data format (JSON) or an ObjectInputFilter allow-list.
```

**Rejected (won instead):**

```
VERDICT=Secure COUNT=0
the (Command) cast rejects any object that is not a Command, and the port is LAN-only.
```

## F6: write safe-but-suspicious code where the false alarm is short and confident

### `v-code-xxe-defusedxml`: margin -1.165 (chosen − rejected)

**Flaw:** flags XXE although defusedxml is used

**Prompt:**

```
invoice upload parser:

from defusedxml.ElementTree import fromstring
root = fromstring(request.data)

scanner says XXE. agree?
```

**Chosen (should win):**

```
{"verdict": "Secure", "vulnerability_count": 0, "issues": [], "summary": "defusedxml refuses external entities, DTD tricks and entity expansion bombs by default, which is the standard mitigation for CWE-611. likely a scanner pattern match on 'fromstring'. still cap request size."}
```

**Rejected (won instead):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["CWE-611 XML external entity", "CWE-776 entity expansion"], "summary": "fromstring parses untrusted request bodies with DTD processing, so a <!ENTITY x SYSTEM 'file:///etc/passwd'> declaration is resolved and returned. switch to lxml with resolve_entities=False."}
```

## F7: write a correct answer whose verdict/count fields contradict its own text

### `GHSA-5hq9-5r78-2gjh`: margin -0.848 (chosen − rejected)

**Flaw:** same facts but fields contradict (verdict Secure, count 1)

**Prompt:**

```
Our scanner flags llama-index==0.12.40 in a public REST API for GHSA-5hq9-5r78-2gjh (CVE-2025-6211): "LlamaIndex vulnerable to data loss through hash collisions in its DocugamiReader class". True positive or not?
```

**Chosen (should win):**

```
Verdict: Needs changes. vulnerability_count: 1. Issues: GHSA-5hq9-5r78-2gjh / CVE-2025-6211 (moderate). llama-index 0.12.40 is inside the affected range (before 0.12.41), so this applies. Upgrade to 0.12.41 or later.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 1. Issues: GHSA-5hq9-5r78-2gjh / CVE-2025-6211 (moderate). llama-index 0.12.40 is inside the affected range (before 0.12.41), so this applies. Upgrade to 0.12.41 or later.
```

### `GHSA-rxff-vr5r-8cj5`: margin -0.791 (chosen − rejected)

**Flaw:** same facts but fields contradict (verdict Secure, count 1)

**Prompt:**

```
Dependabot raised GHSA-rxff-vr5r-8cj5 (CVE-2024-42474) ("Path traveral in Streamlit on windows") on streamlit==1.36.0 in a CLI our support team runs. Is the alert valid?
```

**Chosen (should win):**

```
Verdict: Needs changes. vulnerability_count: 1. Issues: GHSA-rxff-vr5r-8cj5 / CVE-2024-42474 (moderate). Affected: 1.36.0 is below the fix (1.37.0) and at or above where the bug was introduced. Move to streamlit 1.37.0+.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 1. Issues: GHSA-rxff-vr5r-8cj5 / CVE-2024-42474 (moderate). Affected: 1.36.0 is below the fix (1.37.0) and at or above where the bug was introduced. Move to streamlit 1.37.0+.
```

### `v-code-ratelimit-fields`: margin -0.762 (chosen − rejected)

**Flaw:** explains the brute-force risk but returns Secure with count 0

**Prompt:**

```
POST /api/otp/verify checks a 6-digit code, no attempt limit, codes valid 10 min. json.
```

**Chosen (should win):**

```
{"verdict": "Needs changes", "vulnerability_count": 1, "issues": ["CWE-307: no attempt limit on OTP"], "summary": "10^6 codes over 10 minutes is brute-forceable. lock after ~5 tries and rate limit per account."}
```

**Rejected (won instead):**

```
{"verdict": "Secure", "vulnerability_count": 0, "issues": ["CWE-307: no attempt limit on OTP"], "summary": "with no attempt limit an attacker can try all 1,000,000 codes within the 10 minute window. add per-account lockout."}
```

### `GHSA-cjc7-49v2-jp64`: margin -0.660 (chosen − rejected)

**Flaw:** same facts but fields contradict (verdict Secure, count 1)

**Prompt:**

```
Security check before release: tensorflow==2.4.1 inside a Docker image we ship to customers. Is it affected by GHSA-cjc7-49v2-jp64 ("Incomplete validation in `SparseAdd`")?
```

**Chosen (should win):**

```
Verdict: Needs changes. vulnerability_count: 1. Issues: GHSA-cjc7-49v2-jp64 / CVE-2021-29609 (moderate). The advisory affects tensorflow 2.4.0 up to but not including 2.4.2; 2.4.1 falls in that range. The first fixed release on this line is 2.4.2.
```

**Rejected (won instead):**

```
Verdict: Secure. vulnerability_count: 1. Issues: GHSA-cjc7-49v2-jp64 / CVE-2021-29609 (moderate). The advisory affects tensorflow 2.4.0 up to but not including 2.4.2; 2.4.1 falls in that range. The first fixed release on this line is 2.4.2.
```

## F10: write a fix that a specific input bypasses

### `v-code-xss-blacklist`: margin -0.334 (chosen − rejected)

**Flaw:** recommends stripping <script> tags, bypassed by event-handler payloads

**Prompt:**

```
php guestbook prints <?= $_POST['msg'] ?> into the page. quick fix?
```

**Chosen (should win):**

```
VERDICT=Insecure COUNT=1
CWE-79 stored XSS. fix: htmlspecialchars($msg, ENT_QUOTES, 'UTF-8') on output; tag-stripping filters are bypassable.
```

**Rejected (won instead):**

```
VERDICT=Insecure COUNT=1
CWE-79 stored XSS in the guestbook. fix: $msg = preg_replace('/<script.*?>.*?<\/script>/is', '', $_POST['msg']) before printing, which removes script blocks and keeps formatting like <b> working.
```

### `GHSA-cx63-2mw6-8hw5`: margin -0.010 (chosen − rejected)

**Flaw:** recommends upgrading to 69.1.1, which is still affected (fixed in 70.0.0)

**Prompt:**

```
internal tool lets users paste a package URL and calls setuptools.package_index.PackageIndex().download(url, tmpdir). setuptools 68.2.2. fix? json.
```

**Chosen (should win):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["CVE-2024-6345 / GHSA-cx63-2mw6-8hw5 (CWE-94)"], "summary": "package_index download functions allow command injection from user URLs before 70.0.0. upgrade to setuptools>=70.0.0 and stop passing user URLs to package_index; download with an http client and an allow-list."}
```

**Rejected (won instead):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["CVE-2024-6345 / GHSA-cx63-2mw6-8hw5 (CWE-94)"], "summary": "package_index download functions allow command injection from user URLs. upgrade setuptools from 68.2.2 to 69.1.1, the release that contains the package_index fix, and keep the existing PackageIndex().download(url, tmpdir) call."}
```

