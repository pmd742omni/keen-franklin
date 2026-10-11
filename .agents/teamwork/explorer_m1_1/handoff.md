# Server Freshness & Process Lifecycle Investigation Report (M1 - Feature F1)

**Agent**: Explorer M1-1 (Server Freshness & Process Lifecycle Explorer)  
**Parent Orchestrator**: `fe4e8efd-4d28-402d-b25d-f103e6dde375` (Orchestrator 3)  
**Working Directory**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_1`  
**Date**: 2026-10-10  
**Handoff Type**: Hard Handoff (Investigation & Empirical Verification Complete)  

---

## 1. Observation

### 1.1 Existing Server Freshness Defect in Codebase
- **File**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\context\visual_doc_capture.py`
- **Lines 51–63**:
  ```python
  def ensure_server_fresh(self) -> bool:
      """Verify web server is alive and fresh on port 8000."""
      if not is_server_listening(8000):
          print("[VisualDoc] Port 8000 not listening, launching fresh server...")
          subprocess.Popen(
              [sys.executable, "-m", "uvicorn", "agent_city.server:app", "--host", "127.0.0.1", "--port", "8000"],
              cwd=str(_root_dir),
              stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL
          )
          time.sleep(2.0)
      return is_server_listening(8000)
  ```
- **Flaw**: If port 8000 is already listening, `ensure_server_fresh` executes a no-op and returns `True`. It **never** restarts or reloads the web server.
- **Mandate Violation**: Violates the user directive from `ORIGINAL_REQUEST.md:117`:
  > *"Crucial requirement from user: Before each screenshot is taken, the web server must be restarted (or reloaded), and the browser page must be cleanly reloaded to ensure fresh rendering of the 3D canvas and dynamic state. Please incorporate this cycle (server restart/reload -> clean page navigation -> render settlement -> screenshot capture) into the 2-minute documentation engine."*

### 1.2 Process Discovery on Windows 11
- **Tool Command**: `psutil.net_connections(kind="tcp")`
- **Observation**:
  - Successfully identifies listening connections on `127.0.0.1:8000`.
  - When uvicorn is running, `[c.pid for c in psutil.net_connections(kind='tcp') if c.laddr and c.laddr.port == 8000 and c.pid]` returned active PIDs (e.g. `17608`, `17928`, `23992`).
  - Uvicorn on Windows consists of a master process and child worker process. Terminating only the listening PID without child processes or parent process leaves zombie Python instances.

### 1.3 Windows Socket Port Collision Trap (`WinError 10048`)
- **Direct Observation**:
  - In our first test harness (`test_server_freshness.py`), after killing the process, we attempted to test socket drain by opening a local socket and binding to `("127.0.0.1", 8000)`.
  - Closing that test socket on Windows placed port 8000 into a brief OS TCP `TIME_WAIT` state.
  - When `uvicorn` spawned milliseconds later, uvicorn failed with:
    `[WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted`.
  - **Resolution**: Port drain polling must NOT bind to port 8000. Instead, it must check client connection refusal via `connect_ex((host, port)) != 0` AND verify `find_pids_on_port(8000) == []`, followed by an OS TCP settle delay of 150–200ms.

### 1.4 System Startup Latency on Low-Power Quad-Core (Intel N100)
- **Direct Benchmark**:
  - Executed `python -c "import time; t0 = time.time(); import agent_city.server; print('Import duration:', time.time() - t0)"`
  - Output: `Import duration: 4.774689674377441 seconds`.
  - Measured full uvicorn boot until `/api/heartbeat` returned HTTP 200:
    - Trial 1 under moderate load: **14.073 seconds** (`READY! HTTP 200 received at 14.073s (poll 18)`).
    - Trial 2 under heavy CPU load: **17.645 seconds** (`SUCCESS! HTTP 200 at 17.645s`).
    - Trial 3 under peak CPU load (100% CPU): **28.834 seconds** (`SUCCESS! HTTP 200 at 28.834s`).
- **Defect in Project Scope Spec**:
  - `orchestrator_3/PROJECT.md:54` specified a 10-second timeout (`polls /api/heartbeat until HTTP 200 (timeout: 10s)`).
  - On this machine (Intel N100, 4 E-cores, Windows 11), a 10s timeout triggers intermittent/consistent false failures.
  - **Resolution**: Health probe timeout MUST be set to at least **35.0 seconds** (or 40.0s) with 0.5s polling.

### 1.5 Detached Spawning Flags on Windows 11
- **File**: `start.py:92-107`
- **Subprocess Creation Flags**:
  ```python
  DETACHED_PROCESS = 0x00000008
  CREATE_NO_WINDOW = 0x08000000
  flags = DETACHED_PROCESS | CREATE_NO_WINDOW
  ```
