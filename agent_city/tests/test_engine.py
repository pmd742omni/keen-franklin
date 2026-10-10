"""Tier 1-3 Comprehensive Tests for Engine Subsystems:
- Spatial Grid & Zoning
- Collision Detection & Occupancy
- Weighted A* Pathfinding & Coordinate Projections
- Inter-Agent Message Bus & Topic Pub/Sub
- Democratic Consensus Voting & Legislative Execution
- Tri-Resource Ledger, Municipal Treasury, & Taxation
- 6-Phase Asynchronous Simulation Coordinator Loop
- State Serialization & Snapshot Reconstruction
"""

from __future__ import annotations

import asyncio
import math
import pytest

from agent_city.config import (
    DEFAULT_CONFIG,
    MessageType,
    ProposalStatus,
    SimulationConfig,
    SimulationState,
    VoteChoice,
    ZoneType,
)
from agent_city.engine.economy import EconomySystem, ResourceLedger, Transaction
from agent_city.engine.grid import CityGrid, Parcel
from agent_city.engine.message_bus import AgentMessage, CivicProposal, MessageBus
from agent_city.engine.simulation import SimulationCoordinator


# =============================================================================
# 1. Spatial Grid, Zoning, & Collision Detection Tests
# =============================================================================

class TestSpatialGridAndZoning:
    """Tests for CityGrid dimensions, parcel zoning, and terrain movement costs."""

    def test_grid_initialization_defaults(self, grid: CityGrid):
        """Tier 1: Verify grid boundaries, tile matrix size, and default wilderness zones."""
        assert grid.width == 16
        assert grid.height == 16
        assert grid.is_valid_coord(0, 0) is True
        assert grid.is_valid_coord(15, 15) is True
        assert grid.is_valid_coord(16, 16) is False
        assert grid.is_valid_coord(-1, 0) is False

        p = grid.get_parcel(0, 0)
        assert p is not None
        assert p.zone == ZoneType.WILDERNESS
        assert p.passable is True
        assert p.terrain_cost == 2.0
        assert p.occupant_id is None

    def test_set_zone_and_terrain_costs(self, grid: CityGrid):
        """Tier 1: Verify zoning assignment updates default terrain costs."""
        p_road = grid.set_zone(2, 2, ZoneType.ROAD)
        assert p_road is not None
        assert p_road.zone == ZoneType.ROAD
        assert p_road.terrain_cost == 1.0  # Roads have lowest transit cost

        p_park = grid.set_zone(3, 3, ZoneType.PARK)
        assert p_park is not None
        assert p_park.zone == ZoneType.PARK
        assert p_park.terrain_cost == 1.5

        p_ind = grid.set_zone(4, 4, ZoneType.INDUSTRIAL)
        assert p_ind is not None
        assert p_ind.zone == ZoneType.INDUSTRIAL
        assert p_ind.terrain_cost == 2.5

        # Out-of-bounds zoning returns None
        assert grid.set_zone(99, 99, ZoneType.CIVIC) is None

    def test_single_and_multi_tile_buildings(self, grid: CityGrid):
        """Tier 1: Verify building placement, entrance passability, and removal."""
        # Single tile structure
        p = grid.set_building(5, 5, building_id="bldg_1", building_type="RESIDENTIAL", passable=False)
        assert p is not None
        assert p.building_id == "bldg_1"
        assert p.passable is False
        assert grid.get_terrain_cost(5, 5) == math.inf

        # Remove building
        p_cleared = grid.remove_building(5, 5)
        assert p_cleared is not None
        assert p_cleared.building_id is None
        assert p_cleared.passable is True
        assert p_cleared.terrain_cost == 2.0

        # Multi-tile structure (2x2 City Hall with entrance at (0, 0))
        success = grid.place_multi_tile_building(
            building_id="city_hall",
            building_type="CIVIC",
            top_left_x=8,
            top_left_y=8,
            width=2,
            height=2,
            entrance_offset=(0, 0),
            zone=ZoneType.CIVIC,
        )
        assert success is True

        # Entrance is passable
        entrance = grid.get_parcel(8, 8)
        assert entrance is not None
        assert entrance.building_id == "city_hall"
        assert entrance.passable is True

        # Other 3 tiles are impassable
        for x, y in [(9, 8), (8, 9), (9, 9)]:
            parcel = grid.get_parcel(x, y)
            assert parcel is not None
            assert parcel.building_id == "city_hall"
            assert parcel.passable is False

        # Attempting to place overlapping building fails cleanly
        overlap = grid.place_multi_tile_building(
            building_id="overlap_bldg",
            building_type="COMMERCIAL",
            top_left_x=9,
            top_left_y=9,
            width=2,
            height=2,
        )
        assert overlap is False

    def test_collision_detection_and_occupant_movement(self, grid: CityGrid):
        """Tier 1 & 2: Verify atomic occupant positioning, collisions, and handoffs."""
        assert grid.set_occupant(2, 3, "agent_alice") is True
        assert grid.get_occupant(2, 3) == "agent_alice"
        assert grid.find_agent_pos("agent_alice") == (2, 3)

        # Another agent cannot occupy the same parcel (Collision Detection)
        assert grid.can_move_to(2, 3, "agent_bob") is False
        assert grid.set_occupant(2, 3, "agent_bob") is False

        # Same agent moving to their own current position is valid
        assert grid.can_move_to(2, 3, "agent_alice") is True

        # Atomic move to an adjacent parcel
        assert grid.move_occupant(2, 3, 2, 4, "agent_alice") is True
        assert grid.get_occupant(2, 3) is None
        assert grid.get_occupant(2, 4) == "agent_alice"
        assert grid.find_agent_pos("agent_alice") == (2, 4)

        # Moving to impassable tile fails
        grid.set_building(2, 5, "wall_1", passable=False)
        assert grid.move_occupant(2, 4, 2, 5, "agent_alice") is False
        assert grid.get_occupant(2, 4) == "agent_alice"

        # Teleport and cleanup
        assert grid.teleport_occupant(7, 7, "agent_alice") is True
        assert grid.get_occupant(2, 4) is None
        assert grid.get_occupant(7, 7) == "agent_alice"

        assert grid.remove_occupant("agent_alice") is True
        assert grid.get_occupant(7, 7) is None
        assert grid.find_agent_pos("agent_alice") is None

    def test_grid_boundary_corner_cases(self, grid: CityGrid):
        """Tier 2: Boundary tests with negative coordinates and extreme values."""
        assert grid.get_parcel(-1, -1) is None
        assert grid.get_parcel(16, 0) is None
        assert grid.get_parcel(0, 16) is None
        assert grid.can_move_to(-5, 5, "agent_x") is False
        assert grid.can_move_to(20, 20, "agent_x") is False
        assert grid.set_occupant(99, 99, "agent_x") is False
        assert grid.move_occupant(0, 0, -1, 0, "agent_x") is False


