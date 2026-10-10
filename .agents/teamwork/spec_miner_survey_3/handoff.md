# Specification Mining Survey: Database, Monograph, Context Snapshots & Concurrency Architecture

**Investigator**: Explorer 3 (Database & Monograph Spec Miner)  
**Parent Orchestrator**: `fe4e8efd-4d28-402d-b25d-f103e6dde375`  
**Working Directory**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\spec_miner_survey_3`  
**Status**: COMPLETE (Hard Handoff)  
**Date**: 2026-10-10  

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | SQLite DB | `sanctuary_context.db` Schema | Relational SQLite persistence database housing 5 core tables (`epochs`, `benchmarks`, `rate_limits`, `agent_memories`, `artifacts`). | SQL queries via sqlite3 API / CLI | Rows, counts, relational records | Database locks if file locked or corrupted | `.agents/context/context_manager.py:24-95`, `inspect_db.py` |
| 2 | SQLite DB | `artifacts` Table Registry | Indexes all visual and documentation artifacts (screenshots, markdown snapshots, dossiers, PDFs). | `timestamp`, `epoch_id`, `artifact_name`, `artifact_type`, `file_path`, `file_size_bytes`, `metadata_json` | Registered row in SQLite with AUTOINCREMENT ID | Unhandled if path missing size=0; silently registers | `.agents/context/context_manager.py:83-93`, `SCHEMA.md:68-81` |
| 3 | SQLite DB | `benchmarks` Table Telemetry | Captures empirical memory compaction, latency, and system performance metrics. | `timestamp`, `epoch_id`, `metric_name`, `value_numeric`, `unit`, `notes` | Telemetry row with numeric value and units | Coerces `value` to `float()` in Python; fails on non-numeric string | `.agents/context/context_manager.py:44-54`, `SCHEMA.md:24-37` |
| 4 | SQLite DB | `epochs` Table Timeline | Tracks 28 evolution epochs across the 336-hour autonomous horizon. | `epoch_id` (PK), `title`, `phase`, `started_at`, `completed_at`, `status`, `deliverables_json`, `summary` | Epoch record; upserted via `ON CONFLICT(epoch_id) DO UPDATE` | Fails if non-integer PK provided without conflict resolution | `.agents/context/context_manager.py:31-41`, `SCHEMA.md:8-21` |
| 5 | SQLite DB | `rate_limits` Table Tracking | Tracks token budget consumption, window headroom %, step index, and liveness states. | `timestamp`, `tokens_used`, `tokens_headroom_pct`, `step_index`, `rate_limit_state`, `notes` | Logged rate limit row | Fails if `rate_limit_state` is null | `.agents/context/context_manager.py:57-67`, `SCHEMA.md:39-52` |
| 6 | SQLite DB | `agent_memories` Shared Memory | Deliberation log, reflections, decisions, and heartbeat pulse records across agent cohort. | `timestamp`, `agent_name`, `memory_type`, `key`, `content_json` | Serialized JSON payload row | Auto-serializes dict/list with `json.dumps()` | `.agents/context/context_manager.py:70-79`, `SCHEMA.md:54-66` |
| 7 | Snapshot Engine | 5-Minute Context Markdown Snapshot | Periodic aggregation of system vitals, hardware metrics, recent benchmarks, voxel garden state, and agent directives. | Reads `heartbeat.json`, `sanctuary_context.db`, `evolution_state.json` | Generated `context_snapshot_epoch01_*.md` in `.agents/context/snapshots/` and updated `latest_context_snapshot.md` | Warns to stderr on DB write failure; continues loop | `.agents/context/context_cron_markdown.py:42-226` |
| 8 | Snapshot Engine | 2-Minute Multi-Agent Awakening Dossier | High-frequency agent awakening and directive dispatch with token allocation percentages. | Reads `heartbeat.json`, `sanctuary_context.db` | Generates `agent_awakening_epoch01_*.md` and updates `shared_agent_context.json` | Catches DB warning per agent; logs to stderr | `.agents/context/agent_awakening_cron.py:75-210` |
| 9 | Monograph Engine | LaTeX Academic Monograph (`.tex`) | Formal academic monograph summarizing Intel N100 architecture, polyglot kernel, 3D botanical voxel garden, and empirical compaction benchmarks. | Source LaTeX at `evolution/docs/latex/silicon_sanctuary_report.tex` | Compiled 3-page PDF at `evolution/docs/latex/silicon_sanctuary_report.pdf` | Missing visual `\includegraphics` figures; missing Epoch 1 benchmarks | `evolution/docs/latex/silicon_sanctuary_report.tex:1-116` |
| 10 | Concurrency | 1-Second Heartbeat Cron | Sub-second liveness pulse verifying port 8000, CPU/RAM, and token headroom. | Socket connection to 127.0.0.1:8000, `psutil` | Atomic temp-file replacement of `.agents/context/heartbeat.json`; flushes to DB every 10 ticks | Catches socket refusal; increments `consecutive_server_failures` | `.agents/context/system_heartbeat_cron.py:46-145` |
| 11 | Visual Capture | Edge Headless Screenshot Runner | Headless browser capture of 3D Voxel Grove (`/`) and Evolution Portal (`/evolution`). | Microsoft Edge CLI (`--headless=new`, `--screenshot`, `--window-size=1600,1000`) | Timestamped PNG files in `agent_city/` and artifact repository | Re-tries server launch if port 8000 not listening; fails if output size < 1000B | `.agents/context/visual_doc_capture.py:46-164` |
| 12 | Web Serving | FastAPI Context & Monograph Endpoints | Exposes `/api/context/summary`, `/api/context/benchmarks`, `/docs/latex/silicon_sanctuary_report.pdf`, `/evolution`. | HTTP GET requests from client | JSON responses, PDF FileResponse, HTML FileResponse | Crashes/returns 500 if DB locked or unhandled exception occurs | `agent_city/server.py:317-333, 582-667` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | SQLite Schema vs Markdown Cron | `context_cron_markdown.py` reading benchmark columns | Script extracts `b.get('metric_value')` and `b.get('metric_unit')`, but table schema columns are `value_numeric` and `unit`. Result: Markdown table renders blank/empty values (`****` and blank unit). |
| 2 | SQLite Journal Mode Under Concurrency | Multi-process writes from 2 heartbeat daemons + 2 markdown crons + 1 awakening cron | Current `PRAGMA journal_mode` is `DELETE` with `synchronous=2` (FULL). When multiple processes execute concurrent writes, writer lock blocks all readers and other writers, risking `sqlite3.OperationalError: database is locked`. |
| 3 | FastAPI DDL Execution on Request Path | Any HTTP request to `/api/context/summary` or `/api/context/benchmarks` | Instantiates `ContextManager()`, which immediately executes `init_database()`, issuing 5 `CREATE TABLE IF NOT EXISTS` DDL statements with commits on every single read request, causing table lock contention. |
| 4 | Web Browser Image Resolution for Gallery | Image path `<img src="/static/../screenshot_grove_v5.png">` | Standard browser URL normalization resolves `/static/../screenshot_grove_v5.png` to `/screenshot_grove_v5.png`. In `agent_city/server.py`, only `/static` is mounted to `agent_city/static/`, so requests to `/screenshot_grove_v5.png` return 404 unless routed. |
| 5 | Background Process Duplication | `check_procs.py` process enumeration | Found duplicate instances of `system_heartbeat_cron.py` (PIDs 14236 and 20756) and `context_cron_markdown.py` (PIDs 14348 and 28292) across two Python environments (`hermes-agent\venv` and `uv\python\cpython-3.11.11`). Both write to same SQLite DB and heartbeat file. |
| 6 | LaTeX Monograph Visual Figures | `evolution/docs/latex/silicon_sanctuary_report.tex` compilation | Package `\usepackage{graphicx}` is imported, but file contains zero `\begin{figure}` or `\includegraphics` tags. Generated PDF has no visual screenshots or evolution illustrations. |
| 7 | Fresh Web Server Restart Cycle | User requirement: restart/reload server before screenshot | `visual_doc_capture.py` currently checks `is_server_listening(8000)` and only launches if offline. It does not perform a graceful restart/recycle or wait for dynamic 3D settlement before capture. |

---

## 1. Observation

### 1.1 SQLite `sanctuary_context.db` Schema & Status
- **Exact Path**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\context\sanctuary_context.db`
- **File Size**: `196,608` bytes (192 KB).
- **Current Pragmas Observed**:
  - `journal_mode: delete` (Verbatim from `PRAGMA journal_mode;`)
  - `busy_timeout: 5000` (Verbatim from `PRAGMA busy_timeout;` — default Python sqlite3 timeout)
  - `synchronous: 2` (Verbatim from `PRAGMA synchronous;` — FULL synchronous mode)
  - `foreign_keys: 0` (Foreign keys disabled)
  - `wal_autocheckpoint: 1000`