- **Tested Combinations**:
  - `CREATE_NO_WINDOW`: Process stays alive.
  - `CREATE_NEW_PROCESS_GROUP`: Process stays alive.
  - `DETACHED_PROCESS | CREATE_NO_WINDOW`: Process stays alive detached without a console window or standard handle leaks.

### 1.6 Health Probe Endpoint Response Structure
- **URL**: `http://127.0.0.1:8000/api/heartbeat`
- **Output**:
  ```json
  {
    "heartbeat_id": "hb-13869",
    "timestamp": "2026-10-10T22:00:13.059848",
    "epoch": 1,
    "tick": 13869,
    "uptime_seconds": 16465.4,
    "server_live": true,
    "consecutive_failures": 0,
    "rate_limit_state": "nominal"
  }
  ```
- Responds with HTTP 200 and `server_live: True` when operational.

---

## 2. Logic Chain

1. **Premise**: The user requires a clean server restart before each screenshot capture (`ORIGINAL_REQUEST.md:117`).
2. **Current Defect**: `visual_doc_capture.py:ensure_server_fresh` only checks `if not is_server_listening(8000)`. Since port 8000 is usually running, it never terminates or refreshes the server (Observation 1.1).
3. **PID Identification**: To terminate the existing server, we must locate all PIDs listening on port 8000. `psutil.net_connections(kind="tcp")` with a fallback to `psutil.process_iter` and Windows `netstat -ano` guarantees discovery of all owning processes across permission environments (Observation 1.2).
4. **Clean Tree Termination**: Simple Python `proc.terminate()` leaves child worker processes active on Windows. Using `taskkill /F /T /PID <pid>` forcefully and cleanly terminates the entire process tree in the Win32 kernel, verified by `psutil.pid_exists` (Observation 1.2).
5. **Port Drain**: Terminated sockets on Windows enter TCP teardown. Binding a temporary socket to check availability creates a race condition that causes `WinError 10048` when uvicorn immediately attempts to bind (Observation 1.3). Therefore, socket drain must poll `connect_ex` refusal and PID clearance without binding, followed by a 150–200ms settle delay.
6. **Detached Process Spawning**: Spawning uvicorn with `DETACHED_PROCESS (0x00000008) | CREATE_NO_WINDOW (0x08000000)`, `cwd=_root_dir`, and `DEVNULL` streams isolates the server daemon cleanly from the caller's console session (Observation 1.5).
7. **Timeout Calibration**: Because initializing `agent_city.server:app` requires importing polyglot bridges, starting `SimulationCoordinator`, seeding 11 agents, and starting the telemetry loop, cold boot takes 14–28s on an Intel N100 under load (Observation 1.4). Setting the probe timeout to 35.0s ensures reliable readiness without false timeouts, while 0.5s polling returns immediately upon startup.
8. **Empirical Verification**: Testing two consecutive full restart cycles in `.agents/teamwork/explorer_m1_1/test_server_freshness.py` achieved 100% success (`Success: True`), completing in ~20–22s per cycle without orphan processes or socket collisions.

---

## 3. Caveats

1. **Capture Cadence vs. Restart Duration**: Each restart takes ~15–22 seconds on an Intel N100 laptop. For two screenshots (`/` and `/evolution`), executing a full restart before each screenshot takes ~35–45 seconds total. This is well within the 2-minute (120s) cron window, but Worker M1 should ensure sequential execution rather than overlapping runs.
2. **Heartbeat File Pre-requisite**: `/api/heartbeat` reads `.agents/context/heartbeat.json`. If that file does not exist, `/api/heartbeat` still returns HTTP 200 with fallback JSON (`"status": "nominal"`), so the probe is always reliable.
3. **Permissions**: Running `taskkill` and `psutil` within the current user context is fully permitted and verified in this environment.

---

## 4. Conclusion & Concrete Blueprint for Worker M1

Worker M1 should replace lines 51–63 of `c:\Users\ignaz\antigravity\keen-franklin\.agents\context\visual_doc_capture.py` with the following production-grade implementation.

### Implementation Blueprint for `visual_doc_capture.py`

