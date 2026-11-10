# Error worksheet: `runs/SECURITY_REVIEW-cpu-v1/scores.json` on `data/validation/security_review.val.jsonl`

9 of 39 pairs ranked wrong. Write **new** training pairs that target each failure; never copy these pairs into training.

| family | wrong / total |
|---|---|
| F1 | 0 / 1 |
| F2 | 2 / 6 |
| F3 | 0 / 3 |
| F4 | 2 / 6 |
| F5 | 2 / 5 |
| F6 | 2 / 5 |
| F7 | 0 / 2 |
| F8 | 0 / 4 |
| F9 | 0 / 3 |
| F10 | 1 / 4 |

## F2: write the same version-range mistake on a different advisory; quote the range in the prompt for half of them

### `GHSA-8hc4-vh64-cxmj`: margin -1.239 (chosen − rejected)

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

### `GHSA-qwph-4952-7xr6`: margin -0.201 (chosen − rejected)

**Flaw:** flags jsonwebtoken 9.0.2 although the fix shipped in 9.0.0

**Prompt:**

```
audit tool says jsonwebtoken@9.0.2 is affected by the 'none algorithm' bypass. our verify call: jwt.verify(t, pubKey, {algorithms: ['ES256']}). confirm?
```

**Chosen (should win):**

```
{"summary": "false positive. the none-algorithm default bypass (CVE-2022-23540) affects <=8.5.1 and was fixed in 9.0.0; 9.0.2 is patched, and the algorithms allow-list blocks it anyway.", "issues": [], "vulnerability_count": 0, "verdict": "Secure"}
```

**Rejected (won instead):**

```
{"summary": "confirmed. CVE-2022-23540 affects the whole 9.0.x line because 9.0.0 only deprecated the none default; removal came in 9.1.0. upgrade to 9.1.0 and keep the allow-list.", "issues": ["CVE-2022-23540 / GHSA-qwph-4952-7xr6"], "vulnerability_count": 1, "verdict": "Needs changes"}
```

## F4: write a new snippet where one line of context flips the verdict, plus its twin without that line

### `v-code-csrf-bearer-api`: margin -2.798 (chosen − rejected)

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

### `GHSA-grv7-fg5c-xmjg`: margin -1.190 (chosen − rejected)

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

## F5: write vulnerable code with a confident, short 'Secure' answer, in another language or framework

### `v-code-java-objectinputstream`: margin -3.658 (chosen − rejected)

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

### `GHSA-3xgq-45jj-v275`: margin -0.128 (chosen − rejected)

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

### `v-code-xxe-defusedxml`: margin -1.814 (chosen − rejected)

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

### `v-code-regex-dos-email`: margin -0.374 (chosen − rejected)

**Flaw:** flags a linear, anchored regex as ReDoS

**Prompt:**

```
go email check: var re = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[a-z]{2,}$`)
re.MatchString(input) on signup. redos risk?
```

**Chosen (should win):**

```
VERDICT=Secure COUNT=0
Go's regexp package is RE2-based and runs in linear time, so catastrophic backtracking (CWE-1333) is not possible whatever the pattern. fine; maybe cap input length to 254.
```

**Rejected (won instead):**

```
VERDICT=Needs changes COUNT=1
CWE-1333 ReDoS (medium): the two [^@\s]+ groups around @ can backtrack against each other on long inputs without an @, so a 50k-character signup value can stall the request goroutine. rewrite with possessive quantifiers.
```

## F10: write a fix that a specific input bypasses

### `v-code-xss-blacklist`: margin -0.345 (chosen − rejected)

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

