#!/usr/bin/env bash
set -euo pipefail

REPO="https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main"
PY_URL="$REPO/MehTunnel.py"
BIN="/usr/local/bin/mehtunnel"
PY_DST="/opt/mehtunnel/MehTunnel.py"

info() { echo "[*] $*"; }
ok() { echo "[+] $*"; }
err() { echo "[!] $*" >&2; exit 1; }

# Root check
[[ "$(id -u)" -eq 0 ]] || err "Run as root: sudo bash install_mehtunnel.sh"

info "Updating packages..."
apt-get update -y >/dev/null 2>&1 || true
apt-get install -y python3 curl >/dev/null 2>&1 || true

tmp_dir="$(mktemp -d)"
cleanup() { rm -rf "$tmp_dir"; }
trap cleanup EXIT

info "Downloading MehTunnel core..."
curl -fsSL "$PY_URL" -o "$tmp_dir/MehTunnel.py" || err "Download failed"
mkdir -p "$(dirname "$PY_DST")"
install -m 0755 "$tmp_dir/MehTunnel.py" "$PY_DST"

ok "Installing launcher command: $BIN"
cat > "$BIN" <<EOF
#!/usr/bin/env bash
sudo python3 "$PY_DST" "\$@"
EOF
chmod +x "$BIN"

ok "Installation complete! Run with: sudo mehtunnel"
