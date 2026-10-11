# Forensic Audit Report: Milestone M1 (Server Freshness & Edge Headless Capture)

**Auditor**: Forensic Auditor (`auditor_m1_1`)  
**Target**: Milestone M1 (`.agents/context/visual_doc_capture.py`, server freshness cycle, and generated artifacts)  
**Profile**: General Project  
**Integrity Mode**: Development (per `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## 1. Observation

Direct empirical observations, verbatim commands, AST code analysis, and live runtime traces:

### 1.1 Static Code Analysis of `.agents/context/visual_doc_capture.py`
- Analyzed AST tree of `.agents/context/visual_doc_capture.py` (559 lines) for suspicious constants, byte arrays, base64 strings, or mock facades.
  - Byte literals detected: exactly two constants:
    - `b'\x89PNG\r\n\x1a\n'` (standard 8-byte PNG magic header at line 195)
    - `b'IHDR'` (standard IHDR chunk signature at line 202)
  - Zero hardcoded PNG byte payloads, zero base64 encoded images, and zero mock/dummy return values.
  - Return statements verified across all 11 module functions: each returns authentic computational results (`pids`, boolean process health, parsed binary header structs, or execution result dictionaries).
  - Dependency audit: Pure standard library implementation (`subprocess`, `struct`, `socket`, `urllib.request`, `pathlib`, `tempfile`) combined with `psutil` for process tree introspection. Zero external graphics dependencies (e.g., `PIL`/Pillow) required.

### 1.2 Server Freshness & PID Rotation Tracing (`ensure_server_fresh`)
- Initial process discovery: Listening PID on port 8000 identified as `24708`.
- Invocations of `ensure_server_fresh(force_restart=True, port=8000, timeout=35.0)`:
  ```
  [VisualDoc] Terminating existing server processes on port 8000: [24708]
  [VisualDoc] Spawning fresh detached uvicorn server on port 8000...
  [VisualDoc] [OK] Fresh server verified healthy (PID 25216)
  ```
  Subsequent run during full cycle:
  ```
  [VisualDoc] Terminating existing server processes on port 8000: [25216]
  [VisualDoc] Spawning fresh detached uvicorn server on port 8000...
  [VisualDoc] [OK] Fresh server verified healthy (PID 21496)
  ```
- PID delta empirically verified: `24708 -> 25216 -> 21496`. The old process was genuinely terminated via `kill_server_tree` (`psutil.Process.terminate()`, `psutil.wait_procs`, and kernel `taskkill /F /T /PID`).
- OS TCP socket release verified: Socket connection refusal and drain loop prevent `WinError 10048` (`Only one usage of each socket address is normally permitted`).
- Health probe verified: `http://127.0.0.1:8000/api/heartbeat` returned HTTP 200 with dynamic vitals (`heartbeat_id`, `tick`, `hardware.free_memory_mb`, `vitals.ram_pct`).

### 1.3 Microsoft Edge Headless Subprocess Tracing (`capture_page`)
- Binary search located authentic system binary at: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` (size: 4,374,472 bytes).
- Subprocess command line traced during execution:
  ```
  msedge.exe --headless=new --window-size=1920,1080 --virtual-time-budget=3000 --hide-scrollbars --no-first-run --no-default-browser-check --disable-background-networking --user-data-dir=<temp_profile> --screenshot=<output_path> <url>
  ```
- Chromium process lifecycle: Poll-and-terminate pattern polls for screenshot file write (`> 10,000 bytes`) and then executes `kill_server_tree(proc.pid)` to terminate the browser process tree and cleans up `--user-data-dir`.
- Execution latency: Capture completed in **7.8 seconds** with 0 lingering orphan browser processes.

### 1.4 Screenshot Artifact Inspection & Dual-Location Validation
- Full documentation cycle executed: `python .agents/context/visual_doc_capture.py --once`.
- Generated artifacts verified on disk:
  1. `screenshot_grove_20261011_075847.png`:
     - File size: 554,337 bytes
     - Resolution: 1920 x 1080 (32-bit RGBA, IHDR valid)
     - MD5: `64188b901a1415053f3e6919ef7c4d51`
     - SHA-256: `0e8631c3bf795e1e0728c0bce904bbf1c7a87e2f5b5f8846c429ffca7195c88b`
     - Locations: Present in BOTH `agent_city/` and `agent_city/screenshots/` with identical cryptographic hashes.
  2. `screenshot_portal_20261011_075847.png`:
     - File size: 308,016 bytes
     - Resolution: 1920 x 1080 (32-bit RGBA, IHDR valid)
     - MD5: `a92ef59c00b0dbdbe119424c53cbe99c`
     - SHA-256: `cf0f8b1c4323bdf2555546b5a34e0fe93077699709a32c25608c02bcfb1961fa`
     - Locations: Present in BOTH `agent_city/` and `agent_city/screenshots/` with identical cryptographic hashes.
- Discrepancy analysis: Grove MD5 (`64188b90...`) differs completely from Portal MD5 (`a92ef59c...`), proving empirically that these are distinct, independent live web renders of the 3D Voxel canvas and Evolution portal, not duplicate dummy assets.

### 1.5 SQLite Context Database Registration
- Database: `.agents/context/sanctuary_context.db`
- Query: `SELECT artifact_name, artifact_type, file_size_bytes, timestamp, metadata_json FROM artifacts WHERE artifact_name LIKE '%20261011_075847%'`
- Result: Exactly 2 rows registered:
  - `screenshot_grove_20261011_075847.png`: `screenshot_3d_grove`, size `554337`, metadata `{"width": 1920, "height": 1080, "capture_type": "3D Voxel Grove", "url": "http://127.0.0.1:8000/", "timestamp": "2026-10-11 07:58:47"}`
  - `screenshot_portal_20261011_075847.png`: `screenshot_evolution_portal`, size `308016`, metadata `{"width": 1920, "height": 1080, "capture_type": "Evolution Portal", "url": "http://127.0.0.1:8000/evolution", "timestamp": "2026-10-11 07:58:47"}`

### 1.6 E2E Test Suite Execution (Tier 1 Features F1 & F2)
- Command: `python -m pytest tests/e2e/test_tier1_features.py -o pythonpath=tests/e2e -k "TestFeature1WebServerFreshness or TestFeature2EdgeHeadlessCapture" -v`
- Results:
  - `test_f1_01_server_heartbeat_alive`: **PASSED**
  - `test_f1_02_server_port_socket_responsive`: **PASSED**
  - `test_f1_03_server_process_pid_identification`: **PASSED**
  - `test_f1_04_server_freshness_lifecycle_contract`: **PASSED**
  - `test_f1_05_server_city_status_endpoint`: **PASSED**
  - `test_f2_01_edge_binary_presence_and_version`: **PASSED**
  - `test_f2_02_edge_headless_flag_support`: **PASSED**
  - `test_f2_03_edge_capture_root_grove_1080p`: **PASSED**
  - `test_f2_04_edge_capture_evolution_portal_1080p`: **PASSED**
  - `test_f2_05_edge_capture_process_isolation_and_no_orphans`: **PASSED**
- Summary: **10 passed, 0 failed** in 40.54s.

---

## 2. Logic Chain

1. **Premise 1 (Anti-Cheating / Anti-Facade)**:
   - Observation 1.1 proves that `.agents/context/visual_doc_capture.py` contains no pre-packaged binary buffers, base64 strings, or mocked return values. Every function actively performs system calls (`psutil`, `socket`, `subprocess.Popen`, `urllib.request`).
2. **Premise 2 (Authentic Subprocess Invocation)**:
   - Observation 1.3 proves that `msedge.exe` is actually launched as a child process with full `--headless=new` and `--screenshot` parameters targeting live URLs (`http://127.0.0.1:8000/` and `/evolution`).
   - The poll-and-terminate mechanism handles Windows Chromium process retention without leaving zombie processes.
3. **Premise 3 (Authentic Server Lifecycle & Fresh State)**:
   - Observation 1.2 shows that `uvicorn` on port 8000 is genuinely killed and respawned with a new OS PID (`24708 -> 25216 -> 21496`), ensuring complete memory and state reset before capture.
4. **Premise 4 (Authentic Artifact Generation)**:
   - Observation 1.4 confirms that the resulting images are genuine 1920x1080 PNG files with valid IHDR chunks and realistic file sizes (554KB and 308KB). Cryptographic hash comparison proves that Grove and Portal are distinct visual renders matching the live application endpoints.
5. **Premise 5 (Specification Compliance)**:
   - All acceptance criteria from `ORIGINAL_REQUEST.md § 2026-10-10T17:01:39Z` and `§ 2026-10-10T17:03:20Z` (server restart cycle -> clean navigation -> render settlement -> 1080p Edge headless screenshot -> dual-location save -> SQLite registration) are fully satisfied.

---

## 3. Caveats

1. **Cold-boot duration on low-power hardware (Intel N100)**: When running on a 6W TDP quad-core CPU under high memory utilization (>90%), cold-booting `agent_city/server.py` with full agent initialization takes between 10 and 15 seconds. The 35.0-second health probe timeout implemented in `ensure_server_fresh` is essential to prevent false timeouts.
2. **Pytest PYTHONPATH requirement**: When running pytest from the repository root, `-o pythonpath=tests/e2e` must be specified so `conftest.py` is properly resolved by all test runners.
3. No other caveats.

---

## 4. Conclusion

The Milestone M1 implementation in `.agents/context/visual_doc_capture.py` is genuine, fully functional, and completely free of mock facades, hardcoded artifacts, or cheating patterns. All server recycle, headless browser invocation, and dual-location screenshot workflows operate authentically against live endpoints and pass 100% of the Tier 1 E2E contract tests.

**Verdict**: **CLEAN**

---

## 5. Verification Method

To independently verify this verdict:

1. **Execute full visual documentation cycle**:
   ```powershell
   python .agents/context/visual_doc_capture.py --once
   ```
   - Expect: Console logs confirm terminating previous PID, spawning fresh uvicorn PID, capturing both Grove and Portal in ~7.8s, saving to both `agent_city/` and `agent_city/screenshots/`, and exit code `0`.

2. **Inspect generated screenshot dimensions and headers (zero external dependencies)**:
   ```powershell
   python -c "
   from pathlib import Path
   import struct
   for p in sorted(Path('agent_city/screenshots').glob('screenshot_*.png'))[-2:]:
       d = p.read_bytes()
       w, h = struct.unpack('>II', d[16:24])
       print(f'{p.name}: {len(d):,} bytes, {w}x{h}, magic={d[:8] == b\"\x89PNG\r\n\x1a\n\"}')
   "
   ```
   - Expect: Both files report `1920x1080` dimensions, file sizes > 100KB, and `magic=True`.

3. **Verify SQLite registration**:
   ```powershell
   python -c "
   import sqlite3
   c = sqlite3.connect('.agents/context/sanctuary_context.db').cursor()
   for r in c.execute('SELECT artifact_name, artifact_type, file_size_bytes FROM artifacts WHERE artifact_type LIKE \"%screenshot%\" ORDER BY artifact_id DESC LIMIT 2'):
       print(r)
   "
   ```
   - Expect: 2 rows with matching timestamps, types `screenshot_3d_grove` and `screenshot_evolution_portal`.

4. **Run Tier 1 E2E Pytest suite**:
   ```powershell
   python -m pytest tests/e2e/test_tier1_features.py -o pythonpath=tests/e2e -k "TestFeature1WebServerFreshness or TestFeature2EdgeHeadlessCapture" -v
   ```
   - Expect: `10 passed, 0 failed`.
