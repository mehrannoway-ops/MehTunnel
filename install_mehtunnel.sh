#!/usr/bin/env bash
set -euo pipefail

REPO="https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main"
PY_URL="$REPO/MehTunnel.py"
BIN="/usr/local/bin/mehtunnel"
PY_DST="/opt/mehtunnel/MehTunnel.py"

echo "[*] Installing MehTunnel..."
mkdir -p "$(dirname "$PY_DST")"

curl -fsSL "$PY_URL" -o "$PY_DST" || { echo "Download failed"; exit 1; }
chmod +x "$PY_DST"

cat > "$BIN" <<EOF
#!/usr/bin/env bash
python3 "$PY_DST"
EOF
chmod +x "$BIN"

echo "[+] Installed!"
echo "Run: sudo mehtunnel"
