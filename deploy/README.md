# deploy/ (Phase 3)

The executor host: a public VM with ≥ 5 GB RAM, Go 1.25+, and `cmd/adapterexec` from the
pinned kit behind Caddy for TLS. Validators refuse private and loopback IPs and don't
follow redirects. Keep it running until the registration is decided (about 1.5 h on testnet).

Planned files: `Caddyfile`, `adapterexec.service` (systemd), `healthcheck.sh`.
