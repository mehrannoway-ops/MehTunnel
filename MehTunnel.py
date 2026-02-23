#!/usr/bin/env python3
import os, sys, time, socket, struct, threading, subprocess, re, resource

# --------- Tunables ----------
DIAL_TIMEOUT = 5
KEEPALIVE_SECS = 20
SOCKBUF = 8 * 1024 * 1024
BUF_COPY = 256 * 1024
POOL_WAIT = 5
SYNC_INTERVAL = 3

# --------- Auto pool sizing ----------
def auto_pool_size(role: str = "ir") -> int:
    try:
        env_pool = int(os.environ.get("MEHTUNNEL_POOL", "0"))
        if env_pool > 0: return env_pool
    except Exception: pass

    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        nofile = soft if soft and soft > 0 else 1024
    except Exception: nofile = 1024

    mem_mb = 0
    try:
        with open("/proc/meminfo","r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb=int(line.split()[1])
                    mem_mb=mem_kb//1024
                    break
    except Exception: mem_mb=0

    reserve=500
    fd_budget=max(0,nofile-reserve)
    frac=0.22 if role.lower().startswith("ir") else 0.30
    fd_based=int(fd_budget*frac)
    ram_based=int((mem_mb/1024)*250) if mem_mb else 500
    pool=min(fd_based,ram_based)
    if pool<100: pool=100
    if pool>2000: pool=2000
    return pool

# --------- Socket helpers ----------
def is_socket_alive(s: socket.socket) -> bool:
    try:
        s.setblocking(False)
        try: s.recv(1, socket.MSG_PEEK)
        except BlockingIOError: return True
        except Exception: return True
        finally: s.setblocking(True)
        return True
    except Exception: return False

def tune_tcp(sock: socket.socket):
    try: sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
    except Exception: pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKBUF)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKBUF)
    except Exception: pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket,"TCP_KEEPIDLE"): sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPIDLE,KEEPALIVE_SECS)
        if hasattr(socket,"TCP_KEEPINTVL"): sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPINTVL,KEEPALIVE_SECS)
        if hasattr(socket,"TCP_KEEPCNT"): sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPCNT,3)
    except Exception: pass

def dial_tcp(host,port):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tune_tcp(s)
    s.settimeout(DIAL_TIMEOUT)
    s.connect((host,port))
    s.settimeout(None)
    return s

def recv_exact(sock: socket.socket,n:int):
    data=bytearray()
    while len(data)<n:
        chunk=sock.recv(n-len(data))
        if not chunk: return None
        data.extend(chunk)
    return bytes(data)

def pipe(a: socket.socket,b: socket.socket):
    buf=bytearray(BUF_COPY)
    try:
        while True:
            n=a.recv_into(buf)
            if n<=0: break
            b.sendall(memoryview(buf)[:n])
    except Exception: pass
    finally:
        try: a.shutdown(socket.SHUT_RD)
        except Exception: pass
        try: b.shutdown(socket.SHUT_WR)
        except Exception: pass

