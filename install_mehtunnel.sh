#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# MehTunnel Installer + systemd
# ----------------------------

REPO="https://raw.githubusercontent.com/your-github/MehTunnel/main"
PY_URL="$REPO/MehTunnel.py"

INSTALL_DIR="/opt/mehtunnel"
PY_DST="$INSTALL_DIR/MehTunnel.py"
BIN="/usr/local/bin/mehtunnel"

# --------- helpers ----------
err() { echo "[!] $*" >&2; exit 1; }
info() { echo "[*] $*"; }
ok() { echo "[+] $*"; }

need_root(){ [[ "$(id -u)" == "0" ]] || { err "Run as root"; }; }
have(){ command -v "$1" >/dev/null 2>&1; }

# --------- install deps ----------
install_deps(){
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y >/dev/null 2>&1 || true
    for pkg in python3 curl screen; do
        dpkg -s $pkg >/dev/null 2>&1 || apt-get install -y $pkg >/dev/null 2>&1
    done
}

# --------- fetch python core ----------
fetch_core(){
    mkdir -p "$INSTALL_DIR"
    info "Downloading MehTunnel core..."
    curl -fsSL "$PY_URL" -o "$PY_DST" || err "Failed to download MehTunnel.py"
    chmod +x "$PY_DST"
}

# --------- create CLI shortcut ----------
install_bin(){
    cat > "$BIN" <<EOF
#!/usr/bin/env bash
python3 "$PY_DST" "\$@"
EOF
    chmod +x "$BIN"
    ok "Installed CLI: $BIN"
}

# --------- create systemd service ----------
create_service(){
    read -p "Select mode (1=EU,2=IR): " MODE
    [[ "$MODE" == "1" ]] && ROLE="eu" || ROLE="ir"

    read -p "Bridge port [4444]: " BRIDGE
    BRIDGE=${BRIDGE:-4444}

    read -p "Sync port [5555]: " SYNC
    SYNC=${SYNC:-5555}

    if [[ "$ROLE" == "eu" ]]; then
        read -p "Iran IP: " IRAN_IP
        SRVC_NAME="mehtunnel-eu"
        CMD="python3 $PY_DST --mode eu --iran-ip $IRAN_IP --bridge $BRIDGE --sync $SYNC"
    else
        SRVC_NAME="mehtunnel-ir"
        echo "IR mode will auto-sync from EU"
        CMD="python3 $PY_DST --mode ir --bridge $BRIDGE --sync $SYNC --auto-sync"
    fi

    info "Creating systemd service: $SRVC_NAME"
    SERVICE_PATH="/etc/systemd/system/$SRVC_NAME.service"
    cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=MehTunnel $ROLE Tunnel
After=network.target

[Service]
Type=simple
ExecStart=$CMD
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$SRVC_NAME"
    systemctl start "$SRVC_NAME"
    ok "Service $SRVC_NAME started. It will stay active after terminal closes."
}

# ---------------- main ----------------
need_root
install_deps
fetch_core
install_bin
create_service

echo ""
ok "MehTunnel installation completed!"
echo "Run manually: sudo $BIN"
echo "Or manage service with: sudo systemctl [start|stop|status] $SRVC_NAME"
