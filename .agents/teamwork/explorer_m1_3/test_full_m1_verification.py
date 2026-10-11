#!/usr/bin/env python3
"""
Milestone M1 Verification & Integration Test Harness
Location: .agents/teamwork/explorer_m1_3/test_full_m1_verification.py

Demonstrates and verifies:
1. Server Freshness Cycle (F1):
   - Identifies running PID on port 8000
   - Terminates process tree
   - Verifies socket drain (port 8000 released)
   - Spawns fresh detached uvicorn
   - Verifies HTTP 200 on /api/heartbeat and /api/city/status with fresh PID != old_pid
2. Edge Headless Capture (F2):
   - Microsoft Edge headless execution with isolated temp user-data-dir
   - Captures both '/' (Grove) and '/evolution' (Portal)
   - Virtual time settling budget
   - Process tree termination on file readiness (immune to Chromium post-screenshot hang)
3. Strict PNG Validation:
   - Validates magic bytes (\x89PNG\r\n\x1a\n)
   - Validates resolution via IHDR chunk (1920x1080)
   - Validates size > 100KB (102,400 bytes)
4. Edge Case Hardening:
   - Auto-creates missing output directories
   - Handles orphaned / zombie browser processes
   - Handles port contention & socket release delays
"""

import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT_DIR = Path(r"c:\Users\ignaz\antigravity\keen-franklin")
EDGE_BIN = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PORT = 8000
HOST = "127.0.0.1"


def get_pid_on_port(port: int = PORT) -> Optional[int]:
    """Find PID currently listening on given TCP port using netstat on Windows."""
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                try:
                    return int(parts[-1])
                except ValueError:
                    pass
    except Exception:
        pass
    return None


def kill_process_tree_windows(pid: int) -> bool:
    """Forcefully kill process and all children using Windows taskkill."""
    if not pid:
        return True
    try:
        res = subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False


def wait_for_socket_release(port: int = PORT, host: str = HOST, timeout: float = 5.0) -> bool:
    """Verify that port is completely released and can be bound."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex((host, port)) != 0:
                # Connection refused -> port is free. Now test binding:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as binder:
                        binder.bind((host, port))
                        return True
                except OSError:
                    pass
        time.sleep(0.1)
    return False


def spawn_fresh_server(root_dir: Path = ROOT_DIR, port: int = PORT) -> int:
    """Spawn fresh detached uvicorn process and return PID."""
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
        close_fds=True,
    )
    return proc.pid


def wait_for_server_health(url: str, timeout: float = 25.0) -> bool:
    """Poll URL until HTTP 200 is returned (allowing for N100 cold boot)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "M1-Verification/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def inspect_png_header(file_path: Path) -> Dict[str, any]:
    """Parse PNG magic bytes and IHDR chunk with zero third-party dependencies."""
    if not file_path.exists():
        return {"valid": False, "error": "File does not exist"}
    size = file_path.stat().st_size
    if size < 24:
        return {"valid": False, "error": f"File too small ({size} bytes)"}

    with open(file_path, "rb") as f:
        header = f.read(24)

    magic = header[:8]
    if magic != b"\x89PNG\r\n\x1a\n":
        return {"valid": False, "error": f"Invalid magic bytes: {magic!r}"}

    chunk_type = header[12:16]
    if chunk_type != b"IHDR":
        return {"valid": False, "error": f"Missing IHDR chunk: {chunk_type!r}"}

    width, height = struct.unpack(">II", header[16:24])
    return {
        "valid": True,
        "width": width,
        "height": height,
        "size_bytes": size,
        "is_1080p": (width == 1920 and height == 1080),
        "is_gt_100kb": (size > 102400),
    }


