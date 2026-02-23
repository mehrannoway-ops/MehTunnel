#!/usr/bin/env bash
set -euo pipefail

# ----------------------
APP_NAME="MehTunnel"
REPO="https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main"
PY_URL="$REPO/MehTunnel.py"
MEH_DST="/opt/mehtunnel/MehTunnel.py"
SERVICE_DIR="/etc/systemd/system"

# ---------- رنگ‌ها ----------
RED="\033[31m"; GREEN="\033[32m"; CYAN="\033[36m"; RESET="\033[0m"

echo -e "${CYAN}[*] $APP_NAME Installer${RESET}"

# ---------- نصب پیش‌نیازها ----------
echo -e "${CYAN}[*] Installing dependencies...${RESET}"
apt-get update -y >/dev/null
apt-get install -y python3 curl >/dev/null

# ---------- دانلود MehTunnel.py ----------
mkdir -p "$(dirname $MEH_DST)"
echo -e "${CYAN}[*] Downloading MehTunnel.py...${RESET}"
curl -fsSL "$PY_URL" -o "$MEH_DST"
chmod +x "$MEH_DST"

# ---------- گرفتن کانفیگ ----------
echo -e "${CYAN}Select mode:${RESET} 1) EU  2) IR"
read -rp "Mode (1/2): " MODE

if [[ "$MODE" == "1" ]]; then
    read -rp "Iran IP: " IRAN_IP
    read -rp "Bridge port [4444]: " BRIDGE
    BRIDGE=${BRIDGE:-4444}
    read -rp "Sync port [5555]: " SYNC
    SYNC=${SYNC:-5555}

    SERVICE="$SERVICE_DIR/mehtunnel-eu.service"

    cat > "$SERVICE" <<EOF
[Unit]
Description=MehTunnel EU Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $MEH_DST <<EOF
1
$IRAN_IP
$BRIDGE
$SYNC
EOF
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mehtunnel-eu
    systemctl start mehtunnel-eu
    echo -e "${GREEN}[+] MehTunnel EU service created and started!${RESET}"
    echo "Logs: journalctl -u mehtunnel-eu -f"

else
    read -rp "Bridge port [4444]: " BRIDGE
    BRIDGE=${BRIDGE:-4444}
    read -rp "Sync port [5555]: " SYNC
    SYNC=${SYNC:-5555}
    read -rp "Auto-sync ports from EU? (y/n): " AUTOSYNC
    if [[ "${AUTOSYNC,,}" == "n" ]]; then
        read -rp "Manual ports CSV (e.g., 80,443): " PORTS
    else
        PORTS=""
    fi

    SERVICE="$SERVICE_DIR/mehtunnel-ir.service"

    cat > "$SERVICE" <<EOF
[Unit]
Description=MehTunnel IR Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $MEH_DST <<EOF
2
$BRIDGE
$SYNC
$( [[ "${AUTOSYNC,,}" == "y" ]] && echo "y" || echo "n" )
$PORTS
EOF
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mehtunnel-ir
    systemctl start mehtunnel-ir
    echo -e "${GREEN}[+] MehTunnel IR service created and started!${RESET}"
    echo "Logs: journalctl -u mehtunnel-ir -f"
fi