# =============================================================================
# 2. Weighted A* Pathfinding & Projection Math Tests
# =============================================================================

class TestPathfindingAndProjections:
    """Tests for Weighted A* shortest path search and screen projection mathematics."""

    def test_astar_straight_line(self, grid: CityGrid):
        """Tier 1: Verify direct pathfinding between open coordinates."""
        path = grid.find_path((1, 1), (1, 4))
        assert path is not None
        assert path == [(1, 1), (1, 2), (1, 3), (1, 4)]
        assert len(path) == 4

    def test_astar_same_start_and_target(self, grid: CityGrid):
        """Tier 2: When start == target, returns [start]."""
        path = grid.find_path((3, 3), (3, 3))
        assert path == [(3, 3)]

    def test_astar_chooses_cheaper_road_over_wilderness(self, grid: CityGrid):
        """Tier 1: Weighted A* must prefer paved road path (cost=1.0) over wilderness (cost=2.0)."""
        # Set up a detour of roads vs direct rough terrain
        # Start at (1, 1), Target at (3, 1)
        # Direct: (1, 1) -> (2, 1) [cost=2.0] -> (3, 1) [cost=2.0] = total 4.0
        # Road loop: (1, 1) -> (1, 2)[1.0] -> (2, 2)[1.0] -> (3, 2)[1.0] -> (3, 1)[1.0] = total 4.0
        # If we make direct wilderness cost = 5.0, road loop is strictly cheaper:
        grid.get_parcel(2, 1).terrain_cost = 10.0  # Dense swamp / mountain

        for x in [1, 2, 3]:
            grid.set_zone(x, 2, ZoneType.ROAD)  # cost 1.0 each

        path = grid.find_path((1, 1), (3, 1))
        assert path is not None
        # Must detour through row 2 (roads) to avoid expensive swamp at (2, 1)
        assert (2, 1) not in path
        assert (1, 2) in path
        assert (2, 2) in path
        assert (3, 2) in path

    def test_astar_obstacle_avoidance_and_walled_target(self, grid: CityGrid):
        """Tier 2: Path around impassable obstacle, returns None if target is sealed."""
        # Erect a vertical wall at x=2, y in [1, 2, 3]
        for y in [1, 2, 3]:
            grid.set_building(2, y, f"wall_{y}", passable=False)

        path = grid.find_path((1, 2), (3, 2))
        assert path is not None
        # Path must go around the wall either through y=0 or y=4
        for x, y in path:
            assert not (x == 2 and 1 <= y <= 3)

        # Now completely box in target (3, 2)
        grid.set_building(3, 1, "box_top", passable=False)
        grid.set_building(3, 3, "box_bot", passable=False)
        grid.set_building(4, 2, "box_right", passable=False)

        blocked_path = grid.find_path((1, 2), (3, 2))
        assert blocked_path is None  # Completely unreachable

    def test_coordinate_projections_roundtrip(self):
        """Tier 1: Verify isometric and orthographic mathematical transformations and depth sorting."""
        # Isometric transformation
        gx, gy = 5.0, 7.0
        iso_x, iso_y = CityGrid.to_isometric(gx, gy, tile_width=64.0, tile_height=32.0)
        # Expected: iso_x = (5 - 7) * 32 = -64.0, iso_y = (5 + 7) * 16 = 192.0
        assert iso_x == -64.0
        assert iso_y == 192.0

        # Invert isometric back to grid coordinates
        rev_x, rev_y = CityGrid.from_isometric(iso_x, iso_y, tile_width=64.0, tile_height=32.0)
        assert pytest.approx(rev_x, 1e-6) == gx
        assert pytest.approx(rev_y, 1e-6) == gy

        # Orthographic transformation
        ortho_x, ortho_y = CityGrid.to_orthographic(gx, gy, cell_size=24.0)
        assert ortho_x == 120.0
        assert ortho_y == 168.0

        rev_ox, rev_oy = CityGrid.from_orthographic(ortho_x, ortho_y, cell_size=24.0)
        assert pytest.approx(rev_ox, 1e-6) == gx
        assert pytest.approx(rev_oy, 1e-6) == gy

        # Depth key
        assert CityGrid.get_depth_key(5, 7) == 12
        assert CityGrid.get_depth_key(10, 2) == 12


