#!/usr/bin/env bash
set -euo pipefail

APP_NAME="MehTunnel"
PY_URL="https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/MehTunnel.py/main"
PY_DST="/opt/mehtunnel/MehTunnel.py"
BIN="/usr/local/bin/mehtunnel"

# Check root
if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo bash $0"
  exit 1
fi

# Install dependencies
apt-get update -y >/dev/null
apt-get install -y python3 curl systemd >/dev/null

mkdir -p "$(dirname "$PY_DST")"

# Download MehTunnel.py
echo "📥 Downloading MehTunnel.py..."
curl -fsSL "$PY_URL" -o "$PY_DST" || { echo "Failed to download MehTunnel.py"; exit 1; }
chmod +x "$PY_DST"

# Create executable wrapper
cat > "$BIN" <<'EOF'
#!/usr/bin/env bash
python3 /opt/mehtunnel/MehTunnel.py
EOF
chmod +x "$BIN"

echo "⚙️  MehTunnel installed at $BIN"

# Ask user for configuration
echo "Select server to install:"
select MODE in "EU" "IR"; do
    [[ -n "$MODE" ]] && break
done

read -rp "Bridge port [4444]: " BRIDGE_PORT
BRIDGE_PORT=${BRIDGE_PORT:-4444}

read -rp "Sync port [5555]: " SYNC_PORT
SYNC_PORT=${SYNC_PORT:-5555}

if [[ "$MODE" == "EU" ]]; then
    read -rp "Iran server IP: " IRAN_IP
fi

if [[ "$MODE" == "IR" ]]; then
    read -rp "Auto-sync ports from EU? (y/n): " AUTO_SYNC
    if [[ "${AUTO_SYNC,,}" != "y" ]]; then
        read -rp "Manual ports CSV (e.g. 80,443,2083): " MANUAL_PORTS
    fi
fi

SERVICE_NAME="mehtunnel-${MODE,,}"

# Create systemd service
cat > "/etc/systemd/system/$SERVICE_NAME.service" <<EOF
[Unit]
Description=MehTunnel Service (${MODE})
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment="BRIDGE_PORT=$BRIDGE_PORT"
Environment="SYNC_PORT=$SYNC_PORT"
EOF

if [[ "$MODE" == "EU" ]]; then
    cat >> "/etc/systemd/system/$SERVICE_NAME.service" <<EOF
Environment="IRAN_IP=$IRAN_IP"
Environment="RUN_MODE=EU"
EOF
else
    cat >> "/etc/systemd/system/$SERVICE_NAME.service" <<EOF
Environment="RUN_MODE=IR"
Environment="IS_AUTO=${AUTO_SYNC,,}"
Environment="MANUAL_PORTS=${MANUAL_PORTS:-}"
EOF
fi

cat >> "/etc/systemd/system/$SERVICE_NAME.service" <<'EOF'
ExecStart=/usr/bin/python3 /opt/mehtunnel/MehTunnel.py
Restart=always
RestartSec=3
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo "✅ Service $SERVICE_NAME created and started."
echo "View logs: journalctl -u $SERVICE_NAME -f"
