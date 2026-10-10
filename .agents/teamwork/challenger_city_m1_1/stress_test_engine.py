"""
Empirical Adversarial Stress Testing Harness for Agent City Milestone 1.
Authored by challenger_city_m1_1 (teamwork_preview_challenger).

Executes adversarial stress testing against:
1. Spatial Grid & Boundaries (out-of-bounds, multi-tile, ghost occupancy, teleportation)
2. Weighted A* Pathfinding (mazes, cycles, bottlenecks, cost optimality, cutoff limits)
3. Economic Ledger (precision drift, atomic rollback, race conditions, deficit bankruptcy)
4. Simulation Coordinator & Protocols (zero-energy actions, delta wire footprint, serialization roundtrip)
"""

from __future__ import annotations

import asyncio
import json
import math
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, r"c:\Users\ignaz\antigravity\keen-franklin")

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, SimulationState, VoteChoice, ZoneType
from agent_city.engine.economy import EconomySystem, ResourceLedger, Transaction
from agent_city.engine.grid import CityGrid, Parcel
from agent_city.engine.message_bus import AgentMessage, CivicProposal, MessageBus
from agent_city.engine.simulation import SimulationCoordinator


class TestResult:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.error: Optional[str] = None
        self.details: Dict[str, Any] = {}
        self.duration_ms: float = 0.0

    def record_pass(self, duration_ms: float, **details):
        self.passed = True
        self.duration_ms = duration_ms
        self.details = details

    def record_fail(self, error: str, duration_ms: float, **details):
        self.passed = False
        self.error = error
        self.duration_ms = duration_ms
        self.details = details


