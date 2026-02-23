#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# MehTunnel Installer v2.1
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
err()  { echo -e "${CLR_RED}[!] $*${CLR_RESET}"; exit 1; }
ok()   { echo -e "${CLR_GREEN}[+] $*${CLR_RESET}"; }

# -----------------------------
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

# -----------------------------
# Ask user for config
echo "================================"
echo "        MehTunnel Manager"
echo "================================"
read -p "Select mode (1=EU,2=IR): " MODE
if [[ "$MODE" != "1" && "$MODE" != "2" ]]; then
    err "Invalid mode selection"
fi

if [[ "$MODE" == "1" ]]; then
    read -p "Iran exit IP: " IRAN_IP
    read -p "Bridge port [4444]: " BRIDGE_PORT; BRIDGE_PORT=${BRIDGE_PORT:-4444}
    read -p "Sync port [5555]: " SYNC_PORT; SYNC_PORT=${SYNC_PORT:-5555}
    read -p "Pool size [115]: " POOL_SIZE; POOL_SIZE=${POOL_SIZE:-115}
    SERVICE_NAME="mehtunnel-eu"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=MehTunnel EU Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="RUN_MODE=EUROPE"
Environment="IRAN_IP=$IRAN_IP"
Environment="BRIDGE_PORT=$BRIDGE_PORT"
Environment="SYNC_PORT=$SYNC_PORT"
Environment="POOL_SIZE=$POOL_SIZE"
ExecStart=/usr/bin/python3 $PY_DST
Restart=always
RestartSec=3
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOL
else
    read -p "Bridge port [4444]: " BRIDGE_PORT; BRIDGE_PORT=${BRIDGE_PORT:-4444}
    read -p "Sync port [5555]: " SYNC_PORT; SYNC_PORT=${SYNC_PORT:-5555}
    read -p "Auto-sync ports from EU? (y/n): " AUTO_SYNC; AUTO_SYNC=${AUTO_SYNC:-y}
    if [[ "$AUTO_SYNC" == "y" || "$AUTO_SYNC" == "Y" ]]; then
        IS_AUTO="True"
        MANUAL_PORTS=""
    else
        IS_AUTO="False"
        read -p "Manual ports CSV (80,443,...): " MANUAL_PORTS
    fi
    read -p "Pool size [115]: " POOL_SIZE; POOL_SIZE=${POOL_SIZE:-115}
    SERVICE_NAME="mehtunnel-ir"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=MehTunnel IR Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="RUN_MODE=IRAN"
Environment="BRIDGE_PORT=$BRIDGE_PORT"
Environment="SYNC_PORT=$SYNC_PORT"
Environment="IS_AUTO=$IS_AUTO"
Environment="MANUAL_PORTS=$MANUAL_PORTS"
Environment="POOL_SIZE=$POOL_SIZE"
ExecStart=/usr/bin/python3 $PY_DST
Restart=always
RestartSec=3
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOL
fi

# -----------------------------
info "Reloading systemd and enabling service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

ok "✅ Service $SERVICE_NAME created and started"
echo "You can safely close the terminal. The tunnel will keep running."
