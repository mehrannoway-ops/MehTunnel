#!/usr/bin/env bash
set -euo pipefail

REPO="https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main"
BIN="/usr/local/bin/mehtunnel"
PY_DST="/opt/mehtunnel/MehTunnel.py"

info(){ echo "[*] $*"; }
ok(){ echo "[+] $*"; }
err(){ echo "[!] $*"; exit 1; }

# root check
[[ "$(id -u)" == "0" ]] || err "Run as root: sudo bash install_mehtunnel.sh"

export DEBIAN_FRONTEND=noninteractive

info "Updating package lists..."
apt-get update -y >/dev/null 2>&1 || apt-get update >/dev/null 2>&1

# Install dependencies
DEPS=(python3 screen curl iproute2 ca-certificates)
info "Installing dependencies..."
apt-get install -y "${DEPS[@]}" >/dev/null 2>&1 || apt-get install -y "${DEPS[@]}"

tmpdir=$(mktemp -d)
cleanup(){ rm -rf "$tmpdir"; }
trap cleanup EXIT

info "Downloading MehTunnel manager..."
curl -fsSL "$REPO/install_mehtunnel.sh" -o "$tmpdir/mehtunnel.sh" || err "Failed to download manager"

info "Downloading MehTunnel core..."
curl -fsSL "$REPO/MehTunnel.py" -o "$tmpdir/MehTunnel.py" || err "Failed to download core"

[[ -s "$tmpdir/mehtunnel.sh" ]] || err "Manager download is empty"
[[ -s "$tmpdir/MehTunnel.py" ]] || err "Core download is empty"

install -m 0755 "$tmpdir/mehtunnel.sh" "$BIN"
mkdir -p "$(dirname "$PY_DST")"
install -m 0755 "$tmpdir/MehTunnel.py" "$PY_DST"

echo ""
ok "Installation completed!"
echo "Run MehTunnel with:"
echo "sudo mehtunnel"
