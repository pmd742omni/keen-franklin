# Progress — Explorer M1-3

- Last visited: 2026-10-10T23:50:00Z
- Status: Investigation Complete — Writing handoff.md
- Active Task: Authoring comprehensive 5-component handoff report for Caller and Orchestrator
- Findings fully synthesized: Zero-dependency PNG validation, Edge Chromium headless process tree lifecycle, N100 startup timing, server restart multi-factor verification, and edge case resilience blueprint.
- Finding: `close_fds=True` combined with `DETACHED_PROCESS` on Windows can disrupt standard I/O redirection; subprocess.CREATE_NEW_PROCESS_GROUP or CREATE_NO_WINDOW is the reliable pattern.
- Finding: Discovered critical Chromium headless behavior: Edge writes screenshot file quickly (~5-8s) but does NOT exit automatically with --virtual-time-budget=3000. Capture runner must poll for file creation and terminate the process tree rather than waiting for process exit!
- Finding: Pillow (PIL) is not installed; PNG validation must be zero-dependency using Python struct or pure binary parsing!
- Finding: Edge path verified at C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe. Port 8000 currently active under PID 17608.
- Finding: On Intel N100, short timeouts (10s-15s) trigger TimeoutExpired because Chromium cold initialization and WebGL shader compilation require 20s-30s. Capturer and test harnesses MUST set safe timeouts (30s-45s) to avoid false negative timeouts!
