#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# MehTunnel Installer vFinal
# -----------------------------

REPO_USER="mehrannoway-ops"
REPO_NAME="MehTunnel"
PY_FILE="MehTunnel.py"
PY_URL="https://raw.githubusercontent.com/${REPO_USER}/${REPO_NAME}/main/${PY_FILE}"

INSTALL_DIR="/opt/mehtunnel"
PY_DST="${INSTALL_DIR}/${PY_FILE}"
BIN="/usr/local/bin/mehtunnel"

# Colors
CLR_GREEN="\033[32m"; CLR_RED="\033[31m"; CLR_RESET="\033[0m"
info() { echo -e "${CLR_GREEN}[*] $*${CLR_RESET}"; }
err() { echo -e "${CLR_RED}[!] $*${CLR_RESET}"; exit 1; }
ok() { echo -e "${CLR_GREEN}[+] $*${CLR_RESET}"; }

# -----------------------------
[[ "$EUID" -eq 0 ]] || err "Please run as root: sudo bash install_mehtunnel.sh"

info "Updating package lists..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null 2>&1 || true

info "Installing dependencies..."
apt-get install -y python3 curl >/dev/null 2>&1 || apt-get install -y python3 curl

# -----------------------------
info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

info "Downloading MehTunnel..."
curl -fsSL "$PY_URL" -o "$PY_DST" || err "Failed to download MehTunnel.py"
chmod +x "$PY_DST"

# -----------------------------
info "Creating launcher command: mehtunnel"
cat > "$BIN" <<EOF
#!/usr/bin/env bash
python3 "$PY_DST" "\$@"
EOF
chmod +x "$BIN"

# -----------------------------
# Ask user for IR/EU IPs and ports
echo ""
echo "=== MehTunnel Service Setup ==="
read -p "Enter IR server Bridge port [4444]: " IR_BRIDGE
IR_BRIDGE=${IR_BRIDGE:-4444}
read -p "Enter IR server Sync port [5555]: " IR_SYNC
IR_SYNC=${IR_SYNC:-5555}
read -p "Enter IR Manual ports CSV (80,443,...): " IR_PORTS
IR_PORTS=${IR_PORTS:-443}

read -p "Enter EU server IP (Iran IP): " EU_IP
read -p "Enter EU server Bridge port [4444]: " EU_BRIDGE
EU_BRIDGE=${EU_BRIDGE:-4444}
read -p "Enter EU server Sync port [5555]: " EU_SYNC
EU_SYNC=${EU_SYNC:-5555}

# -----------------------------
info "Creating systemd service for IR..."
cat > /etc/systemd/system/mehtunnel-ir.service <<EOF
[Unit]
Description=MehTunnel IR Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $PY_DST IR $IR_BRIDGE $IR_SYNC 115 n $IR_PORTS
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

info "Creating systemd service for EU..."
cat > /etc/systemd/system/mehtunnel-eu.service <<EOF
[Unit]
Description=MehTunnel EU Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $PY_DST EU $EU_IP $EU_BRIDGE $EU_SYNC
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# -----------------------------
info "Reloading systemd..."
systemctl daemon-reload

info "Enabling and starting services..."
systemctl enable mehtunnel-ir --now
systemctl enable mehtunnel-eu --now

ok "Installation and service setup complete!"
echo ""
echo "✅ MehTunnel IR and EU services are running."
echo "Use the following commands to view logs:"
echo "  sudo journalctl -u mehtunnel-ir -f"
echo "  sudo journalctl -u mehtunnel-eu -f"
echo ""
echo "The tunnels will remain active even if you close the terminal."
