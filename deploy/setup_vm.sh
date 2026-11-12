#!/usr/bin/env bash
# One-time executor setup on a fresh Ubuntu/Debian VM (>= 5 GB RAM, ports 80/443 open).
#   sudo EXEC_HOST=203-0-113-7.sslip.io bash deploy/setup_vm.sh
# Run from /opt/adversarialeval (a clone of the repo at the commit that holds the package).
set -euo pipefail
: "${EXEC_HOST:?set EXEC_HOST to the public hostname, e.g. <ip-with-dashes>.sslip.io}"
ROOT=/opt/adversarialeval
cd "$ROOT"
GO_VERSION=${GO_VERSION:-1.25.7}

apt-get update -y
apt-get install -y git curl python3 debian-keyring debian-archive-keyring apt-transport-https gpg
if ! command -v go >/dev/null || ! go version | grep -q "go1.2[5-9]"; then
  curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-$(dpkg --print-architecture).tar.gz" | tar -C /usr/local -xz
fi
export PATH=/usr/local/go/bin:$PATH
if ! command -v caddy >/dev/null; then   # official Caddy apt repository (caddyserver.com/docs/install)
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y && apt-get install -y caddy
fi

bash scripts/setup_kit.sh --full            # kit at the pinned SHA + foundation graph, engine, tokenizer (hash-checked)
(cd third_party/telegraph-wasm-baseline && go build -o "$ROOT/runs/bin/adapterexec" ./cmd/adapterexec)
(cd tools/remotecheck && go build -o "$ROOT/runs/bin/remotecheck" .)
test -f adapters/SECURITY_REVIEW.safetensors || { echo "commit the exported package to adapters/ first"; exit 1; }

id adapterexec >/dev/null 2>&1 || useradd --system --no-create-home adapterexec
install -m 0644 deploy/adapterexec.env.example /etc/adapterexec.env
install -m 0644 deploy/adapterexec.service /etc/systemd/system/adapterexec.service
install -m 0644 deploy/Caddyfile /etc/caddy/Caddyfile
mkdir -p /etc/systemd/system/caddy.service.d
printf '[Service]\nEnvironment=EXEC_HOST=%s\n' "$EXEC_HOST" > /etc/systemd/system/caddy.service.d/host.conf
systemctl daemon-reload
systemctl enable --now adapterexec
systemctl restart caddy
echo "executor: https://$EXEC_HOST/  (check: bash deploy/healthcheck.sh https://$EXEC_HOST/)"
