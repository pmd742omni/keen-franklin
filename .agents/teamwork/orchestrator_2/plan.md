# Project Architecture & Master Plan — Evolving Virtual City Multi-Agent Simulation

## 1. System Architecture

The **Evolving Virtual City** is an asynchronous, high-concurrency civic simulation engine written in Python (FastAPI, asyncio, WebSockets, Pydantic v2, SQLite WAL) coupled with a zero-dependency, modern HTML5/CSS3/ES6+ and programmatic SVG web dashboard.

```
agent_city/
├── server.py                       # FastAPI ASGI application, lifespan events, background simulation task
├── config.py                       # Global simulation constants, tick rates, grid sizing, economy parameters
├── engine/
│   ├── __init__.py
│   ├── simulation.py              # 6-phase async tick coordinator, pause/resume, speed regulation
│   ├── grid.py                    # 2D 32x32 spatial grid, zoning, terrain costs, weighted A* pathfinding
│   ├── economy.py                 # Tri-resource ledger (funds, energy, materials), treasury, sales & property tax
│   ├── message_bus.py             # Multi-channel pub/sub, targeted messaging, public broadcast, consensus voting
│   └── persistence.py             # SQLite WAL snapshotting (6 tables), JSON export/import, headless runner
├── agents/
│   ├── __init__.py
│   ├── base.py                    # BaseAgent Pydantic models, 8-state FSM, 4-tier goal hierarchy, utility engine
│   ├── roles.py                   # 6 Civic Roles: Mayor, Architect, Engineer, Merchant, Scholar, Observer
│   ├── subagents.py               # Hierarchical subagent spawning (Surveyor, ConstructionCrew, ResearchAssistant, Courier, DistrictSupervisor)
│   ├── decision.py                # Action evaluation, needs urgency, trait cosine alignment, congestion penalty
│   └── evolution.py               # 7-D trait vectors, epoch multi-objective fitness evaluation, guided centroid adaptation
├── api/
│   ├── __init__.py
│   ├── routes.py                  # REST API (/api/city/status, /api/agents, /api/buildings, /api/events, /api/controls, /api/snapshot/*)
│   └── websocket.py               # /ws endpoint, differential delta broadcast (< 1.5 KB/tick), client heartbeat
├── static/                        # Zero-dependency frontend (pure vanilla HTML5/CSS3/SVG/ES6+)
│   ├── index.html                 # Cyber-civic dashboard layout, viewport, control panel, HUD, drawer
│   ├── css/
│   │   └── style.css              # Modern CSS, custom properties, glassmorphism, responsive grid
│   └── js/
│       ├── app.js                 # WebSocket client, differential delta reconciler, control event handlers
│       ├── renderer.js            # Programmatic SVG engine, dual projection (Isometric 2.5D + Orthographic CAD)
│       ├── agent_view.js          # 60 FPS LERP motion interpolation, role badges, speech bubbles, vital halos
│       └── charts.js              # Pure Canvas sparkline charts, SVG zoning donut, live logs, agent inspector
├── tests/                         # Comprehensive pytest test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_engine.py             # Spatial grid, A* pathing, 6-phase simulation loop, economy, message bus
│   ├── test_agents.py             # 8-state FSM, goal tiers, utility math, 6 civic roles, trait evolution
│   ├── test_subagents.py          # Parent-child tracking, escrow deposit/refund, concurrency caps, retirement
│   ├── test_api_websocket.py      # REST endpoints and WebSocket differential stream sync
│   ├── test_persistence.py        # SQLite WAL transactions, JSON snapshots, pause/resume, headless mode
│   └── test_e2e_city.py           # 100-tick continuous simulation, multi-agent emergence, stability
├── start_city.bat                 # Windows quick-start launcher with automated browser opening
├── start_city.sh                  # Unix/macOS quick-start launcher
├── requirements.txt               # Backend dependencies (fastapi, uvicorn, pydantic, websockets, pytest, etc.)
└── README.md                      # Architecture guide, quick-start instructions, REST & WebSocket documentation
```

---

## 2. Complete Merged Feature Inventory

