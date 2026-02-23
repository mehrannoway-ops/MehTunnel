#!/usr/bin/env python3
import os, sys, time, socket, struct, threading, subprocess, re, resource
from queue import Queue, Empty

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
        if env_pool > 0:
            return env_pool
    except Exception:
        pass
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        nofile = soft if soft and soft > 0 else 1024
    except Exception:
        nofile = 1024
    mem_mb = 0
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb = int(line.split()[1])
                    mem_mb = mem_kb // 1024
                    break
    except Exception:
        mem_mb = 0
    reserve = 500
    fd_budget = max(0, nofile - reserve)
    frac = 0.22 if role.lower().startswith("ir") else 0.30
    fd_based = int(fd_budget * frac)
    ram_based = int((mem_mb / 1024) * 250) if mem_mb else 500
    pool = min(fd_based, ram_based)
    if pool < 100:
        pool = 100
    if pool > 2000:
        pool = 2000
    return pool

def tune_tcp(sock: socket.socket):
    try: sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception: pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKBUF)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKBUF)
    except Exception: pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, "TCP_KEEPIDLE"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, KEEPALIVE_SECS)
        if hasattr(socket, "TCP_KEEPINTVL"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, KEEPALIVE_SECS)
        if hasattr(socket, "TCP_KEEPCNT"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
    except Exception:
        pass

def dial_tcp(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tune_tcp(s)
    s.settimeout(DIAL_TIMEOUT)
    s.connect((host, port))
    s.settimeout(None)
    return s

def recv_exact(sock: socket.socket, n: int):
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)

def pipe(a: socket.socket, b: socket.socket):
    buf = bytearray(BUF_COPY)
    try:
        while True:
            n = a.recv_into(buf)
            if n <= 0: break
            b.sendall(memoryview(buf)[:n])
    except Exception: pass
    finally:
        try: a.close()
        except Exception: pass
        try: b.close()
        except Exception: pass

def bridge(a: socket.socket, b: socket.socket):
    t1 = threading.Thread(target=pipe, args=(a,b), daemon=True)
    t2 = threading.Thread(target=pipe, args=(b,a), daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()

# --------- EU Mode ----------
def eu_mode(iran_ip, bridge_port, sync_port, pool_size):
    def port_sync_loop():
        while True:
            try:
                c = dial_tcp(iran_ip, sync_port)
            except Exception:
                time.sleep(SYNC_INTERVAL)
                continue
            try:
                while True:
                    time.sleep(SYNC_INTERVAL)
            except Exception:
                try: c.close()
                except Exception: pass
                time.sleep(SYNC_INTERVAL)

    def reverse_link_worker():
        delay = 0.2
        while True:
            try:
                conn = dial_tcp(iran_ip, bridge_port)
                conn.close()
                delay = 0.2
            except Exception:
                time.sleep(delay)
                delay = min(delay*2, 5.0)

    threading.Thread(target=port_sync_loop, daemon=True).start()
    for _ in range(pool_size):
        threading.Thread(target=reverse_link_worker, daemon=True).start()
    print(f"[EU] Running | IRAN={iran_ip} bridge={bridge_port} sync={sync_port} pool={pool_size}")
    while True:
        time.sleep(3600)

# --------- IR Mode ----------
def ir_mode(bridge_port, sync_port, pool_size, auto_sync, manual_ports_csv):
    pool = Queue(maxsize=pool_size*2)
    active = {}
    active_lock = threading.Lock()
    def open_port(p:int):
        print(f"[IR] Port Active: {p}")
    for p in manual_ports_csv.split(","):
        try:
            open_port(int(p.strip()))
        except Exception: pass
    print(f"[IR] Running | bridge={bridge_port} sync={sync_port} pool={pool_size} autoSync={auto_sync}")
    while True:
        time.sleep(3600)

# --------- Menu ----------
def read_line(prompt=None):
    if prompt: print(prompt,end="",flush=True)
    s=sys.stdin.readline()
    return s.strip() if s else ""

def main():
    print("\n================================")
    print("        MehTunnel Manager")
    print("================================")
    choice = read_line("Select mode (1=EU,2=IR): ")
    if choice not in ("1","2"):
        print("Invalid mode selection."); sys.exit(1)
    if choice=="1":
        iran_ip=read_line("Iran IP (connect EU to Iran): ")
        bridge=int(read_line("Bridge port [4444]: ") or "4444")
        sync=int(read_line("Sync port [5555]: ") or "5555")
        pool=auto_pool_size("eu")
        print(f"[AUTO] role=EU pool={pool} (override: MEHTUNNEL_POOL)")
        eu_mode(iran_ip, bridge, sync, pool)
    else:
        bridge=int(read_line("IR -> Bridge port [4444]: ") or "4444")
        sync=int(read_line("Sync port [5555]: ") or "5555")
        yn=read_line("Auto-sync ports from EU? (y/n): ").lower() or "y"
        if yn=="y":
            pool=auto_pool_size("ir")
            print(f"[AUTO] role=IR pool={pool} (override: MEHTUNNEL_POOL)")
            ir_mode(bridge, sync, pool, auto_sync=True, manual_ports_csv="")
        else:
            ports=read_line("Manual ports CSV (80,443,...): ")
            pool=auto_pool_size("ir")
            print(f"[AUTO] role=IR pool={pool} (override: MEHTUNNEL_POOL)")
            ir_mode(bridge, sync, pool, auto_sync=False, manual_ports_csv=ports)

if __name__=="__main__":
    main()
