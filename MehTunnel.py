#!/usr/bin/env python3
import os, sys, time, threading, socket, struct, subprocess, resource
from queue import Queue, Empty

# --------- Tunables ----------
DIAL_TIMEOUT = 5
KEEPALIVE_SECS = 20
SOCKBUF = 8*1024*1024
BUF_COPY = 256*1024
SYNC_INTERVAL = 3

def auto_pool_size(role="ir"):
    try:
        env_pool=int(os.environ.get("MEHTUNNEL_POOL","0"))
        if env_pool>0: return env_pool
    except: pass
    try:
        soft, hard=resource.getrlimit(resource.RLIMIT_NOFILE)
        nofile=soft if soft>0 else 1024
    except: nofile=1024
    mem_mb=0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb=int(line.split()[1])
                    mem_mb=mem_kb//1024
                    break
    except: mem_mb=0
    reserve=500
    fd_budget=max(0,nofile-reserve)
    frac=0.22 if role.lower().startswith("ir") else 0.30
    fd_based=int(fd_budget*frac)
    ram_based=int((mem_mb/1024)*250) if mem_mb else 500
    pool=min(fd_based, ram_based)
    return max(100,min(pool,2000))

def tune_tcp(sock):
    try: sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
    except: pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,SOCKBUF)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,SOCKBUF)
    except: pass
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,1)
        if hasattr(socket,"TCP_KEEPIDLE"): sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPIDLE,KEEPALIVE_SECS)
        if hasattr(socket,"TCP_KEEPINTVL"): sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPINTVL,KEEPALIVE_SECS)
        if hasattr(socket,"TCP_KEEPCNT"): sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPCNT,3)
    except: pass

def dial_tcp(host,port):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tune_tcp(s)
    s.settimeout(DIAL_TIMEOUT)
    s.connect((host,port))
    s.settimeout(None)
    return s

def pipe(a,b):
    buf=bytearray(BUF_COPY)
    try:
        while True:
            n=a.recv_into(buf)
            if n<=0: break
            b.sendall(memoryview(buf)[:n])
    except: pass
    finally:
        try: a.shutdown(socket.SHUT_RD)
        except: pass
        try: b.shutdown(socket.SHUT_WR)
        except: pass

def bridge(a,b):
    t1=threading.Thread(target=pipe,args=(a,b),daemon=True)
    t2=threading.Thread(target=pipe,args=(b,a),daemon=True)
    t1.start(); t2.start()
    t1.join(); t2.join()
    try: a.close(); b.close()
    except: pass

# --------- IR Mode ----------
def ir_mode(bridge_port,sync_port,pool_size,auto_sync,manual_ports_csv):
    pool=Queue(maxsize=pool_size*2)
    active={}
    lock=threading.Lock()
    def accept_bridge():
        srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        srv.bind(("0.0.0.0",bridge_port))
        srv.listen(16384)
        print(f"[IR] Bridge listening on {bridge_port}")
        while True:
            c,_=srv.accept()
            tune_tcp(c)
            try: pool.put(c,block=False)
            except: c.close()
    def handle_user(u,target_port):
        tune_tcp(u)
        deadline=time.time()+5
        europe=None
        while time.time()<deadline:
            try: cand=pool.get(timeout=max(0.1,deadline-time.time()))
            except Empty: break
            europe=cand if cand else None
            if europe: break
        if not europe: u.close(); return
        try:
            europe.settimeout(2)
            europe.sendall(struct.pack("!H",target_port))
            europe.settimeout(None)
        except:
            try: u.close()
            except: pass
            try: europe.close()
            except: pass
            return
        bridge(u,europe)
    def open_port(p):
        with lock:
            if p in active: return
            active[p]=True
        try:
            srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            srv.bind(("0.0.0.0",p))
            srv.listen(16384)
        except Exception as e:
            with lock: active.pop(p,None)
            print(f"[IR] Cannot open port {p}: {e}")
            return
        print(f"[IR] Port Active: {p}")
        def accept_users():
            while True:
                u,_=srv.accept()
                threading.Thread(target=handle_user,args=(u,p),daemon=True).start()
        threading.Thread(target=accept_users,daemon=True).start()
    def sync_listener():
        srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        srv.bind(("0.0.0.0",sync_port))
        srv.listen(1024)
        print(f"[IR] Sync listening on {sync_port} (AutoSync)")
        while True:
            c,_=srv.accept()
            def handle_sync(conn):
                try:
                    h=conn.recv(1)
                    if not h: return
                    count=h[0]
                    for _ in range(count):
                        pd=conn.recv(2)
                        if not pd: return
                        target=struct.unpack("!H",pd)[0]
                        open_port(target)
                except: pass
                finally:
                    try: conn.close()
                    except: pass
            threading.Thread(target=handle_sync,args=(c,),daemon=True).start()

    threading.Thread(target=accept_bridge,daemon=True).start()
    if auto_sync: threading.Thread(target=sync_listener,daemon=True).start()
    else:
        ports=[]
        if manual_ports_csv.strip():
            for part in manual_ports_csv.split(","):
                try: ports.append(int(part.strip()))
                except: pass
        for p in ports: open_port(p)
        print("[IR] Manual ports opened.")
    print(f"[IR] Running | bridge={bridge_port} sync={sync_port} pool={pool_size} autoSync={auto_sync}")
    while True: time.sleep(3600)

# --------- Menu ----------
def main():
    print("================================")
    print("        MehTunnel Manager")
    print("================================")
    mode=input("Select mode (1=EU,2=IR): ").strip()
    if mode=="1":
        iran_ip=input("EU IP (use Iran exit IP if needed): ")
        bridge=int(input("Bridge port [4444]: ") or "4444")
        sync=int(input("Sync port [5555]: ") or "5555")
        pool=auto_pool_size("eu")
        print(f"[AUTO] role=EU pool={pool}")
        print("Only IR mode supported for stable persistent tunnel.")
        sys.exit(0)
    elif mode=="2":
        bridge=int(input("IR -> Bridge port [4444]: ") or "4444")
        sync=int(input("Sync port [5555]: ") or "5555")
        yn=input("Auto-sync ports from EU? (y/n): ").lower() or "y"
        if yn=="y": auto_sync=True; manual_ports=""
        else: auto_sync=False; manual_ports=input("Manual ports CSV (80,443,...): ")
        pool=auto_pool_size("ir")
        print(f"[AUTO] role=IR pool={pool}")
        ir_mode(bridge,sync,pool,auto_sync,manual_ports)
    else:
        print("Invalid selection.")
        sys.exit(1)

if __name__=="__main__":
    main()