| # | Feature ID | Name | Description | Milestone | Source |
|---|------------|------|-------------|-----------|--------|
| 1 | F-ENG-01 | 6-Phase Simulation Loop | Inbound command ingestion, agent perception/deliberation, spatial movement/collision, environmental/economic ticks, WebSocket delta broadcast, drift compensation | M1 | Survey 1 (R1) |
| 2 | F-ENG-02 | 2D Spatial Grid & Zoning | 32x32 grid with zones (Residential, Commercial, Industrial, Civic, Park, Road) and spatial collision hashing | M1 | Survey 1 (R1) |
| 3 | F-ENG-03 | Weighted A* Pathfinding | 4-directional pathfinding with terrain costs (Road=1.0, Park=1.5, Wilderness=2.0, Occupied=Inf) | M1 | Survey 1 (R1) |
| 4 | F-ENG-04 | Tri-Resource Economy | Funds, Energy, Materials balance; consumption, commercial trade, public treasury and taxation | M1 | Survey 1 (R1) |
| 5 | F-ENG-05 | Inter-Agent Message Bus | 1:1 direct messaging, public broadcast, topic channels (#governance, #trade, #construction) | M1 | Survey 1 (R1) |
| 6 | F-ENG-06 | Democratic Consensus Voting | Civic proposals, quorum voting (>50%), automated policy/tax rate execution | M1 | Survey 1 (R1) |
| 7 | F-AGT-01 | BaseAgent & 8-State FSM | IDLE, PERCEIVING, DELIBERATING, MOVING, EXECUTING, COMMUNICATING, RESTING, RETIRED | M2 | Survey 2 (R1, R2) |
| 8 | F-AGT-02 | 4-Tier Goal Hierarchy | Homeostasis (energy < 15) > Civic Mandate > Socio-Economic > Self-Actualization | M2 | Survey 2 (R1) |
| 9 | F-AGT-03 | Multi-Criteria Utility Engine | U(a) math combining need urgency, role alignment, trait cosine similarity, economic feasibility | M2 | Survey 2 (R1) |
| 10 | F-AGT-04 | 6 Distinct Civic Roles | Mayor, Architect, Engineer, Merchant, Scholar, Observer with distinct agendas & action sets | M2 | Survey 2 (R1) |
| 11 | F-AGT-05 | Hierarchical Subagent Spawning | Parent-child contracts, temporary (Surveyor, ConstructionCrew, ResearchAssistant, Courier) & permanent (DistrictSupervisor) | M2 | Survey 2 (R2) |
| 12 | F-AGT-06 | Subagent Resource Escrow & Retirement | Upfront escrow deposit, unused resource refund, task result handback, automatic memory cleanup | M2 | Survey 2 (R2) |
| 13 | F-AGT-07 | Generative Evolution & Traits | 7-D trait vectors, epochal multi-objective fitness evaluation, elitism, guided centroid adaptation | M2 | Survey 2 (R2) |
| 14 | F-API-01 | FastAPI Application & REST Endpoints | /api/city/status, /api/agents, /api/buildings, /api/events, /api/controls, /api/snapshot/* | M3 | Survey 3 (R1, R4) |
| 15 | F-API-02 | WebSocket Differential Streaming | /ws endpoint with INIT_STATE and compact TICK_DELTA (< 1.5 KB/tick), client heartbeats | M3 | Survey 3 (R4) |
| 16 | F-API-03 | SQLite WAL State Persistence | 6 relational tables storing ticks, agents, parcels, buildings, events, and transactions | M3 | Survey 3 (R4) |
| 17 | F-API-04 | JSON Snapshot Export & Import | Single-file portable state serialization, pause, save, resume, and headless CLI runner | M3 | Survey 3 (R4) |
| 18 | F-UI-01 | Zero-Dependency Web Dashboard | Pure HTML5/CSS3/ES6+ cyber-civic UI layout, responsive grid, glassmorphic panels | M4 | Survey 3 (R3) |
| 19 | F-UI-02 | Programmatic SVG Visualizer | Dual projection: 2.5D Isometric (depth sorted x+y) + 2D Orthographic CAD toggle | M4 | Survey 3 (R3) |
| 20 | F-UI-03 | Dynamic Building & Road Graphics | 5-stage building evolution sprites, 4-bit road adjacency solver, 120-tick day/night filter | M4 | Survey 3 (R3) |
| 21 | F-UI-04 | Dynamic Agent Rendering & Motion | 60 FPS LERP motion interpolation, role badges, speech bubbles, vital status halos | M4 | Survey 3 (R3) |
| 22 | F-UI-05 | Analytics HUD & Inspection Drawer | Pure Canvas sparklines (Pop, Subagents, Treasury, Energy), SVG zoning donut, agent inspector | M4 | Survey 3 (R3) |
| 23 | F-UI-06 | Interactive Simulation Controls | Pause, resume, tick speed slider, manual event triggers (resource windfall, zoning mandate) | M4 | Survey 3 (AC) |
| 24 | F-PKG-01 | Cross-Platform Launcher Scripts | start_city.bat and start_city.sh with environment validation and automated browser launch | M5 | Survey 3 (AC) |
| 25 | F-TST-01 | Comprehensive Automated Test Suite | Opaque-box E2E test harness across Tiers 1-4, verifying all components and 100-tick stability | E2E | All Surveys (AC) |

---

## 3. Interface Contracts

### 3.1 Simulation Engine ↔ Agents
- `SimulationCoordinator.step()` calls `agent.perceive(grid_view, public_messages)`
- `agent.deliberate()` returns `AgentAction(type, target_pos, payload)`
- `SimulationCoordinator.resolve_actions()` verifies energy/economic feasibility, updates spatial coordinates in `grid.py`, and records economic transactions in `economy.py`.
- `agent.spawn_subagent(archetype, task, budget)` calls `SimulationCoordinator.register_agent()` with `parent_id` and escrow locks.

### 3.2 Simulation Engine ↔ API & WebSocket
- `SimulationCoordinator.get_init_state() -> InitStateMessage` (full snapshot of grid, zoning, buildings, all active agents, treasury).
- `SimulationCoordinator.get_tick_delta() -> TickDeltaMessage` (tick number, simulation speed, changed agent positions/states/dialogues, newly constructed buildings, treasury balance, active events).
- `routes.py` and `websocket.py` send control commands (`pause`, `resume`, `set_speed`, `trigger_event`, `save_snapshot`) into `SimulationCoordinator.command_queue`.

### 3.3 Backend WebSocket ↔ Frontend Client
- On connection: Server transmits `INIT_STATE`.
- On every simulation tick: Server transmits `TICK_DELTA`.
- Client transmits: `{"type": "CONTROL", "action": "PAUSE" | "RESUME" | "SET_SPEED" | "TRIGGER_EVENT", "payload": {...}}`.
- Client `AgentAnimator` consumes `TICK_DELTA` and interpolates agent positions from `(x_prev, y_prev)` to `(x_curr, y_curr)` using `easeInOutQuad` over `tick_duration_ms`.

---

## 4. Milestones & Dependency Graph

```
[Phase 0: Survey] (COMPLETE)
        │
        ├───► [E2E Testing Track: Test Writer] (Tiers 1-4 Test Suite)
        │               │
        │               ▼
        ├───► [Milestone 1: Core Engine & Data Models] (Grid, Economy, Message Bus)
        │               │
        │               ▼
        ├───► [Milestone 2: Agent Lifecycle & Spawning] (FSM, 6 Roles, Subagents, Evolution)
        │               │
        │               ▼
        ├───► [Milestone 3: Server, REST API & Streaming] (FastAPI, WebSockets, SQLite Persistence)
        │               │
        │               ▼
        ├───► [Milestone 4: Programmatic SVG Visualizer] (Vanilla JS, SVG Map, LERP, HUD, Controls)
        │               │
        │               ▼
        └───► [Milestone 5: Launchers, Packaging & 100% E2E Verification] (start_city.bat/sh, Final Audit)
```

---

## 5. Verification Commands
- Python executable: `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Test command: `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest tests/ -v`
- Server run command: `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000`
