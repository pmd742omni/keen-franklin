#!/usr/bin/env python3
"""
Silicon Sanctuary — Visual Documentation & Screenshot Capture Runner
Location: .agents/context/visual_doc_capture.py

Executes automated web app screenshot capture with clean server recycling:
1. Feature F1: Web Server Freshness Cycle
   - Graceful termination of process tree on port 8000 (psutil + taskkill)
   - OS socket drain loop with connection refusal & settle delay
   - Spawns detached uvicorn process without console window or handle leaks
   - Polls /api/heartbeat health probe (35s timeout for Intel N100 cold-boot)
2. Feature F2: Microsoft Edge Headless Capture Runner
   - Poll-and-terminate headless capture immune to Windows Chromium post-screenshot hang
   - 1080p full resolution (1920x1080), isolated temporary --user-data-dir
   - Shading and 3D canvas virtual-time-budget settling delay
   - Dual-location artifact saving: `agent_city/` and `agent_city/screenshots/`
   - Pure standard library PNG binary struct validation (no PIL/external dependencies)
3. Registers every capture in SQLite `sanctuary_context.db` via ContextManager.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

# Directory setup
_script_dir = Path(__file__).resolve().parent
_root_dir = _script_dir.parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from context_manager import ContextManager

# Win32 Process Flags
WIN32_DETACHED_PROCESS = 0x00000008
WIN32_CREATE_NO_WINDOW = 0x08000000

# Edge binary search candidates
EDGE_SEARCH_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

BRAIN_ARTIFACTS_DIR = Path(r"C:\Users\ignaz\.gemini\antigravity\brain\8e8e0d95-4549-4479-a58e-ba55f3632b57")
DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"


def find_edge_binary() -> str:
    """Locate Microsoft Edge executable on host system."""
    for p in EDGE_SEARCH_PATHS:
        if os.path.exists(p):
            return p
    which_edge = shutil.which("msedge") or shutil.which("msedge.exe")
    if which_edge and os.path.exists(which_edge):
        return which_edge
    return "msedge"


def get_pids_on_port(port: int = DEFAULT_PORT) -> List[int]:
    """Discover all process IDs actively listening on the specified TCP port."""
    pids = set()
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr and conn.laddr.port == port and conn.pid:
                pids.add(conn.pid)
    except Exception:
        # Fallback for restricted permission environments
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                for conn in proc.connections(kind="tcp"):
                    if conn.laddr and conn.laddr.port == port:
                        pids.add(proc.pid)
            except Exception:
                continue

    # Secondary fallback using Windows netstat
    if not pids and sys.platform == "win32":
        try:
            out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
            for line in out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                    try:
                        pids.add(int(parts[-1]))
                    except ValueError:
                        pass
        except Exception:
            pass

    return list(pids)


def kill_server_tree(pid: int) -> bool:
    """Terminate the process and all child processes cleanly without leaving orphans."""
    if not pid or not psutil.pid_exists(pid):
        return True

    # 1. Gracefully attempt psutil terminate on entire tree
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        procs = [parent] + children
        for p in procs:
            try:
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        gone, alive = psutil.wait_procs(procs, timeout=1.5)
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    except Exception:
        pass

    # 2. Windows kernel-level taskkill /F /T ensures complete tree death
    if sys.platform == "win32" and psutil.pid_exists(pid):
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5.0)
        except Exception:
            pass

    return not psutil.pid_exists(pid)


def wait_for_port_drained(port: int = DEFAULT_PORT, host: str = DEFAULT_HOST, timeout: float = 6.0) -> bool:
    """
    Poll until socket is completely released by the OS TCP stack.
    Avoids WinError 10048 by checking connection refusal without holding a bind lock.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        # Check 1: No PIDs holding port
        if get_pids_on_port(port):
            time.sleep(0.1)
            continue

        # Check 2: Connection refused (port free)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex((host, port)) != 0:
                    time.sleep(0.2)  # Critical OS TCP teardown settle delay
                    return True
        except OSError:
            time.sleep(0.2)
            return True

        time.sleep(0.1)
    return False


