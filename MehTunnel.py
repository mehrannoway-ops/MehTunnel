#!/usr/bin/env python3
import os, sys, time, socket, struct, threading, resource
from queue import Queue, Empty

# --------- Tunables ----------
DIAL_TIMEOUT = 5
KEEPALIVE_SECS = 20
SOCKBUF = 8*1024*1024
BUF_COPY = 256*1024
POOL_WAIT = 5
SYNC_INTERVAL = 3

# --------- Helper functions ----------
def tune_tcp(sock: socket.socket):
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKBUF)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKBUF)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, "TCP_KEEPIDLE"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, KEEPALIVE_SECS)
        if hasattr(socket, "TCP_KEEPINTVL"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, KEEPALIVE_SECS)
        if hasattr(socket, "TCP_KEEPCNT"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
    except Exception: pass

def dial_tcp(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tune_tcp(s)
    s.settimeout(DIAL_TIMEOUT)
    s.connect((host, port))
    s.settimeout(None)
    return s

def pipe(a: socket.socket, b: socket.socket):
    buf = bytearray(BUF_COPY)
    try:
        while True:
            n = a.recv_into(buf)
            if n <= 0: break
            b.sendall(memoryview(buf)[:n])
    except: pass
    finally:
        try: a.close()
        except: pass
        try: b.close()
        except: pass

def bridge(a: socket.socket, b: socket.socket):
    t1 = threading.Thread(target=pipe, args=(a,b), daemon=True)
    t2 = threading.Thread(target=pipe, args=(b,a), daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()

# --------- EU Mode ----------
def eu_mode(iran_ip, bridge_port, sync_port, pool_size):
    print(f"[EU] Running | IRAN={iran_ip} bridge={bridge_port} sync={sync_port} pool={pool_size}")
    while True: time.sleep(3600)

# --------- IR Mode ----------
def ir_mode(bridge_port, sync_port, pool_size, auto_sync, manual_ports_csv):
    pool = Queue(maxsize=pool_size*2)
    active = {}
    active_lock = threading.Lock()

    def accept_bridge():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        srv.bind(("0.0.0.0", bridge_port))
        srv.listen(16384)
        print(f"[IR] Bridge listening on {bridge_port}")
        while True:
            try: c,_ = srv.accept()
            except OSError: time.sleep(0.2); continue
            try: pool.put(c, block=False)
            except: c.close()

    def handle_user(user_sock, target_port):
        try:
            europe = pool.get(timeout=POOL_WAIT)
        except Empty:
            try: user_sock.close()
            except: pass
            return
        try:
            europe.sendall(struct.pack("!H", target_port))
        except:
            try: user_sock.close()
            except: pass
            try: europe.close()
            except: pass
            return
        bridge(user_sock, europe)

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
            with active_lock:
                active.pop(p,None)
            print(f"[IR] Cannot open port {p}: {e}")
            return
        print(f"[IR] Port Active: {p}")
        def accept_users():
            while True:
                try: u,_=srv.accept()
                except OSError: time.sleep(0.2); continue
                try: threading.Thread(target=handle_user,args=(u,p),daemon=True).start()
                except: u.close()
        threading.Thread(target=accept_users,daemon=True).start()

    threading.Thread(target=accept_bridge,daemon=True).start()

    if not auto_sync:
        ports=[]
        if manual_ports_csv.strip():
            for part in manual_ports_csv.split(","):
                try: p=int(part.strip())
                except: continue
                if 1<=p<=65535: ports.append(p)
        for p in ports: open_port(p)
        print("[IR] Manual ports opened.")

    print(f"[IR] Running | bridge={bridge_port} sync={sync_port} pool={pool_size} autoSync={auto_sync}")
    while True: time.sleep(3600)

# --------- Main ----------
if __name__=="__main__":
    mode = os.environ.get("RUN_MODE","IRAN")
    bridge = int(os.environ.get("BRIDGE_PORT", "4444"))
    sync   = int(os.environ.get("SYNC_PORT", "5555"))
    pool   = int(os.environ.get("POOL_SIZE", "115"))

    if mode.upper().startswith("EU"):
        iran_ip = os.environ.get("IRAN_IP","1.2.3.4")
        eu_mode(iran_ip, bridge, sync, pool)
    else:
        is_auto = os.environ.get("IS_AUTO","True") == "True"
        manual_ports = os.environ.get("MANUAL_PORTS","")
        ir_mode(bridge, sync, pool, auto_sync=is_auto, manual_ports_csv=manual_ports)
