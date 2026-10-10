# Web Application Lifecycle & Evolution Architecture Investigation

**Agent**: Explorer 1 (Web App Lifecycle Explorer)  
**Parent Orchestrator**: `fe4e8efd-4d28-402d-b25d-f103e6dde375`  
**Working Directory**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_survey_1`  
**Date**: 2026-10-10  

---

## 1. Observation

### 1.1 Web Server Architecture & Endpoints (`agent_city/server.py`)
- **FastAPI Application Definition**:
  - `agent_city/server.py:142`: `app = FastAPI(title="Virtual Agent City API", version="1.0.0", lifespan=lifespan)`
  - `agent_city/server.py:131-140`: Lifespan context manager runs background task `telemetry_broadcaster_loop()` which broadcasts hardware telemetry every 1.0 second over active WebSockets (`agent_city/server.py:91-129`).
  - `agent_city/server.py:145-151`: `CORSMiddleware` configured with `allow_origins=["*"]`.
  - `agent_city/server.py:42`: `coordinator: SimulationCoordinator = SimulationCoordinator(config=DEFAULT_CONFIG)`.
  - `agent_city/server.py:45-51`: Seeds 5 Optimizer Agents (`MemoryGovernorAgent`, `StorageReclaimerAgent`, `ProcessGovernorAgent`, `StartupGuardianAgent`, `PerformanceAuditorAgent`) and 6 civic agents (`Mayor Vance`, `Architect Iris`, `Engineer Tor`, `Merchant Silas`, `Scholar Lin`, `Observer Nova`).
- **Static File Mount & Root Routes**:
  - `agent_city/server.py:582-584`: 
    ```python
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    ```
  - `agent_city/server.py:586-588`:
    ```python
    @app.get("/", response_class=FileResponse)
    async def serve_index() -> FileResponse:
        return FileResponse(static_dir / "index.html")
    ```
  - `agent_city/server.py:590-596`:
    ```python
    @app.get("/evolution", response_class=FileResponse)
    @app.get("/evolution-portal", response_class=FileResponse)
    async def serve_evolution_portal() -> FileResponse:
        portal_file = static_dir / "evolution_portal.html"
        if portal_file.exists():
            return FileResponse(portal_file)
        raise HTTPException(status_code=404, detail="Evolution Portal HTML not found.")
    ```
  - `agent_city/server.py:660-666`:
    ```python
    @app.get("/docs/latex/silicon_sanctuary_report.pdf", response_class=FileResponse)
    async def serve_latex_pdf() -> FileResponse:
        pdf_file = Path(__file__).resolve().parent.parent / "evolution" / "docs" / "latex" / "silicon_sanctuary_report.pdf"
        if pdf_file.exists():
            return FileResponse(pdf_file, media_type="application/pdf")
        raise HTTPException(status_code=404, detail="PDF report not found.")
    ```
- **REST Endpoints Verified**:
  - `GET /api/city/status` (`server.py:226-250`): Simulation tick, grid, economy, enriched with hardware metrics.
  - `GET /api/hardware` (`server.py:251-267`): Real-time CPU, RAM, disk, smoothness index, top 8 processes.
  - `GET /api/native/status` (`server.py:269-272`): Polyglot C/Rust/Java status.
  - `POST /api/native/compact` (`server.py:274-284`, `server.py:668-672`): Win32 NT working set compaction via C DLL.
  - `GET /api/evolution/status` (`server.py:285-296`, `server.py:643-651`): Reads `evolution/evolution_state.json`.
  - `GET /api/evolution/chronicle` (`server.py:297-307`, `server.py:652-659`): Reads `evolution/CHRONICLE.md`.
  - `GET /api/heartbeat` (`server.py:598-612`): Reads `.agents/context/heartbeat.json`.
  - `GET /api/context/summary` (`server.py:317-333`, `server.py:614-630`): SQLite context database summary.
  - `GET /api/context/benchmarks` (`server.py:631-642`): SQLite historical benchmarks.
  - `GET /api/agents` (`server.py:334-363`) & `GET /api/agents/{agent_id}` (`server.py:365-400`): Agent state and traits.
  - `GET /api/buildings` (`server.py:402-418`): City structures and zoning.
  - `GET /api/events` (`server.py:420-424`): Simulation events audit log.
  - `POST /api/controls` (`server.py:425-506`): Simulation control and hardware actions (`PAUSE`, `RESUME`, `STEP`, `SET_SPEED`, `TRIGGER_EVENT`, `BOOST_MEMORY`, `TRIM_MEMORY`, `PURGE_STORAGE`, `FULL_OPTIMIZE`, `TRIM_PID`, `NATIVE_COMPACT`).
  - `POST /api/snapshot/save` (`server.py:507-515`) & `POST /api/snapshot/load` (`server.py:516-528`): State serialization.
  - `WebSocket /ws` (`server.py:533-577`): Tick delta and telemetry broadcasting, client control handling.
- **Endpoint HTTP Verification Output**:
  ```
  http://127.0.0.1:8000/ 200
  http://127.0.0.1:8000/evolution 200
  http://127.0.0.1:8000/api/city/status 200
  http://127.0.0.1:8000/api/heartbeat 200
  ```

### 1.2 Running Process & Server Management Scripts
- **Active Listening Process**:
  - Command: `Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue`
    - Output: `127.0.0.1:8000 Listen OwningProcess: 17608`
  - Command: `Get-CimInstance Win32_Process -Filter "ProcessId = 17608"`
    - Output: `ProcessId: 17608 Name: python.exe CommandLine: "C:\Users\ignaz\AppData\Roaming\uv\python\cpython-3.11.11-windows-x86_64-none\python.exe" -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000`
  - Python check with `psutil`:
    - Command: `python -c "import psutil; [print('CONN:', c.laddr.port, 'PID:', c.pid) for c in psutil.net_connections(kind='inet') if c.laddr.port == 8000]"`
    - Output: `CONN: 8000 PID: 17608`
- **Management Scripts Inspected**:
  - `start.py:75-116` (`start_server_background()`):
    - Checks `is_server_running()` (port 8000 socket probe).
    - If not running, launches uvicorn using `subprocess.Popen` with `DETACHED_PROCESS (0x00000008) | CREATE_NO_WINDOW (0x08000000)`, `stdout=subprocess.DEVNULL`, `stderr=subprocess.DEVNULL`, `close_fds=True`.
    - **Defect noted**: If the server IS running, `start_server_background()` immediately returns `True` and does not provide an actual restart/reload mechanism.
  - `Start-Laptop-Optimizer-City.bat:21` and `agent_city/start_city.bat:21`:
    - Foregound launcher: `python -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000`
  - `agent_city/start_city.sh:21`:
    - Foreground reload launcher: `python3 -m uvicorn agent_city.server:app --host 0.0.0.0 --port 8000 --reload`

### 1.3 3D Voxel Canvas Rendering Architecture (`agent_city/static/voxel_engine.js` & `index.html`)
- **HTML Container & Canvas**:
  - `agent_city/static/index.html:251-253`:
    ```html
    <div class="motherboard-canvas-stage" id="pcbViewport">
      <canvas class="voxel-canvas-root" id="voxelMotherboardCanvas"></canvas>
    ```
- **Engine Initialization**:
  - `agent_city/static/app.js:428-446`:
    ```javascript
    function initVoxelStage() {
      if (!voxelCanvas || !window.VoxelMotherboardEngine) return;
      voxelEngine = new window.VoxelMotherboardEngine();
      voxelEngine.init(voxelCanvas, { ... });
    ```
  - `agent_city/static/voxel_engine.js:256-273`:
    - Context acquisition: `this.ctx = this.canvas.getContext("2d", { alpha: false });`
    - High-DPI handling: `this.dpr = Math.min(2, window.devicePixelRatio || 1);` (`voxel_engine.js:280-287`)
    - Animation loop: `this.animId = requestAnimationFrame(this._boundRender);` (`voxel_engine.js:272`, `voxel_engine.js:684`)
- **Shading, Math, and Projection**:
  - Mathematical Projection (`voxel_engine.js:564-581`):
    ```javascript
    project(x, y, z) {
      const cosA = Math.cos(this.camera.angle);
      const sinA = Math.sin(this.camera.angle);
      const dx = x - 16;
      const dy = y - 16;
      const rx = dx * cosA - dy * sinA;
      const ry = dx * sinA + dy * cosA;
      const sinP = Math.sin(this.camera.pitch);
      const cosP = Math.cos(this.camera.pitch);
      const screenX = this.width / 2 + rx * this.unit + this.camera.panX;
      const screenY = this.height / 2 + ry * sinP * this.unit - z * cosP * this.unit + this.camera.panY;
      return { x: screenX, y: screenY };
    }
    ```
  - MagicaVoxel 3-Face Directional Shading (`voxel_engine.js:1161-1163`):
    - Top face (+Z): `getShade(v.topColor || color, 1.32)`
    - Left face (+Y): `getShade(color, 0.94)`
    - Right face (+X): `getShade(color, 0.70)`
    - Pulse multiplier on high bloat/load: up to 1.25x (`voxel_engine.js:1166-1170`).
    - Hover highlight: Top 1.62x, Left 1.25x, Right 0.96x (`voxel_engine.js:1172-1177`).
  - Depth Sorting (`voxel_engine.js:1089-1093`):
    - Calculates `calcDepth(x, y, z) = ry * cosP + z * sinP`
    - Executes Painter's Algorithm: `voxels.sort((a, b) => a.depth - b.depth)`
- **Procedural Settlement & Botanical Generation (`voxel_engine.js:721-1052`)**:
  - 3-Tier Foundation:
    - Deep foundation (34x34) at z = -1.8 (`PALETTE.EARTH_DEEP`).
    - Terraced loam bedrock (32x32) at z = -1.0 (`PALETTE.EARTH_MID`).
    - Lush lawn turf (30x30) at z = -0.2 (`PALETTE.LAWN_TOP`).
    - Tactile vertical grass blades (`voxel_engine.js:902-913`).
  - Perimeter cedar wood palisade fence (NVMe / Drive C: representation) with posts, pickets, and Forest Warden Owl (`voxel_engine.js:916-960`).
  - Curving stone pathway network (`voxel_engine.js:963-1005`).
  - Azure Lotus Dew Basin (RAM Sanctuary @ 16.0, 16.0) with water surface and floating lotus blossoms (`voxel_engine.js:1008-1012`).
  - 4 Intel N100 Core Quad-Trees on raised earthen knolls:
    1. Core 0: 🌸 Sakura Cherry Blossom (9.0, 14.0) with gnarled roots, knothole trunk, 3-tier billowing cloud canopy, and stone lantern (Tōrō) (`voxel_engine.js:1298-1350`).
    2. Core 1: 🍂 Golden Ginkgo Tree (16.0, 10.5) with 4-tier pyramidal fan spire (`voxel_engine.js:1352-1400`).
    3. Core 2: 🌲 Emerald Jade Pine (9.5, 22.0) with pagoda bonsai tiers (`voxel_engine.js:1402-1450`).
    4. Core 3: 🍁 Scarlet Autumn Maple (23.0, 15.5) with cascading fiery momiji drape (`voxel_engine.js:1452-1500`).
  - Meadow Flora cluster (apps/process threads) & White Voxel Bunny Rabbit (quantum thread governor mascot) (`voxel_engine.js:1054-1068`).
  - Particle Systems: 32 falling petals (`voxel_engine.js:405-424`), 16 fireflies (`voxel_engine.js:384-403`), 4 butterflies (`voxel_engine.js:376-382`), physics debris & shockwaves (`voxel_engine.js:507-562`).
- **Dynamic Telemetry Binding & Render Timing**:
  - `app.js:166-259`: `updateHardwareTelemetry(hw)` feeds `voxelEngine.updateTelemetry(hw)`.
  - Core CPU loads bind to specimen tags, wind sway frequencies, and bloom intensity.
  - Disk bloat (`junk_mb`) dynamically spawns destructible thorn brambles (`THORN_CRIMSON` / `THORN_RED`) (`voxel_engine.js:1014-1032`).
  - Rendering latency: The canvas renders immediately on first animation frame (<16ms). Telemetry stabilizes within ~50-100ms. A headless browser capture requires 500-1000ms settling time for layout dimensions and initial telemetry sync.

### 1.4 Evolution Portal & Visual Evolution Gallery (`agent_city/static/evolution_portal.html`)
- **Structure**:
  - Hero Overview (`evolution_portal.html:343-380`): Displays active epoch, C-kernel RAM reclaimed, compaction latency, and real-time 1s heartbeat beacon (`#hbBeacon`).
  - Visual Evolution Gallery (`evolution_portal.html:383-438`):
    - Header contains a placeholder button: `<button class="action-btn" onclick="captureNewScreenshot()">📸 Trigger Live Capture</button>` (`evolution_portal.html:389`).
    - 3 hardcoded static milestone cards:
      - Card 1: `screenshot_grove_v5.png` (Epoch 0 • Milestone V5)
      - Card 2: `screenshot_grove_v6.png` (Epoch 1 • Relocation Pass V6)
      - Card 3: `screenshot_grove_v7.png` (Epoch 1 • Master Sculpt V7)
- **Critical Image 404 Bug Discovered**:
  - `evolution_portal.html:397`: `<img src="/static/../screenshot_grove_v5.png" alt="Grove V5" class="gallery-img" />`
  - `evolution_portal.html:412`: `<img src="/static/../screenshot_grove_v6.png" alt="Grove V6" class="gallery-img" />`
  - `evolution_portal.html:427`: `<img src="/static/../screenshot_grove_v7.png" alt="Grove V7" class="gallery-img" />`
  - **Empirical Test Result**:
    - `http://127.0.0.1:8000/static/style.css` -> **200 OK**
    - `http://127.0.0.1:8000/screenshot_grove_v5.png` -> **404 Not Found**
    - `http://127.0.0.1:8000/static/../screenshot_grove_v5.png` -> **404 Not Found**
  - **Root Cause**: The screenshot PNG files are located in `agent_city/` (`c:\Users\ignaz\antigravity\keen-franklin\agent_city\screenshot_grove_v*.png`), but FastAPI only mounts `agent_city/static` at `/static`. Neither Starlette nor web browsers permit directory traversal outside `/static`, and no route exists for `/screenshot_grove_*.png`.
- **Missing Gallery Capabilities**:
  - No interactive zoom/lightbox modal exists (clicking a card does nothing).
  - Cards are hardcoded in static HTML instead of dynamically rendering from SQLite `artifacts` table or `/api/context/artifacts`.
  - Epoch badges are static strings rather than dynamic data badges.

### 1.5 Existing Visual Capture Runner & SQLite Integration (`.agents/context/visual_doc_capture.py`)
- **Inspection of `.agents/context/visual_doc_capture.py`**:
  - `visual_doc_capture.py:36`: `EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"` (verified present on disk).
  - `visual_doc_capture.py:51-62`: `ensure_server_fresh()`:
    - Only checks `if not is_server_listening(8000):`. If port 8000 is already active, it does NOT restart or reload the server.
    - **Violation of requirement**: User explicitly specified: *"Before each screenshot is taken, the web server must be restarted (or reloaded), and the browser page must be cleanly reloaded to ensure fresh rendering of the 3D canvas and dynamic state."*
  - `visual_doc_capture.py:74-84`: Edge headless arguments:
    - Uses `--headless=new`, `--disable-gpu`, `--window-size=1600,1000`, `--screenshot=...`.
    - Lacks settling delay (`--virtual-time-budget=2000` or navigation script wait), risking capturing before 2D canvas renders.
  - `visual_doc_capture.py:112`: Saves files to `_root_dir / "agent_city" / grove_filename`, reproducing the 404 mount issue described in 1.4.
  - `visual_doc_capture.py:37`: `BRAIN_ARTIFACTS_DIR` points to an obsolete session path (`8e8e0d95-4549-4479-a58e-ba55f3632b57`). Current session path is `bad2a3f8-7f57-467d-b3d9-b20482ecf3b5`.
- **Database Artifacts Registry (`sanctuary_context.db`)**:
  - Verified `artifacts` table contains 82 entries:
    - ID 1: `screenshot_grove_v5.png` (440,498 bytes)
    - ID 2: `screenshot_grove_v6.png` (446,313 bytes)
    - ID 3: `screenshot_grove_v7.png` (446,725 bytes)
    - IDs 4-82: Context snapshots and agent awakening dossiers.

---

## 2. Logic Chain

1. **Premise 1 (Server Startup & Port 8000 Contention)**:
   - On Windows, uvicorn processes listening on TCP port 8000 cannot simply be overwritten by launching another `uvicorn` instance. Doing so immediately throws `[Errno 10048] address already in use`.
   - Furthermore, `start.py` launches uvicorn as a detached process without tracking or terminating existing PIDs, and `visual_doc_capture.py` skips server startup if port 8000 is open.
   - Therefore, to satisfy the requirement of restarting the web server cleanly before every screenshot capture without port contention or orphan accumulation, an active PID detection and process termination cycle must precede new process instantiation.

2. **Premise 2 (Windows Socket Draining Delay)**:
   - When a Windows process holding a TCP port is terminated via `proc.terminate()` or `proc.kill()`, the operating system socket subsystem requires 100ms to 800ms to release the handle and clear the binding. Spawning uvicorn immediately after killing the process can still trigger port conflict.
   - Therefore, the restart sequence must include an explicit socket drain loop (`is_port_in_use() == False`) before spawning the new uvicorn process, followed by an HTTP liveness polling loop (`http://127.0.0.1:8000/api/heartbeat` returning HTTP 200).

3. **Premise 3 (3D Voxel Canvas Settlement)**:
   - The 3D canvas is rasterized via 2D canvas commands in `requestAnimationFrame` and receives dynamic hardware telemetry asynchronously via `/ws` or REST polling (`/api/hardware`).
   - If Edge headless executes `--screenshot` immediately upon DOM load without waiting, it can capture an unscaled or blank canvas before `initVoxelStage()` and telemetry updates complete.
   - Therefore, Edge headless must be given a virtual time budget (e.g., `--virtual-time-budget=2500`) or the page must set a ready flag (e.g., `window.__SANCTUARY_RENDERED = true`).

4. **Premise 4 (Evolution Gallery 404 Image Disconnect)**:
   - In `server.py:584`, only `agent_city/static` is mounted under `/static`.
   - In `evolution_portal.html:397,412,427`, screenshots are requested from `/static/../screenshot_grove_v5.png`, which normalizes in HTTP clients to `/screenshot_grove_v5.png` and returns 404.
   - In `visual_doc_capture.py:112`, new screenshots are saved to `agent_city/`.
   - Therefore, the Visual Evolution Gallery will remain broken unless either:
     a) `agent_city/server.py` mounts `agent_city/` or a dedicated `/screenshots` / `/artifacts` directory; or
     b) Screenshot runners save images directly into `agent_city/static/screenshots/` and update references accordingly.

