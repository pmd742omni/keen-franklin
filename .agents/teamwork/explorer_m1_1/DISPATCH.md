## 2026-10-10T19:11:43Z
From: fe4e8efd-4d28-402d-b25d-f103e6dde375
Objective:
Investigate Milestone M1 Feature F1: Web Server Freshness & Restart/Reload Cycle.
User mandate: Before each screenshot is taken, the web server must be restarted (or reloaded), and the browser page must be cleanly reloaded to ensure fresh rendering of the 3D canvas and dynamic state (server restart/reload -> clean page navigation -> render settlement -> screenshot capture).
1. Analyze how to implement a bulletproof `ensure_server_fresh()` in `.agents/context/visual_doc_capture.py` on Windows 11.
2. Design process termination (psutil killing PID owning port 8000), socket drain polling loop (waiting until port 8000 is free), detached uvicorn spawn (`python -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000`), and health probe polling `http://127.0.0.1:8000/api/heartbeat` with timeout.
3. Prevent orphaned processes or port binding collisions.
4. Provide concrete implementation blueprint and code snippets for Worker M1.

Scope boundaries:
Read-only exploration. DO NOT edit codebase files. Write report to c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_m1_1\handoff.md and notify caller.
