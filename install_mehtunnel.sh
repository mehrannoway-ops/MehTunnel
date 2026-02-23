#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# MehTunnel Installer v1.0
# -----------------------------

# GitHub URLs
REPO_USER="mehrannoway-ops"
REPO_NAME="MehTunnel"
PY_FILE="MehTunnel.py"
PY_URL="https://raw.githubusercontent.com/${REPO_USER}/${REPO_NAME}/main/${PY_FILE}"

# Installation paths
INSTALL_DIR="/opt/mehtunnel"
PY_DST="${INSTALL_DIR}/${PY_FILE}"
BIN="/usr/local/bin/mehtunnel"

# Colors
CLR_GREEN="\033[32m"; CLR_RED="\033[31m"; CLR_RESET="\033[0m"

# -----------------------------
info() { echo -e "${CLR_GREEN}[*] $*${CLR_RESET}"; }
err() { echo -e "${CLR_RED}[!] $*${CLR_RESET}"; exit 1; }
ok() { echo -e "${CLR_GREEN}[+] $*${CLR_RESET}"; }

# -----------------------------
# Root check
[[ "$EUID" -eq 0 ]] || err "Please run as root: sudo bash install_mehtunnel.sh"

info "Updating package lists..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null 2>&1 || true

info "Installing dependencies..."
apt-get install -y python3 curl >/dev/null 2>&1 || apt-get install -y python3 curl

# -----------------------------
# Prepare directories
info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# -----------------------------
# Download MehTunnel.py
info "Downloading MehTunnel..."
curl -fsSL "$PY_URL" -o "$PY_DST" || err "Failed to download MehTunnel.py"
chmod +x "$PY_DST"

# -----------------------------
# Create launcher script
info "Creating launcher command: mehtunnel"
cat > "$BIN" <<EOF
#!/usr/bin/env bash
# MehTunnel launcher
python3 "$PY_DST"
EOF
chmod +x "$BIN"

# -----------------------------
ok "Installation completed!"
echo ""
echo "Run MehTunnel using:"
echo "sudo mehtunnel"
echo ""
