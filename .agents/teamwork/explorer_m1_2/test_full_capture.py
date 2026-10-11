import os
import sys
import time
import socket
import struct
import shutil
import tempfile
import subprocess
from pathlib import Path

# Paths
root_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin")
work_dir = Path(r"c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_2")

def is_port_open(port: int = 8000) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False

def find_edge() -> str:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    w = shutil.which("msedge") or shutil.which("msedge.exe")
    if w and os.path.exists(w):
        return w
    raise FileNotFoundError("Microsoft Edge executable not found")

def get_png_dimensions(filepath: Path):
    with open(filepath, "rb") as f:
        data = f.read(24)
        if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w, h
    return None, None

def capture_edge_bulletproof(url: str, output_path: Path, timeout: float = 30.0) -> bool:
    edge_bin = find_edge()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    user_data_dir = tempfile.mkdtemp(prefix="edge_capture_profile_")

    cmd = [
        edge_bin,
        "--headless=new",
        "--window-size=1920,1080",
        "--virtual-time-budget=3000",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={user_data_dir}",
        f"--screenshot={str(output_path)}",
        url
    ]

    print(f"Launching Edge headless for {url}...")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captured = False

    try:
        # Poll for file creation
        while time.time() - t0 < timeout:
            if output_path.exists() and output_path.stat().st_size > 10000:
                captured = True
                print(f"Screenshot detected in {time.time() - t0:.2f}s! Size: {output_path.stat().st_size} bytes")
                break
            time.sleep(0.5)

        # Allow 500ms for file handle flush
        time.sleep(0.5)

    finally:
        # Guaranteed process tree cleanup
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Cleanup error: {e}")

        # Clean temporary user profile
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:
            pass

    return captured

print("Checking server status on port 8000...")
server_proc = None
if not is_port_open(8000):
    print("Port 8000 closed. Spawning server for test...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agent_city.server:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(root_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # Wait for server to boot
    for _ in range(40):
        if is_port_open(8000):
            print("Server is up!")
            break
        time.sleep(0.5)

try:
    # Test capture 1: 3D Voxel Grove
    grove_png = work_dir / "blueprint_grove_test.png"
    ok1 = capture_edge_bulletproof("http://127.0.0.1:8000/", grove_png, timeout=30.0)
    w1, h1 = get_png_dimensions(grove_png) if ok1 else (None, None)
    print(f"Grove capture: {ok1}, Dims: {w1}x{h1}, Size: {grove_png.stat().st_size if ok1 else 0}")

    # Test capture 2: Evolution Portal
    portal_png = work_dir / "blueprint_portal_test.png"
    ok2 = capture_edge_bulletproof("http://127.0.0.1:8000/evolution", portal_png, timeout=30.0)
    w2, h2 = get_png_dimensions(portal_png) if ok2 else (None, None)
    print(f"Portal capture: {ok2}, Dims: {w2}x{h2}, Size: {portal_png.stat().st_size if ok2 else 0}")

finally:
    # We do NOT kill server_proc if other agents might need it, or we leave it alive
    print("Test run completed.")
