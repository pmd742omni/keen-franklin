# Project: Autonomous Multi-Agent Visual Documentation System

## Architecture
The system headlessly captures high-resolution visual progress snapshots of the running web application via Microsoft Edge headless, embeds them into interactive evolution galleries and Markdown snapshots, and maintains persistent documentation state across the autonomous horizon.

```
keen-franklin/
├── agent_city/
│   ├── server.py                        # FastAPI backend (port 8000), mounts /static and /screenshots
│   ├── static/
│   │   ├── index.html                   # 3D Voxel Canvas UI (/)
│   │   ├── evolution_portal.html        # Interactive Visual Evolution Gallery (/evolution)
│   │   └── voxel_engine.js              # 2.5D Voxel engine with MagicaVoxel shading
│   └── screenshots/                     # screenshot_grove_*.png, screenshot_portal_*.png
├── .agents/
│   └── context/
│       ├── sanctuary_context.db         # SQLite persistent context DB (WAL mode, artifacts table)
│       ├── visual_doc_capture.py        # 2-minute capture runner & server refresh cycle
│       ├── context_cron_markdown.py     # 5-minute Markdown snapshot generator
│       └── snapshots/                   # Markdown snapshot documents with embedded images
├── evolution/
│   └── docs/latex/
│       ├── silicon_sanctuary_report.tex # LaTeX monograph with figure embeds & empirical benchmarks
│       └── silicon_sanctuary_report.pdf # Compiled PDF
└── tests/
    └── e2e/                             # Opaque-box E2E test suite (Tiers 1-4)
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F1: Web Server Freshness Cycle | Graceful restart/reload of uvicorn server on port 8000, socket draining, clean page reload | M1 | User Request § 2026-10-10T17:03:20Z |
| 2 | F2: Edge Headless Capture Runner | Microsoft Edge headless 1080p capture of `/` and `/evolution` with virtual-time settling delay and temp user-data-dir | M1 | User Request R1 & Explorer 2 |
| 3 | F3: Static Route Mounting & 404 Fix | Mount screenshot storage directory in FastAPI (`server.py`) so `/screenshots/*` are served with HTTP 200 | M2 | Explorer 1 Survey |
| 4 | F4: Interactive Visual Evolution Gallery | Dynamic gallery on `/evolution` with epoch badges, timestamps, zoom/lightbox preview modal | M2 | User Request R2 & Explorer 1 |
| 5 | F5: Markdown Snapshot Image Synchronization | Link & embed newly captured screenshots (`![alt](path)`) into 5-minute context snapshots in `.agents/context/snapshots/` | M3 | User Request R2 & Explorer 3 |
| 6 | F6: SQLite Context Persistence & WAL Hardening | Register screenshots with dimensions & sizes in `artifacts` table; enforce WAL mode and remove DDL from GET path | M3 | User Request R3 & Explorer 3 |
| 7 | F7: LaTeX Monograph Benchmark & Figure Sync | Add `\begin{figure}` and `\includegraphics` to `silicon_sanctuary_report.tex` and compile PDF with multi-epoch benchmarks | M3 | User Request R3 & Explorer 3 |
| 8 | F8: 2-Minute Autonomous Cron Stability | Continuous 2-minute documentation daemon running cleanly alongside 1-second heartbeat without port or lock contention | M4 | User Request Acceptance Criteria |
| 9 | F9: Full E2E Verification & Adversarial Hardening | Pass 100% of E2E test suite (Tiers 1-4) followed by Tier 5 adversarial coverage hardening | M5 | Teamwork Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Server Freshness & Headless Capture Engine | Implement server restart/reload cycle, Edge headless capture runner for `/` and `/evolution` (F1, F2) | none | PLANNED |
| M2 | Static Asset Mounting & Interactive Evolution Gallery | Fix FastAPI image routes, mount `/screenshots`, implement interactive dynamic gallery with zoom on `/evolution` (F3, F4) | M1 | PLANNED |
| M3 | Context DB WAL Hardening, Markdown Image Embeds & LaTeX Sync | SQLite WAL pragmas, artifacts registration with dimensions, snapshot markdown image tags, LaTeX figures & PDF (F5, F6, F7) | M1, M2 | PLANNED |
| M4 | 2-Minute Documentation Daemon Integration | Orchestrate autonomous 2-minute cron runner with process isolation and heartbeat concurrency safety (F8) | M1, M2, M3 | PLANNED |
| M5 | Final Milestone: 100% E2E Pass & Adversarial Hardening | Pass 100% E2E test suite (Tiers 1-4) + Tier 5 Challenger adversarial hardening (F9) | M4, E2E Track | PLANNED |

## Interface Contracts
### Visual Capture Runner ↔ Web Server
- `capture_runner` queries `http://127.0.0.1:8000/api/heartbeat` -> expects HTTP 200 with status JSON.
- If restarting: terminates owning PID of port 8000, polls socket until closed, spawns detached uvicorn, polls `/api/heartbeat` until HTTP 200 (timeout: 10s).
- Capture command: `msedge.exe --headless=new --window-size=1920,1080 --virtual-time-budget=3000 --hide-scrollbars --screenshot=<output_path> <url>`.

### Capture Runner ↔ SQLite Context DB
- Connection: `sqlite3.connect(".agents/context/sanctuary_context.db", timeout=10.0)`.
- Pragmas: `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=10000; PRAGMA synchronous=NORMAL;`.
- Artifact Insert:
  `INSERT INTO artifacts (timestamp, epoch_id, artifact_name, artifact_type, file_path, file_size_bytes, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?)`.
  `metadata_json` must include `{"width": 1920, "height": 1080, "capture_type": "...", "url": "..."}`.

### FastAPI Server ↔ Frontend Gallery
- Route `/screenshots/{filename}` serves PNG files from `agent_city/screenshots/` with `media_type="image/png"`.
- Route `/api/context/artifacts` returns JSON array of screenshot artifacts with `epoch_id`, `timestamp`, `file_name`, `url`, `file_size_bytes`, `metadata`.
- Frontend `/evolution` fetches `/api/context/artifacts` and dynamically populates `.gallery-grid` with zoom preview click handler.

## Code Layout
- `agent_city/server.py`: FastAPI server routes, mounts `/screenshots`. Owned by M2 Worker.
- `agent_city/static/evolution_portal.html`: Interactive Visual Evolution Gallery. Owned by M2 Worker.
- `.agents/context/visual_doc_capture.py`: 2-minute headless screenshot runner & server cycle. Owned by M1 & M4 Workers.
- `.agents/context/context_cron_markdown.py`: Markdown snapshot generator with image links. Owned by M3 Worker.
- `.agents/context/context_manager.py`: SQLite context database connection & WAL pragmas. Owned by M3 Worker.
- `evolution/docs/latex/silicon_sanctuary_report.tex`: LaTeX report with figure embeds. Owned by M3 Worker.
- `tests/e2e/`: Opaque-box E2E test suite. Owned exclusively by E2E Testing Track.
