"""Empirical stress-test suite for reviewer_city_m1_2."""

import sys
sys.path.insert(0, r"c:\Users\ignaz\antigravity\keen-franklin")

import json
import pytest
from agent_city.config import DEFAULT_CONFIG, SimulationConfig, ZoneType, VoteChoice
from agent_city.engine.grid import CityGrid
from agent_city.engine.economy import EconomySystem, ResourceLedger
from agent_city.engine.message_bus import MessageBus, AgentMessage, CivicProposal
from agent_city.engine.simulation import SimulationCoordinator

def test_negative_withdrawal_minting():
    ledger = ResourceLedger(funds=50.0, energy=50.0, materials=50.0)
    res = ledger.withdraw(funds=-100.0)
    print(f"withdraw(funds=-100) returned: {res}, new funds: {ledger.funds}")
    assert res is True
    assert ledger.funds == 150.0  # Balance inflated!

def test_teleportation_via_move():
    grid = CityGrid(width=32, height=32)
    grid.set_occupant(0, 0, "speedy")
    # Move across the entire map
    res = grid.move_occupant(0, 0, 31, 31, "speedy")
    print(f"move_occupant(0, 0 -> 31, 31) returned: {res}")
    assert res is True
    assert grid.find_agent_pos("speedy") == (31, 31)

def test_multitile_tax_duplication():
    grid = CityGrid(width=16, height=16)
    grid.place_multi_tile_building("hall_1", "CIVIC", 2, 2, width=2, height=2)
    # Check how many parcels have building_id == 'hall_1'
    parcels_with_bldg = [
        (p.metadata.get("owner_id", "public"), p.building_id)
        for row in grid._grid for p in row if p.building_id == "hall_1"
    ]
    print(f"Parcels found for 2x2 building: {len(parcels_with_bldg)}")
    assert len(parcels_with_bldg) == 4

def test_multitile_incomplete_demolition():
    grid = CityGrid(width=16, height=16)
    grid.place_multi_tile_building("hall_1", "CIVIC", 2, 2, width=2, height=2)
    grid.remove_building(2, 2)
    # Check if building is still partially on the grid
    remaining = [
        (p.x, p.y) for row in grid._grid for p in row if p.building_id == "hall_1"
    ]
    print(f"Remaining tiles after remove_building(2, 2): {remaining}")
    assert len(remaining) == 3

def test_invalid_zone_type_crash():
    coord = SimulationCoordinator()
    coord.register_agent(type("DummyAgent", (), {"id": "a1", "x": 0, "y": 0})(), initial_x=0, initial_y=0, initial_funds=100.0)
    # Mock action with invalid zone
    actions = [("a1", {"type": "REZONE", "target": (1, 1), "payload": {"zone": "NON_EXISTENT_ZONE"}})]
    import asyncio
    try:
        asyncio.run(coord._phase_3_resolve_actions(actions))
        print("Invalid zone handled gracefully")
    except ValueError as e:
        print(f"Crash on invalid zone: {e}")
        assert "not a valid ZoneType" in str(e)

if __name__ == "__main__":
    test_negative_withdrawal_minting()
    test_teleportation_via_move()
    test_multitile_tax_duplication()
    test_multitile_incomplete_demolition()
    test_invalid_zone_type_crash()
    print("All empirical challenge checks completed successfully!")
