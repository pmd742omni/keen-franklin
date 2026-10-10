# DISPATCH — Worker City Milestone 1: Simulation Engine & Core Models

**Assigned Agent**: worker_city_m1
**Archetype**: teamwork_preview_worker
**Parent**: orchestrator_2 (d8f49c97-82ba-4295-8de9-17407789baa2)
**Working Directory**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\worker_city_m1
**Project Target Directory**: c:\Users\ignaz\antigravity\keen-franklin\agent_city
**Original Request File**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\ORIGINAL_REQUEST.md (read entry timestamped 2026-09-30T16:39:54Z)
**Master Plan Reference**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\orchestrator_2\plan.md
**Explorer Survey 1 Reference**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\explorer_city_survey_1\survey_report.md
**Python Interpreter**: `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Milestone Scope & Deliverables
Implement the core simulation engine, spatial grid, zoning, pathfinding, economy, and message bus under `agent_city/`:
1. `agent_city/config.py`: Global constants, grid dimensions ($32 \times 32$), default tick duration ($0.2\text{s}$), zoning enums (`RESIDENTIAL`, `COMMERCIAL`, `INDUSTRIAL`, `CIVIC`, `PARK`, `ROAD`, `WILDERNESS`), economic parameters (tax rates, energy burn, starting budgets).
2. `agent_city/engine/grid.py`: 2D spatial grid representation, parcel metadata (zone, building_id, terrain_cost, coordinates), collision detection, weighted A* pathfinding (with 4-way movement and terrain weighting), and coordinate projection helpers (isometric and orthographic).
3. `agent_city/engine/economy.py`: Tri-resource balance (Funds, Energy, Materials), transaction tracking, public treasury account, sales tax computation, epoch property tax collection, and economic metrics aggregation.
4. `agent_city/engine/message_bus.py`: In-memory asynchronous message bus supporting 1:1 direct messages, broadcast announcements, topic-based pub/sub channels (`#governance`, `#trade`, `#construction`, `#general`), message filtering, civic proposals, and democratic consensus voting with quorum checking (>50%) and execution callbacks.
5. `agent_city/engine/simulation.py`: `SimulationCoordinator` managing the deterministic 6-phase async tick lifecycle:
   - Phase 1: Inbound external command ingestion
   - Phase 2: Agent perception & deliberation
   - Phase 3: Spatial movement & collision resolution
   - Phase 4: Environmental & economic updates
   - Phase 5: State delta aggregation & broadcast hooks
   - Phase 6: Drift compensation & timing control
   Includes pause, resume, speed multiplier setting, agent registration/unregistration, and tick delta generation.
6. `agent_city/requirements.txt`: Pydantic, FastAPI, Uvicorn, WebSockets, Pytest, Pytest-Asyncio, HTTPX.

## Verification
You MUST execute the test suite using:
`C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest tests/test_engine.py -v` (or run a verification script) and verify that all engine components work genuinely without errors.

## Handoff Requirements
Write a fully populated `handoff.md` and `progress.md` in your working directory.
Report completion to orchestrator_2 via send_message.
