## 2026-10-10T22:07:51Z
You are Worker M1 (Visual Capture Engine Implementer) for Milestone M1.
Your Working Directory: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\worker_m1_1
Original Request Path: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\ORIGINAL_REQUEST.md (YOU MUST READ THIS FIRST)
Project Scope Document: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\orchestrator_3\PROJECT.md (YOU MUST READ THIS FIRST)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership:
You EXCLUSIVELY own and modify:
- c:\Users\ignaz\antigravity\keen-franklin\.agents\context\visual_doc_capture.py
You may also create the directory:
- c:\Users\ignaz\antigravity\keen-franklin\agent_city\screenshots\
DO NOT edit other source files during this milestone.

Requirements to implement in visual_doc_capture.py:
1. Feature F1: Web Server Freshness Cycle
   - `ensure_server_fresh(force_restart=True)`:
     - User mandate: Before each screenshot is taken, the web server must be restarted (or reloaded), and the browser page must be cleanly reloaded to ensure fresh rendering of the 3D canvas and dynamic state.
     - Locate PID owning port 8000 via psutil (and Windows netstat fallback).
     - Gracefully terminate process tree with psutil terminate(), wait_procs(timeout=3), force kill(), and Windows taskkill /F /T /PID fallback.
     - Socket drain loop: wait until port 8000 is completely released and bindable.
     - Spawn detached uvicorn process (`python -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000`) with DETACHED_PROCESS (0x00000008) | CREATE_NO_WINDOW (0x08000000).
     - Health probe: poll `http://127.0.0.1:8000/api/heartbeat` until HTTP 200 returned with valid status JSON (timeout: 15s).

2. Feature F2: Microsoft Edge Headless Capture Runner
   - `capture_page(url, output_path, width=1920, height=1080)`:
     - Locate msedge.exe: check `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, `C:\Program Files\Microsoft\Edge\Application\msedge.exe`, and PATH.
     - Flags: `--headless=new`, `--window-size=1920,1080`, `--virtual-time-budget=3000` (allows 3D canvas and settlement shaders to settle), `--hide-scrollbars`, `--no-first-run`, `--no-default-browser-check`, `--disable-background-networking`, isolated temporary `--user-data-dir`.
     - Output files: save timestamped PNG artifacts `screenshot_grove_<timestamp>.png` and `screenshot_portal_<timestamp>.png` into BOTH `agent_city/` and `agent_city/screenshots/`.
     - Timeout guard: 45s timeout (safe for Intel N100). Terminate any child/orphan msedge processes on error or timeout. Clean up temp user-data-dir in finally block.
     - Validate output PNG: check file exists, size > 100KB, valid PNG magic bytes (`\x89PNG\r\n\x1a\n`). Zero external dependencies (pure binary struct check, no PIL).

3. Main entry point:
   - Allow running `python .agents/context/visual_doc_capture.py` directly to execute the full cycle (restart server -> clean navigation -> render settlement -> capture / -> capture /evolution -> verify PNGs -> return exit code 0).

4. Verification:
   - Run the script and verify it captures both screens, restarts the server, and outputs valid PNG files.
   - Document commands executed and exact results in your handoff report.

Write your report to c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\worker_m1_1\handoff.md and notify the caller via send_message.

## 2026-10-11T01:36:57Z
**Context**: Milestone M1 Implementation
**Content**: Checking on your implementation of `visual_doc_capture.py`. You have all the drop-in findings from Explorer M1-1 and Explorer M1-3. Please proceed directly with writing the implementation to `.agents/context/visual_doc_capture.py` and running the verification test.
**Action**: Please report your current status, any blockers, and ETA for the file implementation.
