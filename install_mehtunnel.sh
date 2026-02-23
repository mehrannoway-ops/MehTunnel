#!/usr/bin/env bash
set -e

PY_FILE="/opt/mehtunnel/MehTunnel.py"
BIN_FILE="/usr/local/bin/mehtunnel"

echo "[*] Updating package lists..."
apt-get update -y

echo "[*] Installing dependencies..."
apt-get install -y python3 python3-pip curl

echo "[*] Creating installation directory..."
mkdir -p /opt/mehtunnel

echo "[*] Downloading MehTunnel..."
curl -Ls https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main/MehTunnel.py -o $PY_FILE

echo "[*] Setting execute permission..."
chmod +x $PY_FILE

echo "[*] Creating launcher command: mehtunnel"
cat > $BIN_FILE <<EOF
#!/usr/bin/env bash
python3 "/opt/mehtunnel/MehTunnel.py" "\$@"
EOF

chmod +x $BIN_FILE

echo "[+] Installation completed!"
echo ""
echo "Run MehTunnel using:"
echo "sudo mehtunnel"
