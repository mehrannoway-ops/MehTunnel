#!/usr/bin/env python3
import os, sys, time, socket, struct, threading, resource
from queue import Queue, Empty

# ---------------- Tunables ----------------
DIAL_TIMEOUT = 5
KEEPALIVE_SECS = 20
SOCKBUF = 8*1024*1024
BUF_COPY = 256*1024
POOL_WAIT = 5
SYNC_INTERVAL = 3

# --------- Pool size calculation ----------
def auto_pool_size(role="ir"):
    try:
        env_pool = int(os.environ.get("MEHTUNNEL_POOL","0"))
        if env_pool>0: return env_pool
    except: pass
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        nofile = soft if soft>0 else 1024
    except: nofile=1024
    try:
        with open("/proc/meminfo","r") as f:
            mem_mb = int(next(l for l in f if l.startswith("MemTotal")).split()[1])//1024
    except: mem_mb=0
    reserve=500
    fd_budget=max(0,nofile-reserve)
    frac = 0.22 if role.lower().startswith("ir") else 0.3
    fd_based=int(fd_budget*frac)
    ram_based=int((mem_mb/1024)*250) if mem_mb else 500
    pool=min(fd_based, ram_based)
    return max(100, min(pool,2000))

# --------- TCP helpers ----------
def tune_tcp(s):
    try: s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
    except: pass
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,SOCKBUF)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,SOCKBUF)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,1)
        if hasattr(socket,"TCP_KEEPIDLE"): s.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPIDLE,KEEPALIVE_SECS)
        if hasattr(socket,"TCP_KEEPINTVL"): s.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPINTVL,KEEPALIVE_SECS)
        if hasattr(socket,"TCP_KEEPCNT"): s.setsockopt(socket.IPPROTO_TCP,socket.TCP_KEEPCNT,3)
    except: pass

def dial_tcp(host,port):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tune_tcp(s)
    s.settimeout(DIAL_TIMEOUT)
    s.connect((host,port))
    s.settimeout(None)
    return s

def recv_exact(sock,n):
    data=bytearray()
    while len(data)<n:
        chunk=sock.recv(n-len(data))
        if not chunk: return None
        data.extend(chunk)
    return bytes(data)

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
    try: a.close()
    except: pass
    try: b.close()
    except: pass

# --------- EU mode ----------
def eu_mode(iran_ip,bridge_port,sync_port,pool_size):
    def sync_loop():
        while True:
            try: c=dial_tcp(iran_ip,sync_port)
            except: time.sleep(SYNC_INTERVAL); continue
            try:
                while True:
                    ports=[]
                    payload=bytes([len(ports)])+b"".join(struct.pack("!H",p) for p in ports)
                    c.settimeout(2); c.sendall(payload); c.settimeout(None)
                    time.sleep(SYNC_INTERVAL)
            except: 
                try: c.close()
                except: pass
                time.sleep(SYNC_INTERVAL)
    def worker():
        while True:
            try:
                conn=dial_tcp(iran_ip,bridge_port)
                hdr=recv_exact(conn,2)
                if not hdr: conn.close(); continue
                target_port=struct.unpack("!H",hdr)[0]
                local=dial_tcp("127.0.0.1",target_port)
                bridge(conn,local)
            except: time.sleep(0.2)
    threading.Thread(target=sync_loop,daemon=True).start()
    for _ in range(pool_size): threading.Thread(target=worker,daemon=True).start()
    print(f"[EU] IR={iran_ip} bridge={bridge_port} sync={sync_port} pool={pool_size}")
    while True: time.sleep(3600)

# --------- IR mode ----------
def ir_mode(bridge_port,sync_port,pool_size,auto_sync,manual_ports_csv):
    pool=Queue(maxsize=pool_size*2)
    active={}
    active_lock=threading.Lock()
    def accept_bridge():
        srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        srv.bind(("0.0.0.0",bridge_port)); srv.listen(16384)
        print(f"[IR] Bridge listening on {bridge_port}")
        while True:
            try: c,_=srv.accept()
            except: time.sleep(0.2); continue
            tune_tcp(c)
            try: pool.put(c,block=False)
            except: c.close()
    threading.Thread(target=accept_bridge,daemon=True).start()
    if auto_sync: print(f"[IR] Auto-sync active"); time.sleep(3600)
    else:
        ports=[]
        if manual_ports_csv.strip(): ports=[int(p) for p in manual_ports_csv.split(",") if 1<=int(p)<=65535]
        print(f"[IR] Manual ports: {ports}"); time.sleep(3600)

# --------- Main ----------
def main():
    mode=input("Select mode (1=EU,2=IR): ").strip()
    if mode=="1":
        iran_ip=input("Iran IP: ").strip()
        bridge=int(input("Bridge port [4444]: ") or "4444")
        sync=int(input("Sync port [5555]: ") or "5555")
        pool=auto_pool_size("eu")
        eu_mode(iran_ip,bridge,sync,pool)
    elif mode=="2":
        bridge=int(input("Bridge port [4444]: ") or "4444")
        sync=int(input("Sync port [5555]: ") or "5555")
        yn=input("Auto-sync from EU? (y/n): ").strip().lower()
        pool=auto_pool_size("ir")
        if yn=="y": ir_mode(bridge,sync,pool,True,"")
        else:
            ports=input("Manual ports CSV (80,443,..): ").strip()
            ir_mode(bridge,sync,pool,False,ports)
    else:
        print("Invalid selection."); sys.exit(1)

if __name__=="__main__": main()
