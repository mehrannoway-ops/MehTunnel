#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# MehTunnel Installer v2.0 (Clean Install)
# -----------------------------

REPO_USER="mehrannoway-ops"
REPO_NAME="MehTunnel"
PY_FILE="MehTunnel.py"
PY_URL="https://raw.githubusercontent.com/${REPO_USER}/${REPO_NAME}/main/${PY_FILE}"

INSTALL_DIR="/opt/mehtunnel"
PY_DST="${INSTALL_DIR}/${PY_FILE}"
BIN="/usr/local/bin/mehtunnel"

CLR_GREEN="\033[32m"; CLR_RED="\033[31m"; CLR_RESET="\033[0m"

info() { echo -e "${CLR_GREEN}[*] $*${CLR_RESET}"; }
err() { echo -e "${CLR_RED}[!] $*${CLR_RESET}"; exit 1; }
ok() { echo -e "${CLR_GREEN}[+] $*${CLR_RESET}"; }

# -----------------------------
[[ "$EUID" -eq 0 ]] || err "Please run as root: sudo bash install_mehtunnel.sh"

info "Cleaning previous MehTunnel installation..."
sudo systemctl stop mehtunnel-ir 2>/dev/null || true
sudo systemctl disable mehtunnel-ir 2>/dev/null || true
sudo rm -f /etc/systemd/system/mehtunnel-ir.service 2>/dev/null || true

sudo systemctl stop mehtunnel-eu 2>/dev/null || true
sudo systemctl disable mehtunnel-eu 2>/dev/null || true
sudo rm -f /etc/systemd/system/mehtunnel-eu.service 2>/dev/null || true

sudo rm -rf "$INSTALL_DIR" 2>/dev/null || true
sudo rm -f "$BIN" 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl reset-failed

# -----------------------------
info "Updating package lists..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null 2>&1 || true

info "Installing dependencies..."
apt-get install -y python3 curl >/dev/null 2>&1 || apt-get install -y python3 curl

# -----------------------------
info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# -----------------------------
info "Downloading MehTunnel..."
curl -fsSL "$PY_URL" -o "$PY_DST" || err "Failed to download MehTunnel.py"
chmod +x "$PY_DST"

# -----------------------------
info "Creating launcher command: mehtunnel"
cat > "$BIN" <<EOF
#!/usr/bin/env bash
python3 "$PY_DST"
EOF
chmod +x "$BIN"

ok "Installation completed!"
echo ""
echo "Run MehTunnel using:"
echo "sudo mehtunnel"
echo ""
