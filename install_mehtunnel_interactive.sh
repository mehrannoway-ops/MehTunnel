#!/bin/bash
# install_mehtunnel_interactive.sh
# Interactive installer for MehTunnel v1.0

set -e

echo "======================================="
echo "       MehTunnel v1.0 Installer"
echo "======================================="

# -------------------------------
# Ask for server type
# -------------------------------
while true; do
    read -p "Which server do you want to install? (EU/IR): " SERVER_TYPE
    SERVER_TYPE=$(echo "$SERVER_TYPE" | tr '[:lower:]' '[:upper:]')
    if [[ "$SERVER_TYPE" == "EU" || "$SERVER_TYPE" == "IR" ]]; then
        break
    else
        echo "Invalid input. Please type EU or IR."
    fi
done

# -------------------------------
# Ask for ports and options
# -------------------------------
read -p "Enter BRIDGE_PORT [default 4444]: " BRIDGE_PORT
BRIDGE_PORT=${BRIDGE_PORT:-4444}

read -p "Enter SYNC_PORT [default 5555]: " SYNC_PORT
SYNC_PORT=${SYNC_PORT:-5555}

IS_AUTO="True"
MANUAL_PORTS=""

if [[ "$SERVER_TYPE" == "IR" ]]; then
    read -p "Use Auto Sync? (True/False) [default True]: " IS_AUTO
    IS_AUTO=${IS_AUTO:-True}
    if [[ "$IS_AUTO" == "False" ]]; then
        read -p "Enter MANUAL_PORTS (comma separated, e.g. 80,443,2083): " MANUAL_PORTS
    fi
fi

# -------------------------------
# Ask for IRAN_IP if EU
# -------------------------------
IRAN_IP=""
if [[ "$SERVER_TYPE" == "EU" ]]; then
    read -p "Enter Iran server IP (for EU server): " IRAN_IP
fi

# -------------------------------
# Remove old files
# -------------------------------
echo "🗑 Removing old MehTunnel files..."
rm -f /root/mehtunnel.py

# -------------------------------
# Download MehTunnel.py
# -------------------------------
echo "📥 Downloading MehTunnel v1.0..."
wget -O /root/mehtunnel.py https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/refs/heads/main/V1.0
chmod +x /root/mehtunnel.py

# -------------------------------
# Create systemd service
# -------------------------------
SERVICE_NAME="mehtunnel-${SERVER_TYPE,,}"  # mehtunnel-eu or mehtunnel-ir
echo "⚙️ Creating systemd service: $SERVICE_NAME ..."

cat <<EOF >/etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=MehTunnel v1.0 ($SERVER_TYPE)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
EOF

if [[ "$SERVER_TYPE" == "EU" ]]; then
    echo "Environment=RUN_MODE=EUROPE" >> /etc/systemd/system/$SERVICE_NAME.service
    echo "Environment=IRAN_IP=$IRAN_IP" >> /etc/systemd/system/$SERVICE_NAME.service
else
    echo "Environment=RUN_MODE=IRAN" >> /etc/systemd/system/$SERVICE_NAME.service
    echo "Environment=IS_AUTO=$IS_AUTO" >> /etc/systemd/system/$SERVICE_NAME.service
    echo "Environment=MANUAL_PORTS=$MANUAL_PORTS" >> /etc/systemd/system/$SERVICE_NAME.service
fi

cat <<EOF >>/etc/systemd/system/$SERVICE_NAME.service
Environment=BRIDGE_PORT=$BRIDGE_PORT
Environment=SYNC_PORT=$SYNC_PORT
ExecStart=/usr/bin/python3 /root/mehtunnel.py
Restart=always
RestartSec=3
LimitNOFILE=1000000
TimeoutSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# -------------------------------
# Enable and start service
# -------------------------------
echo "🚀 Enabling and starting service..."
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "✅ Installation complete!"
echo "View logs using: journalctl -u $SERVICE_NAME -f"