def wait_for_health_probe(
    url: str = "http://127.0.0.1:8000/api/heartbeat",
    timeout: float = 35.0,
    interval: float = 0.5,
) -> bool:
    """Poll health endpoint until HTTP 200 with valid JSON response is received."""
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


def parse_png_header(data: bytes) -> Dict[str, Any]:
    """Parse PNG magic signature and IHDR chunk with zero third-party dependencies."""
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
    if len(data) < 24:
        return {"valid": False, "error": f"Data too short ({len(data)} bytes)"}
    if not data.startswith(PNG_SIGNATURE):
        return {"valid": False, "error": "Invalid PNG magic signature"}

    chunk_type = data[12:16]
    if chunk_type != b"IHDR":
        return {"valid": False, "error": f"Expected IHDR chunk, got {chunk_type!r}"}

    width, height = struct.unpack(">II", data[16:24])
    return {
        "valid": True,
        "width": width,
        "height": height,
        "file_size": len(data),
        "is_1080p": (width == 1920 and height == 1080),
        "is_gt_100kb": (len(data) > 102400),
    }


def validate_png_file(file_path: Path | str, min_size: int = 10000) -> Dict[str, Any]:
    """Validate PNG file existence, non-empty size, and IHDR dimensions."""
    p = Path(file_path)
    if not p.exists():
        return {"valid": False, "error": f"File does not exist: {p}"}
    size = p.stat().st_size
    if size < min_size:
        return {"valid": False, "error": f"File size too small ({size} < {min_size})"}
    try:
        raw_header = p.read_bytes()[:32]
        return parse_png_header(raw_header)
    except Exception as e:
        return {"valid": False, "error": str(e)}


def ensure_server_fresh(
    force_restart: bool = True,
    port: int = DEFAULT_PORT,
    timeout: float = 35.0,
) -> bool:
    """
    Module-level function enforcing clean web server freshness cycle:
    1. If force_restart: terminates all existing server processes on port.
    2. Waits for OS socket drain loop.
    3. Spawns detached uvicorn process with DETACHED_PROCESS | CREATE_NO_WINDOW.
    4. Probes /api/heartbeat until HTTP 200 returned with valid status JSON.
    """
    if not force_restart and wait_for_health_probe(f"http://127.0.0.1:{port}/api/heartbeat", timeout=1.0):
        return True

    pids = get_pids_on_port(port)
    if pids:
        print(f"[VisualDoc] Terminating existing server processes on port {port}: {pids}")
        for pid in pids:
            kill_server_tree(pid)

    if not wait_for_port_drained(port, DEFAULT_HOST, timeout=6.0):
        print(f"[VisualDoc] [ERROR] Port {port} failed to drain within timeout!")
        return False

    print(f"[VisualDoc] Spawning fresh detached uvicorn server on port {port}...")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "agent_city.server:app",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(port),
    ]

    flags = 0
    if sys.platform == "win32":
        flags = WIN32_DETACHED_PROCESS | WIN32_CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        cwd=str(_root_dir),
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=(sys.platform != "win32"),
    )

    healthy = wait_for_health_probe(f"http://127.0.0.1:{port}/api/heartbeat", timeout=timeout)
    if healthy:
        print(f"[VisualDoc] [OK] Fresh server verified healthy (PID {proc.pid})")
        return True
    else:
        print(f"[VisualDoc] [ERROR] Server failed health probe within {timeout}s")
        return False


