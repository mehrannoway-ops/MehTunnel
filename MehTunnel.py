#!/usr/bin/env python3
import os, sys, subprocess

SERVICE_DIR="/etc/systemd/system"

def create_service(mode, bridge, sync, manual_ports=""):
    svc_name = f"mehtunnel-{mode.lower()}"
    manual_ports_arg = manual_ports if manual_ports else ""
    content = f"""[Unit]
Description=MehTunnel {mode} Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/mehtunnel/MehTunnel.py RUN {mode} {bridge} {sync} {manual_ports_arg}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    path = os.path.join(SERVICE_DIR, f"{svc_name}.service")
    with open(path,"w") as f:
        f.write(content)
    subprocess.run(["systemctl","daemon-reload"])
    subprocess.run(["systemctl","enable",svc_name])
    subprocess.run(["systemctl","start",svc_name])
    print(f"✅ Service {svc_name} created and started\nYou can safely close the terminal. The tunnel will keep running.")

def main():
    print("================================")
    print("        MehTunnel Manager")
    print("================================")
    choice = input("Select mode (1=EU,2=IR): ").strip()
    if choice=="1":
        mode="EU"
    elif choice=="2":
        mode="IR"
    else:
        print("Invalid mode."); sys.exit(1)

    bridge = input(f"{mode} -> Bridge port [4444]: ").strip() or "4444"
    sync   = input(f"Sync port [5555]: ").strip() or "5555"

    if mode=="IR":
        auto = input("Auto-sync ports from EU? (y/n): ").lower() or "y"
        if auto=="n":
            manual_ports = input("Manual ports CSV (80,443,...): ").strip()
        else:
            manual_ports=""
    else:
        manual_ports=""

    create_service(mode, bridge, sync, manual_ports)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="RUN":
        # اجرای مستقیم سرویس، با آرگومان‌های systemd
        import MehTunnel_impl as mt
        mt.run(sys.argv[2:])
    else:
        main()
