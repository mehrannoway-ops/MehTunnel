#!/usr/bin/env python3
import os, sys, time, socket, struct, threading, subprocess

SERVICE_NAME_EU = "mehtunnel-eu"
SERVICE_NAME_IR = "mehtunnel-ir"

BRIDGE_DEFAULT = 4444
SYNC_DEFAULT = 5555

PYTHON_PATH = sys.executable
SCRIPT_PATH = os.path.abspath(__file__)

def write_systemd_service(name, mode, iran_ip=None, bridge=4444, sync=5555):
    unit = f"""
[Unit]
Description=MehTunnel {mode.upper()} Service
After=network.target

[Service]
Type=simple
ExecStart={PYTHON_PATH} {SCRIPT_PATH} {mode} {iran_ip or ''} {bridge} {sync}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    path = f"/etc/systemd/system/{name}.service"
    with open(path, "w") as f:
        f.write(unit)
    os.system(f"systemctl daemon-reload")
    os.system(f"systemctl enable {name}")
    os.system(f"systemctl start {name}")
    print(f"[+] Service {name} created and started!")

def eu_mode(iran_ip, bridge, sync):
    print(f"[EU] IR={iran_ip} bridge={bridge} sync={sync} running...")
    while True:
        time.sleep(3600)

def ir_mode(bridge, sync, ports_csv):
    ports = [int(p.strip()) for p in ports_csv.split(",") if p.strip()]
    print(f"[IR] bridge={bridge} sync={sync} ports={ports} running...")
    while True:
        time.sleep(3600)

def main():
    if len(sys.argv) > 1:
        # systemd service mode
        mode = sys.argv[1]
        if mode == "eu":
            iran_ip = sys.argv[2]
            bridge = int(sys.argv[3])
            sync = int(sys.argv[4])
            eu_mode(iran_ip, bridge, sync)
        elif mode == "ir":
            bridge = int(sys.argv[2])
            sync = int(sys.argv[3])
            ports = sys.argv[4]
            ir_mode(bridge, sync, ports)
        return

    # Interactive mode
    print("Select mode (1=EU,2=IR): ", end="")
    choice = input().strip()
    if choice == "1":
        print("Iran IP: ", end="")
        iran_ip = input().strip()
        print(f"Bridge port [{BRIDGE_DEFAULT}]: ", end="")
        bridge = int(input().strip() or BRIDGE_DEFAULT)
        print(f"Sync port [{SYNC_DEFAULT}]: ", end="")
        sync = int(input().strip() or SYNC_DEFAULT)
        write_systemd_service(SERVICE_NAME_EU, "eu", iran_ip, bridge, sync)
    else:
        print(f"Bridge port [{BRIDGE_DEFAULT}]: ", end="")
        bridge = int(input().strip() or BRIDGE_DEFAULT)
        print(f"Sync port [{SYNC_DEFAULT}]: ", end="")
        sync = int(input().strip() or SYNC_DEFAULT)
        print("Manual ports CSV (e.g., 80,443): ", end="")
        ports_csv = input().strip()
        write_systemd_service(SERVICE_NAME_IR, "ir", bridge=bridge, sync=sync)
    print("[*] Setup complete. Use 'journalctl -u mehtunnel-eu -f' or 'mehtunnel-ir' to view logs.")

if __name__ == "__main__":
    main()