def bridge(a: socket.socket,b: socket.socket):
    t1=threading.Thread(target=pipe,args=(a,b),daemon=True)
    t2=threading.Thread(target=pipe,args=(b,a),daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()
    try: a.close()
    except Exception: pass
    try: b.close()
    except Exception: pass

# --------- IR Mode ----------
from queue import Queue, Empty
def ir_mode(bridge_port, sync_port, pool_size, auto_sync, manual_ports_csv):
    pool=Queue(maxsize=pool_size*2)
    active={}
    active_lock=threading.Lock()

    def accept_bridge():
        srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        srv.bind(("0.0.0.0",bridge_port))
        srv.listen(16384)
        print(f"[IR] Bridge listening on {bridge_port}")
        while True:
            try: c,_=srv.accept()
            except OSError: time.sleep(0.2); continue
            tune_tcp(c)
            try: pool.put(c, block=False)
            except Exception:
                try: c.close()
                except Exception: pass

    def handle_user(user_sock,target_port):
        tune_tcp(user_sock)
        deadline=time.time()+POOL_WAIT
        europe=None
        while time.time()<deadline:
            try: cand=pool.get(timeout=max(0.1,deadline-time.time()))
            except Empty: break
            if is_socket_alive(cand):
                europe=cand
                break
            try: cand.close()
            except Exception: pass
        if europe is None:
            try: user_sock.close()
            except Exception: pass
            return
        try:
            europe.settimeout(2)
            europe.sendall(struct.pack("!H",target_port))
            europe.settimeout(None)
        except Exception:
            try: user_sock.close()
            except Exception: pass
            try: europe.close()
            except Exception: pass
            return
        bridge(user_sock,europe)

    def open_port(p:int):
        with active_lock:
            if p in active: return
            active[p]=True
        try:
            srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            srv.bind(("0.0.0.0",p))
            srv.listen(16384)
        except Exception as e:
            with active_lock: active.pop(p,None)
            print(f"[IR] Cannot open port {p}: {e}")
            return
        print(f"[IR] Port Active: {p}")
        def accept_users():
            while True:
                try: u,_=srv.accept()
                except OSError: time.sleep(0.2); continue
                try: threading.Thread(target=handle_user,args=(u,p),daemon=True).start()
                except Exception:
                    try: u.close()
                    except Exception: pass
        threading.Thread(target=accept_users,daemon=True).start()

    def sync_listener():
        srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        srv.bind(("0.0.0.0",sync_port))
        srv.listen(1024)
        print(f"[IR] Sync listening on {sync_port} (AutoSync)")
        while True:
            try: c,_=srv.accept()
            except OSError: time.sleep(0.2); continue
            def handle_sync(conn):
                try:
                    while True:
                        h=recv_exact(conn,1)
                        if not h: break
                        count=h[0]
                        for _ in range(count):
                            pd=recv_exact(conn,2)
                            if not pd: return
                            (p,)=struct.unpack("!H",pd)
                            open_port(p)
                except Exception: pass
                finally:
                    try: conn.close()
                    except Exception: pass
            threading.Thread(target=handle_sync,args=(c,),daemon=True).start()

    threading.Thread(target=accept_bridge,daemon=True).start()
    if auto_sync: threading.Thread(target=sync_listener,daemon=True).start()
    else:
        ports=[]
        if manual_ports_csv.strip():
            for part in manual_ports_csv.split(","):
                try:
                    p=int(part.strip())
                    if 1<=p<=65535: ports.append(p)
                except Exception: pass
        for p in ports: open_port(p)
        print("[IR] Manual ports opened.")

    print(f"[IR] Running | bridge={bridge_port} sync={sync_port} pool={pool_size} autoSync={auto_sync}")
    while True: time.sleep(3600)

# --------- Menu ----------
def read_line(prompt=None):
    if prompt: print(prompt,end="",flush=True)
    s=sys.stdin.readline()
    return s.strip() if s else ""

def main():
    print("\n================================")
    print("        MehTunnel Manager")
    print("================================")
    choice=read_line("Select mode (1=EU,2=IR): ")
    if choice!="2":
        print("Only IR mode supported for stable persistent tunnel."); sys.exit(1)
    bridge=int(read_line("IR -> Bridge port [4444]: ") or "4444")
    sync=int(read_line("Sync port [5555]: ") or "5555")
    yn=read_line("Auto-sync ports from EU? (y/n): ").lower() or "y"
    if yn=="y": auto_sync=True
    else: auto_sync=False
    ports=read_line("Manual ports CSV (80,443,...): ")
    pool=auto_pool_size("ir")

    # --------- Create systemd service ----------
    service_name="mehtunnel-ir.service"
    unit_path=f"/etc/systemd/system/{service_name}"
    cmd=f"python3 {os.path.abspath(__file__)} ir {bridge} {sync} {pool} {ports}"

    if not os.path.exists(unit_path):
        with open(unit_path,"w") as f:
            f.write(f"""[Unit]
Description=MehTunnel IR Service
After=network.target

[Service]
Type=simple
ExecStart={cmd}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")
        os.system("systemctl daemon-reload")
        os.system(f"systemctl enable {service_name}")
        os.system(f"systemctl start {service_name}")
        print(f"\n✅ Service {service_name} created and started")
        print("You can safely close the terminal. The tunnel will keep running.")
    else:
        print(f"\n✅ Service already exists. Starting it...")
        os.system(f"systemctl start {service_name}")

if __name__=="__main__":
    main()