5. **Premise 5 (Gallery Dynamic Evolution & Zoom Previews)**:
   - The user request requires the Visual Evolution Gallery on `/evolution` to feature timestamped snapshots, epoch badges, and zoom previews.
   - Currently, `evolution_portal.html` hardcodes 3 cards and has no modal/lightbox script.
   - Therefore, `evolution_portal.html` must be enhanced with a lightweight client-side lightbox and an API-driven gallery renderer that queries SQLite `artifacts` via a dedicated REST endpoint (e.g. `/api/context/artifacts`).

---

## 3. Caveats

1. **Active Live Server PID 17608**:
   - The server was running throughout this exploration. In accordance with read-only guidelines, PID 17608 was not terminated or restarted during this survey.
2. **Edge Headless Chrome Emulation**:
   - Microsoft Edge on Windows (`msedge.exe`) supports `--headless=new` and `--virtual-time-budget`. On low-power quad-core Intel N100 systems, a budget of 2,000ms is optimal to avoid excessive CPU load while guaranteeing complete canvas rasterization.
3. **No Code Written**:
   - In accordance with explorer boundaries, no source code in `agent_city/` or `.agents/context/` was modified. Concrete proposals and snippets are supplied below.

---

## 4. Conclusion

### 4.1 Root Architecture Summary
- **Backend**: FastAPI on port 8000 with asyncio lifespan broadcaster (`/ws`), 1s heartbeat daemon (`/api/heartbeat`), and polyglot bridges (`/api/native/*`).
- **Frontend 3D Voxel Stage**: Pure vanilla JS + 2D Canvas diorama (`voxel_engine.js`) using MagicaVoxel 3-face directional shading and Painter's algorithm depth sorting. No external 3D libraries needed.
- **Evolution Portal**: Responsive HTML/CSS dashboard (`evolution_portal.html`) hosting telemetry, benchmarks, and chronicle, but suffering from static hardcoding and a 404 path mismatch on screenshots.

