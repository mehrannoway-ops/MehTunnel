#!/usr/bin/env bash
set -euo pipefail

# --- تنظیمات ---
REPO_RAW="https://raw.githubusercontent.com/your-github-user/MehTunnel/main"
PYTHON_FILE="$REPO_RAW/MehTunnel.py"
INSTALL_PATH="/opt/mehtunnel"
SERVICE_NAME="mehtunnel"
BIN_PATH="/usr/local/bin/mehtunnel"

mkdir -p "$INSTALL_PATH"

echo "[*] دانلود MehTunnel.py..."
curl -fsSL "$PYTHON_FILE" -o "$INSTALL_PATH/MehTunnel.py"
chmod +x "$INSTALL_PATH/MehTunnel.py"

# --- ساخت دستور mehtunnel ---
cat > "$BIN_PATH" <<'EOF'
#!/usr/bin/env bash
sudo python3 /opt/mehtunnel/MehTunnel.py
EOF
chmod +x "$BIN_PATH"

# --- ساخت systemd service ---
read -p "Select mode (1=EU,2=IR): " MODE
read -p "Bridge port [4444]: " BRIDGE
BRIDGE=${BRIDGE:-4444}
read -p "Sync port [5555]: " SYNC
SYNC=${SYNC:-5555}
if [[ "$MODE" == "1" ]]; then
  IRAN_IP=$(read -p "Iran IP: " IP && echo $IP)
  SERVICE_FILE="[Unit]
Description=MehTunnel EU
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_PATH/MehTunnel.py <<EOF
1
$IRAN_IP
$BRIDGE
$SYNC
EOF
Restart=always

[Install]
WantedBy=multi-user.target"
  echo "$SERVICE_FILE" | sudo tee /etc/systemd/system/mehtunnel-eu.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now mehtunnel-eu
else
  SERVICE_FILE="[Unit]
Description=MehTunnel IR
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_PATH/MehTunnel.py <<EOF
2
$BRIDGE
$SYNC
y
EOF
Restart=always

[Install]
WantedBy=multi-user.target"
  echo "$SERVICE_FILE" | sudo tee /etc/systemd/system/mehtunnel-ir.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now mehtunnel-ir
fi

echo "[+] نصب کامل شد! از دستور 'mehtunnel' برای اجرای سریع استفاده کنید."
