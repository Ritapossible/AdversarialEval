# deploy/: the executor host

The executor is the public HTTPS endpoint registered as `wasmRunnableUrl`. Validators send it
15 public pairs before downloading the package, then re-score the same texts and demand
bit-identical results. So it must run the kit's `adapterexec` on the real foundation, engine
and the **exact registered package bytes**.

| File | What |
|---|---|
| `setup_vm.sh` | One-time setup on Ubuntu/Debian: Go, Caddy, kit + foundation, builds, services |
| `adapterexec.service` | systemd unit (loopback :8080, restarts, read-only filesystem) |
| `adapterexec.env.example` | Paths and public hashes → `/etc/adapterexec.env` |
| `Caddyfile` | TLS via Let's Encrypt on `EXEC_HOST` (e.g. `<ip-with-dashes>.sslip.io`) |
| `healthcheck.sh` | Calls the public URL with the node's own client, SSRF guard on, like a validator |

Requirements: a public IPv4, ≥ 5 GB RAM, ports 80 and 443 open, and the exported package
committed at `adapters/SECURITY_REVIEW.safetensors` together with its `.manifest.json`.
Validators refuse private and loopback addresses and don't follow redirects. Keep it running
until the registration is decided (about 1.5 h on testnet), and while the adapter is Canonical.

The components were tested locally (`scripts/rehearse.sh`). These deploy files haven't run on
a real VM yet, so the first run of `setup_vm.sh` is where to look if something breaks.