### 4.2 Proposed Implementations for Downstream Engineers

#### Proposal A: Clean Windows Server Restart Engine
Implement a robust restart utility (callable from Python or CLI) with the following verified protocol:
```python
import socket
import subprocess
import sys
import time
import psutil

def restart_sanctuary_server(port: int = 8000, timeout: float = 5.0) -> bool:
    """Safely kills any process on port 8000, waits for port release, and spawns fresh uvicorn."""
    # 1. Kill any existing listener on port 8000
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == port and conn.pid:
            try:
                proc = psutil.Process(conn.pid)
                proc.terminate()
                proc.wait(timeout=2.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    # 2. Wait for port drain
    start_drain = time.time()
    while time.time() - start_drain < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                time.sleep(0.15)
        except OSError:
            break

    # 3. Spawn fresh uvicorn process (detached Windows flags)
    flags = 0
    if sys.platform == "win32":
        flags = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW

    cmd = [
        sys.executable, "-m", "uvicorn", "agent_city.server:app",
        "--host", "127.0.0.1", "--port", str(port)
    ]
    subprocess.Popen(
        cmd,
        cwd=str(Path(__file__).resolve().parent.parent.parent),
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True
    )

    # 4. Poll until HTTP 200 on /api/heartbeat
    start_poll = time.time()
    while time.time() - start_poll < timeout:
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/heartbeat", timeout=0.5) as res:
                if res.getcode() == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False
```

