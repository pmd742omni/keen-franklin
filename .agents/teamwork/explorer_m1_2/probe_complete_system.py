import os
import sys
import time
import socket
import struct
import shutil
import tempfile
import subprocess
import urllib.request
from pathlib import Path

ROOT_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin")
WORK_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")
EDGE_BIN = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
HOST = "127.0.0.1"
PORT = 8000

def get_pid_on_port(port: int = PORT):
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                return int(parts[-1])
    except Exception:
        pass
    return None

def kill_process_tree(pid: int):
    if pid:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_for_heartbeat(timeout=30.0):
    t0 = time.time()
    url = f"http://{HOST}:{PORT}/api/heartbeat"
    while time.time() - t0 < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "M1-Probe/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True, time.time() - t0
        except Exception:
            pass
        time.sleep(0.5)
    return False, time.time() - t0

def inspect_png(file_path: Path):
    if not file_path.exists():
        return {"valid": False, "error": "Missing file"}
    size = file_path.stat().st_size
    if size < 24:
        return {"valid": False, "error": "Too small"}
    with open(file_path, "rb") as f:
        header = f.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return {"valid": False, "error": "Invalid PNG header"}
    w, h = struct.unpack(">II", header[16:24])
    return {"valid": True, "width": w, "height": h, "size_bytes": size, "is_1080p": (w == 1920 and h == 1080)}

def capture(url: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    profile = tempfile.mkdtemp(prefix="edge_capture_test_")
    cmd = [
        str(EDGE_BIN),
        "--headless=new",
        "--window-size=1920,1080",
        "--virtual-time-budget=3000",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile}",
        f"--screenshot={str(output_path)}",
        url
    ]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captured = False
    try:
        while time.time() - t0 < 30.0:
            if output_path.exists() and output_path.stat().st_size > 10000:
                time.sleep(0.5)
                captured = True
                break
            time.sleep(0.5)
    finally:
        kill_process_tree(proc.pid)
        shutil.rmtree(profile, ignore_errors=True)
    
    elapsed = time.time() - t0
    return captured, elapsed, inspect_png(output_path) if captured else {}

print("=== Probing Server & Dual Capture ===")
pid = get_pid_on_port()
print(f"Current PID on port 8000: {pid}")

healthy, dur = wait_for_heartbeat(timeout=3.0)
if not healthy:
    print(f"Server not responding, launching uvicorn detached...")
    spawn_cmd = [sys.executable, "-m", "uvicorn", "agent_city.server:app", "--host", HOST, "--port", str(PORT)]
    flags = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW
    p = subprocess.Popen(spawn_cmd, cwd=str(ROOT_DIR), creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Spawned server PID: {p.pid}")
    healthy, dur = wait_for_heartbeat(timeout=30.0)
    print(f"Server healthy: {healthy} after {dur:.2f}s")
else:
    print(f"Server is currently healthy!")

if healthy:
    # 1. Capture Grove
    grove_png = WORK_DIR / "final_grove_1080p.png"
    c1, d1, info1 = capture(f"http://{HOST}:{PORT}/", grove_png)
    print(f"Grove capture: {c1} in {d1:.2f}s -> {info1}")

    # 2. Capture Portal
    portal_png = WORK_DIR / "final_portal_1080p.png"
    c2, d2, info2 = capture(f"http://{HOST}:{PORT}/evolution", portal_png)
    print(f"Portal capture: {c2} in {d2:.2f}s -> {info2}")
else:
    print("ERROR: Server failed to become healthy.")