# =============================================================================
# 3. Inter-Agent Message Bus & Democratic Consensus Tests
# =============================================================================

class TestMessageBusAndConsensus:
    """Tests for point-to-point messaging, broadcasts, topic pub/sub, and civic voting."""

    def test_direct_messaging_and_inbox_drain(self, message_bus: MessageBus):
        """Tier 1: Direct 1:1 message delivery and inbox draining."""
        message_bus.register_agent("agent_1")
        message_bus.register_agent("agent_2")

        msg = AgentMessage(
            tick=1,
            sender_id="agent_1",
            recipient_id="agent_2",
            type=MessageType.DIRECT,
            content="Greetings from Mayor",
        )
        assert message_bus.send_direct(msg) is True

        inbox_1 = message_bus.drain_inbox("agent_1")
        assert len(inbox_1) == 0

        inbox_2 = message_bus.drain_inbox("agent_2")
        assert len(inbox_2) == 1
        assert inbox_2[0].content == "Greetings from Mayor"
        assert inbox_2[0].sender_id == "agent_1"

        # Subsequent drain is empty
        assert len(message_bus.drain_inbox("agent_2")) == 0

    def test_broadcast_and_topic_pub_sub(self, message_bus: MessageBus):
        """Tier 1: Topic subscriptions, selective publishing, and city-wide broadcasts."""
        message_bus.register_agent("mayor")
        message_bus.register_agent("architect")
        message_bus.register_agent("merchant")

        message_bus.subscribe("architect", "construction")
        message_bus.subscribe("merchant", "trade")

        # Publish to construction: only architect receives it
        msg_build = AgentMessage(
            tick=1,
            sender_id="mayor",
            type=MessageType.TOPIC,
            topic="construction",
            content="New zoning plan available",
        )
        delivered = message_bus.publish("construction", msg_build)
        assert delivered == 1

        assert len(message_bus.drain_inbox("architect")) == 1
        assert len(message_bus.drain_inbox("merchant")) == 0

        # Broadcast announcement: both architect and merchant receive, but not sender
        msg_bcast = AgentMessage(
            tick=2,
            sender_id="mayor",
            type=MessageType.BROADCAST,
            content="Public Town Hall at 12:00",
        )
        delivered_bcast = message_bus.broadcast(msg_bcast)
        assert delivered_bcast == 2
        assert len(message_bus.drain_inbox("architect")) == 1
        assert len(message_bus.drain_inbox("merchant")) == 1
        assert len(message_bus.drain_inbox("mayor")) == 0

        # Dialogue feed records broadcast
        recent_dialogues = message_bus.get_recent_dialogues(10)
        assert any("Town Hall" in d["content"] for d in recent_dialogues)

    @pytest.mark.asyncio
    async def test_democratic_consensus_proposal_passes_and_executes(
        self,
        message_bus: MessageBus,
    ):
        """Tier 1 & 3: Proposal reaches quorum, passes (>50% AYE), and executes callback."""
        executed = []

        def on_proposal_executed(proposal: CivicProposal):
            executed.append(proposal.id)

        message_bus.register_proposal_callback("REZONE", on_proposal_executed)

        prop = CivicProposal(
            creator_id="mayor",
            title="Create Waterfront Park",
            description="Rezone industrial parcel to park",
            action_type="REZONE",
            action_payload={"x": 5, "y": 5, "zone": "PARK"},
            created_tick=1,
            expires_tick=10,
            quorum_required=3,
            pass_threshold_ratio=0.50,
        )
        p_id = message_bus.submit_proposal(prop)
        assert p_id in message_bus.proposals

        # Cast votes: 2 AYE, 1 NAY (Total=3 >= quorum 3, AYE ratio = 2/3 = 66.7% > 50%)
        assert message_bus.cast_vote(p_id, "voter_1", VoteChoice.AYE) is True
        assert message_bus.cast_vote(p_id, "voter_2", VoteChoice.AYE) is True
        assert message_bus.cast_vote(p_id, "voter_3", VoteChoice.NAY) is True

        resolved = await message_bus.evaluate_proposals(current_tick=2)
        assert len(resolved) == 1
        assert resolved[0].status == ProposalStatus.EXECUTED
        assert p_id in executed

    @pytest.mark.asyncio
    async def test_democratic_consensus_tie_and_rejection(
        self,
        message_bus: MessageBus,
    ):
        """Tier 2: Tie vote (50% AYE) fails > 50% threshold and is rejected."""
        prop = CivicProposal(
            creator_id="citizen_1",
            title="Tax Holiday",
            description="Reduce commercial tax to 0%",
            action_type="ADJUST_TAX",
            action_payload={"sales_tax_rate": 0.0},
            created_tick=1,
            expires_tick=5,
            quorum_required=2,
            pass_threshold_ratio=0.50,
        )
        p_id = message_bus.submit_proposal(prop)

        # 1 AYE, 1 NAY (Ratio = 0.50, which is NOT > 0.50)
        message_bus.cast_vote(p_id, "voter_a", VoteChoice.AYE)
        message_bus.cast_vote(p_id, "voter_b", VoteChoice.NAY)

        resolved = await message_bus.evaluate_proposals(current_tick=2)
        assert len(resolved) == 1
        assert resolved[0].status == ProposalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_democratic_consensus_expiration_without_quorum(
        self,
        message_bus: MessageBus,
    ):
        """Tier 2: Proposal expiring without meeting quorum is marked EXPIRED."""
        prop = CivicProposal(
            creator_id="citizen_1",
            title="Late Proposal",
            description="Expiring soon",
            action_type="REZONE",
            created_tick=1,
            expires_tick=10,
            quorum_required=5,
        )
        p_id = message_bus.submit_proposal(prop)
        message_bus.cast_vote(p_id, "voter_1", VoteChoice.AYE)  # Only 1 vote

        # At tick 5: still active
        res_5 = await message_bus.evaluate_proposals(current_tick=5)
        assert len(res_5) == 0

        # At tick 10: expires
        res_10 = await message_bus.evaluate_proposals(current_tick=10)
        assert len(res_10) == 1
        assert res_10[0].status == ProposalStatus.EXPIRED


