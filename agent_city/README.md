# Agent Metropolis — Virtual City of Evolving Agents

An autonomous multi-agent urban simulation that pairs a resilient **Python FastAPI / asyncio** backend with an expressive, adaptive **Vanilla JavaScript & Programmatic SVG** visualizer. Autonomous agents and hierarchical subagents fulfill civic roles, debate proposals, construct buildings, manage economic supply chains, spawn specialized subagents, and evolve across simulation epochs.

---

## Key Highlights

- **6 Autonomous Civic Roles**: Mayor, Architect, Engineer, Merchant, Scholar, and Observer.
- **Hierarchical Subagent Spawning**: Civic agents dynamically spawn specialized subordinate agents (Surveyors, Construction Crews, Research Assistants, Couriers) using escrow-backed `DelegationContract`s and retire them upon mission completion.
- **7-Dimensional Trait Vectors & Evolution**: Generational trait inheritance and mutation (Ambition, Diligence, Sociability, Innovation, Thriftiness, Altruism, Adaptability).
- **Expressive Programmatic SVG Art**: Zero external JavaScript or CSS dependencies. Renders interactive city zoning, buildings, smooth agent movement, and speech bubbles directly on an HTML5 SVG canvas.
- **Differential WebSocket Streaming**: Low-latency `< 1.5 KB` delta frames broadcasted every tick over `/ws`.
- **100% Tested**: Comprehensive 74-test test suite across all 4 tiers (Unit, Boundary, Integration, Long-Horizon E2E emergence).

---

## Architecture

```text
agent_city/
├── server.py              # FastAPI REST endpoints & WebSocket streaming coordinator
├── config.py              # Simulation constants, zoning types, and Pydantic schemas
├── start_city.bat         # One-click Windows launcher (starts server + opens browser)
├── start_city.sh          # Unix/macOS quick-start launcher
├── engine/                # Core Simulation Engine
│   ├── grid.py            # 2D spatial grid, zoning, parcels, and weighted A* pathfinding
│   ├── economy.py         # Atomic resource ledgers, escrow vaults, and taxation
│   ├── message_bus.py     # Inter-agent pub/sub messaging, proposals, and consensus voting
│   └── simulation.py      # Deterministic 6-phase asynchronous tick loop coordinator
├── agents/                # Autonomous Agent Architecture
│   ├── base.py            # BaseAgent, 8-state FSM, 7-D traits, and episodic memory
│   ├── decision.py        # Goal hierarchy trees and dynamic utility scoring
│   ├── roles.py           # 6 Civic Roles (Mayor, Architect, Engineer, Merchant, etc.)
│   ├── subagents.py       # Hierarchical subagent spawning, contracts, and lifecycle
│   └── evolution.py       # Genetic crossover, mutation, and trait adaptation
├── static/                # Expressive Adaptive Frontend
│   ├── index.html         # Responsive layout with viewport, controls, and sidebar
│   ├── style.css          # Modern dark-mode styling with glassmorphism & zone themes
│   └── app.js             # SVG rendering, pan/zoom, WebSocket client, and inspector
└── tests/                 # 4-Tier Automated Test Suite (74 tests passing)
    ├── test_engine.py
    ├── test_agents.py
    ├── test_subagents.py
    ├── test_persistence.py
    ├── test_api_websocket.py
    └── test_e2e_city.py
```

---

## Quick Start

### 1. Launch the Server & Visualizer
Simply double-click `start_city.bat` or run:

```bash
# From within the agent_city directory:
python -m uvicorn agent_city.server:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

### 2. Controls & Interactivity
- **Play / Pause**: Toggle the live simulation loop.
- **Step**: Advance the simulation by exactly 1 tick.
- **Speed**: Adjust simulation rate from 1x (slow) to 20x (turbo).
- **Civic Events**: Inject municipal events like *Resource Windfall* or *Zoning Mandate*.
- **Pan & Zoom**: Click and drag on the SVG map or use the mouse scroll wheel.
- **Citizen Inspector**: Click any agent on the map or in the sidebar to inspect their neural traits, inventory, and active subordinate subagents.
- **Parcel Inspector**: Click any parcel on the map to see zoning type, building tier, and ownership.

---

## Automated Verification

Run the full pytest suite:

```bash
python -m pytest tests/
```

Expected result:
```text
============================= 74 passed in 5.83s ==============================
```
