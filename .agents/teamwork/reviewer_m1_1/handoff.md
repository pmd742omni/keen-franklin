# Milestone M1 Review & Adversarial Audit Report

**Target File**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\context\visual_doc_capture.py`  
**Reviewer**: Reviewer 1 (Visual Capture Code Reviewer & Adversarial Critic)  
**Date**: 2026-10-11  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### Obs 1: Verification Command Execution Output
Running `python .agents/context/visual_doc_capture.py` produces the following verbatim console log:
```
[VisualDoc] Starting Silicon Sanctuary Visual Documentation Runner...
[VisualDoc] === Commencing Cycle 1: 3D Voxel Grove ===
[VisualDoc] Spawning fresh detached uvicorn server on port 8000...
[VisualDoc] [OK] Fresh server verified healthy (PID 15792)
[VisualDoc] [OK] Captured screenshot_grove_20261011_065307.png (554,337 bytes) in 53.1s
[VisualDoc] === Commencing Cycle 2: Evolution Portal ===
[VisualDoc] [ERROR] Capture timed out after 54.9s waiting for screenshot_portal_20261011_065307.png
{
  "timestamp": "2026-10-11 06:53:07",
  "epoch_id": 1,
  "captures": [
    {
      "type": "3D Voxel Grove",
      "filename": "screenshot_grove_20261011_065307.png",
      "size_bytes": 554337,
      "width": 1920,
      "height": 1080,
      "paths": [
        "C:\\Users\\ignaz\\antigravity\\keen-franklin\\agent_city\\screenshot_grove_20261011_065307.png",
        "C:\\Users\\ignaz\\antigravity\\keen-franklin\\agent_city\\screenshots\\screenshot_grove_20261011_065307.png"
      ]
    }
  ],
  "server_freshness": true
}
[VisualDoc] Partial capture completed (1/2 succeeded).
```
Process exited with code `0`.

### Obs 2: Artifact Inventory Inspection
Directory `c:\Users\ignaz\antigravity\keen-franklin\agent_city\screenshots`:
- `screenshot_grove_20261011_065307.png` (554,337 bytes, valid PNG header: 1920x1080)
- `screenshot_portal_*.png` is **COMPLETELY MISSING**. Neither `agent_city/` nor `agent_city/screenshots/` contains the Evolution Portal screenshot.
- SQLite query `SELECT id, artifact_name, artifact_type FROM artifacts WHERE artifact_type LIKE '%screenshot%'`:
  `[(1, 'screenshot_grove_v5.png', ...), (2, 'screenshot_grove_v6.png', ...), (3, 'screenshot_grove_v7.png', ...), (542, 'screenshot_grove_20261011_065307.png', 'screenshot_3d_grove', 554337)]`  
  No `screenshot_portal_*` artifact was ever registered.

### Obs 3: Omission of Server Freshness Cycle before Cycle 2
In `c:\Users\ignaz\antigravity\keen-franklin\.agents\context\visual_doc_capture.py` lines 418-421 vs 471-478:
```python
# Lines 418-421:
print("[VisualDoc] === Commencing Cycle 1: 3D Voxel Grove ===")
if not self.ensure_server_fresh(force_restart=True):
    print("[VisualDoc] Warning: Server restart cycle returned False, continuing probe...")

...

# Lines 471-478:
print("[VisualDoc] === Commencing Cycle 2: Evolution Portal ===")
portal_filename = f"screenshot_portal_{slug}.png"
portal_dest_primary = _root_dir / "agent_city" / portal_filename
portal_dest_gallery = _root_dir / "agent_city" / "screenshots" / portal_filename
portal_url = f"http://127.0.0.1:{self.port}/evolution"