- **Table DDLs and Columns**:
  1. **`artifacts`** (Row count: 58):
     ```sql
     CREATE TABLE artifacts (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         timestamp TEXT NOT NULL,
         epoch_id INTEGER,
         artifact_name TEXT NOT NULL,
         artifact_type TEXT NOT NULL,
         file_path TEXT NOT NULL,
         file_size_bytes INTEGER,
         metadata_json TEXT
     );
     ```
     Columns:
     - `id`: INTEGER, Primary Key (Auto-increment)
     - `timestamp`: TEXT NOT NULL (ISO 8601 string, e.g. `2026-10-10T17:03:50.483051`)
     - `epoch_id`: INTEGER, Nullable (Associated evolution epoch, e.g. `0`, `1`)
     - `artifact_name`: TEXT NOT NULL (e.g. `screenshot_grove_v5.png`, `context_snapshot_epoch01_20261010_191745.md`, `agent_awakening_epoch01_20261010_191640.md`)
     - `artifact_type`: TEXT NOT NULL (Observed types: `'screenshot'`, `'markdown_context_snapshot'`, `'shared_agent_awakening_dossier'`; planned: `'screenshot_3d_grove'`, `'screenshot_evolution_portal'`, `'latex_pdf'`, `'binary'`)
     - `file_path`: TEXT NOT NULL (e.g. `agent_city/screenshot_grove_v5.png`, `C:\Users\ignaz\antigravity\keen-franklin\.agents\context\snapshots\...`)
     - `file_size_bytes`: INTEGER, Nullable (e.g. `440498`, `5604`, `2907`)
     - `metadata_json`: TEXT, Nullable (JSON dictionary with fields like `iteration`, `hb_tick`, `ram_pct`, `headroom_pct`, `cycle`, `url`, `timestamp`)
  2. **`benchmarks`** (Row count: 4):
     ```sql
     CREATE TABLE benchmarks (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         timestamp TEXT NOT NULL,
         epoch_id INTEGER,
         metric_name TEXT NOT NULL,
         value_numeric REAL NOT NULL,
         unit TEXT NOT NULL,
         notes TEXT
     );
     ```
     Current rows verbatim:
     - ID 1: Epoch 0 | `RAM Reclaimed (C-Kernel)` | `3859.75` MB | `Win32 psapi K32EmptyWorkingSet compaction`
     - ID 2: Epoch 0 | `Compaction Latency` | `3398.77` ms | `Scanned 297 processes, trimmed 129`
     - ID 3: Epoch 1 | `RAM Reclaimed (C-Kernel)` | `3698.69` MB | `Win32 psapi K32EmptyWorkingSet compaction across 143 trimmed processes`
     - ID 4: Epoch 1 | `Compaction Latency` | `5518.06` ms | `Scanned 316 processes, trimmed 143 processes`
  3. **`epochs`** (Row count: 2):
     ```sql
     CREATE TABLE epochs (
         epoch_id INTEGER PRIMARY KEY,
         title TEXT NOT NULL,
         phase TEXT NOT NULL,
         started_at TEXT NOT NULL,
         completed_at TEXT,
         status TEXT NOT NULL DEFAULT 'pending',
         deliverables_json TEXT,
         summary TEXT
     );
     ```
     Current rows verbatim:
     - Epoch 0: `Polyglot Native Core Genesis` | Phase: `Genesis` | Status: `completed` | Summary: `C-Kernel, Rust Sentinel, Java Bridge compiled and tested.`
     - Epoch 1: `Topography Refinement & Botanical Sculpting Pass 2` | Phase: `Refinement` | Status: `active` | Summary: `Volumetric Sakura cloud canopy and Ginkgo 16.0, 10.5 relocation.`
  4. **`rate_limits`** (Row count: 597+):
     ```sql
     CREATE TABLE rate_limits (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         timestamp TEXT NOT NULL,
         tokens_used INTEGER,
         tokens_headroom_pct REAL,
         step_index INTEGER,
         rate_limit_state TEXT NOT NULL,
         notes TEXT
     );
     ```
  5. **`agent_memories`** (Row count: 184+):
     ```sql
     CREATE TABLE agent_memories (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         timestamp TEXT NOT NULL,
         agent_name TEXT NOT NULL,
         memory_type TEXT NOT NULL,
         key TEXT NOT NULL,
         content_json TEXT NOT NULL
     );
     ```