# =============================================================================
# 4. Tri-Resource Economy & Municipal Treasury Tests
# =============================================================================

class TestTriResourceEconomy:
    """Tests for ResourceLedger, account transfers, sales tax, property taxes, and grants."""

    def test_resource_ledger_atomic_operations(self):
        """Tier 1: Ledger deposit, sufficiency check, and atomic withdrawal."""
        ledger = ResourceLedger(funds=100.0, energy=50.0, materials=10.0)
        assert ledger.has_sufficient(funds=80.0, energy=50.0, materials=5.0) is True
        assert ledger.has_sufficient(funds=101.0) is False
        assert ledger.has_sufficient(materials=11.0) is False

        # Atomic withdrawal succeeds
        assert ledger.withdraw(funds=30.0, materials=5.0) is True
        assert ledger.funds == 70.0
        assert ledger.materials == 5.0
        assert ledger.energy == 50.0

        # Atomic withdrawal fails with zero balance change if any resource is short
        assert ledger.withdraw(funds=50.0, materials=10.0) is False
        assert ledger.funds == 70.0
        assert ledger.materials == 5.0

        # Deposit
        ledger.deposit(funds=10.0, energy=20.0, materials=15.0)
        assert ledger.funds == 80.0
        assert ledger.energy == 70.0
        assert ledger.materials == 20.0

    def test_commercial_transfer_deducts_sales_tax_into_treasury(
        self,
        economy: EconomySystem,
    ):
        """Tier 1 & 3: Commercial transaction pays sales tax into municipal treasury."""
        initial_treasury = economy.treasury.funds  # 5000.0
        economy.register_account("buyer", funds=200.0)
        economy.register_account("seller", funds=50.0)

        # Transfer $100 with 5% sales tax
        tx = economy.transfer(
            sender_id="buyer",
            recipient_id="seller",
            amount=100.0,
            resource="funds",
            category="COMMERCIAL_TRADE",
            tick=1,
            description="Purchased lumber",
        )
        assert tx is not None
        assert tx.tax_collected == 5.0
        assert tx.net_amount == 95.0

        # Verify account balances
        assert economy.get_ledger("buyer").funds == 100.0
        assert economy.get_ledger("seller").funds == 145.0  # 50 + 95
        assert economy.treasury.funds == initial_treasury + 5.0
        assert economy.total_tax_collected == 5.0

    def test_insufficient_funds_transfer_fails(self, economy: EconomySystem):
        """Tier 2: Transferring more than available balance fails safely."""
        economy.register_account("broke_agent", funds=10.0)
        economy.register_account("vendor", funds=100.0)

        tx = economy.transfer(
            sender_id="broke_agent",
            recipient_id="vendor",
            amount=50.0,
            resource="funds",
        )
        assert tx is None
        assert economy.get_ledger("broke_agent").funds == 10.0
        assert economy.get_ledger("vendor").funds == 100.0

    def test_municipal_grants_and_maintenance(self, economy: EconomySystem):
        """Tier 1: Disbursing grants and charging infrastructure maintenance."""
        treasury_start = economy.treasury.funds
        economy.register_account("research_lab", funds=10.0)

        # Grant from treasury
        assert economy.disburse_grant("research_lab", 200.0, tick=1) is True
        assert economy.treasury.funds == treasury_start - 200.0
        assert economy.get_ledger("research_lab").funds == 210.0

        # Maintenance deduction
        assert economy.charge_maintenance(50.0, tick=2) is True
        assert economy.treasury.funds == treasury_start - 250.0

    def test_epoch_property_tax_collection(self, economy: EconomySystem):
        """Tier 1: Property taxes assessed per building owner and credited to treasury."""
        economy.register_account("owner_1", funds=50.0)
        economy.register_account("owner_2", funds=5.0)  # Insolvent for full tax (rate=10.0)

        parcels = [
            ("owner_1", "house_1"),
            ("owner_1", "shop_1"),
            ("owner_2", "factory_1"),
        ]

        # owner_1 has 2 buildings * 10 = 20 tax (solvent)
        # owner_2 has 1 building, owes 10, but only has 5 (pays 5)
        # Total tax = 25.0
        collected = economy.collect_property_taxes(parcels, tick=20)
        assert collected == 25.0
        assert economy.get_ledger("owner_1").funds == 30.0  # 50 - 20
        assert economy.get_ledger("owner_2").funds == 0.0   # 5 - 5