portal_ok = self.capture_page(portal_url, portal_dest_primary, width=1920, height=1080, virtual_time_budget=2000)
```
`self.ensure_server_fresh()` is called before Cycle 1, but is **NOT called before Cycle 2**.

### Obs 4: Uvicorn Server Crash Caused by Edge Process Kill (WinError 10054)
Inspection of uvicorn server output after Edge capture:
```
Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)
Traceback (most recent call last):
  File "C:\Users\ignaz\AppData\Roaming\uv\python\cpython-3.11.11-windows-x86_64-none\Lib\asyncio\proactor_events.py", line 165, in _call_connection_lost
    self._sock.shutdown(socket.SHUT_RDWR)
ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
```
When `kill_server_tree(proc.pid)` runs `taskkill /F /T` on msedge (lines 135-140, 345), active WebSockets (`/ws`) are terminated with a hard TCP RST, raising unhandled `ConnectionResetError` in asyncio and terminating uvicorn. Because Cycle 2 does not ensure the server is fresh, Cycle 2 requests `http://127.0.0.1:8000/evolution` on a dead port.

### Obs 5: False Success Return Code Masking Partial Failure
In `visual_doc_capture.py` lines 546-554:
```python
    if len(results.get("captures", [])) >= 2:
        print("[VisualDoc] Visual capture cycle successfully completed.")
        return 0
    elif len(results.get("captures", [])) == 1:
        print("[VisualDoc] Partial capture completed (1/2 succeeded).")
        return 0
    else:
        print("[VisualDoc] [ERROR] No captures succeeded.")
        return 1
```
When 1 out of 2 captures fails, `main()` returns exit code `0`.

### Obs 6: Virtual Time Budget Discrepancy
In `visual_doc_capture.py` line 478:
```python
portal_ok = self.capture_page(portal_url, portal_dest_primary, width=1920, height=1080, virtual_time_budget=2000)
```
`virtual_time_budget` is set to `2000` ms, whereas PROJECT.md § Interface Contracts specifies `virtual-time-budget=3000`.

### Obs 7: Validation Function Logic Bug in `validate_png_file`
In `visual_doc_capture.py` lines 225-226:
```python
raw_header = p.read_bytes()[:32]
return parse_png_header(raw_header)
```
In `parse_png_header` line 212:
```python
"is_gt_100kb": (len(data) > 102400)
```
Because `raw_header` is sliced to 32 bytes, `len(data)` is always 32, meaning `is_gt_100kb` is always `False` regardless of the actual file size.

---

## 2. Logic Chain

1. **User Requirement & Contract Violation**:  
   `ORIGINAL_REQUEST.md` (§ 2026-10-10T17:03:20Z) explicitly mandates:  
   *"Before each screenshot is taken, the web server must be restarted (or reloaded), and the browser page must be cleanly reloaded to ensure fresh rendering of the 3D canvas and dynamic state. Please incorporate this cycle (server restart/reload -> clean page navigation -> render settlement -> screenshot capture) into the 2-minute documentation engine."*  
   Per **Obs 3**, `ensure_server_fresh()` is only invoked prior to Cycle 1, and omitted prior to Cycle 2.

2. **Root Cause of Capture 2 Failure**:  
   During Cycle 1, Edge connects to the server and opens a live WebSocket (`/ws`). When `capture_page()` completes, line 345 invokes `kill_server_tree(proc.pid)`, which issues `taskkill /F /T` against Edge. As seen in **Obs 4**, this abrupt socket teardown generates a TCP reset (`RST`) which causes a fatal `ConnectionResetError: [WinError 10054]` in Python's `asyncio.ProactorEventLoop`, killing the uvicorn process. Because Cycle 2 does not call `ensure_server_fresh()`, Edge navigates to a dead server. The page never finishes loading, the screenshot file is never written, and the 45.0s timeout triggers (**Obs 1**).

3. **Missing Deliverable**:  
   Because Cycle 2 times out and fails, `screenshot_portal_*.png` is never written or copied to `agent_city/` or `agent_city/screenshots/`, and is never registered in `sanctuary_context.db` (**Obs 2**). This fails Acceptance Criteria R1 and Milestone M1 goals.

4. **Integrity / Masking Pattern**:  
   Despite the complete failure of Cycle 2, line 551 in `visual_doc_capture.py` explicitly returns `0` when `len(captures) == 1` (**Obs 5**). This prevents callers, cron supervisors, and test runners from catching the failure, falsely classifying an incomplete run as a clean success.

