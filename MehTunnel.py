#!/usr/bin/env python3
import os, sys, subprocess, time

SERVICE_TEMPLATE = """
[Unit]
Description=MehTunnel {mode} Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/mehtunnel/MehTunnel.py --service {mode} --ip {ip} --bridge {bridge} --sync {sync} --ports {ports}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
"""

def create_service(mode, ip, bridge, sync, ports):
    service_name = f"mehtunnel-{mode.lower()}"
    service_file = f"/etc/systemd/system/{service_name}.service"
    with open(service_file, "w") as f:
        f.write(SERVICE_TEMPLATE.format(mode=mode.upper(), ip=ip, bridge=bridge, sync=sync, ports=ports))
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "--now", service_name])
    print(f"\n✅ Service {service_name} created and started")
    print("You can safely close the terminal. The tunnel will keep running.")

def run_mode(mode):
    ip = input("Iran IP: ") if mode=="IR" else input("EU IP: ")
    bridge = input("Bridge port [4444]: ") or "4444"
    sync = input("Sync port [5555]: ") or "5555"
    ports = input("Manual ports CSV (80,443,...): ") or "80,443"
    create_service(mode, ip, bridge, sync, ports)

def main():
    if "--service" in sys.argv:
        # اجرا از طریق systemd
        idx = sys.argv.index("--service")
        mode = sys.argv[idx+1]
        ip = sys.argv[sys.argv.index("--ip")+1]
        bridge = sys.argv[sys.argv.index("--bridge")+1]
        sync = sys.argv[sys.argv.index("--sync")+1]
        ports = sys.argv[sys.argv.index("--ports")+1]
        # اینجا میتونی کد تانل واقعی خودت رو بذاری
        print(f"[{mode}] Running | IP={ip} bridge={bridge} sync={sync} ports={ports}")
        while True:
            time.sleep(3600)
    else:
        print("================================")
        print("        MehTunnel Manager")
        print("================================")
        mode = input("Select mode (1=EU,2=IR): ")
        if mode=="1": run_mode("EU")
        else: run_mode("IR")

if __name__=="__main__":
    main()
