import os
import sys

def create_service(ip, bridge, sync, ports):
    service_name = "mehtunnel-custom"
    service_path = f"/etc/systemd/system/{service_name}.service"
    
    content = f"""[Unit]
Description=MehTunnel Custom Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/mehtunnel/MehTunnel.py --auto --ip {ip} --bridge {bridge} --sync {sync} --ports {ports}
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""
    with open(service_path, "w") as f:
        f.write(content)
    
    os.system("systemctl daemon-reload")
    os.system(f"systemctl enable {service_name}")
    os.system(f"systemctl start {service_name}")
    print(f"✅ سرویس {service_name} ساخته و اجرا شد!")

if __name__ == "__main__":
    # حالت سرویس خودکار
    if "--auto-service" in sys.argv:
        ip = input("Iran IP: ")
        bridge = input("Bridge port [4444]: ")
        sync = input("Sync port [5555]: ")
        ports = input("Manual ports CSV (80,443,...): ")
        create_service(ip, bridge, sync, ports)
        sys.exit(0)
    
    # حالت معمولی MehTunnel
    # ... کد اصلی تانل اینجا ادامه پیدا می‌کنه