```python
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

# Platform-specific constants
WIN32_DETACHED_PROCESS = 0x00000008
WIN32_CREATE_NO_WINDOW = 0x08000000


def get_pids_on_port(port: int = 8000) -> List[int]:
    """Discover all process IDs listening on the specified port."""
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
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    try:
                        pids.add(int(parts[-1]))
                    except ValueError:
                        pass
        except Exception:
            pass

    return list(pids)


def kill_server_tree(pid: int) -> bool:
    """Terminate the process and all child processes cleanly without orphans."""
    if not psutil.pid_exists(pid):
        return True

    # On Windows, kernel-level taskkill /F /T terminates entire process tree
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


def wait_for_port_drained(port: int = 8000, host: str = "127.0.0.1", timeout: float = 6.0) -> bool:
    """Poll until socket is completely released by the OS TCP stack."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        # Check 1: No PIDs holding port
        if get_pids_on_port(port):
            time.sleep(0.1)
            continue

        # Check 2: Connection refused (port free)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex((host, port)) != 0:
                    time.sleep(0.2)  # Critical OS TCP teardown settle delay
                    return True
        except OSError:
            time.sleep(0.2)
            return True

        time.sleep(0.1)
    return False


def wait_for_health_probe(url: str = "http://127.0.0.1:8000/api/heartbeat", timeout: float = 35.0, interval: float = 0.5) -> bool:
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


class VisualDocCapturer:
    # ...
    def ensure_server_fresh(self, force_restart: bool = True, timeout: float = 35.0) -> bool:
        """
        Enforce clean server freshness cycle before visual doc capture:
        1. Identifies and terminates any existing server processes on port 8000.
        2. Waits for OS socket drain to prevent WinError 10048.
        3. Spawns detached uvicorn process without console window or handle leaks.
        4. Polls /api/heartbeat until HTTP 200 confirms full readiness.
        """
        if not force_restart and wait_for_health_probe("http://127.0.0.1:8000/api/heartbeat", timeout=1.0):
            return True

        pids = get_pids_on_port(8000)
        if pids:
            print(f"[VisualDoc] Terminating existing server processes on port 8000: {pids}")
            for pid in pids:
                kill_server_tree(pid)

        if not wait_for_port_drained(8000, "127.0.0.1", timeout=6.0):
            print("[VisualDoc] [ERROR] Port 8000 failed to drain within timeout!")
            return False

        print("[VisualDoc] Spawning fresh detached uvicorn server on port 8000...")
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "agent_city.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
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
        )

        healthy = wait_for_health_probe("http://127.0.0.1:8000/api/heartbeat", timeout=timeout)
        if healthy:
            print(f"[VisualDoc] [OK] Fresh server verified healthy (PID {proc.pid})")
            return True
        else:
            print(f"[VisualDoc] [ERROR] Server failed health probe within {timeout}s")
            return False
```

### Integration in Capture Cycle

In `VisualDocCapturer.run_documentation_cycle()`:
```python
        # Ensure fresh server cycle before capture 1: 3D Voxel Grove
        self.ensure_server_fresh(force_restart=True)
        # Capture 3D Voxel Grove
        # ...

        # Ensure fresh server cycle before capture 2: Evolution Portal
        self.ensure_server_fresh(force_restart=True)
        # Capture Evolution Portal
        # ...
```

---

## 5. Verification Method

### 5.1 Verification Commands
1. **Run Standalone Freshness Cycle Test**:
   ```powershell
   python .agents/teamwork/explorer_m1_1/test_server_freshness.py
   ```
   **Expected Result**:
   - `[FreshServer] Spawned fresh uvicorn server (PID ...)`
   - `[FreshServer] [OK] Server fresh and responding on http://127.0.0.1:8000/api/heartbeat (PIDs: [...])`
   - `Cycle completed in <30.00s. Success: True`

2. **Verify Server Health Probe Directly**:
   ```powershell
   python -c "import urllib.request, json; resp = urllib.request.urlopen('http://127.0.0.1:8000/api/heartbeat', timeout=2); print('Status:', resp.status, 'Body:', json.loads(resp.read().decode('utf-8')))"
   ```
   **Expected Result**:
   - `Status: 200`
   - Valid JSON body with `"server_live": true` or `"status": "nominal"`.

3. **Verify Zero Orphan Processes After Shutdown**:
   ```powershell
   python -c "import psutil; pids = [c.pid for c in psutil.net_connections(kind='tcp') if c.laddr and c.laddr.port == 8000 and c.pid]; print('PIDs on port 8000:', pids)"
   ```
   **Expected Result**: Returns exactly one listening PID (or empty if terminated).

### 5.2 Invalidation Conditions
- Any occurrence of `[WinError 10048] Only one usage of each socket address` upon uvicorn spawn invalidates the socket drain routine.
- Any timeout exceeding 35s on health probing indicates server deadlock or missing dependencies.
- Any leftover zombie process after `taskkill /F /T` invalidates the process termination routine.
