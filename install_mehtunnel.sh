#!/usr/bin/env bash

set -e

PY_FILE="/opt/mehtunnel/MehTunnel.py"

echo "[*] Updating package lists..."
sudo apt update -y

echo "[*] Installing dependencies..."
sudo apt install -y python3 python3-pip curl

echo "[*] Creating installation directory..."
sudo mkdir -p /opt/mehtunnel

echo "[*] Downloading MehTunnel.py..."
sudo curl -Ls https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main/MehTunnel.py -o $PY_FILE
sudo chmod +x $PY_FILE

echo "[*] Creating launcher command: mehtunnel"
sudo bash -c 'cat > /usr/local/bin/mehtunnel <<EOF
#!/usr/bin/env bash
python3 -u /opt/mehtunnel/MehTunnel.py --interactive
EOF'
sudo chmod +x /usr/local/bin/mehtunnel

echo "[+] Installation completed!"
echo ""
echo "Run MehTunnel using:"
echo "sudo mehtunnel"
