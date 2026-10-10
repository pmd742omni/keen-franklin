# DISPATCH — E2E Test Writer (City Simulation)

**Assigned Agent**: test_writer_city_e2e
**Archetype**: teamwork_preview_test_writer
**Parent**: orchestrator_2 (d8f49c97-82ba-4295-8de9-17407789baa2)
**Working Directory**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\test_writer_city_e2e
**Project Target Directory**: c:\Users\ignaz\antigravity\keen-franklin\agent_city
**Original Request File**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\ORIGINAL_REQUEST.md (read entry timestamped 2026-09-30T16:39:54Z)
**Master Plan Reference**: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\orchestrator_2\plan.md
**Python Interpreter**: `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe`

## Mission
Design and implement the complete, opaque-box E2E test suite for the Evolving Virtual City Multi-Agent Simulation according to the 4-tier methodology:
- **Tier 1 (Feature Coverage, >=5 tests per feature area)**: Isolated tests verifying spatial grid, zoning, A* pathfinding, message bus, consensus voting, base agent FSM, 6 civic roles, subagent spawning/retirement, resource escrow, REST endpoints, WebSocket streaming, SQLite WAL persistence, JSON snapshots.
- **Tier 2 (Boundary & Corner Cases, >=5 tests per feature area)**: Zero/negative budgets, grid boundary collisions, pathfinding with no viable path, consensus voting with deadlocks/ties, max subagent recursion ceiling, concurrent WebSocket client disconnects, corrupt snapshot recovery.
- **Tier 3 (Cross-Feature Combinations & Pairwise interactions)**: Architect spawns Surveyor -> Surveyor updates zoning -> Builder constructs building; Merchant trades with Engineer -> sales tax deposited into treasury; Mayor passes tax hike proposal -> citizens adapt budgets.
- **Tier 4 (Real-World Application Scenarios)**: Full 100-tick continuous simulation with >= 8 distinct agents collaborating, generating emergent city expansion, subagent lifecycles, and stable economy without crashes or deadlocks.

## File Ownership
You exclusively own:
- `agent_city/tests/conftest.py`
- `agent_city/tests/test_engine.py`
- `agent_city/tests/test_agents.py`
- `agent_city/tests/test_subagents.py`
- `agent_city/tests/test_api_websocket.py`
- `agent_city/tests/test_persistence.py`
- `agent_city/tests/test_e2e_city.py`
- `agent_city/TEST_INFRA.md`
- `agent_city/TEST_READY.md`

## Output Requirements
1. Implement the test suite under `agent_city/tests/`.
2. Author `agent_city/TEST_INFRA.md` and `agent_city/TEST_READY.md`.
3. Provide `progress.md` and `handoff.md` in your working directory.
4. Report completion to orchestrator_2 via send_message.

## 2026-09-30T16:56:14Z
You are test_writer_city_e2e, a dedicated test authoring subagent (teamwork_preview_test_writer).
Your parent is orchestrator_2 (ID: d8f49c97-82ba-4295-8de9-17407789baa2).
Your Working Directory: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\test_writer_city_e2e
Project Target Directory: c:\Users\ignaz\antigravity\keen-franklin\agent_city
Original Request File: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\ORIGINAL_REQUEST.md (read entry 2026-09-30T16:39:54Z)
Master Plan: c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\orchestrator_2\plan.md
Python Interpreter: C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe

Instructions:
1. Read ORIGINAL_REQUEST.md and plan.md.
2. Read your DISPATCH.md in your working directory.
3. Design and implement the full opaque-box E2E test suite under `agent_city/tests/`:
   - `conftest.py`: Test fixtures, mock event loops, test configurations.
   - `test_engine.py`: Spatial grid, zoning, A* pathfinding, message bus, consensus voting, 6-phase simulation loop, economy ledger.
   - `test_agents.py`: BaseAgent 8-state FSM, 4-tier goal hierarchy, utility evaluation, 6 civic roles, trait evolution.
   - `test_subagents.py`: Hierarchical spawning, parent-child tracking, resource escrow & refunds, concurrency limits, retirement lifecycle.
   - `test_api_websocket.py`: REST endpoints (/api/city/status, /api/agents, /api/buildings, /api/events, /api/controls) and /ws stream protocol.
   - `test_persistence.py`: SQLite WAL schema integrity, JSON snapshot export/import, pause/resume, headless execution.
   - `test_e2e_city.py`: Multi-agent 100-tick continuous simulation, verifying >= 8 distinct agents, subagent spawning, stability, and zero crashes.
4. Author `agent_city/TEST_INFRA.md` and `agent_city/TEST_READY.md`.
5. Maintain progress.md in your working directory and write a self-contained handoff.md.
6. Report completion to orchestrator_2 (d8f49c97-82ba-4295-8de9-17407789baa2) via send_message.