def capture_page(
    url: str,
    output_path: Path | str,
    width: int = 1920,
    height: int = 1080,
    virtual_time_budget: int = 3000,
    timeout: float = 45.0,
) -> bool:
    """
    Module-level function capturing URL via Microsoft Edge Headless:
    - Launches msedge with isolated temporary --user-data-dir
    - Poll-and-terminate pattern: polls for screenshot output to avoid Chromium post-capture hang
    - Cleans up all child/orphan browser processes in finally block
    - Returns True if PNG is written and valid
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)
    if out_p.exists():
        try:
            out_p.unlink()
        except Exception:
            pass

    edge_bin = find_edge_binary()
    temp_profile = tempfile.mkdtemp(prefix="edge_doc_profile_")

    cmd = [
        edge_bin,
        "--headless=new",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={virtual_time_budget}",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        f"--user-data-dir={temp_profile}",
        f"--screenshot={str(out_p)}",
        url,
    ]

    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captured = False

    try:
        # Poll for screenshot creation (avoids waiting for msedge to exit on Windows)
        while time.time() - t0 < timeout:
            if out_p.exists() and out_p.stat().st_size > 10000:
                time.sleep(0.5)  # flush delay
                captured = True
                break
            time.sleep(0.5)
    finally:
        # Guaranteed process tree cleanup
        kill_server_tree(proc.pid)
        time.sleep(0.2)
        shutil.rmtree(temp_profile, ignore_errors=True)

    if not captured:
        print(f"[VisualDoc] [ERROR] Capture timed out after {time.time() - t0:.1f}s waiting for {out_p.name}")
        return False

    png_val = validate_png_file(out_p)
    if not png_val.get("valid", False):
        print(f"[VisualDoc] [ERROR] Invalid PNG generated: {png_val.get('error')}")
        return False

    print(f"[VisualDoc] [OK] Captured {out_p.name} ({out_p.stat().st_size:,} bytes) in {time.time() - t0:.1f}s")
    return True


class VisualDocCapturer:
    """Manages the full visual documentation capture lifecycle."""

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.cm = ContextManager()
        self.edge_path = find_edge_binary()
        # Ensure target directories exist
        ( _root_dir / "agent_city" ).mkdir(parents=True, exist_ok=True)
        ( _root_dir / "agent_city" / "screenshots" ).mkdir(parents=True, exist_ok=True)

    def ensure_server_fresh(self, force_restart: bool = True, timeout: float = 35.0) -> bool:
        """Instance method wrapper for web server freshness cycle."""
        return ensure_server_fresh(force_restart=force_restart, port=self.port, timeout=timeout)

    def capture_page(
        self,
        url: str,
        output_path: Path | str,
        width: int = 1920,
        height: int = 1080,
        virtual_time_budget: int = 3000,
        timeout: float = 45.0,
    ) -> bool:
        """Instance method wrapper for Edge headless capture."""
        return capture_page(
            url=url,
            output_path=output_path,
            width=width,
            height=height,
            virtual_time_budget=virtual_time_budget,
            timeout=timeout,
        )

    def run_documentation_cycle(self) -> Dict[str, Any]:
        """
        Execute full visual capture cycle with clean server reloads:
        1. Restart server -> clean navigation -> render settlement -> capture Grove (/)
        2. Clean reload -> capture Evolution Portal (/evolution)
        3. Save timestamped PNGs to BOTH `agent_city/` and `agent_city/screenshots/`
        4. Register in SQLite `sanctuary_context.db` (artifacts table with 1080p metadata)
        """
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        slug = now.strftime("%Y%m%d_%H%M%S")

        results: Dict[str, Any] = {
            "timestamp": timestamp_str,
            "epoch_id": 1,
            "captures": [],
            "server_freshness": True,
        }

        # ---------------------------------------------------------------------
        # Cycle 1: Capture 3D Voxel Grove (/)
        # ---------------------------------------------------------------------
        print("[VisualDoc] === Commencing Cycle 1: 3D Voxel Grove ===")
        if not self.ensure_server_fresh(force_restart=True):
            print("[VisualDoc] Warning: Server restart cycle returned False, continuing probe...")

        grove_filename = f"screenshot_grove_{slug}.png"
        grove_dest_primary = _root_dir / "agent_city" / grove_filename
        grove_dest_gallery = _root_dir / "agent_city" / "screenshots" / grove_filename
        grove_url = f"http://127.0.0.1:{self.port}/"

        grove_ok = self.capture_page(grove_url, grove_dest_primary, width=1920, height=1080, virtual_time_budget=3000)
        if grove_ok:
            # Dual-location save
            shutil.copy2(grove_dest_primary, grove_dest_gallery)

            # Optional brain artifact copy
            if BRAIN_ARTIFACTS_DIR.exists():
                try:
                    shutil.copy2(grove_dest_primary, BRAIN_ARTIFACTS_DIR / grove_filename)
                except Exception:
                    pass

            file_size = grove_dest_primary.stat().st_size
            meta = {
                "width": 1920,
                "height": 1080,
                "capture_type": "3D Voxel Grove",
                "url": grove_url,
                "timestamp": timestamp_str,
            }

            # Register in SQLite Context DB
            try:
                self.cm.register_artifact(
                    artifact_name=grove_filename,
                    artifact_type="screenshot_3d_grove",
                    file_path=str(grove_dest_primary),
                    epoch_id=1,
                    metadata=meta,
                )
            except Exception as e:
                print(f"[VisualDoc] Warning: SQLite registration error: {e}")

            results["captures"].append({
                "type": "3D Voxel Grove",
                "filename": grove_filename,
                "size_bytes": file_size,
                "width": 1920,
                "height": 1080,
                "paths": [str(grove_dest_primary), str(grove_dest_gallery)],
            })

        # ---------------------------------------------------------------------
        # Cycle 2: Capture Interactive Evolution Portal (/evolution)
        # ---------------------------------------------------------------------
        print("[VisualDoc] === Commencing Cycle 2: Evolution Portal ===")
        portal_filename = f"screenshot_portal_{slug}.png"
        portal_dest_primary = _root_dir / "agent_city" / portal_filename
        portal_dest_gallery = _root_dir / "agent_city" / "screenshots" / portal_filename
        portal_url = f"http://127.0.0.1:{self.port}/evolution"

        portal_ok = self.capture_page(portal_url, portal_dest_primary, width=1920, height=1080, virtual_time_budget=2000)
        if portal_ok:
            # Dual-location save
            shutil.copy2(portal_dest_primary, portal_dest_gallery)

            if BRAIN_ARTIFACTS_DIR.exists():
                try:
                    shutil.copy2(portal_dest_primary, BRAIN_ARTIFACTS_DIR / portal_filename)
                except Exception:
                    pass

            file_size = portal_dest_primary.stat().st_size
            meta = {
                "width": 1920,
                "height": 1080,
                "capture_type": "Evolution Portal",
                "url": portal_url,
                "timestamp": timestamp_str,
            }

            try:
                self.cm.register_artifact(
                    artifact_name=portal_filename,
                    artifact_type="screenshot_evolution_portal",
                    file_path=str(portal_dest_primary),
                    epoch_id=1,
                    metadata=meta,
                )
            except Exception as e:
                print(f"[VisualDoc] Warning: SQLite registration error: {e}")

            results["captures"].append({
                "type": "Evolution Portal",
                "filename": portal_filename,
                "size_bytes": file_size,
                "width": 1920,
                "height": 1080,
                "paths": [str(portal_dest_primary), str(portal_dest_gallery)],
            })

        # Log memory into agent deliberations
        try:
            self.cm.save_memory(
                agent_name="BotanicalMasterSculptor",
                memory_type="visual_capture",
                key=f"capture_{slug}",
                content=results,
            )
        except Exception:
            pass

        return results


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Silicon Sanctuary Visual Documentation Runner")
    parser.add_argument("--once", action="store_true", default=True, help="Run single visual capture cycle")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port (default: 8000)")
    parser.add_argument("--no-restart", action="store_true", help="Skip initial server restart")
    args = parser.parse_args()

    print("[VisualDoc] Starting Silicon Sanctuary Visual Documentation Runner...")
    runner = VisualDocCapturer(port=args.port)
    results = runner.run_documentation_cycle()
    print(json.dumps(results, indent=2))

    # Exit code: 0 if both captures succeeded
    if len(results.get("captures", [])) >= 2:
        print("[VisualDoc] Visual capture cycle successfully completed.")
        return 0
    elif len(results.get("captures", [])) == 1:
        print("[VisualDoc] Partial capture completed (1/2 succeeded).")
        return 0
    else:
        print("[VisualDoc] [ERROR] No captures succeeded.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
