# Error worksheet: `runs/SECURITY_REVIEW-cpu-v2/scores.json` on `runs/SECURITY_REVIEW-cpu-v2/security_review.val.jsonl`

22 of 87 pairs ranked wrong. Write **new** training pairs that target each failure; never copy these pairs into training.

| family | wrong / total |
|---|---|
| F1 | 2 / 6 |
| F2 | 9 / 33 |
| F3 | 0 / 3 |
| F4 | 2 / 6 |
| F5 | 2 / 5 |
| F6 | 2 / 5 |
| F7 | 3 / 11 |
| F8 | 1 / 11 |
| F9 | 0 / 3 |
| F10 | 1 / 4 |

## F1: write a real-looking but wrong advisory id for the same bug class, in a new package

### `GHSA-7gfq-f96f-g85j`: margin -0.247 (chosen − rejected)

**Flaw:** cites GHSA-h6jh-7gv5-28vg (tensorflow), a real advisory for a different package

**Prompt:**

```
Compliance wants the exact GHSA id for langchain: "langchain vulnerable to arbitrary code execution". Our requirements.txt has langchain==0.0.311; the service runs inside a Docker image we ship to customers.
```

**Chosen (should win):**

```
VERDICT=Insecure COUNT=1
GHSA-7gfq-f96f-g85j / CVE-2023-36281 (critical)
langchain 0.0.311 is inside the affected range (before 0.0.312), so this applies. upgrade to 0.0.312 or later.
```

**Rejected (won instead):**

```
VERDICT=Insecure COUNT=1
GHSA-h6jh-7gv5-28vg / CVE-2021-37646 (critical)
langchain 0.0.311 is inside the affected range (before 0.0.312), so this applies. upgrade to 0.0.312 or later.
```

### `GHSA-jm6w-m3j8-898g`: margin -0.151 (chosen − rejected)

**Flaw:** cites GHSA-26c4-7vv6-867j (keras), a real advisory for a different package

**Prompt:**

```
For our audit ticket: which GitHub advisory covers "Unauthenticated remote shutdown in nltk.app.wordnet_app" in nltk? We run nltk==3.9.3 inside a Docker image we ship to customers.
```

**Chosen (should win):**

```
Verdict: Insecure. vulnerability_count: 1. Issues: GHSA-jm6w-m3j8-898g / CVE-2026-33231 (high). Affected: 3.9.3 is below the fix (3.9.4) and at or above where the bug was introduced. Move to nltk 3.9.4+.
```

**Rejected (won instead):**

```
Verdict: Insecure. vulnerability_count: 1. Issues: GHSA-26c4-7vv6-867j / CVE-2026-12480 (high). Affected: 3.9.3 is below the fix (3.9.4) and at or above where the bug was introduced. Move to nltk 3.9.4+.
```

## F2: write the same version-range mistake on a different advisory; quote the range in the prompt for half of them

### `GHSA-qr82-2c78-4m8h`: margin -3.393 (chosen − rejected)

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

### `GHSA-qx2g-xrx7-vfh8`: margin -1.739 (chosen − rejected)

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

### `GHSA-9c47-m6qq-7p4h`: margin -1.668 (chosen − rejected)

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

### `GHSA-fgv4-6jr3-jgfw`: margin -1.664 (chosen − rejected)

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

### `GHSA-ppx5-q359-pvwj`: margin -1.625 (chosen − rejected)

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

### `GHSA-655w-fm8m-m478`: margin -0.927 (chosen − rejected)

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

### `GHSA-9298-4cf8-g4wj`: margin -0.844 (chosen − rejected)

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

### `GHSA-4f3f-g24h-fr8m`: margin -0.276 (chosen − rejected)

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

### `GHSA-x99w-6fgc-pmfw`: margin -0.033 (chosen − rejected)

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

## F4: write a new snippet where one line of context flips the verdict, plus its twin without that line

### `GHSA-grv7-fg5c-xmjg`: margin -2.002 (chosen − rejected)

**Flaw:** treats a build-only transitive dependency with no attacker input as exploitable

**Prompt:**

```
npm audit: braces 3.0.2 (high). path: webpack-dev-server > chokidar > braces, devDependencies only; prod image built with npm ci --omit=dev. patterns are our own globs. release blocker?
```

**Chosen (should win):**