5. **Timing & Budget Constraints**:  
   On low-power hardware (Intel N100), browser cold startup and WebGL compilation take 30–50s under CPU load. A 45s hard timeout is too narrow, especially when combined with a virtual time budget mismatch (2000ms instead of 3000ms, **Obs 6**).

---

## 3. Caveats

1. The standalone capture of `/evolution` was independently verified to succeed in ~33s when the server is explicitly kept running (`python -c "...capture_page..."`). Therefore, Edge itself and the HTML/JS frontend of `/evolution` are fully functional; the failure is entirely due to server death and the missing freshness cycle between captures in `visual_doc_capture.py`.
2. The poll-and-terminate pattern implemented in `capture_page()` successfully solves the Windows Chromium headless post-capture hang (unlike `conftest.py`'s `proc.wait()` which hangs on Windows).
3. The server freshness cycle logic in `ensure_server_fresh()` (socket draining, PID cleanup, and `/api/heartbeat` polling) works properly when called; the defect is that it is not called before each capture and does not isolate/protect uvicorn from client reset crashes.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

The Milestone M1 implementation contains two critical blockers and several major/minor defects:
1. **[CRITICAL - Functional Failure]**: `run_documentation_cycle()` fails to capture the Evolution Portal screenshot (`screenshot_portal_*.png`), leaving the required artifact missing from both `agent_city/` and `agent_city/screenshots/`.
2. **[CRITICAL - Integrity / Masking Violation]**: `main()` returns exit code `0` when only 1 of 2 captures succeeds (`Partial capture completed (1/2 succeeded)`), falsely masking a half-failed cycle.
3. **[CRITICAL - Missing Mandatory Cycle]**: `ensure_server_fresh()` is not called prior to Cycle 2, directly violating the user specification that the server must be restarted/reloaded before *each* screenshot.
4. **[MAJOR - Cascading Socket Crash]**: Abrupt `taskkill` of Edge triggers `WinError 10054` in uvicorn's proactor event loop, killing the server.
5. **[MINOR - Virtual Time Budget]**: Cycle 2 uses `virtual_time_budget=2000` instead of `3000`.
6. **[MINOR - Validation Bug]**: `validate_png_file` passes only 32 bytes to `parse_png_header`, causing `is_gt_100kb` to always report `False`.

### Required Actions for M1 Worker:
1. Call `self.ensure_server_fresh(force_restart=True)` before **both** Cycle 1 (Grove) and Cycle 2 (Portal).
2. Update `main()` to return non-zero exit code (`return 1`) unless **both** captures succeed (`len(captures) >= 2`).
3. Set `virtual_time_budget=3000` for both `/` and `/evolution`.
4. Increase the default capture timeout from `45.0` to `65.0` seconds to accommodate Intel N100 cold-boot execution budgets.
5. In `validate_png_file`, inspect the actual file size (`size > 102400`) instead of checking the sliced 32-byte header.

---

## 5. Verification Method

To independently verify after fixes are applied:

1. **Full Execution Test**:
   ```powershell
   python .agents/context/visual_doc_capture.py
   ```
   **Expected**:
   - Exit code must be `0`.
   - Output must contain: `[VisualDoc] Visual capture cycle successfully completed.`
   - Output must report 2 successful captures in `results["captures"]`.
2. **Artifact Verification**:
   Inspect the filesystem:
   - Check `agent_city/screenshot_grove_*.png` and `agent_city/screenshots/screenshot_grove_*.png`.
   - Check `agent_city/screenshot_portal_*.png` and `agent_city/screenshots/screenshot_portal_*.png`.
   - Verify all 4 files are > 100 KB and have valid PNG dimensions (1920x1080).
3. **Database Verification**:
   ```powershell
   python -c "import sqlite3; conn = sqlite3.connect('.agents/context/sanctuary_context.db'); c = conn.cursor(); print(c.execute('SELECT artifact_name, artifact_type, file_size_bytes FROM artifacts ORDER BY id DESC LIMIT 2').fetchall())"
   ```
   **Expected**: Both `screenshot_3d_grove` and `screenshot_evolution_portal` records present with non-zero size.
