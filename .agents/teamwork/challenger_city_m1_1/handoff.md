# Milestone 1 Gate Verdict & Adversarial Stress Testing Report

**Agent**: `challenger_city_m1_1` (teamwork_preview_challenger)  
**Parent**: `orchestrator_2` (`d8f49c97-82ba-4295-8de9-17407789baa2`)  
**Working Directory**: `c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\challenger_city_m1_1`  
**Target Directory**: `c:\Users\ignaz\antigravity\keen-franklin\agent_city`  
**Date**: 2026-09-30  
**Gate Verdict**: **REJECT**  

---

## 1. Observation

### 1.1 Existing Test Suite Baseline Run
Executing `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest tests/ -v` produced **2 FAILURES**:

1. `tests/test_api_websocket.py:91`:
```
FAILED tests/test_api_websocket.py::TestWebSocketStreamingProtocolContract::test_tick_delta_differential_footprint_constraint
AssertionError: Tick delta payload (2931 bytes) exceeded 1.5 KB limit!
assert 2931 < 1536
```
2. `tests/test_persistence.py:236`:
```
FAILED tests/test_persistence.py::TestJSONSnapshotAndStateContinuity::test_json_snapshot_save_and_restore
AssertionError: assert 5051.5 == 5051.500000000002
 + where 5051.5 = ResourceLedger(funds=5051.5, energy=1000.0, materials=500.0).funds
 + where ResourceLedger(...) = <EconomySystem>.treasury
```

### 1.2 Adversarial Stress Engine Execution
Executing `C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -u c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\challenger_city_m1_1\stress_test_engine.py` yielded **8 PASSED, 9 FAILED**:

```
================================================================================
RUNNING ADVERSARIAL STRESS TEST ENGINE (Milestone 1)
================================================================================
[FAIL] [SPATIAL_GRID] test_out_of_bounds_inputs (12.25ms)
       ERROR: TypeError raised for non-integer coordinate (5.5, 5.5)
[FAIL] [SPATIAL_GRID] test_multi_tile_building_atomic_boundary_overflow (1.76ms)
       ERROR: Zero/negative sized buildings accepted: zero=True, neg=True
[FAIL] [SPATIAL_GRID] test_multi_tile_building_occupant_crush_and_cleanup (6.12ms)
       ERROR: Building was placed directly on top of an active occupant, trapping them in an impassable parcel!
[FAIL] [SPATIAL_GRID] test_ghost_occupancy_leak_on_set_occupant (0.97ms)
       ERROR: Ghost occupancy leak! set_occupant(2, 2, 'agent_1') left 'agent_1' on (1, 1), duplicating agent!
[FAIL] [SPATIAL_GRID] test_unbounded_movement_teleportation (9.86ms)
       ERROR: grid.move_occupant allowed teleportation from (0,0) to (31,31) across 44 tiles without adjacency check!
[PASS] [PATHFINDING] test_astar_labyrinth_cyclic_maze (10.22ms)
       path_length: 221
       solve_time_ms: 2.8
[PASS] [PATHFINDING] test_astar_bottleneck_and_unreachable_target (5.05ms)
       unreach_search_ms: 3.04
[PASS] [PATHFINDING] test_astar_weighted_cost_optimality (1.71ms)
       chosen_cost: 8.0
       direct_cost: 10.0
[PASS] [PATHFINDING] test_astar_diagonal_leak_and_cardinal_invariants (0.92ms)
[PASS] [ECONOMY] test_float_precision_drift_and_serialization (14.89ms)
       in_mem: 90.00000000000057
       serialized: 90.0
[PASS] [ECONOMY] test_atomic_multi_resource_withdrawal_rollback (0.03ms)
[FAIL] [ECONOMY] test_negative_balance_and_deposit_withdrawal_subversion (0.04ms)
       ERROR: Negative withdrawal exploit! withdraw(funds=-100) increased funds to 150.0!
[PASS] [ECONOMY] test_treasury_deficit_and_bankruptcy (0.13ms)
       last_tx: Major Infrastructure Repair (Deficit: 90.0)
[PASS] [ECONOMY] test_concurrent_transfer_race_conditions (1.09ms)
       successful_txs: 5
       victim_remaining: 0.0
       total_received: 100.0
[FAIL] [COORDINATOR] test_exhausted_zero_energy_agent_actions (10.26ms)
       ERROR: Exhausted agent vulnerability! Agent with energy=0.0 was permitted to execute MOVE action!
[FAIL] [COORDINATOR] test_tick_delta_payload_wire_footprint (15.48ms)
       ERROR: TICK_DELTA footprint contract violated! Size: 2103 bytes (Limit: 1536 bytes)
[FAIL] [COORDINATOR] test_state_snapshot_roundtrip_precision (92.70ms)
       ERROR: Snapshot state precision discrepancy! Original treasury: 5000.500000000002, Restored: 5000.5 (Diff: 1.8189894035458565e-12)
================================================================================
STRESS TEST SUMMARY: Total=17, Passed=8, Failed=9
================================================================================
```