# =============================================================================
# 5. 6-Phase Simulation Coordinator Loop & Controls Tests
# =============================================================================

class TestSimulationCoordinator:
    """Tests for the 6-phase async execution loop, pause/resume, and delta generation."""

    @pytest.mark.asyncio
    async def test_coordinator_single_step_lifecycle(
        self,
        coordinator: SimulationCoordinator,
        mock_agent_factory,
    ):
        """Tier 1: Advancing single tick through all 6 phases produces valid delta."""
        agent = mock_agent_factory("agent_test", "CITIZEN", (2, 2))
        coordinator.register_agent(agent, initial_x=2, initial_y=2)

        delta = await coordinator.step()
        assert coordinator.current_tick == 1
        assert delta["type"] == "TICK_DELTA"
        assert delta["tick"] == 1
        assert len(delta["agents"]) == 1
        assert delta["agents"][0]["id"] == "agent_test"
        assert delta["agents"][0]["x"] == 2
        assert delta["agents"][0]["y"] == 2

    @pytest.mark.asyncio
    async def test_coordinator_pause_resume_and_speed_control(
        self,
        coordinator: SimulationCoordinator,
    ):
        """Tier 1: Pause, resume, and speed clamping."""
        assert coordinator.state == SimulationState.STOPPED

        await coordinator.start()
        assert coordinator.state == SimulationState.RUNNING

        await coordinator.pause()
        assert coordinator.state == SimulationState.PAUSED

        await coordinator.resume()
        assert coordinator.state == SimulationState.RUNNING

        # Speed adjustment and bounding
        coordinator.set_speed(15.0)
        assert coordinator.tps == 15.0
        coordinator.set_speed(100.0)  # Exceeds max_tps 25.0
        assert coordinator.tps == 25.0
        coordinator.set_speed(0.1)    # Below min_tps 0.5
        assert coordinator.tps == 0.5

        await coordinator.stop()
        assert coordinator.state == SimulationState.STOPPED

    @pytest.mark.asyncio
    async def test_coordinator_inbound_commands_rezone_and_construct(
        self,
        coordinator: SimulationCoordinator,
    ):
        """Tier 1 & 3: Phase 1 drains inbound commands and modifies spatial grid."""
        coordinator.enqueue_command("REZONE", {"x": 4, "y": 4, "zone": "COMMERCIAL"})
        coordinator.enqueue_command("CONSTRUCT", {"x": 4, "y": 4, "building_id": "mall_1", "building_type": "COMMERCIAL"})

        delta = await coordinator.step()
        assert coordinator.grid.get_parcel(4, 4).zone == ZoneType.COMMERCIAL
        assert coordinator.grid.get_parcel(4, 4).building_id == "mall_1"

        # Dirty parcel must be logged in delta
        assert any(p["x"] == 4 and p["y"] == 4 for p in delta["parcels"])

    @pytest.mark.asyncio
    async def test_coordinator_resolves_agent_actions(
        self,
        coordinator: SimulationCoordinator,
        mock_agent_factory,
    ):
        """Tier 3: Agent deliberate action (MOVE, REZONE, BUILD, TRADE) resolution."""
        # 1. Moving Agent
        def mover_deliberate(a):
            return {"type": "MOVE", "target": (a.x + 1, a.y)}

        mover = mock_agent_factory("mover_1", "CITIZEN", (2, 2), mover_deliberate)
        coordinator.register_agent(mover, initial_x=2, initial_y=2)

        # 2. Rezoning Agent (pays $50 fee)
        def rezoner_deliberate(a):
            return {"type": "REZONE", "target": (8, 8), "payload": {"zone": "PARK"}}

        rezoner = mock_agent_factory("rezoner_1", "ARCHITECT", (5, 5), rezoner_deliberate)
        coordinator.register_agent(rezoner, initial_x=5, initial_y=5, initial_funds=100.0)

        treasury_before = coordinator.economy.treasury.funds

        delta = await coordinator.step()

        # Mover advanced to (3, 2)
        assert mover.x == 3
        assert coordinator.grid.find_agent_pos("mover_1") == (3, 2)

        # Rezoner updated parcel (8, 8) to PARK and paid $50
        assert coordinator.grid.get_parcel(8, 8).zone == ZoneType.PARK
        assert coordinator.economy.get_ledger("rezoner_1").funds == 50.0
        assert coordinator.economy.treasury.funds == treasury_before + 50.0

    @pytest.mark.asyncio
    async def test_coordinator_epoch_transition_accounting(
        self,
        coordinator: SimulationCoordinator,
        mock_agent_factory,
    ):
        """Tier 1: Ticks_per_epoch triggers property tax sweep and epoch notification."""
        coordinator.config.ticks_per_epoch = 5
        agent = mock_agent_factory("property_owner", "MERCHANT", (3, 3))
        coordinator.register_agent(agent, initial_x=3, initial_y=3, initial_funds=100.0)

        # Place building owned by property_owner
        parcel = coordinator.grid.set_building(3, 3, "market_stall", building_type="COMMERCIAL")
        parcel.metadata["owner_id"] = "property_owner"

        for _ in range(5):
            await coordinator.step()

        assert coordinator.current_tick == 5
        assert coordinator.current_epoch == 1
        assert len(agent.epoch_notifications) == 1
        assert agent.epoch_notifications[0] == 1


