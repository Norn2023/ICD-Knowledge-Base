"""
ICD 知识库看门狗 — 自动监控 & 重启 4 个后台服务器

监控 8765/8766/8768/8769 端口的 TCP 连通性，
发现服务挂掉自动重启，并记录日志。

用法:  python watchdog.py          (前台运行)
       python watchdog.py --daemon  (后台静默运行，Windows)
"""
import os, sys, time, socket, subprocess, json, signal
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ─── 服务定义 ───────────────────────────────────────────
SERVICES = [
    {"port": 8765, "name": "ICD 编码知识库",     "cmd": [sys.executable, "server_gzip.py"],         "cwd": str(SCRIPT_DIR / "web")},
    {"port": 8766, "name": "医保药物目录",       "cmd": [sys.executable, "server.py"],              "cwd": str(SCRIPT_DIR / "drug")},
    {"port": 8768, "name": "价格立项指南映射",   "cmd": [sys.executable, "server.py"],              "cwd": str(SCRIPT_DIR / "4way-mapping")},
    {"port": 8769, "name": "医学文献知识库",     "cmd": [sys.executable, "server.py", "8769"],      "cwd": str(SCRIPT_DIR / "literature")},
]


# ─── 工具函数 ───────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line, flush=True)
    with open(str(LOG_DIR / "watchdog.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def port_open(port, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except:
        return False


def start_server(svc):
    logfile = str(LOG_DIR / f"svc_{svc['port']}.log")
    lf = open(logfile, "a", encoding="utf-8")
    lf.write(f"\n--- START at {datetime.now().isoformat()} ---\n")
    lf.flush()

    proc = subprocess.Popen(
        svc["cmd"],
        cwd=svc["cwd"],
        stdout=lf,
        stderr=lf,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    log(f">> START {svc['name']} :{svc['port']} PID={proc.pid}")
    return proc, lf


# ─── 主循环 ─────────────────────────────────────────────
def main():
    log("=" * 45)
    log("  Watchdog started")
    log("=" * 45)

    procs = {}
    logfiles = {}

    # 启动所有服务
    for svc in SERVICES:
        p, lf = start_server(svc)
        procs[svc["port"]] = p
        logfiles[svc["port"]] = lf
        time.sleep(1.5)

    # 等待初始化
    log("Waiting for services to initialize...")
    time.sleep(5)
    for svc in SERVICES:
        ok = port_open(svc["port"])
        status = "OK" if ok else "FAIL"
        log(f"  INIT {svc['name']} :{svc['port']} -> {status}")

    # 监控循环
    interval = 30
    while True:
        time.sleep(interval)

        for svc in SERVICES:
            port = svc["port"]
            p = procs.get(port)
            lf = logfiles.get(port)
            retcode = p.poll()
            is_dead = retcode is not None
            is_open = port_open(port)

            if is_dead:
                log(f"!! CRASH {svc['name']} :{port} PID={p.pid} EXIT={retcode} 重启中...")
            elif not is_open:
                log(f"!! STUCK {svc['name']} :{port} PID={p.pid} 端口无响应, 杀掉重启...")
                p.kill()
                p.wait(timeout=5)
                time.sleep(2)
            else:
                continue  # 正常

            # 关闭旧日志文件
            if lf and not lf.closed:
                lf.close()

            # 重启
            p_new, lf_new = start_server(svc)
            procs[port] = p_new
            logfiles[port] = lf_new
            time.sleep(3)
            recovered = port_open(port)
            log(f"  -> {'OK' if recovered else 'FAIL'} {svc['name']} :{port}")

        # 每日 3:00 清理日志
        now = datetime.now()
        if now.hour == 3 and now.minute < 5:
            for f in LOG_DIR.glob("*.log"):
                if f.stat().st_size > 5 * 1024 * 1024:
                    f.unlink(missing_ok=True)
                    log(f"~~ 清理日志 {f.name}")
                elif (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days > 30:
                    f.unlink(missing_ok=True)
                    log(f"~~ 清理旧日志 {f.name}")


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        # 后台模式: 用 DETACHED_PROCESS 标志启动自身
        if sys.platform == "win32":
            import subprocess as _sp
            _sp.Popen(
                [sys.executable, __file__],
                creationflags=_sp.DETACHED_PROCESS | _sp.CREATE_NO_WINDOW,
                stdout=open(os.devnull, "w"),
                stderr=open(os.devnull, "w"),
                stdin=open(os.devnull, "w"),
            )
            print("Watchdog started in background (daemon mode).")
            sys.exit(0)
        else:
            print("Daemon mode is Windows-only. Run without --daemon on Linux/Mac.")

    try:
        main()
    except KeyboardInterrupt:
        log("Watchdog stopped by user.")
        # 清理子进程
        for svc in SERVICES:
            p = procs.get(svc["port"]) if 'procs' in dir() else None
            if p and p.poll() is None:
                p.terminate()
        sys.exit(0)