### 1.2 `.agents/context/snapshots/` Directory and Formats
- **Exact Path**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\context\snapshots`
- **File Count**: 55 files total.
- **Snapshot File Types**:
  1. `context_snapshot_epoch01_YYYYMMDD_HHMMSS.md` (5-minute periodic cron, ~5.6 KB, 94 lines).
     - Contains: Header metadata, Section 1 (System Liveness & Rate Limit Sentinel table), Section 2 (Polyglot Native Core & Recent Database Benchmarks table), Section 3 (Botanical Voxel Garden State), Section 4 (Multi-Agent Cohort Awakening Roster & Mermaid diagram), Section 5 (Artifact Manifest & Verification Links).
     - *Defect in Benchmark Table Rendering*: In `context_cron_markdown.py:138`:
       `| {b.get('id', '')} | {ts} | {b.get('metric_name', '')} | **{b.get('metric_value', '')}** | {b.get('metric_unit', '')} | {b.get('notes', '')} |`
       In the database, the column names are `value_numeric` and `unit`. Because `b.get('metric_value', '')` is used, the snapshot outputs `****` instead of numbers.
     - *Screenshot Linking Gap*: Section 5 only links to `.pdf`, `.tex`, `.db`, `evolution_portal.html`, and `CHRONICLE.md`. It contains NO embedded images (`![alt](...)`) and NO direct links to newly captured screenshot artifacts (`screenshot_grove_*.png`, `screenshot_portal_*.png`).
  2. `agent_awakening_epoch01_YYYYMMDD_HHMMSS.md` (2-minute agent awakening cron, ~2.9 KB, 60 lines).
     - Contains: Header metadata, Section 1 (System Telemetry table), Section 2 (Roster for `BotanicalMasterSculptor`, `KernelOptimizerDaemon`, `ContextManagerSentinel`, `PolyglotBridgeCoordinator`, `LaTeXMonographArchitect` with token percentages 25%, 20%, 20%, 15%, 20%), Section 3 (Shared DB and JSON memory links).

### 1.3 LaTeX Monograph: `silicon_sanctuary_report.tex` and `.pdf`
- **TeX Source Path**: `c:\Users\ignaz\antigravity\keen-franklin\evolution\docs\latex\silicon_sanctuary_report.tex` (116 lines, 9,073 bytes)
- **PDF File Path**: `c:\Users\ignaz\antigravity\keen-franklin\evolution\docs\latex\silicon_sanctuary_report.pdf` (3 pages)
- **Content Inspection**:
  - `\usepackage{graphicx}` is declared on line 5.
  - Zero `\begin{figure}` or `\includegraphics` tags exist anywhere in the `.tex` file.
  - Section 4 (Empirical Benchmarks, Table 1, lines 85-102) contains only Epoch 0 initial numbers (3,859.75 MB RAM reclaimed, 3,398.77 ms latency, 297 scanned / 129 trimmed processes). It does not reflect Epoch 1 compaction results from SQLite `benchmarks` (ID 3 & 4: 3,698.69 MB, 5,518.06 ms latency, 316 scanned / 143 trimmed processes).
  - Section 5 mentions the 336-hour evolution and context management but contains no visual progression figures or comparisons.

### 1.4 Concurrency, Locking & Running Processes
- **Running Python Processes** (`check_procs.py` output):
  - PID 14236: `system_heartbeat_cron.py --interval 1.0 --db-flush 10` (running from `uv\python\cpython-3.11.11`)
  - PID 20756: `system_heartbeat_cron.py --interval 1.0 --db-flush 10` (running from `hermes-agent\venv`)
  - PID 14348: `context_cron_markdown.py --interval 300` (running from `hermes-agent\venv`)
  - PID 28292: `context_cron_markdown.py --interval 300` (running from `uv\python\cpython-3.11.11`)
  - PID 22600: `agent_awakening_cron.py --interval 120` (running from `uv\python\cpython-3.11.11`)
  - PID 17608 & PID 23744: `uvicorn agent_city.server:app --host 127.0.0.1 --port 8000`
- **Database Connection Pattern in `context_manager.py`**:
  - Lines 18-22: `conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row; return conn`
  - No `timeout` parameter specified in `sqlite3.connect` (default 5.0 seconds).
  - No `PRAGMA journal_mode=WAL;` executed.
  - No `PRAGMA busy_timeout = 10000;` executed.
  - In `ContextManager.__init__()` (line 102): `init_database()` is invoked every time `ContextManager()` is instantiated.
- **FastAPI Endpoints in `agent_city/server.py`**:
  - `/api/context/summary` (lines 318-333, 615-630) creates `ContextManager()`, triggering 5 `CREATE TABLE IF NOT EXISTS` DDL statements with commits on every incoming HTTP GET request.
  - `/api/context/benchmarks` (lines 632-642) creates `ContextManager()`, triggering 5 DDL statements on every incoming request.

---

## 2. Logic Chain

1. **Database Schema & Table Integrity**:
   - The authoritative schema in `SCHEMA.md` defines 5 tables: `epochs`, `benchmarks`, `rate_limits`, `agent_memories`, `artifacts`.
   - Inspection of `sanctuary_context.db` confirms all 5 tables are physically instantiated with exact column signatures and types matching `SCHEMA.md`.
   - The `artifacts` table currently stores 58 rows across types `'screenshot'`, `'markdown_context_snapshot'`, and `'shared_agent_awakening_dossier'`.
   - However, new visual screenshot artifacts (`screenshot_grove_epoch01_*.png`, `screenshot_portal_epoch01_*.png`) defined in `visual_doc_capture.py` are not yet appearing because `visual_doc_capture.py` has not been running continuously.

2. **Snapshot Rendering and Tag Formatting**:
   - The 5-minute markdown snapshot in `.agents/context/snapshots/` is synthesized by `context_cron_markdown.py`.
   - When inspecting `context_snapshot_epoch01_20261010_191745.md`, the benchmark values appear as `****` because the script accesses `b['metric_value']` and `b['metric_unit']`, whereas the database returns `value_numeric` and `unit`.
   - Acceptance criteria require generated Markdown snapshots to include clickable links and embedded image tags to the captured screenshots (`![alt](path)`).
   - Currently, `context_cron_markdown.py` does not query the `artifacts` table for screenshots, so Section 5 contains only links to document files and no image embeds.

3. **LaTeX Monograph Evolution & Visual Alignment**:
   - ORIGINAL_REQUEST §R3 requires: "keeping the LaTeX monograph (silicon_sanctuary_report.tex / compiled .pdf) aligned with empirical visual benchmarks."
   - Inspection of `silicon_sanctuary_report.tex` and `.pdf` reveals that while `\usepackage{graphicx}` is imported, there are zero visual figures or screenshots embedded.
   - Table 1 in the monograph contains only the initial baseline benchmark, leaving out the subsequent Epoch 1 benchmark (3,698.69 MB reclaimed).
   - Therefore, to satisfy the monograph requirements, the LaTeX source must incorporate `\begin{figure}` blocks referencing screenshots from `agent_city/` and an expanded empirical benchmarks table reflecting multi-epoch data from `sanctuary_context.db`.

4. **Concurrency Contention and Locking Safety**:
   - SQLite under default `DELETE` journal mode locks the entire file during any write operation.
   - The process survey revealed that there are two duplicate heartbeat daemons flushing to SQLite every 10 seconds, two duplicate 5-minute markdown crons, and a 2-minute awakening cron inserting 6 records per cycle.
   - Simultaneously, FastAPI serves `/api/context/summary` and `/api/context/benchmarks`, each calling `ContextManager.__init__()` which executes DDL (`CREATE TABLE IF NOT EXISTS`) and commits on every read.
   - Under Windows NTFS file semantics, concurrent writes and DDL under `DELETE` journal mode with default 5-second timeouts create high risk of `sqlite3.OperationalError: database is locked`.
   - To guarantee zero locking errors across the 336-hour horizon, the database must be configured with `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`, `PRAGMA busy_timeout = 10000;`, and `init_database()` must be removed from the request path.

---

## 3. Caveats

1. **Running Processes Not Modified**: In accordance with the read-only exploration constraint, running duplicate processes (PIDs 14236/20756 and 14348/28292) were not terminated. The orchestrator / implementer must deduplicate them when launching the unified documentation suite.
2. **Browser Headless Execution**: Microsoft Edge headless binary location was verified at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, but headless runs were not triggered during this exploration to avoid side-effects on running services.
3. **TeX Live Distribution**: `silicon_sanctuary_report.pdf` exists and is verified to be compiled from October 10, 2026. `pdflatex` or `xelatex` command availability in PATH was not directly invoked to avoid altering compilation artifacts.

---

## 4. Conclusion

The specification mining investigation has uncovered the complete operational blueprint and precise areas requiring enhancement:

1. **Database Specifications**: `sanctuary_context.db` possesses the full relational schema defined in `SCHEMA.md`. The `artifacts` table contains 58 entries and is ready to index 2-minute visual captures (`screenshot_3d_grove` and `screenshot_evolution_portal`) alongside `markdown_context_snapshot` and `shared_agent_awakening_dossier`.
2. **Markdown Snapshot Specifications**:
   - The column key mismatch in `context_cron_markdown.py` (`metric_value` vs `value_numeric`) must be corrected to display real benchmark values in Section 2.2.
   - Section 3 / Section 5 of the 5-minute snapshots must query `artifacts` for recent screenshot records and render clickable embedded image tags:
     `![3D Voxel Grove](<relative_or_file_path>)` and `[![Evolution Portal](<path>)](http://127.0.0.1:8000/evolution)`.
3. **LaTeX Monograph Specifications**:
   - `silicon_sanctuary_report.tex` is well-structured (116 lines) but currently lacks visual figures.
   - It requires the addition of `\begin{figure}[h] \includegraphics[width=...]{...} \caption{...} \end{figure}` elements displaying the 3D Voxel Canvas and Evolution Portal, plus an updated Table 1 syncing both Epoch 0 and Epoch 1 compaction benchmarks.
4. **Database Safety & Concurrency Rules**:
   - `sanctuary_context.db` must be switched to WAL mode via `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`.
   - Connections in `context_manager.py` must enforce `conn.execute("PRAGMA busy_timeout = 10000;")` (or pass `timeout=10.0` in `connect`).
   - `init_database()` must be decoupled from `ContextManager.__init__()` to avoid executing DDL on every HTTP GET request.
   - Running background cron daemons must be deduplicated to ensure exactly one heartbeat daemon, one 2-minute documentation capture daemon, and one 5-minute context snapshot daemon operate across the system.

---

## 5. Verification Method

To independently verify the observations and specifications documented in this report:

1. **Verify SQLite Database Schema and Pragmas**:
   ```powershell
   python -c "import sqlite3; conn = sqlite3.connect(r'.agents\context\sanctuary_context.db'); print('journal_mode:', conn.execute('PRAGMA journal_mode;').fetchone()[0]); print('busy_timeout:', conn.execute('PRAGMA busy_timeout;').fetchone()[0]); print('tables:', [r[0] for r in conn.execute('SELECT name FROM sqlite_master WHERE type=\'table\';').fetchall()]); print('artifacts count:', conn.execute('SELECT COUNT(*) FROM artifacts;').fetchone()[0]); conn.close()"
   ```
2. **Inspect 5-Minute Context Snapshots and Check Column Name Mismatch**:
   ```powershell
   Get-ChildItem -Path .agents\context\snapshots\context_snapshot_*.md | Select-Object -Last 1 | Get-Content | Select-String -Pattern "Compaction Latency" -Context 0,2
   ```
3. **Verify LaTeX Source for Absence of Figures and PDF Existence**:
   ```powershell
   Select-String -Path evolution\docs\latex\silicon_sanctuary_report.tex -Pattern "includegraphics"
   Test-Path evolution\docs\latex\silicon_sanctuary_report.pdf
   ```
4. **Verify Active Python Background Daemons**:
   ```powershell
   Get-Process python | Select-Object Id, ProcessName, WorkingSet64
   ```