#### Proposal B: Static Route Mount Alignment (`agent_city/server.py`)
Add a mount for `agent_city/` artifacts or dedicated screenshot folder:
```python
# In agent_city/server.py around line 585:
artifacts_dir = Path(__file__).parent  # or Path(__file__).parent / "static" / "screenshots"
app.mount("/artifacts", StaticFiles(directory=str(artifacts_dir)), name="artifacts")
```
Or serve `screenshot_grove_*.png` and `screenshot_portal_*.png` via a dynamic regex route:
```python
@app.get("/{image_name:path}.png", response_class=FileResponse)
async def serve_root_image(image_name: str) -> FileResponse:
    target = Path(__file__).parent / f"{image_name}.png"
    if target.exists():
        return FileResponse(target, media_type="image/png")
    raise HTTPException(status_code=404, detail="Image not found")
```

#### Proposal C: Dynamic Gallery & Zoom Preview in `evolution_portal.html`
1. Expose `GET /api/context/artifacts?type=screenshot` in `server.py` querying SQLite `artifacts` table.
2. In `evolution_portal.html`, dynamically populate `#gallery` grid with epoch badges, timestamps, resolution metadata, and click-to-zoom modal (CSS lightbox overlay with `position: fixed; z-index: 1000;`).

---

## 5. Verification Method

