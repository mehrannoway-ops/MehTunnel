#!/bin/bash
set -e

echo "🔹 ساخت دایرکتوری /opt/mehtunnel..."
sudo mkdir -p /opt/mehtunnel
cd /opt/mehtunnel

echo "🔹 دانلود MehTunnel.py جدید..."
sudo curl -L -o MehTunnel.py https://raw.githubusercontent.com/your-repo/MehTunnel/main/MehTunnel.py

echo "🔹 اعمال دسترسی اجرا..."
sudo chmod +x MehTunnel.py

echo "🔹 ایجاد سرویس systemd برای MehTunnel..."
sudo tee /etc/systemd/system/mehtunnel.service > /dev/null <<EOL
[Unit]
Description=MehTunnel Auto Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/mehtunnel/MehTunnel.py --auto
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOL

echo "🔹 بارگذاری سرویس و فعال‌سازی..."
sudo systemctl daemon-reload
sudo systemctl enable mehtunnel
sudo systemctl start mehtunnel

echo "✅ نصب کامل شد! تانل هم اکنون فعال است."
echo "وضعیت سرویس:"
sudo systemctl status mehtunnel --no-pager
