# Verified Ask

Check a `SECURITY_REVIEW_GENERAL` answer against public data before you act on it.
Results and method: [`eval/reports/2026-11-22-verified-ask.md`](../eval/reports/2026-11-22-verified-ask.md).

## Scope

- **Package questions only**: a purl (`pkg:npm/minimist@1.2.5`), `minimist 1.2.5 (npm)`, or
  `Is minimist version 1.2.5 from npm affected ...?`. Ecosystems: PyPI, npm, Maven, Go,
  crates.io and RubyGems.
- **Code snippets are `unchecked`.** Facts can't settle them; that needs the evaluator model.
- **OSV is the reference.** A real issue that OSV doesn't list yet shows as contradicted, with the
  reason. A cited CVE that OSV doesn't carry is only a warning.

## Labels

| Label | Meaning | What a buyer's code should do |
|---|---|---|
| `verified` | every check ran and passed | act on it |
| `contradicted` | public data says the answer is wrong (reason in `checks`) | reject; don't act |
| `unconfirmed` | nothing failed, but something couldn't be confirmed | treat with care, or ask another miner |
| `invalid` | no usable verdict | reject |
| `unchecked` | not a package question | needs another judge |

**The count.** Miners count aliases differently (one bug can have a GHSA and a PYSEC record), so
by default a `vulnerability_count` that differs from OSV is reported as `info` and doesn't block
`verified`. Send `"strict_count": true` to make a mismatch a warning. The count then has to equal
OSV's records, or its distinct vulnerabilities once aliases are merged.

## Run it

```
python -m verify.server                      # http://127.0.0.1:8402, no token needed on loopback
VERIFY_TOKEN=... python -m verify.server --host 0.0.0.0 --rate 60
curl -s localhost:8402/v1/verify -H "Authorization: Bearer $VERIFY_TOKEN" \
  -d '{"target":"pkg:npm/minimist@1.2.5","result":{"verdict":"Secure","vulnerability_count":0,"issues":[]}}'
```

It makes outbound calls on behalf of its callers, so it is built not to become an open proxy:

- On any address other than loopback it **refuses to start without `VERIFY_TOKEN`**, and then every
  request needs `Authorization: Bearer <token>` (compared in constant time).
- Each client address gets `--rate` requests per minute (default 60), then HTTP 429.
- Bodies over 64 KB get 413. `target` is capped at 256 bytes, the intent's own limit.
- At most 8 upstream calls run at once; responses are cached.
- The cache (`--cache`) is written atomically: a temp file, then a rename.
- Standard library only, no account, no key. Sources: api.osv.dev, api.deps.dev, rubygems.org.

## Replay

```
python -m verify.replay bench/out/round-2 bench/out/round-3 --out bench/out/verify-replay [--offline]
python tests/test_verify.py
```