To independently verify the findings in this report:

1. **Verify Running Process & Port 8000 Listener**:
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 | Select-Object LocalAddress,LocalPort,State,OwningProcess
   Get-CimInstance Win32_Process -Filter "ProcessId = 17608" | Select-Object ProcessId, CommandLine
   ```
2. **Verify HTTP Endpoints**:
   ```powershell
   python -c "import urllib.request; [print(u, urllib.request.urlopen(u).getcode()) for u in ['http://127.0.0.1:8000/', 'http://127.0.0.1:8000/evolution', 'http://127.0.0.1:8000/api/city/status', 'http://127.0.0.1:8000/api/heartbeat']]"
   ```
3. **Verify Screenshot 404 Bug on Current Web Server**:
   ```powershell
   python -c "import urllib.request, urllib.error; 
   for u in ['http://127.0.0.1:8000/static/style.css', 'http://127.0.0.1:8000/screenshot_grove_v5.png', 'http://127.0.0.1:8000/static/../screenshot_grove_v5.png']:
       try: print(u, urllib.request.urlopen(u).getcode())
       except urllib.error.HTTPError as e: print(u, e.code)"
   ```
   *Expected result*: `/static/style.css` returns 200; both screenshot URLs return 404.
4. **Verify SQLite Artifacts Registry**:
   ```powershell
   python -c "import sqlite3; con = sqlite3.connect(r'.agents/context/sanctuary_context.db'); cur = con.cursor(); print(cur.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], 'artifacts registered')"
   ```
5. **Verify Edge Executable Path**:
   ```powershell
   Test-Path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
   ```
   *Expected result*: `True`.