# =============================================================================
# 6. State Serialization & Snapshot Reconstruction Tests
# =============================================================================

class TestStateSerialization:
    """Tests for full model serialization to dict and reconstruction."""

    def test_grid_serialization_roundtrip(self, grid: CityGrid):
        """Tier 1: CityGrid to_dict and from_dict reconstructs identical state."""
        grid.set_zone(3, 3, ZoneType.COMMERCIAL)
        grid.set_building(3, 3, "shop_1", building_type="COMMERCIAL", passable=False)
        grid.set_occupant(4, 4, "agent_1")

        data = grid.to_dict()
        restored = CityGrid.from_dict(data)

        assert restored.width == grid.width
        assert restored.height == grid.height
        assert restored.get_parcel(3, 3).zone == ZoneType.COMMERCIAL
        assert restored.get_parcel(3, 3).building_id == "shop_1"
        assert restored.get_parcel(3, 3).passable is False
        assert restored.get_occupant(4, 4) == "agent_1"
        assert restored.find_agent_pos("agent_1") == (4, 4)

    def test_economy_serialization_roundtrip(self, economy: EconomySystem):
        """Tier 1: EconomySystem to_dict and from_dict restores treasury and ledgers."""
        economy.register_account("agent_a", funds=250.0, energy=80.0, materials=15.0)
        economy.transfer("agent_a", "treasury", 50.0, category="DONATION")

        data = economy.to_dict()
        restored = EconomySystem.from_dict(data, config=economy.config)

        assert restored.treasury.funds == economy.treasury.funds
        assert restored.get_ledger("agent_a").funds == 200.0
        assert restored.get_ledger("agent_a").energy == 80.0
        assert len(restored.transaction_history) == len(economy.transaction_history)

    def test_coordinator_serialization_roundtrip(
        self,
        coordinator: SimulationCoordinator,
    ):
        """Tier 1: SimulationCoordinator full state serialization."""
        coordinator.current_tick = 42
        coordinator.current_epoch = 2
        coordinator.state = SimulationState.PAUSED
        coordinator.grid.set_zone(2, 2, ZoneType.PARK)

        data = coordinator.to_dict()
        restored = SimulationCoordinator.from_dict(data, config=coordinator.config)

        assert restored.current_tick == 42
        assert restored.current_epoch == 2
        assert restored.state == SimulationState.PAUSED
        assert restored.grid.get_parcel(2, 2).zone == ZoneType.PARK
