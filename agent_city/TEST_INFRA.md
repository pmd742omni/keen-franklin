# Testing Infrastructure & Methodology Specification (`TEST_INFRA.md`)
**Project**: Evolving Virtual City Multi-Agent Simulation (`agent_city`)  
**Author**: `test_writer_city_e2e` (teamwork_preview_test_writer)  
**Date**: 2026-09-30  
**Target Directory**: `c:\Users\ignaz\antigravity\keen-franklin\agent_city`  

---

## 1. Executive Summary & Test Suite Overview

The `agent_city` test suite provides comprehensive, opaque-box, contract-driven verification across all core simulation subsystems, agent life-cycles, subagent hierarchies, REST/WebSocket APIs, persistence engines, and long-horizon multi-agent emergence.

### 1.1 Test Suite Structure
```
agent_city/tests/
├── __init__.py                  # Package marker
├── conftest.py                  # Pytest fixtures, mock event loops, contract mock agents, configurations
├── test_engine.py               # Tier 1-3: Grid, Zoning, A* Pathfinding, Message Bus, Consensus, Economy, SimulationCoordinator
├── test_agents.py               # Tier 1-3: BaseAgent, 8-state FSM, 4-tier goal hierarchy, utility math, 6 civic roles, trait evolution
├── test_subagents.py            # Tier 1-3: Hierarchical spawning, delegation contracts, resource escrow, recursion guard, retirement
├── test_api_websocket.py        # Tier 1-3: REST endpoints, WebSocket differential streaming (< 1.5 KB/tick), client heartbeats
├── test_persistence.py          # Tier 1-3: SQLite WAL schema integrity, JSON snapshots, state continuity, headless runner
└── test_e2e_city.py             # Tier 4: Multi-agent 100-tick continuous simulation, stability, emergence, zero crashes
```

---

## 2. 4-Tier Test Methodology

The test suite implements the strict 4-Tier testing hierarchy:

| Tier | Category | Minimum Target | Scope & Purpose |
| :--- | :--- | :--- | :--- |
| **Tier 1** | **Feature Coverage** | $\ge 5$ per area | Isolated unit tests validating core module logic, default parameters, state transitions, mathematical calculations, and serialization round-trips. |
| **Tier 2** | **Boundary & Corner Cases** | $\ge 5$ per area | Stress and adversarial tests: grid boundary collisions, walled-off pathfinding targets, zero/negative balances, tie/deadlock voting, max subagent recursion ceilings, and corrupt snapshots. |
| **Tier 3** | **Cross-Feature Integration** | $\ge 3$ per area | Pairwise and multi-system workflows: Architect rezoning $\rightarrow$ municipal permit fee paid $\rightarrow$ grid parcel updated; Commercial trade $\rightarrow$ sales tax collected into treasury; Consensus voting $\rightarrow$ physical city modification callback execution. |
| **Tier 4** | **Real-World Scenarios** | 1 comprehensive | 100-tick continuous simulation with $\ge 8$ distinct agents interacting, spawning subagents, adapting traits, maintaining economic solvency, and verifying zero crashes or deadlocks under strict runtime performance budgets (< 15 seconds). |

---

## 3. Progressive Testability & Decoupled Execution

In multi-agent simulation development, components evolve across distinct milestones:
- **Milestone 1**: Core Engine & Data Models (Grid, Economy, Message Bus, Simulation Loop)
- **Milestone 2**: Agent Lifecycle & Hierarchical Spawning (BaseAgent, 6 Roles, Subagents, Evolution)
- **Milestone 3**: Server, REST API & Streaming (FastAPI, WebSockets, SQLite WAL)
- **Milestone 4**: Programmatic SVG Visualizer (Frontend)
- **Milestone 5**: Launchers, Packaging, & End-to-End Verification

To strictly preserve **Progressive Testability**:
1. All engine, math, and coordination contracts are verified against implemented M1 components immediately.
2. The suite provides a contract-compliant `MockAgent` fixture in `conftest.py`, allowing continuous testing of multi-agent interactions, movement, deliberation, and voting without requiring unfinished agent modules.
3. Tests targeting concrete M2 (`agent_city.agents`) and M3 (`agent_city.server`, `agent_city.api`) classes use graceful conditional imports (`pytest.mark.skipif`). When worker agents implement those modules, the corresponding tests unskip automatically without test harness code modifications.

---

## 4. Subsystem Test Specifications

