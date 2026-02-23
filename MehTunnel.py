#!/usr/bin/env python3
import os, sys, subprocess, getpass

INSTALL_DIR = "/opt/mehtunnel"
SERVICE_DIR = "/etc/systemd/system"

def read_line(prompt):
    return input(prompt).strip()

def main():
    print("\n================================")
    print("        MehTunnel Manager")
    print("================================")
    
    mode = read_line("Select mode (1=EU,2=IR): ")
    if mode not in ("1","2"):
        print("Invalid selection."); sys.exit(1)

    if mode=="1":
        iran_ip = read_line("EU IP: ")
    else:
        iran_ip = read_line("Iran IP: ")

    bridge = read_line(f"Bridge port [4444]: ") or "4444"
    sync = read_line(f"Sync port [5555]: ") or "5555"

    manual_ports = ""
    if mode=="2":
        auto_sync = read_line("Auto-sync ports from EU? (y/n): ").lower() or "y"
        if auto_sync=="n":
            manual_ports = read_line("Manual ports CSV (80,443,...): ")

    # Determine service name
    svc_name = "mehtunnel-eu" if mode=="1" else "mehtunnel-ir"

    # Build ExecStart command
    args = ["python3", f"{INSTALL_DIR}/MehTunnel.py", "RUN"]
    args.append("EU" if mode=="1" else "IR")
    args.append(str(bridge))
    args.append(str(sync))
    args.append(str(115))  # default pool
    if manual_ports: args.append(manual_ports)
    cmdline = " ".join(args)

    # Create systemd service
    svc_file = f"{SERVICE_DIR}/{svc_name}.service"
    with open(svc_file, "w") as f:
        f.write(f"""[Unit]
Description=MehTunnel {'EU' if mode=='1' else 'IR'} Service
After=network.target

[Service]
Type=simple
ExecStart={cmdline}
Restart=always
User={getpass.getuser()}
WorkingDirectory={INSTALL_DIR}
StandardOutput=inherit
StandardError=inherit

[Install]
WantedBy=multi-user.target
""")
    # Reload systemd & enable service
    subprocess.run(["systemctl","daemon-reload"], check=True)
    subprocess.run(["systemctl","enable",svc_name], check=True)
    subprocess.run(["systemctl","start",svc_name], check=True)

    print(f"\n✅ Service {svc_name} created and started")
    print("You can safely close the terminal. The tunnel will keep running.\n")

if __name__=="__main__":
    main()