### 1.3 Code Inspection & Vulnerability Locations
1. **`agent_city/engine/grid.py:70-78`**:
   ```python
   def is_valid_coord(self, x: int, y: int) -> bool:
       return 0 <= x < self.width and 0 <= y < self.height
   ```
   No integer type checking. When float coordinates e.g. `(5.5, 5.5)` are passed, `0 <= 5.5 < 32` is `True`, causing `self._grid[5.5][5.5]` to raise unhandled `TypeError: list indices must be integers or slices, not float`.
2. **`agent_city/engine/grid.py:140-164`**:
   `place_multi_tile_building` does not validate `width > 0 and height > 0`. If `width <= 0`, `range(0)` completes immediately and returns `True`. Furthermore, it only checks `parcel.building_id is not None`, but fails to check `parcel.occupant_id is not None`, placing impassable structures on top of live agents.
3. **`agent_city/engine/grid.py:196-212`**:
   `set_occupant(x, y, occupant_id)` updates `parcel.occupant_id = occupant_id` and `self._agent_positions[occupant_id] = (x, y)`, but fails to clear `occupant_id` from the previous parcel where the agent was located, causing permanent ghost occupancy leaks.
4. **`agent_city/engine/grid.py:214-241` & `agent_city/engine/simulation.py:497-526`**:
   `move_occupant` and `_phase_3_resolve_actions` do not verify whether `(to_x, to_y)` is an adjacent neighbor (`abs(to_x - from_x) + abs(to_y - from_y) == 1`). Agents can pass `{"type": "MOVE", "target": (31, 31)}` and instantaneously teleport 44 tiles in a single tick without pathfinding or obstacle checks.
5. **`agent_city/engine/economy.py:44-59`**:
   `withdraw()` does not reject negative numbers (`funds < 0`). Calling `withdraw(funds=-100)` evaluates `has_sufficient` to `True` and executes `self.funds = max(0.0, funds - (-100))` which deposits $100. Conversely, `deposit(funds=-100)` executes `self.funds = max(0.0, self.funds - 100)` which drains funds bypassing `withdraw()`.
6. **`agent_city/engine/simulation.py:497-526, 528-563`**:
   `_phase_3_resolve_actions` does NOT check whether an agent has sufficient energy before executing actions. Agents with `energy = 0.0` can move and build indefinitely, violating the contract in `plan.md` Section 3.1.
7. **`agent_city/engine/simulation.py:773-836`**:
   `_phase_5_compile_delta` generates a dictionary with full parcel dicts, full action dictionaries, and unpruned metadata, resulting in wire sizes of 2103 to 2931 bytes (exceeding the strict 1536 byte / 1.5 KB requirement).
8. **`agent_city/engine/economy.py:61-68` & `agent_city/engine/simulation.py:718-722`**:
   `ResourceLedger.to_dict()` rounds funds to 2 decimal places (`round(self.funds, 2)`), but in-memory deposits (e.g. `materials=0.2, energy=0.1`) accumulate binary floating-point inaccuracy (`5051.500000000002`). This divergence breaks JSON snapshot roundtripping.

---

## 2. Logic Chain

1. **Contract Invalidation**:
   - The project architecture specification (`plan.md` line 73) and E2E test suite (`test_api_websocket.py:91`) explicitly mandate that the differential state broadcast `TICK_DELTA` must remain `< 1.5 KB` (`1536` bytes).
   - Direct empirical measurement proves the current payload with 8 agents is 2103–2931 bytes (Observation 1.1, 1.2), causing test failure.
2. **Persistence State Invariant Violation**:
   - In-memory floating-point accrual produces imprecise accumulators (`5051.500000000002`) while serialization rounds to 2 decimals (`5051.5`).
   - Snapshot deserialization into a fresh coordinator restores `5051.5`, which fails equality against the in-memory tick state (Observation 1.1, 1.2).