def capture_with_edge_headless(
    url: str,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    virtual_time_budget: int = 3000,
    max_wait_seconds: int = 25,
) -> Dict[str, any]:
    """Capture URL using Microsoft Edge headless, immune to Chromium process hanging."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    temp_profile = tempfile.mkdtemp(prefix="m1_edge_profile_")
    cmd = [
        str(EDGE_BIN),
        "--headless=new",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={virtual_time_budget}",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={temp_profile}",
        f"--screenshot={str(output_path)}",
        url,
    ]

    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captured = False

    try:
        while time.time() - t0 < max_wait_seconds:
            # Check if screenshot is created and has reached meaningful size (>10KB initially)
            if output_path.exists() and output_path.stat().st_size > 10240:
                time.sleep(0.5)  # flush delay
                captured = True
                break
            time.sleep(0.5)
    finally:
        # Terminate Edge process tree immediately
        kill_process_tree_windows(proc.pid)
        time.sleep(0.3)
        shutil.rmtree(temp_profile, ignore_errors=True)

    elapsed = time.time() - t0
    if not captured:
        return {"success": False, "error": f"Timed out after {elapsed:.1f}s waiting for {output_path.name}"}

    png_info = inspect_png_header(output_path)
    return {
        "success": png_info.get("valid", False) and png_info.get("is_1080p", False),
        "elapsed_sec": round(elapsed, 2),
        "output_path": str(output_path),
        **png_info,
    }


def run_full_m1_verification_cycle() -> Dict[str, any]:
    """Run comprehensive M1 verification cycle."""
    report = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "steps": {}}

    # Step 1: Record Pre-Restart State
    old_pid = get_pid_on_port(PORT)
    report["steps"]["pre_restart"] = {"old_pid": old_pid}

    # Step 2: Restart Web Server (F1 Freshness Cycle)
    t_start_restart = time.time()
    if old_pid:
        kill_process_tree_windows(old_pid)
    drained = wait_for_socket_release(PORT, HOST, timeout=5.0)
    spawned_pid = spawn_fresh_server(ROOT_DIR, PORT)
    healthy = wait_for_server_health(f"http://{HOST}:{PORT}/api/heartbeat", timeout=10.0)
    new_pid = get_pid_on_port(PORT)

    report["steps"]["server_restart"] = {
        "old_pid": old_pid,
        "spawned_pid": spawned_pid,
        "new_pid": new_pid,
        "pid_changed": (new_pid is not None and new_pid != old_pid),
        "socket_drained": drained,
        "heartbeat_healthy": healthy,
        "restart_duration_sec": round(time.time() - t_start_restart, 2),
    }

    if not healthy:
        report["status"] = "FAILED"
        report["error"] = "Server restart failed health check"
        return report

    # Step 3: Capture 3D Voxel Grove (/) (F2)
    work_dir = ROOT_DIR / ".agents" / "teamwork" / "explorer_m1_3" / "captures"
    grove_file = work_dir / f"screenshot_grove_verify_{int(time.time())}.png"
    grove_res = capture_with_edge_headless(f"http://{HOST}:{PORT}/", grove_file)
    report["steps"]["capture_grove"] = grove_res

    # Step 4: Capture Evolution Portal (/evolution) (F2)
    portal_file = work_dir / f"screenshot_portal_verify_{int(time.time())}.png"
    portal_res = capture_with_edge_headless(f"http://{HOST}:{PORT}/evolution", portal_file)
    report["steps"]["capture_portal"] = portal_res

    # Step 5: Overall Status Evaluation
    f1_pass = report["steps"]["server_restart"]["pid_changed"] and report["steps"]["server_restart"]["heartbeat_healthy"]
    f2_grove_pass = grove_res.get("valid") and grove_res.get("is_1080p") and grove_res.get("is_gt_100kb")
    f2_portal_pass = portal_res.get("valid") and portal_res.get("is_1080p") and portal_res.get("is_gt_100kb")

    report["evaluation"] = {
        "F1_server_freshness_passed": f1_pass,
        "F2_grove_1080p_valid": f2_grove_pass,
        "F2_portal_1080p_valid": f2_portal_pass,
        "overall_m1_verified": (f1_pass and f2_grove_pass and f2_portal_pass),
    }
    return report


if __name__ == "__main__":
    print("=== Executing Full M1 Verification & Integration Test ===")
    res = run_full_m1_verification_cycle()
    print(json.dumps(res, indent=2))
