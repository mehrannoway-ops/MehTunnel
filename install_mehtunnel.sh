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

CLR_GREEN="\033[32m"; CLR_RED="\033[31m"; CLR_RESET="\033[0m"

info() { echo -e "${CLR_GREEN}[*] $*${CLR_RESET}"; }
err() { echo -e "${CLR_RED}[!] $*${CLR_RESET}"; exit 1; }
ok() { echo -e "${CLR_GREEN}[+] $*${CLR_RESET}"; }

[[ "$EUID" -eq 0 ]] || err "Please run as root: sudo bash install_mehtunnel.sh"

info "Updating package lists..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null 2>&1 || true

info "Installing dependencies..."
apt-get install -y python3 curl >/dev/null 2>&1 || apt-get install -y python3 curl

info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

info "Downloading MehTunnel.py..."
curl -fsSL "$PY_URL" -o "$PY_DST" || err "Failed to download MehTunnel.py"
chmod +x "$PY_DST"

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

# -----------------------------
# Prompt user for IR/EU setup
echo "================================"
echo "        MehTunnel Manager"
echo "================================"
read -rp "Select mode (1=EU,2=IR): " MODE

if [[ "$MODE" == "1" ]]; then
    read -rp "EU IP: " EU_IP
    read -rp "Bridge port [4444]: " BRIDGE
    BRIDGE=${BRIDGE:-4444}
    read -rp "Sync port [5555]: " SYNC
    SYNC=${SYNC:-5555}
    read -rp "Manual ports CSV (80,443,...): " PORTS
    PORTS=${PORTS:-443}

    SERVICE_NAME="mehtunnel-eu"
    cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=MehTunnel EU Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${PY_DST} eu ${EU_IP} ${BRIDGE} ${SYNC} ${PORTS}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

else
    read -rp "IR -> Bridge port [4444]: " BRIDGE
    BRIDGE=${BRIDGE:-4444}
    read -rp "Sync port [5555]: " SYNC
    SYNC=${SYNC:-5555}
    read -rp "Manual ports CSV (80,443,...): " PORTS
    PORTS=${PORTS:-443}

    SERVICE_NAME="mehtunnel-ir"
    cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=MehTunnel IR Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${PY_DST} ir ${BRIDGE} ${SYNC} ${PORTS}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
fi

# -----------------------------
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

ok "✅ Service ${SERVICE_NAME} created and started"
echo "You can safely close the terminal. The tunnel will keep running."