3. **Exploitable Economic Subversion**:
   - `ResourceLedger.withdraw(funds=-100)` prints $100 out of thin air, and `deposit(funds=-100)` acts as an unauthorized siphon (Observation 1.2, 1.3). Financial invariants cannot be guaranteed.
4. **Spatial Grid Corruption & Teleportation**:
   - `move_occupant` and `SimulationCoordinator` lack topological adjacency checks, enabling any agent to bypass walls and teleport across the map (Observation 1.2, 1.3).
   - `set_occupant` leaks ghost occupancies, permanently bricking grid parcels from being entered by other agents.
   - Non-integer coordinate inputs cause crash-level unhandled `TypeError` exceptions instead of returning `None`.
5. **Agent Metabolism Invalidation**:
   - `plan.md` Section 3.1 contract states that action resolution verifies energy feasibility.
   - The coordinator allows agents with 0.0 energy to move and build without penalty (Observation 1.2, 1.3).

---

## 3. Caveats

- **Robust Weighted A* Core**:
  - The core pathfinding implementation in `find_path()` is genuinely optimal and performant. In our 21x21 cyclic labyrinth test, it discovered a 221-step path in only 2.8ms, respected terrain cost weighting (choosing an 8.0 road detour over a 10.0 direct industrial path), prevented diagonal wall leakage, and handled unreachable walled targets in 3.04ms.
- **Atomic Multi-Resource Rollback**:
  - `ResourceLedger.withdraw()` correctly implements atomic all-or-nothing rollback when multiple resources are requested simultaneously (if funds and materials are sufficient but energy is 0, none are deducted).
- **Concurrency & Treasury Deficits**:
  - `EconomySystem` cleanly handled concurrent asynchronous transactions without double-spending and tracked treasury bankruptcy deficits gracefully.

---

## 4. Conclusion

**Gate Verdict: REJECT.**

Milestone 1 cannot be approved in its current state. Downstream milestones (Milestone 2 Agent Lifecycle, Milestone 3 Server Streaming) cannot build safely on top of these vulnerabilities.

### Required Concrete Remediations for Worker:
1. **Input Validation in `CityGrid`**:
   - In `is_valid_coord(x, y)`: Ensure `isinstance(x, int) and isinstance(y, int) and not isinstance(x, bool)`.
   - In `place_multi_tile_building`: Reject `width <= 0 or height <= 0`; verify `parcel.occupant_id is None` for all tiles before placement.
   - In `set_occupant(x, y, occupant_id)`: If `occupant_id` was already in `_agent_positions`, clear `old_parcel.occupant_id = None`.
2. **Movement Adjacency Enforcement**:
   - In `move_occupant` and `SimulationCoordinator._phase_3_resolve_actions`: Require `abs(to_x - from_x) + abs(to_y - from_y) == 1`. Reject non-adjacent jumps.
3. **Economic Ledger Sanitization**:
   - In `ResourceLedger.withdraw` and `deposit`: Ensure all parameters are strictly non-negative (`funds < 0 or energy < 0 or materials < 0: return False`).
   - Quantize float balances consistently (e.g. `round(..., 4)` during `deposit` and `withdraw`, or use Decimal / float rounding in both memory and serialization) to eliminate snapshot restoration divergence (`5051.5` vs `5051.500000000002`).
4. **Energy Feasibility Checks**:
   - In `SimulationCoordinator._phase_3_resolve_actions`: Check that agent has sufficient energy (`ledger.energy >= energy_burn_move` for `MOVE`, and `>= energy_burn_work` for `BUILD`) before resolving the action.
5. **Differential Delta Wire Footprint Optimization**:
   - In `SimulationCoordinator._phase_5_compile_delta`: Prune unnecessary static fields from parcel deltas and resolved action dictionaries so that the JSON wire size stays well under 1536 bytes (1.5 KB limit).

---

## 5. Verification Method

To verify after worker implements remediations:
1. Run the existing project test suite:
   ```powershell
   C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest tests/ -v
   ```
   **Pass Condition**: 0 failures (specifically `test_tick_delta_differential_footprint_constraint` and `test_json_snapshot_save_and_restore` must pass).
2. Run the adversarial stress test suite:
   ```powershell
   C:\Users\ignaz\AppData\Local\Python\pythoncore-3.14-64\python.exe -u c:\Users\ignaz\antigravity\keen-franklin\.agents\teamwork\challenger_city_m1_1\stress_test_engine.py
   ```
   **Pass Condition**: All 17 stress tests pass with 0 failures (`STRESS TEST SUMMARY: Total=17, Passed=17, Failed=0`).
