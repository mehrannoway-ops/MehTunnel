#!/usr/bin/env python3
import os, sys, subprocess, time
from pathlib import Path

INSTALL_DIR = "/opt/mehtunnel"
MEH_FILE = f"{INSTALL_DIR}/MehTunnel.py"

def read_line(prompt=None):
    if prompt: print(prompt, end="", flush=True)
    s = sys.stdin.readline()
    return s.strip() if s else ""

def create_service(name, cmd, desc):
    service_path = f"/etc/systemd/system/{name}.service"
    content = f"""[Unit]
Description={desc}
After=network.target

[Service]
Type=simple
ExecStart={cmd}
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
"""
    Path(service_path).write_text(content)
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", name])
    subprocess.run(["systemctl", "start", name])

def eu_mode():
    iran_ip = read_line("EU -> Iran IP: ")
    bridge = read_line("Bridge port [4444]: ") or "4444"
    sync = read_line("Sync port [5555]: ") or "5555"
    pool = 157
    cmd = f"python3 {MEH_FILE} eu {iran_ip} {bridge} {sync} {pool}"
    create_service("mehtunnel-eu", cmd, "MehTunnel EU Service")
    print("✅ Service mehtunnel-eu created and started")
    print("You can safely close the terminal. The tunnel will keep running.")

def ir_mode():
    bridge = read_line("IR -> Bridge port [4444]: ") or "4444"
    sync = read_line("Sync port [5555]: ") or "5555"
    manual_ports = read_line("Manual ports CSV (80,443,...): ") or ""
    pool = 115
    cmd = f"python3 {MEH_FILE} ir {bridge} {sync} {pool} {manual_ports}"
    create_service("mehtunnel-ir", cmd, "MehTunnel IR Service")
    print("✅ Service mehtunnel-ir created and started")
    print("You can safely close the terminal. The tunnel will keep running.")

def main():
    print("\n================================")
    print("        MehTunnel Manager")
    print("================================")
    choice = read_line("Select mode (1=EU,2=IR): ")
    if choice == "1":
        eu_mode()
    elif choice == "2":
        ir_mode()
    else:
        print("Invalid selection"); sys.exit(1)

if __name__ == "__main__":
    main()