class AdversarialStressEngine:
    def __init__(self):
        self.results: List[TestResult] = []

    def _record(self, result: TestResult):
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] [{result.category}] {result.name} ({result.duration_ms:.2f}ms)")
        if not result.passed:
            print(f"       ERROR: {result.error}")
        if result.details:
            for k, v in result.details.items():
                print(f"       {k}: {v}")

    # =========================================================================
    # CATEGORY 1: Spatial Grid & Boundary Attacks
    # =========================================================================

    def test_out_of_bounds_inputs(self):
        res = TestResult("test_out_of_bounds_inputs", "SPATIAL_GRID")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=32, height=32)
            # Negative, beyond max, float, inf, nan
            invalid_coords = [
                (-1, 0), (0, -1), (-999, -999),
                (32, 0), (0, 32), (100, 100), (999999, 999999),
                (5.5, 5.5), (float("nan"), 0), (0, float("inf")),
            ]

            for x, y in invalid_coords:
                # get_parcel must either return None or safely handle without uncaught exception
                try:
                    p = grid.get_parcel(x, y)  # type: ignore
                    if p is not None:
                        raise AssertionError(f"Expected None for out-of-bounds ({x}, {y}), got {p}")
                except TypeError:
                    # Float/NaN coordinate TypeError in list index is a vulnerability
                    raise AssertionError(f"TypeError raised for non-integer coordinate ({x}, {y})")

                # can_move_to
                if grid.can_move_to(x, y):  # type: ignore
                    raise AssertionError(f"can_move_to returned True for out-of-bounds ({x}, {y})")

                # get_terrain_cost
                cost = grid.get_terrain_cost(x, y)  # type: ignore
                if cost != math.inf:
                    raise AssertionError(f"get_terrain_cost should be inf for out-of-bounds ({x}, {y}), got {cost}")

            res.record_pass((time.monotonic() - t0) * 1000, tested_coords=len(invalid_coords))
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_multi_tile_building_atomic_boundary_overflow(self):
        res = TestResult("test_multi_tile_building_atomic_boundary_overflow", "SPATIAL_GRID")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=10, height=10)
            # Try to place 3x3 building at (8, 8) - extends to (10, 10) which is out of bounds
            success = grid.place_multi_tile_building(
                building_id="b_overflow",
                building_type="COMMERCIAL",
                top_left_x=8,
                top_left_y=8,
                width=3,
                height=3,
            )
            if success:
                raise AssertionError("place_multi_tile_building succeeded across grid boundaries!")

            # Verify no partial placement occurred (atomicity)
            for y in range(8, 10):
                for x in range(8, 10):
                    p = grid.get_parcel(x, y)
                    if p and p.building_id == "b_overflow":
                        raise AssertionError(f"Parcel ({x}, {y}) was partially modified despite placement failure!")

            # Verify zero or negative size buildings are rejected
            zero_success = grid.place_multi_tile_building("b_zero", "COMMERCIAL", 2, 2, 0, 0)
            neg_success = grid.place_multi_tile_building("b_neg", "COMMERCIAL", 2, 2, -2, -2)
            if zero_success or neg_success:
                raise AssertionError(f"Zero/negative sized buildings accepted: zero={zero_success}, neg={neg_success}")

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_multi_tile_building_occupant_crush_and_cleanup(self):
        res = TestResult("test_multi_tile_building_occupant_crush_and_cleanup", "SPATIAL_GRID")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=10, height=10)
            # Place an occupant at (3, 3)
            grid.teleport_occupant(3, 3, "victim_agent")

            # Attempt to place a 3x3 building overlapping (3, 3)
            # A robust system must NOT place an impassable building on top of an occupant
            placed = grid.place_multi_tile_building(
                building_id="b_crush",
                building_type="INDUSTRIAL",
                top_left_x=2,
                top_left_y=2,
                width=3,
                height=3,
                entrance_offset=(0, 0),  # (2, 2) is entrance, (3, 3) is impassable!
            )

            p_victim = grid.get_parcel(3, 3)
            if placed and p_victim and not p_victim.passable:
                raise AssertionError(
                    "Building was placed directly on top of an active occupant, trapping them in an impassable parcel!"
                )

            # Test cleanup: If multi-tile building placed, removing one tile leaves orphan tiles
            grid2 = CityGrid(width=10, height=10)
            grid2.place_multi_tile_building("b_multi", "COMMERCIAL", 0, 0, 2, 2)
            grid2.remove_building(0, 0)
            # Check if (0, 1), (1, 0), (1, 1) still have b_multi
            orphans = []
            for pt in [(0, 1), (1, 0), (1, 1)]:
                p = grid2.get_parcel(pt[0], pt[1])
                if p and p.building_id == "b_multi":
                    orphans.append(pt)
            if orphans:
                raise AssertionError(f"remove_building left orphaned multi-tile building remnants at {orphans}")

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_ghost_occupancy_leak_on_set_occupant(self):
        res = TestResult("test_ghost_occupancy_leak_on_set_occupant", "SPATIAL_GRID")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=10, height=10)
            # Agent set at (1, 1)
            grid.set_occupant(1, 1, "agent_1")
            assert grid.get_occupant(1, 1) == "agent_1"

            # Set same agent at (2, 2) via set_occupant
            grid.set_occupant(2, 2, "agent_1")

            # Check if (1, 1) still has agent_1
            old_occupant = grid.get_occupant(1, 1)
            if old_occupant == "agent_1":
                raise AssertionError(
                    "Ghost occupancy leak! set_occupant(2, 2, 'agent_1') left 'agent_1' on (1, 1), duplicating agent!"
                )

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_unbounded_movement_teleportation(self):
        res = TestResult("test_unbounded_movement_teleportation", "SPATIAL_GRID")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=32, height=32)
            grid.teleport_occupant(0, 0, "speedy_agent")

            # In grid.move_occupant, does it restrict movement to adjacent tiles?
            # An agent moving from (0, 0) to (31, 31) in one step should be rejected
            moved = grid.move_occupant(0, 0, 31, 31, "speedy_agent")
            if moved:
                raise AssertionError(
                    "grid.move_occupant allowed teleportation from (0,0) to (31,31) across 44 tiles without adjacency check!"
                )

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    # =========================================================================
    # CATEGORY 2: Weighted A* Pathfinding Adversarial Stress
    # =========================================================================

    def test_astar_labyrinth_cyclic_maze(self):
        res = TestResult("test_astar_labyrinth_cyclic_maze", "PATHFINDING")
        t0 = time.monotonic()
        try:
            # Generate a 21x21 serpentine maze with cycles
            size = 21
            grid = CityGrid(width=size, height=size)

            # Build snake walls with alternate openings
            for y in range(1, size - 1, 2):
                for x in range(size):
                    grid.set_building(x, y, f"wall_{x}_{y}", passable=False)
                # Create openings
                if (y // 2) % 2 == 0:
                    grid.remove_building(size - 1, y)  # Right opening
                    grid.remove_building(size - 2, y)
                else:
                    grid.remove_building(0, y)         # Left opening
                    grid.remove_building(1, y)

            # Find path from (0, 0) to (size-1, size-1)
            t_path_0 = time.monotonic()
            path = grid.find_path((0, 0), (size - 1, size - 1))
            t_path_ms = (time.monotonic() - t_path_0) * 1000

            if path is None:
                raise AssertionError(f"A* failed to solve 21x21 serpentine maze in {t_path_ms:.2f}ms")

            # Verify path continuity
            for i in range(len(path) - 1):
                p1, p2 = path[i], path[i + 1]
                dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
                if dist != 1:
                    raise AssertionError(f"Path has non-cardinal step: {p1} -> {p2} (dist={dist})")
                parcel = grid.get_parcel(p2[0], p2[1])
                if parcel and not parcel.passable:
                    raise AssertionError(f"Path walked through impassable parcel {p2}")

            res.record_pass(
                (time.monotonic() - t0) * 1000,
                path_length=len(path),
                solve_time_ms=round(t_path_ms, 2),
            )
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_astar_bottleneck_and_unreachable_target(self):
        res = TestResult("test_astar_bottleneck_and_unreachable_target", "PATHFINDING")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=15, height=15)

            # Completely enclose (7, 7) with impassable walls
            grid.set_building(6, 7, "w1", passable=False)
            grid.set_building(8, 7, "w2", passable=False)
            grid.set_building(7, 6, "w3", passable=False)
            grid.set_building(7, 8, "w4", passable=False)

            t_unreach_0 = time.monotonic()
            path = grid.find_path((0, 0), (7, 7))
            t_unreach_ms = (time.monotonic() - t_unreach_0) * 1000

            if path is not None:
                raise AssertionError("find_path found a path into a sealed 4-wall chamber!")

            # Execution time must be fast (bounded by max_nodes exploration)
            if t_unreach_ms > 200.0:
                raise AssertionError(f"Unreachable search took too long ({t_unreach_ms:.2f}ms)")

            # Test target parcel impassable
            grid.set_building(10, 10, "impassable_target", passable=False)
            p_impass = grid.find_path((0, 0), (10, 10))
            if p_impass is not None:
                raise AssertionError("find_path found a path to an impassable target!")

            res.record_pass((time.monotonic() - t0) * 1000, unreach_search_ms=round(t_unreach_ms, 2))
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_astar_weighted_cost_optimality(self):
        res = TestResult("test_astar_weighted_cost_optimality", "PATHFINDING")
        t0 = time.monotonic()
        try:
            # Build a scenario where:
            # Direct path: 5 steps of HIGH cost terrain (INDUSTRIAL: 2.5 per step = 12.5)
            # Detour path: 7 steps of ROAD terrain (ROAD: 1.0 per step = 7.0)
            # A true weighted A* MUST pick the detour path with lower total cost (7.0 < 12.5)
            grid = CityGrid(width=10, height=10)

            # Set direct corridor from (2, 2) to (6, 2) as INDUSTRIAL (cost 2.5)
            for x in range(2, 7):
                grid.set_zone(x, 2, ZoneType.INDUSTRIAL)

            # Set detour from (2, 2) -> (2, 4) -> (6, 4) -> (6, 2) as ROAD (cost 1.0)
            for y in range(2, 5):
                grid.set_zone(2, y, ZoneType.ROAD)
                grid.set_zone(6, y, ZoneType.ROAD)
            for x in range(2, 7):
                grid.set_zone(x, 4, ZoneType.ROAD)

            # Start at (2, 2), Target at (6, 2)
            path = grid.find_path((2, 2), (6, 2))
            if path is None:
                raise AssertionError("find_path returned None for weighted grid")

            # Calculate actual path cost
            total_cost = sum(grid.get_terrain_cost(pt[0], pt[1]) for pt in path[1:])
            direct_cost = 4 * 2.5  # 10.0
            detour_cost = 2 * 1.0 + 4 * 1.0 + 2 * 1.0  # 8.0

            # Detour via road has cost 8.0, direct industrial has cost 10.0
            # If A* ignored weights and used pure BFS/Manhattan distance, it would choose the direct path (length 5, cost 10.0)
            if total_cost > detour_cost + 1e-6:
                raise AssertionError(
                    f"A* failed to choose cheaper detour path! Total cost was {total_cost}, expected <= {detour_cost}"
                )

            res.record_pass((time.monotonic() - t0) * 1000, chosen_cost=total_cost, direct_cost=direct_cost)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_astar_diagonal_leak_and_cardinal_invariants(self):
        res = TestResult("test_astar_diagonal_leak_and_cardinal_invariants", "PATHFINDING")
        t0 = time.monotonic()
        try:
            grid = CityGrid(width=10, height=10)
            # Wall off cardinal neighbors of (5, 5): (4, 5), (6, 5), (5, 4), (5, 6)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                grid.set_building(5 + dx, 5 + dy, f"w_{dx}_{dy}", passable=False)

            # Diagonal neighbors are open (4, 4), (6, 6), etc.
            # find_path MUST NOT leak diagonally through the corners!
            path = grid.find_path((5, 5), (0, 0))
            if path is not None:
                raise AssertionError("find_path leaked diagonally through cardinally walled corner obstacles!")

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    # =========================================================================
    # CATEGORY 3: Economic Ledger Precision, Concurrency, and Deficits
    # =========================================================================

    def test_float_precision_drift_and_serialization(self):
        res = TestResult("test_float_precision_drift_and_serialization", "ECONOMY")
        t0 = time.monotonic()
        try:
            eco = EconomySystem()
            acc = eco.register_account("test_prec", funds=100.0, energy=100.0, materials=100.0)

            # Perform 100 commercial transfers of $0.1
            # In standard IEEE-754: 0.1 * 100 != 10.0 due to binary float representation
            for i in range(100):
                eco.transfer("test_prec", "treasury", 0.1, resource="funds", category="COMMERCIAL_TRADE", tick=i)

            # Check precision consistency between in-memory ledger and serialized dictionary
            in_mem_funds = acc.funds
            serialized_funds = acc.to_dict()["funds"]

            # Divergence between serialized dictionary and in-memory accumulator causes snapshot restore assertion failures!
            if abs(in_mem_funds - serialized_funds) > 1e-12:
                raise AssertionError(
                    f"Floating point precision divergence detected! in_mem={in_mem_funds} != serialized={serialized_funds}"
                )

            res.record_pass((time.monotonic() - t0) * 1000, in_mem=in_mem_funds, serialized=serialized_funds)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_atomic_multi_resource_withdrawal_rollback(self):
        res = TestResult("test_atomic_multi_resource_withdrawal_rollback", "ECONOMY")
        t0 = time.monotonic()
        try:
            ledger = ResourceLedger(funds=1000.0, energy=0.0, materials=500.0)

            # Withdraw: funds=100 (sufficient), energy=10 (INSUFFICIENT), materials=50 (sufficient)
            success = ledger.withdraw(funds=100.0, energy=10.0, materials=50.0)

            if success:
                raise AssertionError("Withdrawal succeeded despite energy being completely insufficient!")

            # Invariant check: Funds and materials must remain completely untouched (zero mutation)
            if ledger.funds != 1000.0 or ledger.materials != 500.0 or ledger.energy != 0.0:
                raise AssertionError(
                    f"Atomic rollback failed! Balances mutated after failed withdrawal: funds={ledger.funds}, materials={ledger.materials}"
                )

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_negative_balance_and_deposit_withdrawal_subversion(self):
        res = TestResult("test_negative_balance_and_deposit_withdrawal_subversion", "ECONOMY")
        t0 = time.monotonic()
        try:
            ledger = ResourceLedger(funds=50.0, energy=50.0, materials=50.0)

            # 1. Attempt negative withdrawal: withdraw(funds=-100)
            # In flawed logic: funds - (-100) = +100!
            w_neg = ledger.withdraw(funds=-100.0)
            if w_neg and ledger.funds > 50.0:
                raise AssertionError(
                    f"Negative withdrawal exploit! withdraw(funds=-100) increased funds to {ledger.funds}!"
                )

            # 2. Attempt negative deposit: deposit(funds=-100)
            # deposit should not allow draining funds without going through withdraw/sufficiency check
            d_init = ledger.funds
            ledger.deposit(funds=-100.0)
            if ledger.funds < d_init:
                raise AssertionError(
                    f"Negative deposit exploit! deposit(funds=-100) drained funds from {d_init} to {ledger.funds} bypassing withdraw()!"
                )

            # 3. Excessive withdrawal must not result in negative balance
            ledger.withdraw(funds=1000.0)
            if ledger.funds < 0.0:
                raise AssertionError(f"Ledger funds went negative: {ledger.funds}")

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    def test_treasury_deficit_and_bankruptcy(self):
        res = TestResult("test_treasury_deficit_and_bankruptcy", "ECONOMY")
        t0 = time.monotonic()
        try:
            eco = EconomySystem()
            eco.treasury.funds = 10.0

            # Charge $100 maintenance (exceeds $10 treasury)
            success = eco.charge_maintenance(cost=100.0, tick=1, description="Major Infrastructure Repair")

            if success:
                raise AssertionError("charge_maintenance returned True despite treasury being in deficit!")

            if eco.treasury.funds < 0.0:
                raise AssertionError(f"Treasury funds dropped below 0 into negative: {eco.treasury.funds}")

            if eco.treasury.funds != 0.0:
                raise AssertionError(f"Treasury should have been drained to 0.0, got {eco.treasury.funds}")

            # Check that transaction record has recorded deficit
            last_tx = eco.transaction_history[-1]
            if "Deficit" not in last_tx.description:
                raise AssertionError(f"Transaction description missing deficit notice: {last_tx.description}")

            res.record_pass((time.monotonic() - t0) * 1000, last_tx=last_tx.description)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    async def test_concurrent_transfer_race_conditions(self):
        res = TestResult("test_concurrent_transfer_race_conditions", "ECONOMY")
        t0 = time.monotonic()
        try:
            eco = EconomySystem()
            # Register a victim account with exactly $100
            eco.register_account("victim", funds=100.0)
            eco.register_account("receiver_1", funds=0.0)
            eco.register_account("receiver_2", funds=0.0)

            # Concurrently launch 10 tasks trying to transfer $20 each (total $200 requested, only $100 available)
            async def do_transfer(r_id: str, amount: float):
                return eco.transfer("victim", r_id, amount, category="DIRECT")

            tasks = []
            for i in range(10):
                target = "receiver_1" if i % 2 == 0 else "receiver_2"
                tasks.append(do_transfer(target, 20.0))

            results = await asyncio.gather(*tasks)
            successful_txs = [r for r in results if r is not None]

            # Invariant: Total withdrawn cannot exceed $100
            victim_funds = eco.get_ledger("victim").funds
            r1_funds = eco.get_ledger("receiver_1").funds
            r2_funds = eco.get_ledger("receiver_2").funds

            total_received = r1_funds + r2_funds
            if victim_funds < -1e-6:
                raise AssertionError(f"Double-spending race condition! Victim funds negative: {victim_funds}")

            if total_received > 100.0 + 1e-6:
                raise AssertionError(
                    f"Double-spending race condition! Total received ({total_received}) exceeded initial funds ($100.0)!"
                )

            res.record_pass(
                (time.monotonic() - t0) * 1000,
                successful_txs=len(successful_txs),
                victim_remaining=victim_funds,
                total_received=total_received,
            )
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    # =========================================================================
    # CATEGORY 4: Simulation Coordinator & Protocols
    # =========================================================================

    async def test_exhausted_zero_energy_agent_actions(self):
        res = TestResult("test_exhausted_zero_energy_agent_actions", "COORDINATOR")
        t0 = time.monotonic()
        try:
            coordinator = SimulationCoordinator()

            class ZombieAgent:
                def __init__(self):
                    self.id = "zombie_1"
                    self.role = "BUILDER"
                    self.x = 2
                    self.y = 2
                    self.current_action = None

                def perceive(self, ctx): pass
                def deliberate(self):
                    return {"type": "MOVE", "target": (self.x + 1, self.y)}

            zombie = ZombieAgent()
            coordinator.register_agent(zombie, initial_x=2, initial_y=2, initial_energy=0.0)

            # Agent has 0.0 energy!
            ledger = coordinator.economy.get_ledger("zombie_1")
            assert ledger.energy == 0.0

            # Step simulation tick
            delta = await coordinator.step()

            # Check if zombie moved!
            new_pos = coordinator.grid.find_agent_pos("zombie_1")
            if new_pos == (3, 2):
                raise AssertionError(
                    "Exhausted agent vulnerability! Agent with energy=0.0 was permitted to execute MOVE action!"
                )

            res.record_pass((time.monotonic() - t0) * 1000)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    async def test_tick_delta_payload_wire_footprint(self):
        res = TestResult("test_tick_delta_payload_wire_footprint", "COORDINATOR")
        t0 = time.monotonic()
        try:
            coordinator = SimulationCoordinator()

            # Register 8 agents
            for i in range(8):
                class DummyAgent:
                    def __init__(self, idx):
                        self.id = f"agent_{idx}"
                        self.role = "CITIZEN"
                        self.x = idx * 2
                        self.y = idx * 2
                    def perceive(self, ctx): pass
                    def deliberate(self):
                        return {"type": "MOVE", "target": (self.x + 1, self.y)}

                a = DummyAgent(i)
                coordinator.register_agent(a, initial_x=a.x, initial_y=a.y)

            # Advance 1 tick
            delta = await coordinator.step()
            raw_json = json.dumps(delta)
            size_bytes = len(raw_json.encode("utf-8"))

            # Contract specification requires < 1.5 KB (1536 bytes)
            if size_bytes >= 1536:
                raise AssertionError(
                    f"TICK_DELTA footprint contract violated! Size: {size_bytes} bytes (Limit: 1536 bytes)"
                )

            res.record_pass((time.monotonic() - t0) * 1000, size_bytes=size_bytes)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    async def test_state_snapshot_roundtrip_precision(self):
        res = TestResult("test_state_snapshot_roundtrip_precision", "COORDINATOR")
        t0 = time.monotonic()
        try:
            coordinator = SimulationCoordinator()

            # Place commercial building to trigger fractional tax/yield increments
            coordinator.grid.set_building(5, 5, "comm_1", building_type="COMMERCIAL")
            coordinator.grid.set_zone(5, 5, ZoneType.COMMERCIAL)

            # Run 5 ticks
            for _ in range(5):
                await coordinator.step()

            orig_funds = coordinator.economy.treasury.funds

            # Snapshot roundtrip
            snap_dict = coordinator.to_dict()
            restored = SimulationCoordinator.from_dict(snap_dict, config=coordinator.config)

            restored_funds = restored.economy.treasury.funds
            if orig_funds != restored_funds:
                raise AssertionError(
                    f"Snapshot state precision discrepancy! Original treasury: {orig_funds}, Restored: {restored_funds} (Diff: {orig_funds - restored_funds})"
                )

            res.record_pass((time.monotonic() - t0) * 1000, orig_funds=orig_funds, restored_funds=restored_funds)
        except Exception as e:
            res.record_fail(str(e), (time.monotonic() - t0) * 1000)
        self._record(res)

    async def run_all(self):
        print("=" * 80)
        print("RUNNING ADVERSARIAL STRESS TEST ENGINE (Milestone 1)")
        print("=" * 80)

        # Category 1: Spatial Grid
        self.test_out_of_bounds_inputs()
        self.test_multi_tile_building_atomic_boundary_overflow()
        self.test_multi_tile_building_occupant_crush_and_cleanup()
        self.test_ghost_occupancy_leak_on_set_occupant()
        self.test_unbounded_movement_teleportation()

        # Category 2: Pathfinding
        self.test_astar_labyrinth_cyclic_maze()
        self.test_astar_bottleneck_and_unreachable_target()
        self.test_astar_weighted_cost_optimality()
        self.test_astar_diagonal_leak_and_cardinal_invariants()

        # Category 3: Economy
        self.test_float_precision_drift_and_serialization()
        self.test_atomic_multi_resource_withdrawal_rollback()
        self.test_negative_balance_and_deposit_withdrawal_subversion()
        self.test_treasury_deficit_and_bankruptcy()
        await self.test_concurrent_transfer_race_conditions()

        # Category 4: Coordinator & Protocols
        await self.test_exhausted_zero_energy_agent_actions()
        await self.test_tick_delta_payload_wire_footprint()
        await self.test_state_snapshot_roundtrip_precision()

        print("=" * 80)
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        print(f"STRESS TEST SUMMARY: Total={total}, Passed={passed}, Failed={failed}")
        print("=" * 80)
        return passed, failed


if __name__ == "__main__":
    runner = AdversarialStressEngine()
    passed, failed = asyncio.run(runner.run_all())
    sys.exit(0 if failed == 0 else 1)
