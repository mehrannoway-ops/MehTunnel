#!/usr/bin/env python3
import sys
import os

def interactive_menu():
    print("================================")
    print("        MehTunnel Manager")
    print("================================")

    mode = input("Select mode (1=EU,2=IR): ").strip()

    if mode == "1":
        iran_ip = input("Iran IP: ").strip()
        bridge = input("Bridge port [4444]: ").strip() or "4444"
        sync = input("Sync port [5555]: ").strip() or "5555"
        create_service("EU", iran_ip, bridge, sync)

    elif mode == "2":
        bridge = input("Bridge port [4444]: ").strip() or "4444"
        sync = input("Sync port [5555]: ").strip() or "5555"
        auto = input("Auto-sync ports? (y/n): ").lower()
        ports = ""
        if auto == "n":
            ports = input("Manual ports CSV: ")
        create_service("IR", "", bridge, sync, auto, ports)

    else:
        print("Invalid option")
        sys.exit(1)


def create_service(mode, ip, bridge, sync, auto="y", ports=""):
    name = f"mehtunnel-{mode.lower()}"
    service = f"""[Unit]
Description=MehTunnel {mode}
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/mehtunnel/MehTunnel.py RUN {mode} {ip} {bridge} {sync} {auto} {ports}
Restart=always
RestartSec=3
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
"""

    path = f"/etc/systemd/system/{name}.service"
    with open(path, "w") as f:
        f.write(service)

    os.system("systemctl daemon-reload")
    os.system(f"systemctl enable {name}")
    os.system(f"systemctl start {name}")

    print(f"\n✅ Service {name} created and started")
    print("You can safely close the terminal. The tunnel will keep running.")


def run_tunnel(args):
    """
    این تابع فقط جایگزین واقعی اجرای تانل هست.
    باید کد فعلی تانل EU/IR رو اینجا بیاری.
    برای نمونه، فقط چاپ می‌کنیم.
    """
    print("Running MehTunnel with args:", args)
    mode = args[0]
    iran_ip = args[1] if len(args) > 1 else ""
    bridge = args[2] if len(args) > 2 else ""
    sync = args[3] if len(args) > 3 else ""
    auto = args[4] if len(args) > 4 else "y"
    ports = args[5] if len(args) > 5 else ""

    print(f"Mode={mode} | IR={iran_ip} | Bridge={bridge} | Sync={sync} | AutoSync={auto} | Ports={ports}")
    print("🚀 MehTunnel is running... (simulation)")

    # اینجا باید حلقه اصلی تانل باشه
    import time
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n🔹 MehTunnel stopped manually")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_menu()
        elif sys.argv[1] == "RUN":
            run_tunnel(sys.argv[2:])
        else:
            print("Unknown option")
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
