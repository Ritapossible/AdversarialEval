import json
C=[]
def add(id_,cwe,lang,aff,code,why,kind="pair"):
    C.append({"id":id_,"kind":kind,"cwe":cwe,"language":lang,"truth":{"affected":aff},"target":f"{lang}:\n{code}","rationale":why,"source_url":f"https://cwe.mitre.org/data/definitions/{cwe.split('-')[1]}.html"})
# 1 path traversal: prefix check bypass
add("path-prefix-vulnerable","CWE-22","Python",True,
'BASE = "/srv/files"\ndef read(name):\n    p = os.path.abspath(os.path.join(BASE, name))\n    if not p.startswith(BASE):\n        abort(403)\n    return open(p).read()',
"startswith on a path without a trailing separator: ../files_secret/x resolves to /srv/files_secret/x, which passes; abspath doesn't resolve symlinks either")
add("path-prefix-fixed","CWE-22","Python",False,
'BASE = "/srv/files"\ndef read(name):\n    p = os.path.realpath(os.path.join(BASE, name))\n    if os.path.commonpath([p, BASE]) != BASE:\n        abort(403)\n    return open(p).read()',
"realpath resolves .. and symlinks; commonpath compares whole path components, so only paths inside BASE pass")
# 2 argument injection
add("git-argv-vulnerable","CWE-88","Python",True,
'def last_commit(ref):\n    # ref comes from the query string\n    r = subprocess.run(["git", "-C", REPO, "log", "-n1", ref], capture_output=True, text=True)\n    return r.stdout',
"no shell, but ref can be an option: --output=/var/www/x.php makes git log write a file of the attacker's choosing")
add("git-argv-fixed","CWE-88","Python",False,
'def last_commit(ref):\n    # ref comes from the query string\n    r = subprocess.run(["git", "-C", REPO, "log", "-n1", "--end-of-options", ref], capture_output=True, text=True)\n    return r.stdout',
"--end-of-options (git 2.24+) makes ref a revision, never an option; reading any revision of this repo is intended")
# 3 open redirect
add("redirect-vulnerable","CWE-601","Python/Flask",True,
'@app.get("/login/done")\ndef done():\n    nxt = request.args.get("next", "/")\n    if not nxt.startswith("/"):\n        nxt = "/"\n    return redirect(nxt)',
"//evil.example starts with '/' but browsers treat it as a scheme-relative URL to another host")
add("redirect-fixed","CWE-601","Python/Flask",False,
'@app.get("/login/done")\ndef done():\n    nxt = request.args.get("next", "/")\n    if not re.fullmatch(r"/(?!/)[\\w\\-./?=&%]*", nxt):\n        nxt = "/"\n    return redirect(nxt)',
"only a single leading slash followed by path-safe characters passes: no '//', backslash, tab or other control characters, so the browser can't read it as another host")
# 4 ReDoS
add("regex-vulnerable","CWE-1333","Python",True,
'def is_staff(email):\n    # email comes from a public sign-up form\n    return re.fullmatch(r"(\\w+\\s?)+@example\\.com", email) is not None',
"nested quantifier (\\w+\\s?)+ backtracks exponentially on input like 'aaaa...a!'")
add("regex-fixed","CWE-1333","Python",False,
'def is_staff(email):\n    # email comes from a public sign-up form\n    return re.fullmatch(r"[\\w.+-]+@example\\.com", email) is not None',
"single character class with one quantifier: linear-time matching")
# 5 prototype pollution
add("merge-vulnerable","CWE-1321","Node.js",True,
'function merge(t, s) {\n  for (const k in s)\n    if (s[k] && typeof s[k] === "object") merge(t[k] ??= {}, s[k]);\n    else t[k] = s[k];\n}\nmerge(settings, JSON.parse(req.body));',
"JSON.parse makes __proto__ an own key; merge then writes through Object.prototype")
add("merge-fixed","CWE-1321","Node.js",False,
'function merge(t, s) {\n for (const k of Object.keys(s)) {\n  if (k === "__proto__") continue;\n  const v = s[k];\n  if (v && typeof v == "object") merge(Object.hasOwn(t,k) ? t[k] : (t[k] = {}), v);\n  else t[k] = v;\n }\n}',
"__proto__ is skipped and recursion only enters the target's own properties, so inherited objects (Object.prototype, Object.prototype.toString) are never written; constructor/prototype keys just become plain own properties")
# 6 tar slip
add("untar-vulnerable","CWE-22","Python 3.11",True,
'def unpack(upload, dest):\n    # upload is a user-supplied .tar file\n    with tarfile.open(fileobj=upload) as t:\n        t.extractall(dest)',
"tarfile.extractall without a filter follows ../ and absolute member names and links (CVE-2007-4559)")
add("untar-fixed","CWE-22","Python 3.12",False,
'def unpack(upload, dest):\n    # upload is a user-supplied .tar file\n    with tarfile.open(fileobj=upload) as t:\n        t.extractall(dest, filter="data")',
"the 'data' extraction filter rejects absolute paths, .. components, links outside dest and special files")
# 7 mass assignment
add("profile-vulnerable","CWE-915","Python/Flask",True,
'# User columns: id, name, email, is_admin\n@app.patch("/me")\ndef update_me():\n    for k, v in request.json.items():\n        setattr(current_user, k, v)\n    db.session.commit()',
"every key in the request body is written, so a user can set is_admin")
add("profile-fixed","CWE-915","Python/Flask",False,
'# User columns: id, name, email, is_admin\n@app.patch("/me")\ndef update_me():\n    d = request.json\n    current_user.name = d.get("name", current_user.name)\n    db.session.commit()',
"only name can change")
# 8 timing
add("token-compare-vulnerable","CWE-208","Python",True,
'def check(request):\n    sent = request.headers.get("X-Api-Token", "")\n    return sent == os.environ["API_TOKEN"]',
"== returns at the first differing byte, leaking how much of the token matched")
add("token-compare-fixed","CWE-208","Python",False,
'def check(request):\n    sent = request.headers.get("X-Api-Token", "")\n    return hmac.compare_digest(sent, os.environ["API_TOKEN"])',
"constant-time comparison")
# 9 randomness
add("reset-token-vulnerable","CWE-338","Python",True,
'def reset_token():\n    alphabet = string.ascii_letters + string.digits\n    return "".join(random.choice(alphabet) for _ in range(32))',
"random is a Mersenne Twister PRNG; its outputs are predictable, unfit for password-reset tokens")
add("reset-token-fixed","CWE-338","Python",False,
'def reset_token():\n    return secrets.token_urlsafe(32)',
"secrets uses the OS CSPRNG")
# 10 ORDER BY injection
add("orderby-vulnerable","CWE-89","Python",True,
'def users(sort):\n    if not any(c in sort for c in ("name", "email")):\n        sort = "name"\n    return db.execute(f"SELECT id, name FROM users ORDER BY {sort}")',
"the check only requires 'name' or 'email' somewhere in the string: 'name; DROP TABLE users' passes")
add("orderby-fixed","CWE-89","Python",False,
'def users(sort):\n    col = {"name": "name", "email": "email"}.get(sort, "name")\n    return db.execute(f"SELECT id, name FROM users ORDER BY {col}")',
"only the two literal column names can reach the query")
# decoys: safe code that looks risky
add("decoy-orderby-allowlist","CWE-89","Python",False,
'def users(sort):\n    if sort.lower() not in ("name", "email"):\n        sort = "name"\n    return db.execute(f"SELECT id, name FROM users ORDER BY {sort}")',
"f-string SQL, but sort can only be name or email in some letter case, which SQL treats as the same column","decoy")
add("decoy-shell-constant","CWE-78","Python",False,
'def disk_report():\n    # no user input reaches this function\n    out = subprocess.run("df -h /var", shell=True, capture_output=True, text=True)\n    return out.stdout',
"shell=True with a constant command and no input","decoy")
add("decoy-md5-etag","CWE-328","Python/Flask",False,
'@app.get("/static/<path:name>")\ndef asset(name):\n    data = files.read(name)  # trusted build artifacts\n    etag = hashlib.md5(data).hexdigest()  # cache validator only\n    return Response(data, headers={"ETag": etag})',
"MD5 as an HTTP cache validator has no security role; collisions only cause a stale cache","decoy")
for c in C:
    n=len(c["target"].encode())
    assert n<=256,(c["id"],n)
json.dump({"name":"code-review-v2","frozen":"before any paid call; see RULE.md","cases":C},open("mind/code-test-v2/cases.json","w"),indent=1)
print(len(C),"cases; max bytes",max(len(c["target"].encode()) for c in C),"affected",sum(c["truth"]["affected"] for c in C))
