#!/bin/bash

INSTALL_DIR="/opt/mehtunnel"
PY_FILE="$INSTALL_DIR/MehTunnel.py"

# ایجاد مسیر نصب
mkdir -p $INSTALL_DIR

# دانلود MehTunnel.py
echo "🔹 دانلود MehTunnel..."
curl -Ls https://raw.githubusercontent.com/mehrannoway-ops/MehTunnel/main/MehTunnel.py -o $PY_FILE
chmod +x $PY_FILE

# گرفتن ورودی کاربر
read -p "انتخاب مد (EU/IR): " MODE
read -p "IP مورد نظر: " IP
read -p "Bridge port: " BRIDGE
read -p "Sync port: " SYNC
read -p "Pool: " POOL

# ساخت سرویس systemd با مقادیر کاربر
SERVICE_FILE="/etc/systemd/system/mehtunnel-${MODE,,}.service"

echo "🔹 ساخت سرویس systemd..."
cat > $SERVICE_FILE <<EOF
[Unit]
Description=MehTunnel ${MODE} Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $PY_FILE $MODE $IP $BRIDGE $SYNC $POOL
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# فعال کردن سرویس
systemctl daemon-reload
systemctl enable "mehtunnel-${MODE,,}"

echo "✅ نصب و ساخت سرویس کامل شد!"
echo "برای اجرای سرویس: sudo systemctl start mehtunnel-${MODE,,}"
echo "و برای مشاهده لاگ: sudo journalctl -u mehtunnel-${MODE,,} -f"