### 4.1 `test_engine.py` (Engine Subsystems)
- **Spatial Grid**: Coordinate validation $[0, W-1] \times [0, H-1]$, default wilderness zoning, parcel retrieval.
- **Zoning & Costs**: Setting zones (Road, Park, Industrial, Civic, Commercial), automatic terrain cost assignment (Road=1.0, Park=1.5, Wilderness=2.0).
- **Buildings**: Single-tile placement and removal; multi-tile footprints (e.g. 2x2 City Hall) with passable entrance offsets and collision validation.
- **Collisions & Occupancy**: Single-occupancy constraints, atomic occupant handoffs, spatial index updates, teleportation, and clean occupant removal.
- **Weighted A\* Pathfinding**: Optimal shortest path, terrain cost preference (roads preferred over wilderness), dynamic obstacle avoidance, same-coordinate identity, and detection of sealed/unreachable targets.
- **Coordinate Projections**: 2.5D Isometric transformations (`to_isometric`, `from_isometric`), 2D CAD Orthographic transformations (`to_orthographic`, `from_orthographic`), lossless round-trip precision, and depth-key sorting (`x + y`).
- **Inter-Agent Message Bus**: 1:1 direct message delivery, public broadcast announcements, topic-based pub/sub channels (`#governance`, `#trade`, `#construction`), mailbox draining, and rolling dialogue feed history.
- **Democratic Consensus**: Civic proposal submission, voting tallies (AYE/NAY/ABSTAIN), quorum ratio verification (>50%), execution callback triggering (REZONE, ADJUST_TAX, DISBURSE_GRANT), tie handling, and expiration.
- **Tri-Resource Economy**: `ResourceLedger` atomic withdrawals and deposits; commercial transfers with 5% sales tax deduction into treasury; civic grant disbursements; property tax epoch sweeps; infrastructure maintenance deductions.
- **Simulation Coordinator**: 6-phase async execution loop; inbound command processing (PAUSE, RESUME, SET_SPEED, TRIGGER_EVENT); agent perception/deliberation dispatch; atomic action resolution (MOVE, BUILD, REZONE, TRADE, REST, SPEAK, PROPOSE, VOTE); compact state delta compilation (< 1.5 KB); dynamic tick rate regulation.
- **Serialization**: Complete dictionary export and byte-for-byte state reconstruction for `CityGrid`, `EconomySystem`, `MessageBus`, and `SimulationCoordinator`.

### 4.2 `test_agents.py` (Autonomous Agents)
- **BaseAgent Model**: Pydantic schema validation, 7-D trait vectors, homeostatic vitals, and inventory.
- **8-State FSM**: Transition pathways `IDLE -> PERCEIVING -> DELIBERATING -> MOVING -> EXECUTING -> COMMUNICATING -> RESTING -> RETIRED`.
- **4-Tier Goal Hierarchy**: Tier 1 (Homeostasis: energy < 15 overrides all) > Tier 2 (Civic Mandate) > Tier 3 (Socio-Economic Exchange) > Tier 4 (Self-Actualization).
- **Multi-Criteria Utility Formulation**:
  $$U(a) = w_{\text{need}} \cdot \mathcal{N}(a) + w_{\text{role}} \cdot \mathcal{R}(a) + w_{\text{trait}} \cdot \mathcal{T}(a) + w_{\text{feas}} \cdot \mathcal{F}(a) - \mathcal{P}_{\text{risk}}(a)$$
- **6 Civic Roles**: Mayor, Architect, Engineer, Merchant, Scholar, Observer agendas and default traits.
- **Evolution**: 7-D trait genome vector cosine similarity, bounded mutation $[0.0, 1.0]$, and epoch fitness scoring.

### 4.3 `test_subagents.py` (Hierarchical Delegation & Escrow)
- **DelegationContract**: Status progression `PENDING -> ACTIVE -> COMPLETED / TIMED_OUT`.
- **Resource Escrow**: Upfront asset locking from parent ledger; automatic refund of unspent funds/materials upon child retirement.
- **Insolvency Guard**: Parents with insufficient assets cannot spawn subagents.
- **Parent Concurrency Caps**: Role-specific maximum concurrent subagents (Architect <= 2, Engineer <= 3, etc.).
- **Recursion Guard**: Strict enforcement of `max_depth = 1` preventing exponential population explosions.

### 4.4 `test_api_websocket.py` (REST API & WebSocket Protocol)
- **Initial State Contract**: Complete `INIT_STATE` frame validation.
- **Differential Streaming**: Compact `TICK_DELTA` broadcast (< 1.5 KB payload constraint on typical ticks).
- **REST Endpoints**: `/api/city/status`, `/api/agents`, `/api/agents/{id}`, `/api/buildings`, `/api/events`, `/api/controls`, `/api/snapshot/*`.
- **Controls & Heartbeats**: Interactive simulation state modification (pause, resume, set speed, trigger events).

### 4.5 `test_persistence.py` (SQLite WAL & Snapshots)
- **SQLite WAL Mode**: `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=NORMAL;`.
- **6 Relational Tables**: `simulation_meta`, `parcels`, `agents`, `economy_history`, `event_log`, `dialogue_messages`.
- **JSON Snapshotting**: Full simulation state export, disk storage, and new coordinator restoration.
- **State Continuity**: Running simulation -> pause -> snapshot save -> load into new engine -> resume seamlessly.
- **Headless Execution**: Fast CLI simulation runner testing.

### 4.6 `test_e2e_city.py` (Tier 4 Emergence Verification)
- **Continuous 100-Tick Run**: Full simulation loop across 5 epochs.
- **$\ge 8$ Distinct Civic Agents**: Mayor, Architect, Engineer, Merchant, Builder, Scholar, Observer, Citizen.
- **Subagent Lifecycles**: Spawning at tick 10, execution, and clean retirement at tick 25.
- **Emergent Urban Expansion**: Real physical structures built, zones reclassified, and economy remaining solvent.
- **Zero Exception Invariant**: Complete execution without crashes, deadlocks, or unhandled exceptions.

---

## 5. Verification Commands

Run the full automated test suite:
```powershell
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/ -v
```

Run individual test modules:
```powershell
# Engine subsystems (Grid, Economy, MessageBus, Coordinator)
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/test_engine.py -v

# Agent FSM, Goal hierarchy, and Civic roles
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/test_agents.py -v

# Subagent delegation, escrow, and recursion caps
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/test_subagents.py -v

# REST API and WebSocket streaming protocol
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/test_api_websocket.py -v

# SQLite WAL and JSON snapshot persistence
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/test_persistence.py -v

# Tier 4 100-tick continuous E2E city simulation
C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest agent_city/tests/test_e2e_city.py -v
```
