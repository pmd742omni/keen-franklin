"""Adversarial stress-test script for Milestone 1 Virtual City Engine."""

from __future__ import annotations

import asyncio
import sys
import os

# Add keen-franklin to sys.path
sys.path.insert(0, r"c:\Users\ignaz\antigravity\keen-franklin")

from agent_city.config import DEFAULT_CONFIG, SimulationConfig, SimulationState, ZoneType, VoteChoice, ProposalStatus
from agent_city.engine.grid import CityGrid, Parcel
from agent_city.engine.economy import EconomySystem, ResourceLedger, Transaction
from agent_city.engine.message_bus import MessageBus, AgentMessage, CivicProposal
from agent_city.engine.simulation import SimulationCoordinator


async def test_negative_withdrawal():
    """Vulnerability test: Can negative withdrawal inflate balances?"""
    print("--- Test 1: Negative Withdrawal ---")
    ledger = ResourceLedger(funds=10.0, energy=10.0, materials=10.0)
    success = ledger.withdraw(funds=-100.0)
    print(f"Withdraw(-100 funds) success: {success}, funds balance: {ledger.funds}")
    if ledger.funds > 10.0:
        print("[VULNERABILITY CONFIRMED] Negative withdrawal increases balance without validation!")
    else:
        print("[PASS] Negative withdrawal rejected or handled.")


async def test_invalid_resource_type():
    """Robustness test: Transfer with invalid resource type."""
    print("\n--- Test 2: Invalid Resource Type ---")
    eco = EconomySystem()
    eco.register_account("alice", funds=100.0)
    eco.register_account("bob", funds=100.0)
    try:
        tx = eco.transfer("alice", "bob", 10.0, resource="cryptocurrency")
        print(f"Transfer returned: {tx}")
    except Exception as e:
        print(f"[EXCEPTION CAUGHT] Transfer raised {type(e).__name__}: {e}")


async def test_building_placement_over_agent():
    """Edge case: Constructing building on top of active agent."""
    print("\n--- Test 3: Building on Occupied Parcel ---")
    coord = SimulationCoordinator()
    
    class DummyAgent:
        def __init__(self, aid, x, y):
            self.id = aid
            self.x = x
            self.y = y
        def deliberate(self):
            return {"type": "IDLE"}
    
    agent = DummyAgent("trapped_agent", 5, 5)
    coord.register_agent(agent, 5, 5)
    print(f"Agent initially at: {coord.grid.find_agent_pos('trapped_agent')}")
    
    # Place impassable building on (5, 5)
    b_parcel = coord.grid.set_building(5, 5, "fortress", passable=False)
    print(f"Building placed on (5, 5), passable={b_parcel.passable}, occupant={b_parcel.occupant_id}")
    print(f"Can move to (5, 5) for another agent: {coord.grid.can_move_to(5, 5, 'other_agent')}")
    print(f"Can move to (5, 5) for trapped agent: {coord.grid.can_move_to(5, 5, 'trapped_agent')}")
    
    # Run a tick
    delta = await coord.step()
    print(f"Tick completed. Trapped agent in delta: {delta['agents'][0]['x']}, {delta['agents'][0]['y']}")


async def test_out_of_bounds_multi_tile():
    """Edge case: Multi-tile building crossing grid boundary."""
    print("\n--- Test 4: Multi-tile Crossing Grid Boundary ---")
    grid = CityGrid(width=16, height=16)
    placed = grid.place_multi_tile_building("border_bldg", "COMMERCIAL", top_left_x=15, top_left_y=15, width=2, height=2)
    print(f"Placed across boundary (15, 15) with size 2x2: {placed}")
    p15_15 = grid.get_parcel(15, 15)
    print(f"Parcel (15, 15) building_id: {p15_15.building_id}")


async def test_concurrency_step_while_running():
    """Stress test: Stepping while continuous simulation is running."""
    print("\n--- Test 5: Stepping while RUNNING ---")
    coord = SimulationCoordinator()
    coord.set_speed(25.0)
    task = await coord.start()
    await asyncio.sleep(0.05)
    
    try:
        # Rapid concurrent stepping
        steps = [coord.step() for _ in range(5)]
        results = await asyncio.gather(*steps)
        print(f"Executed 5 concurrent steps while running. Current tick: {coord.current_tick}")
    except Exception as e:
        print(f"[CONCURRENCY EXCEPTION] {type(e).__name__}: {e}")
    finally:
        await coord.stop()


async def test_all_abstain_proposal():
    """Edge case: Proposal where all voters abstain."""
    print("\n--- Test 6: All Voters Abstain ---")
    bus = MessageBus()
    prop = CivicProposal(
        creator_id="citizen",
        title="Abstain Bill",
        description="Testing all abstentions",
        action_type="REZONE",
        created_tick=1,
        expires_tick=5,
        quorum_required=2,
    )
    bus.submit_proposal(prop)
    bus.cast_vote(prop.id, "voter_1", VoteChoice.ABSTAIN)
    bus.cast_vote(prop.id, "voter_2", VoteChoice.ABSTAIN)
    resolved = await bus.evaluate_proposals(current_tick=2)
    print(f"Resolved count: {len(resolved)}")
    if resolved:
        print(f"Status: {resolved[0].status.value}, AYE={resolved[0].aye_count}, NAY={resolved[0].nay_count}, ABSTAIN={resolved[0].abstain_count}")


async def main():
    await test_negative_withdrawal()
    await test_invalid_resource_type()
    await test_building_placement_over_agent()
    await test_out_of_bounds_multi_tile()
    await test_concurrency_step_while_running()
    await test_all_abstain_proposal()


if __name__ == "__main__":
    asyncio.run(main())
