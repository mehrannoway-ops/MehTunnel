#!/usr/bin/env python3
import os, sys, subprocess, time

def read_line(prompt=None):
    if prompt: print(prompt,end="",flush=True)
    s = sys.stdin.readline()
    return s.strip() if s else ""

def create_service(name, args):
    svc_file = f"/etc/systemd/system/mehtunnel-{name}.service"
    cmd = f"/usr/bin/python3 /opt/mehtunnel/MehTunnel.py {args}"
    with open(svc_file,"w") as f:
        f.write(f"""[Unit]
Description=MehTunnel {name.upper()} Service
After=network.target

[Service]
Type=simple
ExecStart={cmd}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
""")
    subprocess.run(["systemctl","daemon-reload"])
    subprocess.run(["systemctl","enable",f"mehtunnel-{name}"])
    subprocess.run(["systemctl","start",f"mehtunnel-{name}"])
    print(f"\n✅ Service mehtunnel-{name} created and started")
    print("You can safely close the terminal. The tunnel will keep running.\n")

def main():
    print("\n================================")
    print("        MehTunnel Manager")
    print("================================")

    choice = read_line("Select mode (1=EU,2=IR): ")
    if choice not in ("1","2"):
        print("Invalid selection."); sys.exit(1)

    if choice=="1":
        iran_ip = read_line("EU IP (use Iran exit IP if needed): ")
        bridge = read_line("Bridge port [4444]: ") or "4444"
        sync = read_line("Sync port [5555]: ") or "5555"
        pool = read_line("Pool size [auto]: ") or "115"
        args = f"eu {iran_ip} {bridge} {sync} {pool}"
        create_service("eu", args)
    else:
        bridge = read_line("IR -> Bridge port [4444]: ") or "4444"
        sync = read_line("Sync port [5555]: ") or "5555"
        auto = read_line("Auto-sync ports from EU? (y/n): ").lower() or "y"
        manual_ports = ""
        if auto=="n":
            manual_ports = read_line("Manual ports CSV (80,443,...): ")
        pool = read_line("Pool size [auto]: ") or "115"
        args = f"ir {bridge} {sync} {pool} {auto} {manual_ports}"
        create_service("ir", args)

if __name__=="__main__":
    main()