```
VERDICT=Secure COUNT=0 (prod)
CVE-2024-4068 / GHSA-grv7-fg5c-xmjg (braces <3.0.3, resource exhaustion) needs attacker-supplied patterns. here only your own globs reach it, during local dev, and it is not in the prod image. not a blocker; update the dev tree.
```

**Rejected (won instead):**

```
VERDICT=Insecure COUNT=1
braces 3.0.2 < 3.0.3, so CVE-2024-4068 applies through webpack-dev-server > chokidar > braces. high severity findings block releases; add an npm override for braces@3.0.3 and rerun npm audit before shipping.
```

### `v-code-csrf-bearer-api`: margin -0.071 (chosen − rejected)

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

### `v-code-java-objectinputstream`: margin -2.831 (chosen − rejected)

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

### `GHSA-3xgq-45jj-v275`: margin -0.789 (chosen − rejected)

**Flaw:** clears a ReDoS-prone cross-spawn version that receives user-controlled arguments

**Prompt:**

```
CI runner: crossSpawn('git', ['checkout', branchName]) where branchName comes from webhook payloads. cross-spawn 7.0.3. ok?
```

**Chosen (should win):**

```
VERDICT=Needs changes COUNT=1
CVE-2024-21538 / GHSA-3xgq-45jj-v275: ReDoS in cross-spawn <7.0.5 on crafted large strings, and branchName is attacker-influenced. upgrade to 7.0.5, cap length and validate branch names (git check-ref-format).
```

**Rejected (won instead):**

```
VERDICT=Secure COUNT=0
cross-spawn does not use a shell, so branchName from the webhook payload cannot inject commands into crossSpawn('git', ['checkout', branchName]). 7.0.3 is fine.
```

## F6: write safe-but-suspicious code where the false alarm is short and confident

### `v-code-xxe-defusedxml`: margin -4.073 (chosen − rejected)

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

### `v-code-go-html-template`: margin -0.985 (chosen − rejected)

**Flaw:** ignores Go html/template's contextual auto-escaping

**Prompt:**

```
go handler:

var t = template.Must(template.New("p").Parse(`<p>{{.Name}}</p><a href="/u?id={{.ID}}">x</a>`))
t.Execute(w, user)

package is html/template. user.Name is free text. xss?
```

**Chosen (should win):**

```
VERDICT=Secure COUNT=0
html/template escapes contextually: .Name is HTML-escaped in the body, and .ID is URL-escaped inside the href query. no CWE-79 here. do not swap to text/template or wrap values in template.HTML.
```

**Rejected (won instead):**

```
VERDICT=Insecure COUNT=1
CWE-79: user.Name is free text and is rendered straight into <p>{{.Name}}</p> by t.Execute(w, user), so a name with <script> runs in the page. escape .Name with html.EscapeString before Execute.
```

## F7: write a correct answer whose verdict/count fields contradict its own text

### `GHSA-rxff-vr5r-8cj5`: margin -1.091 (chosen − rejected)

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

### `GHSA-5hq9-5r78-2gjh`: margin -0.880 (chosen − rejected)

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

### `GHSA-cjc7-49v2-jp64`: margin -0.618 (chosen − rejected)

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

## F8: write the right finding with the severity off by two levels

### `GHSA-7fh5-64p2-3v2j`: margin -0.688 (chosen − rejected)

**Flaw:** inflates a moderate output-injection parsing bug to critical RCE

**Prompt:**

```
css lint-as-a-service parses user CSS with postcss 8.4.27 and returns the stringified result. scanner: CVE-2023-44270. severity? json.
```

**Chosen (should win):**

```
{"verdict": "Needs changes", "vulnerability_count": 1, "issues": ["CVE-2023-44270 / GHSA-7fh5-64p2-3v2j (CWE-74, moderate)"], "summary": "postcss <8.4.31 mishandles \\r in comments, so crafted CSS can smuggle content into the output that a later consumer treats as real rules. upgrade to 8.4.31."}
```

**Rejected (won instead):**

```
{"verdict": "Insecure", "vulnerability_count": 1, "issues": ["CVE-2023-44270 / GHSA-7fh5-64p2-3v2j (CWE-94, critical)"], "summary": "the postcss parser executes injected code from user CSS, giving remote code execution on the lint service. take the lint-as-a-service endpoint offline until postcss 8.4.27 is replaced."}
```

## F10: write a fix that a specific input bypasses

### `GHSA-cx63-2mw6-8hw5`: margin -0.039 (chosen − rejected)

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

