#!/usr/bin/env python3
"""
Refined Server Freshness Test Harness
Validates:
1. Robust PID discovery on port 8000
2. Clean process tree termination with taskkill fallback
3. Non-blocking socket drain polling
4. Detached uvicorn spawning
5. Robust HTTP /api/heartbeat polling with 35s timeout
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional

import psutil

ROOT_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin")
PORT = 8000
HOST = "127.0.0.1"
HEARTBEAT_URL = f"http://{HOST}:{PORT}/api/heartbeat"


def find_pids_on_port(port: int = PORT) -> List[int]:
    """Find all PIDs currently holding the specified TCP port."""
    pids = set()
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr and conn.laddr.port == port and conn.pid:
                pids.add(conn.pid)
    except Exception:
        # Fallback to per-process connection inspection
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                for conn in proc.connections(kind="tcp"):
                    if conn.laddr and conn.laddr.port == port:
                        pids.add(proc.pid)
            except Exception:
                continue

    # Fallback to netstat on Windows
    if not pids and sys.platform == "win32":
        try:
            out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
            for line in out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    try:
                        pids.add(int(parts[-1]))
                    except ValueError:
                        pass
        except Exception:
            pass

    return list(pids)


def kill_process_tree(pid: int, timeout: float = 3.0) -> bool:
    """Terminate a process and all its children cleanly."""
    if not psutil.pid_exists(pid):
        return True

    # On Windows, taskkill /F /T terminates entire process tree cleanly in kernel
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5.0)
        except Exception:
            pass

    if not psutil.pid_exists(pid):
        return True

    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception:
                pass
        parent.kill()
    except Exception:
        pass

    return not psutil.pid_exists(pid)


def wait_for_socket_drain(port: int = PORT, host: str = HOST, timeout: float = 5.0) -> bool:
    """Poll until socket is completely released and no process is listening on the port."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pids = find_pids_on_port(port)
        if pids:
            time.sleep(0.1)
            continue

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                res = s.connect_ex((host, port))
                if res != 0:
                    time.sleep(0.2)  # OS TCP stack settle delay
                    return True
        except OSError:
            time.sleep(0.2)
            return True

        time.sleep(0.1)
    return False


def spawn_detached_uvicorn(root_dir: Path = ROOT_DIR, port: int = PORT) -> Optional[int]:
    """Spawn detached uvicorn process and return PID."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "agent_city.server:app",
        "--host",
        HOST,
        "--port",
        str(port),
    ]

    flags = 0
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        cwd=str(root_dir),
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    return proc.pid


def wait_for_heartbeat(url: str = HEARTBEAT_URL, timeout: float = 35.0, interval: float = 0.5) -> bool:
    """Poll health probe until HTTP 200 with JSON is returned."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VisualDocCapture-Probe/1.0"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    if isinstance(body, dict):
                        return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def ensure_server_fresh(port: int = PORT, host: str = HOST, timeout: float = 35.0) -> bool:
    """Ensure web server on port 8000 is cleanly restarted and healthy."""
    pids = find_pids_on_port(port)
    if pids:
        print(f"[FreshServer] Terminating existing server PIDs on port {port}: {pids}")
        for pid in pids:
            kill_process_tree(pid)

    drained = wait_for_socket_drain(port, host, timeout=5.0)
    if not drained:
        print(f"[FreshServer] ERROR: Port {port} failed to drain!")
        return False

    spawned_pid = spawn_detached_uvicorn(ROOT_DIR, port)
    print(f"[FreshServer] Spawned fresh uvicorn server (PID {spawned_pid})")

    healthy = wait_for_heartbeat(HEARTBEAT_URL, timeout=timeout)
    if healthy:
        active_pids = find_pids_on_port(port)
        print(f"[FreshServer] [OK] Server fresh and responding on {HEARTBEAT_URL} (PIDs: {active_pids})")
        return True
    else:
        print(f"[FreshServer] [FAIL] Server failed to become healthy within {timeout}s")
        return False


if __name__ == "__main__":
    t0 = time.time()
    success = ensure_server_fresh()
    print(f"Cycle completed in {time.time() - t0:.2f}s. Success: {success}")
